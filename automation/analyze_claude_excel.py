import openpyxl
import os

EXCEL_PATH = r"c:\Users\pm89542\Desktop\parse\Sample_1\AI_vs_Manual_TestCase_Comparison_Req1001.xlsx"

if not os.path.exists(EXCEL_PATH):
    print("File not found:", EXCEL_PATH)
else:
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    print("=========================================================================")
    print("ANALYZING WORKBOOK:", EXCEL_PATH)
    print("Sheet Names:", wb.sheetnames)
    print("=========================================================================\n")

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        print(f"--- SHEET: '{sheet_name}' ({ws.max_row} rows x {ws.max_column} cols) ---")
        
        # Print top 15 rows to understand layout & summary metrics
        for r in range(1, min(25, ws.max_row + 1)):
            row_vals = [str(ws.cell(row=r, column=c).value).strip() if ws.cell(row=r, column=c).value is not None else "" for c in range(1, min(12, ws.max_column + 1))]
            if any(row_vals):
                print(f"Row {r:2d}: {' | '.join(row_vals)}")
        print("\n" + "-"*75 + "\n")
