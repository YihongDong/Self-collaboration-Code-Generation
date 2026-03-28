"""
HumanEval runner using Self-Collaboration agent.

Self-collaboration pattern:
- Analyst: decomposes the requirement into a plan
- Coder: implements code based on the plan
- Tester: generates test cases from the prompt (NOT using private test suite)
- Iterative Coder ↔ Tester loop

Uses write_file + bash actions for code generation and testing.
"""

import os
import sys
import json
import argparse
import subprocess

import tqdm
from datasets import load_dataset

from core.config import ModelConfig, CODER_CONFIG
from core.backend import call_llm_with_tools
from core.agent import ToolAgent as BaseAgent, HUMANEVAL_TOOL_SCHEMAS
from core.utils import prompt_split_humaneval, find_method_name

# ---------------------------------------------------------------------------
# Role-specific system prompts
# ---------------------------------------------------------------------------

TEAM_CONTEXT = """There is a development team that includes a requirement analyst, a Python developer, and a tester. The team needs to develop programs that satisfy the requirement of the users. The different roles have different divisions of labor and need to cooperate with each others."""

ANALYST_PROMPT = TEAM_CONTEXT + """

You are the **Requirement Analyst** on this team. Given a programming requirement, your task is:

1. Analyze the requirement and identify key subproblems.
2. Develop a high-level plan with major implementation steps.
3. Identify edge cases and potential pitfalls.

Respond with a clear, concise plan in JSON format:
{"plan": "step-by-step plan", "edge_cases": ["case1", "case2"], "approach": "description of algorithm/approach"}
"""

CODER_PROMPT = TEAM_CONTEXT + """

You are the **Python Developer** on this team.{context_source}

Your task:
1. Use `write_file` to write the complete Python implementation to `solution.py`.
2. Use `bash` to test it: `python -c "from solution import {entry_point}; print('OK')"`
3. Call `done` when the implementation is correct.

Rules:
- Write clean, correct Python code
- Handle edge cases identified in the plan
- The function must match the given signature exactly
- Test your code before calling done
"""

TESTER_PROMPT = TEAM_CONTEXT + """

You are the **Tester** on this team. You will receive the code written by the developer, and your job is:
1. Write test code that starts with "def check(candidate):" where candidate is a function object.
2. Call candidate with different inputs (up to five) that start with "print", and do not write assert statements.

Remember, you only need to provide the test code in Python and avoid using assert statements.
"""

TESTER_INSTRUCTION = "The code provided by developer is as follows:\n{code}\n"

TESTER_FEEDBACK = """
The report from the Tester is as follows:

Result: {result}
{error_details}

Fix the code based on this feedback. Do NOT repeat the same mistake."""


def run_task(task, config, work_dir, max_round=2, max_steps=10, verbose=True):
    """Run self-collaboration on a single HumanEval task. Returns the generated code."""
    task_id = task["task_id"]
    prompt = task["prompt"]
    entry_point = task["entry_point"]

    # Create a working directory for this task
    task_dir = os.path.join(work_dir, task_id.replace("/", "_"))
    os.makedirs(task_dir, exist_ok=True)

    requirement = f"""```python
{prompt}
```

The function name must be `{entry_point}`."""

    # =========================================================================
    # Phase 1: ANALYST — analyze requirement, make plan
    # =========================================================================
    if verbose:
        print("  === Analyst ===", end="", flush=True)

    analyst_messages = [
        {"role": "system", "content": ANALYST_PROMPT},
        {"role": "user", "content": f"Analyze this requirement and create an implementation plan:\n\n{requirement}"},
    ]

    response = call_llm_with_tools(analyst_messages, config, tools=None)
    analyst_plan = response.choices[0].message.content or ""
    if verbose:
        print(f" plan ({len(analyst_plan)} chars)")

    # =========================================================================
    # Phase 2 & 3: CODER ↔ TESTER iterative loop
    # =========================================================================
    test_report = None

    for round_idx in range(max_round):
        if verbose:
            print(f"  === Round {round_idx + 1}/{max_round}: Coder ===")

        # Build Coder context
        if test_report:
            context_source = " You receive a test report from the Tester"
            coder_task = (
                f"## Plan from the Analyst\n{analyst_plan}\n\n"
                f"## Requirement\n{requirement}\n\n"
                f"{test_report}\n\n"
                f"Fix the implementation based on the test feedback."
            )
        else:
            context_source = " You receive a plan from the Analyst"
            coder_task = (
                f"## Plan from the Analyst\n{analyst_plan}\n\n"
                f"## Requirement\n{requirement}\n\n"
                f"Implement the function based on the Analyst's plan."
            )

        coder_system = CODER_PROMPT.format(
            context_source=context_source,
            entry_point=entry_point,
        )

        coder = BaseAgent(
            config=config,
            system_prompt=coder_system,
            repo_path=task_dir,
            tool_schemas=HUMANEVAL_TOOL_SCHEMAS,
            max_steps=max_steps,
            verbose=verbose,
        )
        coder.run(coder_task)

        # Skip tester on last round
        if round_idx == max_round - 1:
            break

        # =================================================================
        # TESTER phase — LLM generates tests from prompt (not private tests)
        # =================================================================
        if verbose:
            print(f"  === Round {round_idx + 1}/{max_round}: Tester ===", end="", flush=True)

        solution_path = os.path.join(task_dir, "solution.py")
        if not os.path.exists(solution_path):
            if verbose:
                print(" no solution.py found")
            test_report = TESTER_FEEDBACK.format(
                result="ERROR",
                error_details="No solution.py file was written. Use write_file to create it.",
            )
            continue

        with open(solution_path, "r") as f:
            code = f.read()

        # Ask LLM Tester to generate test cases from the code + prompt
        tester_test_code = _generate_tests(config, requirement, code)

        if not tester_test_code:
            if verbose:
                print(" tester produced no tests")
            continue

        # Execute the LLM-generated tests
        passed, output = _run_generated_test(task_dir, tester_test_code, entry_point)

        if verbose:
            print(f" {'PASSED' if passed else 'FAILED'}")

        if passed:
            break

        test_report = TESTER_FEEDBACK.format(
            result="FAILED",
            error_details=f"Test output:\n{output[:2000]}",
        )

    # Read the solution file
    solution_path = os.path.join(task_dir, "solution.py")
    if not os.path.exists(solution_path):
        return ""

    with open(solution_path, "r") as f:
        code = f.read()

    return code


def _generate_tests(config, requirement, code):
    """Ask LLM Tester to generate test cases from the prompt and code.

    Returns the test code string (def check(candidate): ...) or empty string.
    """
    tester_messages = [
        {"role": "system", "content": TESTER_PROMPT},
        {"role": "user", "content": (
            f"## Requirement\n{requirement}\n\n"
            f"{TESTER_INSTRUCTION.format(code=code)}"
        )},
    ]

    try:
        response = call_llm_with_tools(tester_messages, config, tools=None)
        test_code = response.choices[0].message.content or ""

        # Extract code from markdown blocks if present
        if "```python" in test_code:
            start = test_code.index("```python") + len("```python")
            end = test_code.index("```", start)
            test_code = test_code[start:end].strip()
        elif "```" in test_code:
            start = test_code.index("```") + 3
            end = test_code.index("```", start)
            test_code = test_code[start:end].strip()

        # Validate it contains check function
        if "def check" not in test_code:
            return ""

        return test_code
    except Exception:
        return ""


def _run_generated_test(task_dir, test_code, entry_point, timeout=30):
    """Run LLM-generated tests. Returns (passed, output)."""
    test_script = f"""
import sys
sys.path.insert(0, '.')
from solution import {entry_point}

{test_code}

try:
    check({entry_point})
    print("ALL TESTS PASSED")
except Exception as e:
    print(f"TEST FAILED: {{e}}")
    sys.exit(1)
"""
    test_path = os.path.join(task_dir, "_test_runner.py")
    with open(test_path, "w") as f:
        f.write(test_script)

    try:
        result = subprocess.run(
            [sys.executable, test_path],
            cwd=task_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, f"Test timed out after {timeout}s"
    except Exception as e:
        return False, f"Test error: {e}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="HumanEval: Self-collaboration agent")
    parser.add_argument("--output_path", type=str, default="humaneval_output.jsonl")
    parser.add_argument("--work_dir", type=str, default="humaneval_workdir")
    parser.add_argument("--max_round", type=int, default=2,
                        help="Max Coder-Tester rounds (default: 2)")
    parser.add_argument("--max_steps", type=int, default=10,
                        help="Max steps per Coder phase (default: 10)")
    parser.add_argument("--max_samples", type=int, default=None,
                        help="Limit number of tasks to run")
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    config = CODER_CONFIG
    if args.model:
        config = ModelConfig(model=args.model, max_tokens=16384)

    print("Loading HumanEval dataset...")
    dataset = load_dataset("openai_humaneval", split="test")

    if args.max_samples:
        dataset = list(dataset)[:args.max_samples]

    model_name = config.model
    print(f"Model: {model_name} | Max rounds: {args.max_round} | Steps/phase: {args.max_steps}")
    print(f"Output: {args.output_path}")

    with open(args.output_path, "w+") as f:
        pbar = tqdm.tqdm(dataset, total=len(dataset))
        for task in pbar:
            task_id = task["task_id"]
            pbar.set_description(task_id)

            try:
                code = run_task(
                    task, config, args.work_dir,
                    max_round=args.max_round,
                    max_steps=args.max_steps,
                    verbose=not args.quiet,
                )
            except Exception as e:
                print(f"  {task_id}: error: {e}")
                continue

            if not code.strip():
                print(f"  {task_id}: no code generated")
                continue

            method_name = task["entry_point"]
            before_func = task["prompt"][:task["prompt"].rfind("def ")]

            entry_point_found = find_method_name(code)
            solution = {
                "task_id": task_id,
                "prompt": before_func + "\n",
                "test": task["test"],
                "entry_point": entry_point_found or method_name,
                "completion": code,
            }
            f.write(json.dumps(solution) + "\n")
            f.flush()

    print(f"\nDone. Output written to {args.output_path}")


if __name__ == "__main__":
    main()
