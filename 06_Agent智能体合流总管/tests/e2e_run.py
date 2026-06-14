"""Agent E2E Quick Test - 5 scenarios via Dify Chat API"""
import requests
import json
import sys

API_URL = "http://localhost/v1/chat-messages"
API_KEY = "app-jX3smW5hgad8jxsOhqp1osyo"

SCENARIOS = [
    ("你好，请问你能做什么？", "1-自我介绍"),
    ("员工年假有几天？", "2-知识库查询"),
    ("3号楼202房间电风扇坏了", "3-智能派单"),
    ("我要投诉！你们的服务太差了！", "4-人工转接"),
    ("帮我查一下3月份的财务数据", "5-财务查询"),
]


def test_agent(query, scenario_name):
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"场景: {scenario_name}")
    print(f"输入: {query}")
    print("-" * 60)

    try:
        resp = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "inputs": {},
                "query": query,
                "response_mode": "streaming",
                "user": "test-001",
            },
            timeout=120,
            stream=True,
        )

        full_answer = ""
        tool_calls = []
        for line in resp.iter_lines(decode_unicode=True):
            if line and line.startswith("data:"):
                data = json.loads(line[5:])
                if data.get("event") == "agent_message":
                    full_answer += data.get("answer", "")
                elif data.get("event") == "agent_thought":
                    if data.get("tool"):
                        tool_calls.append(data.get("tool", ""))
                elif data.get("event") == "message_end":
                    break

        print(f"调用工具: {tool_calls if tool_calls else '无'}")
        print(f"Agent回答: {full_answer[:500]}")
        return full_answer
    except Exception as e:
        print(f"ERROR: {e}")
        return None


if __name__ == "__main__":
    print("Dify Agent E2E Quick Test")
    print(f"API: {API_URL}")
    results = {}
    for query, name in SCENARIOS:
        answer = test_agent(query, name)
        results[name] = "OK" if answer else "FAIL"

    print("\n" + "=" * 60)
    print("测试结果汇总:")
    for name, status in results.items():
        print(f"  {name}: {status}")
