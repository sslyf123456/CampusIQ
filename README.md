# 基于 RAG + 多智能体校园问答助手

一个由 **RAG 知识库检索** 与 **多智能体协同调度** 驱动的校园智能问答平台。用户（学生/管理员）通过统一的 Web 界面登录后，既可管理校园业务数据（课表、宿舍报修、奖助、通知），也可与 AI 助手对话——AI 通过意图识别路由到对应 Sub-Agent，透传用户 JWT 调用校园内部接口获取实时数据，结合 RAG 知识库生成自然语言回答，全程 SSE 流式输出。

---

## 目录

- [系统架构](#系统架构)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [核心功能](#核心功能)
- [数据库设计](#数据库设计)
- [多智能体架构](#多智能体架构)
- [快速开始](#快速开始)
- [API 概览](#api-概览)
- [部署](#部署)
- [工具脚本](#工具脚本)

---

## 系统架构

```
用户浏览器 / 前端 (Vue 3)
       |
       v
   Nginx :80 (统一入口)
       |
       +---- /api/campus/* ----> campus-service :8001 (校园数据)
       |
       +---- /api/ai/*      ----> ai-service :8002 (AI 问答)
                                     |
                                     | 内部 HTTP 调用 (透传用户 JWT)
                                     v
                                 campus-service 内部接口

  PostgreSQL 16 + pgvector :5432
```

**协作关系：**

- 前端持同一 JWT 同时访问 campus-service 和 ai-service，用户无需分别登录
- ai-service **不直连数据库**，所有业务数据通过 campus-service 暴露的内部接口获取
- 内部接口**透传用户 JWT**：ai-service 将前端用户的 JWT 原样传递给 campus-service，campus-service 解析 JWT 获取用户身份并校验权限，保证数据隔离

### 数据流闭环

```
注册(管理员创建学生) -> 登录(签发JWT) -> 进入系统 -> 查看个人信息/课表/报修/奖助

AI 问答: 用户提问 -> Master Agent 意图识别 -> 路由 Sub-Agent / FAQ检索
       -> 调校园内部接口(透传JWT) -> 汇总回复(SSE流式输出)

Agent 路由:
  ScheduleAgent    -> 查询课表
  RepairAgent      -> 查询宿舍报修工单
  ScholarshipAgent -> 查询奖助记录
  NoticeAgent      -> 检索校园通知
  StudentAgent     -> 查询学生信息(仅管理员)
  FAQAgent         -> 向量知识库兜底回答
```

---

## 技术栈

| 模块 | 技术 |
|------|------|
| **campus-service** | Python 3.11+ / FastAPI / SQLAlchemy 2.0 / Pydantic v2 / bcrypt / PyJWT |
| **ai-service** | Python 3.11+ / FastAPI / OpenAI SDK (async) / pgvector / httpx / sse-starlette |
| **前端** | Vue 3 / TypeScript / Element Plus / Pinia / Vue Router / Vite 6 / axios |
| **数据库** | PostgreSQL 16 + pgvector 扩展 |
| **部署** | Nginx 反向代理 + uvicorn 进程（直接部署，不用 Docker） |

---

## 项目结构

```
project/
|
|-- campus-service/              # 校园后台支撑服务 (FastAPI, :8001)
|   |-- app/
|   |   |-- main.py              # 应用入口, 路由注册, 中间件, 异常处理
|   |   |-- config.py            # 配置管理 (.env 读取)
|   |   |-- database.py          # SQLAlchemy 引擎与会话工厂
|   |   |-- dependencies.py      # 依赖注入 (get_db, get_current_user)
|   |   |-- models/              # SQLAlchemy 数据模型 (student, admin, schedule, ...)
|   |   |-- schemas/             # Pydantic 请求/响应 Schema
|   |   |-- routers/             # API 路由 (auth, students, schedules, repair_orders, ...)
|   |   |-- services/            # 业务逻辑层
|   |   `-- utils/               # 工具 (security, response, exceptions)
|   |-- data/                    # 预置演示数据 (JSON)
|   |-- requirements.txt
|   |-- .env.example
|   `-- .env
|
|-- ai-service/                  # AI 问答核心服务 (FastAPI, :8002)
|   |-- app/
|   |   |-- main.py              # 应用入口, SSE 端点, 生命周期管理(自动入库FAQ)
|   |   |-- config.py            # 配置管理 (LLM, Embedding, campus-service 地址)
|   |   |-- database.py          # 数据库连接
|   |   |-- models/              # 数据模型 (conversation, message)
|   |   |-- schemas/             # Pydantic Schema (chat 请求/响应, SSE 事件)
|   |   |-- routers/             # API 路由 (chat SSE, conversations CRUD)
|   |   |-- agents/              # 多智能体
|   |   |   |-- base_agent.py    # Agent 抽象基类
|   |   |   |-- master_agent.py  # 主 Agent: 意图识别 + 路由
|   |   |   |-- schedule_agent.py
|   |   |   |-- repair_agent.py
|   |   |   |-- scholarship_agent.py
|   |   |   |-- notice_agent.py
|   |   |   |-- student_agent.py
|   |   |   `-- faq_agent.py     # FAQ 知识库兜底
|   |   |-- prompts.py           # 角色化系统提示词 (学生/管理员) + 服务器时间注入
|   |   |-- rag/                 # RAG 知识库
|   |   |   |-- embedding.py     # 文档向量化
|   |   |   |-- vector_store.py  # pgvector 向量存储与检索
|   |   |   `-- loader.py        # FAQ 文档加载与分块
|   |   |-- services/            # 业务逻辑
|   |   |   |-- chat_service.py  # 对话编排 (意图 -> 路由 -> SSE 推送)
|   |   |   |-- campus_client.py # HTTP 客户端, 透传 JWT 调用 campus-service
|   |   |   `-- conversation_service.py
|   |   `-- utils/               # SSE 构造, 异常处理
|   |-- data/faq/                # FAQ 文档源文件 (选课/宿舍/奖助/请假/图书馆)
|   |-- scripts/ingest.py        # FAQ 向量手动入库脚本
|   |-- requirements.txt
|   |-- .env.example
|   `-- .env
|
|-- frontend/                    # 前端应用 (Vue 3 + TypeScript)
|   |-- src/
|   |   |-- main.ts              # 应用入口
|   |   |-- App.vue
|   |   |-- router/index.ts      # 路由配置 + 路由守卫 (Token 校验, 角色判断)
|   |   |-- stores/auth.ts       # Pinia 状态管理 (登录态, Token, 用户信息)
|   |   |-- api/                 # axios 封装 (request, auth, student, schedule, ...)
|   |   |-- views/               # 页面组件 (Login, Profile, Schedule, Repair, ...)
|   |   |-- components/          # 公共组件 (AppLayout, SideNav, InfoTable)
|   |   |-- types/               # TypeScript 类型定义
|   |   `-- utils/token.ts       # Token 存取工具
|   |-- vite.config.ts           # Vite 配置 (代理 /api/campus -> :8001, /api/ai -> :8002)
|   |-- package.json
|   `-- tsconfig.json
|
|-- data/
|   `-- init.sql                 # 数据库建表脚本 (2 schema, 11 表, 7 索引)
|
|-- scripts/                     # 工具脚本
|   |-- smoke_test_pg.py         # PG + pgvector 冒烟测试
|   |-- seed_data.py             # 演示数据导入脚本
|   `-- gen_jwt_secret.py        # JWT 随机密钥生成
|
|-- nginx/                       # Nginx 反向代理配置
|   |-- nginx.windows.conf       # Windows 版 (路径用 F:/.../dist, start nginx 启动)
|   `-- nginx.linux.conf         # Linux 版 (路径用 /opt/.../dist, systemctl 管理)
|-- docs/                        # 项目文档 (API 文档)
|-- video/                       # 汇报视频
|-- ppt/                         # 答辩 PPT
|-- requirements.txt             # 公共 Python 依赖 (脚本用)
`-- .env                         # 全量环境变量 (参考模板)
```

---

## 核心功能

### 用户鉴权

- 管理员创建学生账号（不开放自主注册），学号唯一
- 学生使用学号+密码登录，管理员使用 username+密码登录，签发 JWT（含 role 字段：student / admin）
- 修改密码后旧 Token 立即加入黑名单失效，强制重新登录
- 登出时将 JWT 的 jti 写入 token_blacklist 表，实现真正的登出失效
- Pydantic 422 校验错误统一中文响应

### 校园数据管理

| 模块 | 学生权限 | 管理员权限 |
|------|----------|------------|
| 学生信息 | 查看本人信息 | CRUD 全校学生（搜索+分页），查看选课信息 |
| 课表 | 查看本人课表（学期筛选） | CRUD 课程，查看选课学生名单 |
| 宿舍报修 | 发起报修、查看本人工单 | 查看全部工单，更新处理状态 |
| 奖助 | 查看本人记录 | CRUD 全部奖助记录 |
| 通知 | 检索查看通知 | 发布/编辑/删除通知 |

### RAG 知识库

- 校园 FAQ 文档（选课流程、宿舍管理、奖助申请、请假流程、图书馆规则）向量化存入 pgvector
- 用户提问向量化后余弦相似度检索，召回 Top-K 相关文档片段
- 检索结果注入 LLM 上下文，减少 AI 幻觉
- AI 服务启动时自动检查并入库 FAQ 向量数据

### 多智能体对话

- **Master Agent**：使用 LLM 进行意图识别（JSON 结构化输出），支持 8 种意图类别 + 学期自动提取
- **5 个 Sub-Agent**：ScheduleAgent / RepairAgent / ScholarshipAgent / NoticeAgent / StudentAgent，各自调用校园内部接口获取数据后生成自然语言回答
- **FAQ 兜底**：无业务查询意图时走向量知识库回答
- **角色化提示词**：学生版强调个人数据+亲切语气，管理员版强调全校数据+专业汇总
- **服务器时间注入**：系统提示词末尾拼接当前时间（含星期）和当前学期，使 AI 能理解"本学期""本周""今天"等相对时间词
- **SSE 流式输出**：6 种事件类型（thinking / agent_call / result / error / done / clarify），打字机效果逐字输出
- **多轮对话**：保留历史消息上下文，支持会话管理（新建/切换/删除）

---

## 数据库设计

PostgreSQL 16 + pgvector 扩展，字符集 UTF8，共 2 个 schema、11 张表、7 个索引。

### Schema 划分

| Schema | 归属服务 | 表 |
|--------|----------|-----|
| `campus` | campus-service | students, admins, schedules, student_schedule, repair_orders, scholarship_records, notices, token_blacklist |
| `ai_campus` | ai-service | faq_embeddings, conversations, messages |

### 表结构速查

| 表 | 说明 | 关键字段 |
|----|------|----------|
| campus.students | 学生表 | student_id(学号,唯一), name, password_hash(bcrypt), department, dorm_building, dorm_room |
| campus.admins | 管理员表 | username(唯一), name, password_hash |
| campus.schedules | 课表 | course_name, teacher, weekday(1-7), start_period, end_period, semester, created_by(FK admins) |
| campus.student_schedule | 学生-课程关联(多对多) | student_id(FK), schedule_id(FK), 联合主键 |
| campus.repair_orders | 宿舍报修工单 | student_id(FK), description, status(pending/processing/completed), handler |
| campus.scholarship_records | 奖助记录 | student_id(FK), type(奖学金/助学金), amount, status(pending/approved/rejected), semester |
| campus.notices | 校园通知 | title, content, category(academic/dormitory/scholarship/general), publisher, published_at |
| campus.token_blacklist | Token 黑名单 | jti(唯一), user_sub, expires_at |
| ai_campus.faq_embeddings | FAQ 向量嵌入 | document, chunk_index, content, embedding(VECTOR 1536维) |
| ai_campus.conversations | AI 会话 | student_id(FK campus.students), title, status(active/closed) |
| ai_campus.messages | 消息 | conversation_id(FK), role(user/assistant/system), content, agent_name, metadata(JSONB) |

> faq_embeddings 建有 IVFFlat 余弦距离索引（lists=10），加速 Top-K 向量检索。

完整建表 SQL 见 `data/init.sql`。

---

## 多智能体架构

```
用户提问 -> Master Agent (意图识别 + 路由)
              |-- schedule      -> ScheduleAgent    -> GET /internal/schedule    -> 汇总
              |-- repair        -> RepairAgent      -> GET /internal/repair      -> 汇总
              |-- scholarship   -> ScholarshipAgent -> GET /internal/scholarship  -> 汇总
              |-- notice        -> NoticeAgent      -> GET /internal/notices     -> 汇总
              |-- student       -> StudentAgent     -> GET /internal/students    -> 汇总 (仅管理员)
              |-- faq           -> FAQAgent         -> pgvector 向量检索          -> 回答
              |-- unclear       -> 反问澄清
              `-- out_of_scope  -> 兜底回复
```

**SSE 事件流：**

```
thinking  -> "正在分析您的问题..."
agent_call -> { agent: "schedule", description: "正在调用..." }
result    -> { content: "...", agent: "schedule" }  (分块逐字推送)
done      -> { conversation_id, title }
```

**数据隔离链路：**

```
学生A登录 -> JWT(student_id=A) -> 前端持JWT调用AI问答
    -> ai-service 透传JWT调用 /internal/schedule
    -> campus-service 解析JWT -> student_id=A -> 查询 -> 返回学生A的课表
    -> 学生A无法通过AI或直接API获取学生B的数据
```

---

## 快速开始

### 前置要求

- Python 3.11+
- Node.js 20+
- PostgreSQL 16 + pgvector 扩展

### 1. 数据库准备

```bash
# 安装 pgvector 扩展（以 PostgreSQL 16 为例）
# Windows: 使用 StackBuilder 安装或从源码编译
# Linux: apt install postgresql-16-pgvector

# 创建数据库
psql -U postgres -c "CREATE DATABASE campus_qa ENCODING 'UTF8';"

# 执行建表脚本
psql -U postgres -d campus_qa -f data/init.sql
```

### 2. 配置环境变量

每个服务有独立的 `.env` 文件，从对应的 `.env.example` 复制并修改：

```bash
# campus-service
cp campus-service/.env.example campus-service/.env
# 编辑 campus-service/.env，填写 DB_PASSWORD, JWT_SECRET 等

# ai-service
cp ai-service/.env.example ai-service/.env
# 编辑 ai-service/.env，填写 LLM_API_KEY, EMBEDDING_API_KEY, JWT_SECRET 等
# 注意：JWT_SECRET 必须与 campus-service 一致
# 注意：CAMPUS_SERVICE_URL 应为 http://localhost:8001
```

> 可使用 `python scripts/gen_jwt_secret.py` 生成随机 JWT 密钥，两个服务使用同一密钥。

### 3. 安装依赖

```bash
# campus-service
cd campus-service
pip install -r requirements.txt

# ai-service
cd ai-service
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 4. 导入演示数据

```bash
python scripts/seed_data.py
```

### 5. 启动服务

按顺序启动三个服务：

```bash
# 终端 1: campus-service (:8001)
cd campus-service
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# 终端 2: ai-service (:8002)
cd ai-service
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

# 终端 3: 前端开发服务器 (:5173)
cd frontend
npm run dev
```

启动后访问 `http://localhost:5173` 即可使用。

> ai-service 首次启动时会自动检查 FAQ 向量数据，若不存在则自动向量化入库。也可手动执行 `python ai-service/scripts/ingest.py`。

### 6. 验证

- 健康检查：`GET http://localhost:8001/health` 和 `GET http://localhost:8002/health`
- 数据库冒烟测试：`python scripts/smoke_test_pg.py`
- 使用管理员账号登录前端，创建学生，学生登录后即可使用全部功能

---

## API 概览

### campus-service (`/api/campus/*`)

| 模块 | 端点 | 方法 | 权限 |
|------|------|------|------|
| 健康检查 | `/health` | GET | 公开 |
| 认证 | `/api/campus/auth/login` | POST | 公开 |
| | `/api/campus/auth/me` | GET | 已登录 |
| | `/api/campus/auth/password` | PUT | 已登录 |
| | `/api/campus/auth/logout` | POST | 已登录 |
| 学生管理 | `/api/campus/students` | GET / POST | 管理员 |
| | `/api/campus/students/{student_id}` | GET / PUT / DELETE | 管理员 |
| | `/api/campus/students/{student_id}/schedules` | GET | 管理员 |
| 课表 | `/api/campus/schedules` | GET / POST | 学生查询本人 / 管理员管理全部 |
| | `/api/campus/schedules/semesters` | GET | 已登录 |
| | `/api/campus/schedules/{schedule_id}` | GET / PUT / DELETE | 管理员 |
| | `/api/campus/schedules/{schedule_id}/students` | GET / POST | 管理员（查选课名单 / 添加学生） |
| | `/api/campus/schedules/{schedule_id}/students/{student_id}` | DELETE | 管理员（移除学生） |
| 宿舍报修 | `/api/campus/repair-orders` | GET | 学生查本人 / 管理员查全部 |
| | `/api/campus/repair-orders` | POST | 学生 |
| | `/api/campus/repair-orders/{order_id}` | GET | 学生查本人 / 管理员查全部 |
| | `/api/campus/repair-orders/{order_id}` | PUT | 管理员（处理工单） |
| 奖助 | `/api/campus/scholarships` | GET | 学生查本人 / 管理员查全部 |
| | `/api/campus/scholarships` | POST | 管理员 |
| | `/api/campus/scholarships/{record_id}` | GET | 学生查本人 / 管理员查全部 |
| | `/api/campus/scholarships/{record_id}` | PUT / DELETE | 管理员 |
| 通知 | `/api/campus/notices` | GET | 已登录（关键词 + 分类检索） |
| | `/api/campus/notices` | POST | 管理员 |
| | `/api/campus/notices/{notice_id}` | GET | 已登录 |
| | `/api/campus/notices/{notice_id}` | PUT / DELETE | 管理员 |
| 内部接口 | `/api/campus/internal/schedule` | GET | JWT 透传 |
| | `/api/campus/internal/repair` | GET | JWT 透传 |
| | `/api/campus/internal/scholarship` | GET | JWT 透传 |
| | `/api/campus/internal/notices` | GET | JWT 透传 |
| | `/api/campus/internal/students` | GET | JWT（仅管理员） |

### ai-service (`/api/ai/*`)

| 模块 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 健康检查 | `/health` | GET | 服务状态 |
| 对话 | `/api/ai/chat` | POST | SSE 流式对话 |
| 会话 | `/api/ai/conversations` | GET / POST | 会话列表 / 新建会话 |
| | `/api/ai/conversations/{conversation_id}` | GET | 会话详情（含消息列表） |
| | `/api/ai/conversations/{conversation_id}` | DELETE | 删除会话（逻辑删除） |

> 详细 API 文档见 `docs/campus-service-api.md` 和 `docs/ai-service-api.md`。

---

## 部署

采用直接部署方式（Nginx 反向代理 + uvicorn 进程），不用 Docker。

### Nginx 配置

提供两份配置文件，按部署平台选用：

| 文件 | 平台 | 前端 dist 路径 | 启动方式 |
|------|------|---------------|----------|
| `nginx/nginx.windows.conf` | Windows | `F:/高级软件实作/project/frontend/dist` | `start nginx` |
| `nginx/nginx.linux.conf` | Linux | `/opt/campus-qa/frontend/dist` | `systemctl start nginx` |

两份配置功能一致，差异仅在路径格式、日志位置和系统管理方式。使用前**只需修改 `root` 路径**为实际前端构建产物目录。

**Windows 用法：**

```bash
# 1. 下载 nginx 解压到 C:\nginx
# 2. 复制配置 (或用 -c 指定路径)
copy nginx\nginx.windows.conf C:\nginx\conf\nginx.conf

# 3. 修改 root 路径为实际 dist 目录
# 4. 检查并启动
nginx -t
start nginx
nginx -s reload   # 热重载
```

**Linux 用法：**

```bash
# 1. 安装 nginx
apt install nginx   # Ubuntu/Debian
# yum install nginx  # CentOS

# 2. 部署配置
sudo cp nginx/nginx.linux.conf /etc/nginx/nginx.conf

# 3. 修改 root 路径为实际 dist 目录
# 4. 检查并启动
nginx -t
systemctl start nginx
systemctl reload nginx   # 热重载
```

**配置要点：**

| 配置项 | 说明 |
|--------|------|
| `/` | 前端 SPA 静态文件，`try_files` 回退到 `index.html` 支持 history 路由 |
| `/assets/` | Vite 构建产物（带 hash），1 年长缓存 |
| `/api/campus/` | 代理到 campus-service `:8001`，透传真实 IP |
| `/api/ai/` | 代理到 ai-service `:8002`，**禁用缓冲**保证 SSE 逐字推送 |
| `/health/campus` `/health/ai` | 健康检查端点，便于外部监控 |
| gzip | 压缩 JS/CSS/JSON/SVG 等静态资源 |
| `client_max_body_size` | 10MB，覆盖报修描述、通知内容等 |

> **SSE 注意事项**：ai-service 的 `/api/ai/chat` 端点使用 SSE 流式输出，Nginx 必须设置 `proxy_buffering off` 和 `proxy_http_version 1.1`，否则响应会被缓冲导致前端无法收到逐字推送。

### 启动顺序

1. 启动 PostgreSQL 数据库
2. 启动 campus-service：`uvicorn app.main:app --host 0.0.0.0 --port 8001`
3. 启动 ai-service：`uvicorn app.main:app --host 0.0.0.0 --port 8002`
4. 构建前端：`cd frontend && npm run build`
5. 启动 Nginx：Windows 用 `start nginx`，Linux 用 `systemctl start nginx`

### 配置说明

- 各服务通过自身目录下的 `.env` 管理敏感信息，`load_dotenv()` 显式指向各自 `.env`，不依赖工作目录
- 外层 `.env` 仅作参考模板
- 两个服务的 `JWT_SECRET` 必须一致（共用同一密钥签发和验证 JWT）
- ai-service 的 `CAMPUS_SERVICE_URL` 指向 campus-service 地址（默认 `http://localhost:8001`）
- ai-service 支持 OpenAI 兼容接口（如 DeepSeek），通过 `LLM_BASE_URL` 和 `LLM_MODEL_NAME` 配置

---

## 工具脚本

| 脚本 | 用途 |
|------|------|
| `scripts/smoke_test_pg.py` | PostgreSQL + pgvector 环境冒烟测试 |
| `scripts/seed_data.py` | 演示数据导入（DROP + CREATE 确保表结构最新） |
| `scripts/gen_jwt_secret.py` | 生成随机 JWT 密钥 |
| `ai-service/scripts/ingest.py` | FAQ 文档手动向量化入库 |
