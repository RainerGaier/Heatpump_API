#!/usr/bin/env python
"""
Test script for the Heatpump API deployed on Google Cloud Run.

This script verifies the Cloud Run deployment is working correctly.

Usage:
    python test_api_cloud.py
"""

import httpx
import sys
import json

# Update this with your actual Cloud Run URL
API_BASE_URL = "https://heatpump-api-658843246978.europe-west2.run.app"


def test_health():
    """Test health check endpoint."""
    print("Testing health check...")
    response = httpx.get(f"{API_BASE_URL}/health")
    assert response.status_code == 200
    print(f"[PASS] Health check passed: {response.json()}")


def test_root():
    """Test root endpoint."""
    print("\nTesting root endpoint...")
    response = httpx.get(f"{API_BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    print(f"[PASS] Root endpoint passed")
    print(f"  API Name: {data['name']}")
    print(f"  Version: {data['version']}")


def test_list_models():
    """Test listing available models."""
    print("\nTesting model listing...")
    response = httpx.get(f"{API_BASE_URL}/api/v1/models")
    assert response.status_code == 200
    data = response.json()
    print(f"[PASS] Found {data['total_count']} models")
    print(f"  Sample models: {[m['name'] for m in data['models'][:10]]}")
    return data["models"]


def test_get_model_info(model_name):
    """Test getting model details."""
    print(f"\nTesting model info for {model_name}...")
    response = httpx.get(f"{API_BASE_URL}/api/v1/models/{model_name}")
    assert response.status_code == 200
    data = response.json()
    print(f"[PASS] Model info retrieved:")
    print(f"  Name: {data['name']}")
    print(f"  Topology: {data['topology']}")
    print(f"  Has IHX: {data['has_ihx']}")
    print(f"  Has Economizer: {data['has_economizer']}")
    return data


def test_simulation(model_name):
    """Test running a design simulation."""
    print(f"\nTesting design simulation for {model_name}...")

    # Prepare simulation request
    request_data = {
        "model_name": model_name,
        "params": {},
        "run_offdesign": False,
        "run_partload": False,
    }

    print(f"  Submitting simulation request...")
    print(f"  (This may take 10-30 seconds for convergence...)")

    response = httpx.post(
        f"{API_BASE_URL}/api/v1/simulate/design",
        json=request_data,
        timeout=60.0,
    )

    assert response.status_code == 200
    data = response.json()

    print(f"[PASS] Simulation completed")
    print(f"  Converged: {data['converged']}")

    if data["converged"]:
        print(f"  COP: {data['cop']:.3f}")
        print(f"  Exergy Efficiency: {data.get('epsilon', 'N/A')}")
        print(f"  Heat Output: {data['heat_output']:.0f} W")
        print(f"  Power Input: {data['power_input']:.0f} W")
    else:
        print(f"  Error: {data.get('error_message', 'Unknown error')}")

    return data


def test_api_docs():
    """Test API documentation endpoints."""
    print("\nTesting API documentation...")
    response = httpx.get(f"{API_BASE_URL}/docs")
    assert response.status_code == 200
    print(f"[PASS] Swagger UI accessible at: {API_BASE_URL}/docs")

    response = httpx.get(f"{API_BASE_URL}/redoc")
    assert response.status_code == 200
    print(f"[PASS] ReDoc accessible at: {API_BASE_URL}/redoc")


def main():
    """Run all tests."""
    print("="*60)
    print("Heatpump API Cloud Run Test Suite")
    print("="*60)
    print(f"API URL: {API_BASE_URL}")
    print()

    try:
        # Basic health check
        test_health()

        # Root endpoint
        test_root()

        # API documentation
        test_api_docs()

        # Model discovery
        models = test_list_models()

        # Pick a simple model for testing
        test_model = "simple"

        # Get model details
        test_get_model_info(test_model)

        # Run a simulation
        test_simulation(test_model)

        print("\n" + "="*60)
        print("[PASS] All tests passed!")
        print("="*60)
        print("\nYour Cloud Run deployment is working correctly!")
        print(f"\nAPI Resources:")
        print(f"  • Swagger UI: {API_BASE_URL}/docs")
        print(f"  • ReDoc: {API_BASE_URL}/redoc")
        print(f"  • Health: {API_BASE_URL}/health")
        print()

    except httpx.ConnectError:
        print("\n[FAIL] Error: Could not connect to API")
        print(f"  Make sure the Cloud Run service is deployed and accessible")
        print(f"  URL: {API_BASE_URL}")
        sys.exit(1)
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
