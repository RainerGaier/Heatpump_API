#!/bin/bash
# Deploy Streamlit app to Google Cloud Run
# Usage: ./deploy-streamlit.sh

set -e  # Exit on error

echo "=== Deploying Heat Pump Streamlit App to Cloud Run ==="

# Configuration
SERVICE_NAME="heatpump-streamlit"
REGION="europe-west1"
PORT="8501"
MEMORY="2Gi"

# Check if we're in the right directory
if [ ! -f "Dockerfile.streamlit" ]; then
    echo "Error: Dockerfile.streamlit not found. Run this from heatpumps-main directory."
    exit 1
fi

# Backup current Dockerfile if it exists
if [ -f "Dockerfile" ]; then
    echo "Backing up Dockerfile to Dockerfile.api..."
    mv Dockerfile Dockerfile.api
fi

# Use Streamlit Dockerfile
echo "Setting up Dockerfile.streamlit as Dockerfile..."
cp Dockerfile.streamlit Dockerfile

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --allow-unauthenticated \
    --port $PORT \
    --memory $MEMORY

# Restore original Dockerfile
echo "Restoring original Dockerfile..."
rm Dockerfile
if [ -f "Dockerfile.api" ]; then
    mv Dockerfile.api Dockerfile
fi

echo ""
echo "=== Deployment Complete ==="
echo "Your Streamlit app should be available at the URL shown above."
