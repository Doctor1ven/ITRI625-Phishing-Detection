#!/bin/bash

set -u

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$PROJECT_DIR/.venv/bin/python"
API_URL="http://127.0.0.1:8000"
API_PID=""

cleanup() {
    if [[ -n "$API_PID" ]] && kill -0 "$API_PID" 2>/dev/null; then
        echo
        echo "Stopping FastAPI..."
        kill "$API_PID" 2>/dev/null
        wait "$API_PID" 2>/dev/null
    fi
}

trap cleanup EXIT INT TERM

cd "$PROJECT_DIR" || exit 1

if [[ ! -x "$PYTHON" ]]; then
    echo "The project virtual environment was not found."
    echo "Expected: $PYTHON"
    echo
    echo "Create it with:"
    echo "  python3 -m venv .venv"
    echo "  .venv/bin/python -m pip install -r requirements-lock.txt"
    exit 1
fi

if [[ ! -f "$PROJECT_DIR/models/phishing_pipeline.joblib" ]] || \
   [[ ! -f "$PROJECT_DIR/models/model_metadata.json" ]]; then
    echo "The trained model files are missing."
    echo "Run notebooks/phishing_detection.ipynb from start to finish first."
    exit 1
fi

echo "Starting the ITRI625 Phishing Detector..."
echo "Project: $PROJECT_DIR"
echo "API:     $API_URL"
echo

"$PYTHON" -m uvicorn api.main:app --host 127.0.0.1 --port 8000 &
API_PID=$!

API_READY=0
for ATTEMPT in $(seq 1 40); do
    if ! kill -0 "$API_PID" 2>/dev/null; then
        echo "FastAPI stopped before it became ready. Review the error above."
        exit 1
    fi

    if "$PYTHON" -c \
        "import json, urllib.request; data=json.load(urllib.request.urlopen('$API_URL/health', timeout=1)); raise SystemExit(0 if data.get('model_loaded') else 1)" \
        >/dev/null 2>&1; then
        API_READY=1
        break
    fi

    sleep 0.25
done

if [[ "$API_READY" -ne 1 ]]; then
    echo "FastAPI did not become healthy within 10 seconds."
    exit 1
fi

echo
echo "API is ready. Opening the desktop application..."
echo "Close the desktop window to stop the project."
echo

PHISHING_API_URL="$API_URL" "$PYTHON" -m desktop.app

