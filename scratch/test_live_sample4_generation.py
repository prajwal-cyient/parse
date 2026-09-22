import urllib.request
import json
import re

prompt = """You are a DO-178C Level B Aerospace Verification Test Engineer.
Generate comprehensive DO-178C test cases in JSON format for the requirement below.

REQUIREMENT:
Requirement ID: LRUSWRS-1400
Requirement Statement:
The LRU shall set Low_Threshold_Anomaly_NodeB_Monitor to True if any of the following signals are True:
- PreDrive_Fault_Active
- Rotor_Lock_Engaged
- Inverter_Bridge_Fault
Otherwise, Low_Threshold_Anomaly_NodeB_Monitor shall be set to False.

Return ONLY a JSON object with this structure:
{
  "test_cases": [
    {
      "test_case_id": "TC_LRUSWRS_1400_NORMAL",
      "requirement_id": "LRUSWRS-1400",
      "description": "Verify Low_Threshold_Anomaly_NodeB_Monitor set to True when PreDrive_Fault_Active is True",
      "test_type": "NORMAL",
      "initial_condition": "Operational Mode: FLIGHT_MODE; Target LRU: LRU_1; Low_Threshold_Anomaly_NodeB_Monitor initialized to False.",
      "test_inputs": "PreDrive_Fault_Active = True; Rotor_Lock_Engaged = False; Inverter_Bridge_Fault = False.",
      "expected_result": "Low_Threshold_Anomaly_NodeB_Monitor = True.",
      "pass_criteria": "Low_Threshold_Anomaly_NodeB_Monitor equals True.",
      "related_requirements": "",
      "test_procedure_notes": "Verify via telemetry bus."
    },
    {
      "test_case_id": "TC_LRUSWRS_1400_DC_FALSE",
      "requirement_id": "LRUSWRS-1400",
      "description": "Verify Low_Threshold_Anomaly_NodeB_Monitor set to False when all fault signals are False",
      "test_type": "DC",
      "initial_condition": "Operational Mode: FLIGHT_MODE; Target LRU: LRU_1; Low_Threshold_Anomaly_NodeB_Monitor initialized to True.",
      "test_inputs": "PreDrive_Fault_Active = False; Rotor_Lock_Engaged = False; Inverter_Bridge_Fault = False.",
      "expected_result": "Low_Threshold_Anomaly_NodeB_Monitor = False.",
      "pass_criteria": "Low_Threshold_Anomaly_NodeB_Monitor equals False.",
      "related_requirements": "",
      "test_procedure_notes": "Verify via telemetry bus."
    }
  ]
}
"""

req = urllib.request.Request(
    'http://localhost:11434/api/generate',
    data=json.dumps({
        'model': 'gpt-oss:latest',
        'prompt': prompt,
        'stream': False,
        'options': {'temperature': 0.0, 'num_predict': 1500}
    }).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req, timeout=45) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        raw_text = res.get('response', '')
        print('Response length:', len(raw_text))
        print('Raw Response:\n', raw_text)
except Exception as e:
    print('Error:', e)
