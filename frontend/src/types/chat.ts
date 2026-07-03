/** SSE 事件类型 */
export type SSEEventType = 'thinking' | 'agent_call' | 'result' | 'clarify' | 'error' | 'done'

/** SSE 事件数据 */
export interface SSEEventData {
  content?: string
  clarify?: boolean
  agent?: string
  description?: string
  question?: string
  message?: string
  fallback?: boolean
}

/** 消息 */
export interface ChatMessage {
  id: number
  conversation_id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  agent_name?: string | null
  created_at: string
}

/** 会话 */
export interface Conversation {
  id: number
  student_id: string
  title: string
  status: 'active' | 'closed'
  created_at: string
  updated_at: string
}

/** 会话详情（含消息列表） */
export interface ConversationDetail extends Conversation {
  messages: ChatMessage[]
}

/** Agent 推理步骤（前端临时数据结构） */
export interface AgentStep {
  type: 'thinking' | 'agent_call'
  content: string
  agent?: string
}
