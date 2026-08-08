<script setup lang="ts">
import * as echarts from 'echarts'
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { getE01PointTrend } from '@/services/api'
import type { E01PointTrendPayload, E01TrendFactorOption } from '@/types/e01'
import type { EsgTrendChartMode } from '@/types/esg-class-a'

const props = defineProps<{
  pointId: number | null
  mode: EsgTrendChartMode
}>()

const loading = ref(false)
const error = ref('')
const trend = ref<E01PointTrendPayload | null>(null)
const activeFactor = ref<string | null>(null)
const chartEl = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null
let seq = 0

function dispose() {
  chart?.dispose()
  chart = null
}

function dateLabel(v?: string | null) {
  const t = String(v || '').slice(5, 10)
  return t || ''
}

function render() {
  if (!chartEl.value || !trend.value) return
  if (!chart) chart = echarts.init(chartEl.value)

  if (props.mode === 'bar') {
    const tabs = trend.value.factorOptions || []
    chart.setOption({
      grid: { left: 36, right: 8, top: 8, bottom: 22 },
      xAxis: {
        type: 'category',
        data: tabs.map((t) => t.factorName),
        axisLabel: { color: '#8ba6c3', fontSize: 11, interval: 0, rotate: tabs.length > 3 ? 15 : 0 },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      },
      yAxis: {
        type: 'value',
        minInterval: 1,
        axisLabel: { color: '#8ba6c3', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
      },
      series: [{
        type: 'bar',
        data: tabs.map((t) => t.exceedCount),
        barWidth: 18,
        itemStyle: { color: '#2f9cff', borderRadius: [3, 3, 0, 0] },
      }],
    }, true)
  } else {
    const series = trend.value.series
    const baseline = trend.value.factor.limitValueNum
    chart.setOption({
      grid: { left: 36, right: 8, top: 8, bottom: 22 },
      xAxis: {
        type: 'category',
        data: series.map((p) => dateLabel(p.at)),
        axisLabel: { color: '#8ba6c3', fontSize: 11 },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      },
      yAxis: {
        type: 'value',
        scale: true,
        axisLabel: { color: '#8ba6c3', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
      },
      series: [{
        type: 'line',
        smooth: true,
        symbolSize: 5,
        data: series.map((p, i) => ({
          value: p.valueNum,
          itemStyle: { color: series[i]?.exceeded ? '#ff5a7a' : '#69e36f' },
        })),
        lineStyle: { color: '#2f9cff', width: 1.8 },
        markLine: baseline != null ? {
          symbol: 'none',
          silent: true,
          lineStyle: { color: '#ffc857', type: 'dashed' },
          data: [{ yAxis: baseline }],
        } : undefined,
      }],
    }, true)
  }
  chart.resize()
}

async function load(pointId: number, factorCode?: string | null) {
  const cur = ++seq
  loading.value = true
  error.value = ''
  try {
    const res = await getE01PointTrend(pointId, factorCode)
    if (cur !== seq) return
    if (!res?.data) {
      trend.value = null
      error.value = '暂无趋势数据'
      dispose()
      return
    }
    trend.value = res.data
    activeFactor.value = res.data.factor.factorCode
    await nextTick()
    render()
  } catch {
    if (cur !== seq) return
    error.value = '趋势加载失败'
    trend.value = null
    dispose()
  } finally {
    if (cur === seq) loading.value = false
  }
}

function onFactorTab(tab: E01TrendFactorOption) {
  if (!props.pointId) return
  void load(props.pointId, tab.factorCode)
}

watch(() => [props.pointId, props.mode] as const, ([id]) => {
  dispose()
  trend.value = null
  if (!id) return
  void load(id)
}, { immediate: true })

watch(() => props.mode, () => nextTick(render))
onBeforeUnmount(dispose)
</script>

<template>
  <section class="trend-chart">
    <div class="head">
      <h4>选中点位趋势</h4>
      <div class="modes">
        <slot name="mode-switch" />
      </div>
    </div>
    <div v-if="mode === 'line' && trend?.factorOptions?.length" class="factor-tabs">
      <button
        v-for="tab in trend.factorOptions"
        :key="tab.factorCode"
        type="button"
        class="factor-tab"
        :class="{ active: activeFactor === tab.factorCode }"
        @click="onFactorTab(tab)"
      >
        {{ tab.factorName }}
      </button>
    </div>
    <div v-if="!pointId" class="empty">选择监测点查看趋势</div>
    <div v-else-if="loading" class="empty">趋势加载中…</div>
    <div v-else-if="error" class="empty">{{ error }}</div>
    <div v-else ref="chartEl" class="canvas" />
  </section>
</template>

<style scoped lang="scss">
.trend-chart {
  flex-shrink: 0;
  height: 190px;
  display: flex;
  flex-direction: column;
  border-top: 1px solid rgba(105, 227, 111, 0.18);
  padding-top: 8px;
}

.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;

  h4 {
    margin: 0;
    font-size: 16px;
    font-weight: 700;
    color: #e8f3ff;
  }
}

.factor-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 4px;
}

.factor-tab {
  height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  border: 1px solid rgba(47, 156, 255, 0.35);
  background: rgba(8, 40, 69, 0.55);
  color: #c5d8ef;
  font-size: 12px;
  cursor: pointer;

  &.active {
    border-color: rgba(47, 156, 255, 0.75);
    background: rgba(47, 156, 255, 0.2);
    color: #fff;
  }
}

.canvas {
  flex: 1;
  min-height: 112px;
}

.empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8ba6c3;
  font-size: 14px;
}
</style>
