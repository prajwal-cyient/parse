import urllib.request
import json
import os
import time

url_upload = "http://localhost:8000/api/upload"
file_path = r"c:\Users\pm89542\Desktop\parse\app\uploads\SW_Requirements_Sample_3.docx"

with open(file_path, "rb") as f:
    file_bytes = f.read()

boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="SW_Requirements_Sample_3.docx"\r\n'
    f"Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document\r\n\r\n"
).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

req = urllib.request.Request(url_upload, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
with urllib.request.urlopen(req) as resp:
    res_upload = json.loads(resp.read().decode("utf-8"))

print(f"Upload Success: {res_upload.get('file_name')} - Reqs: {res_upload.get('requirements_found')}")

url_stream = "http://localhost:8000/api/generate-stream"
req_stream = urllib.request.Request(url_stream)

tcs_count = 0
start_time = time.time()

with urllib.request.urlopen(req_stream) as resp:
    for line in resp:
        line_str = line.decode("utf-8").strip()
        if line_str.startswith("data:"):
            data = json.loads(line_str[5:].strip())
            step = data.get("step")
            if step == "QUERYING":
                print(f"[QUERYING] Req {data.get('requirement_id')} ({data.get('current_index')}/{data.get('total_requirements')}) - {data.get('percentage')}%")
            elif step == "PROGRESS":
                tcs_count = data.get("total_generated_so_far", 0)
                print(f"[PROGRESS] {data.get('requirement_id')} - Total TCs So Far: {tcs_count}")
            elif step == "COMPLETED":
                elapsed = round(time.time() - start_time, 2)
                print(f"\n[COMPLETED SUCCESS] Total TCs: {data.get('total_test_cases')} - Time: {elapsed}s")
                print(f"Excel Saved: {data.get('excel_path')}")
