<template>
  <div class="chat-view">
    <!-- Messages -->
    <div class="chat-messages" ref="messagesRef">
      <!-- Empty state -->
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg viewBox="0 0 80 80" width="80" height="80" fill="none">
            <rect x="8" y="8" width="64" height="64" rx="16" fill="#EBF3FF"/>
            <path d="M40 22v36M22 40h36" stroke="#2B7DE9" stroke-width="3" stroke-linecap="round"/>
            <circle cx="40" cy="40" r="24" stroke="#2B7DE9" stroke-width="2" fill="none" opacity="0.3"/>
          </svg>
        </div>
        <h2>有什么可以帮您？</h2>
        <p>基于医学知识库的 AI 问答助手，请输入您的健康咨询问题</p>
        <div class="quick-cards">
          <div
            v-for="q in quickQuestions"
            :key="q.text"
            class="quick-card"
            @click="sendQuick(q.text)"
          >
            <el-icon :size="16" color="#2B7DE9"><ChatDotRound /></el-icon>
            <span>{{ q.text }}</span>
          </div>
        </div>
      </div>

      <!-- Message list -->
      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="msg-row"
        :class="msg.role"
      >
        <!-- AI avatar -->
        <div v-if="msg.role === 'ai'" class="avatar ai-avatar">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none">
            <path d="M12 2v20M2 12h20" stroke="#fff" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>

        <div class="msg-body">
          <div class="bubble" :class="msg.role">
            <!-- Loading -->
            <div v-if="msg.loading" class="typing-dots">
              <span></span><span></span><span></span>
              <span class="typing-label">正在检索知识库并生成回答...</span>
            </div>
            <!-- Content with Markdown -->
            <div v-else class="bubble-content markdown-body" v-html="renderMd(msg.content)"></div>
          </div>
          <!-- Sources -->
          <SourceCard
            v-if="msg.role === 'ai' && msg.sources?.length > 0"
            :sources="msg.sources"
            :confidence="msg.confidence"
          />
        </div>

        <!-- User avatar -->
        <div v-if="msg.role === 'user'" class="avatar user-avatar">
          <el-icon :size="18" color="#fff"><User /></el-icon>
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="chat-input">
      <div class="input-bar">
        <div class="input-hint" v-if="knowledgeCount > 0">
          <el-icon :size="14"><Collection /></el-icon>
          已加载 {{ knowledgeCount }} 份知识文档
        </div>
        <div class="input-row">
          <el-input
            v-model="inputText"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 4 }"
            placeholder="请输入您的健康咨询问题... (Enter 发送，Shift+Enter 换行)"
            resize="none"
            @keydown="onKeydown"
            :disabled="isLoading"
            class="chat-textarea"
          />
          <button
            class="send-btn"
            :disabled="!inputText.trim() || isLoading"
            @click="sendMessage"
          >
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 2L11 13" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { ChatDotRound } from '@element-plus/icons-vue'
import { marked } from 'marked'
import { chatStream, listKnowledge } from '../api'
import SourceCard from '../components/SourceCard.vue'

const messages = ref([])
const inputText = ref('')
const isLoading = ref(false)
const messagesRef = ref(null)
const knowledgeCount = ref(0)
const typewriterQueues = ref({})

const quickQuestions = [
  { text: '高血压的诊断标准是什么？' },
  { text: '阿莫西林怎么吃？一次几粒？' },
  { text: '头晕应该看哪个科室？' },
]

// Configure marked for safe Markdown rendering
marked.setOptions({
  breaks: true,
  gfm: true,
})

onMounted(async () => {
  try {
    const res = await listKnowledge()
    knowledgeCount.value = res.data.documents?.length || 0
  } catch (_) {}
})

function renderMd(text) {
  if (!text) return ''
  return marked.parse(text)
}

function scrollBottom() {
  nextTick(() => {
    if (messagesRef.value) messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  })
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
}

function sendQuick(q) { inputText.value = q; sendMessage() }

async function sendMessage() {
  const q = inputText.value.trim()
  if (!q || isLoading.value) return

  messages.value.push({ role: 'user', content: q })
  inputText.value = ''
  const aiMsg = { role: 'ai', content: '', rawContent: '', loading: true, sources: [], confidence: 0 }
  messages.value.push(aiMsg)
  const msgIdx = messages.value.length - 1
  isLoading.value = true
  scrollBottom()

  // Typewriter state
  typewriterQueues.value[msgIdx] = { chars: [], running: false, buffer: '' }
  const queue = typewriterQueues.value[msgIdx]

  function typewriterTick() {
    if (queue.chars.length > 0) {
      // Consume up to 3 chars per frame for speed
      const batch = Math.min(3, queue.chars.length)
      for (let i = 0; i < batch; i++) {
        queue.buffer += queue.chars.shift()
      }
      aiMsg.content = queue.buffer
      scrollBottom()
    }
    if (queue.chars.length > 0 || queue.running) {
      requestAnimationFrame(typewriterTick)
    }
  }

  await chatStream(
    q, 3,
    // onChunk
    (data) => {
      aiMsg.loading = false
      queue.running = true
      queue.chars.push(...data.content.split(''))
      if (!queue.ticking) {
        queue.ticking = true
        requestAnimationFrame(typewriterTick)
      }
    },
    // onSources
    (data) => { aiMsg.sources = data.sources || []; aiMsg.confidence = data.confidence || 0 },
    // onDone
    () => {
      queue.running = false
      isLoading.value = false
      // Flush remaining chars
      aiMsg.content = queue.buffer + queue.chars.join('')
      scrollBottom()
    },
    // onError
    (err) => {
      aiMsg.loading = false
      aiMsg.content = '抱歉，服务出现错误，请稍后重试。'
      isLoading.value = false
    }
  )
}
</script>

<style lang="scss" scoped>
@import '../assets/styles/variables.scss';

.chat-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: $bg-gray;

  @include mobile {
    padding-bottom: $mobile-tab-height;
  }
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
  scroll-behavior: smooth;

  @include mobile {
    padding: 16px;
  }
}

/* ===== Empty State ===== */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;

  h2 { margin-top: 16px; font-size: 24px; color: $text-title; font-weight: 700; }
  p { margin-top: 8px; font-size: 14px; color: $text-assist; }
}

.quick-cards {
  display: flex;
  gap: 12px;
  margin-top: 32px;
  flex-wrap: wrap;
  justify-content: center;

  @include mobile {
    flex-direction: column;
    width: 100%;
    padding: 0 16px;
  }
}

.quick-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: $bg-white;
  border: 1px solid $border-light;
  border-radius: $radius-lg;
  cursor: pointer;
  font-size: 13px;
  color: $text-body;
  transition: all 150ms ease;
  box-shadow: $shadow-card;

  &:hover {
    border-color: $primary-blue;
    color: $primary-blue;
    box-shadow: $shadow-hover;
    transform: translateY(-2px);
  }

  @include mobile {
    justify-content: center;
  }
}

/* ===== Messages ===== */
.msg-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 24px;
  animation: msgIn 300ms ease-out;

  &.user { flex-direction: row-reverse; }
}

@keyframes msgIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

.msg-body { max-width: 72%; min-width: 0; }

/* ===== Avatar ===== */
.avatar {
  width: 38px; height: 38px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  box-shadow: $shadow-card;
}
.user-avatar { background: linear-gradient(135deg, #2B7DE9, #5B9FE9); }
.ai-avatar { background: linear-gradient(135deg, #10B981, #34D399); }

/* ===== Bubbles ===== */
.bubble {
  padding: 14px 18px;
  border-radius: $radius-xl;
  font-size: 14px;
  line-height: 1.7;
  word-break: break-word;

  &.user {
    background: linear-gradient(135deg, #2B7DE9, #5B9FE9);
    color: $text-white;
    border-bottom-right-radius: $radius-sm;
    box-shadow: 0 2px 12px rgba(43, 125, 233, 0.25);
  }

  &.ai {
    background: $bg-white;
    color: $text-title;
    border: 1px solid $border-light;
    border-bottom-left-radius: $radius-sm;
    border-left: 3px solid $primary-blue;
    box-shadow: $shadow-card;
  }
}

.bubble-content { white-space: pre-wrap; }

/* ===== Markdown Body Styles ===== */
.markdown-body {
  :deep(h1), :deep(h2), :deep(h3), :deep(h4) {
    margin: 12px 0 6px;
    color: $text-title;
    font-weight: 600;
    line-height: 1.4;
  }
  :deep(h1) { font-size: 18px; }
  :deep(h2) { font-size: 16px; }
  :deep(h3) { font-size: 15px; }
  :deep(p) { margin: 4px 0; }
  :deep(ul), :deep(ol) {
    margin: 6px 0;
    padding-left: 20px;
  }
  :deep(li) { margin: 3px 0; }
  :deep(strong) { color: $text-title; font-weight: 600; }
  :deep(code) {
    background: #F2F3F5;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 13px;
    font-family: 'SF Mono', Consolas, monospace;
  }
  :deep(pre) {
    background: #1D2129;
    color: #E8E8E8;
    padding: 14px 16px;
    border-radius: $radius-md;
    overflow-x: auto;
    margin: 10px 0;
  }
  :deep(pre code) {
    background: none;
    padding: 0;
    color: inherit;
    font-size: 13px;
  }
  :deep(blockquote) {
    border-left: 3px solid $primary-blue;
    padding-left: 12px;
    margin: 8px 0;
    color: $text-assist;
  }
}

/* ===== Typing Dots ===== */
.typing-dots {
  display: flex; align-items: center; gap: 5px;

  span:not(.typing-label) {
    width: 8px; height: 8px;
    background: $primary-blue;
    border-radius: 50%;
    animation: dotBounce 1.4s infinite ease-in-out;
  }
  span:nth-child(1) { animation-delay: -0.32s; }
  span:nth-child(2) { animation-delay: -0.16s; }

  .typing-label {
    margin-left: 8px;
    color: $text-assist;
    font-size: 13px;
  }
}

@keyframes dotBounce {
  0%, 80%, 100% { transform: scale(0.3); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* ===== Input ===== */
.chat-input {
  padding: 16px 32px 20px;
  background: $bg-white;
  border-top: 1px solid $border-light;

  @include mobile {
    padding: 12px 16px;
    padding-bottom: 12px + $mobile-tab-height;
  }
}

.input-bar {
  max-width: 800px;
  margin: 0 auto;
}

.input-hint {
  display: flex; align-items: center; gap: 4px;
  font-size: 12px; color: $text-assist;
  margin-bottom: 8px;
}

.input-row {
  display: flex; align-items: flex-end; gap: 12px;
}

.chat-textarea { flex: 1; }

.send-btn {
  width: 42px; height: 42px;
  flex-shrink: 0;
  border: none;
  border-radius: 50%;
  background: linear-gradient(135deg, #2B7DE9, #5B9FE9);
  color: #fff;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 150ms ease;
  box-shadow: 0 2px 8px rgba(43, 125, 233, 0.3);

  &:hover:not(:disabled) { transform: scale(1.05); box-shadow: 0 4px 16px rgba(43, 125, 233, 0.4); }
  &:active:not(:disabled) { transform: scale(0.96); }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}
</style>
