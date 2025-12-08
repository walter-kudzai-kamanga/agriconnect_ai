#!/bin/bash

# Simple wrapper to run the app from project root

cd "$(dirname "$0")/backend" || exit 1

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run uvicorn
python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --reload

