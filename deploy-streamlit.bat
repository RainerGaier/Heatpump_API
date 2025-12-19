@echo off
REM Deploy Streamlit app to Google Cloud Run
REM Usage: deploy-streamlit.bat

echo === Deploying Heat Pump Streamlit App to Cloud Run ===

REM Configuration
set SERVICE_NAME=heatpump-streamlit
set REGION=europe-west1
set PORT=8501
set MEMORY=2Gi

REM Check if we're in the right directory
if not exist "Dockerfile.streamlit" (
    echo Error: Dockerfile.streamlit not found. Run this from heatpumps-main directory.
    exit /b 1
)

REM Backup current Dockerfile if it exists
if exist "Dockerfile" (
    echo Backing up Dockerfile to Dockerfile.api...
    move Dockerfile Dockerfile.api
)

REM Use Streamlit Dockerfile
echo Setting up Dockerfile.streamlit as Dockerfile...
copy Dockerfile.streamlit Dockerfile

REM Deploy to Cloud Run
echo Deploying to Cloud Run...
call gcloud run deploy %SERVICE_NAME% --source . --region %REGION% --allow-unauthenticated --port %PORT% --memory %MEMORY%

REM Restore original Dockerfile
echo Restoring original Dockerfile...
del Dockerfile
if exist "Dockerfile.api" (
    move Dockerfile.api Dockerfile
)

echo.
echo === Deployment Complete ===
echo Your Streamlit app should be available at the URL shown above.
