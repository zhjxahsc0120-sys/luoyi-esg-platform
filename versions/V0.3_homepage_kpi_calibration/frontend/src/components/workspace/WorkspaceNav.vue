<script setup lang="ts">
defineProps<{
  activeNav: string
}>()

const emit = defineEmits<{
  (e: 'navigate', name: string): void
}>()

const navItems = [
  { key: 'workspace', label: '填报概览' },
  { key: 'tasks', label: '我的上传任务' },
  { key: 'smart-upload', label: 'ESG智能入库' },
  { key: 'review', label: '审核管理' },
  { key: 'documents', label: '资料中心与档案' },
]

function handleNavClick(key: string) {
  emit('navigate', key)
}
</script>

<template>
  <nav class="workspace-nav">
    <button
      v-for="item in navItems"
      :key="item.key"
      :class="['nav-item', { active: activeNav === item.key }]"
      @click="handleNavClick(item.key)"
    >
      {{ item.label }}
    </button>
  </nav>
</template>

<style scoped>
.workspace-nav {
  display: flex;
  flex-shrink: 0;
  background: rgba(0, 0, 0, 0.3);
  padding: 0 8px;
  border: 1px solid rgba(47, 156, 255, 0.12);
  border-radius: 8px;
}

.nav-item {
  flex: 1;
  max-width: 200px;
  padding: 8px 12px;
  border: none;
  background: transparent;
  color: #8fa9c8;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
  text-align: center;
}

.nav-item:hover {
  color: #e8f3ff;
  background: rgba(47, 156, 255, 0.05);
}

.nav-item.active {
  color: #2f9cff;
  border-bottom-color: #2f9cff;
  background: rgba(47, 156, 255, 0.08);
}
</style>