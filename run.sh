#!/bin/bash
# Run HumanEval benchmark
set -a; source .env; set +a

python3 run_humaneval.py \
    --output_path humaneval_output.jsonl \
    "$@"
