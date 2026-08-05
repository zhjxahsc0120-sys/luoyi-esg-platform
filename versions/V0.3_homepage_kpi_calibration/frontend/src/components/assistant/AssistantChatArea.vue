<script setup lang="ts">
import { ref, nextTick, watch, type Ref } from 'vue'
import type { ChatMessage, AssistantDataBasis } from '@/types/assistant'
import AssistantWelcome from './AssistantWelcome.vue'
import AssistantMessage from './AssistantMessage.vue'
import AssistantInput from './AssistantInput.vue'

const props = defineProps<{
  messages: ChatMessage[]
  welcomeQuestions: string[]
  isLoading: boolean
  isAcceptance: boolean
}>()

const emit = defineEmits<{
  (e: 'send', text: string): void
  (e: 'welcome-click', question: string): void
  (e: 'view-data-basis', data: AssistantDataBasis): void
  (e: 'follow-up', question: string): void
}>()

const messagesContainer = ref<HTMLElement | null>(null)

const isEmpty = () => props.messages.length === 0

function handleSend(text: string) {
  emit('send', text)
}

function handleWelcomeClick(q: string) {
  emit('welcome-click', q)
}

function handleViewDataBasis(data: AssistantDataBasis) {
  emit('view-data-basis', data)
}

function handleFollowUp(q: string) {
  emit('follow-up', q)
}

watch(
  () => props.messages.length,
  () => {
    nextTick(() => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    })
  }
)
</script>

<template>
  <div class="chat-area">
    <div class="chat-header">
      <div class="chat-title-group">
        <h2 class="chat-title">ESG智能助手</h2>
        <p class="chat-subtitle">高速项目 ESG 管理助手：状态判断 · 风险事项 · 数据依据 · 下一步建议；上级检查可下载合规资料包</p>
      </div>
      <div class="chat-status">
        <div class="status-item">
          <span class="status-dot" />
          <span>数据已更新</span>
        </div>
      </div>
    </div>

    <div class="chat-messages" ref="messagesContainer">
      <AssistantWelcome
        v-if="isEmpty()"
        :questions="welcomeQuestions"
        @question-click="handleWelcomeClick"
      />
      <div v-else class="message-list">
        <AssistantMessage
          v-for="msg in messages"
          :key="msg.id"
          :message="msg"
          @view-data-basis="handleViewDataBasis"
          @follow-up="handleFollowUp"
        />
      </div>
    </div>

    <AssistantInput
      :is-loading="isLoading"
      :is-acceptance="isAcceptance"
      @send="handleSend"
    />
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: rgba(5, 25, 44, 0.52);
  border: 1px solid rgba(74, 147, 207, 0.16);
  border-radius: var(--panel-radius);
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-soft);
  flex-shrink: 0;
}

.chat-title-group {
  flex: 1;
  min-width: 0;
}

.chat-title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.chat-subtitle {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--text-tertiary);
}

.chat-status {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 6px rgba(67, 211, 107, 0.5);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  min-height: 0;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 100%;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: var(--border-base);
  border-radius: 3px;
}

@media (max-width: 1600px) {
  .chat-header {
    padding: 12px 20px;
  }

  .chat-title {
    font-size: 20px;
  }

  .chat-subtitle {
    font-size: 12px;
  }

  .chat-messages {
    padding: 16px;
  }
}
</style>
