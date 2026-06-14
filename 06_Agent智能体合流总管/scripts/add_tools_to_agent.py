"""Get tool provider details and add tools to Agent app"""
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

# Get all tool providers with details
print("1. Getting tool providers with details...")
resp = session.get(f"{BASE}/workspaces/current/tool-providers", headers=headers, timeout=10)
if resp.status_code == 200:
    providers = resp.json()
    if isinstance(providers, dict):
        providers = providers.get("data", [])
    
    tool_list = []
    for p in providers:
        provider_name = p.get("provider_name", "")
        provider_type = p.get("provider_type", "")
        tools_in_provider = p.get("tools", [])
        print(f"\n   Provider: {provider_name} (type: {provider_type})")
        for t in tools_in_provider:
            tname = t.get("name", "unknown")
            tlabel = t.get("label", {}).get("en_US", tname) if isinstance(t.get("label"), dict) else tname
            print(f"     - {tname} ({tlabel})")
            tool_list.append({
                "provider_id": provider_name,
                "provider_type": provider_type,
                "tool_name": tname,
                "tool_label": tlabel
            })
    
    print(f"\n   Total tools found: {len(tool_list)}")
    
    # Now add tools to the app's agent configuration
    print("\n2. Adding tools to Agent app...")
    
    # Get current app config
    resp = session.get(f"{BASE}/apps/{APP_ID}", headers=headers, timeout=10)
    app = resp.json()
    mc = app.get("model_config", {})
    
    # Build the tools array for agent_mode
    agent_tools = []
    for tool in tool_list:
        agent_tools.append({
            "provider_id": tool["provider_id"],
            "provider_type": tool["provider_type"],
            "tool_name": tool["tool_name"],
            "tool_label": tool["tool_label"],
            "tool_configuration": {},
            "enabled": True
        })
    
    print(f"   Adding {len(agent_tools)} tools...")
    
    # Update the app config with tools
    update_payload = {
        "model": mc.get("model", {}),
        "pre_prompt": mc.get("pre_prompt", ""),
        "agent_mode": {
            "enabled": True,
            "max_iteration": 5,
            "strategy": "function_call",
            "tools": agent_tools
        },
        "dataset_configs": mc.get("dataset_configs", {"retrieval_model": "multiple", "datasets": []}),
        "opening_statement": mc.get("opening_statement", ""),
        "suggested_questions": mc.get("suggested_questions", []),
        "suggested_questions_after_answer": mc.get("suggested_questions_after_answer", {"enabled": True}),
        "speech_to_text": mc.get("speech_to_text", {"enabled": False}),
        "text_to_speech": mc.get("text_to_speech", {"enabled": False}),
        "retriever_resource": mc.get("retriever_resource", {"enabled": True}),
        "annotation_reply": mc.get("annotation_reply", {"enabled": False}),
        "more_like_this": mc.get("more_like_this", {"enabled": False}),
        "sensitive_word_avoidance": mc.get("sensitive_word_avoidance", {"enabled": False}),
        "external_data_tools": mc.get("external_data_tools", []),
        "user_input_form": mc.get("user_input_form", []),
        "file_upload": mc.get("file_upload", {"image": {"enabled": False}}),
    }
    
    resp = session.post(
        f"{BASE}/apps/{APP_ID}/model-config",
        headers=headers,
        json=update_payload,
        timeout=15
    )
    print(f"   Update status: {resp.status_code}")
    print(f"   Response: {resp.text[:200]}")
    
    # Verify
    print("\n3. Verifying tools in app...")
    resp = session.get(f"{BASE}/apps/{APP_ID}", headers=headers, timeout=10)
    if resp.status_code == 200:
        app = resp.json()
        tools = app.get("model_config", {}).get("agent_mode", {}).get("tools", [])
        print(f"   Tools now: {len(tools)}")
        for t in tools:
            enabled = t.get("enabled", False)
            name = t.get("tool_name", "?")
            status = "ON" if enabled else "OFF"
            print(f"   - [{status}] {name}")

print("\nDone.")
