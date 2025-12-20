# ============================================================================
# Heat Pump MCP Server - Standalone Executable Builder
# Creates a single .exe file that doesn't require Python to be installed
# ============================================================================

param(
    [switch]$Install,
    [switch]$Build
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Heat Pump MCP Server - Standalone Builder" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check Python
Write-Host "[1/4] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "    Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found. Install Python 3.10+ first." -ForegroundColor Red
    exit 1
}

# Install PyInstaller if needed
Write-Host ""
Write-Host "[2/4] Checking PyInstaller..." -ForegroundColor Yellow
$pyinstallerInstalled = pip show pyinstaller 2>$null
if (-not $pyinstallerInstalled) {
    Write-Host "    Installing PyInstaller..." -ForegroundColor Gray
    pip install pyinstaller --quiet
}
Write-Host "    PyInstaller ready" -ForegroundColor Green

# Install package dependencies
Write-Host ""
Write-Host "[3/4] Installing dependencies..." -ForegroundColor Yellow
pip install -e . --quiet
Write-Host "    Dependencies installed" -ForegroundColor Green

# Build the executable
Write-Host ""
Write-Host "[4/4] Building standalone executable..." -ForegroundColor Yellow

$SpecContent = @"
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/heatpump_mcp/server.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['mcp', 'mcp.server', 'mcp.server.stdio', 'mcp.types', 'httpx', 'anyio'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='heatpump-mcp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"@

$SpecContent | Out-File -FilePath "heatpump-mcp.spec" -Encoding UTF8

# Run PyInstaller
pyinstaller heatpump-mcp.spec --noconfirm 2>&1 | Out-Null

if (Test-Path "dist\heatpump-mcp.exe") {
    $exeSize = (Get-Item "dist\heatpump-mcp.exe").Length / 1MB
    Write-Host "    Built: dist\heatpump-mcp.exe ($([math]::Round($exeSize, 1)) MB)" -ForegroundColor Green
} else {
    Write-Host "    ERROR: Build failed. Check output above." -ForegroundColor Red
    exit 1
}

# Create installer batch file for the standalone exe
$InstallerContent = @'
@echo off
REM Heat Pump MCP Server - Standalone Installer
REM This installs the pre-built executable

echo.
echo ============================================================
echo   Heat Pump MCP Server - Standalone Installer
echo ============================================================
echo.

set INSTALL_DIR=%LOCALAPPDATA%\HeatPumpMCP
set EXE_NAME=heatpump-mcp.exe

echo [1/3] Creating installation directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo [2/3] Copying executable...
copy /Y "%~dp0heatpump-mcp.exe" "%INSTALL_DIR%\%EXE_NAME%" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy executable
    pause
    exit /b 1
)

echo [3/3] Configuring Claude Desktop...
set CONFIG_DIR=%APPDATA%\Claude
set CONFIG_FILE=%CONFIG_DIR%\claude_desktop_config.json

if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"
if exist "%CONFIG_FILE%" copy "%CONFIG_FILE%" "%CONFIG_FILE%.backup" >nul

set "EXE_PATH=%INSTALL_DIR%\%EXE_NAME%"
set "EXE_PATH=%EXE_PATH:\=\\%"

echo {> "%CONFIG_FILE%"
echo   "mcpServers": {>> "%CONFIG_FILE%"
echo     "heatpump-simulator": {>> "%CONFIG_FILE%"
echo       "command": "%EXE_PATH%",>> "%CONFIG_FILE%"
echo       "args": []>> "%CONFIG_FILE%"
echo     }>> "%CONFIG_FILE%"
echo   }>> "%CONFIG_FILE%"
echo }>> "%CONFIG_FILE%"

echo.
echo ============================================================
echo   Installation Complete!
echo ============================================================
echo.
echo Installed to: %INSTALL_DIR%
echo.
echo NEXT STEPS:
echo 1. Close Claude Desktop completely
echo 2. Reopen Claude Desktop
echo 3. Try asking: "What heat pump models are available?"
echo.
pause
'@

$InstallerContent | Out-File -FilePath "dist\install-standalone.bat" -Encoding ASCII

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Build Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Distribution files created in: $ScriptDir\dist\" -ForegroundColor White
Write-Host ""
Write-Host "For non-developers, distribute these files:" -ForegroundColor Yellow
Write-Host "  - heatpump-mcp.exe (standalone executable)" -ForegroundColor Gray
Write-Host "  - install-standalone.bat (one-click installer)" -ForegroundColor Gray
Write-Host ""
Write-Host "Users just need to:" -ForegroundColor Yellow
Write-Host "  1. Download both files to a folder" -ForegroundColor Gray
Write-Host "  2. Double-click install-standalone.bat" -ForegroundColor Gray
Write-Host "  3. Restart Claude Desktop" -ForegroundColor Gray
Write-Host ""
