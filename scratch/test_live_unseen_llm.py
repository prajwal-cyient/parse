import urllib.request
import json

prompt = """You are a DO-178C Level B Aerospace Verification Engineer. Generate DO-178C test cases in JSON format for the following requirement:

REQUIREMENT:
Requirement ID: SWRS-9999-ELEVATOR-ACTUATOR
Requirement Statement:
When Hydraulic_System_Pressure exceeds 3000 PSI and Pilot_Stick_Pitch_Deflection > 5.0 deg, the Actuator_Control_Valve shall transition to POSITION_ACTIVE within 15 ms and transmit Valve_Telemetry_Frame (ID 0x0088) with Actuator_Status = ENGAGED and Fault_Indicator = False. If Hydraulic_System_Pressure <= 3000 PSI, the system shall maintain Valve_Telemetry_Frame with Fault_Indicator = True and Actuator_Status = STANDBY.

Return JSON with structure:
{"test_cases": [{"test_case_id": "...", "requirement_id": "...", "test_type": "NORMAL/DC/BOUNDARY/ROBUSTNESS", "description": "...", "initial_condition": "...", "test_inputs": "...", "expected_result": "...", "pass_criteria": "...", "test_procedure_notes": "..."}]}
"""

req = urllib.request.Request(
    'http://localhost:11434/api/generate',
    data=json.dumps({
        'model': 'gpt-oss:latest',
        'prompt': prompt,
        'format': 'json',
        'stream': False,
        'options': {'temperature': 0.0}
    }).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

with urllib.request.urlopen(req, timeout=60) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    parsed = json.loads(res.get('response'))
    print(json.dumps(parsed, indent=2))
