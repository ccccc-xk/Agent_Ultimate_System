"""Try alternative tool import endpoints in Dify v1.14"""
import requests
import base64
import json
import os

BASE = "http://localhost/console/api"
EMAIL = "2257302877@qq.com"
PASSWORD = "pty666666"

session = requests.Session()
pwd_b64 = base64.b64encode(PASSWORD.encode()).decode()
resp = session.post(f"{BASE}/login", json={"email": EMAIL, "password": pwd_b64}, timeout=10)
csrf = session.cookies.get("csrf_token", "")
headers = {"X-CSRF-Token": csrf, "Referer": "http://localhost"}

# First, check what the existing API providers look like
print("1. Checking existing API providers...")
resp = session.get(f"{BASE}/workspaces/current/tool-providers", headers=headers, timeout=10)
providers = resp.json()
for p in providers:
    if p.get("type") == "api":
        print(f"\n  Provider: {p.get('name')}")
        print(f"  Full data: {json.dumps(p, indent=2, ensure_ascii=False)[:500]}")

# Try to list tools for an API provider by its name
print("\n\n2. Trying to get tools by provider name...")
for p in providers:
    if p.get("type") == "api":
        pname = p.get("name")
        pid = p.get("id")
        
        # Try various endpoint patterns
        for pattern in [
            f"{BASE}/workspaces/current/tools/provider/{pname}",
            f"{BASE}/workspaces/current/tool/provider/{pname}/tools",
            f"{BASE}/workspaces/current/tool-providers/{pid}/tools",
        ]:
            resp = session.get(pattern, headers=headers, timeout=10)
            if resp.status_code == 200:
                print(f"  FOUND: {pattern}")
                print(f"  Response: {json.dumps(resp.json(), ensure_ascii=False)[:500]}")
                break
        else:
            print(f"  {pname}: no tool endpoint found")

# Try deleting and re-creating a provider
print("\n\n3. Trying to delete and re-create project1 provider...")
provider_id = "8e53e959-9c8a-4757-937c-a4792d0df957"

# Delete
resp = session.delete(
    f"{BASE}/workspaces/current/tool-provider/{provider_id}",
    headers=headers,
    timeout=10
)
print(f"  Delete status: {resp.status_code}")

if resp.status_code in [200, 204]:
    # Re-create with proper format
    PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    openapi_path = os.path.join(PROJECT_DIR, "openapi", "project1-tools.json")
    
    with open(openapi_path, "r", encoding="utf-8-sig") as f:
        spec = json.load(f)
    
    # Try create endpoint
    create_payload = {
        "credentials": {
            "api_key": "",
            "api_base_url": "http://host.docker.internal:9001",
        },
        "schema_type": "openapi",
        "schema": json.dumps(spec),
        "icon": {
            "background": "#E4FBCC",
            "content": "🔧"
        },
        "label": {
            "zh_Hans": "项目一企业管理API",
            "en_US": "Project1 Enterprise API"
        }
    }
    
    for ep in [
        f"{BASE}/workspaces/current/tool-provider/api",
        f"{BASE}/workspaces/current/tool-providers/api",
    ]:
        resp = session.post(ep, headers={**headers, "Content-Type": "application/json"}, json=create_payload, timeout=30)
        print(f"  Create ({ep.split('current/')[1]}): {resp.status_code}")
        if resp.status_code in [200, 201]:
            print(f"  Response: {resp.text[:300]}")
            break
        else:
            print(f"  Error: {resp.text[:200]}")

print("\nDone.")
