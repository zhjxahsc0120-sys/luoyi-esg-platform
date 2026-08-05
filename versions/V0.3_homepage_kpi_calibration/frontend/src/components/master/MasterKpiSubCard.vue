<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { motionOff } from '@/composables/useMotionMode'
import type { MasterKpiItem, MasterKpiTheme } from '@/data/master.mock'

const props = defineProps<{
  item: MasterKpiItem
  theme: MasterKpiTheme
}>()

// 数值是否为小数（用于略小字号）
const isDecimal = computed(() => {
  const v = props.item.value
  return typeof v === 'number' && !Number.isInteger(v)
})

// 数值是否为大数（>= 1000 整数，如 E04 = 12856 → "12,856"）
// 用于在单行排版时将字号缩小到 30～32px，避免单位换行
const isLargeValue = computed(() => {
  const v = props.item.value
  return typeof v === 'number' && Number.isInteger(v) && Math.abs(v) >= 1000
})

// ── 千分位格式化（E04 = 12856 → "12,856"）──
function formatNumber(v: number): string {
  if (Number.isInteger(v) && Math.abs(v) >= 1000) {
    return v.toLocaleString('en-US')
  }
  return String(v)
}

// 最终显示值（格式化后）
const finalDisplay = computed<string | number>(() => {
  const v = props.item.value
  return typeof v === 'number' ? formatNumber(v) : v
})

// 当前显示值 —— 数字类型初始为 0（非空字符串）
const displayValue = ref<string | number>(
  typeof props.item.value === 'number' ? 0 : props.item.value
)

let rafId: number | null = null

onMounted(() => {
  const raw = props.item.value

  // 非数字 / 值为 0 / 动画关闭 → 直接显示最终值
  if (typeof raw !== 'number' || raw === 0 || motionOff.value) {
    displayValue.value = finalDisplay.value
    return
  }

  const target: number = raw
  const duration = 600 // 500～800ms 区间
  const startTime = performance.now()
  const isInt = Number.isInteger(target)

  function tick(now: number) {
    const elapsed = now - startTime
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3) // ease-out cubic
    const current = target * eased

    if (isInt) {
      // 整数：千分位格式化（动画过程中中间值也格式化）
      displayValue.value = formatNumber(Math.round(current))
    } else {
      displayValue.value = Number(current.toFixed(3))
    }

    if (progress < 1) {
      rafId = requestAnimationFrame(tick)
    } else {
      // 动画结束 → 稳定显示最终值
      displayValue.value = finalDisplay.value
      rafId = null
    }
  }

  // rAF 异常 fallback → 直接显示最终值
  try {
    rafId = requestAnimationFrame(tick)
  } catch {
    displayValue.value = finalDisplay.value
  }
})

// 组件卸载时清理动画帧
onUnmounted(() => {
  if (rafId !== null && typeof cancelAnimationFrame === 'function') {
    cancelAnimationFrame(rafId)
    rafId = null
  }
})
</script>

<template>
  <div class="master-kpi-card" :class="`theme-${theme}`" :title="item.fullName">
    <div class="kpi-name">
      {{ item.label }}
    </div>
    <div class="kpi-value-row">
      <span class="kpi-value" :class="[`theme-${theme}`, { 'is-decimal': isDecimal, 'is-large-num': isLargeValue }]">{{ displayValue }}</span>
      <span class="kpi-unit">{{ item.unit }}</span>
    </div>
  </div>
</template>
