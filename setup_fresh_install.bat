@echo off
REM Fresh Install Script for Heatpump API
REM This script helps you quickly set up a fresh installation

echo ================================================
echo Heatpump API - Fresh Install Setup
echo ================================================
echo.

REM Get installation directory from user
set /p INSTALL_DIR="Enter installation directory (default: C:\Users\%USERNAME%\heatpump-fresh-install): "
if "%INSTALL_DIR%"=="" set INSTALL_DIR=C:\Users\%USERNAME%\heatpump-fresh-install

echo.
echo Installation directory: %INSTALL_DIR%
echo.
pause

REM Create directory
echo Creating directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
cd /d "%INSTALL_DIR%"

REM Clone repository
echo.
echo Cloning repository...
git clone https://github.com/RainerGaier/Heatpump_API.git
if errorlevel 1 (
    echo ERROR: Failed to clone repository
    pause
    exit /b 1
)

cd Heatpump_API

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment and install
echo.
echo Installing package and dependencies...
echo This may take a few minutes...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -e .

if errorlevel 1 (
    echo ERROR: Failed to install package
    pause
    exit /b 1
)

REM Verify installation
echo.
echo ================================================
echo Verifying installation...
echo ================================================
pip show heatpumps

echo.
echo ================================================
echo Installation complete!
echo ================================================
echo.
echo To use the dashboard:
echo   1. Open a new command prompt
echo   2. Navigate to: %INSTALL_DIR%\Heatpump_API
echo   3. Activate environment: venv\Scripts\activate
echo   4. Run dashboard: heatpumps-dashboard
echo.
echo Or simply run: launch_dashboard.bat
echo.

REM Create launch script
echo @echo off > launch_dashboard.bat
echo cd /d "%INSTALL_DIR%\Heatpump_API" >> launch_dashboard.bat
echo call venv\Scripts\activate.bat >> launch_dashboard.bat
echo heatpumps-dashboard >> launch_dashboard.bat
echo Created launch_dashboard.bat for easy startup!
echo.

pause
