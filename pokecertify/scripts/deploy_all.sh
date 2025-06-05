#!/bin/bash
# PokéCertify Full Deployment Script

set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
elif [ -f ../.env ]; then
    export $(grep -v '^#' ../.env | xargs)
fi

echo "=== [1/4] Initializing Database ==="
bash "$(dirname "$0")/init_db.sh" "${POKECERTIFY_DB_PATH:-pokecertify.db}"

echo "=== [2/4] Deploying Modal Labs Grader ==="
modal deploy src/backend/modal_grader/modal_grader.py

echo "=== [3/4] Starting Backend API (FastAPI) ==="
uvicorn src/backend/api/main:app --host 0.0.0.0 --port 8000 &

echo "=== [4/4] Starting Gradio Frontend ==="
python src/frontend/app.py &

echo "Deployment complete. Backend on :8000, Frontend on :7860 (default Gradio port)."