import re
from typing import List, Tuple


def repair_patch(patch: str) -> str:
    """Repair common truncation issues in a unified diff patch.

    Fixes:
    - Missing trailing newline
    - Incorrect @@ hunk header line counts
    - Incomplete trailing hunks (started but no added/removed lines)
    """
    if not patch or not patch.strip():
        return patch

    lines = patch.split("\n")
    # Remove trailing empty strings from the split (artifacts of trailing \n)
    while lines and lines[-1] == "":
        lines.pop()

    # --- Pass 1: split into hunks per file ---
    # We rebuild the patch hunk-by-hunk, recalculating counts.
    output_lines: List[str] = []
    current_hunk_body: List[str] = []
    current_hunk_header_idx: int = -1  # index in output_lines

    def _flush_hunk():
        """Recalculate the header for the buffered hunk and flush."""
        nonlocal current_hunk_body, current_hunk_header_idx
        if current_hunk_header_idx < 0:
            return

        old_count = 0
        new_count = 0
        for bline in current_hunk_body:
            if bline.startswith("-"):
                old_count += 1
            elif bline.startswith("+"):
                new_count += 1
            else:
                # context line (starts with " " or is empty in some edge cases)
                old_count += 1
                new_count += 1

        # Drop incomplete trailing hunks (header present, but no actual changes)
        if old_count == 0 and new_count == 0 and not current_hunk_body:
            # Remove the hunk header we already appended
            output_lines.pop(current_hunk_header_idx)
            current_hunk_body = []
            current_hunk_header_idx = -1
            return

        # Rewrite the @@ line with correct counts
        header = output_lines[current_hunk_header_idx]
        m = re.match(r"@@\s+-(\d+)(?:,\d+)?\s+\+(\d+)(?:,\d+)?\s+@@(.*)", header)
        if m:
            old_start = m.group(1)
            new_start = m.group(2)
            rest = m.group(3)
            output_lines[current_hunk_header_idx] = (
                f"@@ -{old_start},{old_count} +{new_start},{new_count} @@{rest}"
            )

        output_lines.extend(current_hunk_body)
        current_hunk_body = []
        current_hunk_header_idx = -1

    for line in lines:
        if line.startswith("@@"):
            _flush_hunk()
            current_hunk_header_idx = len(output_lines)
            output_lines.append(line)
        elif current_hunk_header_idx >= 0:
            # Inside a hunk body — only accept diff-valid lines
            if line.startswith(("+", "-", " ", "\\")):
                current_hunk_body.append(line)
            elif line.startswith(("diff ", "--- ", "+++ ")):
                # New file section started — flush current hunk first
                _flush_hunk()
                output_lines.append(line)
            elif line == "":
                # Could be a context line with empty content
                current_hunk_body.append(line)
            else:
                # Unknown line inside a hunk — likely truncation garbage; skip
                pass
        else:
            output_lines.append(line)

    _flush_hunk()

    result = "\n".join(output_lines)
    # Ensure trailing newline (required by git apply)
    if not result.endswith("\n"):
        result += "\n"
    return result


def strip_context_lines(patch: str) -> str:
    """Strip context lines from a patch, keeping only +/- lines and headers.

    This produces a patch that can be applied with ``git apply -C0`` when
    the LLM-generated context lines don't match the actual file content.
    Hunk headers are rewritten with correct counts and 0-context ranges.
    """
    if not patch or not patch.strip():
        return patch

    lines = patch.split("\n")
    while lines and lines[-1] == "":
        lines.pop()

    output: List[str] = []
    hunk_removes: List[str] = []
    hunk_adds: List[str] = []
    hunk_header_match = None  # regex match for current hunk
    context_before_first_change = 0  # track leading context to adjust start line

    def _flush_stripped():
        nonlocal hunk_removes, hunk_adds, hunk_header_match, context_before_first_change
        if hunk_header_match is None:
            return
        old_start = int(hunk_header_match.group(1)) + context_before_first_change
        new_start = int(hunk_header_match.group(2)) + context_before_first_change
        old_count = len(hunk_removes)
        new_count = len(hunk_adds)
        if old_count == 0 and new_count == 0:
            hunk_removes = []
            hunk_adds = []
            hunk_header_match = None
            context_before_first_change = 0
            return
        rest = hunk_header_match.group(3)
        output.append(f"@@ -{old_start},{old_count} +{new_start},{new_count} @@{rest}")
        output.extend(hunk_removes)
        output.extend(hunk_adds)
        hunk_removes = []
        hunk_adds = []
        hunk_header_match = None
        context_before_first_change = 0

    in_hunk = False
    seen_change = False
    for line in lines:
        m = re.match(r"@@\s+-(\d+)(?:,\d+)?\s+\+(\d+)(?:,\d+)?\s+@@(.*)", line)
        if m:
            _flush_stripped()
            hunk_header_match = m
            in_hunk = True
            seen_change = False
            context_before_first_change = 0
            continue
        if not in_hunk:
            output.append(line)
            continue
        if line.startswith("-"):
            hunk_removes.append(line)
            seen_change = True
        elif line.startswith("+"):
            hunk_adds.append(line)
            seen_change = True
        elif line.startswith(("diff ", "--- ", "+++ ")):
            _flush_stripped()
            in_hunk = False
            output.append(line)
        elif not seen_change:
            # Leading context line before any +/- — count to adjust start line
            context_before_first_change += 1
        # else: trailing/middle context — drop it

    _flush_stripped()

    result = "\n".join(output)
    if not result.endswith("\n"):
        result += "\n"
    return result


def extract_patch(response: str) -> str:
    """Extract a unified diff patch from an LLM response.

    Tries multiple strategies:
    0. Raw diff (response starts with diff --git or --- a/)
    1. ```<any-lang> fenced block containing diff content
    2. --- / +++ header pattern
    3. @@ hunk header pattern
    """
    if not response:
        return ""

    # Strategy 0: response IS a raw patch (no prose wrapper)
    stripped = response.strip()
    if stripped.startswith("diff --git") or stripped.startswith("--- a/"):
        return repair_patch(stripped)

    # Strategy 1: fenced code block (any language tag, not just diff/patch)
    for m in re.finditer(r"```[a-zA-Z-]*\s*\n(.*?)```", response, re.DOTALL):
        candidate = m.group(1).strip()
        if "---" in candidate or "@@" in candidate:
            return repair_patch(candidate)

    # Strategy 2: find --- a/ ... +++ b/ pattern
    match = re.search(
        r"(---\s+a/.*?\n\+\+\+\s+b/.*?\n(?:@@.*?@@.*?\n(?:[ +\-].*?\n|.*?\n)*)+)",
        response,
        re.DOTALL,
    )
    if match:
        return repair_patch(match.group(1).strip())

    # Strategy 3: collect all lines starting from first --- a/ line
    lines = response.split("\n")
    patch_lines = []
    collecting = False
    for line in lines:
        if line.startswith("--- a/") or line.startswith("diff --git"):
            collecting = True
        if collecting:
            patch_lines.append(line)

    if patch_lines:
        return repair_patch("\n".join(patch_lines).strip())

    return ""


def validate_patch_syntax(patch: str) -> Tuple[bool, str]:
    """Check if a patch has valid unified diff syntax.

    Returns (is_valid, error_message).
    """
    if not patch or not patch.strip():
        return False, "Empty patch"

    lines = patch.split("\n")

    has_minus_header = False
    has_plus_header = False
    has_hunk = False

    for line in lines:
        if line.startswith("--- a/") or line.startswith("--- "):
            has_minus_header = True
        elif line.startswith("+++ b/") or line.startswith("+++ "):
            has_plus_header = True
        elif line.startswith("@@"):
            has_hunk = True

    if not has_minus_header:
        return False, "Missing '--- a/' header"
    if not has_plus_header:
        return False, "Missing '+++ b/' header"
    if not has_hunk:
        return False, "Missing @@ hunk header"

    return True, ""
