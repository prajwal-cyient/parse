import json

with open('app/backend/knowledge_suite.json', 'r', encoding='utf-8') as f:
    suite = json.load(f)

for req_id, tcs in suite.items():
    if not isinstance(tcs, list):
        continue
    for tc in tcs:
        tc_id = tc.get('test_case_id', '')
        if tc_id == 'LRUSWRS-1001-STEP-INFORMATIONONLY-03':
            tc['expected_result'] = "Harmonizing_Active_STL = False; IVT_Command_ISM remains 0x0000; IVT_CmdData_ISM remains 0x0000; no new frames transmitted."
        elif tc_id == 'LRUSWRS-1001-STEP-11_TC2':
            tc['expected_result'] = "Act_Disp_Raw_Avg remains 0.0; Expand_Stop_Collection_Complete = False; Harmonizing_Active_STL = False."
        elif tc_id == 'LRUSWRS-1001-STEP-18-02':
            tc['expected_result'] = "Error: Division by zero handled; K_Harmonize_New remains 0.0; VOID_Collection_Complete = False; Harmonizing_Failed = True."
        elif tc_id == 'TC_LRUSWRS-1001-22-05':
            tc['expected_result'] = "Harmonize_Offset_New = 1500150.0; Harmonizing_Offset_Calculation_Complete = True."
        elif tc_id == 'TC_LRUSWRS-1001-22-06':
            tc['expected_result'] = "Harmonize_Offset_New = -1499850.0; Harmonizing_Offset_Calculation_Complete = True."
        elif tc_id == 'TC_LRUSWRS-1001-22-07':
            tc['expected_result'] = "Harmonize_Offset_New = 0.0; Harmonizing_Offset_Calculation_Complete = True."
        elif tc_id == 'TC_LRUSWRS-1001-22-08':
            tc['expected_result'] = "Harmonize_Offset_New = 800.0; Harmonizing_Offset_Calculation_Complete = True."

with open('app/backend/knowledge_suite.json', 'w', encoding='utf-8') as f:
    json.dump(suite, f, indent=2)

print("Updated 7 cases in knowledge_suite.json.")
