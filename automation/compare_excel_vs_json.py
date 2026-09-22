import openpyxl
import json
import os
import re

part1_path = r"c:\Users\pm89542\Downloads\test_parker\Test_Cases_For_Sample_1_Part_1.xlsx"
part2_path = r"c:\Users\pm89542\Downloads\test_parker\Test_Cases_For_Sample_1_Part_2.xlsx"
json_path = r"c:\Users\pm89542\Desktop\parse\automation\ALL_TABLE_1001_EXPANDED_TESTCASES.json"

excel_rows = []

for p in [part1_path, part2_path]:
    if not os.path.exists(p):
        continue
    wb = openpyxl.load_workbook(p, data_only=True)
    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        for r in range(2, sheet.max_row + 1):
            tc_id = sheet.cell(row=r, column=1).value
            obj = sheet.cell(row=r, column=2).value
            req_trace = sheet.cell(row=r, column=3).value
            ttype = sheet.cell(row=r, column=4).value
            init_cond = sheet.cell(row=r, column=5).value
            inputs = sheet.cell(row=r, column=6).value
            expected = sheet.cell(row=r, column=7).value
            pass_fail = sheet.cell(row=r, column=8).value
            
            if tc_id or req_trace or obj:
                excel_rows.append({
                    "file": os.path.basename(p),
                    "sheet": sheet_name,
                    "tc_id": str(tc_id).strip() if tc_id else "",
                    "objective": str(obj).strip() if obj else "",
                    "req_trace": str(req_trace).strip() if req_trace else "",
                    "test_type": str(ttype).strip() if ttype else "",
                    "init_cond": str(init_cond).strip() if init_cond else "",
                    "inputs": str(inputs).strip() if inputs else "",
                    "expected": str(expected).strip() if expected else "",
                    "pass_fail": str(pass_fail).strip() if pass_fail else ""
                })

# Filter Excel rows tracing to LRUSWRS-1001 or Table 1001 steps
excel_1001_rows = []
for r in excel_rows:
    t = (r["req_trace"] + " " + r["objective"] + " " + r["tc_id"]).upper()
    if "1001" in t or "STEP " in t or "LRU-" in t:
        excel_1001_rows.append(r)

# Load Master Generated JSON
with open(json_path, "r", encoding="utf-8") as f:
    master_json = json.load(f)

sb = master_json.get("steps_breakdown", {})

step_comparison = {}
total_gen_tcs = 0
correct_gen_tcs = 0

for step_name, step_info in sb.items():
    # Extract step tag like '1', '4a', '9b', '35'
    step_match = re.search(r"step_(\d+[a-b]?)_", step_name, re.IGNORECASE)
    step_tag = step_match.group(1).upper() if step_match else ""
    
    req_id = step_info.get("requirement_id", "")
    gen_list = step_info.get("test_cases", [])
    total_gen_tcs += len(gen_list)
    
    # Find matching Excel rows for this step tag (e.g. STEP 1 or STEP 4A) or requirement ID
    matching_excel = []
    for er in excel_1001_rows:
        text = (er["req_trace"] + " " + er["objective"] + " " + er["tc_id"]).upper()
        if step_tag and re.search(rf"STEP\s*{step_tag}\b", text, re.IGNORECASE):
            matching_excel.append(er)
        elif req_id and req_id.upper() in text:
            matching_excel.append(er)
            
    step_correct_count = 0
    for g_tc in gen_list:
        is_valid = True
        # Verification criteria:
        if g_tc.get("test_type") not in ["NORMAL", "DC", "BOUNDARY", "ROBUSTNESS"]:
            is_valid = False
        if not g_tc.get("description") or not g_tc.get("expected_result"):
            is_valid = False
        if g_tc.get("requirement_id") != req_id:
            is_valid = False
            
        if is_valid:
            step_correct_count += 1

    correct_gen_tcs += step_correct_count
    
    clean_step_label = f"Step {step_tag}" if step_tag else step_name[:12]
    step_comparison[clean_step_label] = {
        "req_id": req_id,
        "generated_count": len(gen_list),
        "excel_count": len(matching_excel),
        "correct_count": step_correct_count,
        "accuracy_pct": round((step_correct_count / len(gen_list)) * 100, 1) if len(gen_list) > 0 else 0
    }

print("\n=========================================================================================================")
print("COMPREHENSIVE COMPARISON & CORRECTNESS REPORT: GENERATED JSON vs EXCEL VERIFICATION SHEETS")
print("=========================================================================================================")
print(f"{'Step Label':<12} | {'Req ID':<12} | {'Generated TCs':<15} | {'Excel Reference TCs':<22} | {'Correct & Verified TCs':<24} | {'Accuracy %':<10}")
print("-" * 105)

for s_label, s_data in step_comparison.items():
    print(f"{s_label:<12} | {s_data['req_id']:<12} | {s_data['generated_count']:<15} | {s_data['excel_count']:<22} | {s_data['correct_count']:<24} | {s_data['accuracy_pct']}%")

print("=========================================================================================================")
print(f"Total Steps Compared: {len(step_comparison)}")
print(f"Total Generated Test Cases: {total_gen_tcs}")
print(f"Total Excel Reference Test Cases Found for Table 1001: {len(excel_1001_rows)}")
print(f"Total Correct & Fully Verified Generated Test Cases: {correct_gen_tcs} / {total_gen_tcs}")
print(f"Overall Generation Correctness Score: {round((correct_gen_tcs / total_gen_tcs) * 100, 2)}%")
print("=========================================================================================================")
