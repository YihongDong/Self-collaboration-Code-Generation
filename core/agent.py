"""
Core agent module: BaseAgent and SelfCollabSession.

BaseAgent is an LLM agent that interacts with a code repository through
actions (read, edit, search, bash, done). Patch extraction is done via
`git diff` after the agent edits files directly.

SelfCollabSession orchestrates the self-collaboration pattern:
  Analyst (Localizer) → Coder (Patcher) ↔ Tester (Verifier)
"""

import json
import os
import re
import subprocess

from core.backend import call_llm_with_tools

# ---------------------------------------------------------------------------
# Action schemas (OpenAI function-calling format)
# ---------------------------------------------------------------------------

# --- Analyst actions: search + read only ---
ANALYST_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Search for a pattern in the repository using grep. Returns matching lines with file paths and line numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Search pattern (regex supported)"},
                    "file_glob": {"type": "string", "description": "File glob filter (e.g. '*.py'). Default: '*.py'"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path relative to repo root"},
                    "start_line": {"type": "integer", "description": "Start line (1-based, optional)"},
                    "end_line": {"type": "integer", "description": "End line (1-based, optional)"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a read-only shell command (e.g. ls, find, grep, python -c). Do NOT edit files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default: 30)"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "done",
            "description": "Signal that your analysis is complete. You MUST provide your analysis result in the message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Your analysis: which files need changes and why"},
                },
                "required": ["message"],
            },
        },
    },
]

# --- Coder actions: read + edit ---
CODER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the repository. Always read before editing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path relative to repo root"},
                    "start_line": {"type": "integer", "description": "Start line (1-based, optional)"},
                    "end_line": {"type": "integer", "description": "End line (1-based, optional)"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit a file by replacing old_string with new_string. old_string must exactly match text in the file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path relative to repo root"},
                    "old_string": {"type": "string", "description": "Exact text to find in the file"},
                    "new_string": {"type": "string", "description": "Text to replace it with"},
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "done",
            "description": "Signal that your code changes are complete.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Summary of changes made"},
                },
                "required": [],
            },
        },
    },
]

# --- Full action set (for standalone single-agent mode) ---
ALL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the repository. Always read before editing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path relative to repo root"},
                    "start_line": {"type": "integer", "description": "Start line (1-based, optional)"},
                    "end_line": {"type": "integer", "description": "End line (1-based, optional)"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit a file by replacing old_string with new_string. old_string must exactly match text in the file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path relative to repo root"},
                    "old_string": {"type": "string", "description": "Exact text to find in the file"},
                    "new_string": {"type": "string", "description": "Text to replace it with"},
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Search for a pattern in the repository using grep.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Search pattern (regex supported)"},
                    "file_glob": {"type": "string", "description": "File glob filter (e.g. '*.py'). Default: '*.py'"},
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command in the repository root.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default: 120)"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "done",
            "description": "Signal that the task is complete.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Optional summary of what was done"},
                },
                "required": [],
            },
        },
    },
]

# --- HumanEval actions ---
HUMANEVAL_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file, creating it if it doesn't exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path relative to working directory"},
                    "content": {"type": "string", "description": "Full file content to write"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command. Use for running/testing code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default: 30)"},
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "done",
            "description": "Signal that the task is complete.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Optional summary"},
                },
                "required": [],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Action execution
# ---------------------------------------------------------------------------

def _safe_resolve(repo_path, file_path):
    """Resolve file_path inside repo_path, preventing path traversal."""
    repo_root = os.path.realpath(repo_path)
    resolved = os.path.realpath(os.path.join(repo_root, file_path))
    if not resolved.startswith(repo_root + os.sep) and resolved != repo_root:
        return None
    return resolved


def _exec_read_file(args, repo_path, container_id=None):
    path = args["path"]
    if container_id:
        # Normalize: strip leading / or /testbed/ prefix if agent passes absolute path
        clean = path.lstrip("/")
        if clean.startswith("testbed/"):
            clean = clean[len("testbed/"):]
        full_path = f"/testbed/{clean}"
        result = subprocess.run(
            ["docker", "exec", container_id, "cat", "-n", full_path],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return f"Error: file not found: {path}"
        lines = result.stdout.split("\n")
        start = args.get("start_line", 1)
        end = args.get("end_line", len(lines))
        return "\n".join(lines[max(0, start-1):end])

    full = _safe_resolve(repo_path, path)
    if not full or not os.path.isfile(full):
        return f"Error: file not found: {path}"

    with open(full, "r", errors="replace") as f:
        lines = f.readlines()

    start = args.get("start_line", 1)
    end = args.get("end_line", len(lines))
    start = max(1, start)
    end = min(len(lines), end)

    numbered = []
    for i in range(start - 1, end):
        numbered.append(f"{i + 1:>6}\t{lines[i].rstrip()}")
    return "\n".join(numbered)


def _exec_edit_file(args, repo_path, container_id=None):
    path = args["path"]
    old_string = args["old_string"]
    new_string = args["new_string"]

    if container_id:
        clean = path.lstrip("/")
        if clean.startswith("testbed/"):
            clean = clean[len("testbed/"):]
        full_path = f"/testbed/{clean}"
        result = subprocess.run(
            ["docker", "exec", container_id, "cat", full_path],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return f"Error: file not found: {path}"
        content = result.stdout
        count = content.count(old_string)
        if count == 1:
            new_content = content.replace(old_string, new_string, 1)
            write_result = subprocess.run(
                ["docker", "exec", "-i", container_id, "tee", full_path],
                input=new_content, capture_output=True, text=True, timeout=10,
            )
            if write_result.returncode != 0:
                return f"Error: failed to write {path}: {write_result.stderr.strip()}"
            return f"Successfully edited {path}"
        elif count > 1:
            return f"Error: old_string matches {count} locations in {path}. Provide more context."
        return f"Error: old_string not found in {path}."

    full = _safe_resolve(repo_path, path)
    if not full or not os.path.isfile(full):
        return f"Error: file not found: {path}"

    with open(full, "r", errors="replace") as f:
        content = f.read()

    # Exact match
    count = content.count(old_string)
    if count == 1:
        new_content = content.replace(old_string, new_string, 1)
        with open(full, "w") as f:
            f.write(new_content)
        return f"Successfully edited {path}"
    elif count > 1:
        return f"Error: old_string matches {count} locations in {path}. Provide more context to make it unique."

    # Fallback: whitespace-normalized match
    def normalize(s):
        return "\n".join(line.strip() for line in s.split("\n"))

    norm_content = normalize(content)
    norm_old = normalize(old_string)

    if norm_content.count(norm_old) == 1:
        content_lines = content.split("\n")
        old_lines = old_string.strip().split("\n")
        norm_old_lines = [l.strip() for l in old_lines]

        for i in range(len(content_lines) - len(norm_old_lines) + 1):
            chunk = [content_lines[i + j].strip() for j in range(len(norm_old_lines))]
            if chunk == norm_old_lines:
                before = "\n".join(content_lines[:i])
                after = "\n".join(content_lines[i + len(norm_old_lines):])
                new_content = before + "\n" + new_string + "\n" + after
                with open(full, "w") as f:
                    f.write(new_content)
                return f"Successfully edited {path} (whitespace-normalized match)"

    return f"Error: old_string not found in {path}. Make sure it exactly matches the file content."


_SEARCH_GLOBS = ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.java",
                  "*.c", "*.h", "*.cpp", "*.rs", "*.go", "*.rb",
                  "*.yaml", "*.yml", "*.toml", "*.cfg", "*.ini", "*.json"]


def _exec_search(args, repo_path, container_id=None):
    pattern = args["pattern"]
    file_glob = args.get("file_glob", "")
    if not file_glob:
        include_args = []
        for g in _SEARCH_GLOBS:
            include_args.extend(["--include", g])
    else:
        include_args = ["--include", file_glob]
    try:
        if container_id:
            grep_cmd = "grep -rn " + " ".join(include_args) + f" '{pattern}' ."
            result = subprocess.run(
                ["docker", "exec", "-w", "/testbed", container_id, "bash", "-c", grep_cmd],
                capture_output=True, text=True, timeout=30,
            )
        else:
            result = subprocess.run(
                ["grep", "-rn"] + include_args + [pattern, "."],
                cwd=repo_path, capture_output=True, text=True, timeout=30,
            )
        output = result.stdout
        lines = output.split("\n")
        if len(lines) > 100:
            output = "\n".join(lines[:100]) + f"\n... ({len(lines) - 100} more lines)"
        return output or "No matches found."
    except subprocess.TimeoutExpired:
        return "Error: search timed out"
    except Exception as e:
        return f"Error: {e}"


def _exec_bash(args, repo_path, container_id=None):
    command = args["command"]
    timeout = args.get("timeout", 120)
    try:
        if container_id:
            result = subprocess.run(
                ["docker", "exec", "-w", "/testbed", container_id, "bash", "-c", command],
                capture_output=True, text=True, timeout=timeout,
            )
        else:
            result = subprocess.run(
                command, shell=True, cwd=repo_path,
                capture_output=True, text=True, timeout=timeout,
            )
        output = result.stdout + result.stderr
        if len(output) > 8000:
            output = output[:4000] + "\n...(truncated)...\n" + output[-4000:]
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {timeout}s"
    except Exception as e:
        return f"Error: {e}"


def _exec_write_file(args, repo_path):
    path = args["path"]
    content = args["content"]
    full = _safe_resolve(repo_path, path)
    if not full:
        return f"Error: invalid path: {path}"
    os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    return f"Successfully wrote {path}"


EXECUTORS = {
    "read_file": _exec_read_file,
    "edit_file": _exec_edit_file,
    "search": _exec_search,
    "bash": _exec_bash,
    "write_file": _exec_write_file,
}


# ---------------------------------------------------------------------------
# ReAct text-mode fallback parser
# ---------------------------------------------------------------------------

_REACT_PATTERN = re.compile(
    r"Action:\s*(\w+)\s*\n\s*Arguments:\s*(\{.*?\})",
    re.DOTALL,
)


def _parse_react(text):
    """Parse ReAct-style text output into (tool_name, args_dict) or None."""
    m = _REACT_PATTERN.search(text)
    if not m:
        return None
    name = m.group(1)
    try:
        args = json.loads(m.group(2))
    except json.JSONDecodeError:
        return None
    return name, args


# ---------------------------------------------------------------------------
# Context management helpers
# ---------------------------------------------------------------------------

def _build_coder_context(analyst_messages, analyst_result, keep_last_reads=3):
    """Extract key file contents from Analyst's exploration for a compact Coder context.

    Instead of passing the full Analyst message history (which can overwhelm
    the model), extract only the last N file read results.
    Returns a string with the key file contents.
    """
    # Walk backwards through messages to find file read results
    file_reads = []
    for msg in reversed(analyst_messages):
        if not isinstance(msg, dict) or msg.get("role") != "tool":
            continue
        content = msg.get("content", "")
        # File read results start with line numbers or are substantial text
        if content and len(content) > 100 and not content.startswith("Error"):
            file_reads.append(content)
            if len(file_reads) >= keep_last_reads:
                break

    if not file_reads:
        return ""

    file_reads.reverse()  # chronological order
    sections = []
    for content in file_reads:
        # Truncate very long reads to ~150 lines
        lines = content.split("\n")
        if len(lines) > 150:
            content = "\n".join(lines[:75]) + \
                f"\n...(truncated {len(lines) - 150} lines)...\n" + \
                "\n".join(lines[-75:])
        sections.append(content)

    return "\n\n---\n\n".join(sections)


def _trim_tool_results(messages, keep_recent=8):
    """Truncate old action result contents to save context space.

    Keeps the last `keep_recent` results intact, truncates older ones
    to first/last 3 lines. Preserves message structure.
    """
    tool_indices = [i for i, m in enumerate(messages)
                    if isinstance(m, dict) and m.get("role") == "tool"]

    if len(tool_indices) <= keep_recent:
        return messages

    to_truncate = set(tool_indices[:-keep_recent])

    result = []
    for i, msg in enumerate(messages):
        if i in to_truncate:
            content = msg.get("content", "")
            if len(content) > 500:
                lines = content.split("\n")
                if len(lines) > 8:
                    truncated = "\n".join(lines[:3]) + \
                        f"\n...(trimmed {len(lines) - 6} lines)...\n" + \
                        "\n".join(lines[-3:])
                else:
                    truncated = content[:200] + "...(trimmed)..." + content[-200:]
                result.append({**msg, "content": truncated})
            else:
                result.append(msg)
        else:
            result.append(msg)

    return result


def _extract_test_errors(output, max_chars=1500):
    """Extract key error lines from verbose test output.

    Returns a compact summary instead of dumping 3000+ chars of raw output.
    """
    lines = output.split("\n")
    failed_tests = []
    error_lines = []
    in_traceback = False
    tb_buffer = []

    for line in lines:
        if re.match(r'^(FAIL|ERROR|FAILED)\b', line):
            failed_tests.append(line.strip())
        elif "FAILED" in line and "::" in line:
            failed_tests.append(line.strip())

        if re.match(r'\s*(AssertionError|TypeError|ValueError|AttributeError|ImportError|KeyError|NameError|RuntimeError)', line):
            error_lines.append(line.rstrip())
        elif line.strip().startswith("E "):
            error_lines.append(line.rstrip())
        elif "raise " in line or "assert " in line:
            error_lines.append(line.rstrip())

        if "Traceback (most recent call last):" in line:
            in_traceback = True
            tb_buffer = [line.rstrip()]
        elif in_traceback:
            tb_buffer.append(line.rstrip())
            if line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                in_traceback = False
                if len(tb_buffer) > 10:
                    tb_buffer = tb_buffer[:2] + ["  ..."] + tb_buffer[-6:]

    parts = []
    if failed_tests:
        parts.append("## Failed tests\n" + "\n".join(failed_tests[:5]))
    if error_lines:
        seen = set()
        unique = []
        for e in error_lines:
            if e.strip() not in seen:
                seen.add(e.strip())
                unique.append(e)
        parts.append("## Key errors\n" + "\n".join(unique[:10]))
    if tb_buffer and not error_lines:
        parts.append("## Last traceback\n" + "\n".join(tb_buffer))
    if not parts:
        tail = "\n".join(lines[-20:])
        parts.append("## Test output (tail)\n" + tail)

    result = "\n\n".join(parts)
    if len(result) > max_chars:
        result = result[:max_chars] + "\n...(truncated)"
    return result


def _extract_edit_context(messages, max_edits=3):
    """Extract edit actions from a Coder round's message history.

    Returns a compact summary of what was edited (file, old→new) so the
    next Coder round understands what was attempted.
    """
    edits = []
    for msg in messages:
        if not isinstance(msg, dict) or msg.get("role") != "assistant":
            continue
        for tc in msg.get("tool_calls", []):
            fn = tc.get("function", {})
            if fn.get("name") != "edit_file":
                continue
            try:
                args = json.loads(fn.get("arguments", "{}"))
            except json.JSONDecodeError:
                continue
            path = args.get("path", "?")
            old = args.get("old_string", "")
            new = args.get("new_string", "")
            # Truncate long strings
            if len(old) > 200:
                old = old[:100] + " ... " + old[-100:]
            if len(new) > 200:
                new = new[:100] + " ... " + new[-100:]
            edits.append(f"File: {path}\n- old: {old}\n+ new: {new}")
            if len(edits) >= max_edits:
                break

    return "\n\n".join(edits) if edits else ""


def _build_analyst_summary(messages):
    """Build an analysis summary from Analyst's actions when it didn't call done.

    Extracts files read and search patterns from the conversation to give
    the Coder a useful starting point instead of 'inconclusive'.
    """
    files_read = []
    searches = []

    for msg in messages:
        if not isinstance(msg, dict):
            continue
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                fn = tc.get("function", tc) if isinstance(tc, dict) else tc
                name = fn.get("name", "")
                args_str = fn.get("arguments", "{}")
                try:
                    args = json.loads(args_str) if isinstance(args_str, str) else args_str
                except json.JSONDecodeError:
                    args = {}
                if name == "read_file":
                    files_read.append(args.get("path", ""))
                elif name == "search":
                    searches.append(args.get("pattern", ""))

    if not files_read:
        return "Analysis inconclusive. Please examine the issue and fix the most likely cause."

    # Deduplicate while preserving order
    seen = set()
    unique_files = []
    for f in files_read:
        if f and f not in seen:
            seen.add(f)
            unique_files.append(f)

    summary = (
        f"The Localizer examined these files: {', '.join(unique_files)}. "
    )
    if searches:
        unique_searches = list(dict.fromkeys(searches))
        summary += f"Search patterns used: {', '.join(unique_searches[:5])}. "
    summary += (
        f"The most likely files to fix: {', '.join(unique_files[-3:])}. "
        f"Please read these files and make the minimal fix."
    )
    return summary


# ---------------------------------------------------------------------------
# BaseAgent — core agent loop
# ---------------------------------------------------------------------------

class BaseAgent:
    """LLM agent that accomplishes tasks through structured actions.

    Works with models that support native function calling (via OpenRouter)
    and falls back to ReAct text parsing for models that don't.
    """

    def __init__(self, config, system_prompt, repo_path,
                 tool_schemas=None, max_steps=30, verbose=True,
                 nudge_at=None, nudge_message=None,
                 restrict_at=None, restrict_to=None,
                 container_id=None):
        self.config = config
        self.system_prompt = system_prompt
        self.repo_path = repo_path
        self.tool_schemas = tool_schemas or ALL_TOOLS
        self.max_steps = max_steps
        self.verbose = verbose
        self.nudge_at = nudge_at
        self.nudge_message = nudge_message
        # Progressive restriction: at restrict_at steps, limit actions to restrict_to
        self.restrict_at = restrict_at
        self.restrict_to = restrict_to
        self.container_id = container_id

    def _execute(self, name, args):
        """Execute an action and return the result string."""
        if name == "done":
            return args.get("message", "Task complete.")
        # Check if action is in allowed schemas
        allowed_names = {t["function"]["name"] for t in self.tool_schemas}
        if name not in allowed_names:
            return f"Error: action '{name}' is not available. Use one of: {', '.join(sorted(allowed_names))}"
        executor = EXECUTORS.get(name)
        if not executor:
            return f"Error: unknown action '{name}'"
        try:
            import inspect
            sig = inspect.signature(executor)
            if "container_id" in sig.parameters:
                return executor(args, self.repo_path, container_id=self.container_id)
            return executor(args, self.repo_path)
        except Exception as e:
            return f"Error executing {name}: {e}"

    def run(self, task, messages=None):
        """Run the agent loop. Returns the final text response or None.

        If messages is provided, continues from that conversation history.
        If task is also given, it is appended as a new user message.
        """
        if messages is None:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": task},
            ]
        elif task:
            messages.append({"role": "user", "content": task})
        self._messages = messages

        tool_step = 0
        empty_streak = 0
        total_empties = 0
        max_empties = 5  # hard cap on total empty responses
        has_edited = False
        readonly_streak = 0
        nudge_count = 0  # track how many read-only nudges fired

        for step in range(self.max_steps * 2):
            if tool_step >= self.max_steps:
                break
            if total_empties >= max_empties or empty_streak >= 3:
                if self.verbose:
                    print(f"  [Bail: {total_empties} empty responses, streak={empty_streak}]")
                break

            # Trim old results periodically to keep context manageable
            if tool_step > 0 and tool_step % 4 == 0:
                messages = _trim_tool_results(messages, keep_recent=6)
                self._messages = messages

            if self.verbose:
                print(f"  [Step {tool_step + 1}/{self.max_steps}]", end="", flush=True)

            response = call_llm_with_tools(messages, self.config, self.tool_schemas)
            msg = response.choices[0].message

            # --- Native function calls ---
            if msg.tool_calls:
                empty_streak = 0
                tool_step += 1

                names = [tc.function.name for tc in msg.tool_calls]
                if self.verbose:
                    print(f" tools: {names}")

                messages.append({
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                })

                for tc in msg.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        args = {}

                    if tc.function.name == "done":
                        if self.verbose:
                            print(f"  [Done] {args.get('message', '')}")
                        return args.get("message", "Task complete.")

                    result = self._execute(tc.function.name, args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })

                # Post-edit nudge: after edit_file, push toward finishing
                if any(tc.function.name == "edit_file" for tc in msg.tool_calls):
                    has_edited = True
                    readonly_streak = 0
                    if tool_step >= 3:  # only after some exploration
                        messages.append({
                            "role": "user",
                            "content": "Good, you've made an edit. Verify with `bash` if needed, then call `done`.",
                        })
                elif all(tc.function.name in ("read_file", "search") for tc in msg.tool_calls):
                    readonly_streak += 1

                # Read-only loop detection: nudge after too many reads without editing
                if not has_edited and readonly_streak >= 3 and tool_step >= 4:
                    nudge_count += 1
                    if nudge_count >= 2:
                        # Hard restriction: remove read/search actions, force edit
                        self.tool_schemas = [
                            t for t in self.tool_schemas
                            if t["function"]["name"] in ("edit_file", "bash", "done")
                        ]
                        messages.append({
                            "role": "user",
                            "content": "STOP reading. I have removed read/search actions. "
                                       "You MUST use `edit_file` now to make the fix, then call `done`.",
                        })
                    else:
                        messages.append({
                            "role": "user",
                            "content": "You have been reading/searching without editing. "
                                       "You have enough context. Use `edit_file` NOW to fix the bug, then call `done`.",
                        })
                    readonly_streak = 0

                # Phase-specific nudge after N steps
                if self.nudge_at and tool_step >= self.nudge_at and self.nudge_message:
                    messages.append({
                        "role": "user",
                        "content": self.nudge_message,
                    })
                    self.nudge_at = None  # only nudge once

                # Progressive restriction: reduce available actions near step limit
                if self.restrict_at and tool_step >= self.restrict_at and self.restrict_to:
                    self.tool_schemas = [
                        t for t in self.tool_schemas
                        if t["function"]["name"] in self.restrict_to
                    ]
                    restrict_names = ", ".join(sorted(self.restrict_to))
                    messages.append({
                        "role": "user",
                        "content": f"You are almost out of steps. Only `{restrict_names}` are available now. Finish up and call `done`.",
                    })
                    self.restrict_at = None  # only restrict once

                continue

            # --- Text-only response: try ReAct fallback ---
            text = msg.content or ""
            parsed = _parse_react(text)

            if parsed:
                name, args = parsed
                empty_streak = 0
                tool_step += 1
                if self.verbose:
                    print(f" react: {name}")

                messages.append({"role": "assistant", "content": text})

                if name == "done":
                    return args.get("message", "Task complete.")

                result = self._execute(name, args)
                messages.append({
                    "role": "user",
                    "content": f"Observation: {result}",
                })
                continue

            # --- Empty or pure-text response ---
            if self.verbose:
                print(f" text ({len(text)} chars)")

            if text and any(phrase in text.lower() for phrase in
                           ["fix is complete", "task is complete", "changes are complete",
                            "analysis is complete", "analysis complete"]):
                return text

            empty_streak += 1
            total_empties += 1

            if empty_streak >= 3:
                messages.append({"role": "assistant", "content": text or "..."})
                messages.append({
                    "role": "user",
                    "content": "You must use the provided actions. Call `done` with your result when finished.",
                })
                empty_streak = 0
            else:
                messages.append({"role": "assistant", "content": text or "..."})
                messages.append({
                    "role": "user",
                    "content": "Continue working on the task.",
                })

        if self.verbose:
            print(f"  [Max steps reached ({self.max_steps})]")
        return None


ToolAgent = BaseAgent  # backward-compatible alias


# ---------------------------------------------------------------------------
# Self-Collaboration Session — Analyst → Coder ↔ Tester loop
# ---------------------------------------------------------------------------

# Role-specific system prompts (parallel to roles/rule_descriptions_actc.py)

TEAM_CONTEXT = """There is a development team that includes a Localizer (Analyst), a Patcher (Coder), and a Verifier (Tester). The team needs to fix real GitHub issues in open-source repositories. The different roles have different divisions of labor and need to cooperate with each other."""

ANALYST_PROMPT = TEAM_CONTEXT + """

You are the **Localizer** on this team. Given a GitHub issue description and the repository structure, your task is to analyze the issue and identify which files and functions need to change.

You have access to: `search`, `read_file`, `bash`, `done`.
Use whichever actions help you understand the issue — search for keywords, read source code, run commands to inspect state, etc.

When you have identified the root cause, call `done` with a JSON analysis:
{"reasoning": "...", "files": [{"path": "file.py", "reason": "..."}]}

IMPORTANT: Your job is ANALYSIS only. Do NOT edit files. Call `done` once you know which files need to change and why.
"""

CODER_PROMPT = TEAM_CONTEXT + """

You are the **Patcher** on this team. You receive a localization analysis from the Localizer{tester_context}. Your task is to make the minimal code fix.

You have access to: `search`, `read_file`, `edit_file`, `bash`, `done`.

Workflow:
1. Read the file(s) identified by the Localizer.
2. Use `edit_file` to fix the bug — `old_string` must EXACTLY match the file content.
3. Optionally use `bash` to run tests and verify your fix.
4. Call `done` when your fix is complete.

Rules:
- Make the SMALLEST change that correctly fixes the bug.
- Do NOT refactor or clean up unrelated code.
- Always read a file before editing it so you can copy exact text for old_string.
"""

TESTER_REPORT_TEMPLATE = """
The verification report from the Verifier is as follows:

Result: {result}
{error_details}

The Patcher must fix the code based on this feedback. Do NOT repeat the same fix that failed."""


class SelfCollabSession:
    """Orchestrates Analyst → Coder ↔ Tester self-collaboration using BaseAgent.

    This preserves the self-collaboration pattern:
    - Three distinct roles with specialized prompts and action sets
    - Structured context passing: Analyst plan → Coder, Test report → Coder
    - Iterative Coder ↔ Tester refinement loop
    - TEAM context shared across all agents

    Key design:
    - No diff generation needed (git diff extracts patch)
    - Each role uses only the actions it needs
    - Tester is deterministic (runs actual tests)
    """

    def __init__(self, config, repo_path, max_round=3,
                 analyst_steps=10, coder_steps=15, verbose=True,
                 container_id=None):
        self.config = config
        self.repo_path = repo_path
        self.max_round = max_round
        self.analyst_steps = analyst_steps
        self.coder_steps = coder_steps
        self.verbose = verbose
        self.container_id = container_id

    def run(self, task_description, test_cmd=None):
        """Run the full self-collaboration loop.

        Args:
            task_description: Issue + repo structure for the analyst.
            test_cmd: Optional test command for the Tester phase.
                      If None, Tester phase is skipped (just Analyst → Coder).

        Returns:
            (session_history, analyst_result, final_coder_result)
        """
        session_history = {}

        # =====================================================================
        # Phase 1: ANALYST — understand the issue, localize files
        # =====================================================================
        if self.verbose:
            print("  === Phase 1: Analyst (Localizer) ===")

        analyst = BaseAgent(
            config=self.config,
            system_prompt=ANALYST_PROMPT,
            repo_path=self.repo_path,
            tool_schemas=ANALYST_TOOLS,
            max_steps=self.analyst_steps,
            verbose=self.verbose,
            nudge_at=self.analyst_steps - 5,
            nudge_message="You are running low on steps. Call `done` NOW with your analysis as JSON:\n{\"reasoning\": \"...\", \"files\": [{\"path\": \"file.py\", \"reason\": \"...\"}]}",
            restrict_at=self.analyst_steps - 3,
            restrict_to={"read_file", "done"},
            container_id=self.container_id,
        )
        analyst_result = analyst.run(task_description)

        if not analyst_result:
            analyst_result = _build_analyst_summary(analyst._messages)

        # Validate JSON format; if not JSON, still usable but log it
        try:
            parsed = json.loads(analyst_result)
            if "files" in parsed:
                analyst_files = [f["path"] for f in parsed["files"]]
            else:
                analyst_files = []
        except (json.JSONDecodeError, TypeError):
            analyst_files = []

        session_history["analyst"] = {"analysis": analyst_result}
        if self.verbose:
            print(f"  Analyst result: {analyst_result[:200]}...")

        # Build Coder context: compact format with key file reads from Analyst
        key_file_contents = _build_coder_context(analyst._messages, analyst_result, keep_last_reads=5)

        # =====================================================================
        # Phase 2 & 3: CODER ↔ TESTER iterative loop
        # =====================================================================
        test_report = None
        coder_result = None
        prev_diff = ""
        prev_coder_messages = []

        for round_idx in range(self.max_round):
            if self.verbose:
                print(f"\n  === Round {round_idx + 1}/{self.max_round}: Coder (Patcher) ===")

            # Build Coder system prompt
            if test_report:
                tester_context = " and a verification report from the Verifier"
            else:
                tester_context = ""
            coder_system = CODER_PROMPT.format(tester_context=tester_context)

            # Build fresh compact context for each round
            if round_idx == 0:
                coder_task = (
                    f"## Localizer's Analysis\n{analyst_result}\n\n"
                    f"## Key File Contents (from Localizer's exploration)\n{key_file_contents}\n\n"
                    f"## Original Issue\n{task_description}\n\n"
                    f"Fix the bug based on the Localizer's analysis. "
                    f"Use `read_file` to review the exact code, then `edit_file` to make the minimal fix."
                )
            else:
                diff_section = f"\n\n## Your previous diff\n```diff\n{prev_diff}\n```" if prev_diff else ""
                # Extract edit context from previous Coder round
                edit_summary = _extract_edit_context(prev_coder_messages)
                edit_section = f"\n\n## What was changed in the previous attempt\n{edit_summary}" if edit_summary else ""
                coder_task = (
                    f"## Localizer's Analysis\n{analyst_result}\n\n"
                    f"## Key File Contents (from Localizer's exploration)\n{key_file_contents}\n\n"
                    f"## Original Issue\n{task_description}\n\n"
                    f"{test_report}{diff_section}{edit_section}\n\n"
                    f"Fix the issue based on the test feedback. "
                    f"The previous fix was incorrect — read the current file state and make a corrected edit."
                )

            coder = BaseAgent(
                config=self.config,
                system_prompt=coder_system,
                repo_path=self.repo_path,
                tool_schemas=ALL_TOOLS,
                max_steps=self.coder_steps,
                verbose=self.verbose,
                nudge_at=self.coder_steps - 5,
                nudge_message="You are running low on steps. Use `edit_file` NOW to make the fix, then call `done`.",
                container_id=self.container_id,
            )
            coder_result = coder.run(coder_task)

            # Capture what the Coder changed (for context in next round)
            if self.container_id:
                diff_result = subprocess.run(
                    ["docker", "exec", "-w", "/testbed", self.container_id, "git", "diff"],
                    capture_output=True, text=True,
                )
            else:
                diff_result = subprocess.run(
                    ["git", "diff"], cwd=self.repo_path,
                    capture_output=True, text=True,
                )
            prev_diff = diff_result.stdout
            prev_coder_messages = coder._messages

            session_history[f"round_{round_idx}"] = {
                "coder": coder_result or "(no response)",
            }

            # Skip tester on last round
            if round_idx == self.max_round - 1:
                break

            # =================================================================
            # TESTER phase — deterministic test execution
            # =================================================================
            if not test_cmd:
                break  # No tests to run, single pass

            if self.verbose:
                print(f"\n  === Round {round_idx + 1}/{self.max_round}: Tester (Verifier) ===")

            status, output = self._run_tests(test_cmd)
            # Check if there's actually a code change
            if self.container_id:
                diff_check = subprocess.run(
                    ["docker", "exec", "-w", "/testbed", self.container_id, "git", "diff"],
                    capture_output=True, text=True,
                )
            else:
                diff_check = subprocess.run(
                    "git diff", shell=True, cwd=self.repo_path,
                    capture_output=True, text=True,
                )
            has_diff = bool(diff_check.stdout.strip())
            if not has_diff:
                status = "failed"
                output = "No code changes were made — nothing to test."
            session_history[f"round_{round_idx}"]["test_passed"] = (status == "passed")
            session_history[f"round_{round_idx}"]["test_output"] = output[:2000]

            if status == "passed":
                if self.verbose:
                    print("  Tests PASSED!")
                break

            # Build test report for next Coder round
            if status == "timeout":
                label = "TIMEOUT"
                detail = f"Test execution timed out. The tests may be hanging or too slow.\n{output}"
            else:
                label = "FAILED"
                detail = f"Test output:\n{_extract_test_errors(output)}"

            if self.verbose:
                print(f"  Tests {label}. Feeding report back to Coder...")

            test_report = TESTER_REPORT_TEMPLATE.format(
                result=label,
                error_details=detail,
            )

        return session_history, analyst_result, coder_result

    def _run_tests(self, test_cmd, timeout=300):
        """Run tests deterministically (no LLM). Returns (status, output).

        status: 'passed', 'failed', or 'timeout'
        """
        try:
            if self.container_id:
                result = subprocess.run(
                    ["docker", "exec", "-w", "/testbed", self.container_id, "bash", "-c", test_cmd],
                    capture_output=True, text=True, timeout=timeout,
                )
            else:
                result = subprocess.run(
                    test_cmd, shell=True, cwd=self.repo_path,
                    capture_output=True, text=True, timeout=timeout,
                )
            output = result.stdout + "\n" + result.stderr
            # Detect "test not found" — FAIL_TO_PASS tests may not exist in base repo
            # Only skip if ALL tests errored with "not found" and total_tests > 0
            if ("no attribute" in output or "not found" in output
                    or "No such file" in output) and result.returncode != 0:
                lines = output.split("\n")
                err_count = sum(1 for l in lines if "ERROR:" in l or "AttributeError" in l)
                total_tests = sum(1 for l in lines if l.strip().startswith("test_"))
                if total_tests > 0 and err_count > 0 and err_count >= total_tests:
                    return "passed", "(tests not in base repo — skipped)"
            if len(output) > 6000:
                output = output[:3000] + "\n...(truncated)...\n" + output[-3000:]
            return ("passed" if result.returncode == 0 else "failed"), output
        except subprocess.TimeoutExpired:
            return "timeout", f"Tests timed out after {timeout}s"
        except Exception as e:
            return "failed", f"Test execution error: {e}"
