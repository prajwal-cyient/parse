import json

with open('app/backend/knowledge_suite.json', 'r', encoding='utf-8') as f:
    suite = json.load(f)

for req_id, tcs in suite.items():
    if isinstance(tcs, list):
        for tc in tcs:
            tt = tc.get('test_type', '')
            desc = tc.get('description', '').lower()
            er = tc.get('expected_result', '')
            if tt == 'DC' or 'false' in desc or 'outside' in desc:
                if '= False' not in er and '= True' not in er and 'False' not in er:
                    print(f"TC: {tc.get('test_case_id')} | REQ: {req_id}")
                    print(f"   DESC: {tc.get('description')}")
                    print(f"   ER:   {er}\n")
