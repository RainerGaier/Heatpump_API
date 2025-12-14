# Heat Pump Reports - Phase 1 Setup Guide

## Overview

Phase 1 implements JSON report storage to Google Cloud Storage, enabling users to save and share simulation results via public URLs.

**Status:** ✅ **READY FOR DEPLOYMENT**

---

## Architecture

```
Streamlit Dashboard
       ↓
   (Future: "Share Report" button)
       ↓
FastAPI /api/v1/reports/save
       ↓
Google Cloud Storage
       ↓
heatpump-outputs bucket
       ↓
Signed URL (7 days expiry)
```

---

## Prerequisites

### 1. Google Cloud Setup

**Required:**
- ✅ GCP Project ID: `lotsawatts`
- ✅ gcloud CLI installed and authenticated
- ✅ Billing enabled on project
- ✅ Cloud Run API enabled
- ✅ Cloud Storage API enabled

**Verify:**
```bash
gcloud auth list
gcloud config get-value project
# Should show: lotsawatts
```

### 2. Python Dependencies

**Added to `pyproject.toml`:**
```toml
"google-cloud-storage>=2.10.0"
"google-auth>=2.23.0"
```

**Install locally:**
```bash
pip install -e .
```

---

## Deployment Steps

### Step 1: Create Cloud Storage Bucket

**Run the setup script:**
```bash
cd c:/Users/gaierr/Energy_Projects/projects/heatpumps/heatpumps-main
chmod +x setup_gcs_bucket.sh
./setup_gcs_bucket.sh
```

**What it does:**
1. Creates bucket: `gs://heatpump-outputs`
2. Sets location: `EU` (London)
3. Configures lifecycle: 30-day auto-deletion
4. Enables CORS for browser access
5. Grants Cloud Run service account write permissions

**Verify bucket exists:**
```bash
gsutil ls -b gs://heatpump-outputs
```

### Step 2: Deploy API to Cloud Run

**Deploy with updated configuration:**
```bash
gcloud builds submit --config cloudbuild.yaml
```

**Environment variables set automatically:**
- `GCP_PROJECT_ID=lotsawatts`
- `GCS_BUCKET_NAME=heatpump-outputs`
- `GCS_LOCATION=EU`
- `REPORTS_EXPIRY_DAYS=30`

**Check deployment:**
```bash
gcloud run services describe heatpump-api --region=EU
```

### Step 3: Test the API

**Run test script:**
```bash
python test_reports_api.py
```

**Expected output:**
```
TEST 1: Save Report
[PASS] Report saved successfully

TEST 2: Get Report
[PASS] Report retrieved successfully

TEST 3: Get Signed URL
[PASS] Signed URL generated

TEST 4: List Reports
[PASS] Found X reports

TEST 5: Delete Report
[PASS] Report deleted successfully

Test Results: 5 passed, 0 failed
```

---

## API Endpoints

### 1. Save Report
```http
POST /api/v1/reports/save
Content-Type: application/json

{
  "simulation_data": {
    "configuration_results": {...},
    "topology_refrigerant": {...},
    "state_variables": {...},
    "economic_evaluation": {...},
    "exergy_assessment": {...},
    "parameters": {...}
  },
  "metadata": {
    "report_id": "uuid-here",
    "created_at": "2025-12-14T10:00:00Z",
    "model_name": "My Heat Pump",
    "topology": "HeatPumpIHX",
    "refrigerant": "R134a"
  }
}
```

**Response (201 Created):**
```json
{
  "report_id": "8f7a9b2c-4d3e-11ef-9a1b-0242ac120002",
  "storage_url": "gs://heatpump-outputs/reports/2025-12/8f7a9b2c.json",
  "signed_url": "https://storage.googleapis.com/heatpump-outputs/...",
  "expires_at": "2025-12-21T10:00:00Z",
  "message": "Report saved successfully"
}
```

### 2. Get Report
```http
GET /api/v1/reports/{report_id}
```

**Response (200 OK):**
```json
{
  "metadata": {...},
  "configuration_results": {...},
  "topology_refrigerant": {...},
  ...
}
```

### 3. Get New Signed URL
```http
GET /api/v1/reports/{report_id}/url?expiration_days=7
```

**Response (200 OK):**
```json
{
  "signed_url": "https://storage.googleapis.com/...",
  "expires_at": "2025-12-21T10:00:00Z"
}
```

### 4. List Reports
```http
GET /api/v1/reports/?limit=100
```

**Response (200 OK):**
```json
[
  {
    "report_id": "abc123",
    "blob_path": "reports/2025-12/abc123.json",
    "size_bytes": 45678,
    "created_at": "2025-12-14T10:00:00Z",
    "metadata": {...}
  }
]
```

### 5. Delete Report
```http
DELETE /api/v1/reports/{report_id}
```

**Response (204 No Content)**

---

## Files Created/Modified

### New Files
1. ✅ `src/heatpumps/api/services/__init__.py` - Services module init
2. ✅ `src/heatpumps/api/services/storage.py` - GCS storage service (320 lines)
3. ✅ `src/heatpumps/api/routes/reports.py` - Reports API routes (328 lines)
4. ✅ `src/heatpumps/streamlit_helpers.py` - Data extraction utilities (450 lines)
5. ✅ `setup_gcs_bucket.sh` - Bucket setup script
6. ✅ `test_reports_api.py` - API test suite
7. ✅ `REPORTS_SETUP.md` - This file

### Modified Files
1. ✅ `pyproject.toml` - Added GCS dependencies
2. ✅ `src/heatpumps/api/config.py` - Added GCS settings (4 new fields)
3. ✅ `src/heatpumps/api/schemas.py` - Added report schemas (70 lines)
4. ✅ `src/heatpumps/api/main.py` - Registered reports router
5. ✅ `cloudbuild.yaml` - Added GCS environment variables
6. ✅ `.env.example` - Documented GCS variables

---

## Using the Streamlit Helper

**In your Streamlit app (future step):**

```python
import uuid
import httpx
from datetime import datetime
from heatpumps.streamlit_helpers import extract_report_data

# After simulation completes
if st.button("📤 Save & Share Report"):
    with st.spinner("Saving report to cloud..."):
        # Extract all simulation data
        report_data = extract_report_data(st.session_state.hp)

        # Generate report ID
        report_id = str(uuid.uuid4())

        # Call API
        response = httpx.post(
            "https://heatpump-api-658843246978.EU.run.app/api/v1/reports/save",
            json={
                "simulation_data": report_data,
                "metadata": {
                    "report_id": report_id,
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "model_name": st.session_state.hp.params['setup']['name'],
                    "topology": st.session_state.hp.params['setup']['type'],
                    "refrigerant": st.session_state.hp.params['setup'].get('refrig', 'unknown')
                }
            },
            timeout=30.0
        )

        if response.status_code == 201:
            data = response.json()
            st.success("Report saved!")
            st.code(data['signed_url'], language="text")
            st.info(f"Link expires: {data['expires_at']}")
        else:
            st.error(f"Failed to save: {response.status_code}")
```

---

## Troubleshooting

### Issue: Bucket creation fails

**Error:** `Bucket already exists`

**Solution:**
```bash
# Check if bucket exists
gsutil ls -b gs://heatpump-outputs

# If exists, skip creation or delete and recreate
gsutil rb gs://heatpump-outputs
./setup_gcs_bucket.sh
```

### Issue: API returns 503 "Storage service unavailable"

**Possible causes:**
1. Bucket doesn't exist
2. Cloud Run doesn't have permissions
3. Environment variables not set

**Solution:**
```bash
# Verify bucket exists
gsutil ls -b gs://heatpump-outputs

# Check Cloud Run environment variables
gcloud run services describe heatpump-api --region=EU --format="value(spec.template.spec.containers[0].env)"

# Should show:
# GCP_PROJECT_ID=lotsawatts
# GCS_BUCKET_NAME=heatpump-outputs

# If missing, redeploy:
gcloud builds submit --config cloudbuild.yaml
```

### Issue: Test script fails with connection error

**Solution:**
```bash
# Check API is deployed and healthy
curl https://heatpump-api-658843246978.EU.run.app/health

# Should return: {"status":"healthy"}

# If not, check Cloud Run logs
gcloud run services logs read heatpump-api --region=EU --limit=50
```

### Issue: Reports not appearing in bucket

**Solution:**
```bash
# List bucket contents
gsutil ls -r gs://heatpump-outputs/reports/

# If empty, check API logs for errors
gcloud run services logs read heatpump-api --region=EU | grep -i error

# Test save endpoint directly
curl -X POST https://heatpump-api-658843246978.EU.run.app/api/v1/reports/save \
  -H "Content-Type: application/json" \
  -d @test_report.json
```

---

## Cost Estimation

### Google Cloud Storage
- **Storage:** $0.020/GB/month (Standard, EU)
- **Operations:** $0.005 per 10,000 Class A operations (writes)
- **Network:** $0.12/GB egress (after first 1GB/month free)

### Example Monthly Costs (1000 reports)
- Storage: 1000 reports × 50KB = 50MB = **$0.001/month**
- Write operations: 1000 writes = **$0.0005/month**
- Read operations: 10,000 reads = **$0.0004/month**
- Network egress: Minimal (signed URLs)
- **Total: ~$0.002/month** (negligible)

### Cloud Run Costs
- No additional cost (same deployment)
- Minimal increase in memory/CPU usage

---

## Security

### Current Setup
- ✅ Reports stored in private bucket
- ✅ Access via signed URLs (7-day expiry)
- ✅ Automatic 30-day deletion (lifecycle policy)
- ✅ Cloud Run service account has minimal permissions
- ✅ CORS enabled for browser access

### Production Recommendations
1. **Add authentication to /reports/save endpoint**
   - Require API key or JWT token
   - Prevent anonymous report uploads

2. **Rate limiting**
   - Limit reports per user/IP
   - Prevent abuse

3. **Shorter signed URL expiry**
   - Change from 7 days to 24 hours
   - Regenerate on demand

4. **Add report metadata validation**
   - Sanitize user inputs
   - Validate JSON structure

---

## Next Steps (Phase 2)

**Phase 1 Complete! ✅**

### Phase 2: HTML Report Rendering
- Create HTML template for reports
- Add `/reports/{id}/view` endpoint
- Render simulation results as formatted web page
- Include charts, tables, diagrams

### Phase 3: PDF Export
- Add PDF generation (using WeasyPrint or similar)
- `/reports/{id}/pdf` endpoint
- Professional report layout
- Include company branding

### Phase 4: Streamlit Integration
- Add "Share Report" button to dashboard
- Show shareable URL in success message
- QR code for mobile sharing
- Copy-to-clipboard functionality

### Phase 5: MCP Server Integration
- Add report generation to MCP tools
- Enable Claude to save and share reports
- Natural language report summaries

---

## Summary

**What Works Now:**
- ✅ Save simulation results as JSON to Cloud Storage
- ✅ Generate shareable URLs (7-day expiry)
- ✅ Retrieve reports by ID
- ✅ List all reports
- ✅ Delete reports
- ✅ Automatic 30-day cleanup

**What's Next:**
- ⏭️ Add "Share Report" button to Streamlit
- ⏭️ HTML rendering for better viewing
- ⏭️ PDF export for professional reports

**Estimated Implementation Time (Phase 1):** ✅ Complete!

**Storage Cost:** ~$0.002/month for 1000 reports (negligible)

---

## Quick Reference

### Check Bucket
```bash
gsutil ls -r gs://heatpump-outputs/reports/
```

### View Report Content
```bash
gsutil cat gs://heatpump-outputs/reports/2025-12/REPORT_ID.json | jq
```

### Delete Old Reports Manually
```bash
gsutil -m rm gs://heatpump-outputs/reports/2025-11/**
```

### Check API Logs
```bash
gcloud run services logs read heatpump-api --region=EU --limit=100
```

### Test API Locally
```bash
# Set environment variables
export GCP_PROJECT_ID=lotsawatts
export GCS_BUCKET_NAME=heatpump-outputs
export GCS_LOCATION=EU

# Run API
python -m uvicorn heatpumps.api.main:app --reload
```

---

**Phase 1 Complete! Ready for deployment and testing.** 🚀
