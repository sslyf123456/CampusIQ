# ai-service 启动指引 & 下一步清单

> 项目：CampusIQ — ai-service  
> 日期：2026-07-01

---

## TL;DR

代码写完了，接下来你需要：**配环境 → 启数据库 → 填配置 → 装依赖 → FAQ入库 → 启服务 → 联调测试**。

---

## 一、环境准备

### 1.1 PostgreSQL + pgvector

ai-service 需要 PostgreSQL 并安装 pgvector 扩展。

```bash
# 如果你用 Docker（推荐，最省事）
docker run -d \
  --name campusiq-postgres \
  -e POSTGRES_USER=campus \
  -e POSTGRES_PASSWORD=campus123 \
  -e POSTGRES_DB=campus_qa \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# 等容器启动后，进入容器安装扩展
docker exec -it campusiq-postgres psql -U campus -d campus_qa -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

如果你不用 Docker，需要本地安装 PostgreSQL + pgvector 扩展，具体方式取决于你的操作系统。

### 1.2 执行数据库初始化

你的项目里应该有一个 `init.sql`（campus-service 的建表脚本），需要执行它来创建 `ai_campus` schema 和相关表：

```bash
# 找到 init.sql 文件
# 假设在 CampusIQ-main 根目录或 campus-service 目录下

# Docker 方式执行
docker exec -it campusiq-postgres psql -U campus -d campus_qa -f /path/to/init.sql

# 或者直接在 psql 里执行
psql -U campus -d campus_qa < init.sql
```

**⚠️ 关键**：`init.sql` 必须包含 `ai_campus` schema 的创建语句和 `faq_embeddings`、`conversations`、`messages` 表的建表语句。如果 init.sql 只有 campus-service 的表，你需要手动补上 ai-service 的表：

```sql
CREATE SCHEMA IF NOT EXISTS ai_campus;

CREATE TABLE IF NOT EXISTS ai_campus.faq_embeddings (
    id SERIAL PRIMARY KEY,
    document VARCHAR(255),
    chunk_index INTEGER,
    content TEXT,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_campus.conversations (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL,
    title VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_campus.messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES ai_campus.conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    agent_name VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 1.3 Python 环境

```bash
# 建议用 Python 3.10+（你已有 3.13.9，够用）

# 进入 ai-service 目录
cd E:/CampusIQ-mainxt/CampusIQ-main/ai-service

# 创建虚拟环境（可选但推荐）
python -m venv venv

# Windows 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

---

## 二、配置 .env

```bash
# 复制模板
cp .env.example .env

# 编辑 .env，填入实际配置
```

`.env` 必填项说明：

```ini
# ===== 数据库 =====
DB_HOST=localhost          # PostgreSQL 地址
DB_PORT=5432              # PostgreSQL 端口
DB_NAME=campus_qa         # 数据库名（与 campus-service 共用）
DB_USER=campus            # 数据库用户
DB_PASSWORD=campus123     # 数据库密码

# ===== LLM =====
LLM_API_KEY=sk-xxx        # DeepSeek 或 OpenAI 的 API Key
LLM_BASE_URL=https://api.deepseek.com/v1  # LLM 接口地址（DeepSeek 用这个）
LLM_MODEL_NAME=deepseek-chat               # 模型名称

# ===== Embedding（FAQ 入库必须） =====
EMBEDDING_API_KEY=sk-xxx  # Embedding API Key（可以跟 LLM_API_KEY 一样如果用同一家）
EMBEDDING_BASE_URL=https://api.deepseek.com/v1  # Embedding 接口地址
EMBEDDING_MODEL=text-embedding-3-small           # Embedding 模型名

# ===== JWT（⚠️ 必须与 campus-service 一致！） =====
JWT_SECRET=你的共享密钥    # ⚠️ 必须和 campus-service 的 JWT_SECRET 完全相同
JWT_ALGORITHM=HS256

# ===== campus-service =====
CAMPUS_SERVICE_URL=http://localhost:8000  # campus-service 地址

# ===== ai-service =====
AI_SERVICE_PORT=8002       # ai-service 监听端口
```

**⚠️ 关键提醒**：
- `JWT_SECRET` 必须跟 campus-service 用同一个值，否则 JWT 验证会失败
- `EMBEDDING_API_KEY` 如果用 DeepSeek，目前 DeepSeek 可能不支持 Embedding 接口，建议用 OpenAI 的 Embedding（`text-embedding-3-small`，维度 1536）
- `CAMPUS_SERVICE_URL` 要指向已经启动的 campus-service

---

## 三、FAQ 知识库入库

配置好 .env 和数据库后，执行入库脚本：

```bash
cd E:/CampusIQ-mainxt/CampusIQ-main/ai-service

# 确保虚拟环境已激活 && 依赖已安装
python scripts/ingest.py
```

脚本会自动：
1. 读取 `data/faq/` 下 5 个 Markdown 文件
2. 按 `##` 标题切分成知识块
3. 调用 Embedding API 生成向量
4. 存入 `ai_campus.faq_embeddings` 表

**预期输出**：
```
开始 FAQ 文档入库，目录: data/faq
加载了 XX 个文档块
入库成功 [1/XX]: course_selection chunk_0
入库成功 [2/XX]: course_selection chunk_1
...
FAQ 入库完成！成功: XX, 失败: 0
```

如果看到 `失败: 0`，说明入库成功。

---

## 四、启动服务

### 4.1 先启动 campus-service

ai-service 依赖 campus-service 的内部接口，所以必须先启动它：

```bash
# 在 campus-service 目录
cd E:/CampusIQ-mainxt/CampusIQ-main/campus-service
# 按 campus-service 的启动方式启动（通常是 Spring Boot 或类似方式）
```

### 4.2 启动 ai-service

```bash
cd E:/CampusIQ-mainxt/CampusIQ-main/ai-service

# 确保虚拟环境已激活
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

启动后你应该看到：
```
INFO:     Uvicorn running on http://0.0.0.0:8002
INFO:     Application startup complete.
```

### 4.3 验证健康检查

```bash
curl http://localhost:8002/health
# 预期返回：{"status": "healthy", "service": "ai-service"}
```

---

## 五、功能测试

### 5.1 基本对话测试

```bash
# 需要一个有效的 JWT token（从 campus-service 登录获取）
curl -X POST http://localhost:8002/api/ai/chat \
  -H "Authorization: Bearer <你的JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "我下周的课表是什么？"}' \
  --no-buffer
```

预期收到 SSE 流式响应：
```
event: thinking
data: {"message": "正在分析您的意图..."}

event: agent_call
data: {"agent": "schedule", "message": "正在查询课表信息..."}

event: result
data: {"message": "您下周的课表如下：..."}

event: done
data: {"message": "对话完成"}
```

### 5.2 FAQ 测试（不需要 campus-service）

```bash
curl -X POST http://localhost:8002/api/ai/chat \
  -H "Authorization: Bearer <你的JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query": "图书馆怎么借书？"}' \
  --no-buffer
```

这个问题会走 FAQAgent（RAG 模式），不需要 campus-service 返回数据。

### 5.3 对话管理测试

```bash
# 创建对话
curl -X POST http://localhost:8002/api/ai/conversations \
  -H "Authorization: Bearer <你的JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title": "测试对话"}'

# 查看对话列表
curl http://localhost:8002/api/ai/conversations \
  -H "Authorization: Bearer <你的JWT_TOKEN>"

# 查看某个对话的消息
curl http://localhost:8002/api/ai/conversations/<对话ID> \
  -H "Authorization: Bearer <你的JWT_TOKEN>"
```

---

## 六、Docker 部署（可选）

如果你想用容器部署：

```bash
cd E:/CampusIQ-mainxt/CampusIQ-main/ai-service

# 构建镜像
docker build -t campusiq-ai-service .

# 运行容器
docker run -d \
  --name campusiq-ai \
  --env-file .env \
  -p 8002:8002 \
  campusiq-ai-service
```

---

## 七、下一步完整清单

按优先级排列，你接下来要做的事：

| 步骤 | 优先级 | 说明 |
|------|--------|------|
| **1. 安装 PostgreSQL + pgvector** | 🔴 必须 | 数据库是所有功能的基础 |
| **2. 执行 init.sql / 手动建表** | 🔴 必须 | 创建 ai_campus schema 和表 |
| **3. 配置 .env** | 🔴 必须 | 填入数据库、LLM、Embedding、JWT 配置 |
| **4. 安装 Python 依赖** | 🔴 必须 | `pip install -r requirements.txt` |
| **5. FAQ 向量入库** | 🔴 必须 | `python scripts/ingest.py` |
| **6. 启动 campus-service** | 🟡 重要 | ai-service 依赖它的内部接口 |
| **7. 启动 ai-service** | 🟡 重要 | `uvicorn app.main:app --port 8002` |
| **8. 健康检查验证** | 🟡 重要 | `/health` 端点 |
| **9. 对话功能测试** | 🟡 重要 | 测试 SSE 流式对话 |
| **10. 获取 JWT Token** | 🟡 重要 | 从 campus-service 登录获取 |
| **11. 扩充 FAQ 知识库** | 🟢 可选 | 添加更多 Markdown 文档覆盖更多场景 |
| **12. Docker 容器化部署** | 🟢 可选 | 用 Dockerfile 构建生产镜像 |
| **13. 前端对接** | 🟢 可选 | 前端调用 SSE 接口展示对话 |

---

## 八、常见问题

### Q: DeepSeek 支持 Embedding 吗？
目前 DeepSeek 可能不提供 Embedding API。建议用 OpenAI 的 `text-embedding-3-small`（维度 1536，和代码中 VECTOR(1536) 对齐）。LLM 可以继续用 DeepSeek，Embedding 单独配 OpenAI：

```ini
LLM_API_KEY=sk-deepseek-xxx
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL_NAME=deepseek-chat

EMBEDDING_API_KEY=sk-openai-xxx
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-small
```

### Q: JWT Token 怎么获取？
通过 campus-service 的登录接口获取。ai-service 和 campus-service 使用相同的 JWT_SECRET，所以 campus-service 生成的 token 在 ai-service 也有效。

### Q: campus-service 没启动怎么办？
ScheduleAgent / RepairAgent / ScholarshipAgent / NoticeAgent 这 4 个 SubAgent 需要调用 campus-service。如果 campus-service 没启动，这些 Agent 会走 fallback 逻辑返回错误提示。但 FAQAgent（RAG 模式）不依赖 campus-service，可以独立工作。

### Q: FAQ 入库后想新增知识怎么办？
往 `data/faq/` 目录添加新的 Markdown 文件（格式：一级标题写主题，二级标题写知识点），然后重新运行 `python scripts/ingest.py`。如果想避免重复入库，可以先清空 `ai_campus.faq_embeddings` 表再跑。

---

_文档生成日期：2026-07-01_
