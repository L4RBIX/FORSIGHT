#!/usr/bin/env bash
set -euo pipefail

echo "Starting Foresight live backend..."
cd "$(dirname "$0")/../backend"
export USE_MOCK=false
uvicorn main:app --reload --port 8000
