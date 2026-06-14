"""Check and fix Agent tools configuration in Dify"""
import requests
import base64
import json

BASE = "http://localhost/console/api"
EMAIL = "2257302877@qq.com"
PASSWORD = "pty666666"
APP_ID = "b4625d7c-e07a-41af-a68e-59193b1c1d3c"

session = requests.Session()
pwd_b64 = base64.b64encode(PASSWORD.encode()).decode()
resp = session.post(f"{BASE}/login", json={"email": EMAIL, "password": pwd_b64}, timeout=10)
csrf = session.cookies.get("csrf_token", "")
headers = {"Content-Type": "application/json", "X-CSRF-Token": csrf, "Referer": "http://localhost"}
print(f"Login: {resp.status_code}")

# Get full app config
print("\n1. Full app config...")
resp = session.get(f"{BASE}/apps/{APP_ID}", headers=headers, timeout=10)
if resp.status_code == 200:
    app = resp.json()
    mc = app.get("model_config", {})
    
    # Check agent_mode
    print(f"   Agent mode: {json.dumps(mc.get('agent_mode', {}), ensure_ascii=False)}")
    
    # Check external_data_tools
    print(f"   External data tools: {json.dumps(mc.get('external_data_tools', []), ensure_ascii=False)[:300]}")
    
    # Check model
    print(f"   Model: {json.dumps(mc.get('model', {}), ensure_ascii=False)[:200]}")
    
    # Check tools list
    tools = mc.get("tools", [])
    print(f"   Tools in config: {len(tools)}")
    for t in tools[:10]:
        print(f"   - {t.get('tool_name', t.get('label', 'unknown'))}: enabled={t.get('enabled', '?')}")

# List all available tools
print("\n2. All available tools for this app...")
resp = session.get(f"{BASE}/apps/{APP_ID}/tools", headers=headers, timeout=10)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    tools = resp.json()
    print(f"   Response: {json.dumps(tools, ensure_ascii=False)[:500]}")

# Try to get tool variables
print("\n3. Tool variables...")
resp = session.get(f"{BASE}/apps/{APP_ID}/tools/variable-conversation", headers=headers, timeout=10)
print(f"   Status: {resp.status_code}")

# Check available tool providers
print("\n4. Available tool providers...")
resp = session.get(f"{BASE}/workspaces/current/tool-providers", headers=headers, timeout=10)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    providers = resp.json()
    if isinstance(providers, list):
        for p in providers[:15]:
            print(f"   - {p.get('provider_name', 'unknown')}: {p.get('tool_name', '')}")
    elif isinstance(providers, dict):
        data = providers.get("data", [])
        for p in data[:15]:
            print(f"   - {p.get('provider_name', 'unknown')}: {p.get('tool_label', '')}")

# Also check api/tools endpoint
print("\n5. API tools list...")
resp = session.get(f"{BASE}/workspaces/current/api-tools", headers=headers, timeout=10)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"   Response: {json.dumps(data, ensure_ascii=False)[:500]}")

print("\nDone.")
