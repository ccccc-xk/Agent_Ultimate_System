"""Debug tool providers - list all"""
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

print("All tool providers:")
resp = session.get(f"{BASE}/workspaces/current/tool-providers", headers=headers, timeout=10)
providers = resp.json()

for i, p in enumerate(providers):
    pid = p.get("id", "?")
    ptype = p.get("type", "?")
    name = p.get("name", "?")
    label = p.get("label", {}).get("en_US", "?")
    is_auth = p.get("is_team_authorization", False)
    tools = p.get("tools", [])
    print(f"\n  [{i}] id={pid}, type={ptype}, name={name}, label={label}, auth={is_auth}, tools={len(tools)}")
    for t in tools:
        print(f"      - {t.get('name','?')}: {t.get('label',{}).get('en_US','?')}")

# For custom API tools, get their tools separately
print("\n\nGetting tools for each custom provider...")
for p in providers:
    if p.get("type") == "api":
        pid = p.get("id")
        print(f"\n  Provider: {pid}")
        resp = session.get(f"{BASE}/workspaces/current/tool-provider/api/{pid}/tools", headers=headers, timeout=10)
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            tools = resp.json()
            print(f"  Response: {json.dumps(tools, indent=2, ensure_ascii=False)[:500]}")

print("\nDone.")
