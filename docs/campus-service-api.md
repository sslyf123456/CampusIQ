# Campus-Service API 文档

## 概述

- **服务名**: campus-service（校园后台支撑服务）
- **框架**: Python FastAPI
- **端口**: 8001
- **认证**: JWT Bearer Token（HS256，24h 过期）
- **统一响应格式**:
  - 分页列表: `{"data": [...], "total": N, "page": N, "page_size": N}`
  - 单条对象: 直接返回对象（无外层 data 包装）
  - 操作确认: `{"detail": "操作描述"}`
  - 错误: `{"detail": "错误描述"}`

## JWT 载荷

```json
{
  "sub": "20230001",
  "role": "student",
  "db_id": 1,
  "jti": "unique-token-id",
  "iat": 1720000000,
  "exp": 1720086400
}
```

- `sub`: 学号或管理员用户名
- `role`: `"student"` | `"admin"`
- `db_id`: 数据库主键 ID（Integer）
- `jti`: JWT 唯一标识，用于 Token 黑名单校验

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

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| username | string | 是 | 1-32 字符 | 学生学号或管理员用户名 |
| password | string | 是 | 1-64 字符 | 密码 |
| role | string | 是 | `"student"` / `"admin"` | 登录角色 |

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

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| old_password | string | 是 | - | 旧密码 |
| new_password | string | 是 | 6-64 字符 | 新密码 |

**响应**: `{"detail": "密码修改成功"}`

**说明**: 修改成功后当前 Token 加入黑名单立即失效，前端需清除登录态并跳转登录页强制重新登录。

---

### POST /api/campus/auth/logout — 退出登录

**权限**: 需登录

**请求头**: `Authorization: Bearer <token>`

**响应**: `{"detail": "已退出登录"}`

**说明**: 后端将该 JWT 的 `jti` 和 `user_sub` 写入 `campus.token_blacklist` 表，后续请求携带该 token 时返回 401。Token 过期后黑名单记录可通过定时任务清理。

---

## 2. 学生管理 `/api/campus/students`

### GET /api/campus/students — 学生列表

**权限**: admin

**参数**:
| 参数 | 类型 | 默认值 | 约束 | 说明 |
|------|------|--------|------|------|
| keyword | string | "" | 最大 64 字符 | 搜索关键词（学号/姓名/院系模糊匹配） |
| page | int | 1 | ≥ 1 | 页码 |
| page_size | int | 20 | 1-100 | 每页条数 |

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

**响应**: 直接返回学生对象（同列表中单条结构，无外层 data 包装）

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

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| student_id | string | 是 | 1-32 字符 | 学号，唯一 |
| name | string | 是 | 1-64 字符 | 姓名 |
| password | string | 是 | 6-64 字符 | 初始密码 |
| gender | string | 否 | `"male"` / `"female"` | 性别 |
| department | string | 否 | 最大 128 字符 | 院系 |
| major | string | 否 | 最大 128 字符 | 专业 |
| phone | string | 否 | 最大 20 字符 | 手机号 |
| email | string | 否 | 最大 128 字符 | 邮箱 |
| birth_date | date | 否 | - | 出生日期 |
| enrollment_year | int | 否 | - | 入学年份 |
| dorm_building | string | 否 | 最大 32 字符 | 宿舍楼 |
| dorm_room | string | 否 | 最大 16 字符 | 宿舍房间号 |

**响应**: 直接返回创建的学生对象（含 `id`），status code 201

---

### PUT /api/campus/students/{student_id} — 更新学生信息

**权限**: admin

**请求**: 同创建，所有字段可选（不含 `student_id` 和 `password`），只传需要更新的字段。

**响应**: 直接返回更新后的学生对象

---

### DELETE /api/campus/students/{student_id} — 删除学生

**权限**: admin

**响应**: `{"detail": "删除成功"}`

---

## 3. 课表管理 `/api/campus/schedules`

### GET /api/campus/schedules — 课表列表

**权限**: student / admin

- **学生**: 返回本人已选课程（通过 student_schedule 关联），支持学期筛选，返回 `{"data": [...]}` 格式（无分页）
- **管理员**: 返回全部课程，支持分页和学期筛选，返回 PaginatedResponse 格式

**参数（通用）**:
| 参数 | 类型 | 默认值 | 约束 | 说明 |
|------|------|--------|------|------|
| semester | string | "" | 最大 32 字符 | 学期筛选（如 "2025-2026-2"） |
| page | int | 1 | ≥ 1 | 页码（仅管理员生效） |
| page_size | int | 50 | 1-100 | 每页条数（仅管理员生效） |

**管理员响应**:
```json
{
  "data": [
    {
      "id": 1,
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
  ],
  "total": 30,
  "page": 1,
  "page_size": 50
}
```

**学生响应**:
```json
{
  "data": [
    {
      "id": 1,
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
  ]
}
```

**排序**: 学期降序（新学年优先） → 周几升序（周一优先） → ID 升序

---

### GET /api/campus/schedules/{schedule_id} — 课程详情

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

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| course_name | string | 是 | 1-128 字符 | 课程名称 |
| teacher | string | 否 | 最大 64 字符 | 任课老师 |
| weekday | int | 是 | 1-7 | 星期（1=周一 … 7=周日） |
| start_period | int | 是 | 1-12 | 开始节次 |
| end_period | int | 是 | 1-12 | 结束节次 |
| location | string | 否 | 最大 128 字符 | 上课教室 |
| start_week | int | 否 | 1-20, 默认 1 | 起始周次 |
| end_week | int | 否 | 1-20, 默认 16 | 结束周次 |
| semester | string | 否 | 最大 32 字符, 默认 "2025-2026-2" | 学期标识 |

**响应**: 直接返回创建的课程对象，status code 201

---

### PUT /api/campus/schedules/{schedule_id} — 更新课程

**权限**: admin

**请求**: 同创建，所有字段可选，只传需要更新的字段。

---

### DELETE /api/campus/schedules/{schedule_id} — 删除课程

**权限**: admin

**响应**: `{"detail": "删除成功"}`

---

### POST /api/campus/schedules/{schedule_id}/students — 添加选课学生

**权限**: admin

**请求**:
```json
{
  "student_ids": ["20230001", "20230002", "20230003"]
}
```

**响应**: `{"detail": "添加成功"}`

---

### DELETE /api/campus/schedules/{schedule_id}/students/{student_id} — 移除选课学生

**权限**: admin

**路径参数**: `student_id` 为学号字符串（如 "20230001"）

**响应**: `{"detail": "移除成功"}`

---

## 4. 宿舍报修 `/api/campus/repair-orders`

### GET /api/campus/repair-orders — 报修工单列表

**权限**: student（本人）/ admin（全部）

- **学生**: 返回本人报修工单
- **管理员**: 返回全部工单

**参数**:
| 参数 | 类型 | 默认值 | 约束 | 说明 |
|------|------|--------|------|------|
| page | int | 1 | ≥ 1 | 页码 |
| page_size | int | 20 | 1-100 | 每页条数 |
| status | string | "" | 最大 32 字符 | 状态筛选: pending / processing / completed |

**响应**:
```json
{
  "data": [
    {
      "id": 1,
      "student_id": 1,
      "description": "宿舍灯管坏了",
      "location": "3号楼308",
      "contact_phone": "13800001111",
      "status": "pending",
      "handler": null,
      "handle_note": null,
      "submitted_at": "2026-07-01T10:00:00",
      "processed_at": null,
      "completed_at": null
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20
}
```

---

### GET /api/campus/repair-orders/{order_id} — 工单详情

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

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| description | string | 是 | 最少 1 字符 | 问题描述 |
| location | string | 否 | 最大 128 字符 | 报修地点 |
| contact_phone | string | 否 | 最大 32 字符 | 联系方式 |

**响应**: 直接返回创建的工单对象，status code 201

---

### PUT /api/campus/repair-orders/{order_id} — 更新工单状态

**权限**: admin

**请求**:
```json
{
  "status": "processing",
  "handler": "维修员张师傅",
  "handle_note": "已上门查看，需更换灯管"
}
```

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| status | string | 是 | `"pending"` / `"processing"` / `"completed"` | 工单状态 |
| handler | string | 否 | 最大 64 字符 | 维修人员 |
| handle_note | string | 否 | - | 处理备注 |

- status 设为 `processing` 时自动记录 `processed_at`
- status 设为 `completed` 时自动记录 `completed_at`

**响应**: 直接返回更新后的工单对象

---

## 5. 奖助记录 `/api/campus/scholarships`

### GET /api/campus/scholarships — 奖助记录列表

**权限**: student（本人）/ admin（全部）

**参数**:
| 参数 | 类型 | 默认值 | 约束 | 说明 |
|------|------|--------|------|------|
| page | int | 1 | ≥ 1 | 页码 |
| page_size | int | 20 | 1-100 | 每页条数 |
| status | string | "" | 最大 32 字符 | 状态筛选: pending / approved / rejected |

**管理员响应**:
```json
{
  "data": [
    {
      "id": 1,
      "student_id": 1,
      "student_no": "20230001",
      "student_name": "张三",
      "type": "奖学金",
      "name": "国家奖学金",
      "amount": 8000.00,
      "status": "approved",
      "semester": "2025-2026-1",
      "note": "综合测评排名年级前5%",
      "created_at": "2026-06-01T10:00:00",
      "updated_at": "2026-06-15T10:00:00"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

**说明**: 管理员端响应包含 `student_no`（学号字符串）和 `student_name`（姓名）字段，用于展示关联学生信息。学生端响应不含这两个字段。排序为 `created_at` 降序。

---

### GET /api/campus/scholarships/{record_id} — 记录详情

**权限**: student（仅本人）/ admin

**响应**: 直接返回奖助记录对象。管理员端含 `student_no` 和 `student_name`，含 `created_at` 和 `updated_at`。

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

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| student_id | string | 是 | 1-32 字符 | 学号（字符串，如 "20230001"） |
| type | string | 是 | 最大 64 字符 | 类型：奖学金 / 助学金 |
| name | string | 是 | 1-128 字符 | 奖项名称 |
| amount | decimal | 否 | ≥ 0, 最大 10 位 2 小数 | 金额（元） |
| status | string | 否 | `"pending"` / `"approved"` / `"rejected"`, 默认 "pending" | 发放状态 |
| semester | string | 否 | 最大 32 字符, 默认 "2025-2026-2" | 学期 |
| note | string | 否 | - | 备注 |

**响应**: 直接返回创建的奖助记录对象，status code 201

---

### PUT /api/campus/scholarships/{record_id} — 更新奖助记录

**权限**: admin

**请求**: 同创建，所有字段可选（不含 `student_id`），只传需要更新的字段。

---

### DELETE /api/campus/scholarships/{record_id} — 删除奖助记录

**权限**: admin

**响应**: `{"detail": "删除成功"}`

---

## 6. 校园通知 `/api/campus/notices`

### GET /api/campus/notices — 通知列表

**权限**: 需登录（学生和管理员均可）

**参数**:
| 参数 | 类型 | 默认值 | 约束 | 说明 |
|------|------|--------|------|------|
| keyword | string | "" | 最大 255 字符 | 标题/正文关键词搜索 |
| category | string | "" | 最大 64 字符 | 分类筛选: academic / dormitory / scholarship / general |
| page | int | 1 | ≥ 1 | 页码 |
| page_size | int | 20 | 1-100 | 每页条数 |

**响应**:
```json
{
  "data": [
    {
      "id": 1,
      "title": "关于选课的通知",
      "content": "选课系统将于下周一开放...",
      "category": "academic",
      "publisher": "教务处",
      "published_at": "2026-07-01T09:00:00",
      "updated_at": "2026-07-01T09:00:00",
      "created_by": 1
    }
  ],
  "total": 20,
  "page": 1,
  "page_size": 20
}
```

**排序**: `published_at` 降序

---

### GET /api/campus/notices/{notice_id} — 通知详情

**权限**: 需登录

**响应**: 直接返回通知对象，含 `updated_at` 字段

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

| 参数 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| title | string | 是 | 1-255 字符 | 通知标题 |
| content | string | 是 | 最少 1 字符 | 通知正文 |
| category | string | 否 | `"academic"` / `"dormitory"` / `"scholarship"` / `"general"`, 默认 "general" | 分类 |
| publisher | string | 否 | 最大 64 字符 | 发布人 |

**响应**: 直接返回创建的通知对象（含 `published_at`、`updated_at`、`created_by`），status code 201

---

### PUT /api/campus/notices/{notice_id} — 编辑通知

**权限**: admin

**请求**: 同创建，所有字段可选，只传需要更新的字段。`updated_at` 自动维护（onupdate）。

---

### DELETE /api/campus/notices/{notice_id} — 删除通知

**权限**: admin

**响应**: `{"detail": "删除成功"}`

---

## 7. 内部接口 `/api/campus/internal`

> 供 ai-service 调用，复用 JWT 认证，student_id 从 JWT 解析实现数据隔离。

### GET /api/campus/internal/schedule — 查询课表

**权限**: JWT(student)，非 student 返回空数组

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| semester | string | "" | 学期筛选（可选） |

**响应**:
```json
{
  "data": [
    {
      "id": 1,
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
  ]
}
```

---

### GET /api/campus/internal/repair — 查询报修工单

**权限**: JWT(student)

**响应**:
```json
{
  "data": [
    {
      "id": 1,
      "student_id": 1,
      "description": "宿舍灯管坏了",
      "location": "3号楼308",
      "contact_phone": "13800001111",
      "status": "pending",
      "handler": null,
      "handle_note": null,
      "submitted_at": "2026-07-01T10:00:00",
      "processed_at": null,
      "completed_at": null
    }
  ]
}
```

---

### GET /api/campus/internal/scholarship — 查询奖助记录

**权限**: JWT(student)

**响应**:
```json
{
  "data": [
    {
      "id": 1,
      "student_id": 1,
      "student_no": "20230001",
      "student_name": "张三",
      "type": "奖学金",
      "name": "国家奖学金",
      "amount": 8000.00,
      "status": "approved",
      "semester": "2025-2026-1",
      "note": "综合测评排名年级前5%",
      "created_at": "2026-06-01T10:00:00",
      "updated_at": "2026-06-15T10:00:00"
    }
  ]
}
```

---

### GET /api/campus/internal/notices — 检索通知

**权限**: JWT(任意)

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| keyword | string | "" | 关键词搜索，返回最多 10 条 |

**响应**:
```json
{
  "data": [
    {
      "id": 1,
      "title": "关于选课的通知",
      "content": "选课系统将于下周一开放...",
      "category": "academic",
      "publisher": "教务处",
      "published_at": "2026-07-01T09:00:00",
      "updated_at": "2026-07-01T09:00:00",
      "created_by": 1
    }
  ]
}
```

---

## 8. 错误处理

### 422 参数校验错误

Pydantic 校验失败时返回中文错误信息（已通过自定义异常处理器统一处理）：

```json
{
  "detail": "参数校验失败: student_id - 字段长度不能超过32个字符"
}
```

### 其他常见错误

| HTTP 状态码 | detail 值 | 说明 |
|-------------|-----------|------|
| 401 | `"未登录或登录已过期"` | 未携带 Token |
| 401 | `"Token无效或已过期"` | Token 解析失败 |
| 401 | `"Token已失效，请重新登录"` | Token 在黑名单中 |
| 403 | `"需要管理员权限"` | 非管理员访问 admin-only 接口 |
| 403 | `"需要学生身份"` | 非学生访问 student-only 接口 |
| 404 | `"xxx不存在"` | 资源未找到 |
| 503 | `"数据库服务不可用，请稍后重试"` | 数据库连接失败（黑名单校验时） |
