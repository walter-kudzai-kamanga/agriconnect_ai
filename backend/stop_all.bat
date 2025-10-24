@echo off
REM 

echo Stopping AgriConnect MCP System...
echo ======================================

REM 
for %%s in (Weather-MCP Market-MCP Transport-MCP MCP-Brain) do (
    echo Stopping %%s...
    taskkill /FI "WINDOWTITLE eq %%s*" /F >nul 2>&1
)

REM 
taskkill /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *MCP*" /F >nul 2>&1

echo.
echo All services stopped.
echo.
