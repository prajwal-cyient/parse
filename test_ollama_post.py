import urllib.request
import json
import time

url = "http://127.0.0.1:11434/api/generate"
payload = {
    "model": "gpt-oss:latest",
    "prompt": "Respond with simple JSON: {\"status\": \"ok\"}",
    "stream": False
}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print(f"SUCCESS in {time.time()-t0:.2f}s!")
        print("Response:", res.get("response"))
except Exception as e:
    print(f"Error after {time.time()-t0:.2f}s: {e}")
