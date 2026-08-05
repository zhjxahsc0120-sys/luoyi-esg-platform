<script setup lang="ts">
import PanelCard from '@/components/layout/PanelCard.vue'
import { useDashboardStore } from '@/stores/dashboard.store'
import { Timer } from 'lucide-vue-next'

const store = useDashboardStore()
</script>

<template>
  <PanelCard title="建设阶段时间轴" :icon="Timer">
    <div class="construction-timeline">
      <div class="timeline-line" />
      <div class="timeline-steps">
        <div v-for="step in store.timeline" :key="step.index" class="timeline-step">
          <div
            class="step-node"
            :class="{ completed: step.completed, active: step.active, pending: !step.completed && !step.active }"
          >
            {{ step.index }}
          </div>
          <div class="step-label">{{ step.label }}</div>
        </div>
      </div>
    </div>
  </PanelCard>
</template>
