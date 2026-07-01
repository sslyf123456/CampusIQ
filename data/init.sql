-- ============================================================
-- Campus QA Assistant - 数据库初始化脚本
-- 数据库：PostgreSQL 16 + pgvector 扩展
-- 字符集：UTF8
-- ============================================================

-- 启用 pgvector 扩展（用于 ai_campus.faq_embeddings 向量列）
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- Schema 1: campus（校园业务数据，归属 campus-service）
-- ============================================================
CREATE SCHEMA IF NOT EXISTS campus;

-- --------------------------
-- 学生表
-- --------------------------
CREATE TABLE IF NOT EXISTS campus.students (
    id              SERIAL PRIMARY KEY,
    student_id      VARCHAR(32)  NOT NULL UNIQUE,       -- 学号，也作为登录账号
    name            VARCHAR(64)  NOT NULL,               -- 姓名
    password_hash   VARCHAR(255) NOT NULL,               -- 密码哈希（bcrypt）
    gender          VARCHAR(8)   CHECK (gender IN ('male', 'female')), -- 性别
    department      VARCHAR(128),                         -- 院系
    major           VARCHAR(128),                         -- 专业
    phone           VARCHAR(20),                          -- 手机号
    email           VARCHAR(128),                         -- 邮箱
    birth_date      DATE,                                 -- 出生日期
    enrollment_year INT,                                  -- 入学年份（哪一届）
    dorm_building   VARCHAR(32),                          -- 宿舍楼
    dorm_room       VARCHAR(16),                          -- 宿舍房间号
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_students_student_id ON campus.students(student_id);
CREATE INDEX IF NOT EXISTS idx_students_enrollment_year ON campus.students(enrollment_year);

COMMENT ON TABLE  campus.students IS '学生表';
COMMENT ON COLUMN campus.students.student_id IS '学号，登录账号，唯一';
COMMENT ON COLUMN campus.students.gender IS 'male=男，female=女';
COMMENT ON COLUMN campus.students.enrollment_year IS '入学年份，标识哪一届学生，如 2023';

-- --------------------------
-- 管理员表
-- --------------------------
CREATE TABLE IF NOT EXISTS campus.admins (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(32)  NOT NULL UNIQUE,          -- 登录账号
    name          VARCHAR(64)  NOT NULL,                  -- 姓名
    password_hash VARCHAR(255) NOT NULL,                  -- 密码哈希（bcrypt）
    phone         VARCHAR(20),                           -- 手机号
    email         VARCHAR(128),                          -- 邮箱
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_admins_username ON campus.admins(username);

COMMENT ON TABLE  campus.admins IS '管理员表';

-- --------------------------
-- 课表
-- --------------------------
CREATE TABLE IF NOT EXISTS campus.schedules (
    id            SERIAL PRIMARY KEY,
    course_name   VARCHAR(128) NOT NULL,               -- 课程名称
    teacher       VARCHAR(64),                          -- 任课老师
    weekday       INT          NOT NULL                  -- 星期几（1=周一 … 7=周日）
                  CHECK (weekday BETWEEN 1 AND 7),
    start_period  INT          NOT NULL                  -- 开始节次（如 1 表示第1节）
                  CHECK (start_period BETWEEN 1 AND 12),
    end_period    INT          NOT NULL                  -- 结束节次
                  CHECK (end_period BETWEEN 1 AND 12),
    location      VARCHAR(128),                         -- 上课教室
    start_week    INT          NOT NULL DEFAULT 1,       -- 起始周次
    end_week      INT          NOT NULL DEFAULT 16,      -- 结束周次
    semester      VARCHAR(32)  NOT NULL DEFAULT '2025-2026-2',  -- 学期
    created_by    INT          REFERENCES campus.admins(id) ON DELETE SET NULL,
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_schedules_semester ON campus.schedules(semester);
CREATE INDEX IF NOT EXISTS idx_schedules_weekday ON campus.schedules(weekday);

COMMENT ON TABLE  campus.schedules IS '课表：管理员维护，学生查询';
COMMENT ON COLUMN campus.schedules.weekday IS '1=周一，7=周日';
COMMENT ON COLUMN campus.schedules.start_period IS '开始节次，如 1';
COMMENT ON COLUMN campus.schedules.end_period IS '结束节次，如 2';

-- --------------------------
-- 学生-课表关联（多对多：一个学生可选多门课，一门课有多个学生）
-- --------------------------
CREATE TABLE IF NOT EXISTS campus.student_schedule (
    student_id   INT NOT NULL REFERENCES campus.students(id) ON DELETE CASCADE,
    schedule_id  INT NOT NULL REFERENCES campus.schedules(id) ON DELETE CASCADE,
    PRIMARY KEY (student_id, schedule_id)
);

COMMENT ON TABLE campus.student_schedule IS '学生-课程关联表：多对多';

-- --------------------------
-- 宿舍报修工单
-- --------------------------
CREATE TABLE IF NOT EXISTS campus.repair_orders (
    id              SERIAL PRIMARY KEY,
    student_id      INT          NOT NULL REFERENCES campus.students(id) ON DELETE CASCADE,
    description     TEXT         NOT NULL,                   -- 问题描述
    location        VARCHAR(128),                          -- 报修地点（如"3号宿舍楼308"）
    contact_phone   VARCHAR(32),                          -- 联系方式
    status          VARCHAR(32)  NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'processing', 'completed')),
    handler         VARCHAR(64),                          -- 维修人员
    handle_note     TEXT,                                 -- 处理备注
    submitted_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),  -- 提交时间
    processed_at    TIMESTAMPTZ,                          -- 处理时间
    completed_at    TIMESTAMPTZ                           -- 完成时间
);

CREATE INDEX IF NOT EXISTS idx_repair_student ON campus.repair_orders(student_id);
CREATE INDEX IF NOT EXISTS idx_repair_status ON campus.repair_orders(status);

COMMENT ON TABLE  campus.repair_orders IS '宿舍报修工单';
COMMENT ON COLUMN campus.repair_orders.status IS 'pending=待处理，processing=处理中，completed=已完成';

-- --------------------------
-- 奖助记录
-- --------------------------
CREATE TABLE IF NOT EXISTS campus.scholarship_records (
    id              SERIAL PRIMARY KEY,
    student_id      INT          NOT NULL REFERENCES campus.students(id) ON DELETE CASCADE,
    type            VARCHAR(64)  NOT NULL,               -- 类型：奖学金/助学金
    name            VARCHAR(128) NOT NULL,               -- 名称（如"国家奖学金"）
    amount          NUMERIC(10,2),                       -- 金额（元）
    status          VARCHAR(32)  NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'approved', 'rejected')),
    semester        VARCHAR(32)  NOT NULL DEFAULT '2025-2026-2',
    note            TEXT,                                 -- 备注
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scholarship_student ON campus.scholarship_records(student_id);
CREATE INDEX IF NOT EXISTS idx_scholarship_status ON campus.scholarship_records(status);

COMMENT ON TABLE  campus.scholarship_records IS '奖助记录';
COMMENT ON COLUMN campus.scholarship_records.type IS '奖学金 / 助学金';
COMMENT ON COLUMN campus.scholarship_records.status IS 'pending=审核中，approved=已发放，rejected=已拒绝';

-- --------------------------
-- 校园通知
-- --------------------------
CREATE TABLE IF NOT EXISTS campus.notices (
    id              SERIAL PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,               -- 通知标题
    content         TEXT         NOT NULL,               -- 通知正文
    category        VARCHAR(64)  NOT NULL DEFAULT 'general'
                    CHECK (category IN ('academic', 'dormitory', 'scholarship', 'general')),
    publisher       VARCHAR(64),                          -- 发布人
    published_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      INT          REFERENCES campus.admins(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_notices_category ON campus.notices(category);
CREATE INDEX IF NOT EXISTS idx_notices_published ON campus.notices(published_at DESC);

COMMENT ON TABLE  campus.notices IS '校园通知公告：管理员发布，学生检索查看';
COMMENT ON COLUMN campus.notices.category IS 'academic=教务，dormitory=后勤，scholarship=评奖，general=通用';

-- --------------------------
-- Token 黑名单表（退出登录后使 JWT 失效）
-- --------------------------
CREATE TABLE IF NOT EXISTS campus.token_blacklist (
    id          SERIAL PRIMARY KEY,
    jti         VARCHAR(64)  NOT NULL UNIQUE,              -- JWT ID（唯一标识）
    user_sub    VARCHAR(64)  NOT NULL,                     -- 用户标识（学号或管理员用户名）
    expires_at  TIMESTAMPTZ  NOT NULL,                     -- Token 原始过期时间
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_token_blacklist_jti ON campus.token_blacklist(jti);
CREATE INDEX IF NOT EXISTS idx_token_blacklist_expires ON campus.token_blacklist(expires_at);

COMMENT ON TABLE  campus.token_blacklist IS '已退出的 JWT 黑名单，过期后自动清理';

-- ============================================================
-- Schema 2: ai_campus（AI 问答数据，归属 ai-service）
-- ============================================================
CREATE SCHEMA IF NOT EXISTS ai_campus;

-- --------------------------
-- FAQ 向量嵌入表（pgvector）
-- 存储校园 FAQ 文档的分块向量，用于 RAG 检索
-- --------------------------
CREATE TABLE IF NOT EXISTS ai_campus.faq_embeddings (
    id          SERIAL PRIMARY KEY,
    document    VARCHAR(255) NOT NULL,                   -- 来源文档名（如 course_selection.md）
    chunk_index INT          NOT NULL,                   -- 分块序号
    content     TEXT         NOT NULL,                   -- 原始文本片段
    embedding   VECTOR(1536) NOT NULL,                  -- 向量（OpenAI text-embedding-3-small 为 1536 维）
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- pgvector 余弦距离索引（IVFFlat，加速 Top-K 检索）
CREATE INDEX idx_faq_embedding ON ai_campus.faq_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

COMMENT ON TABLE  ai_campus.faq_embeddings IS 'FAQ 文档向量嵌入表，用于 RAG 检索';
COMMENT ON COLUMN ai_campus.faq_embeddings.embedding IS '向量维度取决于 Embedding 模型，OpenAI text-embedding-3-small 为 1536';

-- --------------------------
-- 会话表
-- --------------------------
CREATE TABLE IF NOT EXISTS ai_campus.conversations (
    id          SERIAL PRIMARY KEY,
    student_id  INT          NOT NULL REFERENCES campus.students(id) ON DELETE CASCADE,
    title       VARCHAR(255) DEFAULT '新对话',          -- 会话标题（可由 LLM 自动摘要生成）
    status      VARCHAR(32)  NOT NULL DEFAULT 'active'
                CHECK (status IN ('active', 'closed')),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversations_student ON ai_campus.conversations(student_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON ai_campus.conversations(status);

COMMENT ON TABLE  ai_campus.conversations IS 'AI 问答会话';
COMMENT ON COLUMN ai_campus.conversations.status IS 'active=活跃，closed=已关闭';

-- --------------------------
-- 消息表
-- --------------------------
CREATE TABLE IF NOT EXISTS ai_campus.messages (
    id              SERIAL PRIMARY KEY,
    conversation_id INT          NOT NULL REFERENCES ai_campus.conversations(id) ON DELETE CASCADE,
    role            VARCHAR(32)  NOT NULL
                    CHECK (role IN ('user', 'assistant', 'system')),
    content         TEXT         NOT NULL,               -- 消息内容
    agent_name      VARCHAR(64),                          -- 产生该消息的 Agent 名称（如 ScheduleAgent），用户消息为 NULL
    metadata        JSONB,                                 -- 附加信息（如 SSE 事件类型、推理步骤等）
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON ai_campus.messages(conversation_id, created_at);

COMMENT ON TABLE  ai_campus.messages IS '会话中的单条消息';
COMMENT ON COLUMN ai_campus.messages.role IS 'user=用户，assistant=AI，system=系统';
COMMENT ON COLUMN ai_campus.messages.agent_name IS '记录是哪条 Agent 产生的回复，用于前端展示推理过程';
COMMENT ON COLUMN ai_campus.messages.metadata IS 'JSONB，存储 SSE 事件、Agent 推理步骤等附加信息';

