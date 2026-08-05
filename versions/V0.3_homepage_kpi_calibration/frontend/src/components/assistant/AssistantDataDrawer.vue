<script setup lang="ts">
import type { AssistantDataBasis } from '@/types/assistant'

defineProps<{
  data: AssistantDataBasis
  scale: number
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()
</script>

<template>
  <Teleport to="body">
    <div class="drawer-overlay" @click="emit('close')">
      <div class="drawer-container" @click.stop>
        <div class="drawer-header">
          <h3 class="drawer-title">数据依据</h3>
          <button class="drawer-close" @click="emit('close')">×</button>
        </div>

        <div class="drawer-body">
          <div class="drawer-section">
            <div class="section-label">基本信息</div>
            <div class="info-list">
              <div class="info-row">
                <span class="info-label">指标或事项名称</span>
                <span class="info-value">{{ data.itemName }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">统计范围</span>
                <span class="info-value">{{ data.scope }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">更新时间</span>
                <span class="info-value">{{ data.updateTime }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">数据周期</span>
                <span class="info-value">{{ data.dataPeriod }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">核验状态</span>
                <span class="info-value verified">已核验</span>
              </div>
              <div class="info-row">
                <span class="info-label">稳定ID</span>
                <span class="info-value mono">{{ data.stableId }}</span>
              </div>
            </div>
          </div>

          <div class="drawer-section">
            <div class="section-label">数据来源</div>
            <div class="source-list">
              <div v-for="(src, idx) in data.sources" :key="idx" class="source-item">
                <div class="source-info">
                  <div class="source-name">{{ src.name }}</div>
                  <div class="source-time">{{ src.time }}</div>
                </div>
                <div class="source-status">
                  <span class="status-dot" />
                  {{ src.status }}
                </div>
              </div>
            </div>
          </div>

          <div class="drawer-section">
            <div class="section-label">口径说明</div>
            <div class="caliber-text">{{ data.caliber }}</div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 8, 18, 0.6);
  z-index: 2000;
  display: flex;
  justify-content: flex-end;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.drawer-container {
  width: 440px;
  height: 100%;
  background: var(--bg-panel-strong);
  border-left: 1px solid var(--border-base);
  display: flex;
  flex-direction: column;
  animation: slideIn 0.25s ease;
  box-shadow: -8px 0 24px rgba(0, 0, 0, 0.3);
}

@keyframes slideIn {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-soft);
  flex-shrink: 0;
}

.drawer-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.drawer-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  font-size: 24px;
  cursor: pointer;
  border-radius: 4px;
  line-height: 1;

  &:hover {
    background: var(--bg-card-hover);
    color: var(--text-primary);
  }

  &:focus-visible {
    outline: 2px solid var(--cyan);
    outline-offset: -2px;
  }
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}

.drawer-section {
  margin-bottom: 24px;

  &:last-child {
    margin-bottom: 0;
  }
}

.section-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-soft);
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  font-size: 13px;
}

.info-label {
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.info-value {
  color: var(--text-primary);
  text-align: right;
  word-break: break-all;

  &.verified {
    color: var(--green);
  }

  &.mono {
    font-family: Consolas, monospace;
    font-size: 12px;
  }
}

.source-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.source-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-soft);
  border-radius: 6px;
}

.source-info {
  flex: 1;
  min-width: 0;
}

.source-name {
  font-size: 13px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.source-time {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 3px;
}

.source-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--green);
  flex-shrink: 0;
  margin-left: 12px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--green);
}

.caliber-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.7;
  padding: 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-soft);
  border-radius: 6px;
}

.drawer-body::-webkit-scrollbar {
  width: 6px;
}

.drawer-body::-webkit-scrollbar-track {
  background: transparent;
}

.drawer-body::-webkit-scrollbar-thumb {
  background: var(--border-base);
  border-radius: 3px;
}

@media (max-width: 1600px) {
  .drawer-container {
    width: 380px;
  }

  .drawer-header {
    padding: 16px 20px;
  }

  .drawer-body {
    padding: 16px 20px;
  }
}
</style>
