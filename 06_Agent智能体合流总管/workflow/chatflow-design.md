# Dify Chatflow 工作流设计文档

## 概述

本文档描述在 Dify v1.14.2 中构建 "Agent智能体合流总管" Chatflow 应用的完整节点编排方案。

**应用类型**: Chatflow  
**模型**: 项目三微调模型 (vLLM) / DeepSeek 备选  
**对话记忆**: 最近 10 轮  
**流式输出**: 开启

---

## 节点编排总览

```
[开始节点]
    ↓
[LLM 意图分类节点] ← 输出 intent: tool_query / tool_dispatch / knowledge / medical / human_handoff
    ↓
[条件分支节点 IF/ELSE]
    ├── intent == "tool_query"     → [参数检查节点 LLM]
    │                                    ├── 缺参数 → [追问节点] → 结束（等待下一轮）
    │                                    └── 齐全   → [工具调用: 数据查询] → [格式化回答 LLM]
    ├── intent == "tool_dispatch"  → [工具调用: 智能派单] → [格式化 LLM]
    ├── intent == "knowledge"      → [工具调用: 企业RAG知识库] → [基于文档回答 LLM]
    ├── intent == "medical"        → [工具调用: 医疗RAG知识库] → [基于医疗文档回答 + 免责声明]
    ├── intent == "human_handoff"  → [转人工话术模板]
    └── ELSE (兜底)               → [兜底回复模板]
```

---

## 节点详细设计

### 节点 1: 开始节点 (Start)

- **类型**: Start
- **变量**:
  - `sys.query` (string): 用户当前输入
  - `sys.conversation_id` (string): 会话ID
  - `sys.user_id` (string): 用户标识
- **系统提示词**: 引用 `prompts/system-prompt.md` 全文
- **对话轮次**: 设为 10

### 节点 2: LLM 意图分类节点 (LLM)

- **类型**: LLM
- **模型**: 微调模型 / DeepSeek
- **Temperature**: 0.1（低温度保证分类稳定）
- **Prompt**:

```
你是一个意图分类器。根据用户的最新消息和对话历史，判断用户意图。

对话历史：
{{#conversation.history#}}

用户最新消息：{{sys.query}}

请输出以下五个分类之一（只输出分类名，不要输出其他内容）：
- tool_query: 用户想查询或修改业务数据（财务报表、用户信息、物流状态、工单查询等）
- tool_dispatch: 用户描述了报修、投诉、设备故障等需要创建工单的场景
- knowledge: 用户咨询公司规章制度、政策流程、福利待遇等企业知识性问题
- medical: 用户咨询医疗健康、疾病症状、用药、科室等医学相关问题
- human_handoff: 用户明确要求人工服务，或情绪强烈需要人工安抚

如果无法判断，默认输出：tool_query

输出格式：{"intent": "分类名"}
```

- **输出变量**: `intent` (从 JSON 中提取 intent 字段)

### 节点 3: 条件分支节点 (IF/ELSE)

- **类型**: IF/ELSE
- **条件设置**:
  - IF 1: `intent` == `tool_query` → 连接节点 4a
  - IF 2: `intent` == `tool_dispatch` → 连接节点 4b
  - IF 3: `intent` == `knowledge` → 连接节点 4c
  - IF 4: `intent` == `medical` → 连接节点 4f（新增）
  - IF 5: `intent` == `human_handoff` → 连接节点 4d
  - ELSE → 连接节点 4e（兜底）

### 节点 4a: 参数检查与工具路由 (LLM)

- **类型**: LLM
- **Temperature**: 0.1
- **Prompt**:

```
你是参数提取器。根据用户消息和对话历史，判断用户需要调用哪个工具，以及参数是否齐全。

对话历史：
{{#conversation.history#}}

用户最新消息：{{sys.query}}

可选工具及所需参数：
1. finance_report_query（查询财务报表）: 需要 month（月份，格式 YYYY-MM）
2. finance_ai_summary（AI财务摘要）: 需要 month（月份，格式 YYYY-MM）
3. user_search（查询用户信息）: 需要 keyword（姓名/手机/邮箱关键词）
4. nlp_natural_query（大白话查库）: 需要 question（自然语言问题）

请输出 JSON：
- 如果参数齐全：{"status": "ready", "tool": "工具名", "params": {参数字典}}
- 如果参数缺失：{"status": "missing", "missing_param": "缺失参数名", "question": "追问话术"}

注意：从对话历史中提取已提供的参数，不要重复追问。
```

- **输出变量**: `param_check` (JSON 字符串)
- **后续分支**:
  - 如果 `status` == `ready` → 调用对应工具节点
  - 如果 `status` == `missing` → 追问节点

### 节点 4b: 智能派单工具调用

- **类型**: 工具 (Tool)
- **工具**: `smart_dispatch` (来自 project2-tools.json)
- **参数映射**: `text` = `{{sys.query}}`
- **输出变量**: `dispatch_result`

### 节点 4c: 企业RAG知识库查询

- **类型**: 工具 (Tool)
- **工具**: `rag_knowledge_query` (来自 project5-rag.json)
- **参数映射**: `question` = `{{sys.query}}`, `top_k` = `3`
- **输出变量**: `rag_result`

### 节点 4f: 医疗RAG知识库查询（新增）

- **类型**: 工具 (Tool)
- **工具**: `medical_chat_query` (来自 project4-medical-rag.json)
- **参数映射**: `question` = `{{sys.query}}`, `top_k` = `3`
- **输出变量**: `medical_result`
- **后续节点**: 医疗格式化 LLM（回答后追加免责声明）

### 节点 4d: 转人工话术

- **类型**: 模板转换 (Template)
- **模板**:

```
非常理解您的需求，我正在为您转接人工客服，请稍候片刻。

在等待期间，您也可以先简单描述一下您的问题，以便人工客服能够更快地为您服务。

如需紧急帮助，您也可以拨打我们的客服热线：400-XXX-XXXX。
```

### 节点 4e: 兜底回复

- **类型**: 模板转换 (Template)
- **模板**:

```
抱歉，我没有完全理解您的需求。您可以试试以下方式描述：

1. 📊 查询财务数据 — 如"帮我查一下3月份的财务报表"
2. 👤 查询用户信息 — 如"帮我查一下张三的联系方式"
3. 🔧 报修或投诉 — 如"3号楼202室空调坏了"
4. 📚 咨询公司政策 — 如"员工年假有几天"
5. 🏥 健康咨询 — 如"感冒了吃什么药"
6. 👩‍💼 转人工客服
```

### 节点 5: 格式化回答 (LLM)

- **类型**: LLM
- **Temperature**: 0.3
- **Prompt**:

```
你是企业客服助手。请将以下工具返回的数据转换为用户友好的自然语言回答。

用户问题：{{sys.query}}
工具返回数据：{{tool_result}}

要求：
1. 用自然、专业的中文回答
2. 关键数据（金额、日期、单号、姓名）用 **加粗** 显示
3. 数据量大时做摘要总结
4. 不要输出 JSON 或技术格式
5. 保持简洁，不超过200字
```

### 节点 5f: 医疗格式化回答 (LLM)（新增）

- **类型**: LLM
- **Temperature**: 0.3
- **Prompt**:

```
你是医疗健康咨询助手。请基于医疗知识库的返回内容，为用户提供健康信息。

用户问题：{{sys.query}}
知识库返回：{{medical_result}}

要求：
1. 仅基于召回的文档内容回答，不添加未召回的信息
2. 回答清晰易懂
3. 必须在回答末尾加上免责声明："\n\n> ⚠️ 以上信息仅供参考，如有不适请及时就医。"
4. 如果置信度较低，建议用户咨询专业医生
5. 不做诊断，不推荐具体处方
```

### 节点 6: 追问节点 (Template)

- **类型**: 模板转换 (Template)
- **模板**: `{{param_check.question}}` （使用参数检查节点的追问话术）

---

## 工具配置汇总

| 工具名称 | 来源文件 | 端口 | API 认证 | 超时 |
|---------|---------|------|---------|------|
| finance_report_query | project1-tools.json | 9001 | Bearer JWT Token | 30s |
| finance_ai_summary | project1-tools.json | 9001 | Bearer JWT Token | 60s |
| user_search | project1-tools.json | 9001 | Bearer JWT Token | 30s |
| smart_dispatch | project2-tools.json | 9002 | 无 | 60s |
| nlp_natural_query | project2-tools.json | 9002 | 无 | 60s |
| medical_chat_query | project4-medical-rag.json | 8082 | 无 | 60s |
| rag_knowledge_query | project5-rag.json | 8083 | 无 | 60s |

---

## 变量传递图

```
sys.query ──────────→ [意图分类] → intent
                             ↓
intent ────────────→ [条件分支]
                             ↓
sys.query + history → [参数检查] → param_check (tool + params)
                             ↓
param_check.params → [工具调用] → tool_result
                             ↓
sys.query + tool_result → [格式化回答] → 最终输出
```

---

## Dify 画布配置步骤

1. 创建新应用 → 选择 "Chatflow"
2. 在开始节点配置系统提示词（粘贴 system-prompt.md 内容）
3. 设置对话轮次为 10
4. 按上述节点顺序逐一添加节点
5. 连接节点间的条件分支线
6. 导入 OpenAPI 工具（在工具管理页面）
7. 在工具调用节点选择对应工具
8. 发布应用
9. 获取 API Key 用于前端嵌入

---

## 测试要点

- 意图分类准确性：确保五种意图能正确分类
- 参数补全：缺参数时追问，不缺参数时直接调用
- 多轮对话：第1轮追问的参数在第2轮能被正确提取
- 医疗路由：医疗问题走医疗知识库，非企业知识库
- 医疗免责声明：回答末尾必须有免责提示
- 兜底回复：无法识别意图时输出友好提示
- 流式输出：逐字显示效果正常
