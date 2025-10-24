#!/bin/bash

# AgriConnect MCP Brain - Stop Script

echo "Stopping AgriConnect MCP System..."
echo "======================================"

# Store the base directory
BASE_DIR=$(pwd)

# Function to stop a service
stop_service() {
    local name=$1
    local pid_file="${BASE_DIR}/logs/${name}.pid"
    
    if [ -f "${pid_file}" ]; then
        local pid=$(cat "${pid_file}")
        if ps -p ${pid} > /dev/null 2>&1; then
            echo "   Stopping ${name} (PID: ${pid})..."
            kill ${pid} 2>/dev/null
            sleep 1
            # Force kill if still running
            if ps -p ${pid} > /dev/null 2>&1; then
                kill -9 ${pid} 2>/dev/null
            fi
        fi
        rm "${pid_file}"
    fi
}

# Stop all services
stop_service "Weather-MCP"
stop_service "Market-MCP"
stop_service "Transport-MCP"
stop_service "mcp-brain"

echo ""
echo "All services stopped."
echo ""
