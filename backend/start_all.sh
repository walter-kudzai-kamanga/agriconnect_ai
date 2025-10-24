#!/bin/bash

# AgriConnect MCP Brain - Startup Script
# Starts all MCP services and the brain

echo " Starting AgriConnect MCP System..."
echo "======================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo " Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Check if requirements are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo " Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Create logs directory
mkdir -p logs

# Function to start a service
start_service() {
    local name=$1
    local port=$2
    local path=$3
    local log_file="logs/${name}.log"
    
    echo " Starting ${name} on port ${port}..."
    cd "${path}"
    python3 main.py > "../../../${log_file}" 2>&1 &
    local pid=$!
    echo ${pid} > "../../../logs/${name}.pid"
    cd ../../..
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

# Start MCP Brain
echo " Starting MCP Brain on port 8000..."
cd app/mcp_brain
python3 mcp_brain.py > ../../logs/mcp-brain.log 2>&1 &
BRAIN_PID=$!
echo ${BRAIN_PID} > ../../logs/mcp-brain.pid
cd ../..
echo "   PID: ${BRAIN_PID}"

echo ""
echo " All services started successfully!"
echo "======================================"
echo ""
echo " Service Status:"
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
