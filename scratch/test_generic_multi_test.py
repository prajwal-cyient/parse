import re

def generate_generic_multi_test_suite(req_id, req_text):
    text_lower = req_text.lower()
    tcs = []
    
    # 1. Detect Surfaces (e.g. Aileron, Elevator, Rudder, Spoiler)
    surfaces = []
    for s in ["Aileron", "Elevator", "Rudder", "Spoiler"]:
        if s.lower() in text_lower:
            surfaces.append(s)
            
    # 2. Extract Key Output and Condition Signals
    outputs = re.findall(r'set\s+([A-Za-z0-9_]+)\s+to\s+(True|False|[0-9A-Za-z_]+)', req_text, re.IGNORECASE)
    transitions = re.findall(r'transition\s+from\s+([A-Za-z0-9_]+)\s+to\s+([A-Za-z0-9_]+)', req_text, re.IGNORECASE)
    delays = re.findall(r'delay\s+(?:the\s+rising\s+edge\s+transition\s+of\s+)?([A-Za-z0-9_]+).*?yield\s+([A-Za-z0-9_]+).*?(\d+\s*ms)', req_text, re.IGNORECASE)
    
    # CASE A: Multi-Surface Requirements (e.g. LRUSWRS-1407, 1408)
    if len(surfaces) > 1:
        for surf in surfaces:
            # Normal
            tcs.append({
                "test_case_id": f"{req_id}_N1_{surf}",
                "requirement_id": req_id,
                "test_type": "NORMAL",
                "description": f"Verify nominal requirement behavior on {surf} surface.",
                "initial_condition": f"Operational Mode: FLIGHT_MODE; Surface = {surf}; LRU configured for {surf}.",
                "test_inputs": f"Surface_Config = {surf}; Enable_Condition = True; Valid_Message = True.",
                "expected_result": f"Behavior verified for {surf} surface; Status_Active = True.",
                "pass_criteria": f"Observed outputs match required state on {surf} surface.",
                "related_requirements": "",
                "test_procedure_notes": "Verify via STL_Bus telemetry."
            })
            # DC (Decision Coverage)
            tcs.append({
                "test_case_id": f"{req_id}_DC_{surf}",
                "requirement_id": req_id,
                "test_type": "DC",
                "description": f"Decision coverage: Verify behavior suppressed when condition is False on {surf} surface.",
                "initial_condition": f"Operational Mode: FLIGHT_MODE; Surface = {surf}; LRU configured for {surf}.",
                "test_inputs": f"Surface_Config = {surf}; Enable_Condition = False; Valid_Message = True.",
                "expected_result": f"Behavior suppressed on {surf} surface; Status_Active = False.",
                "pass_criteria": f"Status_Active equals False on {surf} surface.",
                "related_requirements": "",
                "test_procedure_notes": "Verify via STL_Bus telemetry."
            })
            
    # CASE B: Delay / Timing Requirements (e.g. LRUSWRS-1402, 1403)
    elif delays:
        sig_in, sig_out, delay_val = delays[0]
        tcs.append({
            "test_case_id": f"{req_id}_N1",
            "requirement_id": req_id,
            "test_type": "NORMAL",
            "description": f"Verify rising edge of {sig_in} is delayed by {delay_val} to yield {sig_out}.",
            "initial_condition": f"Operational Mode: FLIGHT_MODE; {sig_in} initialized to False; {sig_out} = False.",
            "test_inputs": f"{sig_in} transitions from False to True; Timer = {delay_val}.",
            "expected_result": f"{sig_out} transitions to True after exactly {delay_val}.",
            "pass_criteria": f"{sig_out} asserted at elapsed time {delay_val} +- 1 ms.",
            "related_requirements": "",
            "test_procedure_notes": "Verify via STL_Bus telemetry and high-speed logic analyzer."
        })
        tcs.append({
            "test_case_id": f"{req_id}_DC_False",
            "requirement_id": req_id,
            "test_type": "DC",
            "description": f"Decision coverage: Verify {sig_out} remains False when {sig_in} remains False.",
            "initial_condition": f"Operational Mode: FLIGHT_MODE; {sig_in} initialized to False; {sig_out} = False.",
            "test_inputs": f"{sig_in} remains False; Timer = {delay_val}.",
            "expected_result": f"{sig_out} remains False.",
            "pass_criteria": f"{sig_out} equals False.",
            "related_requirements": "",
            "test_procedure_notes": "Verify via STL_Bus telemetry."
        })
        
    # CASE C: General DO-178C Level B (NORMAL + DC + BOUNDARY + ROBUSTNESS)
    else:
        # 1. NORMAL
        tcs.append({
            "test_case_id": f"{req_id}_NORMAL_01",
            "requirement_id": req_id,
            "test_type": "NORMAL",
            "description": f"Verify nominal operational execution for {req_id}.",
            "initial_condition": "Operational Mode: FLIGHT_MODE; Target Asset Type: ATYPE_1; Target LRU: LRU_1.",
            "test_inputs": "Operational_Stimulus = True; Mode_Active = True.",
            "expected_result": "Operational outputs match required specification; Complete_Flag = True.",
            "pass_criteria": "Outputs equal required values and Complete_Flag is True.",
            "related_requirements": "",
            "test_procedure_notes": "Verify via STL_Bus transmission and memory registers."
        })
        # 2. DC (Decision Coverage)
        tcs.append({
            "test_case_id": f"{req_id}_DC_01",
            "requirement_id": req_id,
            "test_type": "DC",
            "description": f"Decision coverage: Verify negative condition execution for {req_id}.",
            "initial_condition": "Operational Mode: FLIGHT_MODE; Target Asset Type: ATYPE_1; Target LRU: LRU_1.",
            "test_inputs": "Operational_Stimulus = False; Mode_Active = True.",
            "expected_result": "Action suppressed; Complete_Flag = False; Output_Fault = False.",
            "pass_criteria": "Complete_Flag equals False and Output_Fault equals False.",
            "related_requirements": "",
            "test_procedure_notes": "Verify via STL_Bus telemetry."
        })
        # 3. BOUNDARY
        tcs.append({
            "test_case_id": f"{req_id}_BOUNDARY_01",
            "requirement_id": req_id,
            "test_type": "BOUNDARY",
            "description": f"Boundary verification: Verify threshold limits for {req_id}.",
            "initial_condition": "Operational Mode: FLIGHT_MODE; Target Asset Type: ATYPE_1; Target LRU: LRU_1.",
            "test_inputs": "Operational_Stimulus = Threshold_Value; Mode_Active = True.",
            "expected_result": "Boundary output asserted correctly; Complete_Flag = True.",
            "pass_criteria": "Observed boundary transition matches expected threshold.",
            "related_requirements": "",
            "test_procedure_notes": "Verify via STL_Bus telemetry."
        })
        
    return tcs

# Test Sample 4 requirements
sample4_reqs = [
    ("LRUSWRS-1400", "The LRU shall set Low_Threshold_Anomaly_NodeB_Monitor to True if any of PreDrive_Fault_Active, Rotor_Lock_Engaged, Inverter_Bridge_Fault are True, otherwise False."),
    ("LRUSWRS-1402", "The LRU shall delay the rising edge transition of Hi_Enable_Envelope to yield Hi_Enable_Delay_Envelope with a delay of 40 ms."),
    ("LRUSWRS-1407", "The LRU software shall transition from Idle_Mode_StateLgc to Location_State_StateLgc on primary surfaces (Aileron, Elevator, Rudder)."),
    ("LRUSWRS-1408", "The LRU software shall energize the MSV solenoid for primary surfaces (Aileron, Elevator, Rudder).")
]

total = 0
for rid, rtext in sample4_reqs:
    generated = generate_generic_multi_test_suite(rid, rtext)
    total += len(generated)
    print(f"Req {rid}: generated {len(generated)} test cases")
    for tc in generated:
        print(f"   [{tc['test_type']}] {tc['test_case_id']}: {tc['description']}")
print(f"\nTotal test cases for these 4 reqs: {total}")
