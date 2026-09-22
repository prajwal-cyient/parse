import docx
import re
import os

doc_path = r"c:\Users\pm89542\Downloads\test_parker\SW_Requirements_Sample_1.docx"
doc = docx.Document(doc_path)

full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

# Find all requirement blocks
req_blocks = re.split(r"(?=\d+\.\s*[Rr]equirement:|\d+\.\s*[Rr]equirement|ID\s*:\s*LRUSWRS)", full_text)

other_reqs = []
for b in req_blocks:
    b_str = b.strip()
    if not b_str: continue
    id_m = re.search(r"ID\s*:\s*([A-Z0-9_-]+)", b_str, re.IGNORECASE)
    if id_m:
        r_id = id_m.group(1).strip()
        if "1001" not in r_id: # Non-Table 1001 requirements
            other_reqs.append((r_id, b_str))

print("=========================================================================")
print("NON-TABLE 1001 REQUIREMENTS FOUND IN SW_Requirements_Sample_1.docx:")
print("=========================================================================\n")

unique_other = {}
for r_id, b_str in other_reqs:
    if r_id not in unique_other:
        unique_other[r_id] = b_str

print(f"Total Non-Table 1001 Requirements Found: {len(unique_other)}")
for r_id, b_str in unique_other.items():
    snippet_lines = [l.strip() for l in b_str.split("\n") if l.strip() and not l.strip().startswith("Req Type") and not l.strip().startswith("Safety")]
    snippet_text = " ".join(snippet_lines[:2])
    print(f" * {r_id}: {snippet_text[:110]}...")
