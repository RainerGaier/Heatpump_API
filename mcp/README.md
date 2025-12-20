# Heat Pump MCP Server

MCP (Model Context Protocol) server that enables **Claude Desktop** to run heat pump simulations via natural language.

## What This Does

Ask Claude questions like:
- *"What heat pump should I use for a 10 MW data centre?"*
- *"Simulate a 5 MW IHX heat pump with R717 ammonia refrigerant"*
- *"Compare cooling options for incoming water at 40°C"*

Claude will run real thermodynamic simulations and return actual performance data (COP, power consumption, heat recovery potential).

---

## Installation Options

Choose the option that best fits your needs:

| Option | Best For | Prerequisites |
|--------|----------|---------------|
| **A: pip install** | Developers | Python 3.10+ |
| **B: One-Click Installer** | Non-developers with Python | Python 3.10+ |
| **C: Standalone .exe** | Anyone (no Python needed) | None |

---

### Option A: For Developers (pip install)

```bash
# Navigate to the mcp folder
cd heatpumps-main/mcp

# Install as editable package
pip install -e .

# Verify installation
heatpump-mcp --help
```

**Configure Claude Desktop:**

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "heatpump-simulator": {
      "command": "heatpump-mcp"
    }
  }
}
```

Restart Claude Desktop.

---

### Option B: For Non-Developers (One-Click Installer)

**Prerequisites:** Python 3.10+ installed

1. Navigate to the `mcp` folder
2. Double-click `install-windows.bat`
3. Follow the prompts
4. Restart Claude Desktop

The installer will:
- Install required Python packages
- Configure Claude Desktop automatically
- Verify the installation

---

### Option C: Standalone Executable (No Python Required)

For users who don't have Python installed:

**Step 1: Build the executable** (done once by developer)

```powershell
cd mcp
.\build-standalone.ps1
```

This creates:
- `dist/heatpump-mcp.exe` - Standalone executable (~30 MB)
- `dist/install-standalone.bat` - One-click installer

**Step 2: Distribute to end users**

Send them:
1. `heatpump-mcp.exe`
2. `install-standalone.bat`

**Step 3: End user installation**
1. Download both files to a folder
2. Double-click `install-standalone.bat`
3. Restart Claude Desktop

---

## Verifying Installation

After installation and restarting Claude Desktop:

1. Look for the 🔌 plug icon (MCP servers connected)
2. Ask Claude: *"List available heat pump models"*
3. Claude should return a list of topologies (simple, ihx, econ_closed, etc.)

---

## Available Tools

| Tool | Description |
|------|-------------|
| `list_heat_pump_models` | Get available topologies |
| `get_model_parameters` | Get default parameters for a model |
| `simulate_design_point` | Run design simulation |
| `analyze_datacenter_cooling` | Complete data centre analysis |
| `save_simulation_report` | Save results to cloud storage (7-day expiry) |
| `get_report` | Retrieve saved report by ID |
| `list_reports` | List all saved reports |
| `view_report_url` | Get HTML report URL |
| `get_report_json_url` | Get JSON data URL |

---

## Example Conversations

### Quick Sizing
```
User: "What heat pump for a 10 MW data centre with wetland cooling?"

Claude: Based on my analysis using the IHX heat pump model:
- COP: 4.2
- Power consumption: 2.38 MW
- Heat recovery potential: 3.5 MW thermal
- Annual heat recovery revenue: £1.12M at £40/MWh
```

### Detailed Simulation
```
User: "Simulate cooling for incoming water at 40°C, outlet at 20°C,
       using R717 ammonia, 1 MW capacity"

Claude: [Runs actual TESPy simulation]
- Model: Simple cycle
- COP: 14.44 (summer), 21.64 (winter)
- Annual PUE: 1.12
```

### Save Report
```
User: "Save this simulation as 'Phase 1 Analysis'"

Claude: Report saved successfully!
- Report ID: abc-123-def
- View at: https://heatpump-api.../reports/abc-123-def/view
- Expires: 7 days
```

---

## How It Works

```
You ask Claude a question
         ↓
Claude Desktop (with MCP enabled)
         ↓
MCP Server (running on your PC)
         ↓
Your API (Google Cloud Run)
         ↓
TESPy Simulation (real physics)
         ↓
Results back to Claude
         ↓
Claude explains results to you
```

---

## Troubleshooting

### Server won't start
```bash
# Check Python version
python --version  # Must be 3.10+

# Reinstall dependencies
pip install -e . --force-reinstall

# Test manually
python -m heatpump_mcp
```

### Claude doesn't see the server
1. Check config file path uses double backslashes: `C:\\Users\\...`
2. Restart Claude Desktop completely (check system tray)
3. Check logs at: `%APPDATA%\Claude\logs\`

### API timeout
- First request may take 10-30 seconds (cold start)
- Subsequent requests are faster

---

## Configuration

The API endpoint can be overridden via environment variable:

```bash
set HEATPUMP_API_URL=https://your-custom-api.run.app
heatpump-mcp
```

---

## Uninstalling

**For pip install:**
```bash
pip uninstall heatpump-mcp
```

**For one-click install:**
Double-click `uninstall-windows.bat`

---

## Project Structure

```
mcp/
├── pyproject.toml           # Package definition (pip install)
├── README.md                # This file
├── install-windows.bat      # One-click installer (requires Python)
├── uninstall-windows.bat    # Uninstaller
├── build-standalone.ps1     # Build standalone .exe (for distribution)
├── requirements-mcp.txt     # Legacy requirements file
├── heatpump_server.py       # Legacy standalone script
└── src/
    └── heatpump_mcp/
        ├── __init__.py
        ├── __main__.py
        └── server.py        # Main server code
```

---

## Links

- **API Documentation:** https://heatpump-api-382432690682.europe-west1.run.app/docs
- **Streamlit UI:** https://heatpumps-simulator.streamlit.app
- **Full Integration Guide:** See `INTEGRATION_GUIDE.md` in parent directory

---

## Success Indicators

- MCP server starts without errors
- Claude shows 🔌 icon when started
- Claude can list heat pump models
- Claude can run simulations
- You get real COP numbers back

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Claude Desktop logs: `%APPDATA%\Claude\logs\`
3. Contact the development team
