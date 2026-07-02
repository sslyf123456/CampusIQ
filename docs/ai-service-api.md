# AI-Service API 文档

## 概述

- **服务名**: ai-service（AI 问答核心服务）
- **框架**: Python FastAPI
- **端口**: 8002
- **认证**: JWT Bearer Token（HS256，需与 campus-service 共用相同 JWT_SECRET）
- **数据库**: 与 campus-service 共用 `campus_qa` 数据库，使用 `ai_campus` schema
- **SSE 事件类型**: thinking / agent_call / result / error / done / clarify

## JWT 载荷

```json
{
  "sub": "20230001",
  "role": "student",
  "db_id": 1,
  "iat": 1720000000,
  "exp": 1720086400
}
```

- `sub`: 学号字符串
- `role`: `"student"` | `"admin"`
- `db_id`: 数据库主键 ID（Integer，用于关联 conversations 表）

---

## 1. 健康检查

### GET /health — 健康检查

**权限**: 公开

**响应**:
```json
{
  "status": "ok",
  "service": "ai-service",
  "version": "1.0.0",
  "port": 8002
}
```

---

## 2. AI 对话 `/api/ai/chat`

### POST /api/ai/chat — SSE 流式对话

**权限**: 需登录（JWT Bearer Token）

**请求头**:
```
Authorization: Bearer <token>
Content-Type: application/json
```

**请求**:
```json
{
  "conversation_id": null,
  "message": "我想查一下这周的课表"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| conversation_id | int/null | 否 | 会话 ID，为空则自动创建新会话 |
| message | string | 是 | 用户消息内容（最大 2000 字符） |

**响应**: SSE 流式响应（text/event-stream）

**SSE 事件流示例**:
```
event: thinking
data: {"content": "正在分析您的问题...", "clarify": false}

event: agent_call
data: {"agent": "schedule", "description": "正在调用 schedule Agent 处理您的问题..."}

event: result
data: {"content": "您这周的", "agent": "schedule"}

event: result
data: {"content": "课程安排如下：", "agent": "schedule"}

... (流式输出，最终回答)

event: done
data: {}
```

**SSE 事件类型说明**:

| 事件类型 | data 格式 | 说明 |
|----------|-----------|------|
| thinking | `{"content": "...", "clarify": bool}` | 正在分析/处理中 |
| agent_call | `{"agent": "...", "description": "..."}` | Sub-Agent 开始处理 |
| result | `{"content": "...", "agent": "..."}` | 流式回答内容（逐字输出） |
| error | `{"message": "...", "fallback": bool}` | 错误信息 |
| done | `{}` | 流结束标记 |
| clarify | `{"question": "..."}` | 反问澄清 |

**agent 值说明**:
- `schedule`: 课表查询 Agent
- `repair`: 宿舍报修查询 Agent
- `scholarship`: 奖助学金查询 Agent
- `notice`: 通知检索 Agent
- `faq`: FAQ 知识库兜底 Agent

**意图识别结果**:

| 意图 | 触发条件 | 返回的 Agent |
|------|----------|--------------|
| schedule | 询问课程安排、上课时间、教室等 | schedule |
| repair | 询问报修进度、报修记录等 | repair |
| scholarship | 询问奖学金、助学金等 | scholarship |
| notice | 寻找校园通知、公告等 | notice |
| faq | 校园常见问题（选课、宿舍管理等） | faq |
| unclear | 问题不明确 | clarify 反问 |
| out_of_scope | 问题超出校园服务范围 | error + 兜底消息 |

**错误响应**:
```json
{
  "detail": "JWT 已过期"
}
```

---

## 3. 会话管理 `/api/ai/conversations`

### GET /api/ai/conversations — 会话列表

**权限**: 需登录

**请求头**: `Authorization: Bearer <token>`

**响应**:
```json
{
  "data": [
    {
      "id": 1,
      "student_id": 1,
      "title": "新对话",
      "status": "active",
      "created_at": "2026-07-02T10:00:00",
      "updated_at": "2026-07-02T10:30:00"
    }
  ]
}
```

**说明**: 只返回当前用户的 active 状态会话，按更新时间倒序排列。

---

### POST /api/ai/conversations — 创建会话

**权限**: 需登录

**请求头**: `Authorization: Bearer <token>`

**请求**:
```json
{
  "title": "我的选课咨询"
}
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| title | string | 否 | "新对话" | 会话标题（最大 200 字符） |

**响应**:
```json
{
  "data": {
    "id": 2,
    "student_id": 1,
    "title": "我的选课咨询",
    "status": "active",
    "created_at": "2026-07-02T11:00:00",
    "updated_at": "2026-07-02T11:00:00"
  }
}
```

---

### GET /api/ai/conversations/{conversation_id} — 会话详情

**权限**: 需登录（只能查看自己的会话）

**请求头**: `Authorization: Bearer <token>`

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| conversation_id | int | 会话 ID |

**响应**:
```json
{
  "data": {
    "id": 1,
    "student_id": 1,
    "title": "新对话",
    "status": "active",
    "created_at": "2026-07-02T10:00:00",
    "updated_at": "2026-07-02T10:30:00",
    "messages": [
      {
        "id": 1,
        "conversation_id": 1,
        "role": "user",
        "content": "我想查一下这周的课表",
        "agent_name": null,
        "created_at": "2026-07-02T10:00:00"
      },
      {
        "id": 2,
        "conversation_id": 1,
        "role": "assistant",
        "content": "您这周的课程安排如下...",
        "agent_name": "schedule",
        "created_at": "2026-07-02T10:00:30"
      }
    ]
  }
}
```

**错误响应**:
```json
{
  "detail": "会话不存在或不属于当前用户"
}
```

---

### DELETE /api/ai/conversations/{conversation_id} — 关闭会话

**权限**: 需登录（只能关闭自己的会话）

**请求头**: `Authorization: Bearer <token>`

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| conversation_id | int | 会话 ID |

**响应**:
```json
{
  "data": {
    "message": "会话已关闭",
    "conversation_id": 1
  }
}
```

**错误响应**:
```json
{
  "detail": "会话不存在或不属于当前用户"
}
```

---

## Apifox 测试步骤

### 前置准备

1. **启动服务**
   ```bash
   # 1. 先启动 campus-service (端口 8001)
   cd campus-service
   uvicorn app.main:app --reload --port 8001

   # 2. 再启动 ai-service (端口 8002)
   cd ai-service
   uvicorn app.main:app --reload --port 8002
   ```

2. **获取 JWT Token**
   - 在 Apifox 中先调用 campus-service 的登录接口获取 token
   - 或手动生成测试 token

### 测试接口清单

#### 1. 健康检查（公开接口，无需认证）

```
GET http://localhost:8002/health
```

**预期**: 返回 200，status 为 "ok"

---

#### 2. 获取会话列表（需认证）

```
GET http://localhost:8002/api/ai/conversations
Headers:
  Authorization: Bearer <your_jwt_token>
```

**预期**: 返回 200，data 为数组

---

#### 3. 创建新会话

```
POST http://localhost:8002/api/ai/conversations
Headers:
  Authorization: Bearer <your_jwt_token>
  Content-Type: application/json
Body:
{
  "title": "测试对话"
}
```

**预期**: 返回 200，data 包含新建的会话信息（记住返回的 id）

---

#### 4. SSE 对话测试（核心功能）

```
POST http://localhost:8002/api/ai/chat
Headers:
  Authorization: Bearer <your_jwt_token>
  Content-Type: application/json
Body:
{
  "conversation_id": <上一步创建的会话ID>,  // 或 null
  "message": "我想查一下这周的课表"
}
```

**Apifox 配置**:
- 将 Response 设置为 `text/event-stream`
- 或使用 Apifox 的 WebSocket/SSE 功能

**预期 SSE 事件流**:
1. `thinking` 事件 → 正在分析
2. `agent_call` 事件 → 识别到意图为 schedule
3. 多个 `result` 事件 → 流式输出回答
4. `done` 事件 → 结束

---

#### 5. 测试不同意图

| 测试问题 | 预期意图 |
|----------|----------|
| "我想查一下这周的课表" | schedule |
| "我的报修进度怎么样了" | repair |
| "奖学金什么时候发" | scholarship |
| "最近有什么通知" | notice |
| "如何办理请假" | faq |
| "今天天气怎么样" | out_of_scope（超出范围） |
| "那个" | unclear（需澄清） |

---

#### 6. 获取会话详情

```
GET http://localhost:8002/api/ai/conversations/{conversation_id}
Headers:
  Authorization: Bearer <your_jwt_token>
```

**预期**: 返回 200，包含该会话的所有消息

---

#### 7. 关闭会话

```
DELETE http://localhost:8002/api/ai/conversations/{conversation_id}
Headers:
  Authorization: Bearer <your_jwt_token>
```

**预期**: 返回 200

---

### 测试 JWT Token 生成（用于本地测试）

如果暂时没有 campus-service 运行环境，可以使用 Python 生成测试 token：

```python
import jwt
import time

payload = {
    "sub": "20230001",
    "role": "student",
    "db_id": 1,
    "iat": int(time.time()),
    "exp": int(time.time()) + 86400  # 24小时后过期
}
token = jwt.encode(payload, "dev-secret-change-in-production", algorithm="HS256")
print(token)
```

---

### 常见错误排查

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| `JWT 已过期` | Token 超过 24 小时 | 重新登录获取新 token |
| `缺少 Authorization header` | 未携带 token | 添加 Authorization header |
| `会话不存在或不属于当前用户` | conversation_id 不存在或不属于当前用户 | 检查 conversation_id |
| SSE 无响应 | ai-service 未启动或连接 campus-service 失败 | 检查服务状态 |
| `campus-service 调用失败` | campus-service 未启动或接口错误 | 先确保 campus-service 正常运行 |
