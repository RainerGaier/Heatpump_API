@echo off
REM ============================================================================
REM Heat Pump MCP Server - Windows Uninstaller
REM Removes the MCP server and Claude Desktop configuration
REM ============================================================================

echo.
echo ============================================================
echo   Heat Pump MCP Server - Uninstaller
echo ============================================================
echo.

set /p CONFIRM="Are you sure you want to uninstall? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo Cancelled.
    exit /b 0
)

echo.
echo [1/3] Uninstalling pip package...
pip uninstall heatpump-mcp -y 2>nul
if errorlevel 1 (
    echo    Package was not installed via pip
) else (
    echo    Package uninstalled
)

echo.
echo [2/3] Removing Claude Desktop configuration...

set CONFIG_FILE=%APPDATA%\Claude\claude_desktop_config.json

if exist "%CONFIG_FILE%" (
    REM Check if backup exists
    if exist "%CONFIG_FILE%.backup" (
        copy "%CONFIG_FILE%.backup" "%CONFIG_FILE%" >nul
        echo    Restored previous configuration from backup
    ) else (
        REM Create empty config
        echo {} > "%CONFIG_FILE%"
        echo    Reset configuration to empty
    )
) else (
    echo    No configuration file found
)

echo.
echo [3/3] Cleanup complete

echo.
echo ============================================================
echo   Uninstallation Complete!
echo ============================================================
echo.
echo Please restart Claude Desktop to apply changes.
echo.
pause
