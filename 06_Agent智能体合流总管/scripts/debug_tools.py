"""Debug tool providers - check raw response"""
import requests
import base64
import json

BASE = "http://localhost/console/api"
EMAIL = "2257302877@qq.com"
PASSWORD = "pty666666"

session = requests.Session()
pwd_b64 = base64.b64encode(PASSWORD.encode()).decode()
resp = session.post(f"{BASE}/login", json={"email": EMAIL, "password": pwd_b64}, timeout=10)
csrf = session.cookies.get("csrf_token", "")
headers = {"Content-Type": "application/json", "X-CSRF-Token": csrf, "Referer": "http://localhost"}

# Get raw tool providers response
print("1. Raw tool providers response:")
resp = session.get(f"{BASE}/workspaces/current/tool-providers", headers=headers, timeout=10)
print(f"   Status: {resp.status_code}")
raw = resp.json()
print(f"   Type: {type(raw)}")
if isinstance(raw, dict):
    print(f"   Keys: {list(raw.keys())}")
    data = raw.get("data", [])
    print(f"   Data length: {len(data)}")
    if data:
        print(f"\n   First item full JSON:")
        print(json.dumps(data[0], indent=2, ensure_ascii=False)[:1000])
        print(f"\n   Second item full JSON:")
        if len(data) > 1:
            print(json.dumps(data[1], indent=2, ensure_ascii=False)[:1000])
elif isinstance(raw, list):
    print(f"   List length: {len(raw)}")
    if raw:
        print(f"\n   First item:")
        print(json.dumps(raw[0], indent=2, ensure_ascii=False)[:1000])

# Also check the specific tool list endpoint
print("\n\n2. Checking /api/tools endpoint...")
resp = session.get(f"{BASE}/workspaces/current/tools", headers=headers, timeout=10)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    print(f"   Response: {json.dumps(resp.json(), indent=2, ensure_ascii=False)[:500]}")

print("\nDone.")
