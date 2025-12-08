#!/bin/bash

# Run the FastAPI app from backend directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    PYTHON_CMD="python"
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${SCRIPT_DIR}"

# Get port from argument or use default
PORT=${1:-8000}

echo "Starting AgriConnect AI on port ${PORT}..."
echo "Working directory: $(pwd)"
echo "Python: $(which $PYTHON_CMD)"
echo ""
echo "Access the dashboard at: http://localhost:${PORT}"
echo "Press CTRL+C to stop"
echo ""

# Run uvicorn
$PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --reload

