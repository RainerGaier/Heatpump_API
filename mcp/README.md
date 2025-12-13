# Heat Pump MCP Server - Setup Instructions

## Quick Start (10 Minutes)

### Step 1: Create the MCP folder
```bash
cd C:\Users\gaierr\Energy_Projects\projects\heatpumps
mkdir mcp
cd mcp
```

### Step 2: Copy files into the mcp folder
Copy these 3 files into `C:\Users\gaierr\Energy_Projects\projects\heatpumps\mcp\`:
- ✅ `heatpump_server.py`
- ✅ `requirements-mcp.txt`
- ✅ `MCP_README.md` (this file)

### Step 3: Install dependencies
```bash
# From the mcp folder
pip install -r requirements-mcp.txt
```

### Step 4: Test the server
```bash
python heatpump_server.py
```

If it starts without errors, press `Ctrl+C` to stop it. That's it - the server works!

---

## Step 5: Configure Claude Desktop

### Find your config file:
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

**Quick way to find it:**
1. Press `Win + R`
2. Type: `%APPDATA%\Claude`
3. Open `claude_desktop_config.json` in Notepad

### Edit the config file:

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

**IMPORTANT:** Use double backslashes `\\` in the path!

### Step 6: Restart Claude Desktop

1. Close Claude Desktop completely
2. Open it again
3. Look for the 🔌 icon (MCP servers connected)

---

## Step 7: Test It!

Ask Claude:
```
"What heat pump topology should I use for a 10 MW data centre with wetland cooling?"
```

Claude should:
1. Call your MCP server
2. Run a real simulation via your API
3. Return actual performance data (COP, power, heat recovery, etc.)

---

## Troubleshooting

### Server won't start?
```bash
# Check Python version (needs 3.10+)
python --version

# Reinstall dependencies
pip install -r requirements-mcp.txt --force-reinstall
```

### Claude doesn't see the server?
1. Check config file path is correct (double backslashes!)
2. Restart Claude Desktop
3. Look for errors in: `%APPDATA%\Claude\logs\`

### API timeout?
- Normal for first simulation (cold start)
- Subsequent calls should be faster

---

## Example Questions to Try

1. "List available heat pump models"
2. "What are the parameters for the IHX model?"
3. "Simulate a 5 MW IHX heat pump with R134a"
4. "Analyze cooling for a 15 MW data centre"
5. "What's the heat recovery potential for 10 MW?"

---

## Project Structure

```
heatpumps/
├── src/heatpumps/
│   └── api/                 # Deployed to Cloud Run
│
├── mcp/                     # Local MCP server
│   ├── heatpump_server.py  # ← Main server
│   ├── requirements-mcp.txt
│   └── README.md
│
├── Dockerfile
└── pyproject.toml
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

## Need Help?

Common issues:
- **Path errors:** Use double backslashes in Windows paths
- **Module not found:** Run `pip install -r requirements-mcp.txt`
- **Server won't connect:** Check Claude Desktop logs
- **Simulation fails:** Check API is still running on Cloud Run

---

## Success Indicators

✅ MCP server starts without errors  
✅ Claude shows 🔌 icon when started  
✅ Claude can list heat pump models  
✅ Claude can run simulations  
✅ You get real COP numbers back  

Congrats! Your MCP server is working! 🎉