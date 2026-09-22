import json
import re

with open('app/backend/knowledge_suite.json', 'r', encoding='utf-8') as f:
    suite = json.load(f)

count = 0
for req_id, tcs in suite.items():
    if isinstance(tcs, list):
        for tc in tcs:
            ti = tc.get('test_inputs', '')
            matches = re.findall(r'([A-Za-z0-9_]*(?:fault|complete)[A-Za-z0-9_]*\s*=\s*[^;,\n]+)', ti, re.IGNORECASE)
            if matches:
                count += 1
                print(f"[{count}] TC: {tc.get('test_case_id')} | REQ: {req_id}")
                print(f"    Inputs: {ti}")
                print(f"    Expected: {tc.get('expected_result')}")
                print(f"    Flags to remove: {matches}\n")

print(f"Total test cases with fault/completion flags in inputs: {count}")
