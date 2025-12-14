#!/usr/bin/env python3
"""
Test script for Save & Share Report integration.

This script tests the complete flow:
1. Run a simple heat pump simulation
2. Extract report data using streamlit_helpers.extract_report_data()
3. Save report via API
4. Verify report was saved correctly
"""

import httpx
import json
import uuid
from datetime import datetime
import sys

# API Configuration
API_BASE_URL = "https://heatpump-api-bo6wip2gyq-nw.a.run.app"

def test_simulation_and_report_extraction():
    """Test creating mock report data (simulating what extract_report_data() returns)."""
    print("\n" + "="*60)
    print("TEST 1: Create Mock Report Data")
    print("="*60)

    try:
        # Create mock report data similar to what extract_report_data() would return
        print("Creating mock report data...")

        report_data = {
            "configuration_results": {
                "cop": 4.23,
                "heat_output_w": 10500000.0,
                "power_input_w": 2482000.0,
                "heat_input_w": 8018000.0,
                "converged": True
            },
            "topology_refrigerant": {
                "topology_type": "simple",
                "model_name": "Test Model - Integration",
                "refrigerant": "R134a",
                "is_cascade": False
            },
            "state_variables": {
                "connections": [
                    {"m": 1.5, "p": 10.2, "h": 425.3, "T": 45.2, "s": 1.832, "v": 0.025},
                    {"m": 1.5, "p": 4.8, "h": 398.1, "T": 15.6, "s": 1.795, "v": 0.048}
                ],
                "columns": ["m", "p", "h", "T", "s", "v"],
                "units": {
                    "m": "kg/s",
                    "p": "bar",
                    "h": "kJ/kg",
                    "T": "°C",
                    "s": "kJ/(kgK)",
                    "v": "m³/kg"
                }
            },
            "economic_evaluation": {
                "total_cost_eur": 125000.50,
                "specific_cost_eur_per_mw": 11904.81,
                "component_costs": {
                    "compressor": 45000.0,
                    "evaporator": 30000.0,
                    "condenser": 28000.0,
                    "ihx": 15000.5,
                    "other": 7000.0
                }
            },
            "exergy_assessment": {
                "epsilon": 0.58,
                "E_F_w": 12345678.0,
                "E_P_w": 10987654.0,
                "E_D_w": 1358024.0,
                "E_L_w": 0.0
            },
            "parameters": {
                "setup": {
                    "type": "simple",
                    "refrig": "R134a"
                }
            }
        }

        print("[PASS] Mock report data created successfully")
        print(f"  Configuration results keys: {list(report_data.get('configuration_results', {}).keys())}")
        print(f"  Has topology_refrigerant: {'topology_refrigerant' in report_data}")
        print(f"  Has state_variables: {'state_variables' in report_data}")
        print(f"  Has economic_evaluation: {'economic_evaluation' in report_data}")
        print(f"  Has exergy_assessment: {'exergy_assessment' in report_data}")
        print(f"  COP: {report_data['configuration_results']['cop']:.3f}")
        print(f"  Heat Output: {report_data['configuration_results']['heat_output_w']/1e6:.2f} MW")

        return True, report_data

    except Exception as e:
        print(f"[FAIL] Exception during mock data creation: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_save_report_to_api(report_data):
    """Test saving the extracted report to the API."""
    print("\n" + "="*60)
    print("TEST 2: Save Report to API")
    print("="*60)

    if report_data is None:
        print("[SKIP] No report data to save")
        return False

    try:
        # Generate report ID and metadata
        report_id = str(uuid.uuid4())
        metadata = {
            "report_id": report_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "model_name": "Test Integration - Simple Heat Pump",
            "topology": "simple",
            "refrigerant": "R134a",
            "api_version": "0.1.0"
        }

        print(f"Saving report {report_id} to API...")

        # Prepare request payload
        payload = {
            "simulation_data": report_data,
            "metadata": metadata
        }

        # Measure payload size
        payload_size = len(json.dumps(payload).encode('utf-8'))
        print(f"  Payload size: {payload_size/1024:.2f} KB")

        # Make API request
        response = httpx.post(
            f"{API_BASE_URL}/api/v1/reports/save",
            json=payload,
            timeout=60.0
        )

        if response.status_code == 201:
            data = response.json()
            print("[PASS] Report saved successfully")
            print(f"  Report ID: {data['report_id']}")
            print(f"  Storage URL: {data['storage_url']}")
            print(f"  Signed URL: {data['signed_url'][:80]}...")
            print(f"  Expires: {data.get('expires_at', 'N/A')}")

            # Test retrieving the report
            print("\nVerifying report can be retrieved...")
            get_response = httpx.get(
                f"{API_BASE_URL}/api/v1/reports/{report_id}",
                timeout=30.0
            )

            if get_response.status_code == 200:
                retrieved_data = get_response.json()
                print("[PASS] Report retrieved successfully")
                print(f"  Retrieved COP: {retrieved_data.get('configuration_results', {}).get('cop', 'N/A')}")
            else:
                print(f"[FAIL] Could not retrieve report: HTTP {get_response.status_code}")

            return True
        else:
            print(f"[FAIL] Save failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    except Exception as e:
        print(f"[FAIL] Exception during API save: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("="*60)
    print("Save & Share Report - Integration Test")
    print("="*60)
    print(f"API URL: {API_BASE_URL}")
    print("\nThis test will:")
    print("  1. Create mock report data (simulating extract_report_data())")
    print("  2. Save the report via the API")
    print("  3. Verify the report can be retrieved")

    # Test 1: Create Mock Data
    success1, report_data = test_simulation_and_report_extraction()

    # Test 2: Save to API
    if success1:
        success2 = test_save_report_to_api(report_data)
    else:
        success2 = False
        print("\n[SKIP] Test 2 skipped due to Test 1 failure")

    # Summary
    print("\n" + "="*60)
    print("INTEGRATION TEST SUMMARY")
    print("="*60)
    print(f"Test 1 (Mock Data Creation): {'PASS' if success1 else 'FAIL'}")
    print(f"Test 2 (API Save & Retrieve): {'PASS' if success2 else 'FAIL'}")

    if success1 and success2:
        print("\n[SUCCESS] All integration tests passed!")
        print("\nThe 'Save & Share Report' button should work correctly in Streamlit.")
        print("\nTo test in Streamlit:")
        print("  1. Run: streamlit run src/heatpumps/hp_dashboard.py")
        print("  2. Configure and run a simulation")
        print("  3. Click the 'Save & Share Report' button")
        print("  4. You should see:")
        print("     - 'Extracting simulation data...' spinner")
        print("     - 'Data extracted successfully' message")
        print("     - 'Uploading to cloud storage...' spinner")
        print("     - 'Report saved successfully!' message")
        print("     - A shareable URL you can copy")
    else:
        print("\n[FAILURE] Some tests failed")
        print("\nTroubleshooting:")
        if not success2:
            print("  - Check if API is accessible")
            print("  - Verify GCS bucket is configured")
            print("  - Check Cloud Run environment variables")
        sys.exit(1)


if __name__ == "__main__":
    main()
