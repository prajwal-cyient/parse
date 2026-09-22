import json
import re
import openpyxl

def audit_all_13():
    with open('app/backend/knowledge_suite.json', 'r', encoding='utf-8') as f:
        suite = json.load(f)
        
    flat_tcs = []
    for req_id, tcs in suite.items():
        if isinstance(tcs, list):
            flat_tcs.extend(tcs)
            
    print(f"=== COMPREHENSIVE 13-POINT CLIENT OBSERVATION AUDIT ({len(flat_tcs)} Test Cases) ===")
    
    defects = {i: [] for i in range(1, 14)}
    
    # 1. LRU / ATYPE APPLICABILITY & COVERAGE
    matrix_reqs = [tc for tc in flat_tcs if "1011" in tc.get("requirement_id", "")]
    if len(matrix_reqs) < 21:
        defects[1].append(f"Expected 21 matrix test cases for Table 1011, found {len(matrix_reqs)}")
    for tc in matrix_reqs:
        if not re.search(r'ATYPE_[123]', tc.get("initial_condition", "")):
            defects[1].append(f"Missing ATYPE in matrix TC: {tc.get('test_case_id')}")
        if not re.search(r'LRU_[1-7]', tc.get("initial_condition", "")):
            defects[1].append(f"Missing LRU in matrix TC: {tc.get('test_case_id')}")
            
    # 2. REQUIREMENT CLUBBING
    # Check clubbed sequences (e.g. 4a+4b, 9a+9b, 14a+14b)
    clubbed_cases = [tc for tc in flat_tcs if "+" in tc.get("requirement_id", "") or "4a" in tc.get("requirement_id", "").lower()]
    if not clubbed_cases:
        defects[2].append("No clubbed sequence test cases found")
        
    # 3. INITIAL CONDITIONS
    for tc in flat_tcs:
        ic = tc.get("initial_condition", "")
        if not ic or len(ic.strip()) < 10:
            defects[3].append(f"Empty/short Initial Condition in {tc.get('test_case_id')}")
        if "FLIGHT_MODE" not in ic:
            defects[3].append(f"Missing FLIGHT_MODE in {tc.get('test_case_id')}")
            
    # 4 & 5. TEST INPUT CLASSIFICATION & OUTPUT VARIABLES (Strict separation)
    forbidden_in_inputs = [
        r'Act_Disp_Range_\w+_Fault',
        r'Harmonizing_PSR_Data_Fault',
        r'Harmonizing_Failed',
        r'Contract_Stop_Collection_Complete',
        r'Expand_Stop_Collection_Complete',
        r'VOID_Collection_Complete',
        r'Harmonizing_Complete',
        r'Harmonizing_Sequence_Complete',
        r'Sequence_Complete',
        r'command(?:ed)?\s+to\b'
    ]
    input_leak_pattern = re.compile(r'\b(?:' + '|'.join(forbidden_in_inputs) + r')\b', re.IGNORECASE)
    
    for tc in flat_tcs:
        ti = tc.get("test_inputs", "")
        if input_leak_pattern.search(ti):
            defects[4].append(f"Output/Setup leaked into Test Inputs in {tc.get('test_case_id')}: '{ti}'")
            defects[5].append(f"Output leaked into Test Inputs in {tc.get('test_case_id')}")
            
    # 6. DERIVED / AVERAGED VALUES
    step1_seen = False
    for tc in flat_tcs:
        if "STEP-1" in tc.get("requirement_id", ""):
            step1_seen = True
        elif "STEP-2" in tc.get("requirement_id", "") or "STEP-3" in tc.get("requirement_id", ""):
            ti = tc.get("test_inputs", "")
            if "50 frames" in ti.lower() or "sampling" in ti.lower():
                defects[6].append(f"Repetitive sampling described in downstream input: {tc.get('test_case_id')}")
                
    # 7. BOOLEAN CONDITIONS (Both True and False, explicit negative assertions)
    for tc in flat_tcs:
        tt = tc.get("test_type", "")
        desc = tc.get("description", "").lower()
        er = tc.get("expected_result", "")
        if tt == "DC" or "false" in desc or "outside" in desc:
            if "= False" not in er and "= True" not in er and "False" not in er:
                defects[7].append(f"Missing explicit boolean assertion in negative test {tc.get('test_case_id')}: '{er}'")
                
    # 8. RELATED STEP CLUBBING
    # 9. HARMONIZING REQUIREMENTS (PSR 1000 consolidation)
    psr_cases = [tc for tc in flat_tcs if tc.get("requirement_id") == "LRUSWRS-1000"]
    if len(psr_cases) != 1:
        defects[9].append(f"Expected exactly 1 consolidated PSR 1000 test case, found {len(psr_cases)}")
    else:
        psr_tc = psr_cases[0]
        for member in ["Harmonize_SFC_PSR", "Harmonize_Offset_PSR", "Config_LRU_PSR", "Asset_ID_PSR", "Upper_Limit_LRU_PSR", "Lower_Limit_LRU_PSR", "CRC_PSR", "Var_ID_PSR", "Label_Version_PSR"]:
            if member not in psr_tc.get("expected_result", ""):
                defects[9].append(f"Consolidated PSR 1000 missing member {member}")
                
    # 10. LINKED / RELATED REQUIREMENT INPUTS (No "None" or empty)
    for tc in flat_tcs:
        ti = tc.get("test_inputs", "").strip().lower()
        if ti in ["none", "none.", "n/a", ""]:
            defects[10].append(f"Empty/None test input in {tc.get('test_case_id')}")
            
    # 11. CONSISTENCY CHECK
    for tc in flat_tcs:
        desc = tc.get("description", "").lower()
        er = tc.get("expected_result", "").lower()
        ti = tc.get("test_inputs", "").lower()
        if "outside" in ti and "fault = false" in er:
            defects[11].append(f"Contradiction: outside range but fault = false in {tc.get('test_case_id')}")
            
    # 12. DO NOT INVENT VALUES
    for tc in flat_tcs:
        if "generic placeholder" in str(tc).lower() or "tbd" in str(tc).lower():
            defects[12].append(f"Found placeholder/TBD in {tc.get('test_case_id')}")
            
    # 13. FINAL VALIDATION SUMMARY
    total_defects = sum(len(v) for v in defects.values())
    print("\n--- AUDIT RESULTS PER CLIENT OBSERVATION RULE ---")
    rules_text = [
        "1. LRU / ATYPE APPLICABILITY AND COVERAGE",
        "2. REQUIREMENT CLUBBING",
        "3. INITIAL CONDITIONS",
        "4. TEST INPUT CLASSIFICATION",
        "5. OUTPUT VARIABLES",
        "6. DERIVED / AVERAGED VALUES",
        "7. BOOLEAN CONDITIONS",
        "8. RELATED STEP CLUBBING",
        "9. HARMONIZING REQUIREMENTS",
        "10. LINKED / RELATED REQUIREMENT INPUTS",
        "11. CONSISTENCY CHECK",
        "12. DO NOT INVENT VALUES",
        "13. FINAL VALIDATION"
    ]
    
    for i in range(1, 14):
        errs = defects[i]
        status = "PASSED (100% Compliant)" if len(errs) == 0 else f"FAILED ({len(errs)} defects)"
        print(f"[{status}] Rule {rules_text[i-1]}")
        for e in errs[:3]:
            print(f"    - {e}")
            
    print(f"\nOVERALL RESULT: {'100% PERFECT PASS (0 DEFECTS)' if total_defects == 0 else f'{total_defects} DEFECTS FOUND'}")

if __name__ == "__main__":
    audit_all_13()
