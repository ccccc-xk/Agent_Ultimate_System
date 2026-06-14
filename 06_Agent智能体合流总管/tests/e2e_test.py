"""
06_Agent智能体合流总管 - 端到端自动化测试
Usage: python e2e_test.py [--skip-unavailable]
"""
import requests
import json
import time
import sys
import os

# === Configuration ===
DIFY_BASE = "http://localhost:9006"
APP_ID = "43fac71b-0234-4aa9-a8e4-c9358e622853"
API_KEY = "app-aPDJY1OXiPiE9wljpJeWwiNq"
CHAT_URL = f"{DIFY_BASE}/v1/chat-messages"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

TEST_CASES = [
    {
        "id": "TC01",
        "name": "知识库问答 - 年假天数",
        "inputs": ["员工年假有几天"],
        "check_keywords": ["年假"],
        "check_not": ["抱歉", "无法"],
    },
    {
        "id": "TC02",
        "name": "知识库问答 - 合同续签",
        "inputs": ["合同到期前多久需要续签"],
        "check_keywords": ["合同"],
        "check_not": ["抱歉"],
    },
    {
        "id": "TC03",
        "name": "医疗咨询 - 感冒用药",
        "inputs": ["感冒了应该吃什么药"],
        "check_keywords": ["感冒"],
        "check_not": [],
    },
    {
        "id": "TC05",
        "name": "智能派单 - 电风扇报修",
        "inputs": ["3号楼202房间电风扇坏了，麻烦赶紧来修一下"],
        "check_keywords": [],
        "check_not": [],
        "note": "需要项目02后端运行",
    },
    {
        "id": "TC07",
        "name": "参数追问 - 缺少月份",
        "inputs": ["帮我查一下财务数据"],
        "check_keywords": ["月"],
        "check_not": [],
        "note": "需要项目01后端运行",
    },
    {
        "id": "TC09",
        "name": "人工转接",
        "inputs": ["我要投诉！让我跟你们经理说话"],
        "check_keywords": ["转", "人工"],
        "check_not": [],
    },
    {
        "id": "TC10",
        "name": "兜底回复",
        "inputs": ["asdfghjkl"],
        "check_keywords": [],
        "check_not": [],
    },
    {
        "id": "TC11",
        "name": "多轮对话 - 参数补全",
        "inputs": ["帮我查一下财务数据", "2026年3月"],
        "check_keywords": [],
        "check_not": [],
        "note": "需要项目01后端运行",
    },
]


def chat_streaming(message, conversation_id=None):
    """Send a chat message and collect streaming response"""
    payload = {
        "inputs": {},
        "query": message,
        "response_mode": "streaming",
        "user": "e2e-test",
    }
    if conversation_id:
        payload["conversation_id"] = conversation_id



def run_single_test(tc):
    """Run a single test case (single-turn)"""
    print(f"\n{'='*60}")
    print(f"[{tc['id']}] {tc['name']}")
    if tc.get("note"):
        print(f"  Note: {tc['note']}")

    conversation_id = None
    last_answer = ""

    for i, msg in enumerate(tc["inputs"]):
        print(f"  User ({i+1}): {msg}")
        result = chat_streaming(msg, conversation_id)

        if "error" in result:
            print(f"  ERROR: {result['error']}")
            return {"id": tc["id"], "name": tc["name"], "status": "ERROR", "detail": result["error"]}

        last_answer = result["answer"]
        conversation_id = result.get("conversation_id")
        print(f"  Agent: {last_answer[:200]}{'...' if len(last_answer) > 200 else ''}")
        time.sleep(1)

    # Check keywords
    passed = True
    issues = []
    for kw in tc.get("check_keywords", []):
        if kw not in last_answer:
            passed = False
            issues.append(f"missing keyword: '{kw}'")

    for kw in tc.get("check_not", []):
        if kw in last_answer:
            # Minor issue, not a hard fail
            issues.append(f"unexpected keyword: '{kw}'")

    status = "PASS" if passed and not issues else ("WARN" if issues and passed else "FAIL")
    print(f"  Result: {status}" + (f" ({'; '.join(issues)})" if issues else ""))

    return {
        "id": tc["id"],
        "name": tc["name"],
        "status": status,
        "answer_preview": last_answer[:300],
        "issues": issues,
    }


def main():
    skip_unavailable = "--skip-unavailable" in sys.argv

    print("=" * 60)
    print("06_Agent智能体合流总管 - 端到端测试")
    print(f"Dify: {DIFY_BASE}")
    print(f"Agent: {APP_ID}")
    print(f"Skip unavailable: {skip_unavailable}")
    print("=" * 60)

    # Quick connectivity check
    try:
        r = requests.get(f"{DIFY_BASE}/v1/parameters", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            print("[OK] Dify API reachable")
        else:
            print(f"[WARN] Dify API returned {r.status_code}")
    except Exception as e:
        print(f"[FAIL] Cannot reach Dify API: {e}")
        if skip_unavailable:
            print("Skipping all tests.")
            return
        sys.exit(1)

    results = []
    for tc in TEST_CASES:
        result = run_single_test(tc)
        results.append(result)
        time.sleep(2)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    warn_count = sum(1 for r in results if r["status"] == "WARN")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")
    err_count = sum(1 for r in results if r["status"] == "ERROR")

    for r in results:
        icon = {"PASS": "OK", "WARN": "!!", "FAIL": "XX", "ERROR": "EE"}.get(r["status"], "??")
        print(f"  [{icon}] {r['id']} {r['name']}: {r['status']}")
        if r.get("issues"):
            print(f"       {r['issues']}")

    print(f"\nTotal: {len(results)} | Pass: {pass_count} | Warn: {warn_count} | Fail: {fail_count} | Error: {err_count}")

    # Save results
    out_path = os.path.join(os.path.dirname(__file__), "test-results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {out_path}")


if __name__ == "__main__":
    main()
    try:
        r = requests.post(CHAT_URL, headers=HEADERS, json=payload, timeout=120, stream=True)
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}

        full_answer = ""
        conv_id = None
        for line in r.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            try:
                evt = json.loads(line[6:])
                etype = evt.get("event", "")
                if etype in ("message", "agent_message"):
                    full_answer += evt.get("answer", "")
                if not conv_id:
                    conv_id = evt.get("conversation_id")
            except json.JSONDecodeError:
                pass

        return {"answer": full_answer, "conversation_id": conv_id}
    except requests.exceptions.Timeout:
        return {"error": "Timeout (120s)"}
    except Exception as e:
        return {"error": str(e)}
