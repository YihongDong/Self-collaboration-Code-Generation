"""
SWE-bench runner using Self-Collaboration agent.

Self-collaboration pattern:
- Analyst (Localizer): searches & reads code to understand the issue
- Coder (Patcher): makes minimal edits via edit_file
- Tester (Verifier): runs tests deterministically, feeds failures back to Coder
- Iterative Coder ↔ Tester loop until tests pass or max_round reached

Agent edits files directly, then `git diff` extracts the patch.
"""

import os
import re
import sys
import json
import argparse
import subprocess

import tqdm
from datasets import load_dataset

from core.config import ModelConfig, CODER_CONFIG
from core import repo_tools
from core.agent import SelfCollabSession


# ---------------------------------------------------------------------------
# SWE-bench environment specs (from swebench.harness.constants)
# ---------------------------------------------------------------------------

# Maps repo → {version → {"install": ..., "pip_packages": [...], "test_cmd": ...}}
# Only covers the 12 repos in SWE-bench Lite.

_PY = sys.executable  # use the current interpreter for subprocess calls

_TEST_DJANGO = f"{_PY} ./tests/runtests.py --verbosity 2 --settings=test_sqlite --parallel 1"
_TEST_PYTEST = f"{_PY} -m pytest --no-header -rA --tb=short -p no:cacheprovider"
_TEST_SYMPY  = "PYTHONWARNINGS='ignore::UserWarning,ignore::SyntaxWarning' bin/test -C --verbose"

REPO_SPECS = {
    "django/django": {
        "install": f"{_PY} -m pip install -e . -q",
        "pip_packages": [],
        "test_cmd": _TEST_DJANGO,
        "test_format": "django",   # "test_method (module.Class)" format
    },
    "astropy/astropy": {
        "install": f"{_PY} -m pip install -e .[test] -q --no-build-isolation",
        "pip_packages": ["numpy", "scipy", "pytest-astropy"],
        "test_cmd": _TEST_PYTEST,
    },
    "scikit-learn/scikit-learn": {
        "install": f"{_PY} -m pip install -v --no-use-pep517 --no-build-isolation -e .",
        "pip_packages": ["numpy", "scipy", "cython", "pytest", "joblib", "threadpoolctl"],
        "test_cmd": _TEST_PYTEST,
    },
    "matplotlib/matplotlib": {
        "install": f"{_PY} -m pip install -e . -q",
        "pip_packages": ["numpy", "pytest"],
        "test_cmd": _TEST_PYTEST,
    },
    "sympy/sympy": {
        "install": f"{_PY} -m pip install -e . -q",
        "pip_packages": ["mpmath"],
        "test_cmd": _TEST_SYMPY,
    },
    "pytest-dev/pytest": {
        "install": f"{_PY} -m pip install -e . -q",
        "pip_packages": [],
        "test_cmd": _TEST_PYTEST,
    },
    "sphinx-doc/sphinx": {
        "install": f"{_PY} -m pip install -e .[test] -q",
        "pip_packages": [],
        "test_cmd": _TEST_PYTEST,
    },
    "pylint-dev/pylint": {
        "install": f"{_PY} -m pip install -e . -q",
        "pip_packages": ["astroid"],
        "test_cmd": _TEST_PYTEST,
    },
    "psf/requests": {
        "install": f"{_PY} -m pip install -e . -q",
        "pip_packages": ["pytest"],
        "test_cmd": _TEST_PYTEST,
    },
    "pydata/xarray": {
        "install": f"{_PY} -m pip install -e . -q",
        "pip_packages": ["numpy", "pandas", "pytest"],
        "test_cmd": _TEST_PYTEST,
    },
    "mwaskom/seaborn": {
        "install": f"{_PY} -m pip install -e .[dev] -q",
        "pip_packages": ["numpy", "pandas", "matplotlib"],
        "test_cmd": _TEST_PYTEST,
    },
    "pallets/flask": {
        "install": f"{_PY} -m pip install -e . -q",
        "pip_packages": ["pytest"],
        "test_cmd": _TEST_PYTEST,
    },
}


# ---------------------------------------------------------------------------
# Environment setup
# ---------------------------------------------------------------------------

def _setup_env(repo_path, repo_name, verbose=True):
    """Install project and dependencies using SWE-bench specs."""
    spec = REPO_SPECS.get(repo_name, {})

    # 1. Install pip_packages first (pre-dependencies)
    pip_pkgs = spec.get("pip_packages", [])
    if pip_pkgs:
        cmd = [_PY, "-m", "pip", "install", "-q"] + pip_pkgs
        if verbose:
            print(f"  Installing deps: {' '.join(pip_pkgs[:5])}")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            print(f"  WARNING: dep install failed: {r.stderr[:200]}")

    # 2. Install the project itself
    install_cmd = spec.get("install", f"{_PY} -m pip install -e . -q")
    if verbose:
        print(f"  Installing project: {install_cmd[:60]}")
    r = subprocess.run(
        install_cmd, shell=True, cwd=repo_path,
        capture_output=True, text=True, timeout=300,
    )
    if r.returncode != 0:
        print(f"  WARNING: project install failed: {r.stderr[:200]}")


def _build_test_cmd(instance, repo_path):
    """Build the correct test command using SWE-bench specs.

    Handles project-specific test runners and test name formats:
    - Django: ./tests/runtests.py --settings=test_sqlite <converted_names>
    - Django name format: "test_method (module.Class)" → "module.Class.test_method"
    - Others: pytest <test_names>
    """
    fail_to_pass = instance.get("FAIL_TO_PASS", "[]")
    if isinstance(fail_to_pass, str):
        fail_to_pass = json.loads(fail_to_pass)
    if not fail_to_pass:
        return None

    repo = instance["repo"]
    spec = REPO_SPECS.get(repo, {})
    test_format = spec.get("test_format", "pytest")
    base_cmd = spec.get("test_cmd", _TEST_PYTEST)

    if test_format == "django":
        # Convert "test_method (module.Class)" → "module.Class.test_method"
        converted = []
        for t in fail_to_pass:
            t = t.strip()
            m = re.match(r'^(\w+)\s+\(([^)]+)\)$', t)
            if m:
                method, path = m.group(1), m.group(2)
                converted.append(f"{path}.{method}")
            else:
                converted.append(t)
        test_names = " ".join(converted)
    else:
        test_names = " ".join(fail_to_pass)

    return f"{base_cmd} {test_names}"


# ---------------------------------------------------------------------------
# Test error extraction — compact feedback for Coder
# ---------------------------------------------------------------------------

def _extract_test_errors(output, max_chars=1500):
    """Extract key error lines from verbose test output.

    Parses test output to find:
    1. FAILED/ERROR test names
    2. Assertion errors and tracebacks (last frame only)
    3. Key error messages

    Returns a compact summary instead of dumping 3000+ chars of raw output.
    """
    lines = output.split("\n")

    # Collect sections
    failed_tests = []
    error_lines = []
    in_traceback = False
    tb_buffer = []

    for line in lines:
        # Capture FAILED/ERROR test names
        if re.match(r'^(FAIL|ERROR|FAILED)\b', line):
            failed_tests.append(line.strip())
        elif "FAILED" in line and "::" in line:
            failed_tests.append(line.strip())

        # Capture assertion errors and key exceptions
        if re.match(r'\s*(AssertionError|TypeError|ValueError|AttributeError|ImportError|KeyError|NameError|RuntimeError)', line):
            error_lines.append(line.rstrip())
        elif line.strip().startswith("E "):
            # pytest's error indicator
            error_lines.append(line.rstrip())
        elif "raise " in line or "assert " in line:
            error_lines.append(line.rstrip())

        # Capture the last traceback block
        if "Traceback (most recent call last):" in line:
            in_traceback = True
            tb_buffer = [line.rstrip()]
        elif in_traceback:
            tb_buffer.append(line.rstrip())
            if line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                in_traceback = False
                # Keep only last 8 lines of traceback (the relevant part)
                if len(tb_buffer) > 10:
                    tb_buffer = tb_buffer[:2] + ["  ..."] + tb_buffer[-6:]

    # Build compact error report
    parts = []

    if failed_tests:
        parts.append("## Failed tests\n" + "\n".join(failed_tests[:5]))

    if error_lines:
        # Deduplicate while preserving order
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
        # Fallback: last 20 lines of output (often has the summary)
        tail = "\n".join(lines[-20:])
        parts.append("## Test output (tail)\n" + tail)

    result = "\n\n".join(parts)
    if len(result) > max_chars:
        result = result[:max_chars] + "\n...(truncated)"
    return result


# ---------------------------------------------------------------------------
# Instance runner
# ---------------------------------------------------------------------------

def run_instance(instance, config, work_dir, max_round=3, max_steps=10, verbose=True):
    """Run self-collaboration on a single SWE-bench instance. Returns (patch, history)."""
    instance_id = instance["instance_id"]

    # 1. Clone and setup
    try:
        repo_path = repo_tools.clone_repo(instance["repo"], instance["base_commit"], work_dir)
    except Exception as e:
        print(f"  Failed to clone: {e}")
        return "", {}

    # 1b. Install project and dependencies (using SWE-bench specs)
    _setup_env(repo_path, instance["repo"], verbose=verbose)

    structure = repo_tools.get_repo_structure(repo_path)

    # 2. Build task description for Analyst
    hints = instance.get("hints_text", "")
    hints_section = f"\n\n## Hints\n{hints}" if hints else ""

    # Include fail-to-pass test names so the agent knows what to target
    fail_to_pass = instance.get("FAIL_TO_PASS", "[]")
    if isinstance(fail_to_pass, str):
        fail_to_pass = json.loads(fail_to_pass)
    test_section = ""
    if fail_to_pass:
        test_section = f"\n\n## Tests That Should Pass After Fix\n" + "\n".join(f"- {t}" for t in fail_to_pass)

    task = f"""## Repository Structure
```
{structure}
```

## Issue
{instance['problem_statement']}
{hints_section}{test_section}"""

    # 3. Build test command (project-specific runner)
    test_cmd = _build_test_cmd(instance, repo_path)
    if verbose and test_cmd:
        print(f"  Test cmd: {test_cmd[:120]}")

    # 4. Run self-collaboration session
    session = SelfCollabSession(
        config=config,
        repo_path=repo_path,
        max_round=max_round,
        analyst_steps=max_steps,
        coder_steps=max_steps,
        verbose=verbose,
    )
    history, analyst_result, coder_result = session.run(task, test_cmd=test_cmd)

    # 5. Extract patch via git diff
    result = subprocess.run(
        ["git", "diff"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    patch = result.stdout

    # 6. Reset repo for next run
    repo_tools.reset_repo(repo_path, instance["base_commit"])

    return patch, history


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="SWE-bench: Self-collaboration agent")
    parser.add_argument("--split", type=str, default="test")
    parser.add_argument("--output_path", type=str, default="swe_v2_predictions.jsonl")
    parser.add_argument("--work_dir", type=str, default="swe_workdir")
    parser.add_argument("--max_round", type=int, default=3,
                        help="Max Coder-Tester rounds (default: 3)")
    parser.add_argument("--max_steps", type=int, default=10,
                        help="Max steps per agent phase (default: 10)")
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--instance_ids", type=str, nargs="+", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    config = CODER_CONFIG
    if args.model:
        config = ModelConfig(model=args.model, max_tokens=16384)

    print("Loading SWE-bench Lite dataset...")
    dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split=args.split)

    if args.instance_ids:
        id_set = set(args.instance_ids)
        dataset = [inst for inst in dataset if inst["instance_id"] in id_set]
        print(f"Filtered to {len(dataset)} instances")

    model_name = config.model
    print(f"Model: {model_name} | Max rounds: {args.max_round} | Steps/phase: {args.max_steps}")
    print(f"Output: {args.output_path}")

    with open(args.output_path, "w+") as f:
        pbar = tqdm.tqdm(dataset, total=len(dataset))
        for instance in pbar:
            instance_id = instance["instance_id"]
            pbar.set_description(instance_id)

            patch, history = run_instance(
                instance, config, args.work_dir,
                max_round=args.max_round,
                max_steps=args.max_steps,
                verbose=not args.quiet,
            )

            if not patch.strip():
                print(f"  {instance_id}: no patch generated")
                continue

            prediction = {
                "instance_id": instance_id,
                "model_name_or_path": model_name,
                "model_patch": patch,
                "session_history": history,
            }
            f.write(json.dumps(prediction) + "\n")
            f.flush()
            print(f"  {instance_id}: patch generated ({len(patch)} chars)")

    print(f"\nDone. Predictions written to {args.output_path}")


if __name__ == "__main__":
    main()
