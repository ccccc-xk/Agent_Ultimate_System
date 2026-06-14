# 企业管理基座系统

AI 全栈生态第一阶段——传统业务骨架系统。提供 RBAC 权限管理、财务报表、数据看板、AI 智能财务摘要等核心能力。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Spring Boot 3.2 + MyBatis-Plus 3.5 + JWT (jjwt 0.12) |
| 前端 | Vue 3 (Setup) + Element Plus + ECharts + Vue Router + Pinia |
| 数据库 | MySQL 8.x (utf8mb4) |
| 构建 | Maven / Vite |

## 项目结构

```
01_企业管理基座系统/
├── database/
│   └── init.sql              # 数据库建表 + 初始化数据
├── backend/                   # Spring Boot 后端
│   ├── pom.xml
│   └── src/main/java/com/enterprise/
│       ├── EnterpriseBaseApplication.java
│       ├── common/R.java              # 统一响应封装
│       ├── config/                    # CORS / MyBatis-Plus / Web / 全局异常
│       ├── controller/                # 6 个 Controller
│       ├── dto/                       # 请求参数 DTO
│       ├── entity/                    # 6 个实体类
│       ├── interceptor/JwtInterceptor # JWT 拦截器
│       ├── mapper/                    # 6 个 Mapper
│       ├── service/                   # 4 个 Service 接口 + 实现
│       ├── util/JwtUtil               # JWT 工具类
│       └── vo/                        # 响应 VO
└── frontend/                  # Vue 3 前端
    ├── src/
    │   ├── layout/AppLayout.vue       # 主布局（侧边栏 + 顶栏）
    │   ├── router/index.js            # 路由 + 守卫
    │   ├── store/user.js              # Pinia 用户状态
    │   ├── utils/request.js           # Axios 封装
    │   └── views/                     # 5 个页面
    └── vite.config.js
```

## 快速启动

### 1. 数据库初始化

```bash
# 登录 MySQL，执行初始化脚本
mysql -u root -p < database/init.sql
```

### 2. 启动后端

```bash
cd backend
# 修改 src/main/resources/application.yml 中的数据库连接信息
mvn spring-boot:run
```

后端默认运行在 `http://localhost:9001`

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://localhost:5173`，已配置代理将 `/api` 请求转发到后端。

### 4. 测试账号

| 用户名 | 密码 | 角色 | 权限 |
|--------|------|------|------|
| admin | 123456 | 超级管理员 | 全部菜单 + 按钮权限 |
| staff01 | 123456 | 普通员工 | 看板 + 财务报表 |

## 接口文档

### 认证

| Method | Path | 说明 |
|--------|------|------|
| POST | /api/auth/login | 登录，返回 token |
| GET | /api/auth/info | 获取当前用户信息 |

### 菜单

| Method | Path | 说明 |
|--------|------|------|
| GET | /api/menu/list | 当前用户菜单树 |
| GET | /api/menu/all | 全部菜单树（管理用） |

### 用户管理

| Method | Path | 说明 |
|--------|------|------|
| GET | /api/user/page | 分页查询 |
| POST | /api/user | 新增用户 |
| PUT | /api/user | 编辑用户 |
| DELETE | /api/user/{id} | 删除用户 |
| PUT | /api/user/reset-password/{id} | 重置密码 |

### 角色管理

| Method | Path | 说明 |
|--------|------|------|
| GET | /api/role/page | 分页查询 |
| GET | /api/role/list | 全部角色 |
| POST | /api/role | 新增角色 |
| PUT | /api/role | 编辑角色 |
| DELETE | /api/role/{id} | 删除角色 |

### 财务管理

| Method | Path | 说明 |
|--------|------|------|
| GET | /api/finance/page | 分页查询 |
| POST | /api/finance | 新增财务数据 |
| PUT | /api/finance | 编辑财务数据 |
| DELETE | /api/finance/{id} | 删除财务数据 |
| POST | /api/finance/ai-summary?month=yyyy-MM | AI 智能财务摘要 |

### 看板

| Method | Path | 说明 |
|--------|------|------|
| GET | /api/dashboard/summary | 汇总数据 + 趋势 |

### 统一响应格式

```json
{
  "code": 200,
  "msg": "success",
  "data": {}
}
```

## AI 摘要配置

在 `application.yml` 中配置大模型 API：

```yaml
ai:
  api-key: ${AI_API_KEY:your-key}
  api-url: ${AI_API_URL:https://api.openai.com/v1/chat/completions}
  model: ${AI_MODEL:gpt-3.5-turbo}
```

也可通过环境变量 `AI_API_KEY`、`AI_API_URL`、`AI_MODEL` 覆盖。
