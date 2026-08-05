<script setup lang="ts">
import PanelCard from '@/components/layout/PanelCard.vue'
import RouteMapSvg from './RouteMapSvg.vue'
import GisLegend from './GisLegend.vue'
import LayerSwitch from './LayerSwitch.vue'
import SatelliteCompareCard from './SatelliteCompareCard.vue'
import { MapPinned } from 'lucide-vue-next'
</script>

<template>
  <PanelCard title="GIS 地图主视觉（空间态势 + 时序影像）" :icon="MapPinned">
    <div class="gis-overview-panel">
      <RouteMapSvg />
      <GisLegend />
      <LayerSwitch />
      <SatelliteCompareCard />
    </div>
  </PanelCard>
</template>
