# 02_政企物流智能化转化

> 第二阶段——让传统业务接口具备"听懂大白话"的能力

---

## 项目架构

```
02_政企物流智能化转化/
├── sql/                        # 数据库初始化脚本
│   └── init.sql
├── backend/                    # SpringBoot 3 后端
│   ├── pom.xml
│   ├── Dockerfile
│   └── src/main/java/com/logistics/smart/
│       ├── SmartLogisticsApplication.java
│       ├── config/             # 配置类
│       ├── controller/         # REST 接口
│       ├── dto/                # 数据传输对象
│       ├── entity/             # 实体类
│       ├── filter/             # 安全过滤器
│       ├── mapper/             # MyBatis-Plus Mapper
│       ├── service/            # 业务逻辑
│       └── websocket/          # WebSocket 推送
├── frontend/                   # Vue 3 前端
│   ├── package.json
│   ├── Dockerfile
│   ├── nginx.conf
│   └── src/
│       ├── App.vue
│       ├── api/                # 接口层
│       ├── composables/        # WebSocket composable
│       ├── router/
│       └── views/              # 页面
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 后端框架 | Spring Boot 3.2 + Java 17 |
| AI 能力 | LangChain4j 0.31 (OpenAI 兼容) |
| 持久层 | MyBatis-Plus 3.5 + MySQL 8.0 |
| 缓存 | Redis 7 |
| 实时通信 | Spring WebSocket |
| 前端框架 | Vue 3 + ElementPlus |
| 构建工具 | Maven / Vite |
| 部署 | Docker + Docker Compose |

---

## 快速启动

### 方式一：Docker Compose（推荐）

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 OPENAI_API_KEY

# 2. 一键启动
docker-compose up -d

# 访问
# 前端：http://localhost
# 后端：http://localhost:9002
```

### 方式二：本地开发

```bash
# 1. 初始化数据库
mysql -u root -p < sql/init.sql

# 2. 启动 Redis
redis-server

# 3. 启动后端
cd backend
# 设置环境变量
export OPENAI_API_KEY=sk-your-key
export OPENAI_BASE_URL=https://api.openai.com/v1
mvn spring-boot:run

# 4. 启动前端
cd frontend
npm install
npm run dev
# 访问 http://localhost:5174
```

---

## 接口文档

### 1. 口语化智能派单

**POST** `/api/nlp/dispatch`

接收口语化文本，大模型自动提取信息并创建工单。

**请求体：**
```json
{
    "text": "刚才5点左右，3号楼202房间的张大爷说电风扇坏了，天气太热了，我已经拿了冰块过去，通知了维修部小王赶紧去看看。"
}
```

**响应：**
```json
{
    "code": 200,
    "message": "工单创建成功",
    "data": {
        "id": 5,
        "location": "3号楼202房间",
        "clientName": "张大爷",
        "issue": "电风扇损坏",
        "actionsTaken": ["已送冰块降温"],
        "assignedTo": "维修部小王",
        "priority": "URGENT",
        "status": "PENDING",
        "createTime": "2024-01-15 17:30:00"
    }
}
```

---

### 2. 大白话智能查库

**POST** `/api/nlp/query`

自然语言问题 → 自动生成 SQL → 执行并返回结果。

**请求体：**
```json
{
    "question": "帮我查一下上个月所有紧急工单"
}
```

**响应：**
```json
{
    "code": 200,
    "message": "查询成功",
    "data": {
        "columns": ["id", "location", "client_name", "issue", "priority", "status", "create_time"],
        "rows": [
            {"id": 1, "location": "3号楼202房间", "client_name": "张大爷", "issue": "电风扇损坏", "priority": "URGENT", "status": "PROCESSING", "create_time": "2024-01-15 17:30:00"}
        ],
        "rowCount": 1,
        "sql": "SELECT * FROM t_work_order WHERE priority = 'URGENT' AND create_time >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)"
    }
}
```

---

### 3. 工单列表

**GET** `/api/work-order/list?page=1&size=10&status=PENDING&priority=URGENT`

支持分页、状态筛选、优先级筛选。

---

### 4. 工单详情

**GET** `/api/work-order/{id}`

---

### 5. 更新工单状态

**PUT** `/api/work-order/status`

```json
{
    "id": 1,
    "status": "PROCESSING"
}
```

状态流转规则：`PENDING → PROCESSING → DONE`（不可回退）

---

### 6. 查询历史

**GET** `/api/nlp/query/history?limit=20`

---

### 7. WebSocket 实时通知

**连接地址：** `ws://localhost:9002/ws/notification`

**通知类型：**
- `NEW_WORK_ORDER` — 新工单创建
- `STATUS_CHANGE` — 工单状态变更

**消息格式：**
```json
{
    "type": "NEW_WORK_ORDER",
    "data": { ...工单对象 },
    "time": "2024-01-15T17:30:00"
}
```

---

## NLP 测试用例

### 口语化派单测试

| 输入文本 | 预期提取 |
|---------|---------|
| 刚才5点左右，3号楼202房间的张大爷说电风扇坏了，天气太热了，我已经拿了冰块过去，通知了维修部小王赶紧去看看。 | location: 3号楼202房间, client: 张大爷, issue: 电风扇损坏, priority: URGENT |
| 1号楼大厅的空调不制冷了，前台反映好几天了，让维修部小陈有空去修一下。 | location: 1号楼大厅, issue: 空调不制冷, assigned: 维修部小陈, priority: NORMAL |
| 7号楼303赵先生门锁坏了打不开门，我已经安排他临时换房，让老赵赶紧来修。 | location: 7号楼303室, client: 赵先生, issue: 门锁故障, priority: URGENT |

### 大白话查询测试

| 自然语言问题 | 预期 SQL 方向 |
|-------------|-------------|
| 帮我查一下上个月所有紧急工单 | SELECT * FROM t_work_order WHERE priority = 'URGENT' AND create_time >= ... |
| 最近三天新建了多少工单 | SELECT COUNT(*) FROM t_work_order WHERE create_time >= DATE_SUB(NOW(), INTERVAL 3 DAY) |
| 哪些工单还没处理 | SELECT * FROM t_work_order WHERE status = 'PENDING' |
| 维修部小王一共处理了多少工单 | SELECT COUNT(*) FROM t_work_order WHERE assigned_to LIKE '%小王%' AND status = 'DONE' |

---

## 安全设计

1. **输入过滤**：正则拦截敏感词、空白输入、纯特殊字符
2. **SQL 安全**：只允许 SELECT，拦截 DROP/DELETE/UPDATE/INSERT/ALTER 等危险操作
3. **CORS**：后端统一配置跨域策略
4. **WebSocket**：心跳保活 + 自动重连

---

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API Key | `sk-your-api-key-here` |
| `OPENAI_BASE_URL` | API Base URL（兼容其他服务） | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | 模型名称 | `gpt-4o` |

---

## 开发工具

- **IntelliJ IDEA**：后端开发
- **Redis Insight**：Redis 可视化管理
- **Docker Desktop**：容器化部署
- **VS Code**：前端开发（可选）
