#!/usr/bin/env python3
"""
Test script for the Reports API endpoints.

This script tests:
1. Saving a report to Cloud Storage
2. Retrieving a report by ID
3. Getting a new signed URL
4. Listing reports
5. Deleting a report
"""

import httpx
import json
import uuid
from datetime import datetime
import sys

# API Configuration
API_BASE_URL = "https://heatpump-api-bo6wip2gyq-nw.a.run.app"
# For local testing, use: API_BASE_URL = "http://localhost:8000"

# Test data
TEST_REPORT_ID = str(uuid.uuid4())


def test_save_report():
    """Test saving a simulation report."""
    print("\n" + "="*60)
    print("TEST 1: Save Report")
    print("="*60)

    sample_report = {
        "simulation_data": {
            "configuration_results": {
                "cop": 4.23,
                "heat_output_w": 10500000.0,
                "power_input_w": 2482000.0,
                "heat_input_w": 8018000.0,
                "converged": True
            },
            "topology_refrigerant": {
                "topology_type": "HeatPumpIHX",
                "model_name": "Test Model",
                "refrigerant": "R134a",
                "is_cascade": False
            },
            "state_variables": {
                "connections": [],
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
                    "type": "HeatPumpIHX",
                    "refrig": "R134a"
                }
            }
        },
        "metadata": {
            "report_id": TEST_REPORT_ID,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "model_name": "Test Heat Pump Model",
            "topology": "HeatPumpIHX",
            "refrigerant": "R134a",
            "api_version": "0.1.0"
        }
    }

    try:
        print(f"Sending save request for report {TEST_REPORT_ID}...")
        response = httpx.post(
            f"{API_BASE_URL}/api/v1/reports/save",
            json=sample_report,
            timeout=30.0
        )

        if response.status_code == 201:
            data = response.json()
            print("[PASS] Report saved successfully")
            print(f"  Report ID: {data['report_id']}")
            print(f"  Storage URL: {data['storage_url']}")
            print(f"  Signed URL: {data['signed_url'][:80]}...")
            print(f"  Expires: {data['expires_at']}")
            return True
        else:
            print(f"[FAIL] Save failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    except Exception as e:
        print(f"[FAIL] Exception occurred: {e}")
        return False


def test_get_report():
    """Test retrieving a report."""
    print("\n" + "="*60)
    print("TEST 2: Get Report")
    print("="*60)

    try:
        print(f"Retrieving report {TEST_REPORT_ID}...")
        response = httpx.get(
            f"{API_BASE_URL}/api/v1/reports/{TEST_REPORT_ID}",
            timeout=30.0
        )

        if response.status_code == 200:
            data = response.json()
            print("[PASS] Report retrieved successfully")
            print(f"  Has metadata: {'metadata' in data}")
            print(f"  Has configuration_results: {'configuration_results' in data}")
            print(f"  COP: {data.get('configuration_results', {}).get('cop', 'N/A')}")
            return True
        else:
            print(f"[FAIL] Retrieval failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    except Exception as e:
        print(f"[FAIL] Exception occurred: {e}")
        return False


def test_get_signed_url():
    """Test generating a new signed URL."""
    print("\n" + "="*60)
    print("TEST 3: Get Signed URL")
    print("="*60)

    try:
        print(f"Getting new signed URL for report {TEST_REPORT_ID}...")
        response = httpx.get(
            f"{API_BASE_URL}/api/v1/reports/{TEST_REPORT_ID}/url",
            params={"expiration_days": 7},
            timeout=30.0
        )

        if response.status_code == 200:
            data = response.json()
            print("[PASS] Signed URL generated")
            print(f"  Signed URL: {data['signed_url'][:80]}...")
            print(f"  Expires: {data['expires_at']}")
            return True
        else:
            print(f"[FAIL] URL generation failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    except Exception as e:
        print(f"[FAIL] Exception occurred: {e}")
        return False


def test_list_reports():
    """Test listing reports."""
    print("\n" + "="*60)
    print("TEST 4: List Reports")
    print("="*60)

    try:
        print("Listing reports...")
        response = httpx.get(
            f"{API_BASE_URL}/api/v1/reports/",
            params={"limit": 10},
            timeout=30.0
        )

        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] Found {len(data)} reports")
            if data:
                print(f"  Latest report ID: {data[0].get('report_id', 'N/A')}")
            return True
        else:
            print(f"[FAIL] Listing failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    except Exception as e:
        print(f"[FAIL] Exception occurred: {e}")
        return False


def test_delete_report():
    """Test deleting a report."""
    print("\n" + "="*60)
    print("TEST 5: Delete Report")
    print("="*60)

    try:
        print(f"Deleting report {TEST_REPORT_ID}...")
        response = httpx.delete(
            f"{API_BASE_URL}/api/v1/reports/{TEST_REPORT_ID}",
            timeout=30.0
        )

        if response.status_code == 204:
            print("[PASS] Report deleted successfully")
            return True
        else:
            print(f"[FAIL] Deletion failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False

    except Exception as e:
        print(f"[FAIL] Exception occurred: {e}")
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Heat Pump Reports API - Test Suite")
    print("="*60)
    print(f"API URL: {API_BASE_URL}")
    print(f"Test Report ID: {TEST_REPORT_ID}")

    tests = [
        ("Save Report", test_save_report),
        ("Get Report", test_get_report),
        ("Get Signed URL", test_get_signed_url),
        ("List Reports", test_list_reports),
        ("Delete Report", test_delete_report),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except httpx.ConnectError:
            print(f"\n[FAIL] Could not connect to API at {API_BASE_URL}")
            print("  Make sure the API is running and accessible")
            failed += 1
            break
        except Exception as e:
            print(f"\n[FAIL] Unexpected error in {test_name}: {e}")
            failed += 1

    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60)

    if failed == 0:
        print("\n[SUCCESS] All tests passed!")
        print("\nYour Reports API is working correctly.")
        print("\nNext steps:")
        print("  1. Integrate with Streamlit dashboard")
        print("  2. Test from actual simulation results")
        print("  3. Verify reports in Cloud Storage bucket")
    else:
        print(f"\n[FAILURE] {failed} test(s) failed")
        print("\nTroubleshooting:")
        print("  1. Check if GCS bucket exists: gsutil ls gs://heatpump-outputs")
        print("  2. Verify environment variables are set in Cloud Run")
        print("  3. Check API logs: gcloud run services logs read heatpump-api --region=europe-west2")
        sys.exit(1)


if __name__ == "__main__":
    main()
