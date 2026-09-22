import json
import re

def fix_suite():
    ks_path = 'app/backend/knowledge_suite.json'
    with open(ks_path, 'r', encoding='utf-8') as f:
        suite = json.load(f)
        
    for req_id, tcs in suite.items():
        if not isinstance(tcs, list):
            continue
        for tc in tcs:
            tc_id = tc.get('test_case_id', '')
            desc = tc.get('description', '')
            tt = tc.get('test_type', 'NORMAL')
            ic = tc.get('initial_condition', '')
            ti = tc.get('test_inputs', '')
            er = tc.get('expected_result', '')
            pc = tc.get('pass_criteria', '')
            
            # 1. Clean weird artifact 'Harmonize_Contract_Stop_STL (pre-averaged single value) = 10.0 (in)'
            ti = re.sub(r'Harmonize_Contract_Stop_STL\s*\(pre-averaged single value\)\s*=\s*10\.0\s*\(in\)', 'Harmonize_Contract_Stop_STL = True', ti)
            ti = re.sub(r'Harmonize_Expand_Stop_STL\s*\(pre-averaged single value\)\s*=\s*10\.0\s*\(in\)', 'Harmonize_Expand_Stop_STL = True', ti)
            ti = re.sub(r'Harmonize_VOID_Stop_STL\s*\(pre-averaged single value\)\s*=\s*10\.0\s*\(in\)', 'Harmonize_VOID_Stop_STL = True', ti)
            ti = re.sub(r'\(in\)', 'in', ti)
            
            # Clean weird signal values like 'Harmonizing_and_Configuration_Parameters_Request = 10.0 (in)'
            ti = re.sub(r'Harmonizing_and_Configuration_Parameters_Request\s*=\s*10\.0(?:\s*in)?', 'Harmonizing_and_Configuration_Parameters_Request = 0x0001', ti)
            ti = re.sub(r'STL_Bus\s*=\s*10\.0(?:\s*in)?', 'STL_Bus = ACTIVE', ti)
            ti = re.sub(r'LRU_Harmonizing_Needed_PIVT\s*=\s*10\.0(?:\s*in)?', 'LRU_Harmonizing_Needed_PIVT = True', ti)
            
            # Clean ER artifacts
            er = re.sub(r'Contract_Stop_Collection_Complete\s*=\s*10\.0(?:\s*in)?', 'Contract_Stop_Collection_Complete = False', er)
            er = re.sub(r'Expand_Stop_Collection_Complete\s*=\s*10\.0(?:\s*in)?', 'Expand_Stop_Collection_Complete = False', er)
            er = re.sub(r'VOID_Collection_Complete\s*=\s*10\.0(?:\s*in)?', 'VOID_Collection_Complete = False', er)
            er = re.sub(r'LRU_Harmonizing_Needed_PIVT\s*=\s*10\.0(?:\s*in)?', 'LRU_Harmonizing_Needed_PIVT = True', er)
            er = re.sub(r'Harmonizing_Complete\s*=\s*10\.0(?:\s*in)?', 'Harmonizing_Complete = True', er)
            er = re.sub(r'LRU_Harmonizing_Needed_PIVT\s*=\s*False operational value \.', 'LRU_Harmonizing_Needed_PIVT = False.', er)
            er = re.sub(r'IVT Response transmitted on STL_Bus with IVT_Receipt_Envelope = False, IVT_Receipt_Content = False:', 'IVT Response transmitted on STL_Bus with IVT_Receipt_Envelope = 0x0017, IVT_Receipt_Content:', er)
            
            # 2. Enforce explicit boolean assertions in all negative / DC / boundary / robustness cases
            is_negative = tt in ("DC", "ROBUSTNESS") or any(k in desc.lower() for k in ["false", "outside", "not equal", "not performed", "fails", "corrupt", "exceeds", "invalid"])
            
            if is_negative:
                # STEP 1
                if "STEP-1" in req_id:
                    if "Harmonizing_Active_STL = False" not in er:
                        er = "Output_Avg_Act_Disp_Raw remains 0; Harmonizing_Active_STL = False; Contract_Stop_Collection_Complete = False."
                # STEP 2
                elif "STEP-2" in req_id:
                    if "Contract_Stop_Collection_Complete = False" not in er and ("false" in desc.lower() or "0" in desc.lower() or "boundary" in desc.lower() or "robustness" in desc.lower()):
                        er = re.sub(r'Act_Disp_Raw_Avg_Contract\s*=\s*0;?', 'Act_Disp_Raw_Avg_Contract = 0.0; Contract_Stop_Collection_Complete = False', er)
                        if "Contract_Stop_Collection_Complete" not in er:
                            er += "; Contract_Stop_Collection_Complete = False"
                # STEP 5 & 10 & 15 & 16
                elif "STEP-5" in req_id:
                    if "outside" in desc.lower() or "true" in desc.lower() or "fault" in desc.lower() or "exceeds" in desc.lower():
                        er = "Act_Disp_Range_Contract_Fault = True; Harmonizing_Failed = False; Contract_Stop_Collection_Complete = False; IVT Response transmitted on STL_Bus with IVT_Receipt_Envelope = 0x0017, IVT_Receipt_Content: Harmonizing_Failed = False, Contract_Stop_Collection_Complete = False."
                elif "STEP-10" in req_id:
                    if "outside" in desc.lower() or "false" in desc.lower() or "fault" in desc.lower():
                        er = "Act_Disp_Range_Expand_Fault = True; Harmonizing_Failed = False; Expand_Stop_Collection_Complete = False; IVT Response transmitted on STL_Bus with IVT_Receipt_Envelope = 0x0017, IVT_Receipt_Content: Harmonizing_Failed = False, Expand_Stop_Collection_Complete = False."
                elif "STEP-12" in req_id:
                    if "Expand_Stop_Collection_Complete = False" not in er and ("false" in desc.lower() or "robustness" in desc.lower() or "dc" in desc.lower()):
                        if "Expand_Stop_Collection_Complete" not in er:
                            er += "; Expand_Stop_Collection_Complete = False"
                elif "STEP-15" in req_id:
                    if "outside" in desc.lower() or "false" in desc.lower() or "fault" in desc.lower():
                        er = "Act_Disp_Range_VOID_Fault = True; Harmonizing_Failed = False; VOID_Collection_Complete = False; IVT Response transmitted on STL_Bus with IVT_Receipt_Envelope = 0x0017, IVT_Receipt_Content: Harmonizing_Failed = False, VOID_Collection_Complete = False."
                elif "STEP-16" in req_id:
                    if "outside" in desc.lower() or "false" in desc.lower() or "fault" in desc.lower():
                        er = "Act_Disp_Range_VOID_Fault = True; Harmonizing_Failed = False; VOID_Collection_Complete = False; IVT Response transmitted on STL_Bus with IVT_Receipt_Envelope = 0x0017, IVT_Receipt_Content: Harmonizing_Failed = False, VOID_Collection_Complete = False."
                elif "STEP-17" in req_id or "STEP-18" in req_id or "STEP-19" in req_id:
                    if "VOID_Collection_Complete = False" not in er and ("false" in desc.lower() or "robustness" in desc.lower() or "dc" in desc.lower()):
                        er += "; VOID_Collection_Complete = False"
                elif "STEP-32" in req_id or "STEP-33" in req_id or "STEP-34" in req_id or "STEP-35" in req_id:
                    if "outside" in desc.lower() or "fault" in desc.lower():
                        er = "Act_Disp_Range_Contract_Fault = True; Harmonizing_Failed = False; Contract_Stop_Collection_Complete = False; IVT Response transmitted on STL_Bus with IVT_Receipt_Envelope = 0x0017, IVT_Receipt_Content: Harmonizing_Failed = False, Contract_Stop_Collection_Complete = False."
                        
            # Clean double periods and clean formatting
            er = re.sub(r'\s*\.\s*\.', '.', er)
            ti = re.sub(r'\s*\.\s*\.', '.', ti)
            ic = re.sub(r'\s*\.\s*\.', '.', ic)
            if not er.endswith('.'):
                er += '.'
            if not ti.endswith('.'):
                ti += '.'
            if not ic.endswith('.'):
                ic += '.'
                
            tc['test_inputs'] = ti
            tc['expected_result'] = er
            tc['initial_condition'] = ic
            
    with open(ks_path, 'w', encoding='utf-8') as f:
        json.dump(suite, f, indent=2)
    print("Updated knowledge_suite.json successfully.")

if __name__ == "__main__":
    fix_suite()
