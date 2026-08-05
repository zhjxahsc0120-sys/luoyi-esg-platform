<script setup lang="ts">
import type { ChatSession, QuickCategory } from '@/types/assistant'

defineProps<{
  sessions: ChatSession[]
  categories: QuickCategory[]
}>()

const emit = defineEmits<{
  (e: 'new-session'): void
  (e: 'session-click', id: string): void
  (e: 'category-click', question: string): void
}>()

function getCategoryColorClass(color: string): string {
  const map: Record<string, string> = {
    green: 'cat-green',
    blue: 'cat-blue',
    purple: 'cat-purple',
    cyan: 'cat-cyan',
    orange: 'cat-orange',
  }
  return map[color] || 'cat-blue'
}
</script>

<template>
  <aside class="assistant-sidebar">
    <button class="new-chat-btn" @click="emit('new-session')">
      <span class="plus-icon">+</span>
      <span>新建会话</span>
    </button>

    <div class="sidebar-section">
      <div class="section-title">最近会话</div>
      <div class="session-list">
        <div
          v-for="s in sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: s.active }"
          @click="emit('session-click', s.id)"
        >
          <div class="session-title">{{ s.title }}</div>
          <div class="session-time">{{ s.lastTime }}</div>
        </div>
      </div>
      <div class="view-all">查看全部会话</div>
    </div>

    <div class="sidebar-section">
      <div class="section-title">快捷能力</div>
      <div class="category-list">
        <div
          v-for="cat in categories"
          :key="cat.key"
          class="category-item"
          :class="getCategoryColorClass(cat.color)"
          @click="emit('category-click', cat.name)"
        >
          <div class="cat-icon">{{ cat.icon }}</div>
          <div class="cat-info">
            <div class="cat-name">{{ cat.name }}</div>
            <div class="cat-desc">{{ cat.desc }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="sidebar-footer">
      <div class="footer-tip">可通过文字或语音查询平台指标、事项、资料和数据。</div>
    </div>
  </aside>
</template>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.assistant-sidebar {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 12px;
  background: rgba(5, 24, 42, 0.78);
  backdrop-filter: blur(6px);
  border: 1px solid rgba(74, 147, 207, 0.16);
  border-radius: var(--panel-radius);
  min-height: 0;
}

.new-chat-btn {
  width: 100%;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid var(--border-blue);
  border-radius: var(--radius-sm);
  background: linear-gradient(180deg, rgba(47, 156, 255, 0.28) 0%, rgba(10, 72, 135, 0.12) 100%);
  color: var(--text-main);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  .plus-icon {
    font-size: 18px;
    font-weight: 600;
    color: var(--cyan);
  }

  &:hover {
    background: rgba(47, 156, 255, 0.36);
    box-shadow: var(--shadow-blue);
  }

  &:focus-visible {
    outline: 2px solid var(--cyan);
    outline-offset: -2px;
  }
}

.sidebar-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  padding: 4px 2px;
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}

.session-item {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.15s ease;
  border: 1px solid transparent;

  &:hover {
    background: var(--bg-card-hover);
  }

  &.active {
    background: rgba(47, 156, 255, 0.12);
    border-color: rgba(47, 156, 255, 0.3);
  }
}

.session-title {
  font-size: 14px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

.session-time {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
}

.view-all {
  font-size: 13px;
  color: var(--text-tertiary);
  padding: 6px 12px;
  cursor: pointer;
  text-align: center;

  &:hover {
    color: var(--cyan);
  }
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 44px;
  padding: 0 12px;
  border-radius: var(--radius-sm);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: var(--bg-card-hover);
  }
}

.cat-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  font-weight: 700;
  font-size: 13px;
  flex-shrink: 0;
}

.cat-green .cat-icon {
  background: rgba(67, 211, 107, 0.15);
  color: var(--green);
}
.cat-blue .cat-icon {
  background: rgba(22, 135, 255, 0.15);
  color: var(--blue);
}
.cat-purple .cat-icon {
  background: rgba(139, 92, 246, 0.15);
  color: var(--purple);
}
.cat-cyan .cat-icon {
  background: rgba(37, 185, 255, 0.15);
  color: var(--cyan);
}
.cat-orange .cat-icon {
  background: rgba(255, 159, 47, 0.15);
  color: var(--orange);
}

.cat-info {
  flex: 1;
  min-width: 0;
}

.cat-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  line-height: 1.3;
}

.cat-desc {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-footer {
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid var(--border-soft);
}

.footer-tip {
  font-size: 12px;
  color: var(--text-tertiary);
  line-height: 1.6;
  text-align: center;
}

@media (max-width: 1600px) {
  .assistant-sidebar {
    width: 240px;
    gap: 12px;
    padding: 10px;
  }

  .cat-desc {
    display: none;
  }

  .new-chat-btn {
    height: 40px;
    font-size: 14px;
  }
}
</style>
