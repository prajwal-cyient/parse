import docx

doc = docx.Document('c:/Users/pm89542/Desktop/parse/SW_Requirements_Sample_1.docx')

found = False
for i, p in enumerate(doc.paragraphs):
    if 'ID :  LRUSWRS-1001' in p.text:
        found = True
    if found:
        print(f"[{i}]: {p.text.encode('ascii', errors='replace').decode('ascii')}")
        if 'ID :  LRUSWRS-1007' in p.text:
            break
