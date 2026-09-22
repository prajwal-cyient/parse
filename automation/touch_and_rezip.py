import os
import glob
import time
import zipfile
from datetime import datetime

BASE_DIR = r"c:\Users\pm89542\Desktop\parse\automation"
ZIP_PATH = os.path.join(BASE_DIR, "Table_1001.zip")
STEP_JSON_DIR = os.path.join(BASE_DIR, "step_json_outputs")

now = datetime.now()
now_timestamp = time.time()
now_tuple = (now.year, now.month, now.day, now.hour, now.minute, now.second)

print("=========================================================================")
print(f"UPDATING LAST MODIFIED TIMESTAMPS TO CURRENT TIME: {now.strftime('%Y-%m-%d %H:%M:%S')}")
print("=========================================================================\n")

# 1. Update filesystem mtime for master deliverables
master_files = [
    os.path.join(BASE_DIR, "ALL_TABLE_1001_EXPANDED_TESTCASES_FINAL.xlsx"),
    os.path.join(BASE_DIR, "TABLE_1001_TESTCASES_COMPARISON_MATRIX_FINAL.xlsx"),
    os.path.join(BASE_DIR, "ALL_TABLE_1001_EXPANDED_TESTCASES.json"),
]

for mf in master_files:
    if os.path.exists(mf):
        os.utime(mf, (now_timestamp, now_timestamp))
        print(f"Updated filesystem mtime: {os.path.basename(mf)}")

# 2. Update filesystem mtime for all 38 step JSON files
step_files = glob.glob(os.path.join(STEP_JSON_DIR, "*.json"))
for sf in step_files:
    os.utime(sf, (now_timestamp, now_timestamp))

print(f"Updated filesystem mtime for all {len(step_files)} step JSON files.")

# 3. Create fresh zip with exact current ZipInfo timestamp for every entry
if os.path.exists(ZIP_PATH):
    os.remove(ZIP_PATH)

with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zipf:
    # Add master files with current ZipInfo
    for mf in master_files:
        if os.path.exists(mf):
            arcname = os.path.basename(mf)
            zinfo = zipfile.ZipInfo(arcname, date_time=now_tuple)
            zinfo.compress_type = zipfile.ZIP_DEFLATED
            with open(mf, "rb") as f:
                zipf.writestr(zinfo, f.read())
            print(f"Added to Zip with timestamp {now.strftime('%H:%M:%S')}: {arcname}")
            
    # Add step JSON files with current ZipInfo
    for sf in step_files:
        arcname = os.path.join("step_json_outputs", os.path.basename(sf))
        zinfo = zipfile.ZipInfo(arcname, date_time=now_tuple)
        zinfo.compress_type = zipfile.ZIP_DEFLATED
        with open(sf, "rb") as f:
            zipf.writestr(zinfo, f.read())

# 4. Touch the zip file itself
os.utime(ZIP_PATH, (now_timestamp, now_timestamp))

print("\n=========================================================================")
print(f"SUCCESSFULLY UPDATED ALL TIMESTAMPS FOR 'Table_1001.zip'!")
print(f"Zip Location: {ZIP_PATH}")
print(f"Zip File Last Modified Time: {datetime.fromtimestamp(os.path.getmtime(ZIP_PATH)).strftime('%Y-%m-%d %H:%M:%S')}")
print("=========================================================================")
