"""Configure DeepSeek model in Dify via API - session-based auth"""
import requests
import base64
import json

BASE = "http://localhost/console/api"
EMAIL = "2257302877@qq.com"
PASSWORD = "pty666666"
DEEPSEEK_KEY = "sk-540222586bf946bfa0e6af4b4453650b"

session = requests.Session()

# Step 1: Login with base64 encoded password
print("1. Logging in...")
pwd_b64 = base64.b64encode(PASSWORD.encode()).decode()
resp = session.post(f"{BASE}/login", json={
    "email": EMAIL,
    "password": pwd_b64
}, timeout=10)
print(f"   Status: {resp.status_code}, Response: {resp.text[:100]}")

if resp.status_code != 200:
    exit(1)

# Get CSRF token from cookies
csrf = session.cookies.get("csrf_token", "")
print(f"   CSRF Token: {csrf[:20]}..." if csrf else "   No CSRF token")

# Set headers
headers = {
    "Content-Type": "application/json",
    "X-CSRF-Token": csrf,
    "Referer": "http://localhost",
}

# Step 2: Get current workspace
print("\n2. Getting workspace info...")
resp = session.get(f"{BASE}/workspaces/current", headers=headers, timeout=10)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    ws = resp.json()
    ws_id = ws.get("id", ws.get("data", {}).get("id", "unknown"))
    print(f"   Workspace ID: {ws_id}")

# Step 3: List current model providers
print("\n3. Current model providers...")
resp = session.get(f"{BASE}/workspaces/current/model-providers", headers=headers, timeout=10)
print(f"   Status: {resp.status_code}")
if resp.status_code == 200:
    providers = resp.json()
    if isinstance(providers, list):
        for p in providers:
            pname = p.get("provider", "") or p.get("provider_name", "")
            print(f"   - {pname}")
    elif isinstance(providers, dict):
        for p in providers.get("data", []):
            pname = p.get("provider", "") or p.get("provider_name", "")
            print(f"   - {pname}")

# Step 4: Try to add OpenAI-compatible provider for DeepSeek
print("\n4. Adding DeepSeek as OpenAI-compatible provider...")

# Try the credentials endpoint
cred_data = {
    "credentials": {
        "openai_api_key": DEEPSEEK_KEY,
        "openai_api_base_url": "https://api.deepseek.com/v1",
    }
}

resp = session.post(
    f"{BASE}/workspaces/current/model-providers/openai_api_compatible/credentials",
    headers=headers,
    json=cred_data,
    timeout=15
)
print(f"   Attempt 1 Status: {resp.status_code}")
print(f"   Response: {resp.text[:200]}")

if resp.status_code != 200:
    # Try alternative format
    cred_data2 = {
        "credentials": {
            "api_key": DEEPSEEK_KEY,
            "base_url": "https://api.deepseek.com/v1",
        }
    }
    resp = session.post(
        f"{BASE}/workspaces/current/model-providers/openai_api_compatible/credentials",
        headers=headers,
        json=cred_data2,
        timeout=15
    )
    print(f"   Attempt 2 Status: {resp.status_code}")
    print(f"   Response: {resp.text[:200]}")

# Step 5: List available model types for this provider
print("\n5. Listing available model types...")
resp = session.get(
    f"{BASE}/workspaces/current/model-providers/openai_api_compatible/models",
    headers=headers,
    timeout=10
)
print(f"   Status: {resp.status_code}")
print(f"   Response: {resp.text[:300]}")

print("\nDone.")
