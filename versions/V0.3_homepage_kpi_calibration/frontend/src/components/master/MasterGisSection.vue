<script setup lang="ts">
// 第一阶段：GIS 仅外框 + 占位
// 第二阶段将只读复用 RouteMapSvg / GisLegend / LayerSwitch / SatelliteCompareCard
import { MapPin } from 'lucide-vue-next'
</script>

<template>
  <div class="master-panel">
    <div class="panel-header">
      <MapPin :size="16" style="color: var(--cyan)" />
      <span class="panel-title">项目现场一张图</span>
      <span class="panel-tag">GIS 占位 · 第二阶段填充</span>
    </div>
    <div class="panel-body">
      <div class="master-placeholder">
        路线 + K 桩号 + 图例 + 图层切换 + 罗盘 + 卫星对比卡
      </div>
    </div>
  </div>
</template>
