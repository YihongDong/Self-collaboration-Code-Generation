import os
import subprocess
import shutil
import sys
from typing import Tuple

from core.patch_utils import strip_context_lines


def clone_repo(repo: str, base_commit: str, work_dir: str) -> str:
    """Clone a GitHub repo and checkout the base commit.

    Returns the path to the cloned repo.
    """
    repo_name = repo.replace("/", "__")
    repo_path = os.path.join(work_dir, repo_name)

    if os.path.exists(repo_path):
        # Already cloned — just reset
        reset_repo(repo_path, base_commit)
        return repo_path

    os.makedirs(work_dir, exist_ok=True)
    url = f"https://github.com/{repo}.git"

    subprocess.run(
        ["git", "clone", "--quiet", url, repo_path],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "checkout", "-f", base_commit],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )
    return repo_path


def get_repo_structure(repo_path: str, max_depth: int = 3) -> str:
    """Generate a directory tree string for the repo, limited to max_depth."""
    lines = []
    repo_path = os.path.abspath(repo_path)

    for root, dirs, files in os.walk(repo_path):
        # Skip hidden dirs and common non-essential dirs
        dirs[:] = [
            d for d in sorted(dirs)
            if not d.startswith(".") and d not in ("__pycache__", "node_modules", ".git", "egg-info")
            and not d.endswith(".egg-info")
        ]

        depth = root.replace(repo_path, "").count(os.sep)
        if depth >= max_depth:
            dirs.clear()
            continue

        indent = "  " * depth
        dirname = os.path.basename(root)
        lines.append(f"{indent}{dirname}/")

        subindent = "  " * (depth + 1)
        for f in sorted(files):
            if not f.startswith("."):
                lines.append(f"{subindent}{f}")

    return "\n".join(lines)


def _safe_resolve(repo_path: str, file_path: str) -> str:
    """Resolve *file_path* inside *repo_path* and ensure it doesn't escape.

    Returns the resolved absolute path, or "" if the path would leave the repo.
    """
    repo_root = os.path.realpath(repo_path)
    resolved = os.path.realpath(os.path.join(repo_root, file_path))
    if not resolved.startswith(repo_root + os.sep) and resolved != repo_root:
        return ""
    return resolved


def read_file(repo_path: str, file_path: str) -> str:
    """Read a file from the repo and return its content with line numbers."""
    full_path = _safe_resolve(repo_path, file_path)
    if not full_path or not os.path.isfile(full_path):
        return ""

    with open(full_path, "r", errors="replace") as f:
        lines = f.readlines()

    numbered = []
    for i, line in enumerate(lines, 1):
        numbered.append(f"{i:>6}\t{line.rstrip()}")
    return "\n".join(numbered)


def search_code(repo_path: str, pattern: str, file_glob: str = "*.py") -> str:
    """Search for a pattern in the repo using grep. Returns matching lines."""
    try:
        result = subprocess.run(
            ["grep", "-rn", "--include", file_glob, pattern, "."],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout
        # Truncate if too long
        lines = output.split("\n")
        if len(lines) > 100:
            output = "\n".join(lines[:100]) + f"\n... ({len(lines) - 100} more lines)"
        return output
    except (subprocess.TimeoutExpired, Exception) as e:
        return f"Search error: {e}"


def apply_patch(repo_path: str, patch: str) -> Tuple[bool, str]:
    """Apply a unified diff patch to the repo. Returns (success, message).

    Tries progressively more lenient strategies:
    1. Strict ``git apply``
    2. ``git apply -C1`` (reduced context matching)
    3. ``git apply --3way`` (3-way merge, more forgiving)
    4. ``patch -p1 --fuzz=3`` (very lenient context matching)
    """
    strategies = [
        (["git", "apply", "--verbose", "-"], "strict"),
        (["git", "apply", "--verbose", "-C1", "-"], "-C1"),
        (["git", "apply", "--verbose", "--3way", "-"], "--3way"),
    ]
    last_err = ""
    for cmd, label in strategies:
        try:
            result = subprocess.run(
                cmd,
                input=patch,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                msg = result.stderr or "Patch applied successfully."
                if label != "strict":
                    msg = f"[applied with {label}] {msg}"
                return True, msg
            last_err = result.stderr or result.stdout or "git apply failed"
        except subprocess.TimeoutExpired:
            return False, "Patch apply timed out"
        except Exception as e:
            return False, str(e)

    # Last resort: strip context lines (which may be hallucinated by the LLM)
    # and apply with line-number positioning only
    stripped = strip_context_lines(patch)
    if stripped and stripped != patch:
        for cmd, label in [
            (["git", "apply", "--verbose", "--unidiff-zero", "-"], "stripped-context"),
            (["patch", "-p1", "--fuzz=3", "--no-backup-if-mismatch"], "patch-fuzz"),
        ]:
            try:
                result = subprocess.run(
                    cmd,
                    input=stripped,
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    msg = result.stderr or result.stdout or "Patch applied successfully."
                    return True, f"[applied with {label}] {msg}"
                last_err = result.stderr or result.stdout or "apply failed"
            except subprocess.TimeoutExpired:
                return False, "Patch apply timed out"
            except Exception as e:
                return False, str(e)
    return False, last_err


def reset_repo(repo_path: str, base_commit: str):
    """Reset the repo to the base commit state."""
    subprocess.run(
        ["git", "checkout", "-f", base_commit],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "clean", "-fd"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )


def run_tests(repo_path: str, test_names: list, timeout: int = 300) -> Tuple[bool, str]:
    """Run pytest with the given test names. Returns (all_passed, output)."""
    if not test_names:
        return True, "No tests to run."

    cmd = [sys.executable, "-m", "pytest", "-xvs"] + test_names
    try:
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout + "\n" + result.stderr
        # Truncate very long output
        if len(output) > 8000:
            output = output[:4000] + "\n...(truncated)...\n" + output[-4000:]
        passed = result.returncode == 0
        return passed, output
    except subprocess.TimeoutExpired:
        return False, f"Tests timed out after {timeout}s"
    except Exception as e:
        return False, f"Test execution error: {e}"
