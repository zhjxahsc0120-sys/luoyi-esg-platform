<script setup lang="ts">
import { computed } from 'vue'
import type { KpiItem, KpiTheme } from '@/types/dashboard'

const props = defineProps<{
  item: KpiItem
  theme: KpiTheme
}>()

const emit = defineEmits<{
  (e: 'select', key: string): void
}>()

const themeColors: Record<KpiTheme, string> = {
  green: '#69e36f',
  blue: '#2f9cff',
  purple: '#a66cff',
}

function formatValue(value: string | number) {
  if (value === null || value === undefined) {
    return '--'
  }
  if (typeof value === 'number') {
    return value.toLocaleString('zh-CN')
  }
  return value
}

const primaryText = computed(() => {
  if (props.item.displayText) return props.item.displayText
  return formatValue(props.item.value)
})

const showUnit = computed(() => {
  if (props.item.displayText) return false
  return Boolean(props.item.unit)
})

const isLongValue = computed(() => primaryText.value.length >= 5)

function handleClick() {
  emit('select', props.item.key)
}
</script>

<template>
  <div
    class="kpi-card"
    :class="{
      'kpi-card--multiline': item.label.length > 10,
      'kpi-card--long-value': isLongValue,
      'kpi-card--e04': item.key === 'E04',
      'kpi-card--text-value': Boolean(item.displayText),
    }"
    :data-kpi-key="item.key"
    role="button"
    tabindex="0"
    @click="handleClick"
    @keydown.enter="handleClick"
    @keydown.space.prevent="handleClick">
    <div class="kpi-label">{{ item.label }}</div>
    <div class="kpi-value-row">
      <span class="kpi-value" :style="{ color: themeColors[theme] }">
        {{ primaryText }}
      </span>
      <span v-if="showUnit" class="kpi-unit">{{ item.unit }}</span>
    </div>
    <div v-if="item.hint" class="kpi-hint">{{ item.hint }}</div>
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.kpi-card {
  @include flex-center;
  flex-direction: column;
  padding: 10px 12px;
  border: 1px solid var(--border-faint);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 0;

  &:hover {
    border-color: var(--border-blue-dim);
    background: rgba(0, 174, 255, 0.04);
    transform: translateY(-1px);
  }

  &:focus {
    outline: none;
    border-color: var(--border-blue);
  }

  .kpi-label {
    font-size: var(--fs-caption);
    color: var(--text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;
    text-align: center;
    margin-bottom: 6px;
  }

  // 长标题多行显示
  &.kpi-card--multiline .kpi-label {
    white-space: normal;
    overflow: visible;
    text-overflow: clip;
    line-height: 1.3;
    min-height: 32px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .kpi-value-row {
    display: flex;
    align-items: baseline;
    gap: 4px;
    justify-content: center;
    min-width: 0;

    .kpi-value {
      font-family: var(--font-num);
      font-size: var(--fs-kpi-num);
      font-weight: 700;
      line-height: 1;
      text-shadow: 0 0 6px currentColor;
      font-variant-numeric: tabular-nums;
    }

    .kpi-unit {
      font-size: var(--fs-unit);
      color: var(--text-muted);
      font-weight: 400;
    }
  }

  &.kpi-card--long-value .kpi-value-row {
    width: 100%;
    box-sizing: border-box;
    white-space: nowrap;

    .kpi-value {
      flex-shrink: 0;
      font-size: 30px;
      letter-spacing: -1px;
    }

    .kpi-unit {
      flex-shrink: 0;
      font-size: 12px;
    }
  }

  &.kpi-card--e04 .kpi-label {
    letter-spacing: -0.15px;
    text-overflow: clip;
  }

  .kpi-hint {
    margin-top: 4px;
    max-width: 100%;
    padding: 0 2px;
    color: var(--text-tertiary, #7f99b8);
    font-size: 10px;
    line-height: 1.25;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &.kpi-card--text-value .kpi-value {
    font-size: 18px;
    letter-spacing: 0;
  }
}
</style>
