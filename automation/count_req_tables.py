import os, json
from docx import Document

DOC_PATH = r"c:\\Users\\pm89542\\Downloads\\test_parker\\SW_Requirements_Sample_1.docx"

if not os.path.exists(DOC_PATH):
    print('Requirements doc not found')
else:
    doc = Document(DOC_PATH)
    tables = doc.tables
    print(f'Number of tables in SW_Requirements_Sample_1.docx: {len(tables)}')
    # Print a brief summary of each table (row count, column count, first row header)
    for idx, tbl in enumerate(tables, start=1):
        rows = len(tbl.rows)
        cols = len(tbl.columns)
        header_cells = tbl.rows[0].cells if rows>0 else []
        header = [cell.text.strip() for cell in header_cells]
        print(f'-- Table {idx}: {rows} rows x {cols} cols, Header: {header}')
