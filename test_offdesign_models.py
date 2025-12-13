#!/usr/bin/env python
"""
Test off-design simulation with different heat pump models.

This script tests which models support off-design simulation to identify
if the 'heat exchanger' KeyError is model-specific or a broader issue.

Usage:
    python test_offdesign_models.py
"""

import httpx
import sys

API_BASE_URL = "http://localhost:8000"

def test_offdesign_with_model(model_name):
    """Test off-design simulation with a specific model."""
    print(f"\n{'='*60}")
    print(f"Testing off-design simulation with model: {model_name}")
    print(f"{'='*60}")

    # Prepare off-design simulation request with minimal configuration
    request_data = {
        "model_name": model_name,
        "params": {},
        "offdesign_config": {
            "heat_source_range": {
                "constant": False,
                "start": 5.0,
                "end": 15.0,
                "steps": 2  # Just 2 steps to test quickly
            },
            "heat_sink_range": {
                "constant": False,
                "start": 30.0,
                "end": 40.0,
                "steps": 2
            },
            "partload_range": {
                "min_ratio": 0.8,
                "max_ratio": 1.0,
                "steps": 2
            }
        }
    }

    print(f"  Configuration: 2x2x2 = 8 operating points")
    print(f"  (This should take ~1 minute...)")

    try:
        response = httpx.post(
            f"{API_BASE_URL}/api/v1/simulate/offdesign",
            json=request_data,
            timeout=300.0,  # 5 minutes
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n[PASS] Off-design simulation completed")
            print(f"  Converged: {data['converged']}")
            print(f"  Design COP: {data.get('design_cop', 'N/A')}")
            print(f"  Total Points: {data['total_points']}")
            print(f"  Converged Points: {data['converged_points']}")

            if data["converged"] and data.get("operating_points"):
                print(f"  Sample operating point:")
                point = data["operating_points"][0]
                if point["converged"]:
                    print(f"    T_hs={point['T_hs_ff']:.1f}°C, T_cons={point['T_cons_ff']:.1f}°C, "
                          f"PL={point['partload_ratio']:.1%}: COP={point['cop']:.3f}")

            return True, "SUCCESS"
        else:
            print(f"\n[FAIL] HTTP Error: {response.status_code}")
            print(f"  Response: {response.text}")
            return False, f"HTTP {response.status_code}"

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


def test_partload_with_model(model_name):
    """Test part-load simulation with a specific model."""
    print(f"\n{'='*60}")
    print(f"Testing part-load simulation with model: {model_name}")
    print(f"{'='*60}")

    request_data = {
        "model_name": model_name,
        "params": {},
        "partload_config": {
            "min_ratio": 0.5,
            "max_ratio": 1.0,
            "steps": 3  # Just 3 steps to test quickly
        }
    }

    print(f"  Configuration: 50% to 100% load, 3 steps")
    print(f"  (This should take ~30 seconds...)")

    try:
        response = httpx.post(
            f"{API_BASE_URL}/api/v1/simulate/partload",
            json=request_data,
            timeout=120.0,
        )

        if response.status_code == 200:
            data = response.json()
            print(f"\n[PASS] Part-load simulation completed")
            print(f"  Converged: {data['converged']}")
            print(f"  Design COP: {data.get('design_cop', 'N/A')}")
            print(f"  Total Points: {data['total_points']}")
            print(f"  Converged Points: {data['converged_points']}")

            if data["converged"] and data.get("partload_points"):
                print(f"  Part-load points:")
                for point in data["partload_points"]:
                    if point["converged"]:
                        print(f"    Load {point['load_ratio']:.1%}: COP={point['cop']:.3f}")

            return True, "SUCCESS"
        else:
            print(f"\n[FAIL] HTTP Error: {response.status_code}")
            print(f"  Response: {response.text}")
            return False, f"HTTP {response.status_code}"

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


def main():
    """Test off-design simulation with multiple models."""
    print("="*60)
    print("Heat Pump Model Off-Design Compatibility Test")
    print("="*60)
    print(f"API Base URL: {API_BASE_URL}")

    # Test with different model types
    models_to_test = [
        "simple",      # Original failing model
        "ihx",         # Has internal heat exchanger
        "econ_closed", # Has economizer (closed)
        "ic",          # Intercooler model
    ]

    results = {}

    for model_name in models_to_test:
        try:
            # Test part-load first (simpler)
            pl_success, pl_error = test_partload_with_model(model_name)

            # Test off-design
            od_success, od_error = test_offdesign_with_model(model_name)

            results[model_name] = {
                "partload": (pl_success, pl_error),
                "offdesign": (od_success, od_error)
            }

        except httpx.ConnectError:
            print(f"\n[FAIL] Error: Could not connect to API server")
            print(f"  Make sure the API is running at {API_BASE_URL}")
            print("  Start it with: heatpumps-api")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")
            break

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY: Off-Design Compatibility Test Results")
    print("="*60)

    for model_name, result in results.items():
        pl_success, pl_error = result["partload"]
        od_success, od_error = result["offdesign"]

        print(f"\n{model_name}:")
        print(f"  Part-load:  {'[PASS]' if pl_success else '[FAIL]'} {'' if pl_success else f'({pl_error})'}")
        print(f"  Off-design: {'[PASS]' if od_success else '[FAIL]'} {'' if od_success else f'({od_error})'}")

    # Conclusion
    print("\n" + "="*60)
    working_models = [m for m, r in results.items()
                      if r["partload"][0] and r["offdesign"][0]]
    failing_models = [m for m, r in results.items()
                      if not (r["partload"][0] and r["offdesign"][0])]

    if working_models:
        print(f"[PASS] Models with working off-design: {', '.join(working_models)}")
    if failing_models:
        print(f"[FAIL] Models with failing off-design: {', '.join(failing_models)}")

    print("="*60)


if __name__ == "__main__":
    main()
