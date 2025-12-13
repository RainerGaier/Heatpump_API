# Heatpump Simulator API

REST API wrapper for the heatpump configurator/simulator, providing programmatic access to all simulation capabilities.

## Features

- **Design Point Simulation**: Calculate steady-state performance for heat pump models
- **Model Discovery**: List available models, parameters, and refrigerants
- **Parameter Customization**: Override default parameters via JSON
- **Async Support**: Background task processing (coming soon)
- **Auto-generated Docs**: Interactive API documentation at `/docs`

## Quick Start

### Installation

The API dependencies are included in the main package. Install the package with:

```bash
cd heatpumps-main
pip install -e .
```

### Running the API Server

#### Option 1: Using the CLI command
```bash
heatpumps-api
```

#### Option 2: Using uvicorn directly
```bash
uvicorn heatpumps.api.main:app --reload --port 8000
```

#### Option 3: Using Python
```python
from heatpumps.api.main import run
run()
```

The API will be available at: `http://localhost:8000`

### Interactive Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health & Info

- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint

### Models

- `GET /api/v1/models` - List all available heat pump models
- `GET /api/v1/models/{model_name}` - Get details about a specific model
- `GET /api/v1/models/{model_name}/parameters` - Get default parameters for a model
- `GET /api/v1/models/refrigerants/list` - List supported refrigerants

### Simulation

- `POST /api/v1/simulate/design` - Run design point simulation ✅
- `POST /api/v1/simulate/partload` - Run part-load characteristics ✅
- `POST /api/v1/simulate/offdesign` - Run off-design simulation with temperature sweeps ✅
- `POST /api/v1/simulate/design/detailed` - Run simulation with detailed results (coming soon)
- `POST /api/v1/simulate/async` - Submit async simulation task (coming soon)

### Tasks (Async)

- `GET /api/v1/tasks/{task_id}` - Get task status (coming soon)
- `DELETE /api/v1/tasks/{task_id}` - Cancel a running task (coming soon)
- `GET /api/v1/tasks` - List tasks (coming soon)

## Usage Examples

### Example 1: List Available Models

```bash
curl http://localhost:8000/api/v1/models
```

Response:
```json
{
  "models": [
    {
      "name": "HeatPumpSimple",
      "display_name": "simple cycle",
      "topology": "base",
      "has_ihx": false,
      "has_economizer": false
    },
    ...
  ],
  "total_count": 46
}
```

### Example 2: Get Default Parameters

```bash
curl http://localhost:8000/api/v1/models/simple/parameters
```

### Example 3: Run Design Simulation

**Note:** Use the lowercase model key (e.g., `"simple"`, `"ihx"`, `"econ_closed"`), not the class name.

```bash
curl -X POST http://localhost:8000/api/v1/simulate/design \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "simple",
    "params": {
      "T_hs_ff": 10.0,
      "T_cons_ff": 35.0
    }
  }'
```

Response:
```json
{
  "model_name": "simple",
  "converged": true,
  "cop": 4.23,
  "epsilon": 0.58,
  "heat_output": 10500.0,
  "power_input": 2482.0,
  "cost_total": null
}
```

### Example 4: Python Client

```python
import httpx

# List models
response = httpx.get("http://localhost:8000/api/v1/models")
models = response.json()
print(f"Available models: {models['total_count']}")

# Run simulation (use lowercase model key)
simulation_request = {
    "model_name": "simple",
    "params": {
        "T_hs_ff": 15.0,
        "T_cons_ff": 40.0
    }
}

response = httpx.post(
    "http://localhost:8000/api/v1/simulate/design",
    json=simulation_request,
    timeout=60.0
)

result = response.json()
print(f"COP: {result['cop']}")
print(f"Heat Output: {result['heat_output']} W")
```

### Example 5: Part-Load Characteristics

**Note:** This endpoint takes 1-3 minutes as it runs design + off-design simulations.

```bash
curl -X POST http://localhost:8000/api/v1/simulate/partload \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "simple",
    "params": {}
  }'
```

Response:
```json
{
  "model_name": "simple",
  "converged": true,
  "design_cop": 4.23,
  "design_heat_output": 10500000.0,
  "partload_points": [
    {
      "load_ratio": 0.3,
      "cop": 3.85,
      "heat_output": 3150000.0,
      "power_input": 818200.0,
      "epsilon": 0.52,
      "converged": true
    },
    {
      "load_ratio": 0.5,
      "cop": 4.12,
      "heat_output": 5250000.0,
      "power_input": 1274500.0,
      "epsilon": 0.56,
      "converged": true
    },
    {
      "load_ratio": 0.75,
      "cop": 4.19,
      "heat_output": 7875000.0,
      "power_input": 1879700.0,
      "epsilon": 0.57,
      "converged": true
    },
    {
      "load_ratio": 1.0,
      "cop": 4.23,
      "heat_output": 10500000.0,
      "power_input": 2482000.0,
      "epsilon": 0.58,
      "converged": true
    }
  ],
  "total_points": 8,
  "converged_points": 8
}
```

**Use Cases for Part-Load:**
- Calculate seasonal performance (SCOP)
- Analyze real-world efficiency at varying loads
- Optimize control strategies
- Compare variable-speed vs fixed-speed compressors

### Example 6: Custom Part-Load Range

Control the part-load range for more targeted analysis:

```bash
curl -X POST http://localhost:8000/api/v1/simulate/partload \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "simple",
    "params": {},
    "partload_config": {
      "min_ratio": 0.5,
      "max_ratio": 1.0,
      "steps": 5
    }
  }'
```

Response includes only the specified load range (50%-100% in 5 steps).

### Example 7: Off-Design Simulation with Temperature Sweeps

Run comprehensive off-design analysis across temperature and load ranges:

```bash
curl -X POST http://localhost:8000/api/v1/simulate/offdesign \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "simple",
    "params": {},
    "offdesign_config": {
      "heat_source_range": {
        "constant": false,
        "start": 5.0,
        "end": 20.0,
        "steps": 4
      },
      "heat_sink_range": {
        "constant": false,
        "start": 30.0,
        "end": 55.0,
        "steps": 6
      },
      "partload_range": {
        "min_ratio": 0.3,
        "max_ratio": 1.0,
        "steps": 8
      }
    }
  }'
```

Response:
```json
{
  "model_name": "simple",
  "converged": true,
  "design_cop": 4.23,
  "design_heat_output": 10500000.0,
  "temperature_range": {
    "T_hs_ff": [5.0, 10.0, 15.0, 20.0],
    "T_cons_ff": [30.0, 40.0, 45.0, 50.0, 55.0]
  },
  "partload_range": [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
  "operating_points": [
    {
      "T_hs_ff": 5.0,
      "T_cons_ff": 30.0,
      "partload_ratio": 0.3,
      "cop": 3.85,
      "heat_output": 3150000.0,
      "power_input": 818200.0,
      "epsilon": 0.52,
      "converged": true
    },
    // ... 191 more points (4 × 6 × 8 = 192 total)
  ],
  "total_points": 192,
  "converged_points": 189
}
```

**Use Cases for Off-Design:**
- Generate performance maps across operating envelope
- Analyze COP degradation at extreme conditions
- Identify optimal operating ranges
- Export data for building energy simulations
- Validate against manufacturer datasheets

**Configuration Options:**

You can keep temperatures constant or sweep them:

```json
{
  "heat_source_range": {
    "constant": true  // Use design point temperature only
  },
  "heat_sink_range": {
    "constant": false,
    "start": 30.0,
    "end": 60.0,
    "steps": 7
  }
}
```

### Example 8: IHX Parameter Override

For models with internal heat exchangers (IHX), override the superheat temperature difference:

```bash
curl -X POST http://localhost:8000/api/v1/simulate/design \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "ihx",
    "params": {
      "ihx": {
        "dT_sh": 10.0
      }
    }
  }'
```

**IHX Models and Parameters:**

- Single IHX models (e.g., `ihx`, `ihx_trans`): Use `params.ihx.dT_sh`
- Dual IHX models (e.g., `cascade_2ihx`): Use `params.ihx1.dT_sh` and `params.ihx2.dT_sh`
- Quad IHX models: Use `params.ihx1.dT_sh` through `params.ihx4.dT_sh`

To check if a model has IHX support:
```bash
curl http://localhost:8000/api/v1/models/ihx
# Check the "nr_ihx" field in the response
```

## Configuration

Configuration is managed via environment variables. Copy `.env.example` to `.env` and adjust:

```bash
cp .env.example .env
```

Key settings:

```env
HOST=0.0.0.0              # Server host
PORT=8000                 # Server port
DEBUG=true                # Enable debug mode
LOG_LEVEL=INFO            # Logging level
SIMULATION_TIMEOUT=300    # Max simulation time (seconds)
```

## Architecture

### Directory Structure

```
src/heatpumps/api/
├── __init__.py           # Package initialization
├── main.py               # FastAPI app and entry point
├── config.py             # Configuration settings
├── schemas.py            # Pydantic request/response models
├── dependencies.py       # Shared dependencies
├── workers.py            # Background task workers
└── routes/
    ├── simulate.py       # Simulation endpoints
    ├── models.py         # Model info endpoints
    └── tasks.py          # Task management endpoints
```

### How It Works

1. **Shared Core**: API and Streamlit dashboard both use the same simulation engine from `heatpumps.models`
2. **Parameter-Driven**: JSON parameters map directly to model configurations
3. **Validation**: Pydantic schemas ensure type safety and validation
4. **Extensible**: Easy to add new endpoints and features

## Co-existence with Streamlit Dashboard

The API and Streamlit dashboard can run simultaneously:

```bash
# Terminal 1 - Streamlit Dashboard
heatpumps-dashboard

# Terminal 2 - FastAPI Server
heatpumps-api
```

They share the same simulation engine but serve different purposes:
- **Dashboard**: Interactive exploration and visualization
- **API**: Programmatic access and automation

## Development

### Running in Development Mode

```bash
# With auto-reload
uvicorn heatpumps.api.main:app --reload --port 8000

# With DEBUG enabled
DEBUG=true heatpumps-api
```

### Testing

```bash
# Run tests (coming soon)
pytest tests/api/

# Test specific endpoint
curl -X POST http://localhost:8000/api/v1/simulate/design \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

## Future Enhancements

- [x] Part-load simulation endpoint ✅ **IMPLEMENTED**
- [x] Custom part-load range configuration ✅ **IMPLEMENTED**
- [x] Off-design simulation endpoint with temperature sweeps ✅ **IMPLEMENTED**
- [x] IHX parameter override support ✅ **IMPLEMENTED**
- [ ] Add async task processing with Celery/RQ
- [ ] Result caching with Redis
- [ ] API key authentication
- [ ] Rate limiting
- [ ] Detailed state point results
- [ ] Export results to CSV/Excel
- [ ] Batch simulation support
- [ ] WebSocket for real-time progress updates

## Deployment

### Docker (Coming Soon)

```bash
docker build -t heatpump-api .
docker run -p 8000:8000 heatpump-api
```

### Production

For production deployment:

1. Set `DEBUG=false` in `.env`
2. Use a production ASGI server (gunicorn + uvicorn)
3. Set up reverse proxy (nginx)
4. Enable authentication and rate limiting
5. Configure proper logging
6. Use Redis for caching and task queue

```bash
gunicorn heatpumps.api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Use different port
PORT=8001 heatpumps-api
```

### Import Errors

Make sure the package is installed:
```bash
pip install -e .
```

### Simulation Not Converging

If simulations fail to converge:
- Check parameter values are reasonable
- Adjust pressure ratios and temperature differences
- Review the error message in the response

## Support

For issues or questions:
- Check the interactive docs at `/docs`
- Review the main heatpumps documentation
- Open an issue on GitHub

## License

MIT License - Same as the main heatpumps package
