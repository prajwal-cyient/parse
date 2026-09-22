import os
import json
import glob

DIR_PATH = r"c:\Users\pm89542\Desktop\parse\automation\step_json_outputs"

files = glob.glob(os.path.join(DIR_PATH, "*.json"))

print("=========================================================================")
print(f"RENAMING STEP JSON FILES IN: {DIR_PATH}")
print(f"Total Step Files Found: {len(files)}")
print("=========================================================================\n")

renamed_count = 0

for file_path in files:
    filename = os.path.basename(file_path)
    
    # Read file to extract requirement_id and step_id
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Skipping {filename} due to read error: {e}")
        continue
        
    req_id = data.get("requirement_id", "").strip().replace("-", "_")
    step_id = data.get("step_id", "").strip().lower()
    
    if not req_id and "test_cases" in data and len(data["test_cases"]) > 0:
        req_id = data["test_cases"][0].get("requirement_id", "").strip().replace("-", "_")
        
    # Extract clean step tag (e.g. step_1, step_4a, step_35)
    step_match = filename.replace("_expanded_testcases.json", "").replace(".json", "")
    
    if req_id:
        new_filename = f"{step_match}_{req_id}.json"
    else:
        new_filename = f"{step_match}.json"
        
    new_filepath = os.path.join(DIR_PATH, new_filename)
    
    if file_path != new_filepath:
        os.rename(file_path, new_filepath)
        print(f"Renamed: '{filename}' --> '{new_filename}'")
        renamed_count += 1
    else:
        print(f"Already named correctly: '{filename}'")

print("\n=========================================================================")
print(f"SUCCESSFULLY RENAMED {renamed_count} STEP JSON FILES!")
print("=========================================================================")
