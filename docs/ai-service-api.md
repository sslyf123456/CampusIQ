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
  "sub": "2023001001",
  "role": "student",
  "db_id": 1,
  "iat": 1720000000,
  "exp": 1720086400
}
```

- `sub`: 学号字符串
- `role`: `"student"` | `"admin"`
- `db_id`: 数据库主键 ID（**Integer**，用于关联 conversations 表的 student_id 字段）

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
- `student`: 学生信息查询 Agent（仅管理员）
- `faq`: FAQ 知识库兜底 Agent

**意图识别结果**:

| 意图 | 触发条件 | 返回的 Agent |
|------|----------|--------------|
| schedule | 询问课程安排、上课时间、教室等 | schedule |
| repair | 询问报修进度、报修记录等 | repair |
| scholarship | 询问奖学金、助学金等 | scholarship |
| notice | 寻找校园通知、公告等 | notice |
| student | 询问学生名单、学生详情、院系学生等（仅管理员） | student |
| faq | 校园常见问题（选课、宿舍管理等） | faq |
| unclear | 问题不明确 | clarify 反问 |
| out_of_scope | 问题超出校园服务范围 | error + 兜底消息 |

**角色化系统提示词**: ai-service 根据 JWT 中的 `role` 字段（student / admin）注入不同的系统提示词：
- **学生版**: 强调个人数据范围（仅本人课表/报修/奖助），语气亲切友好
- **管理员版**: 强调全校数据范围，语气专业简洁，便于管理决策
- **服务器时间注入**: 系统提示词末尾自动拼接服务器当前时间（含星期），格式如 `当前服务器时间：2026年07月04日 星期六 00:20`，使 AI 能正确理解"本学期""本周""今天"等相对时间词
- **注入范围**: 全链路生效 — MasterAgent 意图识别、所有 Sub-Agent LLM 调用、最终回答 LLM 调用，均通过 `get_system_prompt(role)` 统一注入

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

**响应**（直接返回数组，无 data 包裹）:
```json
[
  {
    "id": 1,
    "student_id": 1,
    "title": "新对话",
    "status": "active",
    "created_at": "2026-07-02T10:00:00",
    "updated_at": "2026-07-02T10:30:00"
  }
]
```

**说明**: 只返回当前用户的 active 状态会话，按更新时间倒序排列。`student_id` 为 **Integer** 类型（数据库主键）。

---

### POST /api/ai/conversations — 创建会话

**权限**: 需登录

**请求头**: `Authorization: Bearer <token>` `Content-Type: application/json`

**请求**:
```json
{
  "title": "我的选课咨询"
}
```

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| title | string | 否 | "新对话" | 会话标题（最大 200 字符） |

**响应**（直接返回对象，无 data 包裹）:
```json
{
  "id": 2,
  "student_id": 1,
  "title": "我的选课咨询",
  "status": "active",
  "created_at": "2026-07-02T11:00:00",
  "updated_at": "2026-07-02T11:00:00"
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

**响应**（直接返回对象，无 data 包裹）:
```json
{
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
      "metadata_": null,
      "created_at": "2026-07-02T10:00:00"
    },
    {
      "id": 2,
      "conversation_id": 1,
      "role": "assistant",
      "content": "您这周的课程安排如下...",
      "agent_name": "schedule",
      "metadata_": null,
      "created_at": "2026-07-02T10:00:30"
    }
  ]
}
```

**错误响应**:
```json
{
  "detail": "会话不存在或不属于当前用户"
}
```

---

### DELETE /api/ai/conversations/{conversation_id} — 删除会话

**权限**: 需登录（只能删除自己的会话）

**说明**: 逻辑删除，将会话 status 设为 closed，删除后不再出现在会话列表中，但数据仍保留在数据库。不可恢复。

**请求头**: `Authorization: Bearer <token>`

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| conversation_id | int | 会话 ID |

**响应**:
```json
{
  "message": "会话已删除",
  "conversation_id": 1
}
```

**错误响应**:
```json
{
  "detail": "会话不存在或不属于当前用户"
}
```

---

## 常见错误排查

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| `JWT 已过期` | Token 过期 | 重新登录获取新 token |
| `缺少 Authorization header` | 未携带 token | 添加 Authorization header |
| `JWT 无效: ...` | Token 签名不匹配或格式错误 | 确认 JWT_SECRET 与 campus-service 一致 |
| `会话不存在或不属于当前用户` | conversation_id 不存在或不属于当前用户 | 检查 conversation_id 和 db_id |
| SSE 无响应 | ai-service 未启动或连接 campus-service 失败 | 检查服务状态 |
| `campus-service 调用失败` | campus-service 未启动或接口错误 | 先确保 campus-service 正常运行 |
