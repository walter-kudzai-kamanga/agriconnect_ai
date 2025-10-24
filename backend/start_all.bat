@echo off
REM AgriConnect MCP Brain - Windows Startup Script

echo Starting AgriConnect MCP System...
echo ======================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Please install Python 3.8+
    exit /b 1
)

REM Create logs directory
if not exist logs mkdir logs

REM Start Weather MCP
echo Starting Weather MCP on port 8001...
start "Weather-MCP" /min cmd /c "cd app\mcp_server\weather_servers && python main.py > ..\..\..\logs\weather-mcp.log 2>&1"
timeout /t 2 /nobreak >nul

REM Start Market MCP
echo Starting Market MCP on port 8002...
start "Market-MCP" /min cmd /c "cd app\mcp_server\market_server && python main.py > ..\..\..\logs\market-mcp.log 2>&1"
timeout /t 2 /nobreak >nul

REM Start Transport MCP
echo Starting Transport MCP on port 8003...
start "Transport-MCP" /min cmd /c "cd app\mcp_server\transport_server && python main.py > ..\..\..\logs\transport-mcp.log 2>&1"
timeout /t 2 /nobreak >nul

echo Waiting for MCP services to initialize...
timeout /t 5 /nobreak >nul

REM Start MCP Brain
echo Starting MCP Brain on port 8000...
start "MCP-Brain" cmd /c "cd app\mcp_brain && python mcp_brain.py > ..\..\logs\mcp-brain.log 2>&1"
timeout /t 2 /nobreak >nul

echo.
echo All services started successfully!
echo ======================================
echo.
echo Service Status:
echo    Weather MCP:   http://localhost:8001/health
echo    Market MCP:    http://localhost:8002/health
echo    Transport MCP: http://localhost:8003/health
echo    MCP Brain:     http://localhost:8000/health
echo.
echo Logs available in: .\logs\
echo To stop all services: stop_all.bat
echo.
echo Test the system:
echo    curl http://localhost:8000/test-users
echo.
