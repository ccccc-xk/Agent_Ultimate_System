"""Configure DeepSeek model in Dify - using native DeepSeek provider"""
import requests
import base64
import json

BASE = "http://localhost/console/api"
EMAIL = "2257302877@qq.com"
PASSWORD = "pty666666"
DEEPSEEK_KEY = "sk-540222586bf946bfa0e6af4b4453650b"

session = requests.Session()

# Login
print("1. Logging in...")
pwd_b64 = base64.b64encode(PASSWORD.encode()).decode()
resp = session.post(f"{BASE}/login", json={"email": EMAIL, "password": pwd_b64}, timeout=10)
print(f"   Status: {resp.status_code}")
csrf = session.cookies.get("csrf_token", "")
headers = {"Content-Type": "application/json", "X-CSRF-Token": csrf, "Referer": "http://localhost"}

# Check DeepSeek provider
print("\n2. Checking DeepSeek provider...")
resp = session.get(f"{BASE}/workspaces/current/model-providers/langgenius/deepseek/deepseek", headers=headers, timeout=10)
print(f"   Status: {resp.status_code}")
print(f"   Response: {resp.text[:300]}")

# Try to configure DeepSeek provider credentials
print("\n3. Configuring DeepSeek provider...")
resp = session.post(
    f"{BASE}/workspaces/current/model-providers/langgenius/deepseek/deepseek/credentials",
    headers=headers,
    json={
        "credentials": {
            "api_key": DEEPSEEK_KEY,
        }
    },
    timeout=15
)
print(f"   Status: {resp.status_code}")
print(f"   Response: {resp.text[:300]}")

# List available models in DeepSeek provider
print("\n4. Listing DeepSeek models...")
resp = session.get(
    f"{BASE}/workspaces/current/model-providers/langgenius/deepseek/deepseek/models",
    headers=headers,
    timeout=10
)
print(f"   Status: {resp.status_code}")
print(f"   Response: {resp.text[:500]}")

# Try to enable deepseek-chat model
print("\n5. Enabling deepseek-chat model...")
resp = session.post(
    f"{BASE}/workspaces/current/models/model-types/llm",
    headers=headers,
    json={
        "provider": "langgenius/deepseek/deepseek",
        "model": "deepseek-chat",
        "model_type": "llm",
        "credentials": {
            "api_key": DEEPSEEK_KEY,
        }
    },
    timeout=15
)
print(f"   Status: {resp.status_code}")
print(f"   Response: {resp.text[:300]}")

print("\nDone.")
