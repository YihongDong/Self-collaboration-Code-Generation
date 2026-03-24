"""
SWE-bench Docker evaluator.

Runs inside swe-collab container (Python 3.11). Controls Epoch AI pre-built
ARM64 containers via Docker socket for agent execution + evaluation.

Architecture:
  swe-collab container (this script, Python 3.11)
    │ docker exec
    ▼
  epoch ARM64 container (correct Python + deps + repo at /testbed)

Evaluation uses the official swebench eval_script + grading when available,
falling back to test_cmd execution otherwise.

Usage:
  ./run_swe_docker.sh --instance_ids django__django-15400
"""

import os
import json
import shlex
import argparse
import datetime
import subprocess
import platform
from pathlib import Path

# Load .env BEFORE any config imports
if os.path.exists(".env"):
    for line in open(".env"):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k, v)

import tqdm
from datasets import load_dataset

from core.config import ModelConfig, CODER_CONFIG
from core.agent import SelfCollabSession

# swebench grading — each import isolated to avoid false HAS_SWEBENCH=False
HAS_SWEBENCH_SPEC = False
HAS_SWEBENCH_GRADE = False
try:
    from swebench.harness.test_spec.test_spec import make_test_spec  # type: ignore[import]
    HAS_SWEBENCH_SPEC = True
except ImportError:
    pass
try:
    from swebench.harness.grading import get_eval_report  # type: ignore[import]
    HAS_SWEBENCH_GRADE = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Docker helpers
# ---------------------------------------------------------------------------

DOCKER_WORKDIR = "/testbed"


def _detect_arch():
    """Detect architecture from Docker daemon, not from current process."""
    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{.Architecture}}"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            raise RuntimeError(f"docker info failed: {result.stderr.strip()}")
        arch = result.stdout.strip()
        if not arch:
            raise RuntimeError("docker info returned empty architecture")
        if "arm" in arch or "aarch" in arch:
            return "arm64"
        return "x86_64"
    except Exception as e:
        fallback = "arm64" if platform.machine() in ("arm64", "aarch64") else "x86_64"
        print(f"  WARNING: arch detection failed ({e}), falling back to {fallback}")
        return fallback


_cfg = {"arch": _detect_arch()}


def get_image_name(instance_id):
    return f"ghcr.io/epoch-research/swe-bench.eval.{_cfg['arch']}.{instance_id}:latest"


def _image_cache():
    """Cache available images. Raises RuntimeError if Docker daemon is unreachable."""
    if not hasattr(_image_cache, "_set"):
        result = subprocess.run(
            ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Docker daemon error: {result.stderr.strip()}")
        _image_cache._set = set(result.stdout.strip().split("\n")) - {""}
    return _image_cache._set


def image_exists(instance_id):
    """Check if image exists locally, try pulling if not."""
    image = get_image_name(instance_id)
    if image in _image_cache():
        return True
    # Try pulling
    print(f"  Pulling {image}...")
    result = subprocess.run(
        ["docker", "pull", image],
        capture_output=True, text=True, timeout=300,
    )
    if result.returncode == 0:
        _image_cache._set.add(image)
        return True
    return False


def start_container(instance_id, run_id):
    """Start epoch container. Returns container_id."""
    image = get_image_name(instance_id)
    name = f"swe-{run_id}-{instance_id}"[:63]
    result = subprocess.run(
        ["docker", "run", "-d", "--name", name, image, "tail", "-f", "/dev/null"],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to start: {result.stderr}")
    return result.stdout.strip()[:12]


def stop_container(container_id):
    subprocess.run(["docker", "rm", "-f", container_id],
                   capture_output=True, text=True, timeout=15)


def exec_in(cid, cmd, timeout=120):
    """Execute command in container. Returns (returncode, output)."""
    try:
        result = subprocess.run(
            ["docker", "exec", "-w", DOCKER_WORKDIR, cid, "bash", "-c", cmd],
            capture_output=True, text=True, timeout=timeout,
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 124, f"Command timed out after {timeout}s: {cmd[:80]}"


def safe_test_names(names):
    """Shell-escape test identifiers to prevent injection."""
    return " ".join(shlex.quote(n) for n in names)


def _is_output_path_persisted(output_path):
    """Only allow outputs under mounted logs/ to avoid container-local data loss."""
    p = Path(os.path.normpath(str(output_path)))
    if p.is_absolute():
        p = p.resolve()
        logs_abs = Path("/app/logs").resolve()
        return p == logs_abs or logs_abs in p.parents
    parts = p.parts
    return bool(parts) and parts[0] == "logs"


# ---------------------------------------------------------------------------
# Test command builder — uses eval_script when available
# ---------------------------------------------------------------------------

def build_test_cmd(instance, cid):
    """Build test command. Prefers swebench eval_script, falls back to heuristic.

    Returns (test_cmd, eval_script, test_spec_or_None).
    """
    fail_to_pass = instance.get("FAIL_TO_PASS", "[]")
    if isinstance(fail_to_pass, str):
        fail_to_pass = json.loads(fail_to_pass)

    eval_script = None
    test_spec = None
    if HAS_SWEBENCH_SPEC:
        try:
            test_spec = make_test_spec(instance)
            eval_script = test_spec.eval_script
        except Exception:
            pass

    # Keep official evaluation path available even when no FAIL_TO_PASS is listed.
    if not fail_to_pass:
        return None, eval_script, test_spec

    if eval_script:
        for line in eval_script.split("\n"):
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("set") \
                    and not stripped.startswith("cd") and not stripped.startswith("git") \
                    and not stripped.startswith("source") and not stripped.startswith("conda") \
                    and not stripped.startswith("export"):
                if "pytest" in stripped or "runtests" in stripped or "bin/test" in stripped:
                    return stripped, eval_script, test_spec

    # Fallback: heuristic
    escaped = safe_test_names(fail_to_pass)
    rc, _ = exec_in(cid, "test -f tests/runtests.py", timeout=5)
    if rc == 0:
        return f"python tests/runtests.py --verbosity 2 --settings=test_sqlite --parallel 1 {escaped}", eval_script, test_spec
    return f"python -m pytest --no-header -rA --tb=short {escaped}", eval_script, test_spec


# ---------------------------------------------------------------------------
# Evaluation — official grading when available
# ---------------------------------------------------------------------------

def evaluate_patch(instance, cid, patch, eval_script, test_spec, log_dir, safe_model_name, timeout):
    """Evaluate using official swebench grading if available, else return None for fallback."""
    instance_id = instance["instance_id"]

    if eval_script and test_spec and HAS_SWEBENCH_GRADE:
        try:
            eval_path = log_dir / "eval.sh"
            eval_path.write_text(eval_script)
            cp_result = subprocess.run(
                ["docker", "cp", str(eval_path), f"{cid}:/eval.sh"],
                capture_output=True, text=True, timeout=10,
            )
            if cp_result.returncode != 0:
                raise RuntimeError(f"docker cp failed: {cp_result.stderr}")
            rc, test_output = exec_in(cid, "/bin/bash /eval.sh", timeout=timeout)
            if not test_output.strip():
                raise RuntimeError("eval script produced no output")
            test_output_path = log_dir / "test_output.txt"
            test_output_path.write_text(test_output)

            pred = {
                "instance_id": instance_id,
                "model_name_or_path": safe_model_name,
                "model_patch": patch,
            }
            report = get_eval_report(
                test_spec=test_spec, prediction=pred,
                test_log_path=test_output_path, include_tests_status=True,
            )
            (log_dir / "report.json").write_text(json.dumps(report, indent=2))

            return report.get(instance_id, {}).get("resolved", False)
        except RuntimeError as e:
            print(f"    Eval environment error (not a test failure): {e}")
        except Exception as e:
            print(f"    Grading error, falling back to rc check: {e}")

    return None


# ---------------------------------------------------------------------------
# Per-instance runner
# ---------------------------------------------------------------------------

def run_instance_docker(instance, config, run_id, safe_model_name,
                        max_round=2, max_steps=12, timeout=300, verbose=True):
    """Run agent inside epoch Docker container, then evaluate."""
    instance_id = instance["instance_id"]

    if not image_exists(instance_id):
        if verbose:
            print(f"  {instance_id}: SKIP (image not found)")
        return instance_id, False, "", "skipped"

    log_dir = Path("logs") / run_id / safe_model_name / instance_id
    log_dir.mkdir(parents=True, exist_ok=True)

    cid = None
    try:
        # 1. Start container
        if verbose:
            print(f"  Starting container...")
        cid = start_container(instance_id, run_id)
        _, py_ver = exec_in(cid, "python --version", timeout=5)
        if verbose:
            print(f"  Container {cid} | {py_ver.strip()}")

        # 2. Repo structure
        _, structure = exec_in(cid, "find . -maxdepth 3 -type f -name '*.py' | head -80", timeout=10)

        # 3. Task description
        hints = instance.get("hints_text", "")
        hints_section = f"\n\n## Hints\n{hints}" if hints else ""
        fail_to_pass = instance.get("FAIL_TO_PASS", "[]")
        if isinstance(fail_to_pass, str):
            fail_to_pass = json.loads(fail_to_pass)
        test_section = ""
        if fail_to_pass:
            test_section = "\n\n## Tests That Should Pass After Fix\n" + \
                "\n".join(f"- {t}" for t in fail_to_pass)

        task = f"""## Repository Structure
```
{structure[:3000]}
```

## Issue
{instance['problem_statement']}
{hints_section}{test_section}"""

        # 4. Build test command
        test_cmd, eval_script, test_spec = build_test_cmd(instance, cid)
        if verbose and test_cmd:
            print(f"  Test: {test_cmd[:100]}")
        if verbose and eval_script:
            print(f"  Official eval_script available ({len(eval_script)} chars)")

        # 5. Run agent — all ops docker exec to epoch container
        session = SelfCollabSession(
            config=config,
            repo_path=DOCKER_WORKDIR,
            max_round=max_round,
            analyst_steps=max_steps,
            coder_steps=max_steps,
            verbose=verbose,
            container_id=cid,
        )
        history, analyst_result, coder_result = session.run(task, test_cmd=test_cmd)

        # 6. Extract patch
        _, patch = exec_in(cid, "git diff", timeout=10)

        if not patch.strip():
            if verbose:
                print(f"  {instance_id}: no patch")
            return instance_id, False, "", "skipped"

        (log_dir / "patch.diff").write_text(patch)
        if verbose:
            print(f"  Patch: {len(patch)} chars")

        # 7. Evaluate with official grading
        if verbose:
            print(f"  Evaluating...")
        resolved = evaluate_patch(instance, cid, patch, eval_script, test_spec, log_dir, safe_model_name, timeout)

        # Fallback if official grading didn't work
        grading_method = "official"
        if resolved is None and test_cmd:
            rc, test_output = exec_in(cid, test_cmd, timeout=timeout)
            (log_dir / "test_output.txt").write_text(test_output)
            resolved = rc == 0
            grading_method = "rc_fallback"
            (log_dir / "grading_method.txt").write_text("rc_fallback: non-comparable with official SWE-bench")
        elif resolved is None:
            # No eval was performed (no test_cmd, no eval_script)
            grading_method = "no_eval"

        resolved = bool(resolved) if resolved is not None else False
        if verbose:
            tag = "" if grading_method == "official" else f" [{grading_method}]"
            print(f"  {instance_id}: {'RESOLVED' if resolved else 'FAILED'}{tag}")
        return instance_id, resolved, patch, grading_method

    except Exception as e:
        if verbose:
            print(f"  {instance_id}: ERROR - {e}")
        return instance_id, False, "", "error"
    finally:
        if cid:
            stop_container(cid)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="SWE-bench: Self-collaboration agent in Docker")
    parser.add_argument("--split", type=str, default="test")
    parser.add_argument("--output_path", type=str, default="logs/swe_predictions.jsonl",
                        help="Output predictions file (use logs/ prefix to ensure it's mounted)")
    parser.add_argument("--max_round", type=int, default=2)
    parser.add_argument("--max_steps", type=int, default=12)
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--instance_ids", type=str, nargs="+", default=None)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--arch", type=str, default=None,
                        help="Image architecture override (default: auto-detect)")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if not _is_output_path_persisted(args.output_path):
        raise ValueError(
            f"output_path must be under logs/ (mounted to host). Got: {args.output_path}"
        )

    # Override arch if specified
    if args.arch:
        _cfg["arch"] = args.arch

    config = CODER_CONFIG
    if args.model:
        config = ModelConfig(model=args.model, max_tokens=16384)

    model_name = config.model
    safe_model_name = model_name.replace("/", "__").replace(":", "_")

    print("Loading SWE-bench Lite dataset...")
    dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split=args.split)

    if args.instance_ids:
        id_set = set(args.instance_ids)
        instances = [inst for inst in dataset if inst["instance_id"] in id_set]
    else:
        instances = list(dataset)

    print(f"Instances: {len(instances)} | Model: {model_name} | Arch: {_cfg['arch']}")
    if HAS_SWEBENCH_GRADE and HAS_SWEBENCH_SPEC:
        print(f"  swebench grading: available")
    elif HAS_SWEBENCH_SPEC:
        print(f"  swebench grading: partial (spec only, no grading)")
    else:
        print(f"  swebench grading: not available (fallback to rc check)")

    available = [inst for inst in instances if image_exists(inst["instance_id"])]
    missing = [inst["instance_id"] for inst in instances if not image_exists(inst["instance_id"])]
    if missing:
        print(f"  Missing images: {', '.join(missing[:5])}")
    print(f"  Ready: {len(available)}/{len(instances)}")

    if not available:
        print("No instances to run.")
        return

    run_id = datetime.datetime.now().strftime("collab_%Y%m%d_%H%M%S")
    print(f"\n=== Running {len(available)} instances ===")

    results = []
    Path(args.output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_path, "w") as f:
        for instance in tqdm.tqdm(available, desc="Instances"):
            iid, resolved, patch, grading = run_instance_docker(
                instance, config, run_id, safe_model_name,
                max_round=args.max_round, max_steps=args.max_steps,
                timeout=args.timeout, verbose=not args.quiet,
            )
            results.append((iid, resolved, grading))
            if patch.strip():
                f.write(json.dumps({
                    "instance_id": iid,
                    "model_name_or_path": safe_model_name,
                    "model_patch": patch,
                    "grading_method": grading,
                }) + "\n")
                f.flush()

    print(f"\n=== Results ===")
    resolved_count = sum(1 for _, r, _ in results if r)
    for iid, resolved, grading in results:
        tag = "" if grading == "official" else f" [{grading}]"
        print(f"  {iid}: {'RESOLVED' if resolved else 'FAILED'}{tag}")
    print(f"\nResolved: {resolved_count}/{len(results)}")


if __name__ == "__main__":
    main()
