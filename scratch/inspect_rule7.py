import json
import re

with open('app/backend/knowledge_suite.json', 'r', encoding='utf-8') as f:
    suite = json.load(f)

count = 0
for req_id, tcs in suite.items():
    if isinstance(tcs, list):
        for tc in tcs:
            tt = tc.get('test_type', '')
            desc = tc.get('description', '')
            er = tc.get('expected_result', '')
            ti = tc.get('test_inputs', '')
            
            issues = []
            if tt == 'DC' or 'false' in desc.lower() or 'outside' in desc.lower() or 'not performed' in desc.lower() or 'invalid' in desc.lower():
                if '= False' not in er and '= True' not in er and 'False' not in er:
                    issues.append("Missing explicit boolean assertion in ER")
            if '10.0 (in)' in er or 'False operational value' in er:
                issues.append("Malformed placeholder/artifact in ER")
            if '10.0 (in)' in ti:
                issues.append("Malformed placeholder/artifact in TI")
                
            if issues:
                count += 1
                print(f"[{count}] TC: {tc.get('test_case_id')} [{tt}] | REQ: {req_id}")
                print(f"    Issues: {issues}")
                print(f"    DESC: {desc}")
                print(f"    TI:   {ti}")
                print(f"    ER:   {er}\n")

print(f"Total test cases with Rule 7 / text issues: {count}")
