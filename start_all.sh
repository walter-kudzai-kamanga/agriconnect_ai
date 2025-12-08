#!/bin/bash

# Wrapper script to start AgriConnect from project root
# This script changes to the backend directory and runs the actual start script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend"

if [ -f "./start_all.sh" ]; then
    bash ./start_all.sh
else
    echo "Error: start_all.sh not found in backend directory"
    exit 1
fi

