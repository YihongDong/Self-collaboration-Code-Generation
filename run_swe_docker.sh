#!/bin/bash
# Run SWE-bench with Docker evaluation
set -e

IMAGE_NAME="swe-collab"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Build image if needed
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    echo "Building Docker image $IMAGE_NAME..."
    docker build -t "$IMAGE_NAME" "$SCRIPT_DIR"
fi

# logs/ is mounted — output_path defaults to logs/swe_predictions.jsonl
# No need for separate file mount
docker run --rm \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$SCRIPT_DIR/swe_workdir:/app/swe_workdir" \
    -v "$SCRIPT_DIR/logs:/app/logs" \
    -v "$SCRIPT_DIR/.env:/app/.env:ro" \
    "$IMAGE_NAME" "$@"
