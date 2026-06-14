"""Re-import OpenAPI tools into Dify and associate with Agent app"""
import requests
import base64
import json
import os

BASE = "http://localhost/console/api"
EMAIL = "2257302877@qq.com"
PASSWORD = "pty666666"
APP_ID = "b4625d7c-e07a-41af-a68e-59193b1c1d3c"
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

session = requests.Session()
pwd_b64 = base64.b64encode(PASSWORD.encode()).decode()
resp = session.post(f"{BASE}/login", json={"email": EMAIL, "password": pwd_b64}, timeout=10)
csrf = session.cookies.get("csrf_token", "")
headers = {"X-CSRF-Token": csrf, "Referer": "http://localhost"}

print(f"Login: {resp.status_code}")

# Check Dify API docs for tool import endpoint
# In Dify, custom tools can be imported via POST /workspaces/current/tool-provider/api
openapi_files = [
    "project1-tools.json",
    "project2-tools.json",
    "project4-medical-rag.json",
    "project5-rag.json",
]

for fname in openapi_files:
    fpath = os.path.join(PROJECT_DIR, "openapi", fname)
    if not os.path.exists(fpath):
        print(f"\nSkipping {fname} - not found")
        continue
    
    print(f"\n{'='*50}")
    print(f"Importing: {fname}")
    
    with open(fpath, "r", encoding="utf-8-sig") as f:
        openapi_spec = json.load(f)
    
    # Try to import via the tools API
    import_payload = {
        "provider": fname.replace(".json", "").replace("-", "_"),
        "icon": {
            "background": "#E4FBCC",
            "content": "🔧"
        },
        "credentials": {
            "api_key": "",
            "api_base_url": openapi_spec.get("servers", [{}])[0].get("url", ""),
        },
        "schema_type": "openapi",
        "schema": json.dumps(openapi_spec),
    }
    
    resp = session.post(
        f"{BASE}/workspaces/current/tool-provider/api",
        headers={**headers, "Content-Type": "application/json"},
        json=import_payload,
        timeout=30
    )
    print(f"  Import status: {resp.status_code}")
    print(f"  Response: {resp.text[:300]}")

# Now check providers again
print(f"\n{'='*50}")
print("Checking providers after import...")
resp = session.get(f"{BASE}/workspaces/current/tool-providers", headers=headers, timeout=10)
if resp.status_code == 200:
    providers = resp.json()
    for p in providers:
        pid = p.get("id", "?")
        ptype = p.get("type", "?")
        name = p.get("name", "?")
        tools = p.get("tools", [])
        if ptype == "api":
            print(f"  {name} (type={ptype}, id={pid[:12]}..., tools={len(tools)})")
            for t in tools:
                print(f"    - {t.get('name', '?')}")

print("\nDone.")
