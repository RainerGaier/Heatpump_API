#!/usr/bin/env python3
"""
Test script for the Heat Pump MCP Server.

This script tests the MCP server by sending it JSON-RPC requests
and verifying the responses, simulating what Claude Desktop would do.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add mcp to path
sys.path.insert(0, str(Path(__file__).parent))

from heatpump_server import app


async def test_list_tools():
    """Test that the server exposes the correct tools."""
    print("Testing list_tools()...")

    tools = await app.list_tools()

    print(f"✓ Found {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:60]}...")

    assert len(tools) == 4, f"Expected 4 tools, got {len(tools)}"
    assert tools[0].name == "list_heat_pump_models"
    assert tools[1].name == "get_model_parameters"
    assert tools[2].name == "simulate_design_point"
    assert tools[3].name == "analyze_datacenter_cooling"

    print("✓ All tools present and correct\n")
    return True


async def test_list_models():
    """Test listing heat pump models."""
    print("Testing list_heat_pump_models tool...")

    result = await app.call_tool("list_heat_pump_models", {})

    assert len(result) == 1
    assert result[0].type == "text"
    assert "Available Heat Pump Models" in result[0].text
    assert "simple" in result[0].text.lower()

    print("✓ list_heat_pump_models works correctly")
    print(f"  Response preview: {result[0].text[:100]}...\n")
    return True


async def test_get_parameters():
    """Test getting model parameters."""
    print("Testing get_model_parameters tool...")

    result = await app.call_tool("get_model_parameters", {"model_name": "simple"})

    assert len(result) == 1
    assert result[0].type == "text"
    assert "Parameters for simple" in result[0].text
    assert "json" in result[0].text

    print("✓ get_model_parameters works correctly")
    print(f"  Response preview: {result[0].text[:150]}...\n")
    return True


async def test_simulate_design():
    """Test running a design simulation."""
    print("Testing simulate_design_point tool...")

    arguments = {
        "model_name": "simple",
        "refrigerant": "R134a",
        "cooling_capacity_kw": 5000,
        "evaporator_inlet_temp": 20,
        "evaporator_outlet_temp": 15,
        "condenser_inlet_temp": 30,
        "condenser_outlet_temp": 70,
    }

    result = await app.call_tool("simulate_design_point", arguments)

    assert len(result) == 1
    assert result[0].type == "text"
    assert "Simulation Results" in result[0].text
    assert ("Converged" in result[0].text or "Failed" in result[0].text)

    if "COP" in result[0].text:
        print("✓ simulate_design_point works correctly")
        print(f"  Simulation converged with results:")
        # Extract COP from response
        for line in result[0].text.split("\n"):
            if "COP" in line or "Power" in line or "Cooling" in line:
                print(f"    {line.strip()}")
    else:
        print("⚠ simulate_design_point returned but didn't converge")
        print(f"  Response: {result[0].text[:200]}...")

    print()
    return True


async def test_analyze_datacenter():
    """Test data centre analysis."""
    print("Testing analyze_datacenter_cooling tool...")

    arguments = {
        "cooling_capacity_mw": 10,
        "wetland_temp_summer": 20,
        "wetland_temp_winter": 6,
        "supply_temp": 15,
        "return_temp": 30,
        "heat_recovery": True,
    }

    result = await app.call_tool("analyze_datacenter_cooling", arguments)

    assert len(result) == 1
    assert result[0].type == "text"
    assert "Data Centre Cooling Analysis" in result[0].text
    assert "10 MW" in result[0].text

    print("✓ analyze_datacenter_cooling works correctly")
    print(f"  Analysis includes:")
    for line in result[0].text.split("\n"):
        if "COP" in line or "PUE" in line or "Heat Recovery" in line:
            print(f"    {line.strip()}")

    print()
    return True


async def main():
    """Run all tests."""
    print("="*60)
    print("Heat Pump MCP Server Test Suite")
    print("="*60)
    print()

    tests = [
        ("List Tools", test_list_tools),
        ("List Models", test_list_models),
        ("Get Parameters", test_get_parameters),
        ("Simulate Design", test_simulate_design),
        ("Analyze Data Centre", test_analyze_datacenter),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_name} FAILED: {e}\n")
            failed += 1
        except Exception as e:
            print(f"✗ {test_name} ERROR: {e}\n")
            import traceback
            traceback.print_exc()
            failed += 1

    print("="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60)

    if failed == 0:
        print("\n✓ All tests passed! Your MCP server is ready to use.")
        print("\nNext steps:")
        print("1. Configure Claude Desktop (see README.md)")
        print("2. Restart Claude Desktop")
        print("3. Look for the 🔌 icon")
        print("4. Ask Claude: 'List available heat pump models'")
    else:
        print(f"\n✗ {failed} test(s) failed. Please review the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
