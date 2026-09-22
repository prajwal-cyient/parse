import json
import re

with open('app/backend/knowledge_suite.json', 'r', encoding='utf-8') as f:
    suite = json.load(f)

for req_id, tcs in suite.items():
    if isinstance(tcs, list):
        for tc in tcs:
            ti = tc.get('test_inputs', '')
            lines = [l.strip() for l in ti.split(';') if l.strip()]
            for l in lines:
                if any(k in l.lower() for k in ['_fault', '_complete', 'calculated_', 'derived_', 'fault =', 'status =']):
                    print(f'{tc.get("test_case_id")} [{tc.get("test_type")}]: "{l}"')
