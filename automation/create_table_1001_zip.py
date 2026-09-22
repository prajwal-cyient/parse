import zipfile
import os
import glob

BASE_DIR = r"c:\Users\pm89542\Desktop\parse\automation"
ZIP_PATH = os.path.join(BASE_DIR, "Table_1001.zip")
STEP_JSON_DIR = os.path.join(BASE_DIR, "step_json_outputs")

files_to_zip = [
    os.path.join(BASE_DIR, "ALL_TABLE_1001_EXPANDED_TESTCASES_FINAL.xlsx"),
    os.path.join(BASE_DIR, "TABLE_1001_TESTCASES_COMPARISON_MATRIX_FINAL.xlsx"),
    os.path.join(BASE_DIR, "ALL_TABLE_1001_EXPANDED_TESTCASES.json"),
]

print("=========================================================================")
print(f"CREATING MASTER DELIVERABLE ZIP: {ZIP_PATH}")
print("=========================================================================\n")

with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zipf:
    # 1. Add Master Excel & Master JSON files
    for file_path in files_to_zip:
        if os.path.exists(file_path):
            arcname = os.path.basename(file_path)
            zipf.write(file_path, arcname)
            print(f"Added to zip: {arcname}")
        else:
            print(f"Warning: File not found: {file_path}")
            
    # 2. Add all 38 renamed step JSON files
    step_files = glob.glob(os.path.join(STEP_JSON_DIR, "*.json"))
    print(f"\nAdding {len(step_files)} step JSON files from 'step_json_outputs'...")
    for s_file in step_files:
        arcname = os.path.join("step_json_outputs", os.path.basename(s_file))
        zipf.write(s_file, arcname)

print("\n=========================================================================")
print(f"SUCCESSFULLY CREATED 'Table_1001.zip'!")
print(f"Zip File Location: {ZIP_PATH}")
print(f"File Size: {os.path.getsize(ZIP_PATH)} bytes")
print("=========================================================================")
