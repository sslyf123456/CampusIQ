# Campus-Service API 文档

## 概述

- **服务名**: campus-service（校园后台支撑服务）
- **框架**: Python FastAPI
- **端口**: 8001
- **认证**: JWT Bearer Token（HS256，24h 过期）
- **统一响应格式**:
  - 成功: `{"data": {...}}` 或 `{"data": [...], "total": N, "page": N, "page_size": N}`
  - 错误: `{"detail": "错误描述"}`

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

- `sub`: 学号或管理员用户名
- `role`: `"student"` | `"admin"`
- `db_id`: 数据库主键 ID

---

## 1. 认证模块 `/api/campus/auth`

### POST /api/campus/auth/login — 登录

**权限**: 公开

**请求**:
```json
{
  "username": "20230001",
  "password": "123456",
  "role": "student"
}
```

**响应**:
```json
{
  "token": "eyJhbGciOi...",
  "user": {
    "role": "student",
    "username": "20230001",
    "name": "张三"
  }
}
```

**说明**: `role` 指定登录角色，`student` 用学号登录（查 students 表），`admin` 用用户名登录（查 admins 表）。前端登录入口通过角色切换区分。

---

### GET /api/campus/auth/me — 获取当前用户信息

**权限**: 需登录

**请求头**: `Authorization: Bearer <token>`

**响应（学生）**:
```json
{
  "role": "student",
  "student_id": "20230001",
  "name": "张三",
  "gender": "male",
  "department": "计算机科学与技术",
  "major": "计算机科学与技术",
  "phone": "13800001111",
  "email": "zhangsan@campus.edu.cn",
  "birth_date": "2004-03-15",
  "enrollment_year": 2023,
  "dorm_building": "3号楼",
  "dorm_room": "308"
}
```

**响应（管理员）**:
```json
{
  "role": "admin",
  "username": "admin",
  "name": "系统管理员",
  "phone": "13800000000",
  "email": "admin@campus.edu.cn"
}
```

---

### PUT /api/campus/auth/password — 修改密码

**权限**: 需登录

**请求**:
```json
{
  "old_password": "123456",
  "new_password": "654321"
}
```

**响应**: `{"detail": "密码修改成功"}`

---

### POST /api/campus/auth/logout — 退出登录

**权限**: 需登录

**请求头**: `Authorization: Bearer <token>`

**响应**: `{"detail": "已退出登录"}`

**说明**: 后端将该 JWT 的 `jti` 写入 `campus.token_blacklist` 表，后续请求携带该 token 时返回 401（Token已失效，请重新登录）。token 过期后黑名单记录自动失效，可通过定时任务清理。

---

## 2. 学生管理 `/api/campus/students`

### GET /api/campus/students — 学生列表

**权限**: admin

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| keyword | string | "" | 搜索关键词（学号/姓名/院系模糊匹配） |
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页条数（最大 100） |

**响应**:
```json
{
  "data": [
    {
      "id": 1,
      "student_id": "20230001",
      "name": "张三",
      "gender": "male",
      "department": "计算机科学与技术",
      "major": "计算机科学与技术",
      "phone": "13800001111",
      "email": "zhangsan@campus.edu.cn",
      "birth_date": "2004-03-15",
      "enrollment_year": 2023,
      "dorm_building": "3号楼",
      "dorm_room": "308"
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20
}
```

---

### GET /api/campus/students/{student_id} — 学生详情

**权限**: admin

---

### POST /api/campus/students — 创建学生

**权限**: admin

**请求**:
```json
{
  "student_id": "20240099",
  "name": "新同学",
  "password": "123456",
  "gender": "male",
  "department": "计算机科学与技术",
  "major": "软件工程",
  "phone": "13800009999",
  "email": "xin@campus.edu.cn",
  "birth_date": "2005-06-01",
  "enrollment_year": 2024,
  "dorm_building": "5号楼",
  "dorm_room": "301"
}
```

---

### PUT /api/campus/students/{student_id} — 更新学生信息

**权限**: admin

**请求**: 同创建，所有字段可选，只传需要更新的字段。

---

### DELETE /api/campus/students/{student_id} — 删除学生

**权限**: admin

**响应**: `{"detail": "删除成功"}`

---

## 3. 课表管理 `/api/campus/schedules`

### GET /api/campus/schedules — 课表列表

**权限**: student / admin

- **学生**: 返回本人已选课程（通过 student_schedule 关联）
- **管理员**: 返回全部课程，支持分页和学期筛选

**参数（管理员）**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 50 | 每页条数 |
| semester | string | "" | 学期筛选 |

---

### GET /api/campus/schedules/{id} — 课程详情

**权限**: admin

---

### POST /api/campus/schedules — 创建课程

**权限**: admin

**请求**:
```json
{
  "course_name": "高级软件设计",
  "teacher": "刘老师",
  "weekday": 1,
  "start_period": 1,
  "end_period": 2,
  "location": "教学楼A101",
  "start_week": 1,
  "end_week": 16,
  "semester": "2025-2026-2"
}
```

---

### PUT /api/campus/schedules/{id} — 更新课程

**权限**: admin

---

### DELETE /api/campus/schedules/{id} — 删除课程

**权限**: admin

---

### POST /api/campus/schedules/{id}/students — 添加选课学生

**权限**: admin

**请求**:
```json
{
  "student_ids": ["20230001", "20230002", "20230003"]
}
```

---

### DELETE /api/campus/schedules/{id}/students/{student_id} — 移除选课学生

**权限**: admin

---

## 4. 宿舍报修 `/api/campus/repair-orders`

### GET /api/campus/repair-orders — 报修工单列表

**权限**: student / admin

- **学生**: 返回本人报修工单
- **管理员**: 返回全部工单

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页条数 |
| status | string | "" | 状态筛选: pending / processing / completed |

---

### GET /api/campus/repair-orders/{id} — 工单详情

**权限**: student（仅本人）/ admin

---

### POST /api/campus/repair-orders — 发起报修

**权限**: student

**请求**:
```json
{
  "description": "宿舍灯管坏了",
  "location": "3号楼308",
  "contact_phone": "13800001111"
}
```

---

### PUT /api/campus/repair-orders/{id} — 更新工单状态

**权限**: admin

**请求**:
```json
{
  "status": "processing",
  "handler": "维修员张师傅",
  "handle_note": "已上门查看，需更换灯管"
}
```

- status 设为 `processing` 时自动记录 `processed_at`
- status 设为 `completed` 时自动记录 `completed_at`

---

## 5. 奖助记录 `/api/campus/scholarships`

### GET /api/campus/scholarships — 奖助记录列表

**权限**: student（本人）/ admin（全部）

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页条数 |
| status | string | "" | 状态筛选: pending / approved / rejected |

---

### GET /api/campus/scholarships/{id} — 记录详情

**权限**: student（仅本人）/ admin

---

### POST /api/campus/scholarships — 创建奖助记录

**权限**: admin

**请求**:
```json
{
  "student_id": "20230001",
  "type": "奖学金",
  "name": "国家奖学金",
  "amount": 8000.00,
  "status": "approved",
  "semester": "2025-2026-1",
  "note": "综合测评排名年级前5%"
}
```

---

### PUT /api/campus/scholarships/{id} — 更新奖助记录

**权限**: admin

---

### DELETE /api/campus/scholarships/{id} — 删除奖助记录

**权限**: admin

---

## 6. 校园通知 `/api/campus/notices`

### GET /api/campus/notices — 通知列表

**权限**: 需登录（学生和管理员均可）

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| keyword | string | "" | 标题/正文关键词搜索 |
| category | string | "" | 分类筛选: academic / dormitory / scholarship / general |
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页条数 |

---

### GET /api/campus/notices/{id} — 通知详情

**权限**: 需登录

---

### POST /api/campus/notices — 发布通知

**权限**: admin

**请求**:
```json
{
  "title": "关于选课的通知",
  "content": "选课系统将于下周一开放...",
  "category": "academic",
  "publisher": "教务处"
}
```

---

### PUT /api/campus/notices/{id} — 编辑通知

**权限**: admin

---

### DELETE /api/campus/notices/{id} — 删除通知

**权限**: admin

---

## 7. 内部接口 `/api/campus/internal`

> 供 ai-service 调用，复用 JWT 认证，student_id 从 JWT 解析实现数据隔离。

### GET /api/campus/internal/schedule — 查询课表

**权限**: JWT(student)，非 student 返回空数组

---

### GET /api/campus/internal/repair — 查询报修工单

**权限**: JWT(student)

---

### GET /api/campus/internal/scholarship — 查询奖助记录

**权限**: JWT(student)

---

### GET /api/campus/internal/notices — 检索通知

**权限**: JWT(任意)

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| keyword | string | "" | 关键词搜索，返回最多 10 条 |
