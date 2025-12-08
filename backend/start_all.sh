#!/bin/bash

# AgriConnect MCP Brain - Startup Script
# Starts all MCP services and the brain

# Get the backend directory (where this script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo " Starting AgriConnect MCP System..."
echo "======================================"
echo " Working directory: $(pwd)"

# Check if virtual environment exists and activate it
if [ -d "venv" ]; then
    echo " Activating virtual environment..."
    source venv/bin/activate
    PYTHON_CMD="python"
    PIP_CMD="pip"
elif [ -d "../venv" ]; then
    echo " Activating virtual environment from parent directory..."
    source ../venv/bin/activate
    PYTHON_CMD="python"
    PIP_CMD="pip"
else
    echo " No virtual environment found, using system Python..."
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
fi

# Check if Python is available
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo " Python not found. Please install Python 3.8+"
    exit 1
fi

# Check if requirements are installed
if ! $PYTHON_CMD -c "import fastapi" 2>/dev/null; then
    echo " Installing dependencies..."
    echo " Attempting to install from requirements.txt..."
    if ! $PIP_CMD install -r requirements.txt 2>&1 | tee /tmp/pip-install.log; then
        echo " Warning: Some packages failed to install."
        echo " Trying minimal requirements..."
        if [ -f "requirements-minimal.txt" ]; then
            $PIP_CMD install -r requirements-minimal.txt
        else
            echo " Installing core packages manually..."
            $PIP_CMD install fastapi uvicorn[standard] sqlalchemy pydantic requests httpx aiohttp
        fi
    fi
fi

# Create logs directory
mkdir -p logs

# Set PYTHONPATH to include backend directory
export PYTHONPATH="${PYTHONPATH}:${SCRIPT_DIR}"

# Function to start a service
start_service() {
    local name=$1
    local port=$2
    local path=$3
    local log_file="${SCRIPT_DIR}/logs/${name}.log"
    
    echo " Starting ${name} on port ${port}..."
    cd "${SCRIPT_DIR}/${path}"
    export PYTHONPATH="${PYTHONPATH}:${SCRIPT_DIR}"
    $PYTHON_CMD main.py > "${log_file}" 2>&1 &
    local pid=$!
    echo ${pid} > "${SCRIPT_DIR}/logs/${name}.pid"
    cd "$SCRIPT_DIR"
    echo "   PID: ${pid}"
    sleep 2
}

# Start MCP services
start_service "Weather-MCP" 8001 "app/mcp_server/weather_servers"
start_service "Market-MCP" 8002 "app/mcp_server/market_server"
start_service "Transport-MCP" 8003 "app/mcp_server/transport_server"

# Wait for services to be ready
echo " Waiting for MCP services to initialize..."
sleep 5

# Start Main FastAPI App (MCP Brain + Dashboard)
echo " Starting Main FastAPI App on port 8000..."
cd "$SCRIPT_DIR"
export PYTHONPATH="${PYTHONPATH}:${SCRIPT_DIR}"
$PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "${SCRIPT_DIR}/logs/main-app.log" 2>&1 &
MAIN_PID=$!
echo ${MAIN_PID} > "${SCRIPT_DIR}/logs/main-app.pid"
echo "   PID: ${MAIN_PID}"
sleep 3

echo ""
echo " All services started successfully!"
echo "======================================"
echo ""
echo " Service Status:"
echo "   Main App:      http://localhost:8000"
echo "   Weather MCP:   http://localhost:8001/health"
echo "   Market MCP:    http://localhost:8002/health"
echo "   Transport MCP: http://localhost:8003/health"
echo "   MCP Brain:     http://localhost:8000/health"
echo ""
echo "Logs available in: ./logs/"
echo " To stop all services: ./stop_all.sh"
echo ""
echo " Test the system:"
echo "   curl http://localhost:8000/test-users"
echo ""
