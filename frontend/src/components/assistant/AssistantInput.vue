<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  isLoading: boolean
  isAcceptance: boolean
}>()

const emit = defineEmits<{
  (e: 'send', text: string): void
}>()

const inputText = ref('')
const isRecording = ref(false)
const attachedFile = ref<string | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

const placeholder = '请输入您的问题，支持自然语言查询……'

function handleSend() {
  if (props.isLoading || !inputText.value.trim()) return
  emit('send', inputText.value.trim())
  inputText.value = ''
  attachedFile.value = null
}

function handleKeypress(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function handleClear() {
  inputText.value = ''
  attachedFile.value = null
}

function toggleRecording() {
  isRecording.value = !isRecording.value
  if (isRecording.value) {
    setTimeout(() => {
      if (isRecording.value) {
        inputText.value = '当前有哪些未闭环环保问题？'
        isRecording.value = false
      }
    }, 2000)
  }
}

function handleAttachClick() {
  fileInput.value?.click()
}

function handleFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    attachedFile.value = target.files[0].name
  }
}

function removeAttachment() {
  attachedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}
</script>

<template>
  <div class="input-area">
    <div v-if="attachedFile" class="attached-file">
      <span class="file-icon">📎</span>
      <span class="file-name">{{ attachedFile }}</span>
      <button class="file-remove" @click="removeAttachment">×</button>
    </div>
    <div class="input-container" :class="{ 'is-recording': isRecording }">
      <textarea
        v-model="inputText"
        class="message-input"
        :placeholder="placeholder"
        :disabled="isLoading"
        rows="2"
        @keydown="handleKeypress"
      />
      <div class="input-toolbar">
        <div class="toolbar-left">
          <button class="tool-btn" title="附件" @click="handleAttachClick">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </button>
          <input ref="fileInput" type="file" style="display:none" @change="handleFileChange" />
          <button
            class="tool-btn voice-btn"
            :class="{ active: isRecording }"
            :title="isRecording ? '停止录音' : '语音输入'"
            @click="toggleRecording"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z" stroke-linecap="round" stroke-linejoin="round" />
              <path d="M19 10v2a7 7 0 01-14 0v-2M12 19v4M8 23h8" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            <span v-if="isRecording" class="recording-text">正在录音</span>
          </button>
        </div>
        <div class="toolbar-right">
          <button class="tool-btn text-btn" :disabled="!inputText && !attachedFile" @click="handleClear">
            清空
          </button>
          <button v-if="isLoading" class="tool-btn text-btn stop-btn">
            停止生成
          </button>
          <button class="send-btn" :disabled="isLoading || !inputText.trim()" @click="handleSend">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            <span>发送</span>
          </button>
        </div>
      </div>
    </div>
    <div class="input-hint">
      按 Enter 发送，Shift + Enter 换行
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.input-area {
  flex-shrink: 0;
  padding: 16px 24px 20px;
  border-top: 1px solid rgba(55, 145, 220, 0.18);
  background: rgba(8, 35, 60, 0.92);
  box-shadow:
    0 -10px 30px rgba(0, 0, 0, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.025);
}

.attached-file {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  margin-bottom: 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-soft);
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.file-icon {
  font-size: 14px;
}

.file-name {
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-remove {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  border-radius: 3px;

  &:hover {
    background: var(--bg-card-hover);
    color: var(--text-primary);
  }
}

.input-container {
  background: rgba(8, 40, 69, 0.65);
  border: 1px solid rgba(55, 145, 220, 0.34);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.2s ease;

  &:focus-within {
    border-color: var(--border-blue);
    box-shadow: 0 0 0 3px rgba(37, 185, 255, 0.08);
  }

  &.is-recording {
    border-color: var(--red);
    box-shadow: 0 0 16px rgba(255, 75, 85, 0.15);
  }
}

.message-input {
  width: 100%;
  padding: 16px 20px 12px;
  border: none;
  outline: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 15px;
  font-family: inherit;
  resize: none;
  line-height: 1.6;
  min-height: 56px;
  max-height: 200px;

  &::placeholder {
    color: var(--text-disabled);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.input-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px 10px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.tool-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: 6px;
  font-size: 13px;
  transition: all 0.15s ease;

  svg {
    width: 18px;
    height: 18px;
  }

  &:hover:not(:disabled) {
    color: var(--text-primary);
    background: var(--bg-card-hover);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  &:focus-visible {
    outline: 2px solid var(--cyan);
    outline-offset: -2px;
  }
}

.voice-btn {
  &.active {
    color: var(--red);
    background: rgba(255, 75, 85, 0.1);
  }
}

.recording-text {
  font-size: 13px;
  animation: pulse 1.2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.text-btn {
  padding: 8px 14px;
  font-size: 13px;
}

.stop-btn {
  color: var(--text-secondary);

  &:hover:not(:disabled) {
    color: var(--red);
  }
}

.send-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border: none;
  background: linear-gradient(135deg, var(--blue) 0%, var(--cyan) 100%);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;

  svg {
    width: 16px;
    height: 16px;
  }

  &:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(22, 135, 255, 0.35);
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  &:focus-visible {
    outline: 2px solid var(--cyan);
    outline-offset: 2px;
  }
}

.input-hint {
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-disabled);
  text-align: center;
}

@media (max-width: 1600px) {
  .input-area {
    padding: 12px 20px 16px;
  }

  .message-input {
    padding: 10px 14px;
    font-size: 13px;
  }

  .send-btn {
    padding: 6px 14px;
    font-size: 13px;
  }
}
</style>
