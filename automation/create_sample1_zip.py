import os
import zipfile
import time
from datetime import datetime

sample1_dir = r"c:\Users\pm89542\Desktop\parse\samples\sample_1"
zip_path = r"c:\Users\pm89542\Desktop\parse\samples\Sample_1.zip"

now = time.time()

# Touch filesystem mtimes
for root, dirs, files in os.walk(sample1_dir):
    for f in files:
        if not f.startswith("~$"):
            fp = os.path.join(root, f)
            os.utime(fp, (now, now))

dt_now = datetime.fromtimestamp(now)
zip_dt = (dt_now.year, dt_now.month, dt_now.day, dt_now.hour, dt_now.minute, dt_now.second)
dt_str = dt_now.strftime("%Y-%m-%d %H:%M:%S")

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(sample1_dir):
        for f in files:
            if not f.startswith("~$"):
                fp = os.path.join(root, f)
                arcname = os.path.relpath(fp, sample1_dir)
                zinfo = zipfile.ZipInfo(arcname, zip_dt)
                with open(fp, "rb") as fh:
                    zf.writestr(zinfo, fh.read())

os.utime(zip_path, (now, now))

print("=========================================================================")
print("SUCCESSFULLY CREATED COMPLETE SAMPLE 1 ZIP ARCHIVE!")
print(f"Zip Location: {zip_path}")
print(f"Zip Last Modified Time: {dt_str}")
print("=========================================================================")
