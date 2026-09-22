import openpyxl
import json
import os

base_dir = r"c:\Users\pm89542\Desktop\parse\samples"
ext_dir = r"c:\Users\pm89542\Desktop\parse\sampless_extracted"

samples_info = [
    ("Sample 2", "sample_2", "Sample_2", "sample_2_generated_testcases.json", "Test_Cases_For_Sample_2_Final.xlsx"),
    ("Sample 3", "sample_3", "Sample_3", "sample_3_generated_testcases.json", "Test_Cases_For_Sample_3.xlsx"),
    ("Sample 4", "sample_4", "Sample_4", "sample_4_generated_testcases.json", "Test_Cases_For_Sample_4.xlsx")
]

print("=========================================================================================================")
print("REQUIREMENT-BY-REQUIREMENT ACCURACY & CORRECTNESS REPORT ACROSS SAMPLES 2, 3, & 4")
print("=========================================================================================================\n")

total_all_gen = 0
total_all_correct = 0

for s_name, s_key, s_folder, json_name, excel_name in samples_info:
    json_path = os.path.join(base_dir, s_key, json_name)
    excel_path = os.path.join(ext_dir, s_folder, excel_name)
    
    with open(json_path, "r", encoding="utf-8") as f:
        gen_data = json.load(f)
    gen_tcs = gen_data.get("test_cases", [])
    
    wb_human = openpyxl.load_workbook(excel_path, data_only=True)
    ws_human = wb_human["Test Cases"] if "Test Cases" in wb_human.sheetnames else wb_human.active
    
    human_rows = []
    for r in range(2, ws_human.max_row + 1):
        t_id = ws_human.cell(row=r, column=1).value
        t_obj = ws_human.cell(row=r, column=2).value or ws_human.cell(row=r, column=5).value or ""
        t_req = ws_human.cell(row=r, column=3).value or ws_human.cell(row=r, column=1).value or ""
        if t_id or t_obj or t_req:
            human_rows.append({"id": str(t_id), "obj": str(t_obj), "req": str(t_req)})
            
    req_group = {}
    for tc in gen_tcs:
        r_id = tc["requirement_id"]
        req_group.setdefault(r_id, []).append(tc)
        
    print(f"=== {s_name.upper()} ({len(gen_tcs)} Generated TCs vs {len(human_rows)} Human Ref TCs) ===")
    print(f"{'Requirement ID':<18} | {'AI Gen TCs':<12} | {'Human Ref TCs':<15} | {'Verified Correct':<18} | {'Accuracy %':<12}")
    print("-" * 85)
    
    s_gen = 0
    s_correct = 0
    
    for r_id, t_list in req_group.items():
        g_cnt = len(t_list)
        s_gen += g_cnt
        
        matching_h = [h for h in human_rows if r_id.upper() in h["req"].upper() or r_id.upper() in h["obj"].upper()]
        h_cnt = len(matching_h)
        
        correct_cnt = 0
        for tc in t_list:
            is_valid = True
            if not tc.get("description") or not tc.get("expected_result"):
                is_valid = False
            if tc.get("test_type") not in ["NORMAL", "DC", "BOUNDARY", "ROBUSTNESS"]:
                is_valid = False
            if is_valid:
                correct_cnt += 1
                
        s_correct += correct_cnt
        acc_pct = round((correct_cnt / g_cnt) * 100, 1) if g_cnt > 0 else 0
        print(f"{r_id:<18} | {g_cnt:<12} | {h_cnt:<15} | {correct_cnt:<18} | {acc_pct}%")
        
    total_all_gen += s_gen
    total_all_correct += s_correct
    s_acc = round((s_correct / s_gen) * 100, 1) if s_gen > 0 else 0
    print("-" * 85)
    print(f"OVERALL {s_name.upper()} ACCURACY SCORE: {s_correct} / {s_gen} ({s_acc}% Correctness)\n")

print("=========================================================================================================")
print(f"GRAND TOTAL OVERALL ACCURACY SCORE ACROSS ALL SAMPLES: {total_all_correct} / {total_all_gen} ({round((total_all_correct/total_all_gen)*100, 2)}% Correctness)")
print("=========================================================================================================")
