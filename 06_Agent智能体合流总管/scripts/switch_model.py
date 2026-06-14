"""Switch Dify Agent model to DeepSeek - v3 with correct API format"""
import requests
import base64
import json

BASE = "http://localhost/console/api"
EMAIL = "2257302877@qq.com"
PASSWORD = "pty666666"
APP_ID = "b4625d7c-e07a-41af-a68e-59193b1c1d3c"

session = requests.Session()

# Login
pwd_b64 = base64.b64encode(PASSWORD.encode()).decode()
resp = session.post(f"{BASE}/login", json={"email": EMAIL, "password": pwd_b64}, timeout=10)
csrf = session.cookies.get("csrf_token", "")
headers = {"Content-Type": "application/json", "X-CSRF-Token": csrf, "Referer": "http://localhost"}
print(f"Login: {resp.status_code}")

# Get full app detail to understand the structure
print("\n1. Getting app detail...")
resp = session.get(f"{BASE}/apps/{APP_ID}", headers=headers, timeout=10)
if resp.status_code == 200:
    app = resp.json()
    print(f"   App: {app.get('name')}, Mode: {app.get('mode')}")
    model = app.get("model_config", {}).get("model", {})
    print(f"   Current model: provider={model.get('provider')}, model={model.get('model')}")
    print(f"   Completion params: {model.get('completion_params', {})}")
    
    # Get the full model_config
    model_config = app.get("model_config", {})
    print(f"\n   model_config keys: {list(model_config.keys())}")

# Try different API endpoints for model config update
print("\n2. Trying model-config update with name field...")
update_payload = {
    "model": {
        "provider": "langgenius/deepseek/deepseek",
        "model": "deepseek-v4-flash",
        "name": "deepseek-v4-flash",
        "mode": "chat",
        "completion_params": {
            "temperature": 0.7,
            "max_tokens": 2048
        }
    }
}

# Try PUT
resp = session.put(
    f"{BASE}/apps/{APP_ID}/model-config",
    headers=headers,
    json=update_payload,
    timeout=15
)
print(f"   PUT status: {resp.status_code}")
print(f"   Response: {resp.text[:200]}")

if resp.status_code != 200:
    # Try with the full model_config from the app
    if resp.status_code != 200:
        print("\n   Trying POST with different format...")
        # Include all required fields
        full_payload = {
            "model": {
                "provider": "langgenius/deepseek/deepseek",
                "model": "deepseek-v4-flash",
                "name": "deepseek-v4-flash",
                "mode": "chat",
                "completion_params": {
                    "temperature": 0.7,
                    "max_tokens": 2048
                }
            },
            "pre_prompt": "",
            "agent_mode": {
                "enabled": True,
                "max_iteration": 5,
                "strategy": "function_call"
            },
            "dataset_configs": {
                "retrieval_model": "multiple",
                "datasets": []
            }
        }
        resp = session.post(
            f"{BASE}/apps/{APP_ID}/model-config",
            headers=headers,
            json=full_payload,
            timeout=15
        )
        print(f"   POST full status: {resp.status_code}")
        print(f"   Response: {resp.text[:300]}")

# Verify
print("\n3. Verifying...")
resp = session.get(f"{BASE}/apps/{APP_ID}", headers=headers, timeout=10)
if resp.status_code == 200:
    app = resp.json()
    model = app.get("model_config", {}).get("model", {})
    print(f"   Current model: provider={model.get('provider')}, model={model.get('model')}")

print("\nDone.")
