import docx

doc = docx.Document('c:/Users/pm89542/Desktop/parse/SW_Requirements_Sample_1.docx')

print("=== TABLE 1 DETAILS (Table 1001) ===")
table = doc.tables[0]
for r_idx, row in enumerate(table.rows):
    cells_text = [cell.text.strip().replace('\n', ' ') for cell in row.cells]
    print(f"Row {r_idx:2d}: {' | '.join(cells_text).encode('ascii', errors='replace').decode('ascii')}")
