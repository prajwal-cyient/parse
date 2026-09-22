import docx

doc = docx.Document('c:/Users/pm89542/Desktop/parse/SW_Requirements_Sample_1.docx')

# Let's iterate body elements to see paragraphs and tables in sequence around LRUSWRS-1001
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.text.paragraph import Paragraph
from docx.table import Table

for child in doc.element.body:
    if isinstance(child, CT_P):
        p = Paragraph(child, doc)
        if 'Req Type' in p.text or 'Safety' in p.text or 'LRUSWRS-1001' in p.text:
            print("P:", p.text.encode('ascii', errors='replace').decode('ascii'))
