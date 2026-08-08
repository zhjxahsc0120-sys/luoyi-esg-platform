<script setup lang="ts">
import { computed } from 'vue'
import ESGRiskPanel from '@/components/esg-class-a/ESGRiskPanel.vue'
import { KPI_HOME_CATALOG } from '@/data/kpi-catalog'
import { useDashboardStore } from '@/stores/dashboard.store'
import type { E01CategoryFilter, E01OpenPoint, E01OverviewStats, E01PanelLayer, E01PointScope } from '@/types/e01'
import type { EsgClassAPanelConfig } from '@/types/esg-class-a'

defineProps<{
  selectedPointId: number | null
  layer: E01PanelLayer
  categoryFilter: E01CategoryFilter
  pointScope: E01PointScope
}>()

const emit = defineEmits<{
  close: []
  changeCategory: [category: E01CategoryFilter]
  changeScope: [scope: E01PointScope]
  selectPoint: [point: E01OpenPoint]
  clearSelection: []
  overviewReady: [points: E01OpenPoint[]]
}>()

const store = useDashboardStore()
const liveE01 = computed(() =>
  store.kpis.flatMap((g) => g.items).find((item) => item.key === 'E01'),
)
const summaryValue = computed(() => {
  const item = liveE01.value
  if (!item) return '0项'
  return item.displayText || `${item.value}${item.unit || ''}`
})

function syncHomeKpi(overview: E01OverviewStats, isDemo?: boolean) {
  store.syncE01Kpi(overview, isDemo)
}

const panelConfig = computed<EsgClassAPanelConfig>(() => ({
  moduleKey: 'E01',
  title: KPI_HOME_CATALOG.E01.fullName,
  theme: 'green',
}))
</script>

<template>
  <ESGRiskPanel
    :config="panelConfig"
    :summary-value="summaryValue"
    :selected-point-id="selectedPointId"
    :category-filter="categoryFilter"
    :point-scope="pointScope"
    @close="emit('close')"
    @change-category="emit('changeCategory', $event)"
    @change-scope="emit('changeScope', $event)"
    @select-point="emit('selectPoint', $event)"
    @clear-selection="emit('clearSelection')"
    @overview-ready="emit('overviewReady', $event)"
    @stats-ready="syncHomeKpi"
  />
</template>
