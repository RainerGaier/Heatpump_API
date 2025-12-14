#!/bin/bash
# Setup script for Google Cloud Storage bucket for Heat Pump Reports
# Run this script BEFORE deploying the API to ensure the bucket exists

set -e  # Exit on error

# Configuration
PROJECT_ID="lotsawatts"
BUCKET_NAME="heatpump-outputs"
LOCATION="EU"
LIFECYCLE_DAYS=30

echo "========================================="
echo "Heat Pump Reports - GCS Bucket Setup"
echo "========================================="
echo ""
echo "Configuration:"
echo "  Project ID: ${PROJECT_ID}"
echo "  Bucket Name: ${BUCKET_NAME}"
echo "  Location: ${LOCATION}"
echo "  Lifecycle: ${LIFECYCLE_DAYS} days"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI not found. Please install Google Cloud SDK."
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "Error: Not authenticated with gcloud. Run 'gcloud auth login' first."
    exit 1
fi

# Set project
echo "Setting active project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Check if bucket already exists
if gsutil ls -b gs://${BUCKET_NAME} &> /dev/null; then
    echo "Warning: Bucket gs://${BUCKET_NAME} already exists."
    read -p "Do you want to update its configuration? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping bucket creation."
        exit 0
    fi
else
    # Create bucket
    echo "Creating bucket gs://${BUCKET_NAME}..."
    gcloud storage buckets create gs://${BUCKET_NAME} \
        --project=${PROJECT_ID} \
        --location=${LOCATION} \
        --uniform-bucket-level-access \
        --public-access-prevention
fi

# Create lifecycle policy file
echo "Creating lifecycle policy (${LIFECYCLE_DAYS} days expiration)..."
cat > /tmp/lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {
          "type": "Delete"
        },
        "condition": {
          "age": ${LIFECYCLE_DAYS},
          "matchesPrefix": ["reports/"]
        }
      }
    ]
  }
}
EOF

# Apply lifecycle policy
echo "Applying lifecycle policy..."
gsutil lifecycle set /tmp/lifecycle.json gs://${BUCKET_NAME}

# Create CORS configuration
echo "Configuring CORS for browser access..."
cat > /tmp/cors.json <<EOF
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type", "Content-Length", "Date"],
    "maxAgeSeconds": 3600
  }
]
EOF

# Apply CORS configuration
echo "Applying CORS configuration..."
gsutil cors set /tmp/cors.json gs://${BUCKET_NAME}

# Grant Cloud Run service account access
echo "Granting storage permissions to Cloud Run service account..."
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "  Service Account: ${SERVICE_ACCOUNT}"

gcloud storage buckets add-iam-policy-binding gs://${BUCKET_NAME} \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/storage.objectAdmin"

# Clean up temp files
rm -f /tmp/lifecycle.json /tmp/cors.json

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Bucket Details:"
echo "  URL: gs://${BUCKET_NAME}"
echo "  Location: ${LOCATION}"
echo "  Lifecycle: Reports expire after ${LIFECYCLE_DAYS} days"
echo "  CORS: Enabled for browser access"
echo "  IAM: Cloud Run service account has write access"
echo ""
echo "Next Steps:"
echo "  1. Deploy your API with: gcloud builds submit --config cloudbuild.yaml"
echo "  2. Test the /api/v1/reports/save endpoint"
echo "  3. Verify reports are saved to gs://${BUCKET_NAME}/reports/"
echo ""
echo "View bucket contents:"
echo "  gsutil ls -r gs://${BUCKET_NAME}/reports/"
echo ""
