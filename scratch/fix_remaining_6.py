import json

with open('app/backend/knowledge_suite.json', 'r', encoding='utf-8') as f:
    suite = json.load(f)

for req_id, tcs in suite.items():
    if isinstance(tcs, list):
        for tc in tcs:
            tc_id = tc.get('test_case_id', '')
            if tc_id == 'LRUSWRS-1001-STEP-INFORMATIONONLY-02':
                tc['expected_result'] = "IVT_Command_ISM remains 0x0000; IVT_CmdData_ISM remains 0x0000; Harmonizing_Active_STL = False; no new frames transmitted."
            elif tc_id == 'TC_LRUSWRS-1001-STEP-6-03':
                tc['expected_result'] = "Act_Disp_Raw_Avg remains baseline (0.0); Harmonizing_Active_STL = False; Expand_Stop_Collection_Complete = False."
            elif tc_id == 'TC_LRUSWRS-1001-STEP-6-04':
                tc['expected_result'] = "Act_Disp_Raw_Avg remains baseline (0.0); Harmonizing_Active_STL = False; Expand_Stop_Collection_Complete = False."
            elif tc_id == 'LRUSWRS-1001-STEP-20-INVALID-PROFILE-ELEVATOR-1':
                tc['expected_result'] = "K_Harmonize_New remains 0.0; Primary_Harmonize_Calc = False; Harmonizing_Failed = False."
            elif tc_id == 'LRUSWRS-1001-STEP-20-INVALID-PROFILE-AILERON-1':
                tc['expected_result'] = "K_Harmonize_New remains 0.0; Primary_Harmonize_Calc = False; Harmonizing_Failed = False."
            elif tc_id == 'LRUSWRS-1001-STEP-21-03':
                tc['expected_result'] = "K_Harmonize_New remains 0.0; Primary_Harmonize_Calc = False; Harmonizing_Failed = False."

with open('app/backend/knowledge_suite.json', 'w', encoding='utf-8') as f:
    json.dump(suite, f, indent=2)

print("Updated remaining 6 cases in knowledge_suite.json.")
