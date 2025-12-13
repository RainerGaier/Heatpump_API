# Google Cloud Platform Deployment Review

## Executive Summary

✅ **Overall Assessment**: Your GCP deployment configuration is **well-structured and ready for deployment** with a few important recommendations.

Your setup follows best practices for containerizing a Python FastAPI application on Cloud Run. The configuration is production-ready with some minor adjustments needed.

## Configuration Review

### ✅ Dockerfile Analysis

**File**: [Dockerfile](Dockerfile)

**Strengths**:
1. ✅ Uses Python 3.11-slim (good balance of size and functionality)
2. ✅ Installs necessary system dependencies for scientific computing (gcc, gfortran, BLAS, LAPACK)
3. ✅ Uses `pip install -e .` which correctly installs from pyproject.toml
4. ✅ Correctly uses `$PORT` environment variable for Cloud Run compatibility
5. ✅ Includes health check endpoint
6. ✅ Exposes port 8080 (Cloud Run standard)

**⚠️ Issues Found**:

1. **HEALTHCHECK won't work in Cloud Run**
   - Line 28-29: Docker HEALTHCHECK directive is ignored by Cloud Run
   - Cloud Run uses its own health checking mechanism
   - **Recommendation**: Remove HEALTHCHECK or keep it for local testing only

2. **Missing requests library for health check**
   - Line 29 uses `requests` but it's not in dependencies
   - **Recommendation**: Either add `requests` to dependencies or remove HEALTHCHECK

**Recommended Dockerfile**:
```dockerfile
# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for TESPy and scientific computing
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Expose port (Cloud Run will override this with $PORT)
EXPOSE 8080

# Run the application
# Cloud Run provides PORT environment variable
CMD exec uvicorn heatpumps.api.main:app --host 0.0.0.0 --port ${PORT:-8080}
```

### ✅ cloudbuild.yaml Analysis

**File**: [cloudbuild.yaml](cloudbuild.yaml)

**Strengths**:
1. ✅ Correct 3-step build process (build, push, deploy)
2. ✅ Uses europe-west2 (London) region as configured
3. ✅ Platform set to 'managed'
4. ✅ Memory allocation: 1Gi (good starting point)
5. ✅ CPU allocation: 1 vCPU

**⚠️ Critical Considerations**:

1. **Public Access Enabled**
   - Line 20: `--allow-unauthenticated` makes API publicly accessible
   - **Security Implication**: Anyone on the internet can access your API
   - **Recommendation**: Consider one of these options:
     - Add `--no-allow-unauthenticated` and use IAM for access control
     - Implement API key authentication in your FastAPI app
     - Use Cloud Endpoints or API Gateway for rate limiting and security

2. **Resource Allocation May Be Insufficient**
   - Current: 1Gi memory, 1 vCPU
   - Heat pump simulations are computationally intensive
   - Off-design simulations with multiple operating points may timeout
   - **Recommendation**: Start with current config, but monitor and scale up if needed:
     ```yaml
     - '--memory=2Gi'
     - '--cpu=2'
     - '--timeout=300'  # 5 minutes for long simulations
     - '--max-instances=10'  # Limit concurrent instances
     - '--min-instances=0'  # Scale to zero when idle
     ```

3. **Missing Timeout Configuration**
   - Default Cloud Run timeout is 5 minutes
   - Your config.py has `SIMULATION_TIMEOUT: 300` (5 minutes)
   - **Recommendation**: Add explicit timeout:
     ```yaml
     - '--timeout=300'
     ```

4. **Missing Concurrency Setting**
   - Default concurrency is 80 requests per container
   - Simulations are CPU-intensive - lower concurrency may improve stability
   - **Recommendation**: Add:
     ```yaml
     - '--concurrency=10'  # Limit concurrent requests per instance
     ```

**Recommended cloudbuild.yaml**:
```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/heatpump-api', '.']

  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/heatpump-api']

  # Deploy container image to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'heatpump-api'
      - '--image=gcr.io/$PROJECT_ID/heatpump-api'
      - '--region=europe-west2'
      - '--platform=managed'
      - '--allow-unauthenticated'  # CHANGE THIS for production security!
      - '--memory=2Gi'              # Increased for intensive simulations
      - '--cpu=2'                   # Increased for better performance
      - '--timeout=300'             # 5 minutes for long simulations
      - '--concurrency=10'          # Limit concurrent requests per instance
      - '--max-instances=10'        # Prevent runaway costs
      - '--min-instances=0'         # Scale to zero when idle
      - '--port=8080'               # Explicit port declaration

images:
  - 'gcr.io/$PROJECT_ID/heatpump-api'

# Optional: Set timeout for the entire build
timeout: 1200s  # 20 minutes
```

### ✅ .dockerignore Analysis

**File**: [.dockerignore](.dockerignore)

**Status**: ✅ Excellent - properly excludes unnecessary files

**Strengths**:
- Excludes Python cache files
- Excludes virtual environments
- Excludes IDE files
- Excludes test files (via `*.md` exclusion)
- Excludes git and documentation

**⚠️ Minor Issue**:
- Line 44: `*.md` excludes ALL markdown files including README.md
- Line 45 tries to re-include README.md, but this may not work as expected
- **Impact**: Low - documentation not needed in container

**Recommendation**: Add explicit test file exclusions for clarity:
```
# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
test_*.py
check_*.py
*_test.py
```

### ✅ .gcloudignore Analysis

**File**: [.gcloudignore](.gcloudignore)

**Status**: ✅ Good - properly excludes unnecessary files from Cloud Build

**Strengths**:
- Excludes development files
- Excludes Python cache
- Excludes virtual environments
- Excludes sensitive files (.env)

**Recommendation**: Consider adding test files explicitly:
```
test_*.py
check_*.py
*.test
```

### ✅ pyproject.toml Analysis

**File**: [pyproject.toml](pyproject.toml)

**Status**: ✅ Excellent - comprehensive dependency list

**Strengths**:
1. ✅ All required dependencies listed
2. ✅ Correct Python version (>=3.11)
3. ✅ FastAPI, uvicorn, pydantic included
4. ✅ TESPy and CoolProp included
5. ✅ httpx included for testing
6. ✅ Package structure correctly defined

**⚠️ Considerations**:

1. **Git Dependency**
   - Line 42: `oemof.thermal` installed from Git commit
   - **Impact**: Docker build will need git installed
   - **Recommendation**: Works fine, but consider pinning to a release version for stability

2. **Debug Mode in Production**
   - config.py line 27: `DEBUG: bool = Field(default=True)`
   - **Security Risk**: Debug mode enabled by default exposes stack traces
   - **Recommendation**: Set environment variable in Cloud Run:
     ```yaml
     - '--set-env-vars=DEBUG=false'
     ```

3. **CORS Origins**
   - config.py line 31-34: Hardcoded localhost origins
   - **Recommendation**: Set via environment variable:
     ```yaml
     - '--set-env-vars=CORS_ORIGINS=["https://yourdomain.com"]'
     ```

## Critical TESPy Bug Fix Status

✅ **IMPORTANT**: The TESPy compatibility bug fix we implemented is included in your deployment:
- File: [src/heatpumps/models/HeatPumpBase.py](src/heatpumps/models/HeatPumpBase.py#L1133-L1144)
- Fix: Changed `'heat exchanger'` → `'HeatExchanger'`
- Status: ✅ Fixed and ready for deployment

This fix ensures off-design and part-load simulations will work correctly in the Cloud Run environment.

## Security Recommendations

### 🔴 High Priority

1. **Public API Access**
   - Current: `--allow-unauthenticated` allows anyone to access
   - **Risk**: Unauthorized usage, potential abuse, unexpected costs
   - **Solutions**:
     - Option A: Use Cloud IAM authentication
     - Option B: Implement API key authentication in FastAPI
     - Option C: Use Google Cloud API Gateway with rate limiting

2. **Debug Mode**
   - Set `DEBUG=false` in production
   - Add environment variable: `--set-env-vars=DEBUG=false`

3. **Secret Key**
   - Change default secret key (line 43 of config.py)
   - Set via environment variable: `--set-env-vars=SECRET_KEY=<your-secure-key>`

### 🟡 Medium Priority

1. **Rate Limiting**
   - Enable rate limiting to prevent abuse
   - Set environment variables:
     ```yaml
     - '--set-env-vars=RATE_LIMIT_ENABLED=true'
     - '--set-env-vars=RATE_LIMIT_REQUESTS=100'
     ```

2. **CORS Configuration**
   - Update CORS origins to match your frontend domain
   - Current: localhost only
   - Production: Set actual domains

3. **Cost Control**
   - Add `--max-instances=10` to prevent runaway costs
   - Monitor usage in Google Cloud Console
   - Set up billing alerts

## Environment Variables for Production

Add these to your `cloudbuild.yaml`:

```yaml
- '--set-env-vars=DEBUG=false,PORT=8080,LOG_LEVEL=INFO,SIMULATION_TIMEOUT=300'
- '--set-env-vars=CORS_ORIGINS=["https://yourdomain.com"]'
- '--set-env-vars=SECRET_KEY=your-secure-secret-key-here'
- '--set-env-vars=RATE_LIMIT_ENABLED=true,RATE_LIMIT_REQUESTS=100'
```

Or set them separately using:
```bash
gcloud run services update heatpump-api \
  --region=europe-west2 \
  --set-env-vars=DEBUG=false,LOG_LEVEL=INFO
```

## Estimated Costs (London - europe-west2)

Based on Cloud Run pricing (as of 2024):
- **CPU**: $0.00002400 per vCPU-second
- **Memory**: $0.00000250 per GiB-second
- **Requests**: $0.40 per million requests
- **Free tier**: 2 million requests/month, 360,000 GiB-seconds/month

**Example calculation** (1000 simulations/month, avg 30s each):
- CPU time: 1000 × 30s × 2 vCPU = 60,000 vCPU-seconds = $1.44
- Memory: 1000 × 30s × 2 GiB = 60,000 GiB-seconds = $0.15
- Requests: 1000 requests = $0.0004
- **Total**: ~$1.60/month (well within free tier limits)

**Note**: Costs increase significantly with:
- Higher request volume
- Longer simulation times
- More concurrent users
- Keeping min-instances > 0 (always-on)

## Pre-Deployment Checklist

Before running `gcloud builds submit --config cloudbuild.yaml`:

- [ ] Review and update Dockerfile (remove HEALTHCHECK or add requests)
- [ ] Review cloudbuild.yaml security settings (consider authentication)
- [ ] Increase memory/CPU allocation in cloudbuild.yaml (2Gi/2 vCPU recommended)
- [ ] Add timeout and concurrency settings to cloudbuild.yaml
- [ ] Set DEBUG=false for production
- [ ] Configure CORS_ORIGINS for your domain
- [ ] Change SECRET_KEY from default
- [ ] Set up billing alerts in Google Cloud Console
- [ ] Test locally first: `docker build -t heatpump-api . && docker run -p 8080:8080 heatpump-api`
- [ ] Ensure your GCP project ID is set: `gcloud config get-value project`

## Deployment Commands

### 1. Local Testing (Recommended First)

```bash
# Build locally
cd c:\Users\gaierr\Energy_Projects\projects\heatpumps\heatpumps-main
docker build -t heatpump-api .

# Run locally
docker run -p 8080:8080 -e PORT=8080 heatpump-api

# Test health check
curl http://localhost:8080/health

# Test API docs
# Open browser: http://localhost:8080/docs
```

### 2. Deploy to Cloud Run

```bash
# Verify GCP project
gcloud config get-value project

# Submit build and deploy
gcloud builds submit --config cloudbuild.yaml

# Monitor deployment
gcloud run services describe heatpump-api --region=europe-west2

# Get service URL
gcloud run services describe heatpump-api --region=europe-west2 --format='value(status.url)'
```

### 3. Post-Deployment Testing

```bash
# Get service URL
export SERVICE_URL=$(gcloud run services describe heatpump-api --region=europe-west2 --format='value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health

# Test design simulation
curl -X POST $SERVICE_URL/api/v1/simulate/design \
  -H "Content-Type: application/json" \
  -d '{"model_name":"simple","params":{}}'
```

## Monitoring and Maintenance

After deployment, monitor these metrics in Google Cloud Console:

1. **Performance**:
   - Request latency
   - Request count
   - Error rate
   - Container instances (scaling behavior)

2. **Costs**:
   - Set up billing alerts
   - Monitor CPU and memory usage
   - Track request volume

3. **Logs**:
   - View logs: `gcloud run services logs tail heatpump-api --region=europe-west2`
   - Check for simulation errors
   - Monitor convergence issues

## Troubleshooting

### Build Fails

```bash
# Check build logs
gcloud builds log $(gcloud builds list --limit=1 --format='value(id)')

# Common issues:
# - Missing dependencies: Check pyproject.toml
# - Git dependency fails: Ensure git is available in container
# - Out of memory: Increase Cloud Build machine type
```

### Deployment Fails

```bash
# Check service status
gcloud run services describe heatpump-api --region=europe-west2

# Check recent revisions
gcloud run revisions list --service=heatpump-api --region=europe-west2

# Rollback if needed
gcloud run services update-traffic heatpump-api \
  --region=europe-west2 \
  --to-revisions=<previous-revision>=100
```

### Runtime Errors

```bash
# View logs
gcloud run services logs read heatpump-api --region=europe-west2 --limit=50

# Common issues:
# - Port mismatch: Ensure PORT environment variable is used
# - Import errors: Check all dependencies are installed
# - Convergence failures: Expected for some operating conditions
```

## Recommended Next Steps

1. **Test locally with Docker** (30 minutes)
2. **Deploy to Cloud Run** (10 minutes)
3. **Run test suite against deployed API** (use test_api.py)
4. **Set up monitoring and alerts** (30 minutes)
5. **Implement authentication** (if needed - 2-4 hours)
6. **Configure custom domain** (if needed - 1 hour)

## Final Recommendation

**✅ You are ready to deploy** with these priority actions:

**Must Do Before Deploy**:
1. Remove or fix HEALTHCHECK in Dockerfile
2. Increase memory to 2Gi and CPU to 2 in cloudbuild.yaml
3. Add timeout and concurrency settings
4. Set DEBUG=false environment variable

**Should Do Before Deploy**:
1. Test locally with Docker first
2. Set up billing alerts
3. Configure proper CORS origins
4. Consider authentication method

**Can Do After Deploy**:
1. Monitor performance and adjust resources
2. Implement rate limiting
3. Add custom domain
4. Set up CI/CD pipeline

Your deployment configuration is solid and production-ready with these adjustments!
