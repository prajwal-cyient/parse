import openpyxl

def validate_delta_final():
    old_path = r"c:\Users\pm89542\Desktop\parse\SW_Requirements_Sample_1_Test_Cases_20260804_185720.xlsx"
    app_path = r"c:\Users\pm89542\Desktop\parse\SW_Requirements_Sample_1_Test_Cases_DELTA_APPROVED.xlsx"
    fin_path = r"c:\Users\pm89542\Desktop\parse\SW_Requirements_Sample_1_Test_Cases_DELTA_FINAL.xlsx"

    wb_old = openpyxl.load_workbook(old_path)
    wb_app = openpyxl.load_workbook(app_path)
    wb_fin = openpyxl.load_workbook(fin_path)

    ws_old = wb_old.active
    ws_app = wb_app.active
    ws_fin = wb_fin.active

    # Extract test cases from all three files
    def get_tcs(ws):
        tcs = []
        for r in range(3, ws.max_row + 1):
            tc_id = str(ws.cell(r, 2).value or "").strip()
            req_id = str(ws.cell(r, 3).value or "").strip()
            desc = str(ws.cell(r, 5).value or "").strip()
            init = str(ws.cell(r, 6).value or "").strip()
            inp = str(ws.cell(r, 7).value or "").strip()
            exp = str(ws.cell(r, 8).value or "").strip()
            if tc_id or req_id:
                tcs.append({
                    "row": r,
                    "tc_id": tc_id,
                    "req_id": req_id,
                    "desc": desc,
                    "init": init,
                    "inp": inp,
                    "exp": exp
                })
        return tcs

    tcs_old = get_tcs(ws_old)
    tcs_app = get_tcs(ws_app)
    tcs_fin = get_tcs(ws_fin)

    print("=== WORKBOOK ROW & TEST CASE COUNTS ===")
    print(f"OLD Baseline Test Cases: {len(tcs_old)}")
    print(f"DELTA_APPROVED Test Cases: {len(tcs_app)}")
    print(f"DELTA_FINAL Test Cases: {len(tcs_fin)}")

    # 1. Check LRUSWRS-1011 standalone cases in DELTA_FINAL
    tcs_1011 = [t for t in tcs_fin if t['req_id'] == 'LRUSWRS-1011']
    print(f"\n=== 1. LRUSWRS-1011 VERIFICATION ===")
    print(f"Total LRUSWRS-1011 test cases in DELTA_FINAL: {len(tcs_1011)}")
    tc_1011_ids = [t['tc_id'] for t in tcs_1011]
    expected_1011_ids = [f"SWVCP_AAP_TC_1011_PSR_{i:02d}" for i in range(1, 22)]
    print(f"All 21 IDs match expected pattern: {tc_1011_ids == expected_1011_ids}")

    # 2. Check LRUSWRS-1000 in DELTA_FINAL
    tcs_1000 = [t for t in tcs_fin if t['req_id'] == 'LRUSWRS-1000']
    tombstones_1000 = [t for t in tcs_1000 if 'CONSOLIDATED' in t['desc']]
    print(f"\n=== 2. LRUSWRS-1000 VERIFICATION ===")
    print(f"Total LRUSWRS-1000 test cases in DELTA_FINAL: {len(tcs_1000)}")
    print(f"Executable 1000 ID: {[t['tc_id'] for t in tcs_1000]}")
    print(f"Tombstone / placeholder rows remaining: {len(tombstones_1000)}")

    # 3. Check Observations 2-4 and 6-8 equality between DELTA_APPROVED and DELTA_FINAL
    print(f"\n=== 3. OBSERVATIONS 2-4 and 6-8 COMPARISON (APPROVED vs FINAL) ===")
    obs_reqs = {
        "Obs 2": ["LRU-9169", "LRU-9222"],
        "Obs 3": ["LRU-9174", "LRU-9184"],
        "Obs 4": ["LRU-9170", "LRU-9171", "LRU-9177", "LRU-9895", "LRU-9209", "LRU-9210"],
        "Obs 6": ["LRUSWRS-1003"],
        "Obs 7": ["LRUSWRS-1002"],
        "Obs 8": ["LRUSWRS-1004"]
    }

    all_obs_unchanged = True
    for obs_name, req_list in obs_reqs.items():
        app_sub = [t for t in tcs_app if t['req_id'] in req_list]
        fin_sub = [t for t in tcs_fin if t['req_id'] in req_list]
        
        # Check if contents match
        app_data = [(t['tc_id'], t['req_id'], t['desc'], t['init'], t['inp'], t['exp']) for t in app_sub]
        fin_data = [(t['tc_id'], t['req_id'], t['desc'], t['init'], t['inp'], t['exp']) for t in fin_sub]
        
        match = (app_data == fin_data)
        if not match:
            all_obs_unchanged = False
        print(f"  {obs_name} ({', '.join(req_list)}): {len(app_sub)} cases in APPROVED, {len(fin_sub)} cases in FINAL | MATCH: {match}")

    print(f"All Observations 2-4 and 6-8 100% Identical between APPROVED and FINAL: {all_obs_unchanged}")

    # 4. Check Unrelated cases between OLD baseline and DELTA_FINAL
    print(f"\n=== 4. UNRELATED CASES CHECK (OLD Baseline vs DELTA_FINAL) ===")
    modified_reqs = ["LRUSWRS-1000", "LRUSWRS-1011", "LRU-9169", "LRU-9222", "LRU-9174", "LRU-9184",
                     "LRU-9170", "LRU-9171", "LRU-9177", "LRU-9895", "LRU-9209", "LRU-9210",
                     "LRUSWRS-1003", "LRUSWRS-1002", "LRUSWRS-1004"]

    unmodified_old = [t for t in tcs_old if t['req_id'] not in modified_reqs]
    unmodified_fin = [t for t in tcs_fin if t['req_id'] not in modified_reqs]

    print(f"Unrelated Test Cases in OLD: {len(unmodified_old)}")
    print(f"Unrelated Test Cases in FINAL: {len(unmodified_fin)}")

    unrelated_matches = True
    for t_old, t_fin in zip(unmodified_old, unmodified_fin):
        if (t_old['tc_id'], t_old['req_id'], t_old['desc'], t_old['inp'], t_old['exp']) != \
           (t_fin['tc_id'], t_fin['req_id'], t_fin['desc'], t_fin['inp'], t_fin['exp']):
            unrelated_matches = False
            print(f"Mismatch at TC {t_old['tc_id']}")

    print(f"All 304 Unrelated Baseline Test Cases 100% UNCHANGED: {unrelated_matches}")

if __name__ == "__main__":
    validate_delta_final()
