"""
Dify 配置自动化脚本
将 OpenAPI 工具导入 Dify，检查模型配置，更新前端配置
"""
import requests
import json
import base64
import os
import sys

BASE_URL = "http://localhost:9006"
EMAIL = "2257302877@qq.com"
PASSWORD = "pty666666"
APP_ID = "3b4ade8b-ab3c-45ab-8c4e-38661ecb1ed6"
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

session = requests.Session()


def login():
    pwd_b64 = base64.b64encode(PASSWORD.encode()).decode()
    resp = session.post(f"{BASE_URL}/console/api/login", json={
        "email": EMAIL, "password": pwd_b64
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    csrf = session.cookies.get("csrf_token")
    session.headers["X-CSRF-Token"] = csrf
    print("[OK] Dify login successful")
    return True


def check_models():
    resp = session.get(f"{BASE_URL}/console/api/workspaces/current/models/model-types/llm")
    if resp.status_code == 200:
        data = resp.json()
        print(f"\n[INFO] Available LLM models:")
        for provider in data.get("data", []):
            for model in provider.get("models", []):
                print(f"  - {provider.get('provider')}/{model.get('model')}")
        return data
    print(f"[WARN] Could not fetch models: {resp.status_code}")
    return None


def get_app_details():
    resp = session.get(f"{BASE_URL}/console/api/apps/{APP_ID}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"\n[INFO] App: {data.get('name')} (mode: {data.get('mode')})")
        return data
    print(f"[WARN] Could not fetch app: {resp.status_code}")
    return None


def import_openapi_tool(json_path, tool_name, auth_token=None):
    """Import an OpenAPI JSON file as a custom tool in Dify"""
    print(f"\n[INFO] Importing tool: {tool_name}")

    with open(json_path, "r", encoding="utf-8-sig") as f:
        openapi_spec = json.load(f)

    credentials = {"auth_type": "none"}
    if auth_token:
        credentials = {
            "auth_type": "api_key",
            "api_key": auth_token,
            "api_key_header": "Authorization",
            "api_key_header_prefix": "Bearer",
        }

    payload = {
        "provider": tool_name,
        "credentials": credentials,
        "icon": {"content": "\U0001f527", "background": "#E4FBCC"},
        "schema_type": "openapi",
        "schema": json.dumps(openapi_spec, ensure_ascii=False),
        "privacy_policy": "",
        "custom_disclaimer": "",
    }

    resp = session.post(
        f"{BASE_URL}/console/api/workspaces/current/tool-provider/api/add",
        json=payload,
    )

    if resp.status_code in (200, 201):
        print(f"  [OK] {tool_name} imported successfully")
        return True
    else:
        print(f"  [WARN] Import failed: {resp.status_code} - {resp.text[:300]}")
        return False


def list_api_tools():
    resp = session.get(f"{BASE_URL}/console/api/workspaces/current/tools/api")
    if resp.status_code == 200:
        data = resp.json()
        print(f"\n[INFO] Registered API tools ({len(data)}):")
        for t in data:
            provider = t.get("provider", "unknown")
            tools_list = t.get("tools", [])
            print(f"  - {provider}: {len(tools_list)} tool(s)")
            for tool in tools_list:
                print(f"      * {tool.get('name', '?')}: {tool.get('description', '')[:60]}")
        return data
    print(f"[WARN] Could not list tools: {resp.status_code}")
    return []


def get_api_key():
    resp = session.get(f"{BASE_URL}/console/api/apps/{APP_ID}/api-keys")
    if resp.status_code == 200:
        data = resp.json()
        keys = data.get("data", [])
        if keys:
            key = keys[0].get("token")
            print(f"[OK] API Key: {key}")
            return key
    print(f"[WARN] Could not get API key: {resp.status_code}")
    return None


def update_frontend_config(api_key):
    for name in ("demo.html", "index.html"):
        path = os.path.join(PROJECT_DIR, "frontend", name)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace("app-replace-with-your-key", api_key)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[OK] Updated {name} with API key")


def get_p01_jwt_token():
    """Get JWT token from P01 for tool auth"""
    try:
        resp = requests.post(
            "http://localhost:9001/api/auth/login",
            json={"username": "admin", "password": "123456"},
            timeout=5,
        )
        if resp.status_code == 200:
            data = resp.json()
            token = data.get("data", {}).get("roles", [None])[0]
            if token:
                print(f"[OK] P01 JWT token obtained")
                return token
    except Exception as e:
        print(f"[WARN] Could not get P01 JWT: {e}")
    return None


def main():
    print("=" * 60)
    print("Dify 自动化配置脚本")
    print("=" * 60)

    login()
    check_models()
    get_app_details()

    # Get P01 JWT for authenticated tools
    p01_token = get_p01_jwt_token()

    # Import OpenAPI tools
    openapi_dir = os.path.join(PROJECT_DIR, "openapi")
    tools_to_import = [
        ("project1-tools.json", "project1_enterprise_api", p01_token),
        ("project2-tools.json", "project2_logistics_api", None),
        ("project4-medical-rag.json", "project4_medical_rag", None),
        ("project5-rag.json", "project5_rag_api", None),
    ]

    for filename, tool_name, token in tools_to_import:
        json_path = os.path.join(openapi_dir, filename)
        if os.path.exists(json_path):
            import_openapi_tool(json_path, tool_name, token)
        else:
            print(f"[SKIP] {filename} not found")

    list_api_tools()
    api_key = get_api_key()
    if api_key:
        update_frontend_config(api_key)

    print("\n" + "=" * 60)
    print("Configuration complete!")
    print(f"App URL: {BASE_URL}/app/{APP_ID}/workflow")
    print(f"API Key: {api_key or 'N/A'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
