# API Structure Overview

## Complete Directory Structure

```
heatpumps-main/
├── src/heatpumps/
│   ├── models/                    # Core simulation engine (SHARED)
│   │   ├── HeatPumpBase.py
│   │   ├── HeatPumpSimple.py
│   │   └── ... (46 model classes)
│   ├── parameters.py              # Parameter loading (SHARED)
│   ├── simulation.py              # Simulation helpers (SHARED)
│   ├── variables.py               # Model registry (SHARED)
│   ├── hp_dashboard.py            # Streamlit UI
│   ├── run_dashboard.py           # Dashboard CLI
│   └── api/                       # NEW: FastAPI wrapper
│       ├── __init__.py            # Package init
│       ├── main.py                # FastAPI app & entry point
│       ├── config.py              # Settings & environment vars
│       ├── schemas.py             # Pydantic models (validation)
│       ├── dependencies.py        # Shared dependencies
│       ├── workers.py             # Background task workers
│       └── routes/
│           ├── __init__.py
│           ├── simulate.py        # Simulation endpoints
│           ├── models.py          # Model info endpoints
│           └── tasks.py           # Task management endpoints
├── pyproject.toml                 # Updated with API deps
├── .env.example                   # NEW: Config template
├── API_README.md                  # NEW: API documentation
└── API_STRUCTURE.md               # This file
```

## File Summary

### Core API Files

| File | Purpose | Status |
|------|---------|--------|
| `api/__init__.py` | Package initialization | ✅ Complete |
| `api/main.py` | FastAPI app, CORS, exception handling, CLI entry point | ✅ Complete |
| `api/config.py` | Environment-based configuration with pydantic-settings | ✅ Complete |
| `api/schemas.py` | 15+ Pydantic models for request/response validation | ✅ Complete |
| `api/dependencies.py` | Dependency injection (auth, rate limiting, services) | ✅ Stub |
| `api/workers.py` | Background task execution & webhook support | ✅ Stub |

### Route Modules

| File | Endpoints | Status |
|------|-----------|--------|
| `routes/simulate.py` | POST /design, /design/detailed, /offdesign, /partload, /async | ✅ /design complete<br>⚠️ Others stubbed |
| `routes/models.py` | GET /models, /{model_name}, /{model_name}/parameters, /refrigerants/list | ✅ Complete |
| `routes/tasks.py` | GET/DELETE /tasks/{task_id}, GET /tasks | ⚠️ Stubbed |

## API Endpoints

### ✅ Currently Functional

```
GET  /                                           # API info
GET  /health                                     # Health check
GET  /api/v1/models                             # List all models
GET  /api/v1/models/{model_name}                # Model details
GET  /api/v1/models/{model_name}/parameters     # Default parameters
GET  /api/v1/models/refrigerants/list           # List refrigerants
POST /api/v1/simulate/design                    # Run design simulation
```

### ⚠️ Stubbed (Returns 501 Not Implemented)

```
POST /api/v1/simulate/design/detailed           # Detailed results
POST /api/v1/simulate/offdesign                 # Off-design sweep
POST /api/v1/simulate/partload                  # Part-load characteristics
POST /api/v1/simulate/async                     # Async task submission
GET  /api/v1/tasks/{task_id}                    # Task status
```

## How Streamlit & API Co-exist

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interfaces                          │
├──────────────────────────┬──────────────────────────────────┤
│   Streamlit Dashboard    │         FastAPI Wrapper          │
│   (hp_dashboard.py)      │         (api/main.py)            │
│   Port: 8501             │         Port: 8000               │
│   For: Human users       │         For: Programmatic access │
└──────────────┬───────────┴───────────────┬──────────────────┘
               │                           │
               └───────────┬───────────────┘
                          │
            ┌─────────────▼──────────────┐
            │   Shared Core Engine       │
            ├────────────────────────────┤
            │ • models/ (46 classes)     │
            │ • parameters.py            │
            │ • simulation.py            │
            │ • variables.py             │
            └────────────────────────────┘
```

**Both interfaces:**
- Use the same simulation logic
- Share parameter loading
- Call identical model classes
- Can run simultaneously on different ports

## Running Both Services

```bash
# Terminal 1 - Streamlit (existing)
heatpumps-dashboard
# Access at: http://localhost:8501

# Terminal 2 - FastAPI (new)
heatpumps-api
# Access at: http://localhost:8000
# Docs at: http://localhost:8000/docs
```

## Dependencies Added to pyproject.toml

```toml
"fastapi>=0.115.0",           # Web framework
"uvicorn[standard]>=0.32.0",  # ASGI server
"pydantic>=2.10.0",           # Data validation
"pydantic-settings>=2.6.0",   # Environment config
"httpx>=0.28.0",              # HTTP client (for webhooks)
```

## Configuration

Environment variables (`.env` file):

```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8501

# Features (future)
API_KEY_ENABLED=false
RATE_LIMIT_ENABLED=false
CACHE_ENABLED=false
```

## Quick Test

```bash
# Install dependencies
pip install -e .

# Start API
heatpumps-api

# Test in another terminal
curl http://localhost:8000/api/v1/models | python -m json.tool
```

## Next Steps for Full Implementation

1. **Implement off-design simulation** in `routes/simulate.py`
2. **Implement part-load simulation** in `routes/simulate.py`
3. **Add detailed results extraction** (state points, exergy)
4. **Set up Celery/RQ** for async tasks
5. **Add Redis caching** for duplicate simulations
6. **Implement authentication** (API keys)
7. **Add rate limiting** (per-client limits)
8. **Create Dockerfile** for containerized deployment
9. **Write API integration tests**
10. **Add CI/CD pipeline**

## Design Principles

✅ **Separation of Concerns**: UI and API are separate but share core logic
✅ **No Code Duplication**: Single source of truth for simulation
✅ **Backward Compatible**: Streamlit dashboard unchanged
✅ **Extensible**: Easy to add new endpoints
✅ **Standards-Based**: OpenAPI/Swagger, REST conventions
✅ **Production-Ready Foundation**: Config management, error handling, logging
