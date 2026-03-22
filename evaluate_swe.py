"""
Evaluate SWE-bench predictions.

Usage:
    # Local evaluation (no Docker needed)
    python3 evaluate_swe.py --predictions swe_predictions.jsonl

    # Official Docker evaluation (requires Docker)
    python3 evaluate_swe.py --predictions swe_predictions.jsonl --docker
"""

import json
import argparse
import sys
import os


def evaluate_local(predictions_path):
    """Evaluate predictions based on local test results in session_history."""
    predictions = []
    with open(predictions_path) as f:
        for line in f:
            line = line.strip()
            if line:
                predictions.append(json.loads(line))

    total = len(predictions)
    has_patch = 0
    tests_passed = 0
    tests_failed = 0
    tests_skipped = 0

    print(f"{'Instance':<40} {'Patch':>6} {'Test':>10}")
    print("-" * 60)

    for pred in predictions:
        iid = pred["instance_id"]
        patch = pred.get("model_patch", "")
        history = pred.get("session_history", {})

        patch_ok = bool(patch.strip())
        if patch_ok:
            has_patch += 1

        # Check test results across rounds
        test_status = "N/A"
        for key in sorted(history.keys()):
            if isinstance(history[key], dict) and "test_passed" in history[key]:
                if history[key]["test_passed"]:
                    test_status = "PASSED"
                    tests_passed += 1
                    break
                else:
                    test_status = "FAILED"
        if test_status == "FAILED":
            tests_failed += 1
        elif test_status == "N/A":
            tests_skipped += 1

        print(f"{iid:<40} {'Y' if patch_ok else 'N':>6} {test_status:>10}")

    print("-" * 60)
    print(f"Total instances:    {total}")
    print(f"Patches generated:  {has_patch}/{total} ({has_patch/total*100:.0f}%)" if total else "")
    print(f"Tests passed:       {tests_passed}/{total}")
    print(f"Tests failed:       {tests_failed}/{total}")
    print(f"Tests skipped/N/A:  {tests_skipped}/{total}")
    print()
    print("NOTE: This is local evaluation only. For official results,")
    print("      use --docker flag (requires Docker installed).")


def evaluate_docker(predictions_path, dataset_name, split, max_workers, timeout):
    """Evaluate predictions using official swebench Docker harness."""
    try:
        from swebench.harness.run_evaluation import run_instances
        from swebench.harness.test_spec.test_spec import make_test_spec
        from swebench.harness.utils import load_swebench_dataset
        import docker
        docker.from_env().ping()
    except ImportError:
        print("ERROR: swebench or docker package not installed.")
        print("  pip install swebench docker")
        sys.exit(1)
    except Exception:
        print("ERROR: Docker is not running. Start Docker Desktop first.")
        sys.exit(1)

    # Load predictions
    predictions = {}
    with open(predictions_path) as f:
        for line in f:
            line = line.strip()
            if line:
                pred = json.loads(line)
                predictions[pred["instance_id"]] = pred

    if not predictions:
        print("No predictions to evaluate.")
        return

    # Load dataset instances matching predictions
    dataset = load_swebench_dataset(dataset_name, split)
    instances = [inst for inst in dataset if inst["instance_id"] in predictions]

    print(f"Evaluating {len(instances)} instances with Docker...")
    print(f"Dataset: {dataset_name} | Split: {split}")
    print(f"Max workers: {max_workers} | Timeout: {timeout}s")

    run_id = os.path.basename(predictions_path).replace(".jsonl", "")
    run_instances(
        predictions=predictions,
        instances=instances,
        cache_level="env",
        clean=False,
        force_rebuild=False,
        max_workers=max_workers,
        run_id=run_id,
        timeout=timeout,
    )

    # Collect results
    from pathlib import Path
    from swebench.harness.constants import RUN_EVALUATION_LOG_DIR, LOG_REPORT

    log_dir = RUN_EVALUATION_LOG_DIR / run_id
    resolved = 0
    total = 0
    for inst_id in predictions:
        model_name = predictions[inst_id].get("model_name_or_path", "None").replace("/", "__")
        report_path = log_dir / model_name / inst_id / LOG_REPORT
        if report_path.exists():
            report = json.loads(report_path.read_text())
            total += 1
            if report.get(inst_id, {}).get("resolved", False):
                resolved += 1
                print(f"  {inst_id}: RESOLVED")
            else:
                print(f"  {inst_id}: NOT RESOLVED")

    print(f"\nResults: {resolved}/{total} resolved ({resolved/total*100:.1f}%)" if total else "")


def main():
    parser = argparse.ArgumentParser(description="Evaluate SWE-bench predictions")
    parser.add_argument("--predictions", type=str, required=True,
                        help="Path to predictions JSONL file")
    parser.add_argument("--docker", action="store_true",
                        help="Use official Docker evaluation (requires Docker)")
    parser.add_argument("--dataset", type=str, default="princeton-nlp/SWE-bench_Lite")
    parser.add_argument("--split", type=str, default="test")
    parser.add_argument("--max_workers", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()

    if not os.path.exists(args.predictions):
        print(f"ERROR: {args.predictions} not found")
        sys.exit(1)

    if args.docker:
        evaluate_docker(args.predictions, args.dataset, args.split,
                        args.max_workers, args.timeout)
    else:
        evaluate_local(args.predictions)


if __name__ == "__main__":
    main()
