#!/bin/bash
# Verify and configure existing bucket for Heat Pump Reports
# Run this to ensure heatpump-outputs bucket has the correct settings

set -e

PROJECT_ID="lotsawatts"
BUCKET_NAME="heatpump-outputs"
LIFECYCLE_DAYS=30

echo "========================================="
echo "Heat Pump Reports - Bucket Verification"
echo "========================================="
echo ""
echo "Project ID: ${PROJECT_ID}"
echo "Bucket Name: ${BUCKET_NAME}"
echo ""

# Set project
echo "Setting active project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Check if bucket exists
echo ""
echo "Checking if bucket exists..."
if ! gcloud storage buckets list --filter="name:${BUCKET_NAME}" --format="value(name)" | grep -q "${BUCKET_NAME}"; then
    echo "ERROR: Bucket gs://${BUCKET_NAME} does not exist!"
    exit 1
fi
echo "✓ Bucket exists"

# Check lifecycle policy
echo ""
echo "Checking lifecycle policy..."
if gsutil lifecycle get gs://${BUCKET_NAME} 2>&1 | grep -q "has no lifecycle configuration"; then
    echo "⚠ No lifecycle policy found. Applying 30-day expiration policy..."

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

    gsutil lifecycle set /tmp/lifecycle.json gs://${BUCKET_NAME}
    rm -f /tmp/lifecycle.json
    echo "✓ Lifecycle policy applied (${LIFECYCLE_DAYS} days)"
else
    echo "✓ Lifecycle policy exists"
    gsutil lifecycle get gs://${BUCKET_NAME}
fi

# Check CORS configuration
echo ""
echo "Checking CORS configuration..."
if gsutil cors get gs://${BUCKET_NAME} 2>&1 | grep -q "has no CORS configuration"; then
    echo "⚠ No CORS configuration found. Applying CORS policy..."

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

    gsutil cors set /tmp/cors.json gs://${BUCKET_NAME}
    rm -f /tmp/cors.json
    echo "✓ CORS policy applied"
else
    echo "✓ CORS configuration exists"
    gsutil cors get gs://${BUCKET_NAME}
fi

# Check IAM permissions for Cloud Run service account
echo ""
echo "Checking IAM permissions for Cloud Run service account..."
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format="value(projectNumber)")

if [ -z "$PROJECT_NUMBER" ]; then
    echo "ERROR: Could not retrieve project number"
    echo "Please run manually to grant permissions:"
    echo "  gcloud storage buckets add-iam-policy-binding gs://${BUCKET_NAME} \\"
    echo "    --member='serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com' \\"
    echo "    --role='roles/storage.objectAdmin'"
    exit 1
fi

SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
echo "  Project Number: ${PROJECT_NUMBER}"
echo "  Service Account: ${SERVICE_ACCOUNT}"

# Check if service account already has permissions
if gcloud storage buckets get-iam-policy gs://${BUCKET_NAME} --format=json | grep -q "${SERVICE_ACCOUNT}"; then
    echo "✓ Service account already has permissions"
else
    echo "⚠ Granting storage.objectAdmin role to Cloud Run service account..."
    gcloud storage buckets add-iam-policy-binding gs://${BUCKET_NAME} \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/storage.objectAdmin"
    echo "✓ Permissions granted"
fi

echo ""
echo "========================================="
echo "Verification Complete!"
echo "========================================="
echo ""
echo "Bucket Configuration Summary:"
echo "  ✓ Bucket exists: gs://${BUCKET_NAME}"
echo "  ✓ Lifecycle policy: Reports expire after ${LIFECYCLE_DAYS} days"
echo "  ✓ CORS: Enabled for browser access"
echo "  ✓ IAM: Cloud Run service account has objectAdmin access"
echo ""
echo "Next Steps:"
echo "  1. Deploy API: gcloud builds submit --config cloudbuild.yaml"
echo "  2. Test API: python test_reports_api.py"
echo "  3. View bucket: gsutil ls -r gs://${BUCKET_NAME}/reports/"
echo ""
