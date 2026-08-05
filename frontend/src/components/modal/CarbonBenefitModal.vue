<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { X, Info, AlertTriangle, ChevronDown, ShieldCheck } from 'lucide-vue-next'
import type { KpiDetailConfig } from '@/types/dashboard'

const props = defineProps<{ detail: KpiDetailConfig }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const isAcceptanceMode = new URLSearchParams(window.location.search).get('acceptance') === '1'

// P3.2: C01≡E04 同 scope 勾稽 + 演示标识
const c01EqualsE04 = computed(() => (props.detail as any).c01EqualsE04 ?? true)
const topicScope = computed(() => (props.detail as any).scope ?? 'demo')
const topicIsDemo = computed(() => (props.detail as any).isDemo ?? true)
const topicBoundaryVersion = computed(() => (props.detail as any).boundaryVersion ?? 'DEMO-BOUND-E04-20260718')
const segmentAnalysisNote = computed(() => (props.detail as any).segmentAnalysisNote ?? '标段分析为演示维度，非首页 E04 KPI 口径')
// P3.2: C03 成本区默认折叠
const costCollapsed = ref(true)

type TabKey = 'overview' | 'sources' | 'benefit' | 'measures-costs'
const tabs: { key: TabKey; label: string }[] = [
  { key: 'overview', label: '碳排概览' },
  { key: 'sources', label: '排放来源' },
  { key: 'benefit', label: '低碳增益' },
  { key: 'measures-costs', label: '措施与成本' },
]

const activeTab = ref<TabKey>('overview')
const modalRef = ref<HTMLDivElement | null>(null)
const scale = ref(1)

const trendChartRef = ref<HTMLDivElement | null>(null)
const donutChartRef = ref<HTMLDivElement | null>(null)
const comparisonChartRef = ref<HTMLDivElement | null>(null)
const segmentBarChartRef = ref<HTMLDivElement | null>(null)

let trendChart: echarts.ECharts | null = null
let donutChart: echarts.ECharts | null = null
let comparisonChart: echarts.ECharts | null = null
let segmentBarChart: echarts.ECharts | null = null

const topic = computed(() => props.detail.topicData || {})
const overview = computed(() => topic.value.overview || {})
const sources = computed(() => topic.value.sources || {})
const benefit = computed(() => topic.value.benefit || {})
const measuresCosts = computed(() => topic.value.measuresCosts || {})

const monthlyEmissions = computed<any[]>(() => overview.value.monthlyEmissions || [])
const emissionSources = computed<any[]>(() => overview.value.emissionSources || sources.value.rows || [])
const materialBreakdown = computed<any[]>(() => sources.value.materialBreakdown || [])
const segmentBreakdown = computed<any[]>(() => sources.value.segmentBreakdown || [])
const materialSegmentBreakdown = computed<any[]>(() => sources.value.materialSegmentBreakdown || [])
const totalEmission = computed(() => sources.value.totalEmission ?? emissionSources.value.reduce((sum, s) => sum + Number(s.totalEmission || s.emission || 0), 0))

const benefitMonths = computed<any[]>(() => benefit.value.months || [])
const benefitActualData = computed<any[]>(() => benefit.value.actualData || [])
const benefitBaselineData = computed<any[]>(() => benefit.value.baselineData || [])
const accountingRows = computed<any[]>(() => benefit.value.accountingRows || [])
const baselineTotal = computed(() => benefit.value.baselineTotal ?? 0)
const actualTotal = computed(() => benefit.value.actualTotal ?? 0)
const accountedReduction = computed(() => benefit.value.accountedReduction ?? 0)
const reductionRate = computed(() => benefit.value.reductionRate ?? 0)
const measureEstimatedReduction = computed(() => benefit.value.measureEstimatedReduction ?? 0)

const measures = computed<any[]>(() => measuresCosts.value.measures || [])
const costSummary = computed<any>(() => measuresCosts.value.costSummary || {})

const selectedSourceCode = ref<string>('')
const selectedMeasureCode = ref<string>('')

const sourceColors = ['#69e36f', '#2f9cff', '#a66cff', '#ffb347']

// 智能精度：最多保留两位小数，末尾无意义的0不显示
// 12856.00 -> 12,856 ; 1255.44 -> 1,255.44 ; 30.00 -> 30 ; 43.80 -> 43.8
function fmt(value: unknown, maxDigits = 2): string {
  const num = Number(value)
  if (!Number.isFinite(num)) return value == null ? '—' : String(value)
  // 先用最多 maxDigits 位小数，再去除末尾无效 0
  const fixed = num.toFixed(maxDigits).replace(/\.?0+$/, '')
  // 加千分位
  const [intPart, decPart] = fixed.split('.')
  const grouped = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  return decPart ? `${grouped}.${decPart}` : grouped
}

// 保留指定位小数但不补 0（用于排放因子等业务可读精度）
function fmtFactor(value: unknown, maxDigits = 6): string {
  const num = Number(value)
  if (!Number.isFinite(num)) return value == null ? '—' : String(value)
  // 自动选择最短可读精度：从1位到maxDigits位，找到第一个不损失精度的
  for (let d = 0; d <= maxDigits; d++) {
    const candidate = num.toFixed(d)
    if (Number(candidate) === num) {
      return d === 0 ? candidate : candidate.replace(/\.?0+$/, '')
    }
  }
  return num.toFixed(maxDigits).replace(/\.?0+$/, '')
}

function fmtPct(value: unknown, maxDigits = 2): string {
  const num = Number(value)
  if (!Number.isFinite(num)) return '—'
  // 30.00 -> 30% ; 43.80 -> 43.8% ; 10.13 -> 10.13%
  const fixed = num.toFixed(maxDigits).replace(/\.?0+$/, '')
  return fixed + '%'
}

// ===== 分页逻辑（每页6项，统一用于三个明细表） =====
const TABLE_PAGE_SIZE = 6
const monthlyTablePage = ref(1)
const accountingTablePage = ref(1)
const measuresTablePage = ref(1)

const monthlyTableTotalPages = computed(() => Math.max(1, Math.ceil(monthlyEmissions.value.length / TABLE_PAGE_SIZE)))
const pagedMonthlyEmissions = computed(() => {
  const reversed = [...monthlyEmissions.value].reverse()
  const start = (monthlyTablePage.value - 1) * TABLE_PAGE_SIZE
  return reversed.slice(start, start + TABLE_PAGE_SIZE)
})

const accountingTableTotalPages = computed(() => Math.max(1, Math.ceil(accountingRows.value.length / TABLE_PAGE_SIZE)))
const pagedAccountingRows = computed(() => {
  const start = (accountingTablePage.value - 1) * TABLE_PAGE_SIZE
  return accountingRows.value.slice(start, start + TABLE_PAGE_SIZE)
})

const measuresTableTotalPages = computed(() => Math.max(1, Math.ceil(measures.value.length / TABLE_PAGE_SIZE)))
const pagedMeasures = computed(() => {
  const start = (measuresTablePage.value - 1) * TABLE_PAGE_SIZE
  return measures.value.slice(start, start + TABLE_PAGE_SIZE)
})

watch([monthlyEmissions], () => { monthlyTablePage.value = 1 })
watch([accountingRows], () => { accountingTablePage.value = 1 })
watch([measures], () => { measuresTablePage.value = 1 })

function updateScale() {
  scale.value = Math.min(1, window.innerWidth / 1436, window.innerHeight / 880)
}

function handleResize() {
  updateScale()
  trendChart?.resize()
  donutChart?.resize()
  comparisonChart?.resize()
  segmentBarChart?.resize()
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') emit('close')
}

function closeOnOverlay(event: MouseEvent) {
  if (event.target === event.currentTarget) emit('close')
}

const selectedSource = computed(() => emissionSources.value.find(s => s.sourceCode === selectedSourceCode.value) || emissionSources.value[0])

const materialSegmentRows = computed(() => {
  return materialSegmentBreakdown.value.map((row: any) => {
    const m: Record<string, number> = {}
    if (Array.isArray(row.materials)) {
      row.materials.forEach((mat: any) => {
        const key = mat.materialCode || mat.materialTypeCode || ''
        m[key] = Number(mat.emissionAmount || 0)
      })
    }
    const cement = m.cement || m.CEMENT || 0
    const steel = m.steel || m.STEEL || 0
    const asphalt = m.asphalt || m.ASPHALT || 0
    return {
      segmentCode: row.segmentCode,
      segmentName: row.segmentName,
      cementEmission: cement,
      steelEmission: steel,
      asphaltEmission: asphalt,
      totalEmission: cement + steel + asphalt,
    }
  })
})

const selectedSourceSegments = computed(() => {
  const src = selectedSource.value
  if (!src) return []
  if (src.segments) return src.segments
  if (src.sourceCode === 'material') {
    return materialSegmentRows.value.map((item: any) => ({
      segmentCode: item.segmentCode,
      segmentName: item.segmentName,
      emissionAmount: item.totalEmission,
      activityAmount: 0,
      share: 0,
    }))
  }
  return []
})

const selectedSourceMaxEmission = computed(() => {
  const segs = selectedSourceSegments.value
  if (!segs.length) return 1
  return Math.max(...segs.map((s: any) => Number(s.emissionAmount || s.totalEmission || 0)), 1)
})

function initTrendChart() {
  if (!trendChartRef.value) return
  trendChart?.dispose()
  trendChart = echarts.init(trendChartRef.value)
  const monthly = monthlyEmissions.value
  const months = monthly.map(m => m.month?.replace(/^\d{4}-/, '') + '月' || '')
  const monthlyData = monthly.map(m => Number(m.monthlyEmission) || 0)
  const cumulativeData = monthly.map(m => Number(m.cumulativeEmission) || 0)

  trendChart.setOption({
    animation: !isAcceptanceMode,
    animationDuration: 600,
    tooltip: {
      trigger: 'axis',
      textStyle: { fontSize: 13 },
      backgroundColor: 'rgba(7, 25, 45, 0.95)',
      borderColor: 'rgba(105, 227, 111, 0.3)',
      formatter: (params: any[]) => {
        const month = params[0]?.axisValue ?? ''
        const lines = [month]
        params.forEach(p => {
          lines.push(`${p.marker}${p.seriesName}：${fmt(p.value)} tCO₂e`)
        })
        return lines.join('<br/>')
      },
    },
    legend: {
      top: 4,
      left: 'center',
      itemWidth: 14,
      itemHeight: 8,
      itemGap: 24,
      textStyle: { color: '#b8cce3', fontSize: 13 },
      data: ['当月排放', '累计排放'],
    },
    grid: { left: 60, right: 70, top: 38, bottom: 36, containLabel: false },
    xAxis: {
      type: 'category',
      data: months,
      axisLine: { lineStyle: { color: 'rgba(143, 169, 200, 0.28)' } },
      axisTick: { show: false },
      axisLabel: { color: '#b8cce3', fontSize: 13, margin: 10 },
    },
    yAxis: [
      {
        type: 'value',
        name: '当月 tCO₂e',
        nameTextStyle: { color: '#8fa9c8', fontSize: 12 },
        axisLabel: { color: '#8fa9c8', fontSize: 12 },
        splitLine: { lineStyle: { color: 'rgba(143, 169, 200, 0.09)' } },
      },
      {
        type: 'value',
        name: '累计 tCO₂e',
        nameTextStyle: { color: '#8fa9c8', fontSize: 12 },
        axisLabel: { color: '#8fa9c8', fontSize: 12 },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '当月排放',
        type: 'bar',
        barWidth: 46,
        barMaxWidth: 48,
        data: monthlyData,
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#63DC75' },
            { offset: 0.5, color: '#43C965' },
            { offset: 1, color: '#24944E' },
          ]),
        },
      },
      {
        name: '累计排放',
        type: 'line',
        yAxisIndex: 1,
        symbol: 'circle',
        symbolSize: 8,
        showSymbol: true,
        lineStyle: { width: 2.8, color: '#31B7FF', type: 'solid' },
        itemStyle: { color: '#E8F7FF', borderColor: '#31B7FF', borderWidth: 2 },
        data: cumulativeData,
        smooth: false,
        // 不在折线末端额外显示数值标签，避免与摘要卡重复
        label: { show: false },
        endLabel: { show: false },
      },
    ],
  })
}

function initDonutChart() {
  if (!donutChartRef.value) return
  donutChart?.dispose()
  donutChart = echarts.init(donutChartRef.value)
  const srcs = emissionSources.value
  const data = srcs.map((s, i) => ({
    name: s.sourceName || s.source,
    value: Number(s.totalEmission || s.emission || 0),
    itemStyle: { color: sourceColors[i % sourceColors.length] },
  }))

  donutChart.setOption({
    animation: !isAcceptanceMode,
    animationDuration: 600,
    tooltip: {
      trigger: 'item',
      textStyle: { fontSize: 13 },
      backgroundColor: 'rgba(7, 25, 45, 0.95)',
      borderColor: 'rgba(105, 227, 111, 0.3)',
      formatter: (params: any) => {
        return `${params.marker}${params.name}<br/>排放量：${fmt(params.value)} tCO₂e<br/>占比：${fmtPct(params.percent)}`
      },
    },
    series: [
      {
        type: 'pie',
        radius: ['36px', '60px'],
        center: ['50%', '48%'],
        avoidLabelOverlap: false,
        label: { show: false },
        labelLine: { show: false },
        data,
      },
    ],
  })
}

function initComparisonChart() {
  if (!comparisonChartRef.value) return
  comparisonChart?.dispose()
  comparisonChart = echarts.init(comparisonChartRef.value)
  const months = benefitMonths.value.length
    ? benefitMonths.value.map((m: string) => m.replace(/^\d{4}-/, '') + '月')
    : accountingRows.value.map(r => r.month?.replace(/^\d{4}-/, '') + '月' || '')
  const baseline = benefitBaselineData.value.length
    ? benefitBaselineData.value
    : accountingRows.value.map(r => Number(r.baselineEmission) || 0)
  const actual = benefitActualData.value.length
    ? benefitActualData.value
    : accountingRows.value.map(r => Number(r.actualEmission) || 0)

  comparisonChart.setOption({
    animation: !isAcceptanceMode,
    animationDuration: 600,
    tooltip: {
      trigger: 'axis',
      textStyle: { fontSize: 13 },
      backgroundColor: 'rgba(7, 25, 45, 0.95)',
      borderColor: 'rgba(105, 227, 111, 0.3)',
      axisPointer: { type: 'shadow' },
      formatter: (params: any[]) => {
        const month = params[0]?.axisValue ?? ''
        const lines = [month]
        params.forEach(p => {
          lines.push(`${p.marker}${p.seriesName}：${fmt(p.value)} tCO₂e`)
        })
        return lines.join('<br/>')
      },
    },
    legend: {
      top: 4,
      right: 10,
      itemWidth: 14,
      itemHeight: 8,
      itemGap: 20,
      textStyle: { color: '#b8cce3', fontSize: 13 },
      data: ['同口径基准排放', '同口径实际排放'],
    },
    grid: { left: 60, right: 20, top: 44, bottom: 36 },
    xAxis: {
      type: 'category',
      data: months,
      axisLine: { lineStyle: { color: 'rgba(143, 169, 200, 0.28)' } },
      axisTick: { show: false },
      axisLabel: { color: '#b8cce3', fontSize: 13, margin: 10 },
    },
    yAxis: {
      type: 'value',
      name: 'tCO₂e',
      nameTextStyle: { color: '#8fa9c8', fontSize: 12 },
      axisLabel: { color: '#8fa9c8', fontSize: 12 },
      splitLine: { lineStyle: { color: 'rgba(143, 169, 200, 0.09)' } },
    },
    series: [
      {
        name: '同口径基准排放',
        type: 'bar',
        barWidth: 26,
        barGap: '18%',
        data: baseline,
        itemStyle: {
          borderRadius: [3, 3, 0, 0],
          color: '#2f9cff',
        },
      },
      {
        name: '同口径实际排放',
        type: 'bar',
        barWidth: 26,
        data: actual,
        itemStyle: {
          borderRadius: [3, 3, 0, 0],
          color: '#43c965',
        },
      },
    ],
  })
}

function initSegmentBarChart() {
  if (!segmentBarChartRef.value) return
  segmentBarChart?.dispose()
  segmentBarChart = echarts.init(segmentBarChartRef.value)
  const segs = selectedSourceSegments.value
  const names = segs.map((s: any) => s.segmentName || s.name || '')
  const values = segs.map((s: any) => Number(s.emissionAmount || s.totalEmission || s.emission || 0))
  const src = selectedSource.value
  const colorIndex = emissionSources.value.findIndex(s => s.sourceCode === selectedSourceCode.value)
  const barColor = sourceColors[colorIndex >= 0 ? colorIndex : 0]

  segmentBarChart.setOption({
    animation: !isAcceptanceMode,
    animationDuration: 500,
    tooltip: {
      trigger: 'axis',
      textStyle: { fontSize: 13 },
      backgroundColor: 'rgba(7, 25, 45, 0.95)',
      borderColor: 'rgba(105, 227, 111, 0.3)',
      axisPointer: { type: 'shadow' },
      formatter: (params: any[]) => {
        const p = params[0]
        return `${p.name}<br/>${p.marker}排放量：${fmt(p.value)} tCO₂e`
      },
    },
    grid: { left: 10, right: 50, top: 10, bottom: 10, containLabel: true },
    xAxis: {
      type: 'value',
      show: false,
    },
    yAxis: {
      type: 'category',
      data: names,
      inverse: true,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#b8cce3', fontSize: 13 },
    },
    series: [
      {
        type: 'bar',
        barWidth: 13,
        data: values,
        itemStyle: {
          borderRadius: [0, 2, 2, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: barColor + '99' },
            { offset: 1, color: barColor },
          ]),
        },
        label: {
          show: true,
          position: 'right',
          color: '#d9e7f5',
          fontSize: 13,
          formatter: (params: any) => fmt(params.value),
        },
      },
    ],
  })
}

function initAllCharts() {
  nextTick(() => {
    if (activeTab.value === 'overview') {
      initTrendChart()
      initDonutChart()
    } else if (activeTab.value === 'sources') {
      initSegmentBarChart()
    } else if (activeTab.value === 'benefit') {
      initComparisonChart()
    }
  })
}

watch(activeTab, () => {
  nextTick(() => {
    if (activeTab.value === 'overview') {
      if (!trendChart) initTrendChart()
      if (!donutChart) initDonutChart()
      else { trendChart.resize(); donutChart.resize() }
    } else if (activeTab.value === 'sources') {
      if (!segmentBarChart) initSegmentBarChart()
      else segmentBarChart.resize()
    } else if (activeTab.value === 'benefit') {
      if (!comparisonChart) initComparisonChart()
      else comparisonChart.resize()
    }
  })
})

watch(selectedSourceCode, () => {
  nextTick(() => {
    if (activeTab.value === 'sources') {
      initSegmentBarChart()
    }
  })
})

watch(() => props.detail, () => {
  if (!isAcceptanceMode) {
    initAllCharts()
  }
}, { deep: true })

const accountingMonthsCount = computed(() => monthlyEmissions.value.length || 6)
const startMonth = computed(() => monthlyEmissions.value[0]?.month || '2026-02')
const endMonth = computed(() => monthlyEmissions.value[monthlyEmissions.value.length - 1]?.month || '2026-07')

function formatMonthRange(start: string, end: string) {
  const s = start.replace('-', '年') + '月'
  const e = end.replace(/^\d{4}-/, '') + '月'
  return `${s}至${e}`
}

onMounted(() => {
  updateScale()
  if (emissionSources.value.length > 0) {
    selectedSourceCode.value = emissionSources.value[0].sourceCode || 'diesel'
  }
  if (measures.value.length > 0) {
    selectedMeasureCode.value = measures.value[0].measureCode || measures.value[0].id
  }
  nextTick(() => {
    initAllCharts()
    modalRef.value?.focus()
  })
  window.addEventListener('resize', handleResize)
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleKeydown)
  trendChart?.dispose()
  donutChart?.dispose()
  comparisonChart?.dispose()
  segmentBarChart?.dispose()
  trendChart = null
  donutChart = null
  comparisonChart = null
  segmentBarChart = null
})
</script>

<template>
  <Teleport to="body">
    <div class="carbon-overlay" :class="{ acceptance: isAcceptanceMode }" @click="closeOnOverlay">
      <div
        ref="modalRef"
        class="carbon-modal"
        :class="{ acceptance: isAcceptanceMode }"
        :style="{ '--carbon-scale': scale }"
        role="dialog"
        aria-modal="true"
        aria-labelledby="carbon-modal-title"
        tabindex="-1"
      >
        <header class="carbon-header">
          <h2 id="carbon-modal-title">
            <b>CARBON</b>
            <span>{{ detail.fullName || '碳足迹与低碳增益' }}</span>
          </h2>
          <!-- P3.2: C01≡E04 同 scope 勾稽标识 -->
          <div class="header-scope-badges">
            <span v-if="topicIsDemo" class="scope-badge scope-demo"><ShieldCheck :size="13" />演示数据</span>
            <span class="scope-badge scope-consistent" :class="{ 'scope-mismatch': !c01EqualsE04 }">
              {{ c01EqualsE04 ? 'C01 ≡ E04 同源' : 'C01 ≠ E04 异常' }}
            </span>
            <span class="scope-badge scope-boundary">{{ topicBoundaryVersion }}</span>
          </div>
          <div class="header-meta">
            <i />
            <span>MySQL 碳核算专题数据</span>
            <span class="meta-dot">·</span>
            <span>{{ (detail as any).updatedAt || detail.updateTime || '—' }}</span>
          </div>
          <button type="button" aria-label="关闭" class="close-btn" @click="emit('close')">
            <X :size="22" />
          </button>
        </header>

        <nav class="carbon-tabs" aria-label="碳专题页签">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            type="button"
            class="tab-btn"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </nav>

        <main class="carbon-body">
          <!-- 页签一：碳排概览 -->
          <section v-if="activeTab === 'overview'" class="tab-page overview-page">
            <div class="summary-grid summary-five">
              <div class="summary-card card-green">
                <span class="card-label">项目累计碳排放</span>
                <div class="card-value-row">
                  <strong class="card-value">{{ fmt(totalEmission) }}</strong>
                  <em class="card-unit">tCO₂e</em>
                </div>
              </div>
              <div class="summary-card card-green">
                <span class="card-label">本月碳排放</span>
                <div class="card-value-row">
                  <strong class="card-value">{{ fmt(monthlyEmissions[monthlyEmissions.length - 1]?.monthlyEmission) }}</strong>
                  <em class="card-unit">tCO₂e</em>
                </div>
              </div>
              <div class="summary-card card-teal">
                <span class="card-label">相对基准核算减排量</span>
                <div class="card-value-row">
                  <strong class="card-value">{{ fmt(accountedReduction) }}</strong>
                  <em class="card-unit">tCO₂e</em>
                </div>
              </div>
              <div class="summary-card card-blue">
                <span class="card-label">在施低碳措施</span>
                <div class="card-value-row">
                  <strong class="card-value">{{ measures.length }}</strong>
                  <em class="card-unit">项</em>
                </div>
              </div>
              <div class="summary-card card-blue">
                <span class="card-label">核算月份</span>
                <div class="card-value-row">
                  <strong class="card-value">{{ accountingMonthsCount }}</strong>
                  <em class="card-unit">个月</em>
                </div>
              </div>
            </div>

            <div class="overview-content">
              <div class="overview-left">
                <div class="panel trend-panel">
                  <div class="panel-title">
                    <b>月度排放趋势</b>
                    <span class="panel-sub">单位：tCO₂e</span>
                  </div>
                  <div ref="trendChartRef" class="trend-chart"></div>
                </div>

                <div class="panel monthly-table-panel">
                  <div class="panel-title">
                    <b>月度排放明细</b>
                    <span class="panel-sub">共 {{ monthlyEmissions.length }} 项</span>
                  </div>
                  <div class="table-wrap table-wrap--paged">
                    <table>
                      <thead>
                        <tr>
                          <th class="col-left">月份</th>
                          <th class="col-right">当月排放 (tCO₂e)</th>
                          <th class="col-right">累计排放 (tCO₂e)</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="item in pagedMonthlyEmissions" :key="item.month">
                          <td class="col-left">{{ item.month }}</td>
                          <td class="col-right">{{ fmt(item.monthlyEmission) }}</td>
                          <td class="col-right">{{ fmt(item.cumulativeEmission) }}</td>
                        </tr>
                        <tr v-if="pagedMonthlyEmissions.length === 0">
                          <td colspan="3" class="empty">暂无月度排放数据</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="pagination">
                    <span class="page-info">第 {{ monthlyTablePage }} / {{ monthlyTableTotalPages }} 页：共 {{ monthlyEmissions.length }} 项：每页 {{ TABLE_PAGE_SIZE }} 项</span>
                    <div class="page-actions">
                      <button type="button" class="page-btn" :disabled="monthlyTablePage === 1" @click="monthlyTablePage--">上一页</button>
                      <button type="button" class="page-btn" :disabled="monthlyTablePage === monthlyTableTotalPages" @click="monthlyTablePage++">下一页</button>
                    </div>
                  </div>
                </div>
              </div>

              <div class="overview-right">
                <div class="panel source-panel">
                  <div class="panel-title">
                    <b>排放来源构成</b>
                  </div>
                  <div class="source-donut-wrap">
                    <div ref="donutChartRef" class="donut-chart"></div>
                    <div class="donut-center">
                      <div class="donut-value">{{ fmt(totalEmission) }}</div>
                      <div class="donut-unit">tCO₂e</div>
                    </div>
                  </div>
                  <div class="source-list">
                    <div
                      v-for="(src, idx) in emissionSources"
                      :key="src.sourceCode || src.source"
                      class="source-item"
                    >
                      <i class="source-dot" :style="{ background: sourceColors[idx % sourceColors.length] }"></i>
                      <span class="source-name">{{ src.sourceName || src.source }}</span>
                      <span class="source-value">{{ fmt(src.totalEmission || src.emission) }}</span>
                      <span class="source-share">{{ fmtPct(src.share) }}</span>
                    </div>
                  </div>
                </div>

                <div class="panel scope-panel">
                  <div class="panel-title">
                    <b>本期核算说明</b>
                  </div>
                  <div class="scope-content">
                    <div class="scope-row">
                      <span class="scope-label">核算阶段</span>
                      <span class="scope-value">施工阶段</span>
                    </div>
                    <div class="scope-row">
                      <span class="scope-label">统计期间</span>
                      <span class="scope-value">{{ formatMonthRange(startMonth, endMonth) }}</span>
                    </div>
                    <div class="scope-row">
                      <span class="scope-label">纳入来源</span>
                      <span class="scope-value">{{ emissionSources.length }}类</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- 页签二：排放来源 -->
          <section v-else-if="activeTab === 'sources'" class="tab-page sources-page">
            <div class="sources-top">
              <div class="panel source-summary-panel">
                <div class="panel-title">
                  <b>排放来源核算汇总</b>
                  <span class="panel-sub">来源合计：{{ fmt(totalEmission) }} tCO₂e</span>
                </div>
                <div class="table-wrap table-wrap--paged">
                  <table class="source-summary-table">
                    <colgroup>
                      <col style="width: 16%">
                      <col style="width: 20%">
                      <col style="width: 10%">
                      <col style="width: 15%">
                      <col style="width: 14%">
                      <col style="width: 17%">
                      <col style="width: 8%">
                    </colgroup>
                    <thead>
                      <tr>
                        <th class="col-left">排放来源</th>
                        <th class="col-right">活动量</th>
                        <th class="col-center">单位</th>
                        <th class="col-right">排放因子</th>
                        <th class="col-center">因子单位</th>
                        <th class="col-right">核算排放量 (tCO₂e)</th>
                        <th class="col-right">排放占比</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="src in emissionSources"
                        :key="src.sourceCode || src.source"
                        :class="{ selected: selectedSourceCode === src.sourceCode }"
                        @click="selectedSourceCode = src.sourceCode"
                      >
                        <td class="col-left">
                          <i v-if="selectedSourceCode === src.sourceCode" class="row-indicator"></i>
                          {{ src.sourceName || src.source }}
                        </td>
                        <td class="col-right">{{ fmt(src.totalActivityAmount || src.activityValue) }}</td>
                        <td class="col-center">{{ src.activityUnit }}</td>
                        <td class="col-right">{{ src.emissionFactor != null ? fmtFactor(src.emissionFactor, 6) : '分项核算' }}</td>
                        <td class="col-center">{{ src.factorUnit || '—' }}</td>
                        <td class="col-right"><b>{{ fmt(src.totalEmission || src.emission) }}</b></td>
                        <td class="col-right">{{ fmtPct(src.share) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <div class="sources-bottom">
              <div class="panel segment-panel">
                <div class="panel-title">
                  <b>{{ selectedSource?.sourceName || selectedSource?.source || '标段分解' }} - 标段分解</b>
                  <span class="panel-sub segment-analysis-note">{{ segmentAnalysisNote }}</span>
                </div>
                <div class="segment-content segment-content--full">
                  <div v-if="selectedSource?.sourceCode === 'material'" class="segment-full">
                    <div class="table-wrap table-wrap--paged">
                      <table class="matrix-table">
                        <colgroup>
                          <col style="width: 22%">
                          <col style="width: 17%">
                          <col style="width: 17%">
                          <col style="width: 17%">
                          <col style="width: 27%">
                        </colgroup>
                        <thead>
                          <tr>
                            <th class="col-left">标段</th>
                            <th class="col-right">水泥排放</th>
                            <th class="col-right">钢材排放</th>
                            <th class="col-right">沥青排放</th>
                            <th class="col-right">材料排放合计</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="row in materialSegmentRows" :key="row.segmentCode">
                            <td class="col-left">{{ row.segmentName }}</td>
                            <td class="col-right">{{ fmt(row.cementEmission) }}</td>
                            <td class="col-right">{{ fmt(row.steelEmission) }}</td>
                            <td class="col-right">{{ fmt(row.asphaltEmission) }}</td>
                            <td class="col-right"><b>{{ fmt(row.totalEmission) }}</b></td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                  <div v-else class="segment-full">
                    <div class="table-wrap table-wrap--paged">
                      <table>
                        <colgroup>
                          <col style="width: 22%">
                          <col style="width: 20%">
                          <col style="width: 17%">
                          <col style="width: 17%">
                          <col style="width: 24%">
                        </colgroup>
                        <thead>
                          <tr>
                            <th class="col-left">标段</th>
                            <th class="col-right">活动量</th>
                            <th class="col-left">活动量单位</th>
                            <th class="col-right">核算排放量 (tCO₂e)</th>
                            <th class="col-right">该来源占比</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="seg in selectedSource?.segments || []" :key="seg.segmentCode">
                            <td class="col-left">{{ seg.segmentName }}</td>
                            <td class="col-right">{{ fmt(seg.activityAmount) }}</td>
                            <td class="col-left">{{ selectedSource?.activityUnit || '—' }}</td>
                            <td class="col-right">{{ fmt(seg.emissionAmount) }}</td>
                            <td class="col-right">{{ fmtPct(seg.share) }}</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                  <div class="segment-bar-wrap">
                    <div ref="segmentBarChartRef" class="segment-bar-chart"></div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- 页签三：低碳增益 -->
          <section v-else-if="activeTab === 'benefit'" class="tab-page benefit-page">
            <!-- P3.2: C02 演示/平台测算标识 -->
            <div class="topic-demo-notice">
              <AlertTriangle :size="14" />
              <span>本页减排核算数据为演示/平台测算，未经甲方确认，不作为正式核算依据。</span>
            </div>
            <div class="summary-grid summary-four">
              <div class="summary-card card-blue">
                <span class="card-label">同口径基准排放</span>
                <div class="card-value-row">
                  <strong class="card-value">{{ fmt(baselineTotal) }}</strong>
                  <em class="card-unit">tCO₂e</em>
                </div>
              </div>
              <div class="summary-card card-green">
                <span class="card-label">同口径实际排放</span>
                <div class="card-value-row">
                  <strong class="card-value">{{ fmt(actualTotal) }}</strong>
                  <em class="card-unit">tCO₂e</em>
                </div>
              </div>
              <div class="summary-card card-teal">
                <span class="card-label">相对基准核算减排量</span>
                <div class="card-value-row">
                  <strong class="card-value">{{ fmt(accountedReduction) }}</strong>
                  <em class="card-unit">tCO₂e</em>
                </div>
              </div>
              <div class="summary-card card-teal">
                <span class="card-label">低碳措施预计减排量</span>
                <div class="card-value-row">
                  <strong class="card-value">{{ fmt(measureEstimatedReduction) }}</strong>
                  <em class="card-unit">tCO₂e</em>
                </div>
              </div>
            </div>

            <div class="benefit-content">
              <div class="benefit-left">
                <div class="panel comparison-panel">
                  <div class="panel-title">
                    <div class="title-with-icon">
                      <b>月度基准排放与实际排放对比</b>
                      <div class="info-icon-wrap">
                        <Info :size="14" class="info-icon" />
                        <div class="info-tooltip">同口径基准排放与实际排放采用相同统计期间和排放来源范围。</div>
                      </div>
                    </div>
                    <span class="panel-sub">单位：tCO₂e</span>
                  </div>
                  <div ref="comparisonChartRef" class="comparison-chart"></div>
                </div>

                <div class="panel accounting-table-panel">
                  <div class="panel-title">
                    <b>月度减排核算明细</b>
                    <span class="panel-sub">共 {{ accountingRows.length }} 项</span>
                  </div>
                  <div class="table-wrap table-wrap--paged">
                    <table>
                      <colgroup>
                        <col style="width: 20%">
                        <col style="width: 22%">
                        <col style="width: 22%">
                        <col style="width: 18%">
                        <col style="width: 18%">
                      </colgroup>
                      <thead>
                        <tr>
                          <th class="col-left">月份</th>
                          <th class="col-right">同口径基准排放 (tCO₂e)</th>
                          <th class="col-right">同口径实际排放 (tCO₂e)</th>
                          <th class="col-right">核算差额 (tCO₂e)</th>
                          <th class="col-right">差额比例 (%)</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="row in pagedAccountingRows" :key="row.month || row.accountingCode">
                          <td class="col-left">{{ row.month }}</td>
                          <td class="col-right">{{ fmt(row.baselineEmission) }}</td>
                          <td class="col-right">{{ fmt(row.actualEmission) }}</td>
                          <td class="col-right positive">{{ fmt(row.accountedReduction) }}</td>
                          <td class="col-right positive">{{ fmtPct(row.reductionRate || (row.baselineEmission ? row.accountedReduction / row.baselineEmission * 100 : 0)) }}</td>
                        </tr>
                        <tr v-if="pagedAccountingRows.length === 0">
                          <td colspan="5" class="empty">暂无减排核算数据</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="pagination">
                    <span class="page-info">第 {{ accountingTablePage }} / {{ accountingTableTotalPages }} 页 · 共 {{ accountingRows.length }} 项 · 每页 {{ TABLE_PAGE_SIZE }} 项</span>
                    <div class="page-actions">
                      <button type="button" class="page-btn" :disabled="accountingTablePage === 1" @click="accountingTablePage--">上一页</button>
                      <button type="button" class="page-btn" :disabled="accountingTablePage === accountingTableTotalPages" @click="accountingTablePage++">下一页</button>
                    </div>
                  </div>
                </div>
              </div>

              <div class="benefit-right">
                <div class="panel caliber-panel">
                  <div class="panel-title">
                    <b>减排量口径说明</b>
                  </div>
                  <div class="caliber-content">
                    <div class="caliber-item">
                      <p class="caliber-text">
                        <b>相对基准核算减排量 {{ fmt(accountedReduction) }} tCO₂e：</b>
                        同口径基准排放 − 实际排放。
                      </p>
                    </div>
                    <div class="caliber-item">
                      <p class="caliber-text">
                        <b>低碳措施预计减排量 {{ fmt(measureEstimatedReduction) }} tCO₂e：</b>
                        各项低碳措施的预估减排效果汇总。
                      </p>
                    </div>
                    <div class="caliber-item">
                      <p class="caliber-notice">
                        两项指标的统计方法和用途不同，不作合计。
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- 页签四：措施与成本 -->
          <section v-else class="tab-page measures-page">
            <!-- P3.2: C05 演示/平台测算标识 -->
            <div class="topic-demo-notice">
              <AlertTriangle :size="14" />
              <span>措施预计减排量与成本数据为演示/平台测算，未经甲方确认；措施预计减排量不与核算减排量合计。</span>
            </div>
            <div class="summary-grid summary-four">
              <div class="summary-card card-blue">
                <span class="card-label">低碳措施预计投入</span>
                <div class="card-value-row">
                  <strong class="card-value">{{ fmt(costSummary.investmentCost) }}</strong>
                  <em class="card-unit">{{ costSummary.currencyUnit || '万元' }}</em>
                </div>
              </div>
              <div class="summary-card card-green">
                <span class="card-label">预计运行费用节约</span>
                <div class="card-value-row">
                  <strong class="card-value">{{ fmt(costSummary.operatingSaving) }}</strong>
                  <em class="card-unit">{{ costSummary.currencyUnit || '万元' }}</em>
                </div>
              </div>
              <div class="summary-card card-green">
                <span class="card-label">预计材料运输及处置支出减少</span>
                <div class="card-value-row">
                  <strong class="card-value">{{ fmt(costSummary.materialTransportDisposalSaving) }}</strong>
                  <em class="card-unit">{{ costSummary.currencyUnit || '万元' }}</em>
                </div>
              </div>
              <div class="summary-card card-teal">
                <span class="card-label">低碳措施节约成本</span>
                <div class="card-value-row">
                  <strong class="card-value">{{ fmt(costSummary.totalCostSaving ?? (Number(costSummary.operatingSaving || 0) + Number(costSummary.materialTransportDisposalSaving || 0))) }}</strong>
                  <em class="card-unit">{{ costSummary.currencyUnit || '万元' }}</em>
                </div>
              </div>
            </div>

            <div class="measures-content">
              <div class="measures-left">
                <div class="panel measures-table-panel">
                  <div class="panel-title">
                    <b>措施台账</b>
                    <span class="panel-sub">共 {{ measures.length }} 项</span>
                  </div>
                  <div class="table-wrap table-wrap--paged">
                    <table class="measures-table">
                      <colgroup>
                        <col style="width: 24%">
                        <col style="width: 20%">
                        <col style="width: 12%">
                        <col style="width: 14%">
                        <col style="width: 15%">
                        <col style="width: 15%">
                      </colgroup>
                      <thead>
                        <tr>
                          <th class="col-left">措施名称</th>
                          <th class="col-left">应用范围</th>
                          <th class="col-center">实施状态</th>
                          <th class="col-right">预计减排量 (tCO₂e)</th>
                          <th class="col-right">投入成本 (万元)</th>
                          <th class="col-right">运行节约 (万元)</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr
                          v-for="m in pagedMeasures"
                          :key="m.measureCode || m.id"
                          :class="{ selected: selectedMeasureCode === (m.measureCode || m.id) }"
                          @click="selectedMeasureCode = m.measureCode || m.id"
                        >
                          <td class="col-left">
                            <i v-if="selectedMeasureCode === (m.measureCode || m.id)" class="row-indicator"></i>
                            {{ m.measureName }}
                          </td>
                          <td class="col-left measure-scope">{{ m.scope }}</td>
                          <td class="col-center">
                            <span class="status-tag">{{ m.status }}</span>
                          </td>
                          <td class="col-right">{{ fmt(m.estimatedReduction) }}</td>
                          <td class="col-right">{{ fmt(m.investmentCost) }}</td>
                          <td class="col-right">{{ fmt(m.operatingSaving) }}</td>
                        </tr>
                        <tr v-if="pagedMeasures.length === 0">
                          <td colspan="6" class="empty">暂无措施台账数据</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="pagination">
                    <span class="page-info">第 {{ measuresTablePage }} / {{ measuresTableTotalPages }} 页 · 共 {{ measures.length }} 项 · 每页 {{ TABLE_PAGE_SIZE }} 项</span>
                    <div class="page-actions">
                      <button type="button" class="page-btn" :disabled="measuresTablePage === 1" @click="measuresTablePage--">上一页</button>
                      <button type="button" class="page-btn" :disabled="measuresTablePage === measuresTableTotalPages" @click="measuresTablePage++">下一页</button>
                    </div>
                  </div>
                </div>
              </div>

              <div class="measures-right">
                <div class="panel cost-panel">
                  <!-- P3.2: C03 默认折叠 + 强演示警告 -->
                  <div class="panel-title cost-panel-title" @click="costCollapsed = !costCollapsed" style="cursor:pointer">
                    <div class="title-with-icon">
                      <b>预计成本影响</b>
                      <ChevronDown :size="14" :class="{ 'chevron-expanded': !costCollapsed }" style="transition:transform .15s ease;flex-shrink:0" />
                    </div>
                    <span class="panel-sub cost-collapsed-hint" v-if="costCollapsed">点击展开（演示数据）</span>
                  </div>
                  <div v-if="!costCollapsed" class="cost-content">
                    <div class="cost-strong-warning">
                      <AlertTriangle :size="14" />
                      <span>以下成本数据为演示测算结果，非正式财务确认数据，不得称为甲方确认。C03 成本区默认折叠。</span>
                    </div>
                    <div class="cost-formula">
                      <span class="formula-num">{{ fmt(costSummary.operatingSaving) }}</span>
                      <span class="formula-op">+</span>
                      <span class="formula-num">{{ fmt(costSummary.materialTransportDisposalSaving) }}</span>
                      <span class="formula-op">=</span>
                      <span class="formula-result">{{ fmt(costSummary.totalCostSaving ?? (Number(costSummary.operatingSaving || 0) + Number(costSummary.materialTransportDisposalSaving || 0))) }}</span>
                      <span class="formula-unit">{{ costSummary.currencyUnit || '万元' }}</span>
                    </div>
                    <p class="cost-desc">
                      低碳措施节约成本 = 预计运行费用节约 + 预计材料、运输及处置支出减少
                    </p>
                    <div class="cost-notice">
                      当前金额为项目测算值，不属于正式财务确认数据。
                    </div>
                  </div>
                </div>

                <div class="panel caliber-panel-small">
                  <div class="panel-title">
                    <b>减排量口径说明</b>
                  </div>
                  <div class="caliber-content-small">
                    <p class="caliber-text-small">
                      <b>相对基准核算减排量 {{ fmt(accountedReduction) }} tCO₂e：</b>
                      同口径基准排放 − 实际排放。
                    </p>
                    <p class="caliber-text-small">
                      <b>低碳措施预计减排量 {{ fmt(measureEstimatedReduction) }} tCO₂e：</b>
                      各项低碳措施的预估减排效果汇总。
                    </p>
                    <p class="caliber-notice-small">
                      两项指标的统计方法和用途不同，不作合计。
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </main>

        <footer class="carbon-footer">
          <span
            class="footer-source"
            :title="detail.dataSource || 'carbon_emission_activity / carbon_emission_factor / carbon_material_usage / carbon_reduction_accounting / carbon_reduction_measure'"
          >
            数据来源：MySQL 碳核算专题数据
          </span>
          <span class="footer-notice">
            {{ (detail as any).dataNotice || (detail as any).costNotice || '当前数据用于功能验证，不作为正式核算或财务确认依据。' }}
          </span>
          <button type="button" class="footer-close-btn" @click="emit('close')">关闭</button>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<style scoped lang="scss">
.carbon-overlay {
  position: fixed;
  inset: 0;
  z-index: 10020;
  display: grid;
  place-items: center;
  overflow: hidden;
  background: rgba(2, 10, 22, 0.78);
  backdrop-filter: blur(4px);
  font-family: "Microsoft YaHei", sans-serif;

  &.acceptance {
    animation: none;
  }
}

.carbon-modal {
  width: 1436px;
  height: 880px;
  box-sizing: border-box;
  display: grid;
  grid-template-rows: 58px 40px 1fr 52px;
  overflow: hidden;
  border: 1px solid rgba(105, 227, 111, 0.32);
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(7, 25, 45, 0.99), rgba(3, 15, 30, 0.99));
  box-shadow: 0 20px 70px rgba(0, 0, 0, 0.45);
  color: #e8f3ff;
  outline: none;
  transform: scale(var(--carbon-scale));
  transform-origin: center center;

  &.acceptance,
  &.acceptance * {
    animation: none !important;
    transition: none !important;
  }
}

/* Header */
.carbon-header {
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid rgba(105, 227, 111, 0.15);

  h2 {
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 0;
    font-size: 22px;
    font-weight: 600;

    b {
      color: #69e36f;
      font-size: 26px;
      font-weight: 700;
      letter-spacing: 1.5px;
    }

    span {
      font-weight: 600;
    }
  }

  .close-btn {
    display: grid;
    place-items: center;
    width: 36px;
    height: 36px;
    margin-left: 16px;
    border: 0;
    background: transparent;
    color: #9fb4ca;
    cursor: pointer;
    border-radius: 4px;

    &:hover {
      background: rgba(105, 227, 111, 0.08);
      color: #e8f3ff;
    }

    &:focus {
      outline: none;
    }

    &:focus-visible {
      outline: 1px solid rgba(105, 227, 111, 0.5);
      outline-offset: -2px;
    }
  }
}

.header-meta {
  margin-left: auto;
  color: #7892aa;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 0;

  i {
    display: inline-block;
    width: 8px;
    height: 8px;
    margin-right: 8px;
    border-radius: 50%;
    background: #69e36f;
    box-shadow: 0 0 8px #69e36f;
  }

  .meta-dot {
    margin: 0 8px;
  }
}

/* Tabs */
.carbon-tabs {
  display: flex;
  padding: 0 20px;
  border-bottom: 1px solid rgba(105, 227, 111, 0.12);
  background: rgba(1, 12, 26, 0.42);

  .tab-btn {
    position: relative;
    min-width: 132px;
    height: 100%;
    border: 0;
    background: transparent;
    color: #8fa9c8;
    font-size: 15px;
    cursor: pointer;
    padding: 0 16px;

    &:focus {
      outline: none;
    }

    &:focus-visible {
      outline: 1px solid rgba(105, 227, 111, 0.5);
      outline-offset: -2px;
      border-radius: 2px;
    }

    &.active {
      color: #eaffed;

      &:after {
        content: "";
        position: absolute;
        right: 26px;
        bottom: 0;
        left: 26px;
        height: 2px;
        background: #69e36f;
        box-shadow: 0 0 8px rgba(105, 227, 111, 0.7);
      }
    }
  }
}

/* Body */
.carbon-body {
  min-height: 0;
  padding: 10px;
  overflow: hidden;
}

.tab-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 0;
}

/* Summary cards */
.summary-grid {
  display: grid;
  gap: 12px;
  flex: 0 0 auto;

  &.summary-five {
    grid-template-columns: repeat(5, 1fr);
  }

  &.summary-four {
    grid-template-columns: repeat(4, 1fr);
  }
}

.summary-card {
  min-width: 0;
  padding: 10px 14px;
  box-sizing: border-box;
  border: 1px solid rgba(105, 227, 111, 0.13);
  background: linear-gradient(135deg, rgba(105, 227, 111, 0.07), rgba(47, 156, 255, 0.025));
  border-radius: 4px;

  .card-label {
    display: block;
    color: #8fa9c8;
    font-size: 13px;
    line-height: 1;
  }

  .card-value-row {
    margin-top: 6px;
    display: flex;
    align-items: baseline;
    gap: 8px;
  }

  .card-value {
    font-size: 24px;
    line-height: 1.1;
    font-weight: 700;
    font-family: "DIN Alternate", "Roboto Condensed", sans-serif;
  }

  .card-unit {
    color: #8fa9c8;
    font-size: 13px;
    font-style: normal;
  }

  &.card-green .card-value {
    color: #69e36f;
  }

  &.card-teal .card-value {
    color: #4dd0c4;
  }

  &.card-blue .card-value {
    color: #2f9cff;
  }
}

/* Panel */
.panel {
  min-height: 0;
  box-sizing: border-box;
  border: 1px solid rgba(105, 227, 111, 0.12);
  background: rgba(7, 28, 49, 0.62);
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.panel-title {
  height: 34px;
  min-height: 34px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
  padding: 0 12px;
  border-bottom: 1px solid rgba(105, 227, 111, 0.1);

  b {
    font-size: 15px;
    font-weight: 600;
  }

  .panel-sub {
    color: #6f8ba5;
    font-size: 13px;
  }

  .title-with-icon {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.info-icon-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;

  .info-icon {
    color: #8fa9c8;
    cursor: help;
  }

  &:hover .info-tooltip {
    opacity: 1;
    visibility: visible;
    transform: translateX(-50%) translateY(0);
  }
}

.info-tooltip {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%) translateY(4px);
  width: 280px;
  padding: 10px 12px;
  background: rgba(7, 25, 45, 0.98);
  border: 1px solid rgba(105, 227, 111, 0.3);
  border-radius: 4px;
  color: #d9e7f5;
  font-size: 13px;
  line-height: 1.6;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s ease;
  z-index: 10;
  pointer-events: none;
}

/* Table */
.table-wrap {
  min-height: 0;
  flex: 1;
  overflow: auto;

  &.table-wrap--paged {
    // 分页表格：一页 6 行，禁用垂直滚动，仅允许横向滚动
    overflow-x: auto;
    overflow-y: hidden;
    max-height: none;
    flex: none;
    height: auto;
  }

  &::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(105, 227, 111, 0.22);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    table-layout: fixed;
  }

  th {
    position: sticky;
    top: 0;
    z-index: 1;
    height: 32px;
    padding: 0 10px;
    background: #0c2943;
    color: #90a9c0;
    font-weight: 500;
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  td {
    height: 34px;
    padding: 0 10px;
    border-bottom: 1px solid rgba(143, 169, 200, 0.07);
    color: #c8d8e7;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  tr:hover td {
    background: rgba(105, 227, 111, 0.04);
  }

  .col-left {
    text-align: left;
  }

  .col-right {
    text-align: right;
    font-variant-numeric: tabular-nums;
  }

  .col-center {
    text-align: center;
  }

  .empty {
    text-align: center;
    color: #6f879d;
    font-size: 13px;
    padding: 16px 0;
  }
}

/* 分页栏 */
.pagination {
  flex: 0 0 auto;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  border-top: 1px solid rgba(105, 227, 111, 0.08);
  background: rgba(7, 28, 49, 0.42);
  color: #8fa9c8;
  font-size: 13px;

  .page-info {
    font-variant-numeric: tabular-nums;
  }

  .page-actions {
    display: flex;
    gap: 8px;
  }

  .page-btn {
    min-width: 64px;
    height: 26px;
    border: 1px solid rgba(105, 227, 111, 0.22);
    border-radius: 3px;
    background: transparent;
    color: #c8d8e7;
    font-size: 12px;
    cursor: pointer;

    &:hover:not(:disabled) {
      background: rgba(105, 227, 111, 0.08);
      color: #e8f3ff;
    }

    &:disabled {
      opacity: 0.4;
      cursor: not-allowed;
    }

    &:focus {
      outline: none;
    }

    &:focus-visible {
      outline: 1px solid rgba(105, 227, 111, 0.5);
      outline-offset: -2px;
    }

    &--num {
      min-width: 28px;
      width: 28px;

      &.active {
        background: rgba(105, 227, 111, 0.15);
        border-color: rgba(105, 227, 111, 0.4);
        color: #69e36f;
      }
    }
  }

  .page-dots {
    color: #5a7a9a;
    font-size: 12px;
    line-height: 26px;
  }
}

.positive {
  color: #69e36f !important;
}

/* Overview page — 左侧约76%，右侧约24% */
.overview-content {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  grid-template-rows: minmax(0, 1fr) auto;
  gap: 10px;
  min-height: 0;
  flex: 1;
}

.overview-left,
.overview-right {
  display: contents;
}

.trend-panel {
  grid-column: 1;
  grid-row: 1;
  min-height: 0;
}

.trend-chart {
  width: 100%;
  flex: 1;
  min-height: 180px;
}

.monthly-table-panel {
  grid-column: 1;
  grid-row: 2;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

/* Source panel */
.source-panel {
  grid-column: 2;
  grid-row: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.source-donut-wrap {
  position: relative;
  width: 100%;
  min-height: 120px;
  max-height: 150px;
  flex: 1 1 130px;
  padding: 6px 0;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.donut-chart {
  width: 100%;
  height: 100%;
}

.donut-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  pointer-events: none;

  .donut-value {
    font-size: 22px;
    font-weight: 700;
    color: #e8f3ff;
    font-family: "DIN Alternate", "Roboto Condensed", sans-serif;
    line-height: 1.1;
  }

  .donut-unit {
    font-size: 12px;
    color: #8fa9c8;
    margin-top: 2px;
  }
}

.source-list {
  padding: 10px 14px 14px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.source-item {
  display: grid;
  grid-template-columns: 8px 1fr auto auto;
  gap: 8px;
  align-items: center;
  height: 26px;
  font-size: 13px;

  .source-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }

  .source-name {
    color: #9fb4c8;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .source-value {
    color: #dce8f5;
    font-weight: 500;
    text-align: right;
    font-variant-numeric: tabular-nums;
    min-width: 72px;
  }

  .source-share {
    color: #6f8ba5;
    font-style: normal;
    text-align: right;
    font-variant-numeric: tabular-nums;
    min-width: 48px;
  }
}

/* Scope panel */
.scope-panel {
  grid-column: 2;
  grid-row: 2;
  display: flex;
  flex-direction: column;
}

.scope-content {
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.scope-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 26px;

  .scope-label {
    color: #7892aa;
    font-size: 12px;
  }

  .scope-value {
    color: #e8f3ff;
    font-size: 12px;
    font-weight: 600;
  }
}

/* Sources page */
.sources-page {
  .sources-top {
    flex: 0 0 35%;
    min-height: 0;
  }

  .sources-bottom {
    flex: 1;
    min-height: 0;
  }
}

.source-summary-table {
  tbody tr {
    cursor: pointer;
    position: relative;

    &.selected {
      background: rgba(105, 227, 111, 0.08);

      td {
        color: #e8f3ff;
      }
    }
  }

  .row-indicator {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: #69e36f;
  }
}

.segment-panel {
  flex: 1;
}

.segment-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 12px;
  flex: 1;
  min-height: 0;

  &.segment-content--full {
    // 全宽标段分解：表格占 1fr，图表占固定 280px
    grid-template-columns: minmax(0, 1fr) 280px;
    align-items: stretch;
  }
}

.segment-left,
.segment-left-wide,
.segment-full {
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;

  .table-wrap {
    flex: 1;
  }
}

.segment-right,
.segment-bar-wrap {
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.segment-bar-chart {
  width: 100%;
  height: 100%;
  min-height: 200px;
}

.matrix-table {
  td b {
    color: #69e36f;
  }
}

/* Benefit page */
.benefit-content {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 12px;
  min-height: 0;
  flex: 1;
}

.benefit-left {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

.benefit-right {
  min-height: 0;
}

.comparison-panel {
  flex: 1.1;
}

.comparison-chart {
  width: 100%;
  flex: 1;
  min-height: 220px;
}

.accounting-table-panel {
  flex: 0 0 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.caliber-panel {
  height: 100%;
}

.caliber-content {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.caliber-item {
  .caliber-text {
    margin: 0;
    color: #b8cce3;
    font-size: 13px;
    line-height: 1.7;

    b {
      color: #e8f3ff;
      font-weight: 600;
    }
  }
}

.caliber-notice {
  margin: 0;
  padding: 10px 12px;
  border-left: 2px solid #ffb347;
  color: #ffbd67;
  font-size: 13px;
  line-height: 1.6;
  background: rgba(255, 179, 71, 0.05);
}

/* Measures page */
.measures-content {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 12px;
  min-height: 0;
  flex: 1;
}

.measures-left {
  min-height: 0;
}

.measures-right {
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 12px;
  min-height: 0;
}

.measures-table-panel {
  flex: 0 0 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.measures-table {
  tbody tr {
    cursor: pointer;
    position: relative;

    &.selected {
      background: rgba(105, 227, 111, 0.08);

      td {
        color: #e8f3ff;
      }
    }

    td {
      height: 44px;
      padding-top: 4px;
      padding-bottom: 4px;
    }
  }

  .measure-scope {
    color: #9fb4c8;
    font-size: 13px;
    line-height: 1.4;
  }

  .row-indicator {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: #69e36f;
  }
}

.status-tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 10px;
  background: rgba(105, 227, 111, 0.12);
  color: #69e36f;
  font-size: 12px;
  font-weight: 500;
}

/* Cost panel */
.cost-panel {
  flex: 0 0 auto;
}

.cost-content {
  padding: 16px 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cost-formula {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 6px;
  flex-wrap: wrap;

  .formula-num {
    font-size: 20px;
    color: #e7f3ff;
    font-weight: 600;
    font-family: "DIN Alternate", "Roboto Condensed", sans-serif;
  }

  .formula-op {
    color: #7892aa;
    font-size: 16px;
  }

  .formula-result {
    font-size: 22px;
    color: #69e36f;
    font-weight: 700;
    font-family: "DIN Alternate", "Roboto Condensed", sans-serif;
  }

  .formula-unit {
    color: #7892aa;
    font-size: 13px;
    margin-left: 2px;
  }
}

.cost-desc {
  margin: 0;
  color: #8fa9c8;
  font-size: 13px;
  line-height: 1.6;
  text-align: center;
}

.cost-notice {
  padding: 10px 12px;
  border: 1px solid rgba(255, 179, 71, 0.24);
  background: rgba(255, 179, 71, 0.06);
  color: #ffbd67;
  font-size: 13px;
  text-align: center;
  line-height: 1.5;
  border-radius: 4px;
}

.caliber-panel-small {
  min-height: 0;
}

.caliber-content-small {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;

  .caliber-text-small {
    margin: 0;
    color: #b8cce3;
    font-size: 12px;
    line-height: 1.6;

    b {
      color: #e8f3ff;
      font-weight: 600;
    }
  }

  .caliber-notice-small {
    margin: 0;
    padding: 8px 10px;
    border-left: 2px solid #ffb347;
    color: #ffbd67;
    font-size: 12px;
    line-height: 1.5;
    background: rgba(255, 179, 71, 0.05);
  }
}

/* P3.2: Scope badges in header */
.header-scope-badges {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: 12px;
  flex-shrink: 0;
}

.scope-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}

.scope-demo {
  border: 1px solid rgba(255, 179, 71, 0.3);
  background: rgba(255, 179, 71, 0.08);
  color: #ffbd67;
}

.scope-consistent {
  border: 1px solid rgba(105, 227, 111, 0.25);
  background: rgba(105, 227, 111, 0.08);
  color: #69e36f;
}

.scope-consistent.scope-mismatch {
  border: 1px solid rgba(255, 107, 107, 0.3);
  background: rgba(255, 107, 107, 0.08);
  color: #ff8a8a;
}

.scope-boundary {
  border: 1px solid rgba(47, 156, 255, 0.25);
  background: rgba(47, 156, 255, 0.06);
  color: #2f9cff;
  font-family: "DIN Alternate", "Roboto Condensed", sans-serif;
}

/* P3.2: Segment analysis note */
.segment-analysis-note {
  color: #ffbd67 !important;
  font-size: 11px !important;
}

/* P3.2: Topic demo notice */
.topic-demo-notice {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid rgba(255, 179, 71, 0.24);
  border-radius: 4px;
  background: rgba(255, 179, 71, 0.06);
  color: #ffbd67;
  font-size: 12px;
  line-height: 1.5;
  flex: 0 0 auto;
}

/* P3.2: C03 cost collapse */
.cost-panel-title {
  cursor: pointer;
  transition: background 0.15s;

  &:hover {
    background: rgba(105, 227, 111, 0.04);
  }
}

.chevron-expanded {
  transform: rotate(180deg);
}

.cost-collapsed-hint {
  color: #ffbd67 !important;
  font-size: 11px !important;
}

.cost-strong-warning {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border: 1px solid rgba(255, 107, 107, 0.24);
  border-radius: 4px;
  background: rgba(255, 107, 107, 0.06);
  color: #ff8a8a;
  font-size: 12px;
  line-height: 1.5;
  margin-bottom: 4px;
}

/* Footer */
.carbon-footer {
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-top: 1px solid rgba(105, 227, 111, 0.12);
  color: #6f879d;
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  gap: 16px;

  .footer-source {
    overflow: hidden;
    text-overflow: ellipsis;
    cursor: help;
    flex-shrink: 1;
  }

  .footer-notice {
    flex: 1;
    text-align: center;
    color: #ffb347;
  }

  .footer-close-btn {
    width: 96px;
    height: 32px;
    border: 1px solid rgba(105, 227, 111, 0.35);
    border-radius: 4px;
    background: rgba(105, 227, 111, 0.08);
    color: #e8f3ff;
    font-size: 14px;
    cursor: pointer;
    flex-shrink: 0;

    &:hover {
      background: rgba(105, 227, 111, 0.15);
    }

    &:focus {
      outline: none;
    }

    &:focus-visible {
      outline: 1px solid rgba(105, 227, 111, 0.5);
      outline-offset: -2px;
    }
  }
}
</style>
