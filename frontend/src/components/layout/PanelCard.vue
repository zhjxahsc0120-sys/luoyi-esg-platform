<script setup lang="ts">
defineProps<{
  title?: string
  icon?: object | (() => void)
  theme?: 'e' | 's' | 'g' | 'x'
  flush?: boolean
}>()
</script>

<template>
  <div class="panel-card" :class="{ 'panel-card--flush': flush }" :data-theme="theme || 'x'">
    <div v-if="title" class="panel-title">
      <component :is="icon" v-if="icon" class="panel-icon" />
      <span>{{ title }}</span>
    </div>
    <slot />
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.panel-card {
  @include panel-base;
  height: 100%;
  padding: var(--panel-pad);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-card--flush {
  padding: 0;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  font-size: var(--fs-module-title);
  font-weight: 600;
  color: var(--text-main);
  margin-bottom: var(--space-8);
  flex-shrink: 0;
}

.panel-icon {
  width: 18px;
  height: 18px;
  color: var(--cyan);
  flex-shrink: 0;
}

[data-theme="e"] .panel-icon { color: var(--color-e); }
[data-theme="s"] .panel-icon { color: var(--color-s); }
[data-theme="g"] .panel-icon { color: var(--color-g); }
</style>
