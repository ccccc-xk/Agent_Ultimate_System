"""Try to add tools to existing API providers in Dify"""
import requests
import base64
import json
import os

BASE = "http://localhost/console/api"
EMAIL = "2257302877@qq.com"
PASSWORD = "pty666666"
APP_ID = "b4625d7c-e07a-41af-a68e-59193b1c1d3c"

session = requests.Session()
pwd_b64 = base64.b64encode(PASSWORD.encode()).decode()
resp = session.post(f"{BASE}/login", json={"email": EMAIL, "password": pwd_b64}, timeout=10)
csrf = session.cookies.get("csrf_token", "")
headers = {"X-CSRF-Token": csrf, "Referer": "http://localhost", "Content-Type": "application/json"}

# Get all providers
resp = session.get(f"{BASE}/workspaces/current/tool-providers", headers=headers, timeout=10)
providers = resp.json()

# For each API provider, try to add tools
for p in providers:
    if p.get("type") != "api":
        continue
    
    pid = p.get("id")
    pname = p.get("name")
    print(f"\n=== {pname} ({pid}) ===")
    
    # Try to get the provider's schema/spec
    for ep in [
        f"{BASE}/workspaces/current/tool-provider/{pid}/schema",
        f"{BASE}/workspaces/current/tool-provider/api/{pid}",
        f"{BASE}/workspaces/current/tool-providers/{pid}",
    ]:
        resp = session.get(ep, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"  Schema endpoint: {ep.split('current/')[1]}")
            print(f"  Response: {json.dumps(data, ensure_ascii=False)[:500]}")
            break

# Now try the most likely Dify v1.14 tool management endpoints
print("\n\n=== Trying to discover tool management endpoints ===")

# Check the Dify API docs endpoint
for ep in [
    f"{BASE}/workspaces/current/tool-providers",
    f"{BASE}/workspaces/current/tool-providers/builtin",
    f"{BASE}/workspaces/current/tool-providers/api",
    f"{BASE}/workspaces/current/tool-providers/model",
]:
    resp = session.get(ep, headers=headers, timeout=10)
    print(f"  {ep.split('current/')[1]}: {resp.status_code}")

# Try to create a tool for the project2 provider (simpler, no auth)
print("\n\n=== Creating a tool for project2 ===")
provider_id = "d53008c5-3fa7-4b1d-902d-ffa3f464d5ee"

# Try POST to add a tool
tool_payload = {
    "name": "smart_dispatch",
    "label": {
        "zh_Hans": "智能派单",
        "en_US": "Smart Dispatch"
    },
    "description": {
        "zh_Hans": "当用户描述报修/投诉/故障场景时，调用此工具自动创建工单",
        "en_US": "Auto-dispatch work orders from natural language descriptions"
    },
    "parameters": [
        {
            "name": "text",
            "type": "string",
            "required": True,
            "description": "用户的口语化报修/投诉描述文本"
        }
    ],
    "method": "POST",
    "path": "/api/nlp/dispatch"
}

for ep in [
    f"{BASE}/workspaces/current/tool-provider/{provider_id}/tools",
    f"{BASE}/workspaces/current/tool-provider/api/{provider_id}/tools",
]:
    resp = session.post(ep, headers=headers, json=tool_payload, timeout=15)
    print(f"  POST {ep.split('current/')[1]}: {resp.status_code}")
    if resp.status_code in [200, 201]:
        print(f"  Success: {resp.text[:200]}")
        break
    else:
        print(f"  Error: {resp.text[:200]}")

print("\nDone.")
