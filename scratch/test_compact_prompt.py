import urllib.request
import json

prompt = """You are an aerospace DO-178C test engineer. Generate a DO-178C test case in JSON format for the requirement below.

Requirement:
Requirement ID: SWRS-9999
Statement: When Hydraulic_System_Pressure exceeds 3000 PSI and Pilot_Stick_Pitch_Deflection > 5.0 deg, the Actuator_Control_Valve shall transition to POSITION_ACTIVE within 15 ms and transmit Valve_Telemetry_Frame (ID 0x0088) with Actuator_Status = ENGAGED and Fault_Indicator = False.

Respond ONLY with valid JSON in this structure:
{
  "test_cases": [
    {
      "test_case_id": "TC_SWRS_9999_NORMAL",
      "requirement_id": "SWRS-9999",
      "description": "Verify nominal activation of actuator valve when pressure exceeds 3000 PSI and deflection > 5.0 deg.",
      "test_type": "NORMAL",
      "initial_condition": "Operational Mode: FLIGHT_MODE; Actuator_Control_Valve in STANDBY.",
      "test_inputs": "Hydraulic_System_Pressure = 3200 PSI; Pilot_Stick_Pitch_Deflection = 6.0 deg.",
      "expected_result": "Actuator_Control_Valve = POSITION_ACTIVE; Valve_Telemetry_Frame ID = 0x0088; Actuator_Status = ENGAGED; Fault_Indicator = False.",
      "pass_criteria": "Actuator transitions to POSITION_ACTIVE within 15 ms and telemetry frame is transmitted.",
      "test_procedure_notes": "Verify via telemetry bus frame 0x0088."
    }
  ]
}
"""

payload = {
    'model': 'gpt-oss:latest',
    'prompt': prompt,
    'stream': False,
    'options': {'temperature': 0.0, 'num_predict': 1024}
}

req = urllib.request.Request(
    'http://localhost:11434/api/generate',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

with urllib.request.urlopen(req, timeout=45) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    print("Response text length:", len(res.get('response', '')))
    print(res.get('response'))
