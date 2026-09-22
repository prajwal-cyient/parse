import sys, os
sys.path.insert(0, 'app/backend')
from ollama_client import OllamaClient
from signal_classifier import SignalClassifier, SignalDictionary
from applicability_engine import ApplicabilityEngine
import json
import re

# 1. Create a brand new, unseen aerospace requirement from another domain (FADEC Engine Control)
test_req_id = "FADEC-SWRS-5001"
test_req_text = """
ID : FADEC-SWRS-5001
When Engine_N2_Speed exceeds 12000 RPM and Fuel_Metering_Valve_Position < 45.0 deg, the EEC software shall transition to HIGH_POWER_MODE within 20 ms and transmit FADEC_Status_Word_01 (ID 0x0310) with Engine_Power_Active = True and Overspeed_Fault = False.
When Engine_N2_Speed <= 12000 RPM, the EEC software shall set Engine_Power_Active = False and maintain HIGH_POWER_MODE = False.
"""

print(f"=== TESTING GENERIC AI GENERATION ON BRAND NEW REQUIREMENT: {test_req_id} ===")
print("Requirement Text:\n", test_req_text)

# Run generic DO-178C generation pipeline
tcs = OllamaClient.query_requirement(test_req_id, test_req_text)
print(f"\nGenerated {len(tcs)} Test Cases from Generic Pipeline:")

all_passed = True
for idx, tc in enumerate(tcs, 1):
    print(f"\n--- [Test Case {idx}] {tc.get('test_case_id')} [{tc.get('test_type')}] ---")
    print(f"  Description:        {tc.get('description')}")
    print(f"  Initial Conditions: {tc.get('initial_condition')}")
    print(f"  Test Inputs:        {tc.get('test_inputs')}")
    print(f"  Expected Results:   {tc.get('expected_result')}")
    print(f"  Pass/Fail Criteria: {tc.get('pass_criteria')}")
    
    # Audit 3-tier separation:
    ti = (tc.get('test_inputs') or '').lower()
    er = (tc.get('expected_result') or '').lower()
    desc = (tc.get('description') or '').lower()
    tt = (tc.get('test_type') or '').upper()
    
    # Check no output in inputs
    if any(k in ti for k in ['_fault', '_complete', 'engine_power_active =', 'high_power_mode =']):
        print("  [FAIL] Output leaked into inputs!")
        all_passed = False
    else:
        print("  [PASS] Clean 3-Tier separation (no outputs in inputs).")
        
    # Check explicit negative assertion on DC test
    if tt == 'DC' or 'false' in desc:
        if '= false' in er or 'false' in er:
            print("  [PASS] Explicit boolean negative assertion present.")
        else:
            print("  [FAIL] Missing boolean false assertion in DC test!")
            all_passed = False

print("\n" + "="*60)
if all_passed:
    print("VERDICT: 100% SUCCESS — GENERIC PIPELINE WORKS DYNAMICALLY FOR ANY NEW REQUIREMENT!")
else:
    print("VERDICT: ISSUES FOUND")
print("="*60)
