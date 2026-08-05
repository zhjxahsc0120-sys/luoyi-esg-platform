<script setup lang="ts">
import { computed } from 'vue'
import { masterTimelineSteps } from '@/data/master.mock'

const steps = masterTimelineSteps

// 连接线段：step[i] 到 step[i+1]
const segments = computed(() => {
  const segs: { index: number; status: 'completed' | 'pending' }[] = []
  for (let i = 0; i < steps.length - 1; i++) {
    const current = steps[i]
    const next = steps[i + 1]
    // 如果当前和下一个都是 completed，连接线为 completed（绿色）
    // 如果当前是 active 或 next 是 pending 且 current 不是 completed，则 pending
    if (current.status === 'completed' && (next.status === 'completed' || next.status === 'active')) {
      segs.push({ index: i, status: 'completed' })
    } else {
      segs.push({ index: i, status: 'pending' })
    }
  }
  return segs
})
</script>

<template>
  <div class="master-timeline-panel">
    <div class="timeline-inner">
      <template v-for="(step, i) in steps" :key="step.index">
        <!-- 连接线（在节点之前，跳过第一个） -->
        <div
          v-if="i > 0"
          class="tl-segment"
          :class="segments[i - 1].status"
        />
        <!-- 节点 -->
        <div class="tl-step" :class="step.status">
          <div class="tl-node-wrap">
            <div v-if="step.status === 'active'" class="tl-glow" />
            <div class="tl-node">
              <svg v-if="step.status === 'completed'" class="tl-check" viewBox="0 0 16 16" fill="none">
                <path d="M3.5 8.5L6.5 11.5L12.5 5" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <span v-else-if="step.status === 'active'" class="tl-node-num">{{ step.index }}</span>
              <span v-else class="tl-node-num">{{ step.index }}</span>
            </div>
          </div>
          <div class="tl-label" :class="{ active: step.status === 'active' }">{{ step.label }}</div>
          <div v-if="step.status === 'active'" class="tl-current-tag">当前阶段</div>
        </div>
      </template>
    </div>
  </div>
</template>
