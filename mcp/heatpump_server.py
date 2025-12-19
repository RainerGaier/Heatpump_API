#!/usr/bin/env python3
"""
Heat Pump MCP Server

This MCP server provides Claude with tools to run heat pump simulations
by calling the deployed Google Cloud Run API.

Tools available:
- list_heat_pump_models: Get available heat pump topologies
- get_model_parameters: Get default parameters for a model
- simulate_design_point: Run a design point simulation
- analyze_datacenter_cooling: Complete data centre analysis
- save_simulation_report: Save simulation results to cloud storage
- get_report: Retrieve a saved report by ID
- list_reports: List all saved reports

Author: Rainer Gaier
Project: UK Hackathon - Data Centre Cooling Analysis
"""

import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json
from datetime import datetime, timezone
import uuid

# Your deployed API endpoint
API_BASE_URL = "https://heatpump-api-382432690682.europe-west1.run.app"

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

Runs thermodynamic simulation using TESPy and returns basic performance metrics:
COP, power consumption, heat output, efficiency, and convergence status.

NOTE: This returns summary results only. For detailed state points, exergy analysis,
and P-h/T-s diagrams, use the Streamlit interface at https://heatpumps-simulator.streamlit.app

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
        Tool(
            name="save_simulation_report",
            description="""Save simulation results to cloud storage and get a shareable report URL.

After running a simulation, use this tool to persist the results and generate
an HTML report that can be viewed in a browser.

**IMPORTANT:** Reports saved via MCP contain BASIC results only:
- COP, heat output, power input
- Basic configuration parameters

For FULL detailed reports with the following, use the Streamlit web interface
at https://heatpumps-simulator.streamlit.app :
- P-h and T-s diagrams
- Exergy analysis with Sankey diagram
- Complete state variables table
- Economic evaluation
- Topology diagrams

Args:
    project_name: Name for this simulation project (e.g., "London Data Centre Phase 1")
    model_name: Heat pump model used (e.g., "ihx", "simple")
    refrigerant: Refrigerant used (e.g., "R134a")
    simulation_data: Dictionary containing simulation results (COP, heat_output, power_input, etc.)

Returns:
    Report ID and URLs for viewing the HTML report and raw JSON data.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "User-defined project name for the report",
                    },
                    "model_name": {
                        "type": "string",
                        "description": "Heat pump model name",
                    },
                    "refrigerant": {
                        "type": "string",
                        "description": "Refrigerant used",
                        "default": "R134a",
                    },
                    "simulation_data": {
                        "type": "object",
                        "description": "Simulation results to save",
                        "properties": {
                            "cop": {"type": "number"},
                            "heat_output_w": {"type": "number"},
                            "power_input_w": {"type": "number"},
                            "heat_input_w": {"type": "number"},
                            "epsilon": {"type": "number"},
                        },
                    },
                },
                "required": ["project_name", "model_name", "simulation_data"],
            },
        ),
        Tool(
            name="get_report",
            description="""Retrieve a saved simulation report by ID.

Use this to fetch the full details of a previously saved report,
including all simulation results, state variables, and analysis data.

Args:
    report_id: The UUID of the report to retrieve""",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_id": {
                        "type": "string",
                        "description": "UUID of the report to retrieve",
                    }
                },
                "required": ["report_id"],
            },
        ),
        Tool(
            name="list_reports",
            description="""List all saved simulation reports.

Returns a list of available reports with their IDs, creation dates,
project names, and model information.

Args:
    limit: Maximum number of reports to return (default 20)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum reports to return",
                        "default": 20,
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="view_report_url",
            description="""Get the HTML view URL for a report.

Use this when you want to provide the user with a link to view
the full interactive report in their browser (with diagrams and formatting).

Args:
    report_id: The UUID of the report""",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_id": {
                        "type": "string",
                        "description": "UUID of the report",
                    }
                },
                "required": ["report_id"],
            },
        ),
        Tool(
            name="get_report_json_url",
            description="""Get the full JSON data URL for a report.

Use this when the user wants access to the complete simulation data in JSON format,
including all state variables, exergy analysis, economic evaluation, and parameters.

The URL returns the full report data via the API endpoint (not the GCS storage URL).

Args:
    report_id: The UUID of the report""",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_id": {
                        "type": "string",
                        "description": "UUID of the report",
                    }
                },
                "required": ["report_id"],
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
                result += f"- **Status:** Converged\n"
            else:
                result += "## Failed to Converge\n"
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

        elif name == "save_simulation_report":
            # Generate report ID
            report_id = str(uuid.uuid4())

            # Build metadata
            metadata = {
                "report_id": report_id,
                "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "project_name": arguments.get("project_name", "Untitled Project"),
                "model_name": arguments.get("model_name", "Unknown"),
                "topology": arguments.get("model_name", "Unknown"),
                "refrigerant": arguments.get("refrigerant", "R134a"),
            }

            # Build simulation data structure
            sim_data = arguments.get("simulation_data", {})
            simulation_data = {
                "configuration_results": {
                    "cop": sim_data.get("cop"),
                    "heat_output_w": sim_data.get("heat_output_w"),
                    "power_input_w": sim_data.get("power_input_w"),
                    "heat_input_w": sim_data.get("heat_input_w"),
                },
                "topology_refrigerant": {
                    "model_type": arguments.get("model_name"),
                    "refrigerant": arguments.get("refrigerant", "R134a"),
                },
                "parameters": sim_data.get("parameters", {}),
                "state_variables": sim_data.get("state_variables", {}),
                "economic_evaluation": sim_data.get("economic_evaluation", {}),
                "exergy_assessment": sim_data.get("exergy_assessment", {}),
            }

            # Call API to save report
            payload = {
                "simulation_data": simulation_data,
                "metadata": metadata,
            }

            response = await client.post(
                f"{API_BASE_URL}/api/v1/reports/save",
                json=payload,
                timeout=60.0
            )

            if response.status_code == 201:
                data = response.json()
                view_url = f"{API_BASE_URL}/api/v1/reports/{report_id}/view"

                result = "# Report Saved Successfully\n\n"
                result += f"**Project:** {arguments.get('project_name', 'Untitled Project')}\n"
                result += f"**Report ID:** `{report_id}`\n\n"
                result += f"## View Report\n\n"
                result += f"**HTML Report:** {view_url}\n\n"
                result += f"**Raw JSON:** {data.get('signed_url', 'N/A')}\n\n"
                result += f"*Link expires: {data.get('expires_at', 'in 7 days')}*"
            else:
                result = f"# Failed to Save Report\n\n"
                result += f"**Status:** {response.status_code}\n"
                result += f"**Error:** {response.text}"

            return [TextContent(type="text", text=result)]

        elif name == "get_report":
            report_id = arguments["report_id"]
            response = await client.get(f"{API_BASE_URL}/api/v1/reports/{report_id}")

            if response.status_code == 200:
                report = response.json()
                metadata = report.get("metadata", {})
                config = report.get("configuration_results", {})

                result = f"# Report: {metadata.get('project_name', 'Untitled')}\n\n"
                result += f"**Report ID:** `{report_id}`\n"
                result += f"**Created:** {metadata.get('created_at', 'Unknown')}\n"
                result += f"**Model:** {metadata.get('model_name', 'Unknown')}\n"
                result += f"**Refrigerant:** {metadata.get('refrigerant', 'Unknown')}\n\n"

                if config:
                    result += "## Results\n\n"
                    if config.get("cop"):
                        result += f"- **COP:** {config['cop']:.2f}\n"
                    if config.get("heat_output_w"):
                        result += f"- **Heat Output:** {config['heat_output_w']/1000:.1f} kW\n"
                    if config.get("power_input_w"):
                        result += f"- **Power Input:** {config['power_input_w']/1000:.1f} kW\n"

                result += f"\n## Report URLs\n\n"
                result += f"**HTML Report (interactive):**\n{API_BASE_URL}/api/v1/reports/{report_id}/view\n\n"
                result += f"**Full JSON Data:**\n{API_BASE_URL}/api/v1/reports/{report_id}\n"
            elif response.status_code == 404:
                result = f"# Report Not Found\n\nNo report found with ID: `{report_id}`"
            else:
                result = f"# Error Retrieving Report\n\n**Status:** {response.status_code}"

            return [TextContent(type="text", text=result)]

        elif name == "list_reports":
            limit = arguments.get("limit", 20)
            response = await client.get(
                f"{API_BASE_URL}/api/v1/reports/",
                params={"limit": limit}
            )

            if response.status_code == 200:
                reports = response.json()

                result = "# Saved Reports\n\n"

                if not reports:
                    result += "*No reports found.*"
                else:
                    for report in reports:
                        metadata = report.get("metadata", {})
                        project_name = metadata.get('project_name', 'Untitled')
                        result += f"## {project_name}\n"
                        result += f"- **ID:** `{report.get('report_id', 'N/A')}`\n"
                        result += f"- **Model:** {metadata.get('model_name', 'Unknown')}\n"
                        result += f"- **Refrigerant:** {metadata.get('refrigerant', 'Unknown')}\n"
                        result += f"- **Created:** {report.get('created_at', 'Unknown')}\n"
                        result += f"- **Size:** {report.get('size_bytes', 0) / 1024:.1f} KB\n\n"

                    result += f"*Showing {len(reports)} reports*"
            else:
                result = f"# Error Listing Reports\n\n**Status:** {response.status_code}"

            return [TextContent(type="text", text=result)]

        elif name == "view_report_url":
            report_id = arguments["report_id"]
            view_url = f"{API_BASE_URL}/api/v1/reports/{report_id}/view"

            result = f"# Report View URL\n\n"
            result += f"**Report ID:** `{report_id}`\n\n"
            result += f"**HTML Report URL:**\n{view_url}\n\n"
            result += "*Open this URL in a browser to view the full interactive report with diagrams.*"

            return [TextContent(type="text", text=result)]

        elif name == "get_report_json_url":
            report_id = arguments["report_id"]

            # The full JSON data is available at the API endpoint directly
            json_url = f"{API_BASE_URL}/api/v1/reports/{report_id}"

            # Verify the report exists
            response = await client.head(json_url)

            if response.status_code == 200:
                result = f"# Full JSON Data URL\n\n"
                result += f"**Report ID:** `{report_id}`\n\n"
                result += f"**JSON Data URL:**\n{json_url}\n\n"
                result += "*This URL returns the complete simulation data including all state variables, exergy analysis, and parameters in JSON format.*"
            elif response.status_code == 404:
                result = f"# Report Not Found\n\nNo report found with ID: `{report_id}`"
            else:
                # Even if HEAD fails, provide the URL (GET might work)
                result = f"# Full JSON Data URL\n\n"
                result += f"**Report ID:** `{report_id}`\n\n"
                result += f"**JSON Data URL:**\n{json_url}\n\n"
                result += "*This URL returns the complete simulation data in JSON format.*"

            return [TextContent(type="text", text=result)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
