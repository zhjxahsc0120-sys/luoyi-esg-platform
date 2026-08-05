<script setup lang="ts">
import { useDashboardStore } from '@/stores/dashboard.store'

const store = useDashboardStore()

const layers = [
  { key: 'all', label: '全线' },
  { key: 'section1', label: '标段一' },
  { key: 'section2', label: '标段二' },
  { key: 'environment', label: '环保点位' },
  { key: 'risk', label: '风险点' },
  { key: 'uav', label: '无人机影像' },
]
</script>

<template>
  <div class="layer-switch">
    <button
      v-for="layer in layers"
      :key="layer.key"
      class="layer-btn"
      :class="{ active: store.activeLayers.includes(layer.key) }"
      @click="store.toggleLayer(layer.key)"
    >
      {{ layer.label }}
    </button>
  </div>
</template>
