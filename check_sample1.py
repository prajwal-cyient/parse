import os

path = 'extracted_samples/sample 1.txt'
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        txt = f.read()
    print("LRUSWRS-1001 in sample 1.txt:", 'LRUSWRS-1001' in txt)
else:
    print("sample 1.txt not found in extracted_samples")
