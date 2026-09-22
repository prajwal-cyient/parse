import docx

doc = docx.Document('c:/Users/pm89542/Desktop/parse/SW_Requirements_Sample_1.docx')

print("=== ALL PARAGRAPHS IN DOCX ===")
for i, p in enumerate(doc.paragraphs):
    txt = p.text.strip()
    if '1001' in txt or 'LRUSWRS' in txt or 'Harmoniz' in txt:
        print(f"P[{i}]: {txt.encode('ascii', errors='replace').decode('ascii')}")

print("\n=== SEARCHING FOR LRUSWRS-1001 BLOCK ===")
for i, p in enumerate(doc.paragraphs):
    if 'LRUSWRS-1001' in p.text:
        # print 10 paragraphs before and 30 paragraphs after
        start = max(0, i - 5)
        end = min(len(doc.paragraphs), i + 35)
        for j in range(start, end):
            print(f"[{j}]: {doc.paragraphs[j].text.encode('ascii', errors='replace').decode('ascii')}")
