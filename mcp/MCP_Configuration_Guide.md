# Heat Pump MCP Server - Configuration & Usage Guide

## What This MCP Server Does

This MCP server gives Claude the ability to:

1. **Run real thermodynamic simulations** via your deployed API
2. **Analyze data centre cooling** requirements
3. **Compare heat pump topologies** (simple, IHX, economizer)
4. **Calculate heat recovery potential** and ROI
5. **Provide engineering recommendations** based on real physics

---

## Example Conversations

### Example 1: Simple Question

**User:** "What heat pump should I use for a 10 MW data centre with wetland cooling?"

**Claude (with MCP):**

1. Calls `analyze_datacenter_cooling(cooling_capacity_mw=10)`
2. Gets real simulation results from your API
3. Responds: "For a 10 MW data centre with wetland access, I recommend a three-tier cooling strategy:

   - Free cooling 60-70% of the year (PUE 1.05-1.15)
   - IHX heat pump for shoulder seasons (COP 4.2, PUE 1.24)
   - Backup chillers for peaks

   Based on simulation, the IHX topology delivers:

   - COP: 4.21
   - Power: 2.38 MW
   - Annual PUE: 1.18 (world-class)
   - Heat recovery potential: 3.5 MW = £1.1M/year revenue at £40/MWh"

---

### Example 2: Comparison Request

**User:** "Compare simple vs IHX vs economizer heat pumps for 5 MW cooling"

**Claude (with MCP):**

1. Calls `compare_topologies(cooling_capacity_kw=5000000, ...)`
2. Runs 3 separate simulations
3. Shows comparison table:

```
| Topology      | COP  | Power (kW) | Notes              |
|---------------|------|------------|--------------------|
| simple        | 3.45 | 1,449      | Lowest cost        |
| ihx           | 4.12 | 1,214      | Good balance       |
| econ_closed   | 4.68 | 1,068      | Highest efficiency |

Recommendation: IHX topology (COP 4.12) offers the best balance 
of efficiency and complexity for most 5-50 MW applications.
```

---

### Example 3: Integration with Rob's Platform

**User:** "We found a site in Birmingham near the River Tame. Flood Zone 2, 

available water flow 1000 m³/h at 15-20°C. Can we build a 15 MW data centre?"

**Claude (with MCP + Rob's flood data):**

1. Calls Rob's flood risk agent → "Zone 2 = moderate risk"
2. Calls `analyze_datacenter_cooling(cooling_capacity_mw=15, wetland_temp_summer=20, ...)`
3. Integrates both analyses:

"Site Analysis:

- Cooling: ✅ Feasible (wetland provides sufficient capacity)
- Flood Risk: ⚠️ Moderate (Zone 2) - equipment must be elevated
- Strategy: Free cooling 65% of year, IHX heat pump 25%, backup 10%
- Performance: COP 4.3 shoulder season, annual PUE 1.19
- Heat Recovery: 5.25 MW potential = £1.68M/year revenue
- Recommendation: Viable with elevated heat pump placement above 100-year flood level"

---

## Configuration Files

### 1. MCP Settings (Claude Desktop)

Location: `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

```json
{
  "mcpServers": {
    "heatpump-simulator": {
      "command": "python",
      "args": [
        "C:\\Users\\gaierr\\Energy_Projects\\projects\\heatpumps\\heatpump_mcp_server.py"
      ],
      "env": {
        "API_BASE_URL": "https://heatpump-api-658843246978.europe-west2.run.app"
      }
    }
  }
}
```

### 2. Required Dependencies

`requirements-mcp.txt`:

```
mcp>=0.9.0
httpx>=0.27.0
pydantic>=2.0.0
```

---

## Tools Available to Claude

### 1. `list_heat_pump_models()`

**What it does:** Gets all available heat pump topologies  

**When Claude uses it:** User asks "what models are available" or "what heat pump options"  

**Returns:** List of 40+ models with descriptions

### 2. `get_model_parameters(model_name)`

**What it does:** Gets default parameters for a specific model  

**When Claude uses it:** Before running simulation, or when user asks about configuration  

**Returns:** Full parameter structure (JSON)

### 3. `simulate_design_point(...)`

**What it does:** Runs full TESPy thermodynamic simulation  

**When Claude uses it:** User asks to "simulate" or "calculate performance"  

**Returns:** COP, power, efficiency, convergence status  

**Takes:** ~2-10 seconds

### 4. `analyze_datacenter_cooling(...)`

**What it does:** Complete data centre cooling analysis  

**When Claude uses it:** User asks about data centre applications  

**Returns:** Strategy, performance, heat recovery, recommendations  

**Takes:** ~5-15 seconds (runs multiple simulations)

### 5. `compare_topologies(...)`

**What it does:** Compares 2-5 topologies side-by-side  

**When Claude uses it:** User asks to "compare" or "which is better"  

**Returns:** Comparison table + recommendation  

**Takes:** ~10-30 seconds (multiple simulations)

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    User Question                         │
│  "What heat pump for 10 MW data centre near wetland?"    │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│                Claude Desktop                            │
│  - Natural language understanding                        │
│  - Thermal engineering knowledge                         │
│  - Tool selection & orchestration                        │
└────────────────────┬─────────────────────────────────────┘
                     │ MCP Protocol (stdio)
                     ▼
┌──────────────────────────────────────────────────────────┐
│         Heat Pump MCP Server (Python)                    │
│  File: heatpump_mcp_server.py                            │
│  Running on: Your local PC                               │
│                                                          │
│  Tools:                                                  │
│  ├─ list_heat_pump_models()                              │
│  ├─ get_model_parameters(model)                          │
│  ├─ simulate_design_point(...)                           │
│  ├─ analyze_datacenter_cooling(...)                      │
│  └─ compare_topologies(...)                              │
└────────────────────┬─────────────────────────────────────┘
                     │ HTTPS API Calls
                     ▼
┌──────────────────────────────────────────────────────────┐
│         Your Deployed API (Google Cloud Run)             │
│  URL: heatpump-api-658843246978...run.app                │
│                                                          │
│  Endpoints:                                              │
│  ├─ GET  /api/v1/models                                  │
│  ├─ GET  /api/v1/models/{name}/parameters                │
│  ├─ POST /api/v1/simulate/design                         │
│  └─ Returns: Real TESPy simulation results               │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────┐
│              TESPy Engine (in container)                 │
│  - Thermodynamic modeling                                │
│  - Fluid property calculations (CoolProp)                │
│  - Network solver                                        │
│  - Returns: COP, power, efficiency, convergence          │
└──────────────────────────────────────────────────────────┘
```

---

## Data Flow Example

**Question:** "What's the COP for a 5 MW IHX heat pump?"

1. **User → Claude:** Natural language question
2. **Claude → MCP Server:** `simulate_design_point(model_name="ihx", cooling_capacity_kw=5000000, ...)`
3. **MCP Server → API:** `POST /api/v1/simulate/design` with JSON payload
4. **API → TESPy:** Runs thermodynamic simulation (2-5 seconds)
5. **TESPy → API:** Returns `{cop: 4.21, power: 1189000, converged: true}`
6. **API → MCP Server:** JSON response
7. **MCP Server → Claude:** Formatted results with interpretation
8. **Claude → User:** "The IHX heat pump achieves a COP of 4.21, consuming 1.19 MW 

   of electrical power to deliver 5 MW of cooling. This is excellent efficiency 

   for this application."

---

## Integration with Rob's Platform

Your MCP server can be combined with Rob's flood risk agents:

```python
# Rob's system calls both agents
flood_result = await flood_agent.assess_site(location, elevation)
thermal_result = await heatpump_agent.analyze_datacenter_cooling(
    cooling_capacity_mw=15,
    wetland_temp_summer=18
)

# Claude combines results
comprehensive_analysis = f"""
Site Feasibility Assessment:
- Flood Risk: {flood_result.risk_level}
- Cooling Strategy: {thermal_result.strategy}
- Performance: PUE {thermal_result.pue}
- Heat Recovery: £{thermal_result.revenue_annual:,}/year
- Overall: {'✅ RECOMMENDED' if feasible else '⚠️ CONCERNS'}
"""
```

---

## Benefits Over Traditional Approach

### Without MCP:

❌ User asks → Claude guesses/estimates → Inaccurate results  

❌ User must manually run simulations → Copy/paste results  

❌ No integration between flood risk and thermal analysis  

### With MCP:

✅ User asks → Claude runs real simulations → Accurate physics-based results  

✅ Automatic tool selection → Seamless experience  

✅ Integrated multi-agent analysis → Comprehensive recommendations  

✅ Cites actual simulation data → Trustworthy engineering advice  

---

## Next Steps

1. **Review this example code** - Understand the structure
2. **Decide if you want to build it** - Is it worth the time for hackathon?
3. **Test locally first** - Before integrating with Rob
4. **Add to presentation** - "AI agents running real thermodynamic simulations"

Ready to build this? Or want to see more examples first?