import urllib.request
import json
import time

endpoint = "http://localhost:11434/api/generate"
payload = {
    "model": "gpt-oss:latest",
    "prompt": "You are a DO-178C test generator. Return a JSON object with a 'test_cases' list containing 1 test case for LRUSWRS-1002.",
    "format": "json",
    "stream": False,
    "options": {"temperature": 0.0, "num_ctx": 4096, "num_predict": 512}
}

t0 = time.time()
print("Sending request to gpt-oss:latest...")
req = urllib.request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=60) as resp:
    res = json.loads(resp.read().decode("utf-8"))
    print(f"Response in {time.time()-t0:.2f}s:")
    print(res.get("response"))
