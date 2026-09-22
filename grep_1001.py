import glob
import json

print("=== GREP FOR 1001 IN DESKTOP/PARSE ===")
for p in glob.glob("c:/Users/pm89542/Desktop/parse/**/*.json", recursive=True):
    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
        txt = f.read()
        if '1001' in txt:
            print(f"Found 1001 in {p}")
            
for p in glob.glob("c:/Users/pm89542/Desktop/parse/**/*.txt", recursive=True):
    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
        txt = f.read()
        if '1001' in txt:
            print(f"Found 1001 in {p}")
