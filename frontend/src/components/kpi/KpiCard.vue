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
      'kpi-card--long-value': isLongValue,
      'kpi-card--text-value': Boolean(item.displayText),
    }"
    :data-kpi-key="item.key"
    role="button"
    tabindex="0"
    @click="handleClick"
    @keydown.enter="handleClick"
    @keydown.space.prevent="handleClick">
    <!-- V0.4.2：仅名称 + 数值 + 单位；名称占主视觉区；无 hint/环比 -->
    <div class="kpi-label">{{ item.label }}</div>
    <div class="kpi-value-row">
      <span class="kpi-value" :style="{ color: themeColors[theme] }">
        {{ primaryText }}
      </span>
      <span v-if="showUnit" class="kpi-unit">{{ item.unit }}</span>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.kpi-card {
  /* V0.4.2：卡片吃满分组高度，名称占上部主视觉区，数值贴下部 */
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: stretch;
  height: 100%;
  min-height: 0;
  min-width: 0;
  padding: 8px 6px 10px;
  border: 1px solid var(--border-faint);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: all 0.2s ease;
  gap: 4px;
  box-sizing: border-box;

  &:hover {
    border-color: var(--border-blue-dim);
    background: rgba(0, 174, 255, 0.04);
    transform: translateY(-1px);
  }

  &:focus {
    outline: none;
    border-color: var(--border-blue);
  }

  /* 层级 1：指标名称 — 占卡片主要上部空间 */
  .kpi-label {
    flex: 1 1 auto;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    font-size: 18px;
    font-weight: 700;
    line-height: 1.22;
    letter-spacing: 0;
    color: #e8f3ff;
    text-align: center;
    white-space: normal;
    overflow: visible;
    text-overflow: clip;
    word-break: keep-all;
    overflow-wrap: anywhere;
  }

  /* 层级 2/3：核心数值（保持原尺寸）+ 单位（略增） */
  .kpi-value-row {
    flex: 0 0 auto;
    display: flex;
    align-items: baseline;
    gap: 5px;
    justify-content: center;
    min-width: 0;
    padding-top: 2px;

    .kpi-value {
      font-family: var(--font-num);
      font-size: var(--fs-kpi-num);
      font-weight: 700;
      line-height: 1;
      text-shadow: 0 0 6px currentColor;
      font-variant-numeric: tabular-nums;
    }

    .kpi-unit {
      font-size: 16px;
      color: #b7cce3;
      font-weight: 600;
      line-height: 1;
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
      font-size: 16px;
    }
  }

  &.kpi-card--text-value .kpi-value {
    font-size: 18px;
    letter-spacing: 0;
  }
}
</style>
