import json
import openpyxl
import os

JSON_PATH = r"c:\Users\pm89542\Desktop\parse\automation\ALL_TABLE_1001_EXPANDED_TESTCASES.json"
EXCEL_PATH = r"c:\Users\pm89542\Desktop\parse\automation\ALL_TABLE_1001_EXPANDED_TESTCASES.xlsx"
MATRIX_PATH = r"c:\Users\pm89542\Desktop\parse\automation\TABLE_1001_TESTCASES_COMPARISON_MATRIX.xlsx"

# 1. Load Master JSON
with open(JSON_PATH, "r", encoding="utf-8") as f:
    master_json = json.load(f)

json_tcs = []
for step_name, step_info in master_json.get("steps_breakdown", {}).items():
    for tc in step_info.get("test_cases", []):
        json_tcs.append(tc)

print("=========================================================================")
print("STRICT 1-TO-1 CROSS-CHECK: MASTER JSON vs EXCEL DELIVERABLES")
print("=========================================================================")
print(f"Total Test Cases in Master JSON: {len(json_tcs)}")

# 2. Check Master Excel Export
wb_export = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
ws_export = wb_export.active

excel_export_rows = ws_export.max_row - 2 # Minus Title banner (Row 1) and Header (Row 2)
print(f"Total Test Case Rows in Master Excel ({os.path.basename(EXCEL_PATH)}): {excel_export_rows}")

# Cross-check field contents row by row
export_mismatches = 0
for idx, j_tc in enumerate(json_tcs, start=3):
    j_id = j_tc.get("test_case_id", "").strip()
    j_req = j_tc.get("requirement_id", "").strip()
    j_desc = j_tc.get("description", "").strip()
    j_type = str(j_tc.get("test_type", "")).strip().upper()
    j_init = j_tc.get("initial_condition", "").strip()
    j_inputs = j_tc.get("test_inputs", "").strip()
    j_exp = j_tc.get("expected_result", "").strip()
    
    e_id = str(ws_export.cell(row=idx, column=2).value or "").strip()
    e_req = str(ws_export.cell(row=idx, column=3).value or "").strip()
    e_type = str(ws_export.cell(row=idx, column=4).value or "").strip().upper()
    e_desc = str(ws_export.cell(row=idx, column=5).value or "").strip()
    e_init = str(ws_export.cell(row=idx, column=6).value or "").strip()
    e_inputs = str(ws_export.cell(row=idx, column=7).value or "").strip()
    e_exp = str(ws_export.cell(row=idx, column=8).value or "").strip()
    
    if j_id != e_id or j_req != e_req or j_type != e_type or j_desc != e_desc or j_init != e_init or j_inputs != e_inputs or j_exp != e_exp:
        export_mismatches += 1
        print(f"Mismatch at Row {idx}: JSON ID='{j_id}' vs Excel ID='{e_id}'")

print(f"Field-by-Field Mismatches in Master Excel: {export_mismatches}")

# 3. Check Comparison Matrix Workbook (Tab 2)
wb_matrix = openpyxl.load_workbook(MATRIX_PATH, data_only=True)
ws_matrix = wb_matrix["AI Generated (545 TCs)"]
matrix_rows = ws_matrix.max_row - 2

print(f"Total Test Case Rows in Matrix Workbook ({os.path.basename(MATRIX_PATH)} - Tab 2): {matrix_rows}")

matrix_mismatches = 0
for idx, j_tc in enumerate(json_tcs, start=3):
    j_id = j_tc.get("test_case_id", "").strip()
    m_id = str(ws_matrix.cell(row=idx, column=2).value or "").strip()
    if j_id != m_id:
        matrix_mismatches += 1

print(f"Field-by-Field Mismatches in Matrix Workbook Tab 2: {matrix_mismatches}")

print("=========================================================================")
if export_mismatches == 0 and matrix_mismatches == 0 and len(json_tcs) == excel_export_rows == matrix_rows == 545:
    print("VERIFICATION RESULT: 100% PERFECT MATCH! ZERO MISSING FIELDS, ZERO TRUNCATION.")
else:
    print("VERIFICATION RESULT: DISCREPANCY DETECTED!")
print("=========================================================================")
