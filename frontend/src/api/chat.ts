import request from './request'
import { getToken } from '@/utils/token'
import type { Conversation, ConversationDetail, SSEEventType, SSEEventData } from '@/types/chat'

/** 获取会话列表 */
export function getConversationsApi() {
  return request.get<Conversation[]>('/ai/conversations').then(res => res.data)
}

/** 创建新会话 */
export function createConversationApi(title: string = '新对话') {
  return request.post<Conversation>('/ai/conversations', { title }).then(res => res.data)
}

/** 获取会话详情（含消息列表） */
export function getConversationDetailApi(id: number) {
  return request.get<ConversationDetail>(`/ai/conversations/${id}`).then(res => res.data)
}

/** 关闭/删除会话 */
export function closeConversationApi(id: number) {
  return request.delete(`/ai/conversations/${id}`).then(res => res.data)
}

/**
 * SSE 流式对话
 * 用 fetch + ReadableStream 解析 SSE（axios 不支持流式）
 */
export async function chatStreamApi(
  conversationId: number | null,
  message: string,
  onEvent: (event: SSEEventType, data: SSEEventData) => void,
): Promise<void> {
  const token = getToken()
  const res = await fetch('/api/ai/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      message,
    }),
  })

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`)
  }

  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    // 按 SSE 事件分隔（双换行）
    const parts = buffer.split('\n\n')
    buffer = parts.pop() || ''

    for (const part of parts) {
      const lines = part.split('\n')
      let eventType: string = 'message'
      let dataStr: string = ''

      for (const line of lines) {
        if (line.startsWith('event:')) {
          eventType = line.slice(6).trim()
        } else if (line.startsWith('data:')) {
          dataStr += line.slice(5).trim()
        }
      }

      if (eventType && dataStr) {
        let data: SSEEventData = {}
        try {
          data = JSON.parse(dataStr)
        } catch {
          data = { content: dataStr }
        }
        onEvent(eventType as SSEEventType, data)
      }
    }
  }
}
