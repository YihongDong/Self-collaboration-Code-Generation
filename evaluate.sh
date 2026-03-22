#!/bin/bash
# Evaluate predictions
set -a; source .env; set +a

python3 evaluate/all_evaluate.py --input_path "${1:-humaneval_output.jsonl}"
