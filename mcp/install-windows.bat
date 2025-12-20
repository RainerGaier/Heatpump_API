@echo off
REM ============================================================================
REM Heat Pump MCP Server - Windows Installer
REM For non-developers: One-click installation for Claude Desktop integration
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   Heat Pump MCP Server - Windows Installer
echo ============================================================
echo.

REM Check for Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH.
    echo.
    echo Please install Python 3.10 or later from:
    echo   https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo    Found Python %PYVER%

REM Get Python major.minor version
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do (
    set PYMAJOR=%%a
    set PYMINOR=%%b
)

if %PYMAJOR% LSS 3 (
    echo ERROR: Python 3.10+ required, found Python %PYVER%
    pause
    exit /b 1
)
if %PYMAJOR%==3 if %PYMINOR% LSS 10 (
    echo ERROR: Python 3.10+ required, found Python %PYVER%
    pause
    exit /b 1
)

REM Install the MCP package
echo.
echo [2/5] Installing Heat Pump MCP package...
cd /d "%~dp0"
pip install -e . --quiet
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install package. Try running as Administrator.
    pause
    exit /b 1
)
echo    Package installed successfully

REM Find the heatpump-mcp command location
echo.
echo [3/5] Locating MCP server executable...
for /f "tokens=*" %%i in ('where heatpump-mcp 2^>nul') do set MCP_PATH=%%i
if "%MCP_PATH%"=="" (
    REM Fallback to python -m approach
    set MCP_CMD=python -m heatpump_mcp
    echo    Using: python -m heatpump_mcp
) else (
    set MCP_CMD="%MCP_PATH%"
    echo    Found: %MCP_PATH%
)

REM Configure Claude Desktop
echo.
echo [4/5] Configuring Claude Desktop...

set CONFIG_DIR=%APPDATA%\Claude
set CONFIG_FILE=%CONFIG_DIR%\claude_desktop_config.json

REM Create directory if it doesn't exist
if not exist "%CONFIG_DIR%" (
    mkdir "%CONFIG_DIR%"
    echo    Created Claude config directory
)

REM Backup existing config
if exist "%CONFIG_FILE%" (
    copy "%CONFIG_FILE%" "%CONFIG_FILE%.backup" >nul
    echo    Backed up existing config to claude_desktop_config.json.backup
)

REM Get the script directory with escaped backslashes
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:\=\\%"
set "SERVER_PATH=%SCRIPT_DIR%src\\heatpump_mcp\\server.py"

REM Create or update config file
echo {> "%CONFIG_FILE%"
echo   "mcpServers": {>> "%CONFIG_FILE%"
echo     "heatpump-simulator": {>> "%CONFIG_FILE%"
echo       "command": "python",>> "%CONFIG_FILE%"
echo       "args": [>> "%CONFIG_FILE%"
echo         "%SERVER_PATH%">> "%CONFIG_FILE%"
echo       ]>> "%CONFIG_FILE%"
echo     }>> "%CONFIG_FILE%"
echo   }>> "%CONFIG_FILE%"
echo }>> "%CONFIG_FILE%"

echo    Claude Desktop configured

REM Verify installation
echo.
echo [5/5] Verifying installation...
python -c "from heatpump_mcp import __version__; print(f'    Heat Pump MCP v{__version__} installed successfully')"
if errorlevel 1 (
    echo    Warning: Could not verify package installation
)

echo.
echo ============================================================
echo   Installation Complete!
echo ============================================================
echo.
echo NEXT STEPS:
echo.
echo 1. Close Claude Desktop completely (check system tray)
echo 2. Reopen Claude Desktop
echo 3. Look for the plug icon showing MCP servers connected
echo 4. Try asking: "What heat pump models are available?"
echo.
echo If you encounter issues:
echo - Check logs at: %APPDATA%\Claude\logs\
echo - Run 'python "%~dp0src\heatpump_mcp\server.py"' to test manually
echo.
echo ============================================================
echo.
pause
