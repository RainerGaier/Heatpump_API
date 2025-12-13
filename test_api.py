#!/usr/bin/env python
"""
Quick test script for the Heatpump API.

This script demonstrates basic API usage and verifies the API is working correctly.
Run this after starting the API server with: heatpumps-api

Usage:
    python test_api.py
"""

import httpx
import sys
import json

API_BASE_URL = "http://localhost:8000"


def test_health():
    """Test health check endpoint."""
    print("Testing health check...")
    response = httpx.get(f"{API_BASE_URL}/health")
    assert response.status_code == 200
    print(f"✓ Health check passed: {response.json()}")


def test_list_models():
    """Test listing available models."""
    print("\nTesting model listing...")
    response = httpx.get(f"{API_BASE_URL}/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    print(f"✓ Found {data['total_count']} models")
    print(f"  Sample models: {[m['name'] for m in data['models'][:10]]}")
    return data["models"]


def test_get_model_info(model_name):
    """Test getting model details."""
    print(f"\nTesting model info for {model_name}...")
    response = httpx.get(f"{API_BASE_URL}/api/v1/models/{model_name}")
    assert response.status_code == 200
    data = response.json()
    print(f"✓ Model info retrieved:")
    print(f"  Name: {data['name']}")
    print(f"  Topology: {data['topology']}")
    print(f"  Has IHX: {data['has_ihx']}")
    print(f"  Has Economizer: {data['has_economizer']}")
    return data


def test_get_parameters(model_name):
    """Test getting default parameters."""
    print(f"\nTesting parameter retrieval for {model_name}...")
    response = httpx.get(f"{API_BASE_URL}/api/v1/models/{model_name}/parameters")
    assert response.status_code == 200
    data = response.json()
    print(f"✓ Default parameters retrieved")
    print(f"  Parameter keys: {list(data['parameters'].keys())[:10]}...")
    return data["parameters"]


def test_simulation(model_name):
    """Test running a design simulation."""
    print(f"\nTesting design simulation for {model_name}...")

    # Prepare simulation request
    request_data = {
        "model_name": model_name,
        "params": {
            # Optionally override parameters here
            # "T_hs_ff": 10.0,
            # "T_cons_ff": 35.0,
        },
        "run_offdesign": False,
        "run_partload": False,
    }

    print(f"  Submitting simulation request...")
    print(f"  (This may take 10-30 seconds for convergence...)")

    response = httpx.post(
        f"{API_BASE_URL}/api/v1/simulate/design",
        json=request_data,
        timeout=60.0,  # Allow 60 seconds for simulation
    )

    assert response.status_code == 200
    data = response.json()

    print(f"✓ Simulation completed")
    print(f"  Converged: {data['converged']}")

    if data["converged"]:
        print(f"  COP: {data['cop']:.3f}")
        print(f"  Exergy Efficiency: {data.get('epsilon', 'N/A')}")
        print(f"  Heat Output: {data['heat_output']:.0f} W")
        print(f"  Power Input: {data['power_input']:.0f} W")
    else:
        print(f"  Error: {data.get('error_message', 'Unknown error')}")

    return data


def test_refrigerants():
    """Test listing supported refrigerants."""
    print("\nTesting refrigerant listing...")
    response = httpx.get(f"{API_BASE_URL}/api/v1/models/refrigerants/list")
    assert response.status_code == 200
    data = response.json()
    print(f"✓ Found {data['total_count']} refrigerants")
    print(f"  Examples: {data['refrigerants'][:5]}")


def test_partload(model_name):
    """Test running part-load characteristics simulation."""
    print(f"\nTesting part-load simulation for {model_name}...")

    # Prepare part-load simulation request
    request_data = {
        "model_name": model_name,
        "params": {},  # Use defaults
        "run_offdesign": False,
        "run_partload": False,
    }

    print(f"  Submitting part-load simulation request...")
    print(f"  (This may take 1-3 minutes for off-design + part-load analysis...)")

    response = httpx.post(
        f"{API_BASE_URL}/api/v1/simulate/partload",
        json=request_data,
        timeout=300.0,  # Allow 5 minutes for part-load simulation
    )

    assert response.status_code == 200
    data = response.json()

    print(f"✓ Part-load simulation completed")
    print(f"  Converged: {data['converged']}")
    print(f"  Design COP: {data.get('design_cop', 'N/A')}")
    print(f"  Total Points: {data['total_points']}")
    print(f"  Converged Points: {data['converged_points']}")

    if data["converged"] and data["partload_points"]:
        print(f"  Part-load performance:")
        for point in data["partload_points"][:5]:  # Show first 5 points
            if point["converged"]:
                print(f"    Load {point['load_ratio']:.1%}: COP={point['cop']:.3f}, Q={point['heat_output']:.0f} W")
        if len(data["partload_points"]) > 5:
            print(f"    ... and {len(data['partload_points']) - 5} more points")
    else:
        print(f"  Warning: {data.get('error_message', 'Some points did not converge')}")

    return data


def test_partload_custom_range(model_name):
    """Test part-load simulation with custom range configuration."""
    print(f"\nTesting part-load simulation with custom range for {model_name}...")

    # Prepare request with custom part-load range
    request_data = {
        "model_name": model_name,
        "params": {},
        "partload_config": {
            "min_ratio": 0.5,
            "max_ratio": 1.0,
            "steps": 4
        }
    }

    print(f"  Custom range: 50% to 100% load, 4 steps")

    response = httpx.post(
        f"{API_BASE_URL}/api/v1/simulate/partload",
        json=request_data,
        timeout=300.0,
    )

    assert response.status_code == 200
    data = response.json()

    print(f"✓ Custom part-load simulation completed")
    print(f"  Total Points: {data['total_points']}")
    print(f"  Converged Points: {data['converged_points']}")

    return data


def test_offdesign(model_name):
    """Test running full off-design simulation with temperature sweeps."""
    print(f"\nTesting off-design simulation for {model_name}...")

    # Prepare off-design simulation request with custom ranges
    request_data = {
        "model_name": model_name,
        "params": {},
        "offdesign_config": {
            "heat_source_range": {
                "constant": False,
                "start": 5.0,
                "end": 15.0,
                "steps": 3
            },
            "heat_sink_range": {
                "constant": False,
                "start": 30.0,
                "end": 50.0,
                "steps": 3
            },
            "partload_range": {
                "min_ratio": 0.5,
                "max_ratio": 1.0,
                "steps": 3
            }
        }
    }

    print(f"  Heat source: 5°C to 15°C (3 steps)")
    print(f"  Heat sink: 30°C to 50°C (3 steps)")
    print(f"  Part-load: 50% to 100% (3 steps)")
    print(f"  Expected points: 3 × 3 × 3 = 27")
    print(f"  (This may take 2-5 minutes...)")

    response = httpx.post(
        f"{API_BASE_URL}/api/v1/simulate/offdesign",
        json=request_data,
        timeout=600.0,  # Allow 10 minutes for off-design simulation
    )

    assert response.status_code == 200
    data = response.json()

    print(f"✓ Off-design simulation completed")
    print(f"  Converged: {data['converged']}")
    print(f"  Design COP: {data.get('design_cop', 'N/A')}")
    print(f"  Total Points: {data['total_points']}")
    print(f"  Converged Points: {data['converged_points']}")

    if data["converged"] and data["operating_points"]:
        print(f"  Temperature ranges simulated:")
        print(f"    Heat source: {data['temperature_range']['T_hs_ff']}")
        print(f"    Heat sink: {data['temperature_range']['T_cons_ff']}")
        print(f"  Part-load range: {data['partload_range']}")

        # Show sample operating points
        print(f"  Sample operating points:")
        for point in data["operating_points"][:3]:  # Show first 3 points
            if point["converged"]:
                print(f"    T_hs={point['T_hs_ff']:.1f}°C, T_cons={point['T_cons_ff']:.1f}°C, "
                      f"PL={point['partload_ratio']:.1%}: COP={point['cop']:.3f}")
        if len(data["operating_points"]) > 3:
            print(f"    ... and {len(data['operating_points']) - 3} more points")
    else:
        print(f"  Warning: {data.get('error_message', 'Some points did not converge')}")

    return data


def test_ihx_parameter_override(model_name="ihx"):
    """Test IHX parameter override for models with internal heat exchanger."""
    print(f"\nTesting IHX parameter override for {model_name}...")

    # Prepare simulation request with IHX parameter override
    request_data = {
        "model_name": model_name,
        "params": {
            "ihx": {
                "dT_sh": 10.0  # Override superheat temperature difference
            }
        }
    }

    print(f"  Overriding IHX dT_sh to 10.0 K")

    response = httpx.post(
        f"{API_BASE_URL}/api/v1/simulate/design",
        json=request_data,
        timeout=60.0,
    )

    assert response.status_code == 200
    data = response.json()

    print(f"✓ IHX parameter override simulation completed")
    print(f"  Converged: {data['converged']}")
    if data["converged"]:
        print(f"  COP: {data['cop']:.3f}")

    return data


def main():
    """Run all tests."""
    print("=" * 60)
    print("Heatpump API Test Suite")
    print("=" * 60)
    print(f"API Base URL: {API_BASE_URL}")
    print()

    try:
        # Basic health check
        test_health()

        # Model discovery
        models = test_list_models()

        # Pick a simple model for testing (use the model key, not class name)
        test_model = "simple"

        # Get model details
        test_get_model_info(test_model)

        # Get default parameters
        test_get_parameters(test_model)

        # List refrigerants
        test_refrigerants()

        # Run a simulation (this is the heavy test)
        test_simulation(test_model)

        # Run part-load simulation (longest test - optional)
        print("\n" + "=" * 60)
        print("Optional: Extended simulation tests")
        print("These tests will take 5-10 minutes total. Skip? (y/n): ", end="", flush=True)
        # For automated testing, just run it
        # In interactive mode, you could add: skip = input().lower() == 'y'
        skip = False  # Set to True to skip by default
        if not skip:
            # Test basic part-load
            test_partload(test_model)

            # Test custom part-load range
            test_partload_custom_range(test_model)

            # Test full off-design simulation
            test_offdesign(test_model)

            # Test IHX parameter override
            test_ihx_parameter_override("ihx")
        else:
            print("Skipped")

        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        print("\nAPI is working correctly. Try these commands:")
        print(f"  • Swagger UI: {API_BASE_URL}/docs")
        print(f"  • ReDoc: {API_BASE_URL}/redoc")
        print()

    except httpx.ConnectError:
        print("\n✗ Error: Could not connect to API server")
        print(f"  Make sure the API is running at {API_BASE_URL}")
        print("  Start it with: heatpumps-api")
        sys.exit(1)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
