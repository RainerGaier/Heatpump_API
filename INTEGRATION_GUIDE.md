# Heat Pump Simulation Application - Integration Guide

**Version:** 1.0
**Date:** December 2024
**Author:** Rainer Gaier
**Project:** UK Hackathon - Data Centre Cooling Analysis

---

## Table of Contents

1. [Overview & Purpose](#overview--purpose)
2. [Architecture](#architecture)
3. [Process Flow](#process-flow)
4. [Components](#components)
   - [FastAPI REST API](#1-fastapi-rest-api)
   - [MCP Server (Claude Desktop Integration)](#2-mcp-server-claude-desktop-integration)
   - [Streamlit Web Application](#3-streamlit-web-application)
5. [Google Cloud Services](#google-cloud-services)
6. [Data Formats](#data-formats)
7. [Report Types](#report-types)
8. [Integration Options](#integration-options)
9. [API Reference](#api-reference)
10. [MCP Server Usage](#mcp-server-usage)
11. [When to Use What](#when-to-use-what)

---

## Overview & Purpose

The **Heat Pump Simulation Application** is a comprehensive thermodynamic modelling platform designed for:

- **Data Centre Cooling Analysis**: Evaluating heat pump performance for large-scale cooling (1-100+ MW)
- **Heat Recovery Assessment**: Calculating potential district heating integration
- **Topology Comparison**: Comparing different heat pump configurations (simple, IHX, economizer variants)
- **Multi-Refrigerant Analysis**: Supporting R134a, R717 (Ammonia), R290 (Propane), R1234yf, and more
- **Economic Evaluation**: Cost estimation with CEPCI adjustment and multi-currency support

The application uses **TESPy** (Thermal Engineering Systems in Python) as its core simulation engine, providing physics-based thermodynamic calculations.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACES                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐     │
│   │   Streamlit UI   │    │  Claude Desktop  │    │   Direct API     │     │
│   │   (Full Reports) │    │   (via MCP)      │    │   Consumers      │     │
│   └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘     │
│            │                       │                       │                │
└────────────┼───────────────────────┼───────────────────────┼────────────────┘
             │                       │                       │
             ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          GOOGLE CLOUD RUN                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     FastAPI REST API                                 │   │
│   │                                                                      │   │
│   │   Endpoints:                                                         │   │
│   │   • /api/v1/models      - List available topologies                 │   │
│   │   • /api/v1/simulate    - Run thermodynamic simulations             │   │
│   │   • /api/v1/reports     - Save/retrieve/view reports                │   │
│   │   • /api/v1/tasks       - Async simulation management               │   │
│   │                                                                      │   │
│   │   URL: https://heatpump-api-382432690682.europe-west1.run.app       │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
└────────────────────────────────────┼─────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GOOGLE CLOUD STORAGE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Bucket: heatpump-reports-lotsawatts                                       │
│   • JSON report data (with 7-day lifecycle expiry)                          │
│   • Signed URLs for secure access                                            │
│   • Region: europe-west1                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Process Flow

### Input → Processing → Output

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              INPUTS                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. TOPOLOGY SELECTION                                                       │
│     • Simple cycle, IHX (Internal Heat Exchanger)                           │
│     • Economizer variants (open/closed, with/without IHX)                   │
│     • Intercooler, Transcritical CO2                                        │
│                                                                              │
│  2. REFRIGERANT SELECTION                                                    │
│     • Synthetic: R134a, R1234yf, R410A                                      │
│     • Natural: R717 (Ammonia), R290 (Propane), R744 (CO2)                   │
│                                                                              │
│  3. OPERATING CONDITIONS                                                     │
│     • Evaporator inlet/outlet temperatures (heat source)                    │
│     • Condenser inlet/outlet temperatures (heat sink)                       │
│     • Cooling/heating capacity (kW or MW)                                   │
│                                                                              │
│  4. COMPONENT PARAMETERS (Optional)                                          │
│     • Compressor efficiency, heat exchanger approach temps                  │
│     • Pressure drops, superheat/subcooling                                  │
│                                                                              │
│  5. COST PARAMETERS (Optional)                                               │
│     • Reference year, CEPCI values                                          │
│     • Display currency (24 currencies supported)                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PROCESSING                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. TESPY THERMODYNAMIC SIMULATION                                           │
│     • Builds component network based on topology                            │
│     • Applies refrigerant properties (CoolProp)                             │
│     • Solves mass/energy balances iteratively                               │
│     • Calculates state points at each connection                            │
│                                                                              │
│  2. PERFORMANCE CALCULATIONS                                                 │
│     • COP (Coefficient of Performance)                                       │
│     • Heat output (W), Power input (W)                                       │
│     • Exergy efficiency (ε)                                                  │
│                                                                              │
│  3. EXERGY ANALYSIS                                                          │
│     • Fuel/Product exergy for each component                                │
│     • Exergy destruction rates                                              │
│     • Component-level efficiency breakdown                                   │
│                                                                              │
│  4. ECONOMIC EVALUATION                                                      │
│     • Component costs (Kosmadakis 2023 correlations)                        │
│     • CEPCI inflation adjustment                                            │
│     • Currency conversion (EUR base → selected currency)                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              OUTPUTS                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. CONFIGURATION RESULTS                                                    │
│     • COP, heat output (W), power input (W)                                 │
│     • Exergy efficiency, convergence status                                 │
│                                                                              │
│  2. STATE VARIABLES TABLE                                                    │
│     • Temperature (K/°C), Pressure (bar), Enthalpy (kJ/kg)                  │
│     • Entropy (kJ/kg·K), Mass flow (kg/s) at each connection               │
│                                                                              │
│  3. THERMODYNAMIC DIAGRAMS                                                   │
│     • P-h (Pressure-Enthalpy) diagram with cycle overlay                   │
│     • T-s (Temperature-Entropy) diagram with cycle overlay                 │
│     • Topology schematic (SVG)                                              │
│                                                                              │
│  4. EXERGY ASSESSMENT                                                        │
│     • Component exergy table (E_F, E_P, E_D, ε, y*, y)                      │
│     • Sankey diagram (exergy flows)                                         │
│                                                                              │
│  5. ECONOMIC EVALUATION                                                      │
│     • Component-level costs                                                  │
│     • Total investment cost (in selected currency)                          │
│                                                                              │
│  6. SAVED REPORTS                                                            │
│     • JSON data (Cloud Storage, 7-day expiry)                               │
│     • HTML report (browser viewable)                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. FastAPI REST API

**Deployment:** Google Cloud Run
**URL:** `https://heatpump-api-382432690682.europe-west1.run.app`
**Documentation:**
- Swagger UI: `/docs`
- ReDoc: `/redoc`

#### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint with API info |
| `/health` | GET | Health check for monitoring |
| `/api/v1/models` | GET | List all available heat pump topologies |
| `/api/v1/models/{name}/parameters` | GET | Get default parameters for a model |
| `/api/v1/simulate/design` | POST | Run design point simulation |
| `/api/v1/tasks` | POST | Submit async simulation task |
| `/api/v1/tasks/{id}` | GET | Get task status |
| `/api/v1/reports/save` | POST | Save report to Cloud Storage |
| `/api/v1/reports/{id}` | GET | Get report JSON data |
| `/api/v1/reports/{id}/view` | GET | View report as HTML |
| `/api/v1/reports` | GET | List all saved reports |

#### Example API Request

```bash
curl -X POST "https://heatpump-api-382432690682.europe-west1.run.app/api/v1/simulate/design" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "ihx",
    "params": {
      "setup": {"refrig": "R134a"},
      "fluids": {"wf": "R134a", "si": "water", "so": "water"},
      "cons": {"Q": -5000000},
      "B1": {"T": 20},
      "B2": {"T": 15},
      "C1": {"T": 30},
      "C3": {"T": 70}
    }
  }'
```

#### Example API Response

```json
{
  "model_name": "HeatPumpIHX",
  "converged": true,
  "cop": 4.23,
  "epsilon": 0.58,
  "heat_output": 6050000.0,
  "power_input": 1430000.0,
  "cost_total": 245000.0
}
```

---

### 2. MCP Server (Claude Desktop Integration)

**Purpose:** Enables Claude Desktop to run heat pump simulations via natural language
**Location:** `mcp/heatpump_server.py`
**Protocol:** Model Context Protocol (MCP)

#### Available Tools

| Tool | Description |
|------|-------------|
| `list_heat_pump_models` | Get available topologies |
| `get_model_parameters` | Get default parameters for a model |
| `simulate_design_point` | Run design simulation |
| `analyze_datacenter_cooling` | Complete data centre analysis |
| `save_simulation_report` | Save results to cloud storage |
| `get_report` | Retrieve saved report |
| `list_reports` | List all saved reports |
| `view_report_url` | Get HTML report URL |
| `get_report_json_url` | Get JSON data URL |

#### MCP Configuration (Claude Desktop)

Location: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "heatpump-simulator": {
      "command": "python",
      "args": [
        "C:\\Users\\gaierr\\Energy_Projects\\projects\\heatpumps\\mcp\\heatpump_server.py"
      ]
    }
  }
}
```

#### Example MCP Conversation

**User:** "What heat pump should I use for a 10 MW data centre with wetland cooling?"

**Claude (using MCP tools):**
1. Calls `analyze_datacenter_cooling` with capacity=10 MW
2. Returns: "For a 10 MW data centre, I recommend an IHX heat pump with R134a. Based on the simulation:
   - COP: 4.2
   - Power consumption: 2.38 MW
   - Heat recovery potential: 3.5 MW thermal
   - Annual heat recovery revenue: £1.12M at £40/MWh"

---

### 3. Streamlit Web Application

**Deployment:** Streamlit Cloud (or Google Cloud Run)
**URL:** `https://heatpumps-simulator.streamlit.app`
**Source:** `src/heatpumps/hp_dashboard.py`

#### Features (Full Application)

- Interactive topology and refrigerant selection
- Real-time parameter adjustment with sliders
- P-h and T-s diagrams with cycle overlay
- Exergy analysis with Sankey diagrams
- Economic evaluation with currency selection
- Report generation and cloud saving
- Off-design and part-load analysis

---

## Google Cloud Services

### Services Used

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **Cloud Run** | Hosts FastAPI and Streamlit apps | Auto-scaling, europe-west1 |
| **Cloud Storage** | Stores simulation reports | 7-day lifecycle policy |
| **Cloud Build** | CI/CD for deployments | Dockerfile-based |

### Cloud Storage Configuration

**Bucket:** `heatpump-reports-lotsawatts`
**Region:** europe-west1
**Lifecycle:** Objects auto-delete after 7 days

```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 7}
      }
    ]
  }
}
```

### Environment Variables (Cloud Run)

| Variable | Description |
|----------|-------------|
| `GCP_PROJECT_ID` | Google Cloud project ID |
| `GCS_BUCKET_NAME` | Cloud Storage bucket name |
| `GCS_LOCATION` | Storage location (europe-west1) |
| `PORT` | Service port (set by Cloud Run) |

---

## Data Formats

### JSON Report Structure

```json
{
  "metadata": {
    "report_id": "uuid-string",
    "created_at": "2024-12-20T10:00:00Z",
    "project_name": "Data Centre Phase 1",
    "model_name": "ihx",
    "model_display_name": "Internal Heat Exchanger",
    "topology": "HeatPumpIHX",
    "refrigerant": "R134a",
    "api_version": "0.1.0"
  },
  "configuration_results": {
    "cop": 4.23,
    "heat_output_w": 6050000.0,
    "power_input_w": 1430000.0,
    "heat_input_w": 4620000.0,
    "epsilon": 0.58,
    "converged": true
  },
  "topology_refrigerant": {
    "model_type": "ihx",
    "refrigerant": "R134a",
    "refrigerant_properties": {
      "gwp": 1430,
      "odp": 0,
      "safety_class": "A1"
    }
  },
  "parameters": {
    "evaporator": {
      "inlet_temp_c": 20,
      "outlet_temp_c": 15
    },
    "condenser": {
      "inlet_temp_c": 30,
      "outlet_temp_c": 70
    }
  },
  "state_variables": {
    "connections": [
      {
        "id": "1",
        "label": "Evap In",
        "T_K": 283.15,
        "p_bar": 3.5,
        "h_kJ_kg": 420.5,
        "s_kJ_kgK": 1.82,
        "m_kg_s": 12.5
      }
    ]
  },
  "economic_evaluation": {
    "cost_total": 245000.0,
    "costs_by_component": {
      "compressor": 85000.0,
      "condenser": 65000.0,
      "evaporator": 55000.0,
      "ihx": 40000.0
    },
    "currency_code": "GBP",
    "currency_symbol": "£",
    "exchange_rate": 0.83,
    "cepci_reference": 816.0,
    "cepci_current": 866.4
  },
  "exergy_assessment": {
    "component_exergy": [
      {
        "component": "Compressor",
        "E_F": 1430000.0,
        "E_P": 1287000.0,
        "E_D": 143000.0,
        "epsilon": 0.90,
        "y_star": 0.45,
        "y": 0.10
      }
    ],
    "total_exergy_destruction": 358000.0,
    "exergetic_efficiency": 0.58
  },
  "diagrams": {
    "topology_svg": "/static/topologies/ihx.svg",
    "ph_diagram_base64": "data:image/png;base64,...",
    "ts_diagram_base64": "data:image/png;base64,...",
    "sankey_base64": "data:image/png;base64,..."
  }
}
```

### Key Data Fields Explained

| Field | Description | Units |
|-------|-------------|-------|
| `cop` | Coefficient of Performance (heat out / power in) | dimensionless |
| `heat_output_w` | Total heat delivered to condenser | Watts |
| `power_input_w` | Compressor electrical power | Watts |
| `epsilon` | Exergetic efficiency | 0-1 |
| `E_F` | Fuel exergy (exergy input to component) | Watts |
| `E_P` | Product exergy (useful exergy output) | Watts |
| `E_D` | Exergy destruction (thermodynamic losses) | Watts |

---

## Report Types

### Full Report (Streamlit)

Generated from the Streamlit web interface with complete simulation data:

**Contents:**
- Configuration results (COP, heat output, power input)
- Topology diagram (SVG schematic)
- P-h and T-s state diagrams (with cycle overlay)
- Complete state variables table
- Exergy assessment with Sankey diagram
- Economic evaluation with currency conversion
- All input parameters

**Storage:** 7 days in Google Cloud Storage
**Access:** HTML view at `/api/v1/reports/{id}/view`

### Summary Report (MCP)

Generated via MCP server calls with basic results only:

**Contents:**
- COP, heat output, power input
- Basic configuration parameters
- Model and refrigerant info

**Note:** For detailed diagrams, exergy analysis, and economic evaluation, use the Streamlit interface.

---

## Integration Options

### Option 1: Direct API Integration

For programmatic access from other applications:

```python
import requests

API_URL = "https://heatpump-api-382432690682.europe-west1.run.app"

# Run simulation
response = requests.post(f"{API_URL}/api/v1/simulate/design", json={
    "model_name": "ihx",
    "params": {
        "setup": {"refrig": "R134a"},
        "cons": {"Q": -5000000},
        "B1": {"T": 20}, "B2": {"T": 15},
        "C1": {"T": 30}, "C3": {"T": 70}
    }
})

result = response.json()
print(f"COP: {result['cop']}")
```

### Option 2: MCP Integration

For AI-assisted analysis through Claude Desktop:

1. Install MCP server dependencies
2. Configure Claude Desktop with server path
3. Use natural language to request simulations

### Option 3: Embed Streamlit

For end-user web interfaces:

```html
<iframe
  src="https://heatpumps-simulator.streamlit.app"
  width="100%"
  height="800px">
</iframe>
```

---

## API Reference

### Full API Documentation

- **Swagger UI:** https://heatpump-api-382432690682.europe-west1.run.app/docs
- **ReDoc:** https://heatpump-api-382432690682.europe-west1.run.app/redoc

### Authentication

Currently **no authentication** required (public API).
For production deployment, consider adding:
- API keys
- OAuth2
- IP whitelisting

### Rate Limits

No explicit rate limits, but:
- Cold start latency: ~10-30 seconds
- Simulation time: 5-30 seconds depending on complexity
- Consider implementing client-side caching

---

## MCP Server Usage

### Prerequisites

```bash
# Python 3.10+
pip install mcp httpx
```

### Configuration

1. Edit Claude Desktop config (`%APPDATA%\Claude\claude_desktop_config.json`)
2. Add the heatpump-simulator server configuration
3. Restart Claude Desktop

### Example Prompts

| Prompt | MCP Tool Called |
|--------|-----------------|
| "List available heat pump models" | `list_heat_pump_models` |
| "What parameters does the IHX model have?" | `get_model_parameters` |
| "Simulate a 5 MW IHX heat pump with R134a" | `simulate_design_point` |
| "Analyze cooling for a 15 MW data centre" | `analyze_datacenter_cooling` |
| "Save this simulation as 'Phase 1'" | `save_simulation_report` |

---

## When to Use What

| Use Case | Recommended Interface | Reason |
|----------|----------------------|--------|
| **Interactive exploration** | Streamlit | Full parameter control, diagrams |
| **Quick sizing questions** | MCP/Claude | Natural language, fast answers |
| **Automated analysis** | REST API | Programmable, batch processing |
| **Report generation** | Streamlit | Full diagrams, exergy, economics |
| **Integration testing** | REST API | Direct HTTP, predictable responses |
| **Client presentations** | Streamlit HTML reports | Professional, printable format |

### Decision Flowchart

```
Do you need detailed diagrams and exergy analysis?
├── YES → Use Streamlit web interface
│
└── NO → Is this an automated/batch process?
         ├── YES → Use REST API directly
         │
         └── NO → Are you using Claude Desktop?
                  ├── YES → Use MCP server
                  │
                  └── NO → Use REST API or Streamlit
```

---

## Quick Reference

### URLs

| Resource | URL |
|----------|-----|
| API Base | https://heatpump-api-382432690682.europe-west1.run.app |
| API Docs | https://heatpump-api-382432690682.europe-west1.run.app/docs |
| Streamlit | https://heatpumps-simulator.streamlit.app |
| Report View | /api/v1/reports/{report_id}/view |
| Report JSON | /api/v1/reports/{report_id} |

### Supported Topologies

| Key | Name | Description |
|-----|------|-------------|
| `simple` | Simple Cycle | Basic vapor compression |
| `ihx` | IHX | Internal heat exchanger |
| `econ_closed` | Economizer (Closed) | Closed flash economizer |
| `econ_open` | Economizer (Open) | Open flash economizer |
| `econ_closed_ihx` | Econ + IHX | Closed economizer with IHX |
| `ic` | Intercooler | Two-stage with intercooling |
| `trans` | Transcritical | Transcritical CO2 cycle |

### Supported Refrigerants

- **Synthetic:** R134a, R1234yf, R410A, R407C
- **Natural:** R717 (Ammonia), R290 (Propane), R744 (CO2), R600a (Isobutane)

### Contact

For technical questions or integration support, contact the development team.

---

*Generated: December 2024*
