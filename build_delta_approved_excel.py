import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from copy import copy
import os

def build_delta_excel():
    src_path = r"c:\Users\pm89542\Desktop\parse\SW_Requirements_Sample_1_Test_Cases_20260804_185720.xlsx"
    out_dir = r"c:\Users\pm89542\Desktop\parse\app\outputs"
    os.makedirs(out_dir, exist_ok=True)
    out_path_1 = os.path.join(out_dir, "SW_Requirements_Sample_1_Test_Cases_DELTA_APPROVED.xlsx")
    out_path_2 = r"c:\Users\pm89542\Desktop\parse\SW_Requirements_Sample_1_Test_Cases_DELTA_APPROVED.xlsx"

    wb = openpyxl.load_workbook(src_path)
    ws = wb.active
    ws.title = "Test Cases (Delta Highlighted)"

    yellow_fill = PatternFill(start_color="FFF59D", end_color="FFF59D", fill_type="solid")
    bold_font = Font(name="Calibri", size=10, bold=True, color="000000")
    regular_font = Font(name="Calibri", size=10, color="000000")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")

    thin_border = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB')
    )

    changelog = []

    def set_cell(row, col, new_val, obs_num, field_name, req_id, tc_id, justification):
        cell = ws.cell(row=row, column=col)
        old_val = str(cell.value or "")
        if old_val.strip() != str(new_val).strip():
            changelog.append({
                "obs": obs_num,
                "row": row,
                "tc_id": tc_id,
                "req_id": req_id,
                "field": field_name,
                "old": old_val,
                "new": str(new_val),
                "reason": justification
            })
            cell.value = new_val
            cell.fill = yellow_fill

    # -------------------------------------------------------------
    # 1. Observation 3: Row 19 & Row 21 (LRU-9184 & LRU-9174 false condition)
    # -------------------------------------------------------------
    # Row 19:
    set_cell(19, 8,
             "The averaging operation is NOT performed; Expand_Stop_Collection_Complete = False.",
             "Obs 3", "Expected Result(s)", "LRU-9184", ws.cell(row=19, column=2).value,
             "Assert explicit boolean false output per client observation 3.")

    # Row 21 (LRU_9174_DC_Condition):
    set_cell(21, 8,
             "Act_Disp_Raw_Avg_Expand is NOT performed; Expand_Stop_Collection_Complete = False.",
             "Obs 3", "Expected Result(s)", "LRU-9174", ws.cell(row=21, column=2).value,
             "Assert explicit boolean false output per client observation 3.")

    # -------------------------------------------------------------
    # 2. Observation 4: Club Steps 4A+4B (Rows 10-14) & 9A+9B (Rows 26-30)
    # -------------------------------------------------------------
    # Row 10 (LRU_9171_N1): Step 4A previously showed no inputs
    set_cell(10, 7,
             "Act_Disp_Range_Contract_Fault = False; Transmission_Timer = 20 ms; Surface = Left Aileron.",
             "Obs 4", "Test Inputs", "LRU-9171", ws.cell(row=10, column=2).value,
             "Add operational stimulus to Step 4A and club with Step 3/4B per client observation 4.")
    set_cell(10, 8,
             "Set and transmit IVT Response on STL_Bus: IVT_Receipt_Envelope = 0x0017, IVT_Receipt_Content: Contract_Stop_Collection_Complete = True, Harmonizing_Failed = False.",
             "Obs 4", "Expected Result(s)", "LRU-9171", ws.cell(row=10, column=2).value,
             "Unified transmission output asserting Contract_Stop_Collection_Complete and Harmonizing_Failed.")

    # Row 11:
    set_cell(11, 7,
             "Act_Disp_Range_Contract_Fault = True; Transmission_Timer = 20 ms; Surface = Left Aileron.",
             "Obs 4", "Test Inputs", "LRU-9171", ws.cell(row=11, column=2).value,
             "Fault stimulus for clubbed 4A/4B response.")
    set_cell(11, 8,
             "Set and transmit IVT Response on STL_Bus: IVT_Receipt_Envelope = 0x0017, IVT_Receipt_Content: Harmonizing_Failed = True.",
             "Obs 4", "Expected Result(s)", "LRU-9171", ws.cell(row=11, column=2).value,
             "Assert Harmonizing_Failed = True upon contract range fault.")

    # Row 26 (LRU_9895_N1): Step 9A
    set_cell(26, 7,
             "Act_Disp_Range_Expand_Fault = False; Transmission_Timer = 20 ms; Surface = Left Aileron.",
             "Obs 4", "Test Inputs", "LRU-9895", ws.cell(row=26, column=2).value,
             "Add operational stimulus to Step 9A and club with Step 8/9B per client observation 4.")
    set_cell(26, 8,
             "Set and transmit IVT Response on STL_Bus: IVT_Receipt_Envelope = 0x0017, IVT_Receipt_Content: Expand_Stop_Collection_Complete = True, Harmonizing_Failed = False.",
             "Obs 4", "Expected Result(s)", "LRU-9895", ws.cell(row=26, column=2).value,
             "Unified transmission output asserting Expand_Stop_Collection_Complete and Harmonizing_Failed.")

    # -------------------------------------------------------------
    # 3. Observation 5: LRUSWRS-1000 (Rows 108 to 116)
    # Consolidate 9 PSR members into 1 unified test case
    # -------------------------------------------------------------
    set_cell(108, 2, "SWVCP_AAP_TC_1000_PSR_ALL", "Obs 5", "Test Case ID", "LRUSWRS-1000", "TC-LRUSWRS-1000-01", "Consolidated test case ID.")
    set_cell(108, 5,
             "Verify that all 9 PSR Harmonizing data members (Harmonize_SFC_PSR, Harmonize_Offset_PSR, Config_LRU_PSR, Asset_ID_PSR, Upper_Limit_LRU_PSR, Lower_Limit_LRU_PSR, CRC_PSR, Var_ID_PSR, Software/Firmware Version) reside in PSR when LRU enters Harmonizing mode.",
             "Obs 5", "Test Case Description", "LRUSWRS-1000", "SWVCP_AAP_TC_1000_PSR_ALL", "Unified record verification description.")
    set_cell(108, 6,
             "Operational Mode: FLIGHT_MODE; Target Asset Type: ATYPE_1; Target LRU: LRU_1; LRU entering Harmonizing mode per LRUSWRS-1003.",
             "Obs 5", "Initial Condition(s)", "LRUSWRS-1000", "SWVCP_AAP_TC_1000_PSR_ALL", "Setup state before mode trigger.")
    set_cell(108, 7,
             "IVT_Mode_ModeLgc = True; Harmonizing_Active_STL = True; Read back all 9 PSR data members.",
             "Obs 5", "Test Inputs", "LRUSWRS-1000", "SWVCP_AAP_TC_1000_PSR_ALL", "Specific inputs mandated by client observation 5.")
    set_cell(108, 8,
             "All 9 PSR data members exist in PSR with valid configured values: Harmonize_SFC_PSR, Harmonize_Offset_PSR, Config_LRU_PSR, Asset_ID_PSR, Upper_Limit_LRU_PSR, Lower_Limit_LRU_PSR, CRC_PSR, Var_ID_PSR, and Software/Firmware Version.",
             "Obs 5", "Expected Result(s)", "LRUSWRS-1000", "SWVCP_AAP_TC_1000_PSR_ALL", "Single consolidated verification asserted.")

    for r_psr in range(109, 117):
        set_cell(r_psr, 5,
                 "[CONSOLIDATED INTO ROW 108 (SWVCP_AAP_TC_1000_PSR_ALL) PER CLIENT OBSERVATION 5 - Only one test case is sufficient to cover this requirement]",
                 "Obs 5", "Test Case Description", "LRUSWRS-1000", ws.cell(row=r_psr, column=2).value,
                 "Consolidated into single test case per client observation 5.")
        set_cell(r_psr, 7, "Covered by Row 108 (SWVCP_AAP_TC_1000_PSR_ALL).", "Obs 5", "Test Inputs", "LRUSWRS-1000", ws.cell(row=r_psr, column=2).value, "Consolidated.")
        set_cell(r_psr, 8, "Covered by Row 108 (SWVCP_AAP_TC_1000_PSR_ALL).", "Obs 5", "Expected Result(s)", "LRUSWRS-1000", ws.cell(row=r_psr, column=2).value, "Consolidated.")

    # -------------------------------------------------------------
    # 4. Observation 7: LRUSWRS-1002 (Row 117 / previously row 115)
    # -------------------------------------------------------------
    set_cell(117, 7,
             "IVT_Mode_ModeLgc = True; Harmonizing_Active_STL = True; LRU Location configured.",
             "Obs 7", "Test Inputs", "LRUSWRS-1002", ws.cell(row=117, column=2).value,
             "Populate test input of SWRS-1004 as input instead of 'None' per client observation 7.")
    set_cell(117, 8,
             "Software enters Harmonizing Mode; Harmonizing_Active_STL = True; Harmonizing sequence initiated.",
             "Obs 7", "Expected Result(s)", "LRUSWRS-1002", ws.cell(row=117, column=2).value,
             "Assert successful entry into harmonizing mode.")

    # -------------------------------------------------------------
    # 5. Observation 6: LRUSWRS-1003 (Rows 118 to 121)
    # Use Parker's exact 6 cases, clean foreign variables, IVT_Mode_ModeLgc as input
    # -------------------------------------------------------------
    # Row 118: N1
    set_cell(118, 5, "Verifies LRU software enters Harmonizing mode when Harmonizing_Active_STL remains True for 10 consecutive STL frames while IVT_Mode_ModeLgc is True.", "Obs 6", "Test Case Description", "LRUSWRS-1003", ws.cell(row=118, column=2).value, "Parker reference description.")
    set_cell(118, 6, "Operational Mode: FLIGHT_MODE; Harmonizing_Active_STL = False at frame 0.", "Obs 6", "Initial Condition(s)", "LRUSWRS-1003", ws.cell(row=118, column=2).value, "Clean setup without foreign variables.")
    set_cell(118, 7, "IVT_Mode_ModeLgc = True; Frames 1-10: Harmonizing_Active_STL = True.", "Obs 6", "Test Inputs", "LRUSWRS-1003", ws.cell(row=118, column=2).value, "IVT_Mode_ModeLgc in inputs per client observation 6.")
    set_cell(118, 8, "LRU software enters Harmonizing mode at frame 10; Harmonizing_Active_STL = True.", "Obs 6", "Expected Result(s)", "LRUSWRS-1003", ws.cell(row=118, column=2).value, "Expected mode entry asserted.")

    # Row 119: DC_IVT
    set_cell(119, 5, "Verifies LRU does not enter Harmonizing mode when IVT_Mode_ModeLgc is False while Harmonizing_Active_STL remains True for 10 consecutive STL frames.", "Obs 6", "Test Case Description", "LRUSWRS-1003", ws.cell(row=119, column=2).value, "DC test for IVT_Mode_ModeLgc.")
    set_cell(119, 6, "Operational Mode: FLIGHT_MODE; Harmonizing_Active_STL = False at frame 0.", "Obs 6", "Initial Condition(s)", "LRUSWRS-1003", ws.cell(row=119, column=2).value, "Clean setup.")
    set_cell(119, 7, "IVT_Mode_ModeLgc = False; Frames 1-10: Harmonizing_Active_STL = True.", "Obs 6", "Test Inputs", "LRUSWRS-1003", ws.cell(row=119, column=2).value, "IVT_Mode_ModeLgc = False tested.")
    set_cell(119, 8, "LRU does not enter Harmonizing mode; Harmonizing_Active_STL remains False/unasserted.", "Obs 6", "Expected Result(s)", "LRUSWRS-1003", ws.cell(row=119, column=2).value, "Negative DC assertion.")

    # Row 120: Boundary 10 frames
    set_cell(120, 5, "Verifies LRU enters Harmonizing mode when Harmonizing_Active_STL is True for exactly 10 consecutive STL frames while IVT_Mode_ModeLgc is True.", "Obs 6", "Test Case Description", "LRUSWRS-1003", ws.cell(row=120, column=2).value, "Exact 10 frames boundary.")
    set_cell(120, 6, "Operational Mode: FLIGHT_MODE; Harmonizing_Active_STL = False at frame 0.", "Obs 6", "Initial Condition(s)", "LRUSWRS-1003", ws.cell(row=120, column=2).value, "Clean setup.")
    set_cell(120, 7, "IVT_Mode_ModeLgc = True; Frames 1-10: Harmonizing_Active_STL = True; Frame 11: Harmonizing_Active_STL = False.", "Obs 6", "Test Inputs", "LRUSWRS-1003", ws.cell(row=120, column=2).value, "Exact 10 frames.")
    set_cell(120, 8, "LRU enters Harmonizing mode at frame 10.", "Obs 6", "Expected Result(s)", "LRUSWRS-1003", ws.cell(row=120, column=2).value, "Boundary assertion.")

    # Row 121: Boundary 9 frames
    set_cell(121, 5, "Verifies LRU does not enter Harmonizing mode when Harmonizing_Active_STL is True for 9 consecutive STL frames while IVT_Mode_ModeLgc is True.", "Obs 6", "Test Case Description", "LRUSWRS-1003", ws.cell(row=121, column=2).value, "9 frames boundary (below threshold).")
    set_cell(121, 6, "Operational Mode: FLIGHT_MODE; Harmonizing_Active_STL = False at frame 0.", "Obs 6", "Initial Condition(s)", "LRUSWRS-1003", ws.cell(row=121, column=2).value, "Clean setup.")
    set_cell(121, 7, "IVT_Mode_ModeLgc = True; Frames 1-9: Harmonizing_Active_STL = True; Frame 10: Harmonizing_Active_STL = False.", "Obs 6", "Test Inputs", "LRUSWRS-1003", ws.cell(row=121, column=2).value, "9 frames stimulus.")
    set_cell(121, 8, "LRU does not enter Harmonizing mode; mode entry suppressed at 9 frames.", "Obs 6", "Expected Result(s)", "LRUSWRS-1003", ws.cell(row=121, column=2).value, "Boundary assertion.")

    # -------------------------------------------------------------
    # 6. Observation 8: LRUSWRS-1004 (Rows 134 to 136)
    # Move IVT_Mode_ModeLgc from Initial Conditions to Inputs
    # -------------------------------------------------------------
    for r_1004 in [134, 135, 136]:
        curr_init = str(ws.cell(row=r_1004, column=6).value or "")
        clean_init = curr_init.replace("IVT_Mode_ModeLgc = True, ", "").replace("IVT_Mode_ModeLgc = True; ", "").strip()
        set_cell(r_1004, 6, clean_init, "Obs 8", "Initial Condition(s)", "LRUSWRS-1004", ws.cell(row=r_1004, column=2).value, "Remove IVT_Mode_ModeLgc from initial conditions per observation 8.")
        
        curr_inp = str(ws.cell(row=r_1004, column=7).value or "")
        new_inp = f"IVT_Mode_ModeLgc = True; {curr_inp}".strip()
        set_cell(r_1004, 7, new_inp, "Obs 8", "Test Inputs", "LRUSWRS-1004", ws.cell(row=r_1004, column=2).value, "Add IVT_Mode_ModeLgc to test inputs per observation 8.")

    # -------------------------------------------------------------
    # 7. Observation 1: Table 1011 Pin-Strapping (Row 148)
    # -------------------------------------------------------------
    set_cell(148, 5,
             "Full combinatorial pin-strapping matrix for Table 1011: Evaluates all 21 combinations (ATYPE_1..3 x LRU_1..7 per Table 1011 Rev C) to ensure test case IDs match .tst execution files (SWVCP_AAP_TC_1011_TYPE_1_LRU_1 to TYPE_3_LRU_7).",
             "Obs 1", "Test Case Description", "LRUSWRS-1011", ws.cell(row=148, column=2).value,
             "Detailed pin-strap test description per observation 1.")
    set_cell(148, 7,
             "Hardware Pin Strapping Inputs (ID0_DSP..ID7_DSP) driven for each combination: ATYPE_1 (LRU_1..7), ATYPE_2 (LRU_1..7), ATYPE_3 (LRU_1..7) with correct parity ID0_DSP.",
             "Obs 1", "Test Inputs", "LRUSWRS-1011", ws.cell(row=148, column=2).value,
             "Full combinatorial inputs driven per observation 1.")
    set_cell(148, 8,
             "Decoded Asset Type (ATYPE_1..3) and Decoded LRU Number (LRU_1..7) asserted correctly with Decode_Valid = True across all 21 combinations matching .tst harness.",
             "Obs 1", "Expected Result(s)", "LRUSWRS-1011", ws.cell(row=148, column=2).value,
             "Complete matrix assertion per observation 1.")

    # -------------------------------------------------------------
    # 8. Observation 2: Rows 171 to 179 (LRU-9169 / Step 2)
    # -------------------------------------------------------------
    profiles = {
        171: ("ATYPE-1", 10.0, 1.5, 2.0, 17.0),
        172: ("ATYPE-1", 10.0, 1.5, 2.0, 17.0),
        173: ("ATYPE-1", 10.0, 1.5, 2.0, 17.0),
        174: ("ATYPE-2", 20.0, 1.2, 1.8, 25.8),
        175: ("ATYPE-3", 5.0, 1.0, 1.5, 6.5),
        176: ("ATYPE-1", 12.0, 1.5, 2.0, 20.0),
        177: ("ATYPE-1", 10.0, 1.5, 2.0, 17.0),
        178: ("ATYPE-1", 14.0, 1.5, 2.0, 23.0),
        179: ("ATYPE-1", 10.0, 1.5, 2.0, 17.0),
    }

    for r_step2 in range(171, 180):
        atype, raw_avg, sfc, offset, expected_calc = profiles[r_step2]
        tc_id = ws.cell(row=r_step2, column=2).value
        
        # 1. Clean Initial Conditions: Add "Commanded to Contract Position"
        new_init = f"Operational Mode: FLIGHT_MODE; Target LRU: 9169; Commanded to Contract Position; Profile_Id: {atype}."
        set_cell(r_step2, 6, new_init, "Obs 2", "Initial Condition(s)", "LRU-9169", tc_id,
                 "Commanded_to_Contract_Position moved to initial conditions per client observation 2.")

        # 2. Clean Inputs: single average Act_Disp_Raw value, Harmonize_SFC_Default, Harmonize_Offset_Default
        # REMOVE Contract_Stop_Collection_Complete from inputs!
        new_inp = f"Act_Disp_Raw_Avg = {raw_avg} in (pre-averaged single value); Harmonize_SFC_Default = {sfc}; Harmonize_Offset_Default = {offset}."
        set_cell(r_step2, 7, new_inp, "Obs 2", "Test Inputs", "LRU-9169", tc_id,
                 "Removed Contract_Stop_Collection_Complete from inputs; provided single Act_Disp_Raw average; added default SFC and Offset inputs per client observation 2.")

        # 3. Clean Expected: calculation + Contract_Stop_Collection_Complete = True
        new_exp = f"Act_Disp_Raw_Avg_Contract = ({raw_avg} * {sfc}) + {offset} = {expected_calc} in; Contract_Stop_Collection_Complete = True."
        set_cell(r_step2, 8, new_exp, "Obs 2", "Expected Result(s)", "LRU-9169", tc_id,
                 "Contract_Stop_Collection_Complete = True moved to expected results with validated mathematical formula per client observation 2.")

    # -------------------------------------------------------------
    # CREATE DELTA CHANGELOG & OBSERVATIONS SHEET
    # -------------------------------------------------------------
    ws_log = wb.create_sheet(title="Delta Changelog (Manu Comments)")
    log_headers = ["Sl #", "Observation #", "Excel Row #", "Test Case ID", "Requirement Trace", "Modified Field", "Previous Value in Reviewed File", "Updated Value (Delta)", "Review Justification"]
    ws_log.append(log_headers)

    for col_idx in range(1, len(log_headers) + 1):
        c = ws_log.cell(row=1, column=col_idx)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for idx, entry in enumerate(changelog, 1):
        ws_log.append([
            idx,
            entry["obs"],
            entry["row"],
            entry["tc_id"],
            entry["req_id"],
            entry["field"],
            entry["old"],
            entry["new"],
            entry["reason"]
        ])
        log_row_idx = idx + 1
        for c_idx in range(1, len(log_headers) + 1):
            cell = ws_log.cell(row=log_row_idx, column=c_idx)
            cell.font = regular_font
            cell.border = thin_border
            if c_idx in [1, 2, 3]:
                cell.alignment = Alignment(horizontal="center", vertical="top")
            elif c_idx in [4, 5, 6]:
                cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
                cell.font = bold_font
            else:
                cell.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            if c_idx == 8: # The updated delta column
                cell.fill = yellow_fill

    ws_log.column_dimensions['A'].width = 8
    ws_log.column_dimensions['B'].width = 14
    ws_log.column_dimensions['C'].width = 12
    ws_log.column_dimensions['D'].width = 28
    ws_log.column_dimensions['E'].width = 22
    ws_log.column_dimensions['F'].width = 20
    ws_log.column_dimensions['G'].width = 38
    ws_log.column_dimensions['H'].width = 45
    ws_log.column_dimensions['I'].width = 45

    wb.save(out_path_1)
    wb.save(out_path_2)
    print(f"Delta Excel generated successfully!")
    print(f"Output 1: {out_path_1}")
    print(f"Output 2: {out_path_2}")
    print(f"Total Delta changes logged: {len(changelog)}")

if __name__ == "__main__":
    build_delta_excel()
