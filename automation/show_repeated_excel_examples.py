import openpyxl
import os

p1 = r"c:\Users\pm89542\Downloads\test_parker\Test_Cases_For_Sample_1_Part_1.xlsx"
wb = openpyxl.load_workbook(p1, data_only=True)
sheet = wb["Test Cases"]

print("========================================================================")
print("EXACT EXAMPLES OF REPEATED ROWS IN HUMAN MANUAL EXCEL")
print("========================================================================\n")

step1_rows = []
step6_rows = []
step35_rows = []

for r in range(2, sheet.max_row + 1):
    tc_id = sheet.cell(row=r, column=1).value
    obj = sheet.cell(row=r, column=2).value
    req = sheet.cell(row=r, column=3).value
    ttype = sheet.cell(row=r, column=4).value
    init_cond = sheet.cell(row=r, column=5).value
    inputs = sheet.cell(row=r, column=6).value
    expected = sheet.cell(row=r, column=7).value
    
    text = (str(obj) + " " + str(req) + " " + str(tc_id)).upper()
    if "STEP 1" in text or "LRU-6135" in text or "50 FRAMES" in text:
        step1_rows.append((tc_id, obj, inputs, expected))
    elif "STEP 6" in text or "LRU-9184" in text:
        step6_rows.append((tc_id, obj, inputs, expected))
    elif "STEP 35" in text or "LRU-9239" in text:
        step35_rows.append((tc_id, obj, inputs, expected))

print(f"Total Repeated Rows Found for Step 1 in Excel: {len(step1_rows)} rows!")
print("------------------------------------------------------------------------")
print("Sample of Consecutive Repeated Rows in Excel for Step 1:")
print("------------------------------------------------------------------------")
for idx, (tc_id, obj, inp, exp) in enumerate(step1_rows[:6], 1):
    print(f"Row {idx} [ID: {tc_id}]:")
    print(f"  Objective: {str(obj).strip()}")
    print(f"  Inputs   : {str(inp).strip()}")
    print(f"  Expected : {str(exp).strip()}\n")

print("========================================================================")
print(f"Total Repeated Rows Found for Step 6 in Excel: {len(step6_rows)} rows!")
print("------------------------------------------------------------------------")
print("Sample of Consecutive Repeated Rows in Excel for Step 6:")
print("------------------------------------------------------------------------")
for idx, (tc_id, obj, inp, exp) in enumerate(step6_rows[:6], 1):
    print(f"Row {idx} [ID: {tc_id}]:")
    print(f"  Objective: {str(obj).strip()}")
    print(f"  Inputs   : {str(inp).strip()}")
    print(f"  Expected : {str(exp).strip()}\n")
