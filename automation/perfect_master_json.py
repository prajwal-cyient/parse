import json
import re

MASTER_FILE = r"c:\Users\pm89542\Desktop\parse\automation\ALL_TABLE_1001_EXPANDED_TESTCASES.json"

with open(MASTER_FILE, "r", encoding="utf-8") as f:
    master_data = json.load(f)

seen_ids = set()
total_tcs = 0
duplicates_fixed = 0
fields_fixed = 0

for step_name, step_info in master_data.get("steps_breakdown", {}).items():
    tcs = step_info.get("test_cases", [])
    req_id = step_info.get("requirement_id", "LRU-SWRS")
    
    for idx, tc in enumerate(tcs, 1):
        total_tcs += 1
        tc_id = tc.get("test_case_id", "").strip()
        
        # 1. Deduplicate test_case_id
        if not tc_id or tc_id in seen_ids:
            new_id = f"{tc_id}_{idx}" if tc_id else f"{req_id}_TC_{idx}"
            if new_id in seen_ids:
                new_id = f"{req_id}_{step_name.upper()}_TC_{idx}"
            tc["test_case_id"] = new_id
            seen_ids.add(new_id)
            duplicates_fixed += 1
        else:
            seen_ids.add(tc_id)
            
        # 2. Fix mandatory fields if empty or missing
        if not tc.get("requirement_id"):
            tc["requirement_id"] = req_id
            fields_fixed += 1
            
        if not tc.get("description"):
            tc["description"] = f"Verify software logic for {req_id} ({tc.get('test_type', 'NORMAL')})."
            fields_fixed += 1
            
        if not tc.get("test_type"):
            tc["test_type"] = "NORMAL"
            fields_fixed += 1
            
        if not tc.get("initial_condition") or tc.get("initial_condition").strip().lower() in ["none", "n/a", ""]:
            tc["initial_condition"] = "LRU operating in Location_State_StateLgc mode."
            fields_fixed += 1
            
        if not tc.get("test_inputs"):
            tc["test_inputs"] = f"Configured parameters according to {req_id} verification setup."
            fields_fixed += 1
            
        if not tc.get("expected_result"):
            tc["expected_result"] = f"Software executes according to {req_id} specification."
            fields_fixed += 1
            
        if not tc.get("pass_criteria"):
            tc["pass_criteria"] = "Observed software behaviour matches expected_result."
            fields_fixed += 1
            
        if tc.get("related_requirements") is None:
            tc["related_requirements"] = ""
            
        if tc.get("test_procedure_notes") is None:
            tc["test_procedure_notes"] = "Verification mechanism to be defined by the verification environment."

master_data["total_test_cases"] = total_tcs

with open(MASTER_FILE, "w", encoding="utf-8") as f:
    json.dump(master_data, f, indent=2, ensure_ascii=False)

print("====================================================")
print("MASTER JSON POST-PROCESSING COMPLETE!")
print(f"Total Steps: {len(master_data.get('steps_breakdown', {}))}")
print(f"Total Expanded Test Cases: {total_tcs}")
print(f"Duplicates Fixed: {duplicates_fixed}")
print(f"Missing Fields Fixed: {fields_fixed}")
print(f"Updated File Saved To: {MASTER_FILE}")
print("====================================================")
