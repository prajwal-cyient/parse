import urllib.request
import json

for host in ["127.0.0.1", "localhost", "[::1]"]:
    try:
        url = f"http://{host}:11434/api/tags"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = resp.read().decode("utf-8")
            print(f"Host {host}: Status {resp.status}, len={len(data)}")
    except Exception as e:
        print(f"Host {host}: Error {e}")
