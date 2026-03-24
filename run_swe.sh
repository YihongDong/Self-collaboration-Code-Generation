#!/bin/bash
# Run SWE-bench Lite benchmark
set -a; source .env; set +a

python3 run_swe.py \
    --work_dir swe_workdir \
    --max_round 3 \
    --max_steps 15 \
    --output_path swe_predictions.jsonl \
    "$@"
