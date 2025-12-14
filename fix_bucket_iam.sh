#!/bin/bash
# Fix IAM permissions for Cloud Run service account
# Run this after setup_gcs_bucket.sh if IAM binding failed

set -e

PROJECT_ID="lotsawatts"
BUCKET_NAME="heatpump-outputs"

echo "Getting project number..."
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")

if [ -z "$PROJECT_NUMBER" ]; then
    echo "Error: Could not retrieve project number."
    echo "Please run manually:"
    echo "  1. Get project number: gcloud projects describe ${PROJECT_ID} --format='value(projectNumber)'"
    echo "  2. Grant access: gcloud storage buckets add-iam-policy-binding gs://${BUCKET_NAME} \\"
    echo "       --member='serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com' \\"
    echo "       --role='roles/storage.objectAdmin'"
    exit 1
fi

SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "Project Number: ${PROJECT_NUMBER}"
echo "Service Account: ${SERVICE_ACCOUNT}"
echo ""
echo "Granting storage.objectAdmin role to Cloud Run service account..."

gcloud storage buckets add-iam-policy-binding gs://${BUCKET_NAME} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/storage.objectAdmin"

echo ""
echo "✓ IAM permissions granted successfully!"
echo ""
echo "Verify with:"
echo "  gcloud storage buckets get-iam-policy gs://${BUCKET_NAME}"
