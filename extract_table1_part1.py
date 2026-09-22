import docx

doc = docx.Document('c:/Users/pm89542/Desktop/parse/SW_Requirements_Sample_1.docx')

print("=== TABLE 1 DETAILS ROWS 0 to 21 ===")
table = doc.tables[0]
for r_idx in range(min(22, len(table.rows))):
    row = table.rows[r_idx]
    cells_text = [cell.text.strip().replace('\n', ' ') for cell in row.cells]
    print(f"Row {r_idx:2d}: {' | '.join(cells_text).encode('ascii', errors='replace').decode('ascii')}")
