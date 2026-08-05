<script setup lang="ts">
import { defineAsyncComponent, ref } from 'vue'
import type { GisBusinessLinkOpenPayload } from '@/modules/traffic-gis-overview/types'

const TrafficGisOverview = defineAsyncComponent(() =>
  import('@/modules/traffic-gis-overview').then((module) => module.TrafficGisOverview)
)

const previewTip = ref('')
let tipTimer: ReturnType<typeof setTimeout> | undefined

function handleOpenKpiSource(payload: GisBusinessLinkOpenPayload) {
  previewTip.value = `预览页已触发 KPI 来源定位：${payload.sourceId}。请在领导首页灰度态验证弹窗联动。`
  if (tipTimer) clearTimeout(tipTimer)
  tipTimer = setTimeout(() => {
    previewTip.value = ''
  }, 4000)
}
</script>

<template>
  <section class="gis-preview-container">
    <TrafficGisOverview
      project-id="LUOYI-ESG"
      data-mode="api"
      :show-legend="true"
      :show-mode-switch="false"
      :show-config-button="false"
      :design-only="true"
      @open-kpi-source="handleOpenKpiSource"
    />
    <Transition name="preview-tip">
      <div v-if="previewTip" class="gis-preview-tip">{{ previewTip }}</div>
    </Transition>
  </section>
</template>

<style scoped>
.gis-preview-container {
  position: relative;
  width: 100%;
  height: 720px;
  min-height: 520px;
}
.gis-preview-tip {
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  padding: 8px 16px;
  font-size: 12px;
  color: #b8ecff;
  background: rgba(15, 35, 60, 0.9);
  border: 1px solid rgba(47, 156, 255, 0.5);
  border-radius: 6px;
  z-index: 10;
}
.preview-tip-enter-active,
.preview-tip-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.preview-tip-enter-from,
.preview-tip-leave-to {
  opacity: 0;
  transform: translate(-50%, -10px);
}
</style>
