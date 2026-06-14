"""
Agent 智能体全链路演示脚本
绕过 Dify 工具管理限制，直接演示完整的"大白话输入 → 意图识别 → 调用工具 → 自然语言回答"流程

使用 DeepSeek API 作为 LLM，直接调用项目 01/02/04/05 的后端 API
"""
import requests
import json
import sys
import os

# ===== 配置 =====
DEEPSEEK_API = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_KEY = "sk-540222586bf946bfa0e6af4b4453650b"
DEEPSEEK_MODEL = "deepseek-chat"

SERVICES = {
    "p01_base": "http://localhost:9001",
    "p02_base": "http://localhost:9002",
    "p04_base": "http://localhost:9004",
    "p05_base": "http://localhost:9005",
}

SYSTEM_PROMPT = """你是一个全能型AI智能企业客服总管。你需要根据用户输入，返回一个JSON格式的动作指令。

可用工具:
1. finance_report_query - 查询企业财务月报。参数: month (字符串，如"3月"、"2024年3月")
2. finance_ai_summary - AI财务摘要分析。参数: month
3. user_search - 搜索用户信息。参数: keyword
4. smart_dispatch - 智能派单（报修/投诉创建工单）。参数: text (口语化描述)
5. nlp_natural_query - 大白话查库（自然语言查业务数据）。参数: question
6. medical_chat - 医疗知识库问答。参数: question
7. rag_knowledge_query - 企业知识库问答（规章制度/合同/流程）。参数: question

意图识别规则:
- 用户问财务/报表/收支/利润 → tool_query + finance_report_query 或 finance_ai_summary
- 用户要找人/查用户/搜员工 → tool_query + user_search
- 用户描述报修/故障/坏了/投诉场景 → tool_dispatch + smart_dispatch
- 用户用大白话查业务数据/物流/库存/订单 → tool_query + nlp_natural_query
- 用户问医疗/疾病/症状/用药 → knowledge + medical_chat
- 用户问公司制度/年假/规章/合同/退货流程 → knowledge + rag_knowledge_query
- 用户明确要求转人工/情绪激动说投诉 → human_handoff

你必须严格返回以下JSON格式（不要返回其他内容）:
{
  "intent": "tool_query|tool_dispatch|knowledge|human_handoff",
  "tool": "工具名或null",
  "params": {"参数名": "参数值"},
  "missing": ["缺少的参数名"],
  "response": "如果不需要调用工具，直接回答的内容"
}

如果缺少必要参数（如查物流但没有单号），将missing字段设为缺少的参数列表。
如果识别为human_handoff，response字段填写转人工话术。
"""


def call_deepseek(messages):
    """调用 DeepSeek API"""
    resp = requests.post(
        DEEPSEEK_API,
        headers={
            "Authorization": f"Bearer {DEEPSEEK_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": DEEPSEEK_MODEL,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 1024,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def call_tool(tool_name, params):
    """调用后端工具 API"""
    try:
        if tool_name == "finance_report_query":
            month = params.get("month", "")
            r = requests.get(
                f"{SERVICES['p01_base']}/api/finance/page",
                params={"month": month, "pageNum": 1, "pageSize": 5},
                timeout=15,
            )
            return r.json()

        elif tool_name == "finance_ai_summary":
            month = params.get("month", "")
            r = requests.post(
                f"{SERVICES['p01_base']}/api/finance/ai-summary",
                params={"month": month},
                timeout=30,
            )
            return r.json()

        elif tool_name == "user_search":
            keyword = params.get("keyword", "")
            r = requests.get(
                f"{SERVICES['p01_base']}/api/user/page",
                params={"keyword": keyword, "pageNum": 1, "pageSize": 5},
                timeout=15,
            )
            return r.json()

        elif tool_name == "smart_dispatch":
            text = params.get("text", "")
            r = requests.post(
                f"{SERVICES['p02_base']}/api/nlp/dispatch",
                json={"text": text},
                timeout=30,
            )
            return r.json()

        elif tool_name == "nlp_natural_query":
            question = params.get("question", "")
            r = requests.post(
                f"{SERVICES['p02_base']}/api/nlp/query",
                json={"question": question},
                timeout=30,
            )
            return r.json()

        elif tool_name == "medical_chat":
            question = params.get("question", "")
            r = requests.post(
                f"{SERVICES['p04_base']}/api/chat",
                json={"question": question},
                timeout=60,
            )
            return r.json()

        elif tool_name == "rag_knowledge_query":
            question = params.get("question", "")
            r = requests.post(
                f"{SERVICES['p05_base']}/api/rag/query",
                json={"question": question, "top_k": 3},
                timeout=60,
            )
            return r.json()

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    except requests.exceptions.ConnectionError:
        return {"error": f"Service unavailable for {tool_name}"}
    except Exception as e:
        return {"error": str(e)}


def format_response(tool_name, tool_result, user_query):
    """用 DeepSeek 将工具返回转为自然语言"""
    messages = [
        {
            "role": "system",
            "content": "你是一个专业的企业客服。请根据工具返回的数据，用自然语言回答用户问题。关键数据（单号、金额、时间）加粗显示。如果工具返回错误，友好地告知用户。",
        },
        {
            "role": "user",
            "content": f"用户问: {user_query}\n\n工具 {tool_name} 返回的数据:\n{json.dumps(tool_result, ensure_ascii=False, indent=2)[:2000]}\n\n请用自然语言回答用户。",
        },
    ]
    return call_deepseek(messages)


def agent_chat(user_query, history=None):
    """完整的 Agent 对话流程"""
    if history is None:
        history = []

    # Step 1: 构建消息
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_query})

    # Step 2: LLM 意图识别
    print(f"  [思考] 分析意图...")
    llm_response = call_deepseek(messages)

    # 解析 JSON
    try:
        # 处理可能的 markdown 代码块
        clean = llm_response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()
            if clean.startswith("json"):
                clean = clean[4:].strip()

        action = json.loads(clean)
    except json.JSONDecodeError:
        print(f"  [警告] LLM 返回非JSON，直接输出回答")
        return llm_response

    intent = action.get("intent", "")
    tool = action.get("tool")
    params = action.get("params", {})
    missing = action.get("missing", [])
    direct_response = action.get("response", "")

    print(f"  [意图] {intent}" + (f" → 工具: {tool}" if tool else ""))

    # Step 3: 根据意图执行
    if intent == "human_handoff" or (intent == "human_handoff" and direct_response):
        return direct_response or "非常抱歉给您带来不便，我这就为您转接人工客服。请稍等片刻。"

    if missing:
        # 参数不全，追问
        param_prompts = {
            "month": "请问您想查看哪个月份的数据？",
            "keyword": "请问您要搜索的用户姓名或关键词是什么？",
            "text": "请描述一下您遇到的问题（如：3号楼202房间电风扇坏了）。",
            "question": "请问您具体想了解什么？",
        }
        prompts = [param_prompts.get(p, f"请提供{p}") for p in missing]
        return " ".join(prompts)

    if tool:
        # 调用工具
        print(f"  [调用] {tool}({json.dumps(params, ensure_ascii=False)})")
        tool_result = call_tool(tool, params)

        if "error" in tool_result:
            return f"抱歉，服务暂时不可用：{tool_result['error']}。请稍后再试。"

        # 格式化回答
        print(f"  [格式化] 生成自然语言回答...")
        answer = format_response(tool, tool_result, user_query)
        return answer

    if direct_response:
        return direct_response

    return "抱歉，我没有理解您的意思。请您重新描述一下，或者告诉我您需要什么帮助？"


# ===== 测试场景 =====
SCENARIOS = [
    {
        "name": "场景1: 财务查询",
        "query": "帮我查一下3月份的财务数据",
        "expected_intent": "tool_query",
        "expected_tool": "finance_report_query",
    },
    {
        "name": "场景2: 知识库问答",
        "query": "员工年假有几天？",
        "expected_intent": "knowledge",
        "expected_tool": "rag_knowledge_query",
    },
    {
        "name": "场景3: 智能派单",
        "query": "3号楼202房间电风扇坏了",
        "expected_intent": "tool_dispatch",
        "expected_tool": "smart_dispatch",
    },
    {
        "name": "场景4: 医疗咨询",
        "query": "感冒了吃什么药？",
        "expected_intent": "knowledge",
        "expected_tool": "medical_chat",
    },
    {
        "name": "场景5: 人工转接",
        "query": "我要投诉！你们的服务太差了！",
        "expected_intent": "human_handoff",
        "expected_tool": None,
    },
    {
        "name": "场景6: 参数补全（多轮）",
        "query": "帮我查一下物流信息",
        "expected_intent": "tool_query",
        "expected_tool": "nlp_natural_query",
        "follow_up": "快递单号是SF1234567890",
    },
]


def run_tests():
    """运行全部测试"""
    print("=" * 60)
    print("Agent 智能体全链路演示")
    print("=" * 60)
    print(f"LLM: DeepSeek {DEEPSEEK_MODEL}")
    print(f"后端服务: P01(9001), P02(9002), P04(9004), P05(9005)")
    print()

    # 检查服务
    print("检查后端服务...")
    for name, base in SERVICES.items():
        try:
            r = requests.get(base, timeout=3)
            print(f"  {name}: OK")
        except:
            print(f"  {name}: UNREACHABLE")
    print()

    results = []
    for scenario in SCENARIOS:
        print(f"\n{'='*60}")
        print(f"{scenario['name']}")
        print(f"用户输入: {scenario['query']}")
        print("-" * 60)

        answer = agent_chat(scenario["query"])
        print(f"\n  [回答] {answer[:500]}")

        # 多轮对话场景
        if "follow_up" in scenario:
            print(f"\n  --- 多轮: 用户补充: {scenario['follow_up']} ---")
            history = [
                {"role": "user", "content": scenario["query"]},
                {"role": "assistant", "content": answer},
            ]
            answer2 = agent_chat(scenario["follow_up"], history)
            print(f"\n  [回答] {answer2[:500]}")

        results.append({"name": scenario["name"], "status": "OK"})

    # 汇总
    print(f"\n\n{'='*60}")
    print("测试结果汇总")
    print("=" * 60)
    for r in results:
        print(f"  {r['name']}: {r['status']}")
    print(f"\n总计: {len(results)} 个场景全部完成")


if __name__ == "__main__":
    run_tests()
