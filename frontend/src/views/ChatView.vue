<template>
  <div class="chat-page">
    <el-card shadow="never" class="chat-card">
      <div class="chat-body">
        <!-- 左侧会话列表 -->
        <div class="sidebar">
          <div class="sidebar-header">
            <el-button type="primary" size="small" @click="handleNewConversation" style="width: 100%;">
              新建对话
            </el-button>
          </div>
          <div class="conversation-list">
            <div
              v-for="conv in conversations"
              :key="conv.id"
              class="conversation-item"
              :class="{ active: conv.id === currentConversationId }"
              @click="handleSelectConversation(conv.id)"
            >
              <div class="conv-title">{{ conv.title }}</div>
              <div class="conv-time">{{ formatTime(conv.updated_at) }}</div>
              <el-icon class="conv-delete" @click.stop="handleDeleteConversation(conv.id)"><Close /></el-icon>
            </div>
            <div v-if="conversations.length === 0" class="empty-tip">
              暂无会话
            </div>
          </div>
        </div>

        <!-- 右侧对话区 -->
        <div class="chat-main">
          <template v-if="currentConversationId || messages.length">
            <!-- 消息列表 -->
            <div class="message-list" ref="messageListRef">
              <template v-for="(msg, idx) in messages" :key="idx">
                <!-- 用户消息 -->
                <div v-if="msg.role === 'user'" class="message-row user">
                  <div class="bubble user-bubble">{{ msg.content }}</div>
                </div>
                <!-- AI 消息 -->
                <div v-else-if="msg.role === 'assistant'" class="message-row ai">
                  <!-- 推理过程（可折叠） -->
                  <el-collapse v-if="msg.steps && msg.steps.length" class="steps-collapse">
                    <el-collapse-item title="推理过程">
                      <div v-for="(step, si) in msg.steps" :key="si" class="step-item">
                        <span v-if="step.type === 'thinking'" class="step-thinking">{{ step.content }}</span>
                        <span v-else-if="step.type === 'agent_call'" class="step-agent">
                          [{{ step.agent }}] {{ step.content }}
                        </span>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                  <div class="bubble ai-bubble">{{ msg.content }}</div>
                </div>
              </template>

              <!-- 正在输入提示 -->
              <div v-if="thinking" class="message-row ai">
                <div class="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>

            <!-- 输入区 -->
            <div class="input-area">
              <el-input
                v-model="inputText"
                type="textarea"
                :rows="2"
                placeholder="输入你的问题..."
                :disabled="thinking"
                @keyup.enter.ctrl="handleSend"
                resize="none"
              />
              <el-button
                type="primary"
                :loading="thinking"
                :disabled="!inputText.trim()"
                @click="handleSend"
                class="send-btn"
              >
                发送
              </el-button>
            </div>
          </template>

          <!-- 空状态 -->
          <div v-else class="empty-state">
            <el-icon size="48" color="#c0c4cc"><ChatDotRound /></el-icon>
            <p class="empty-title">AI 校园问答助手</p>
            <p class="empty-desc">点击"新建对话"开始提问</p>
            <div class="suggestions">
              <div class="suggestion-item" @click="quickAsk('我这周有什么课？')">我这周有什么课？</div>
              <div class="suggestion-item" @click="quickAsk('我的宿舍报修处理了吗？')">我的宿舍报修处理了吗？</div>
              <div class="suggestion-item" @click="quickAsk('我的奖学金发了吗？')">我的奖学金发了吗？</div>
              <div class="suggestion-item" @click="quickAsk('奖学金怎么申请？')">奖学金怎么申请？</div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Close, ChatDotRound } from '@element-plus/icons-vue'
import {
  getConversationsApi,
  createConversationApi,
  getConversationDetailApi,
  closeConversationApi,
  chatStreamApi,
} from '@/api/chat'
import type { Conversation, ChatMessage, AgentStep, SSEEventType, SSEEventData } from '@/types/chat'

const conversations = ref<Conversation[]>([])
const currentConversationId = ref<number | null>(null)
const messages = ref<(ChatMessage & { steps?: AgentStep[] })[]>([])
const inputText = ref('')
const thinking = ref(false)
const messageListRef = ref<HTMLElement>()

/** 格式化时间 */
function formatTime(t: string): string {
  if (!t) return ''
  return t.replace('T', ' ').slice(0, 16)
}

/** 滚动到底部 */
function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

/** 加载会话列表 */
async function loadConversations() {
  try {
    conversations.value = await getConversationsApi()
  } catch {
    // 后端未启动时静默处理
  }
}

/** 新建会话 */
async function handleNewConversation() {
  try {
    const conv = await createConversationApi('新对话')
    conversations.value.unshift(conv)
    currentConversationId.value = conv.id
    messages.value = []
  } catch {
    ElMessage.error('创建会话失败')
  }
}

/** 选择会话 */
async function handleSelectConversation(id: number) {
  if (currentConversationId.value === id) return
  currentConversationId.value = id
  messages.value = []
  try {
    const detail = await getConversationDetailApi(id)
    messages.value = detail.messages.map(m => ({ ...m }))
    scrollToBottom()
  } catch {
    ElMessage.error('加载会话失败')
  }
}

/** 删除/关闭会话 */
async function handleDeleteConversation(id: number) {
  try {
    await closeConversationApi(id)
    conversations.value = conversations.value.filter(c => c.id !== id)
    if (currentConversationId.value === id) {
      currentConversationId.value = null
      messages.value = []
    }
  } catch {
    ElMessage.error('删除会话失败')
  }
}

/** 快捷提问 */
function quickAsk(question: string) {
  if (!currentConversationId.value) {
    handleNewConversation().then(() => {
      inputText.value = question
    })
  } else {
    inputText.value = question
  }
}

/** 发送消息 */
async function handleSend() {
  const text = inputText.value.trim()
  if (!text || thinking.value) return

  // 如果没有会话，先创建
  if (!currentConversationId.value) {
    try {
      const conv = await createConversationApi('新对话')
      conversations.value.unshift(conv)
      currentConversationId.value = conv.id
    } catch {
      ElMessage.error('创建会话失败')
      return
    }
  }

  // 添加用户消息
  messages.value.push({
    id: Date.now(),
    conversation_id: currentConversationId.value!,
    role: 'user',
    content: text,
    created_at: new Date().toISOString(),
  })
  inputText.value = ''
  scrollToBottom()

  // 准备 AI 消息占位
  const aiMsg: ChatMessage & { steps?: AgentStep[] } = {
    id: Date.now() + 1,
    conversation_id: currentConversationId.value!,
    role: 'assistant',
    content: '',
    agent_name: null,
    created_at: new Date().toISOString(),
    steps: [],
  }
  messages.value.push(aiMsg)
  const aiMsgIndex = messages.value.length - 1  // 记录索引，通过响应式 Proxy 修改
  scrollToBottom()

  thinking.value = true

  try {
    await chatStreamApi(currentConversationId.value, text, (event, data) => {
      switch (event as SSEEventType) {
        case 'thinking':
          messages.value[aiMsgIndex].steps!.push({ type: 'thinking', content: data.content || '思考中...' })
          break
        case 'agent_call':
          messages.value[aiMsgIndex].steps!.push({
            type: 'agent_call',
            content: data.description || '',
            agent: data.agent,
          })
          break
        case 'result':
          messages.value[aiMsgIndex].content += data.content || ''
          scrollToBottom()
          break
        case 'clarify':
          messages.value[aiMsgIndex].content = data.question || '请明确您的问题'
          break
        case 'error':
          messages.value[aiMsgIndex].content = data.message || '抱歉，处理时出现错误'
          break
        case 'done':
          break
      }
    })
  } catch {
    messages.value[aiMsgIndex].content = '连接失败，请稍后重试'
  } finally {
    thinking.value = false
    scrollToBottom()
    // 刷新会话列表（标题可能被后端更新）
    loadConversations()
  }
}

loadConversations()
</script>

<style scoped>
.chat-page {
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
}

.chat-page :deep(.el-card) {
  height: 100%;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.chat-page :deep(.el-card__body) {
  height: 100%;
  padding: 0;
  border-radius: 8px;
  overflow: hidden;
}

.chat-body {
  display: flex;
  height: 100%;
  overflow: hidden;
}

/* 左侧会话列表 */
.sidebar {
  width: 240px;
  flex-shrink: 0;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  background: #fafafa;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
}

.conversation-item {
  padding: 12px 16px;
  cursor: pointer;
  position: relative;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}

.conversation-item:hover {
  background: #f5f7fa;
}

.conversation-item.active {
  background: #ecf5ff;
}

.conv-title {
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-right: 20px;
}

.conv-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.conv-delete {
  position: absolute;
  right: 12px;
  top: 14px;
  color: #c0c4cc;
  cursor: pointer;
  display: none;
}

.conversation-item:hover .conv-delete {
  display: block;
}

.conv-delete:hover {
  color: #f56c6c;
}

.empty-tip {
  text-align: center;
  color: #c0c4cc;
  font-size: 13px;
  padding: 40px 0;
}

/* 右侧对话区 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #ffffff;
}

/* 消息列表 */
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.message-row {
  margin-bottom: 16px;
  display: flex;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.ai {
  justify-content: flex-start;
  flex-direction: column;
  align-items: flex-start;
}

/* 气泡 */
.bubble {
  max-width: 70%;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.user-bubble {
  background: #409eff;
  color: #fff;
}

.ai-bubble {
  background: #fff;
  color: #303133;
  border: 1px solid #e4e7ed;
}

/* 推理过程折叠面板 */
.steps-collapse {
  width: 70%;
  margin-bottom: 8px;
  border: 1px solid #faecd8;
  border-radius: 6px;
  background: #fdf6ec;
}

.steps-collapse :deep(.el-collapse-item__header) {
  padding: 0 12px;
  font-size: 13px;
  color: #8c7a62;
  background: transparent;
  border-bottom: none;
  height: 36px;
}

.steps-collapse :deep(.el-collapse-item__wrap) {
  background: transparent;
  border-bottom: none;
}

.steps-collapse :deep(.el-collapse-item__content) {
  padding: 8px 12px;
  font-size: 12px;
  color: #8c7a62;
}

.step-item {
  margin-bottom: 4px;
}

.step-thinking {
  color: #909399;
}

.step-agent {
  color: #5a8dee;
}

/* 正在输入动画 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #c0c4cc;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-6px);
    opacity: 1;
  }
}

/* 输入区 */
.input-area {
  padding: 16px 24px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  gap: 12px;
  align-items: flex-end;
  background: #fff;
}

.input-area :deep(.el-textarea) {
  flex: 1;
}

.send-btn {
  flex-shrink: 0;
}

/* 空状态 */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.empty-title {
  font-size: 20px;
  font-weight: 500;
  color: #303133;
  margin: 16px 0 8px;
}

.empty-desc {
  font-size: 14px;
  color: #909399;
  margin-bottom: 32px;
}

.suggestions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  max-width: 500px;
}

.suggestion-item {
  padding: 12px 16px;
  border: 1px solid #b0b4bb;
  border-radius: 8px;
  font-size: 13px;
  color: #303133;
  background: #f7f8fa;
  cursor: pointer;
  text-align: center;
  transition: all 0.2s;
}

.suggestion-item:hover {
  border-color: #409eff;
  color: #409eff;
  background: #f0f7ff;
}
</style>
