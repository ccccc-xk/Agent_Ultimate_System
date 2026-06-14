"""
Dify Console API: Upload knowledge docs + configure Agent features
"""
import requests
import json
import time
import os
import base64

BASE = "http://localhost:9006/console/api"
EMAIL = "2257302877@qq.com"
PW = "pty666666"
APP_ID = "43fac71b-0234-4aa9-a8e4-c9358e622853"
DS_ID = "87ef9c2e-e78e-4715-aa55-e12568474a8e"
DOCS = r"D:\Codex-project\Agent_Ultimate_System\05_企业级高级RAG知识库\backend\data"
FILES = [
    "\u516c\u53f8\u89c4\u7ae0\u5236\u5ea6\u624b\u518c.md",
    "\u533b\u9662\u79d1\u5ba4\u4ecb\u7ecd.md",
    "\u5408\u540c\u7ba1\u7406\u89c4\u8303.md",
    "\u5e38\u7528\u836f\u7269\u8bf4\u660e.md",
    "\u5e38\u89c1\u75be\u75c5\u8bca\u7597\u6307\u5357.md",
]
OPENING = (
    "\u60a8\u597d\uff01\u6211\u662fAI\u667a\u80fd\u4f01\u4e1a\u5ba2\u670d\u603b\u7ba1\uff0c\u53ef\u4ee5\u5e2e\u60a8\uff1a\n\n"
    "- \u67e5\u8be2\u8d22\u52a1\u6570\u636e\u3001\u5458\u5de5\u4fe1\u606f\n"
    "- \u5904\u7406\u62a5\u4fee\u6295\u8bc9\uff0c\u81ea\u52a8\u521b\u5efa\u5de5\u5355\n"
    "- \u89e3\u7b54\u516c\u53f8\u89c4\u7ae0\u5236\u5ea6\u3001\u5408\u540c\u7ba1\u7406\u7b49\u653f\u7b56\u95ee\u9898\n"
    "- \u63d0\u4f9b\u533b\u7597\u5065\u5eb7\u54a8\u8be2\n"
    "- \u8f6c\u63a5\u4eba\u5de5\u5ba2\u670d\n\n"
    "\u8bf7\u95ee\u6709\u4ec0\u4e48\u53ef\u4ee5\u5e2e\u60a8\u7684\uff1f"
)

def csrf(s):
    for c in s.cookies:
        if c.name == "csrf_token":
            return c.value
    return ""

def main():
    print("=== Dify Knowledge & Agent Setup ===")
    s = requests.Session()

    # Login
    ep = base64.b64encode(PW.encode()).decode()
    r = s.post(f"{BASE}/login", json={"email": EMAIL, "password": ep})
    if r.status_code != 200:
        print(f"Login FAIL: {r.status_code} {r.text[:200]}")
        return
    tk = csrf(s)
    print(f"[1] Login OK, csrf={tk[:16]}...")

    # Upload files then create documents
    print("\n[2] Uploading files & creating documents...")
    ok_count = 0
    for fname in FILES:
        fp = os.path.join(DOCS, fname)
        if not os.path.exists(fp):
            print(f"  SKIP: {fname}")
            continue

        # Step 1: upload file
        with open(fp, "rb") as f:
            r1 = s.post(
                f"{BASE}/files/upload",
                files={"file": (fname, f, "text/markdown")},
                data={"source": "datasets"},
                headers={"X-CSRF-Token": tk},
            )
        if r1.status_code not in (200, 201):
            print(f"  [FAIL-upload] {fname}: {r1.status_code} {r1.text[:150]}")
            continue
        fid = r1.json().get("id", "")
        print(f"  File OK: {fname} -> {fid[:12]}")

        # Step 2: create document from file
        r2 = s.post(
            f"{BASE}/datasets/{DS_ID}/documents",
            json={
                "indexing_technique": "economy",
                "data_source": {
                    "info_list": {
                        "data_source_type": "upload_file",
                        "file_info_list": {"file_ids": [fid]},
                    }
                },
                "process_rule": {"mode": "automatic"},
                "doc_form": "text_model",
                "doc_language": "Chinese",
            },
            headers={"X-CSRF-Token": tk, "Content-Type": "application/json"},
        )
        if r2.status_code in (200, 201):
            print(f"  Doc OK: {fname}")
            ok_count += 1
        else:
            print(f"  [FAIL-doc] {fname}: {r2.status_code} {r2.text[:150]}")
        time.sleep(2)

    # Wait for indexing
    if ok_count > 0:
        print(f"\n[3] Waiting for indexing ({ok_count} docs)...")
        for i in range(30):
            r = s.get(
                f"{BASE}/datasets/{DS_ID}/documents",
                headers={"X-CSRF-Token": tk},
                params={"page": 1, "limit": 20},
            )
            if r.status_code == 200:
                docs = r.json().get("data", [])
                pending = [
                    d.get("name", "?")
                    for d in docs
                    if d.get("indexing_status") not in ("completed", "available")
                ]
                if not pending and docs:
                    print(f"  All {len(docs)} docs indexed!")
                    break
                if pending:
                    print(f"  Poll {i+1}: {len(pending)} still indexing...")
            time.sleep(5)
        else:
            print("  Timeout (150s)")

    # Update Agent model config (dataset binding)
    print("\n[4] Binding dataset to Agent...")
    r = s.get(f"{BASE}/apps/{APP_ID}", headers={"X-CSRF-Token": tk})
    if r.status_code == 200:
        mc = r.json().get("model_config", {})
        mc["dataset_configs"] = {
            "datasets": {
                "datasets": [{"dataset": {"id": DS_ID, "name": "\u4f01\u4e1a\u77e5\u8bc6\u5e93"}, "id": DS_ID}]
            },
            "retrieval_model": "multiple",
        }
        r2 = s.post(
            f"{BASE}/apps/{APP_ID}/model-config",
            json=mc,
            headers={"X-CSRF-Token": tk, "Content-Type": "application/json"},
        )
        print(f"  Model config: {r2.status_code}")

    # Update app features (opening statement, etc)
    print("\n[5] Enabling features...")
    r = s.get(f"{BASE}/apps/{APP_ID}", headers={"X-CSRF-Token": tk})
    if r.status_code == 200:
        app = r.json()
        r3 = s.put(
            f"{BASE}/apps/{APP_ID}",
            json={
                "name": app.get("name", "\u667a\u80fd\u5ba2\u670d\u603b\u7ba1"),
                "icon": app.get("icon"),
                "icon_background": app.get("icon_background"),
                "opening_statement": OPENING,
                "suggested_questions_after_answer": {"enabled": True},
                "retriever_resource": {"enabled": True},
                "annotation_reply": {"enabled": True, "id": None},
            },
            headers={"X-CSRF-Token": tk, "Content-Type": "application/json"},
        )
        print(f"  Features: {r3.status_code}")
        if r3.status_code != 200:
            print(f"    {r3.text[:200]}")

    # Verify
    print("\n[Verify]")
    r = s.get(f"{BASE}/apps/{APP_ID}", headers={"X-CSRF-Token": tk})
    if r.status_code == 200:
        mc = r.json().get("model_config", {})
        print(f"  Opening: {'YES' if mc.get('opening_statement') else 'NO'}")
        ds = mc.get("dataset_configs", {}).get("datasets", {}).get("datasets", [])
        print(f"  Datasets: {len(ds)}")
        for d in ds:
            print(f"    - {d.get('dataset', {}).get('name', '?')}")

    print(f"\n  Knowledge: http://localhost:9006/datasets/{DS_ID}/documents")
    print(f"  Agent:     http://localhost:9006/app/{APP_ID}/configuration")
    print("Done!")

if __name__ == "__main__":
    main()
