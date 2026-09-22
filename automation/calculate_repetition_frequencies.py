import openpyxl
import os
import re

p1 = r"c:\Users\pm89542\Downloads\test_parker\Test_Cases_For_Sample_1_Part_1.xlsx"
p2 = r"c:\Users\pm89542\Downloads\test_parker\Test_Cases_For_Sample_1_Part_2.xlsx"

rows = []
for p in [p1, p2]:
    if os.path.exists(p):
        wb = openpyxl.load_workbook(p, data_only=True)
        sheet = wb['Test Cases'] if 'Test Cases' in wb.sheetnames else wb.active
        for r in range(2, sheet.max_row + 1):
            obj = str(sheet.cell(row=r, column=2).value or sheet.cell(row=r, column=5).value or '').strip()
            req = str(sheet.cell(row=r, column=3).value or '').strip()
            tc_id = str(sheet.cell(row=r, column=1).value or '').strip()
            if '1001' in (req+obj+tc_id).upper() or 'STEP ' in (req+obj+tc_id).upper() or 'LRU-' in (req+obj+tc_id).upper():
                rows.append((tc_id, req, obj))

counts = {}
for tc_id, req, obj in rows:
    c_obj = re.sub(r'\b(LRU_\d+|Atype-\d+|0\.\d+|10\.\d+|True|False)\b', '', obj, flags=re.IGNORECASE)
    c_obj = re.sub(r'\s+', ' ', c_obj).strip()
    counts.setdefault(c_obj, []).append((tc_id, req, obj))

freq_buckets = {"2 times": 0, "3 to 5 times": 0, "6 to 10 times": 0, "11 to 30 times": 0, "31 to 101 times!": 0}
total_repeated_scenarios = 0

print("=========================================================================")
print("HOW MANY TIMES WERE THE EXACT SAME TEST OBJECTIVES REPEATED BY HUMANS?")
print("=========================================================================\n")

sorted_patterns = sorted(counts.items(), key=lambda x: len(x[1]), reverse=True)

print("Top Most Extreme Copy-Pasted Test Case Scenarios:")
print("-" * 85)
for idx, (pattern, instances) in enumerate(sorted_patterns[:8], 1):
    cnt = len(instances)
    sample_id = instances[0][0]
    sample_obj = instances[0][2][:85]
    print(f"{idx}. REPEATED {cnt} TIMES IN EXCEL SHEET! (Ref ID: {sample_id})")
    print(f"   Text: \"{sample_obj}...\"\n")

for pattern, instances in counts.items():
    cnt = len(instances)
    if cnt > 1:
        total_repeated_scenarios += 1
        if cnt == 2: freq_buckets["2 times"] += 1
        elif 3 <= cnt <= 5: freq_buckets["3 to 5 times"] += 1
        elif 6 <= cnt <= 10: freq_buckets["6 to 10 times"] += 1
        elif 11 <= cnt <= 30: freq_buckets["11 to 30 times"] += 1
        else: freq_buckets["31 to 101 times!"] += 1

print("=========================================================================")
print("REPETITION FREQUENCY BREAKDOWN:")
print("=========================================================================")
for bucket, b_cnt in freq_buckets.items():
    print(f" * Scenarios Repeated {bucket:<20}: {b_cnt} different test objectives")

print(f"\nTotal Distinct Test Objectives Repeated More Than Once: {total_repeated_scenarios}")
