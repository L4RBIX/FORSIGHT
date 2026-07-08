#!/usr/bin/env bash
set -euo pipefail

echo "Starting Foresight mock backend..."
cd "$(dirname "$0")/../backend"
export USE_MOCK=true
uvicorn main:app --reload --port 8000
