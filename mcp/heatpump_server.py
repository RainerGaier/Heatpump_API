#!/usr/bin/env python3
"""
Heat Pump MCP Server

This MCP server provides Claude with tools to run heat pump simulations
by calling the deployed Google Cloud Run API.

Author: Rainer Gaier
Project: UK Hackathon - Data Centre Cooling Analysis
"""

import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json

# Your deployed API endpoint
API_BASE_URL = "https://heatpump-api-658843246978.europe-west2.run.app"

# Initialize MCP server
app = Server("heatpump-simulator")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """Define the tools available to Claude."""
    return [
        Tool(
            name="list_heat_pump_models",
            description="""Get a list of all available heat pump models/topologies.
            
Returns information about each model including name, topology type, 
whether it has IHX or economizer, and supported refrigerants.

Use this when you need to know what heat pump options are available.""",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_model_parameters",
            description="""Get default parameters for a specific heat pump model.

Shows all configurable parameters including refrigerant selection,
temperatures, pressures, and component efficiencies.

Args:
    model_name: Heat pump model (e.g., "ihx", "simple", "econ_closed")""",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_name": {
                        "type": "string",
                        "description": "Heat pump model name",
                    }
                },
                "required": ["model_name"],
            },
        ),
        Tool(
            name="simulate_design_point",
            description="""Run a design point simulation for a heat pump.

Runs full thermodynamic simulation using TESPy and returns COP,
power consumption, heat output, and convergence status.

Args:
    model_name: Which topology to use (e.g., "ihx", "simple")
    refrigerant: Which refrigerant (R134a, R717, R1234yf, etc.)
    cooling_capacity_kw: Desired cooling output in kW
    evaporator_inlet_temp: Heat source temperature in °C
    evaporator_outlet_temp: Cooling supply temperature in °C
    condenser_inlet_temp: Heat sink inlet in °C
    condenser_outlet_temp: Hot water delivery in °C""",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_name": {
                        "type": "string",
                        "description": "Heat pump model (e.g., 'ihx', 'simple')",
                    },
                    "refrigerant": {
                        "type": "string",
                        "description": "Refrigerant (R134a, R717, R1234yf, R290)",
                        "default": "R134a",
                    },
                    "cooling_capacity_kw": {
                        "type": "number",
                        "description": "Cooling capacity in kW",
                    },
                    "evaporator_inlet_temp": {
                        "type": "number",
                        "description": "Heat source inlet temp (°C)",
                    },
                    "evaporator_outlet_temp": {
                        "type": "number",
                        "description": "Cooling supply temp (°C)",
                    },
                    "condenser_inlet_temp": {
                        "type": "number",
                        "description": "Heat sink inlet temp (°C)",
                    },
                    "condenser_outlet_temp": {
                        "type": "number",
                        "description": "Hot water delivery temp (°C)",
                    },
                },
                "required": [
                    "model_name",
                    "cooling_capacity_kw",
                    "evaporator_inlet_temp",
                    "evaporator_outlet_temp",
                    "condenser_inlet_temp",
                    "condenser_outlet_temp",
                ],
            },
        ),
        Tool(
            name="analyze_datacenter_cooling",
            description="""Complete analysis of data centre cooling requirements.

Analyzes cooling needs, recommends topologies, runs simulations,
and calculates heat recovery potential.

Perfect for: "What heat pump for X MW data centre?" questions.

Args:
    cooling_capacity_mw: Cooling requirement in MW
    wetland_temp_summer: Summer water temp (°C, default 20)
    wetland_temp_winter: Winter water temp (°C, default 6)
    supply_temp: Cooling supply temp (°C, default 15)
    return_temp: Return water temp (°C, default 30)
    heat_recovery: Include heat recovery analysis (default true)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "cooling_capacity_mw": {
                        "type": "number",
                        "description": "Data centre cooling capacity in MW",
                    },
                    "wetland_temp_summer": {
                        "type": "number",
                        "description": "Summer wetland temp (°C)",
                        "default": 20,
                    },
                    "wetland_temp_winter": {
                        "type": "number",
                        "description": "Winter wetland temp (°C)",
                        "default": 6,
                    },
                    "supply_temp": {
                        "type": "number",
                        "description": "Required cooling supply (°C)",
                        "default": 15,
                    },
                    "return_temp": {
                        "type": "number",
                        "description": "Server return water (°C)",
                        "default": 30,
                    },
                    "heat_recovery": {
                        "type": "boolean",
                        "description": "Include heat recovery",
                        "default": True,
                    },
                },
                "required": ["cooling_capacity_mw"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls from Claude."""

    async with httpx.AsyncClient(timeout=60.0) as client:

        if name == "list_heat_pump_models":
            response = await client.get(f"{API_BASE_URL}/api/v1/models")
            response.raise_for_status()
            models = response.json()

            result = "# Available Heat Pump Models\n\n"
            for model in models.get("models", [])[:10]:  # Show first 10
                result += f"## {model['name']}\n"
                result += f"- Display: {model['display_name']}\n"
                result += f"- Topology: {model['topology']}\n"
                result += f"- IHX: {model['has_ihx']}\n"
                result += f"- Economizer: {model['has_economizer']}\n\n"

            result += f"\n*Showing 10 of {len(models.get('models', []))} total models*"
            return [TextContent(type="text", text=result)]

        elif name == "get_model_parameters":
            model_name = arguments["model_name"]
            response = await client.get(
                f"{API_BASE_URL}/api/v1/models/{model_name}/parameters"
            )
            response.raise_for_status()
            params = response.json()

            result = f"# Parameters for {model_name}\n\n```json\n"
            result += json.dumps(params, indent=2)
            result += "\n```"

            return [TextContent(type="text", text=result)]

        elif name == "simulate_design_point":
            payload = {
                "model_name": arguments["model_name"],
                "params": {
                    "setup": {"refrig": arguments.get("refrigerant", "R134a")},
                    "fluids": {
                        "wf": arguments.get("refrigerant", "R134a"),
                        "si": "water",
                        "so": "water",
                    },
                    "cons": {"Q": -abs(arguments["cooling_capacity_kw"])},
                    "B1": {"T": arguments["evaporator_inlet_temp"]},
                    "B2": {"T": arguments["evaporator_outlet_temp"]},
                    "C1": {"T": arguments["condenser_inlet_temp"]},
                    "C3": {"T": arguments["condenser_outlet_temp"]},
                },
            }

            response = await client.post(
                f"{API_BASE_URL}/api/v1/simulate/design", json=payload
            )
            response.raise_for_status()
            sim = response.json()

            result = f"# Simulation Results\n\n"
            result += f"**Model:** {arguments['model_name']}\n"
            result += f"**Refrigerant:** {arguments.get('refrigerant', 'R134a')}\n\n"

            if sim["converged"]:
                result += "## Performance\n\n"
                result += f"- **COP:** {sim['cop']:.2f}\n"
                result += f"- **Power:** {sim['power_input']/1000:.1f} kW\n"
                result += f"- **Cooling:** {abs(sim['heat_output'])/1000:.1f} kW\n"
                result += f"- **Efficiency:** {sim['epsilon']*100:.1f}%\n"
                result += f"- **Status:** ✅ Converged\n"
            else:
                result += "## ❌ Failed to Converge\n"
                if sim.get("error_message"):
                    result += f"\nError: {sim['error_message']}"

            return [TextContent(type="text", text=result)]

        elif name == "analyze_datacenter_cooling":
            capacity_mw = arguments["cooling_capacity_mw"]
            capacity_kw = capacity_mw * 1000000

            result = f"# Data Centre Cooling Analysis - {capacity_mw} MW\n\n"

            # Strategy
            result += "## Recommended Strategy\n\n"
            result += "**Three-Tier Hybrid Approach:**\n\n"
            result += "1. **Free Cooling** (60-70% of year)\n"
            result += "   - Direct wetland heat exchange\n"
            result += "   - PUE: 1.05-1.15\n\n"
            result += "2. **IHX Heat Pump** (20-30% of year)\n"
            result += "   - Shoulder seasons\n"
            result += "   - Heat recovery capable\n\n"
            result += "3. **Backup Chillers** (5-15% of year)\n"
            result += "   - Peak summer\n\n"

            # Run simulation
            payload = {
                "model_name": "ihx",
                "params": {
                    "setup": {"refrig": "R134a"},
                    "fluids": {"wf": "R134a", "si": "water", "so": "water"},
                    "cons": {"Q": -capacity_kw},
                    "B1": {"T": arguments.get("wetland_temp_summer", 20)},
                    "B2": {"T": arguments.get("supply_temp", 15)},
                    "C1": {"T": arguments.get("return_temp", 30)},
                    "C3": {"T": 70},
                },
            }

            response = await client.post(
                f"{API_BASE_URL}/api/v1/simulate/design", json=payload
            )

            if response.status_code == 200:
                sim = response.json()
                if sim["converged"]:
                    cop = sim["cop"]
                    power_mw = sim["power_input"] / 1000000

                    result += f"## Heat Pump Performance\n\n"
                    result += f"- **COP:** {cop:.2f}\n"
                    result += f"- **Power:** {power_mw:.2f} MW\n"
                    result += f"- **PUE:** {1 + (1/cop):.2f}\n\n"

                    if arguments.get("heat_recovery", True):
                        recoverable_mw = capacity_mw * 0.35
                        annual_heat_mwh = recoverable_mw * 8000
                        revenue = annual_heat_mwh * 40

                        result += f"## Heat Recovery\n\n"
                        result += f"- **Capacity:** {recoverable_mw:.1f} MW\n"
                        result += f"- **Annual:** {annual_heat_mwh:,.0f} MWh\n"
                        result += (
                            f"- **Revenue:** £{revenue:,.0f}/year (at £40/MWh)\n\n"
                        )

                    result += f"## Annual Performance\n\n"
                    result += f"- **PUE:** 1.15-1.25 (world-class)\n"
                    result += f"- **Energy savings:** 40-60% vs traditional\n"

            return [TextContent(type="text", text=result)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
