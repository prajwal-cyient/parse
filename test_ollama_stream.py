import urllib.request
import json
import time

url = "http://localhost:11434/api/generate"
payload = {
    "model": "gpt-oss:latest",
    "prompt": "Respond with simple JSON: {\"status\": \"ok\"}",
    "stream": True
}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        print(f"Connection established in {time.time()-t0:.2f}s!")
        full_response = ""
        for line in resp:
            if line:
                chunk = json.loads(line.decode("utf-8"))
                full_response += chunk.get("response", "")
        print(f"Stream COMPLETE in {time.time()-t0:.2f}s!")
        print("Full Response:", full_response)
except Exception as e:
    print(f"Stream error after {time.time()-t0:.2f}s: {e}")
