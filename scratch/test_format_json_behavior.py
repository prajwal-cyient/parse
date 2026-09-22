import urllib.request
import json

payload = {
    'model': 'gpt-oss:latest',
    'prompt': 'Return a valid JSON object: {"message": "hello world"}',
    'stream': False
}
req = urllib.request.Request('http://localhost:11434/api/generate', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=30) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    print('Without format:json ->', repr(res.get('response')))

payload['format'] = 'json'
req = urllib.request.Request('http://localhost:11434/api/generate', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req, timeout=30) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    print('With format:json ->', repr(res.get('response')))
