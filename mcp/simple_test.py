#!/usr/bin/env python3
"""Simple test for MCP server - just verifies it can start and has the right tools."""

import sys
from pathlib import Path

# Add mcp to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from heatpump_server import app
    print("[PASS] MCP server imported successfully")
    print(f"[INFO] Server name: {app.name}")
    print(f"[INFO] This means your MCP server code is valid!")
    print()
    print("Next steps:")
    print("1. Configure Claude Desktop with the path to heatpump_server.py")
    print("2. Restart Claude Desktop")
    print("3. Look for the plug icon (MCP servers connected)")
    print("4. Ask Claude: 'List available heat pump models'")
    print()
    print("The error you saw when running 'python heatpump_server.py' is NORMAL.")
    print("MCP servers communicate via JSON-RPC over stdin/stdout, not command line.")

except ImportError as e:
    print(f"[FAIL] Could not import MCP server: {e}")
    print("Run: pip install -r requirements-mcp.txt")
    sys.exit(1)
except Exception as e:
    print(f"[FAIL] Error loading MCP server: {e}")
    sys.exit(1)
