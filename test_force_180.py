import requests
import json
import time

url_upload = "http://localhost:8080/api/upload"
with open("SW_Requirements_Sample_1.docx", "rb") as f:
    files = {"file": ("SW_Requirements_Sample_1.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    res = requests.post(url_upload, files=files)

print("Upload response:", res.json().get("status"), "Requirements:", res.json().get("requirements_found"))

url_stream = "http://localhost:8080/api/generate-stream?force=true"
print("Connecting to stream with force=true...")
response = requests.get(url_stream, stream=True)

final_count = 0
for line in response.iter_lines():
    if line:
        decoded = line.decode("utf-8").strip()
        if decoded.startswith("data: "):
            payload = json.loads(decoded[6:])
            step = payload.get("step")
            if step == "PROGRESS":
                pct = payload.get("percentage")
                cur = payload.get("current_index")
                tot = payload.get("total_requirements")
                so_far = payload.get("total_generated_so_far")
                # print first and last few
                if cur in [1, 10, 20, 30, 40, 50, 60, 61]:
                    print(f"Progress: [{cur}/{tot}] ({pct}%) -> {so_far} test cases so far")
            elif step == "COMPLETED":
                final_count = payload.get("total_test_cases")
                print(f"\n===> GENERATION COMPLETED! Total Test Cases: {final_count} <===")

print("Test complete. Result:", final_count)
