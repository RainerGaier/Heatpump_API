# Manual Bucket Verification Steps

Since `gcloud` isn't available in Git Bash, run these commands in **Windows Command Prompt** or **PowerShell** where Google Cloud SDK is installed.

## Step 1: Set Active Project

```bash
gcloud config set project lotsawatts
```

## Step 2: Verify Bucket Exists

```bash
gcloud storage buckets list --filter="name:heatpump-outputs"
```

**Expected output:**
```
NAME              LOCATION  STORAGE_CLASS
heatpump-outputs  EU        STANDARD
```

✅ If you see this, your bucket exists and is correctly configured in EU region.

## Step 3: Check Lifecycle Policy

```bash
gsutil lifecycle get gs://heatpump-outputs
```

**What to look for:**
- Should have a rule to delete objects after 30 days
- Rule should apply to `reports/` prefix

**If missing or incorrect, apply this policy:**

```bash
# Create lifecycle configuration
cat > lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {
          "type": "Delete"
        },
        "condition": {
          "age": 30,
          "matchesPrefix": ["reports/"]
        }
      }
    ]
  }
}
EOF

# Apply it
gsutil lifecycle set lifecycle.json gs://heatpump-outputs

# Clean up
del lifecycle.json
```

## Step 4: Check CORS Configuration

```bash
gsutil cors get gs://heatpump-outputs
```

**What to look for:**
- Should allow GET and HEAD methods
- Should allow all origins (`*`)

**If missing or incorrect, apply this CORS configuration:**

```bash
# Create CORS configuration
cat > cors.json <<EOF
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD"],
    "responseHeader": ["Content-Type", "Content-Length", "Date"],
    "maxAgeSeconds": 3600
  }
]
EOF

# Apply it
gsutil cors set cors.json gs://heatpump-outputs

# Clean up
del cors.json
```

## Step 5: Check IAM Permissions

First, get your project number:

```bash
gcloud projects describe lotsawatts --format="value(projectNumber)"
```

**Example output:** `123456789012`

Then check bucket IAM policy:

```bash
gcloud storage buckets get-iam-policy gs://heatpump-outputs
```

**What to look for:**
Look for an entry like this (where `123456789012` is your project number):

```yaml
members:
- serviceAccount:123456789012-compute@developer.gserviceaccount.com
role: roles/storage.objectAdmin
```

**If missing, grant the permission:**

```bash
# Replace PROJECT_NUMBER with the actual number from step above
gcloud storage buckets add-iam-policy-binding gs://heatpump-outputs \
    --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

**Example (replace with your project number):**
```bash
gcloud storage buckets add-iam-policy-binding gs://heatpump-outputs \
    --member="serviceAccount:123456789012-compute@developer.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

## Step 6: Verify Configuration Summary

After completing the above steps, your bucket should have:

- ✅ **Location:** EU (multi-region)
- ✅ **Lifecycle Policy:** 30-day automatic deletion for `reports/` prefix
- ✅ **CORS:** Enabled for browser access (GET, HEAD methods)
- ✅ **IAM:** Cloud Run default service account has `storage.objectAdmin` role

## Step 7: Test Bucket Access

Try listing the bucket contents:

```bash
gsutil ls gs://heatpump-outputs
```

If the bucket is empty or only has a few items, that's fine. This just verifies you have access.

## Next Steps After Verification

Once the bucket is properly configured:

### 1. Install Python Dependencies

In Git Bash or Command Prompt:
```bash
cd C:\Users\gaierr\Energy_Projects\projects\heatpumps\heatpumps-main
pip install -e .
```

This installs:
- `google-cloud-storage>=2.10.0`
- `google-auth>=2.23.0`

### 2. Deploy to Cloud Run

In a terminal with gcloud access:
```bash
cd C:\Users\gaierr\Energy_Projects\projects\heatpumps\heatpumps-main
gcloud builds submit --config cloudbuild.yaml
```

This will:
- Build Docker container
- Deploy to Cloud Run in `europe-west2`
- Set environment variables:
  - `GCP_PROJECT_ID=lotsawatts`
  - `GCS_BUCKET_NAME=heatpump-outputs`
  - `GCS_LOCATION=EU`
  - `REPORTS_EXPIRY_DAYS=30`

### 3. Test the API

After deployment, test the endpoints:

```bash
cd C:\Users\gaierr\Energy_Projects\projects\heatpumps\heatpumps-main
python test_reports_api.py
```

**Expected output:**
```
TEST 1: Save Report       [PASS]
TEST 2: Get Report        [PASS]
TEST 3: Get Signed URL    [PASS]
TEST 4: List Reports      [PASS]
TEST 5: Delete Report     [PASS]

Test Results: 5 passed, 0 failed
```

### 4. Verify Reports in Cloud Storage

```bash
gsutil ls -r gs://heatpump-outputs/reports/
```

You should see reports saved in year-month folders:
```
gs://heatpump-outputs/reports/2025-12/
gs://heatpump-outputs/reports/2025-12/abc123-def4-5678-90ab-cdefg1234567.json
```

## Troubleshooting

### Can't Find gcloud Command

If you get "gcloud: command not found":

1. **Install Google Cloud SDK:** https://cloud.google.com/sdk/docs/install
2. **Or use Cloud Shell:** https://console.cloud.google.com/cloudshell (has gcloud pre-installed)
3. **Or add to PATH:** Find where gcloud is installed and add to your PATH environment variable

**Common Windows locations:**
- `C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin`
- `%LOCALAPPDATA%\Google\Cloud SDK\google-cloud-sdk\bin`

### Permission Denied Errors

If you get permission errors:

```bash
# Make sure you're authenticated
gcloud auth login

# Set the correct project
gcloud config set project lotsawatts

# Try the command again
```

### Bucket Doesn't Exist

If the bucket doesn't exist, you can create it:

```bash
cd C:\Users\gaierr\Energy_Projects\projects\heatpumps\heatpumps-main
bash setup_gcs_bucket.sh
```

This will create the bucket with all necessary configuration.

---

**Ready to proceed?** Complete Steps 1-5 above, then move on to deployment and testing!
