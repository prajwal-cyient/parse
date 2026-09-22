import docx
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.text.paragraph import Paragraph

doc = docx.Document('c:/Users/pm89542/Desktop/parse/SW_Requirements_Sample_1.docx')

after_tbl = False
count = 0
for child in doc.element.body:
    if isinstance(child, CT_Tbl):
        after_tbl = True
    elif after_tbl and isinstance(child, CT_P):
        p = Paragraph(child, doc)
        txt = p.text.strip()
        if txt:
            print("P:", txt.encode('ascii', errors='replace').decode('ascii'))
            count += 1
            if count >= 15:
                break
