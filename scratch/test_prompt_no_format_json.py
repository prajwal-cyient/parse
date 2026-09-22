import urllib.request
import json
import sys
sys.path.insert(0, 'app/backend')
from ollama_client import OllamaClient

req_id = 'SWRS-9999'
req_text = 'When Hydraulic_System_Pressure exceeds 3000 PSI and Pilot_Stick_Pitch_Deflection > 5.0 deg, the Actuator_Control_Valve shall transition to POSITION_ACTIVE within 15 ms and transmit Valve_Telemetry_Frame (ID 0x0088) with Actuator_Status = ENGAGED and Fault_Indicator = False. If Hydraulic_System_Pressure <= 3000 PSI, the system shall maintain Valve_Telemetry_Frame with Fault_Indicator = True and Actuator_Status = STANDBY.'

prompt = OllamaClient.PROMPT_TEMPLATE.format(req_id=req_id, req_text=req_text)

payload = {
    "model": "gpt-oss:latest",
    "prompt": prompt,
    "stream": False,
    "options": {"temperature": 0.0, "num_ctx": 4096, "num_predict": 1024},
}

req = urllib.request.Request(
    'http://localhost:11434/api/generate',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

with urllib.request.urlopen(req, timeout=60) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    raw_output = res.get('response', '')
    print("RAW LLM OUTPUT:")
    print(raw_output)
    print("\nPARSED VIA AUTO_REPAIR_JSON:")
    repaired = OllamaClient.auto_repair_json(raw_output)
    parsed = json.loads(repaired)
    print(json.dumps(parsed, indent=2))
