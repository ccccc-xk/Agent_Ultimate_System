"""Get API tool details from each provider"""
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

api_providers = [
    ("8e53e959-9c8a-4757-937c-a4792d0df957", "project1"),
    ("d53008c5-3fa7-4b1d-902d-ffa3f464d5ee", "project2"),
    ("7d8ae4a0-28bd-4cf4-9301-cfd5bd9af49c", "project4"),
    ("fb0e9d52-adae-41a0-9ab7-73ceb8365cba", "project5"),
]

for pid, name in api_providers:
    print(f"\n=== {name} ({pid}) ===")
    
    # Try various endpoints
    endpoints = [
        f"{BASE}/workspaces/current/tool-provider/{pid}",
        f"{BASE}/workspaces/current/tool-provider/api/{pid}",
        f"{BASE}/workspaces/current/tool-providers/{pid}",
        f"{BASE}/workspaces/current/tool-providers/api/{pid}",
        f"{BASE}/workspaces/current/tool-provider/api/tools",
    ]
    
    for ep in endpoints:
        resp = session.get(ep, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"  Endpoint: {ep.split('tool')[1]}")
            print(f"  Response: {json.dumps(data, indent=2, ensure_ascii=False)[:300]}")
            break
    else:
        print(f"  All endpoints returned non-200")

# Also check the tools/ endpoint for the app
print("\n\n=== App Tools ===")
APP_ID = "b4625d7c-e07a-41af-a68e-59193b1c1d3c"
endpoints = [
    f"{BASE}/apps/{APP_ID}/tools",
    f"{BASE}/apps/{APP_ID}/tool-configs",
    f"{BASE}/apps/{APP_ID}/tools/builtin",
    f"{BASE}/apps/{APP_ID}/tools/api",
]
for ep in endpoints:
    resp = session.get(ep, headers=headers, timeout=10)
    print(f"  {ep.split('apps/')[1]}: {resp.status_code}")
    if resp.status_code == 200:
        print(f"    {json.dumps(resp.json(), ensure_ascii=False)[:300]}")

print("\nDone.")
