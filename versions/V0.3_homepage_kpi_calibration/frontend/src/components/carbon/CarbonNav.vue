<script setup lang="ts">
defineProps<{
  activeTab: string
}>()

const emit = defineEmits<{
  (e: 'navigate', name: string): void
}>()

const navItems = [
  { key: 'overview', label: '概览' },
  { key: 'boundary', label: '构成与边界' },
  { key: 'detail', label: '明细' },
]

function handleNavClick(key: string) {
  emit('navigate', key)
}
</script>

<template>
  <nav class="carbon-nav workspace-nav">
    <button
      v-for="item in navItems"
      :key="item.key"
      :class="['nav-item', { active: activeTab === item.key }]"
      @click="handleNavClick(item.key)"
    >
      {{ item.label }}
    </button>
  </nav>
</template>

<style scoped>
.carbon-nav {
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
