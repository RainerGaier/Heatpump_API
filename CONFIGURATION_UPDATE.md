# Configuration Update Summary

## Overview
Updated all configuration files to use the existing Google Cloud Storage bucket instead of creating a new one.

## Configuration Changes

### Existing Bucket Details
- **Project ID:** `lotsawatts` (was: `heatpump-simulator-api`)
- **Bucket Name:** `heatpump-outputs` (was: `heatpump-reports-heatpump-simulator-api`)
- **Location:** `EU` multi-region (was: `europe-west2`)
- **Storage URL:** `gs://heatpump-outputs/`

### Files Updated

#### 1. `.env.example`
Updated environment variable examples:
```bash
GCP_PROJECT_ID=lotsawatts
GCS_BUCKET_NAME=heatpump-outputs
GCS_LOCATION=EU
REPORTS_EXPIRY_DAYS=30
```

#### 2. `cloudbuild.yaml`
Updated Cloud Run deployment environment variables (line 28):
```yaml
--set-env-vars=DEBUG=false,LOG_LEVEL=INFO,SIMULATION_TIMEOUT=300,GCP_PROJECT_ID=lotsawatts,GCS_BUCKET_NAME=heatpump-outputs,GCS_LOCATION=EU,REPORTS_EXPIRY_DAYS=30
```

#### 3. `setup_gcs_bucket.sh`
Updated configuration section (lines 8-10):
```bash
PROJECT_ID="lotsawatts"
BUCKET_NAME="heatpump-outputs"
LOCATION="EU"
```

**Note:** Since the bucket already exists, you can skip running this script. Use `verify_bucket_config.sh` instead.

#### 4. `fix_bucket_iam.sh`
Updated configuration (lines 7-8):
```bash
PROJECT_ID="lotsawatts"
BUCKET_NAME="heatpump-outputs"
```

#### 5. `test_reports_api.py`
Updated troubleshooting message (line 285):
```python
print("  1. Check if GCS bucket exists: gsutil ls gs://heatpump-outputs")
```

#### 6. `REPORTS_SETUP.md`
Global replacements throughout documentation:
- `heatpump-simulator-api` → `lotsawatts`
- `heatpump-reports-heatpump-simulator-api` → `heatpump-outputs`
- `europe-west2` → `EU`

### New Files Created

#### `verify_bucket_config.sh`
New script to verify and configure the existing bucket:
- Checks if bucket exists
- Verifies lifecycle policy (30-day expiration)
- Verifies CORS configuration
- Checks IAM permissions for Cloud Run service account
- Applies missing configurations automatically

## Next Steps

### 1. Verify Existing Bucket Configuration
Run the verification script to ensure the bucket has all necessary settings:

```bash
cd c:/Users/gaierr/Energy_Projects/projects/heatpumps/heatpumps-main
chmod +x verify_bucket_config.sh
./verify_bucket_config.sh
```

This will:
- ✓ Confirm bucket exists
- ✓ Apply lifecycle policy if missing (30-day auto-deletion)
- ✓ Apply CORS configuration if missing
- ✓ Grant Cloud Run service account permissions if missing

### 2. Install Dependencies
Ensure the GCS client libraries are installed:

```bash
cd c:/Users/gaierr/Energy_Projects/projects/heatpumps/heatpumps-main
pip install -e .
```

This will install:
- `google-cloud-storage>=2.10.0`
- `google-auth>=2.23.0`

### 3. Deploy to Cloud Run
Deploy the updated API with correct environment variables:

```bash
gcloud builds submit --config cloudbuild.yaml
```

The deployment will automatically set:
- `GCP_PROJECT_ID=lotsawatts`
- `GCS_BUCKET_NAME=heatpump-outputs`
- `GCS_LOCATION=EU`
- `REPORTS_EXPIRY_DAYS=30`

### 4. Test the API
Run the test suite to verify everything works:

```bash
python test_reports_api.py
```

Expected output:
```
TEST 1: Save Report       [PASS]
TEST 2: Get Report        [PASS]
TEST 3: Get Signed URL    [PASS]
TEST 4: List Reports      [PASS]
TEST 5: Delete Report     [PASS]

Test Results: 5 passed, 0 failed
```

### 5. Verify Reports in Cloud Storage
Check that reports are being saved correctly:

```bash
gsutil ls -r gs://heatpump-outputs/reports/
```

You should see reports organized by year-month:
```
gs://heatpump-outputs/reports/2025-12/
gs://heatpump-outputs/reports/2025-12/abc123-def4-5678-90ab-cdefg1234567.json
```

## Benefits of Using Existing Bucket

✅ **Avoids permission issues** - Bucket already has proper IAM configuration

✅ **Consistent project** - All resources in `lotsawatts` project

✅ **EU location** - Multi-region redundancy and compliance

✅ **No duplication** - Uses existing infrastructure

✅ **Faster deployment** - No bucket creation step needed

## Configuration Reference

### Environment Variables (Cloud Run)
```bash
GCP_PROJECT_ID=lotsawatts
GCS_BUCKET_NAME=heatpump-outputs
GCS_LOCATION=EU
REPORTS_EXPIRY_DAYS=30
```

### Local Testing (.env file)
Create a `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

Ensure these variables are set:
```bash
GCP_PROJECT_ID=lotsawatts
GCS_BUCKET_NAME=heatpump-outputs
GCS_LOCATION=EU
REPORTS_EXPIRY_DAYS=30
```

### Bucket Structure
```
gs://heatpump-outputs/
├── reports/
│   ├── 2025-12/
│   │   ├── report-id-1.json
│   │   ├── report-id-2.json
│   │   └── ...
│   └── 2026-01/
│       └── ...
```

### Lifecycle Policy
Reports in the `reports/` folder are automatically deleted after 30 days.

### CORS Policy
Allows browser access to report files:
```json
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type", "Content-Length", "Date"],
    "maxAgeSeconds": 3600
  }
]
```

### IAM Permissions
Cloud Run service account has `roles/storage.objectAdmin` on the bucket:
- Service Account: `PROJECT_NUMBER-compute@developer.gserviceaccount.com`
- Permissions: Read, write, delete objects

## Troubleshooting

### Issue: API returns "Storage service unavailable"

**Check environment variables:**
```bash
gcloud run services describe heatpump-api --region=europe-west2 --format="value(spec.template.spec.containers[0].env)"
```

Should show:
```
GCP_PROJECT_ID=lotsawatts
GCS_BUCKET_NAME=heatpump-outputs
```

If missing, redeploy:
```bash
gcloud builds submit --config cloudbuild.yaml
```

### Issue: Permission denied when saving reports

**Check IAM permissions:**
```bash
gcloud storage buckets get-iam-policy gs://heatpump-outputs
```

Should include:
```yaml
members:
- serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com
role: roles/storage.objectAdmin
```

If missing, run:
```bash
./verify_bucket_config.sh
```

Or manually grant:
```bash
PROJECT_NUMBER=$(gcloud projects describe lotsawatts --format="value(projectNumber)")
gcloud storage buckets add-iam-policy-binding gs://heatpump-outputs \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

### Issue: Test script fails with connection error

**Check API is running:**
```bash
curl https://heatpump-api-658843246978.europe-west2.run.app/health
```

Should return:
```json
{"status":"healthy"}
```

**Check logs:**
```bash
gcloud run services logs read heatpump-api --region=europe-west2 --limit=50
```

## Summary

✅ All configuration files updated to use `gs://heatpump-outputs`

✅ Project changed from `heatpump-simulator-api` to `lotsawatts`

✅ Location changed from `europe-west2` to `EU` multi-region

✅ New verification script created: `verify_bucket_config.sh`

✅ Ready for deployment and testing

---

**Status:** Configuration update complete. Ready to deploy!

**Next Command:** `./verify_bucket_config.sh`
