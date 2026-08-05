<script setup lang="ts">
import { computed } from 'vue'
import PanelCard from '@/components/layout/PanelCard.vue'
import RingChart from '@/components/charts/RingChart.vue'
import { useDashboardStore } from '@/stores/dashboard.store'
import { Leaf } from 'lucide-vue-next'

const store = useDashboardStore()

const displayMetrics = computed(() =>
  store.carbon.filter((item) => item.label !== '较基准下降').slice(0, 3)
)

const sourceColors: Record<string, string> = {
  施工用油: '#2f9cff',
  施工用电: '#69e36f',
  主要材料: '#a66cff',
  其他: '#ffb347',
}

const chartData = computed(() => {
  const total = store.carbonSrc.reduce((sum, item) => sum + Number(item.value || 0), 0)
  if (!total) return []
  return store.carbonSrc.map((item) => ({
    name: item.name,
    value: Number(((Number(item.value || 0) / total) * 100).toFixed(1)),
    color: item.color || sourceColors[item.name],
  }))
})

const levelColors: Record<string, string> = {
  高: '#69e36f',
  较高: '#2f9cff',
  中: '#ffb347',
  低: '#8fa9c8',
}

const levelWidths: Record<string, string> = {
  高: '100%',
  较高: '80%',
  中: '60%',
  低: '40%',
}

function formatMetricValue(value: string | number) {
  const numericValue = Number(value)
  return Number.isFinite(numericValue) ? numericValue.toLocaleString('en-US') : value
}
</script>

<template>
  <PanelCard title="碳足迹与低碳增益" :icon="Leaf">
    <div class="carbon-grid">
      <div v-for="item in displayMetrics" :key="item.label" class="metric-card carbon-metric-card">
        <div class="metric-label">{{ item.label }}</div>
        <div class="metric-value-row">
          <span class="metric-value">{{ formatMetricValue(item.value) }}</span>
          <span v-if="item.unit" class="metric-unit">{{ item.unit }}</span>
        </div>
      </div>
      <div class="carbon-subpanel carbon-source-panel">
        <div class="carbon-subtitle">碳足迹来源构成</div>
        <div class="carbon-source-content">
          <div class="carbon-ring-wrap">
            <RingChart :data="chartData" />
          </div>
          <div class="carbon-legend">
            <div v-for="(item, index) in chartData" :key="item.name" class="legend-row">
              <span class="legend-swatch" :style="{ background: item.color || sourceColors[item.name] }" />
              <span class="legend-name">{{ item.name }}</span>
              <span class="legend-value">{{ item.value }}%</span>
            </div>
          </div>
        </div>
      </div>
      <div class="carbon-subpanel reduction-panel">
        <div class="carbon-subtitle">主要减排措施</div>
        <div class="reduction-list">
          <div v-for="(item, index) in store.reductions" :key="index" class="reduction-row">
            <span class="reduction-name">{{ item.name }}</span>
            <span class="reduction-track">
              <span
                class="reduction-fill"
                :style="{
                  width: levelWidths[item.level] || '40%',
                  background: levelColors[item.level] || '#8fa9c8',
                }"
              />
            </span>
            <span class="reduction-level" :style="{ color: levelColors[item.level] || '#8fa9c8' }">
              {{ item.level }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </PanelCard>
</template>

<style scoped lang="scss">
.carbon-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  grid-template-rows: 70px minmax(0, 1fr);
  gap: 8px;
  min-width: 0;
  min-height: 0;
}

.carbon-metric-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
  padding: 4px 6px;
}

.carbon-metric-card .metric-label {
  margin-bottom: 4px;
  font-size: 14px;
  line-height: 18px;
}

.carbon-metric-card .metric-value {
  color: #fff;
  font-size: 32px;
  font-weight: 700;
  line-height: 1;
}

.carbon-metric-card:nth-child(1) { grid-column: 1 / span 2; }
.carbon-metric-card:nth-child(2) { grid-column: 3 / span 2; }
.carbon-metric-card:nth-child(3) { grid-column: 5 / span 2; }

.metric-value-row {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 5px;
  min-width: 0;
}

.metric-unit {
  color: var(--text-muted);
  font-size: 11.5px;
  font-weight: 400;
  line-height: 1;
  white-space: nowrap;
}

.carbon-subpanel {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  height: 100%;
  padding: 6px;
  overflow: hidden;
  background: var(--bg-card);
  border: 1px solid var(--border-blue-dim);
  border-radius: 6px;
}

.carbon-source-panel { grid-column: 1 / span 3; }
.reduction-panel { grid-column: 4 / span 3; }

.carbon-subtitle {
  height: 20px;
  margin: 0 0 6px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  line-height: 20px;
  flex-shrink: 0;
}

.carbon-source-content {
  flex: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(118px, 1.15fr);
  column-gap: 14px;
  align-items: center;
  min-width: 0;
  min-height: 0;
}

.carbon-ring-wrap {
  position: relative;
  z-index: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.carbon-ring-wrap :deep(.chart-container) {
  width: 100%;
  height: 100%;
  max-width: 100%;
  max-height: 100%;
  min-width: 0;
  min-height: 0;
}

.carbon-legend {
  position: relative;
  z-index: 1;
  display: grid;
  grid-auto-rows: 18px;
  align-content: center;
  gap: 8px;
  padding-left: 2px;
  min-width: 0;
  min-height: 0;
}

.legend-row {
  display: grid;
  grid-template-columns: 8px minmax(0, 1fr) 46px;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.legend-swatch {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}

.legend-name,
.legend-value,
.reduction-name,
.reduction-level {
  font-size: 12.5px;
  line-height: 16px;
  white-space: nowrap;
}

.legend-name,
.reduction-name {
  color: var(--text-muted);
  text-align: left;
}

.legend-value,
.reduction-level {
  font-weight: 600;
  text-align: right;
}

.reduction-level {
  font-size: 12px;
}

.reduction-list {
  flex: 1;
  display: grid;
  grid-template-rows: repeat(4, 20px);
  align-content: space-between;
  gap: 0;
  padding-bottom: 6px;
  box-sizing: border-box;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.reduction-row {
  display: grid;
  grid-template-columns: 126px minmax(0, 1fr) 34px;
  align-items: center;
  column-gap: 6px;
  min-width: 0;
  min-height: 0;
}

.reduction-name {
  overflow: hidden;
  text-overflow: ellipsis;
}

.reduction-track {
  display: block;
  width: 100%;
  height: 7px;
  overflow: hidden;
  border-radius: 4px;
  background: rgba(47, 156, 255, 0.12);
}

.reduction-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
}
</style>
