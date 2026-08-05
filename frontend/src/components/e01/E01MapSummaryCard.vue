<script setup lang="ts">
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { getE01PointTrend } from '@/services/api'
import type { E01OpenPoint, E01PointTrendPayload, E01TrendFactorOption } from '@/types/e01'
import { formatSectionLabel, typeWithSection } from '@/utils/section-label'

const props = defineProps<{
  point: E01OpenPoint | null
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const loading = ref(false)
const error = ref('')
const trend = ref<E01PointTrendPayload | null>(null)
const activeFactorCode = ref<string | null>(null)
const chartEl = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null
let loadSeq = 0

const title = computed(() => {
  const code = props.point?.pointCode
  const name = trend.value?.point.pointName || props.point?.pointName
  if (code && name && !name.includes(code)) return `${code} ${name}`
  return name || code || props.point?.locationText || '监测点'
})

const locationText = computed(
  () => trend.value?.point.locationText
    || props.point?.locationText
    || '—',
)

const typeLine = computed(() => {
  const p = trend.value?.point || props.point
  if (!p) return ''
  const typeMap: Record<string, string> = {
    WATER: '水质监测点',
    AIR: '扬尘监测点',
    NOISE: '噪声监测点',
  }
  const type = typeMap[p.monitorCategory] || `${p.monitorCategoryLabel || ''}监测点`
  const sectionText = formatSectionLabel(p.sectionCode || p.sectionName)
  return typeWithSection(type, sectionText)
})

const factorTabs = computed<E01TrendFactorOption[]>(() => {
  if (trend.value?.factorOptions?.length) return trend.value.factorOptions
  return (props.point?.factors || []).map((f) => ({
    factorCode: f.factorCode,
    factorName: f.factorName,
    unit: f.unit,
    sampleCount: 0,
    exceedCount: f.exceedMultiple != null && Number(f.exceedMultiple) > 1 ? 1 : 0,
  }))
})

const eventFactor = computed(() => {
  const code = (activeFactorCode.value || trend.value?.factor.factorCode || '').toUpperCase()
  if (!code || !props.point?.factors?.length) return null
  return props.point.factors.find((f) => String(f.factorCode).toUpperCase() === code) || null
})

const displayFactor = computed(() => {
  return eventFactor.value || props.point?.factors?.[0] || null
})

const exceedText = computed(() => {
  const multi = displayFactor.value?.exceedMultiple
  if (multi == null || Number.isNaN(Number(multi)) || Number(multi) <= 1) return null
  return `${Number(multi).toFixed(2)}倍`
})

const latestExceeded = computed(() => Boolean(trend.value?.stats.latestExceeded))

function display(value: unknown) {
  if (value === null || value === undefined || value === '') return null
  return String(value)
}

function dateOnly(value?: string | null) {
  const text = display(value)
  if (!text) return '—'
  return text.slice(0, 10)
}

function valueText(value: unknown, unit?: string | null) {
  const text = display(value)
  if (!text) return '—'
  return unit ? `${text} ${unit}` : text
}

function shortFactorName(name: string) {
  const map: Record<string, string> = {
    悬浮物: 'SS',
    pH值: 'pH',
    化学需氧量: 'COD',
    PM10日均浓度: 'PM10',
    昼间等效声级: '昼间',
    夜间等效声级: '夜间',
  }
  return map[name] || name
}

function disposeChart() {
  if (chart) {
    chart.dispose()
    chart = null
  }
}

function renderChart() {
  if (!chartEl.value || !trend.value) return
  if (!chart) chart = echarts.init(chartEl.value)
  const series = trend.value.series
  const categories = series.map((p) => dateOnly(p.at).slice(5))
  const values = series.map((p) => (p.valueNum == null ? null : p.valueNum))
  const baseline = trend.value.factor.limitValueNum
  chart.setOption(
    {
      animationDuration: 220,
      grid: { left: 34, right: 8, top: 10, bottom: 20 },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(4,25,48,0.92)',
        borderColor: 'rgba(255,159,47,0.35)',
        textStyle: { color: '#e8f3ff', fontSize: 11 },
        confine: true,
      },
      xAxis: {
        type: 'category',
        data: categories,
        axisLabel: { color: '#7f95ad', fontSize: 10 },
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.12)' } },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        scale: true,
        axisLabel: { color: '#7f95ad', fontSize: 10 },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
      },
      series: [
        {
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 5,
          data: values.map((v, i) => ({
            value: v,
            itemStyle: { color: series[i]?.exceeded ? '#ff5a7a' : '#ff9f2f' },
          })),
          lineStyle: { color: '#ff9f2f', width: 1.8 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(255,159,47,0.22)' },
              { offset: 1, color: 'rgba(255,159,47,0.02)' },
            ]),
          },
          markLine: baseline != null
            ? {
                symbol: 'none',
                silent: true,
                label: { show: false },
                lineStyle: { color: '#69e36f', type: 'dashed', width: 1.2 },
                data: [{ yAxis: baseline }],
              }
            : undefined,
        },
      ],
    },
    true,
  )
  chart.resize()
}

async function loadTrend(pointId: number, factorCode?: string | null) {
  const seq = ++loadSeq
  loading.value = true
  error.value = ''
  try {
    const res = await getE01PointTrend(pointId, factorCode)
    if (seq !== loadSeq) return
    if (!res || res.code !== 0 || !res.data) {
      trend.value = null
      error.value = '趋势暂不可用'
      disposeChart()
      return
    }
    trend.value = res.data
    activeFactorCode.value = res.data.factor.factorCode
    await nextTick()
    renderChart()
  } catch {
    if (seq !== loadSeq) return
    trend.value = null
    error.value = '趋势加载失败'
    disposeChart()
  } finally {
    if (seq === loadSeq) loading.value = false
  }
}

function switchFactor(code: string) {
  if (!props.point || code === activeFactorCode.value) return
  void loadTrend(props.point.pointId, code)
}

function onResize() {
  chart?.resize()
}

watch(
  () => [props.visible, props.point?.pointId] as const,
  ([visible, pointId]) => {
    if (!visible || pointId == null) {
      trend.value = null
      error.value = ''
      activeFactorCode.value = null
      disposeChart()
      return
    }
    activeFactorCode.value = null
    void loadTrend(pointId, null)
  },
  { immediate: true },
)

watch(
  () => props.visible,
  (visible) => {
    if (visible) window.addEventListener('resize', onResize)
    else window.removeEventListener('resize', onResize)
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  disposeChart()
})
</script>

<template>
  <aside v-if="visible && point" class="e01-map-summary" aria-label="点位摘要">
    <header class="e01-map-summary__head">
      <div>
        <p>{{ typeLine }}</p>
        <h3>{{ title }}</h3>
      </div>
      <button type="button" class="e01-map-summary__close" aria-label="关闭摘要" @click="emit('close')">×</button>
    </header>

    <div class="e01-map-summary__meta">
      <span class="status">{{ trend?.point.status || point.status }}</span>
      <span>{{ dateOnly(trend?.point.discoveredAt || point.discoveredAt) }}</span>
    </div>

    <p class="e01-map-summary__loc">
      <span>位置</span>
      {{ locationText }}
    </p>

    <div v-if="factorTabs.length > 1" class="e01-map-summary__tabs" role="tablist" aria-label="监测因子">
      <button
        v-for="tab in factorTabs"
        :key="tab.factorCode"
        type="button"
        role="tab"
        :aria-selected="activeFactorCode === tab.factorCode"
        :class="{ active: activeFactorCode === tab.factorCode, warn: tab.exceedCount > 0 }"
        @click="switchFactor(tab.factorCode)"
      >
        {{ shortFactorName(tab.factorName) }}
        <i v-if="tab.exceedCount > 0">{{ tab.exceedCount }}</i>
      </button>
    </div>

    <div class="e01-map-summary__metrics">
      <div>
        <span>监测指标</span>
        <strong>{{ trend?.factor.factorName || displayFactor?.factorName || '—' }}</strong>
      </div>
      <div>
        <span>当前值</span>
        <strong :class="{ warn: latestExceeded || (displayFactor?.exceedMultiple != null && Number(displayFactor.exceedMultiple) > 1) }">
          {{ valueText(trend?.stats.latestValue ?? displayFactor?.detectedValue, trend?.factor.unit || displayFactor?.unit) }}
        </strong>
      </div>
      <div>
        <span>标准值</span>
        <strong>{{ valueText(trend?.factor.limitValue ?? displayFactor?.limitValue, trend?.factor.unit || displayFactor?.unit) }}</strong>
      </div>
      <div>
        <span>超标情况</span>
        <strong :class="{ warn: Boolean(exceedText) }">
          {{ exceedText || (trend ? `${trend.stats.exceedCount}/${trend.stats.sampleCount}` : '—') }}
        </strong>
      </div>
    </div>

    <p v-if="eventFactor && eventFactor.exceedMultiple != null" class="e01-map-summary__event">
      事件初检
      <b>{{ valueText(eventFactor.detectedValue, eventFactor.unit) }}</b>
      · 超标 {{ eventFactor.exceedMultiple }} 倍
    </p>

    <div class="e01-map-summary__chart-wrap">
      <div class="e01-map-summary__trend-label">趋势</div>
      <div v-if="loading && !trend" class="e01-map-summary__state">加载趋势…</div>
      <div v-else-if="error && !trend" class="e01-map-summary__state is-error">{{ error }}</div>
      <div v-show="trend" ref="chartEl" class="e01-map-summary__chart" />
      <div v-if="loading && trend" class="e01-map-summary__loading">切换中…</div>
    </div>
  </aside>
</template>

<style scoped lang="scss">
.e01-map-summary {
  position: absolute;
  right: 12px;
  bottom: 12px;
  z-index: 20;
  width: min(328px, calc(100% - 24px));
  padding: 10px 12px 10px;
  border-radius: 8px;
  border: 1px solid rgba(255, 159, 47, 0.42);
  background: rgba(4, 22, 40, 0.92);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
  color: #d7e6f5;
  backdrop-filter: blur(6px);
  animation: e01-summary-in 0.22s ease-out;
}

@keyframes e01-summary-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.e01-map-summary__head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: flex-start;

  p {
    margin: 0;
    font-size: 12px;
    color: #8ba6c3;
  }

  h3 {
    margin: 3px 0 0;
    font-size: 15px;
    line-height: 1.35;
    color: #f3f8ff;
    font-weight: 700;
  }
}

.e01-map-summary__close {
  width: 26px;
  height: 26px;
  border: 1px solid rgba(255, 159, 47, 0.35);
  border-radius: 5px;
  background: rgba(8, 40, 69, 0.65);
  color: #f3f8ff;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  flex-shrink: 0;
}

.e01-map-summary__meta {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #8ba6c3;

  .status {
    color: #ff9f2f;
    border: 1px solid rgba(255, 159, 47, 0.4);
    border-radius: 3px;
    padding: 1px 6px;
  }
}

.e01-map-summary__loc {
  margin: 8px 0 0;
  font-size: 12px;
  color: #e8f3ff;
  line-height: 1.45;

  span {
    display: inline-block;
    margin-right: 6px;
    color: #7f95ad;
  }
}

.e01-map-summary__tabs {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;

  button {
    height: 24px;
    padding: 0 7px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 4px;
    background: rgba(8, 40, 69, 0.55);
    color: #8ba6c3;
    font-size: 11px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 4px;

    i {
      font-style: normal;
      font-size: 10px;
      color: #ff8f5a;
      border: 1px solid rgba(255, 143, 90, 0.35);
      border-radius: 2px;
      padding: 0 3px;
      line-height: 14px;
    }

    &.warn {
      border-color: rgba(255, 143, 90, 0.28);
    }

    &.active {
      color: #ff9f2f;
      border-color: rgba(255, 159, 47, 0.55);
      background: rgba(255, 159, 47, 0.12);
    }
  }
}

.e01-map-summary__metrics {
  margin-top: 8px;
  display: grid;
  grid-template-columns: 1.1fr 1.2fr;
  gap: 6px 10px;

  span {
    display: block;
    font-size: 11px;
    color: #7f95ad;
  }

  strong {
    display: block;
    margin-top: 1px;
    font-size: 13px;
    color: #e8f3ff;
    font-weight: 600;
    &.warn { color: #ff8f5a; }
  }
}

.e01-map-summary__event {
  margin: 6px 0 0;
  font-size: 11px;
  color: #8ba6c3;
  line-height: 1.4;

  b {
    color: #ff8f5a;
    font-weight: 600;
  }
}

.e01-map-summary__chart-wrap {
  position: relative;
  margin-top: 8px;
  height: 108px;
  border: 1px solid rgba(255, 159, 47, 0.18);
  border-radius: 5px;
  background: rgba(8, 40, 69, 0.35);
  overflow: hidden;
}

.e01-map-summary__trend-label {
  position: absolute;
  top: 4px;
  left: 6px;
  z-index: 1;
  font-size: 10px;
  color: #7f95ad;
  pointer-events: none;
}

.e01-map-summary__chart {
  width: 100%;
  height: 100%;
}

.e01-map-summary__state {
  height: 100%;
  display: grid;
  place-items: center;
  font-size: 12px;
  color: #8ba6c3;
  &.is-error { color: #ff9f2f; }
}

.e01-map-summary__loading {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  background: rgba(4, 22, 40, 0.35);
  font-size: 11px;
  color: #c3d4e8;
  pointer-events: none;
}
</style>
