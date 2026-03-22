#!/bin/bash
# Run SWE-bench Lite benchmark
set -a; source .env; set +a

python3 run_swe.py \
    --work_dir swe_workdir \
    --max_round 2 \
    --max_steps 12 \
    --output_path swe_predictions.jsonl \
    "$@"
