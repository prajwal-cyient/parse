import os
from test_parse import parse_file_content

extracted_dir = 'extracted_samples'
for fname in sorted(os.listdir(extracted_dir)):
    if fname.endswith('.txt'):
        fpath = os.path.join(extracted_dir, fname)
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        reqs = parse_file_content(fname, content)
        for r in reqs:
            print(f"=== {fname} | Req #{r['req_num']} ({r['req_id']}) ===")
            print("TEXT:\n" + r['req_text'].encode('ascii', errors='replace').decode('ascii'))
            if r['notes']:
                print("NOTES:\n" + r['notes'].encode('ascii', errors='replace').decode('ascii'))
            print(f"TYPE: {r['req_type']} | SAFETY: {r['safety_impact']} | RATIONALE: {r['safety_rationale']}")
            print("-" * 50)
