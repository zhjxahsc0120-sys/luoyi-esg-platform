<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  progress: number
  size?: number
  strokeWidth?: number
  color?: string
}>()

const size = computed(() => props.size || 90)
const stroke = computed(() => props.strokeWidth || 10)
const radius = computed(() => (size.value - stroke.value) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)
const offset = computed(() => circumference.value - (props.progress / 100) * circumference.value)
const color = computed(() => props.color || '#a66cff')
</script>

<template>
  <div class="progress-ring" :style="{ width: `${size}px`, height: `${size}px` }">
    <svg :width="size" :height="size" viewBox="0 0 100 100">
      <circle
        cx="50"
        cy="50"
        :r="radius"
        fill="none"
        stroke="rgba(255,255,255,0.08)"
        :stroke-width="stroke"
      />
      <circle
        cx="50"
        cy="50"
        :r="radius"
        fill="none"
        :stroke="color"
        :stroke-width="stroke"
        stroke-linecap="round"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="offset"
        transform="rotate(-90 50 50)"
        style="transition: stroke-dashoffset 0.6s ease;"
      />
    </svg>
    <div class="progress-text">{{ progress }}%</div>
  </div>
</template>

<style scoped lang="scss">
.progress-ring {
  position: relative;

  .progress-text {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    font-weight: 700;
    color: var(--text-main);
  }
}
</style>
