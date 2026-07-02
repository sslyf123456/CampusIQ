# ai-service 交付总结

> 项目：CampusIQ — 基于 RAG + 多智能体校园问答助手  
> 模块：ai-service（AI 问答核心服务，端口 8002）  
> 日期：2026-07-01

---

## TL;DR

完成了 ai-service 全部代码开发，共 **40 个文件**（32 Python + 5 FAQ Markdown + Dockerfile + .env.example + requirements.txt + ingest.py），语法检查 0 错误，全局一致性审查 IS_PASS: YES，与架构师设计完全对齐。

---

## 交付概览

| 项目 | 状态 |
|------|------|
| 代码文件数 | 40 |
| 语法检查 | ✅ 0 错误 |
| 全局一致性审查 | ✅ IS_PASS: YES |
| 架构对齐 | ✅ 已完成 |
| QA 测试 | ✅ 通过 |
| 已知问题 | 0 |

---

## 架构设计

### 整体架构

```
用户请求 → FastAPI (8002) → JWT验证 → ChatService
                                      ↓
                               MasterAgent（意图分类）
                                      ↓ 路由
                    ┌─────────────────┼─────────────────┐
                    ↓                 ↓                 ↓
              4个SubAgent        FAQAgent           通用回复
          (Schedule/Repair/    (RAG检索+生成)
           Scholarship/Notice)
                    ↓                 ↓
             campus-service      pgvector向量库
             (内部API调用)      (FAQ知识检索)
```

### 核心组件

| 组件 | 文件 | 说明 |
|------|------|------|
| **BaseAgent** | `app/agents/base_agent.py` | 抽象基类，统一 Agent 接口（run/build_prompt/_call_llm） |
| **MasterAgent** | `app/agents/master_agent.py` | 意图分类 + 路由分发，通过 LLM 判断用户意图 |
| **ScheduleAgent** | `app/agents/schedule_agent.py` | 课表查询，调用 campus-service 获取课表数据后生成回答 |
| **RepairAgent** | `app/agents/repair_agent.py` | 报修查询，调用 campus-service 获取报修记录 |
| **ScholarshipAgent** | `app/agents/scholarship_agent.py` | 奖学金查询，调用 campus-service 获取奖学金信息 |
| **NoticeAgent** | `app/agents/notice_agent.py` | 通知查询，调用 campus-service 获取校园通知 |
| **FAQAgent** | `app/agents/faq_agent.py` | RAG 模式，检索 FAQ 向量库 + LLM 生成回答 |

### 数据流

- **JWT 透明传递**：ai-service 不解析 JWT 内容，直接将用户 token 透传给 campus-service 内部接口
- **student_id 来源**：从 JWT 中取 `db_id` 字段（整数主键）作为 `student_id`，与 `campus.students(id)` FK 对齐
- **SSE 流式响应**：事件类型统一为 `thinking / agent_call / result / error / done / clarify`

### RAG 流程

```
FAQ Markdown → FAQLoader → split_by_heading() → Embedding API → pgvector 存储
                                                                              ↓
用户提问 → FAQAgent → 向量相似度检索 → Top-K 文档块 → LLM 生成回答 → SSE 输出
```

---

## 完整文件清单

### 核心应用代码（app/）

| 文件路径 | 说明 |
|----------|------|
| `app/__init__.py` | 包初始化 |
| `app/main.py` | FastAPI 入口，CORS、路由注册、/health、启动检查 |
| `app/config.py` | Settings 配置类（数据库、LLM、Embedding、JWT 等） |
| `app/database.py` | SQLAlchemy engine + sessionmaker，ai_campus schema |

### Agent 模块（app/agents/）

| 文件路径 | 说明 |
|----------|------|
| `app/agents/__init__.py` | 包初始化 |
| `app/agents/base_agent.py` | Agent 抽象基类 |
| `app/agents/master_agent.py` | 意意分类 + 路由 MasterAgent |
| `app/agents/schedule_agent.py` | 课表查询 SubAgent |
| `app/agents/repair_agent.py` | 报修查询 SubAgent |
| `app/agents/scholarship_agent.py` | 奖学金查询 SubAgent |
| `app/agents/notice_agent.py` | 通知查询 SubAgent |
| `app/agents/faq_agent.py` | FAQ RAG Agent |

### 数据模型（app/models/）

| 文件路径 | 说明 |
|----------|------|
| `app/models/__init__.py` | 包初始化 |
| `app/models/conversation.py` | Conversation 模型（student_id=Integer FK） |
| `app/models/message.py` | Message 模型（含 agent_name、metadata JSONB） |

### API 路由（app/routers/）

| 文件路径 | 说明 |
|----------|------|
| `app/routers/__init__.py` | 包初始化 |
| `app/routers/chat.py` | POST /api/ai/chat SSE 流式对话端点 |
| `app/routers/conversations.py` | 对话 CRUD（GET/POST/GET by id/DELETE） |

### 数据 Schema（app/schemas/）

| 文件路径 | 说明 |
|----------|------|
| `app/schemas/__init__.py` | 包初始化 |
| `app/schemas/chat.py` | ChatRequest、SSEEvent、ConversationResponse、MessageResponse |

### 业务服务（app/services/）

| 文件路径 | 说明 |
|----------|------|
| `app/services/__init__.py` | 包初始化 |
| `app/services/chat_service.py` | ChatService 对话编排器，管理 Agent 路由与 SSE 流 |
| `app/services/campus_client.py` | httpx 异步客户端，JWT 透传调用 campus-service |
| `app/services/conversation_service.py` | 对话 CRUD 服务（student_id: int） |

### RAG 模块（app/rag/）

| 文件路径 | 说明 |
|----------|------|
| `app/rag/__init__.py` | 包初始化 |
| `app/rag/embedding.py` | OpenAI Embedding 包装（get_embedding / get_embeddings_batch） |
| `app/rag/vector_store.py` | pgvector 向量操作（store_embedding / search_similar cosine） |
| `app/rag/loader.py` | FAQLoader + split_by_heading（按 ## 标题分块） |

### 工具模块（app/utils/）

| 文件路径 | 说明 |
|----------|------|
| `app/utils/__init__.py` | 包初始化 |
| `app/utils/sse.py` | SSE 事件格式化（format_sse_event） |
| `app/utils/exceptions.py` | 自定义异常 + fallback 回复模板 |

### FAQ 知识文档（data/faq/）

| 文件路径 | 说明 |
|----------|------|
| `data/faq/course_selection.md` | 选课流程 FAQ |
| `data/faq/dormitory.md` | 住宿相关 FAQ |
| `data/faq/leave_request.md` | 请假流程 FAQ |
| `data/faq/library.md` | 图书馆服务 FAQ |
| `data/faq/scholarship_apply.md` | 奖学金申请 FAQ |

### 配置 & 脚本

| 文件路径 | 说明 |
|----------|------|
| `requirements.txt` | Python 依赖包列表 |
| `.env.example` | 环境变量模板 |
| `Dockerfile` | 容器化构建 |
| `scripts/ingest.py` | FAQ 向量化入库脚本 |

---

## 关键设计决策 & 修复记录

### 第一轮修复（代码自检）

1. **student_id 类型修正**：`String(50) → Integer`，与数据库 FK `campus.students(id)` 对齐
2. **JWT 字段修正**：从 `user_info["sub"]`（学号字符串）改为 `user_info["db_id"]`（整数主键）
3. **typing 导入修正**：`from typing import list` → `from typing import List`

### 第二轮修正（架构师设计对齐）

1. **新增 BaseAgent 抽象基类**：统一 Agent 接口（run/build_prompt/_call_llm）
2. **SSE 事件类型统一**：`route/agent_start/agent_result/answer` → `thinking/agent_call/result/error/done/clarify`
3. **新增 FAQLoader 类 + split_by_heading()**：按 Markdown ## 标题分块
4. **新增 scripts/ingest.py**：独立 FAQ 向量化入库脚本
5. **新增 Dockerfile**：容器化构建支持
6. **ChatService 使用 sub_agents 字典路由**：按意图名分发 Agent
7. **参数名统一为 student_db_id**：与 JWT db_id 对齐，避免歧义

---

## 待部署验证项

| 项目 | 说明 |
|------|------|
| PostgreSQL + pgvector | 需安装 pgvector 扩展并创建 campus_qa 数据库 |
| LLM API Key | 配置 DeepSeek 或 OpenAI API Key |
| Embedding API Key | FAQ 向量化入库需要 Embedding 服务 |
| JWT_SECRET | 必须与 campus-service 使用相同密钥 |
| campus-service 运行 | ai-service 依赖 campus-service 内部接口 |

---

_文档生成日期：2026-07-01_
