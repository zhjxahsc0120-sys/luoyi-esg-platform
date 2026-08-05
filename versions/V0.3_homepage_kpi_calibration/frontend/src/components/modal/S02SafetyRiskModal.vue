<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { Check, Clock, FileCheck, ShieldAlert, X } from 'lucide-vue-next'
import { getDashboardKpiDetail } from '@/services/api'

// S 组业务主色：蓝色（与 E 组绿色、G 组紫色区分）
const THEME_COLOR = '#2f9cff'

// 语义状态色（不跟随 S 组主色）
const STATUS_COLORS = {
  normal: '#69e36f',     // 正常、已完成、已闭环：绿色
  processing: '#2f9cff', // 处理中、办理中：蓝色
  pending: '#ffb347',    // 待处理、临期、提醒：橙色
  danger: '#ff4f5e',     // 逾期、异常、高风险：红色
  muted: '#8ba6c3',     // 次要文字、暂无数据：灰色
} as const

type RiskLevel = '重大' | '较大'

interface RiskPointRow {
  rowId: string         // 稳定 ID（数据加载时按原始顺序生成，不随排序/筛选变化）
  name: string
  level: RiskLevel
  location: string
  type: string
  time: string
  status: string
}

interface S02Data {
  summary: { biggerCount: number; majorCount: number; newThisMonth: number; closedThisMonth: number; relatedPoints: number }
  detailData: RiskPointRow[]
  dataSource: string
  updateTime: string
}

const emit = defineEmits<{ (e: 'close'): void }>()

const isAcceptanceMode = new URLSearchParams(window.location.search).get('acceptance') === '1'
const modalRef = ref<HTMLDivElement | null>(null)
const chartRef = ref<HTMLDivElement | null>(null)
const scale = ref(1)
let chart: echarts.ECharts | null = null

const data = ref<S02Data>({
  summary: { biggerCount: 4, majorCount: 2, newThisMonth: 1, closedThisMonth: 2, relatedPoints: 4 },
  detailData: [],
  dataSource: '安全风险分级管控系统',
  updateTime: '2026-07-13 11:00',
})

// 选中行（稳定 ID 联动右侧"重点管控提醒"）
const selectedRowId = ref<string | null>(null)

// 风险点原始数组（保留原始顺序，用于生成稳定 ID）
const rawRows = ref<RiskPointRow[]>([])

// 排序：重大优先，同等级按管控起始日期升序
const sortedRows = computed<RiskPointRow[]>(() => {
  const levelWeight: Record<RiskLevel, number> = { '重大': 0, '较大': 1 }
  return [...rawRows.value].sort((a, b) => {
    const w = levelWeight[a.level] - levelWeight[b.level]
    if (w !== 0) return w
    return a.time.localeCompare(b.time)
  })
})

// 风险等级构成
const levelComposition = computed(() => {
  const major = rawRows.value.filter(r => r.level === '重大').length
  const bigger = rawRows.value.filter(r => r.level === '较大').length
  const total = major + bigger
  return { major, bigger, total }
})

// 风险类型分布（按数量降序，同数量按名称）
const typeDistribution = computed(() => {
  const map = new Map<string, { major: number; bigger: number; total: number }>()
  rawRows.value.forEach(row => {
    const entry = map.get(row.type) || { major: 0, bigger: 0, total: 0 }
    if (row.level === '重大') entry.major += 1
    else entry.bigger += 1
    entry.total += 1
    map.set(row.type, entry)
  })
  return Array.from(map, ([name, value]) => ({ name, ...value }))
    .sort((a, b) => b.total - a.total || a.name.localeCompare(b.name, 'zh-CN'))
})

// 顶部摘要卡（与 dashboard_payload.json 的 summary 字段对齐）
const summaryCards = computed(() => [
  { label: '较大风险点', value: String(data.value.summary.biggerCount), unit: '项', color: STATUS_COLORS.pending },
  { label: '重大风险点', value: String(data.value.summary.majorCount), unit: '项', color: STATUS_COLORS.danger },
  { label: '本月新增', value: String(data.value.summary.newThisMonth), unit: '项', color: STATUS_COLORS.processing },
  { label: '本月销号', value: String(data.value.summary.closedThisMonth), unit: '项', color: STATUS_COLORS.normal },
  { label: '涉及工点', value: String(data.value.summary.relatedPoints), unit: '个', color: THEME_COLOR },
])

// 当前在管合计口径：较大 + 重大（与首页 S02 卡片值一致）
const totalManaged = computed(() => levelComposition.value.total)

// 风险等级构成比例
const majorRatio = computed(() => totalManaged.value === 0 ? 0 : Math.round((levelComposition.value.major / totalManaged.value) * 100))
const biggerRatio = computed(() => totalManaged.value === 0 ? 0 : 100 - majorRatio.value)

// 重点管控提醒：从真实清单聚合
const controlReminders = computed(() => {
  const majorCount = levelComposition.value.major
  const items: { label: string; value: string; level: 'danger' | 'muted' }[] = []
  // 重大风险点数量可由清单证明
  items.push({
    label: '重大风险点',
    value: `${majorCount} 项`,
    level: majorCount > 0 ? 'danger' : 'muted',
  })
  // 临近作业风险：清单无对应真实字段
  items.push({ label: '临近作业风险', value: '暂无可判定提醒', level: 'muted' })
  // 长期未复核：清单无对应真实日期
  items.push({ label: '长期未复核', value: '暂无可判定提醒', level: 'muted' })
  return items
})

const levelClass = (level: RiskLevel) => level === '重大' ? 'major' : 'bigger'

function initChart() {
  if (!chartRef.value) return
  chart?.dispose()
  chart = echarts.init(chartRef.value)
  const dist = typeDistribution.value
  const yAxisData = [...dist].reverse().map(d => d.name)
  const majorSeries = [...dist].reverse().map(d => d.major)
  const biggerSeries = [...dist].reverse().map(d => d.bigger)

  // 横轴最大值：max<=2 时固定为 2；max>2 时按实际值的 115% 扩展
  const maxVal = dist.reduce((m, d) => Math.max(m, d.total), 0)
  const xAxisMax = maxVal <= 2 ? 2 : Math.ceil(maxVal * 1.15)

  chart.setOption({
    animation: !isAcceptanceMode,
    animationDuration: 450,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(5,18,38,0.92)',
      borderColor: 'rgba(47,156,255,0.3)',
      textStyle: { color: '#e8f3ff', fontSize: 13 },
      formatter: (params: any[]) => {
        const name = params[0]?.axisValue ?? ''
        let major = 0, bigger = 0
        params.forEach(p => {
          if (p.seriesName === '重大风险') major = p.value
          else if (p.seriesName === '较大风险') bigger = p.value
        })
        return `${name}<br/>重大风险：${major} 项<br/>较大风险：${bigger} 项<br/>合计：${major + bigger} 项`
      },
    },
    legend: {
      data: ['重大风险', '较大风险'],
      right: 10,
      top: 0,
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: '#b8cce3', fontSize: 13 },
    },
    grid: { left: 80, right: 50, top: 32, bottom: 24 },
    xAxis: {
      type: 'value',
      max: xAxisMax,
      minInterval: 1,
      axisLine: { show: false },
      axisLabel: { color: '#8fa9c8', fontSize: 13, formatter: (v: number) => Number.isInteger(v) ? v : '' },
      splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
    },
    yAxis: {
      type: 'category',
      data: yAxisData,
      axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
      axisTick: { show: false },
      axisLabel: { color: '#b8cce3', fontSize: 13 },
    },
    series: [
      {
        name: '重大风险',
        type: 'bar',
        stack: 'total',
        data: majorSeries,
        barWidth: 14,
        itemStyle: {
          color: STATUS_COLORS.danger,
          borderRadius: [3, 0, 0, 3],
        },
        label: {
          show: true,
          position: 'insideRight',
          color: '#fff',
          fontSize: 12,
          fontWeight: 600,
          formatter: (p: any) => p.value > 0 ? `${p.value}项` : '',
        },
      },
      {
        name: '较大风险',
        type: 'bar',
        stack: 'total',
        data: biggerSeries,
        barWidth: 14,
        itemStyle: {
          color: STATUS_COLORS.pending,
          borderRadius: [0, 3, 3, 0],
        },
        label: {
          show: true,
          position: 'insideRight',
          color: '#fff',
          fontSize: 12,
          fontWeight: 600,
          formatter: (p: any) => p.value > 0 ? `${p.value}项` : '',
        },
      },
    ],
  })
}

function updateScale() {
  scale.value = Math.min(1, window.innerWidth / 1920, window.innerHeight / 1080)
}

function handleResize() { updateScale(); chart?.resize() }
function handleKeydown(event: KeyboardEvent) { if (event.key === 'Escape') emit('close') }
function handleOverlayClick(event: MouseEvent) { if (event.target === event.currentTarget) emit('close') }

function toggleRow(row: RiskPointRow) {
  if (selectedRowId.value === row.rowId) {
    selectedRowId.value = null
  } else {
    selectedRowId.value = row.rowId
  }
}

// 数据来源：dashboard_payload.json 中 kpiDetails.S02
// 由于该接口只提供当前清单、无历史月度快照，主图采用"当前在管风险点分布"横向堆叠条形图
async function loadData() {
  const resp = await getDashboardKpiDetail('S02')
  if (!resp) return
  const summary = resp.summary || []
  const biggerCount = Number(summary.find(s => s.label === '较大风险点')?.value ?? 0)
  const majorCount = Number(summary.find(s => s.label === '重大风险点')?.value ?? 0)
  const newThisMonth = Number(summary.find(s => s.label === '本月新增')?.value ?? 0)
  const closedThisMonth = Number(summary.find(s => s.label === '本月销号')?.value ?? 0)
  const relatedPoints = Number(summary.find(s => s.label === '涉及工点')?.value ?? 0)

  // 按原始数组顺序生成稳定 ID（不使用名称、不使用排序后的下标）
  const rows: RiskPointRow[] = ((resp.detailData as any[]) || []).map((row, index) => ({
    rowId: `S02-RP-${String(index + 1).padStart(2, '0')}`,
    name: String(row.name ?? ''),
    level: (row.level === '重大' ? '重大' : '较大') as RiskLevel,
    location: String(row.location ?? ''),
    type: String(row.type ?? ''),
    time: String(row.time ?? ''),
    status: String(row.status ?? ''),
  }))

  data.value = {
    summary: { biggerCount, majorCount, newThisMonth, closedThisMonth, relatedPoints },
    detailData: rows,
    dataSource: resp.dataSource || '安全风险分级管控系统',
    updateTime: resp.updateTime || '—',
  }
  rawRows.value = rows
}

watch(() => typeDistribution.value, () => nextTick(initChart), { deep: true, immediate: false })

onMounted(() => {
  updateScale()
  nextTick(() => { initChart(); modalRef.value?.focus() })
  window.addEventListener('resize', handleResize)
  window.addEventListener('keydown', handleKeydown)
  loadData().then(() => nextTick(initChart))
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleKeydown)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div class="s02-overlay" :class="{ acceptance: isAcceptanceMode }" @click="handleOverlayClick">
    <div
      ref="modalRef"
      class="s02-modal"
      :class="{ acceptance: isAcceptanceMode }"
      :style="{ '--s02-scale': scale }"
      role="dialog"
      aria-modal="true"
      aria-labelledby="s02-modal-title"
      tabindex="-1"
    >
      <header class="s02-header">
        <h2 id="s02-modal-title">
          <span class="title-key">S02</span>
          <span class="title-name">重大风险源管控</span>
        </h2>
        <button type="button" aria-label="关闭" @click="emit('close')">
          <X :size="22" />
        </button>
      </header>

      <section class="s02-summary" aria-label="S02摘要">
        <div v-for="item in summaryCards" :key="item.label" class="summary-card">
          <span class="summary-label">{{ item.label }}</span>
          <div class="summary-value-row">
            <strong :style="{ color: item.color }">{{ item.value }}</strong>
            <small v-if="item.unit">{{ item.unit }}</small>
          </div>
        </div>
      </section>

      <main class="s02-content">
        <div class="s02-main">
          <section class="panel chart-panel">
            <div class="panel-heading">
              <h3>当前在管风险点分布</h3>
              <span>按风险类型堆叠（重大 / 较大）</span>
            </div>
            <div ref="chartRef" class="s02-chart" />
          </section>

          <section class="panel table-panel">
            <div class="panel-heading">
              <h3>安全风险点明细</h3>
              <span>默认重大优先，按管控起始日期排序</span>
            </div>
            <div class="table-wrap">
              <table class="risk-table">
                <thead>
                  <colgroup>
                    <col style="width: 25%" />
                    <col style="width: 10%" />
                    <col style="width: 21%" />
                    <col style="width: 11%" />
                    <col style="width: 13%" />
                    <col style="width: 10%" />
                    <col style="width: 10%" />
                  </colgroup>
                  <tr>
                    <th class="col-left">风险点名称</th>
                    <th class="col-center">风险等级</th>
                    <th class="col-left">所在工点</th>
                    <th class="col-center">风险类型</th>
                    <th class="col-center">管控起始日期</th>
                    <th class="col-center">当前状态</th>
                    <th class="col-center">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="sortedRows.length === 0">
                    <td colspan="7" class="empty-row">暂无在管风险点数据</td>
                  </tr>
                  <tr
                    v-for="row in sortedRows"
                    :key="row.rowId"
                    :class="{ 'row-selected': selectedRowId === row.rowId }"
                    @click="toggleRow(row)"
                  >
                    <td :title="row.name" class="cell-name col-left">{{ row.name }}</td>
                    <td class="col-center">
                      <span class="level-tag" :class="levelClass(row.level)">{{ row.level }}</span>
                    </td>
                    <td :title="row.location" class="col-left">{{ row.location }}</td>
                    <td class="col-center">{{ row.type }}</td>
                    <td class="col-center">{{ row.time }}</td>
                    <td class="col-center">
                      <span class="status-tag" :class="row.status === '持续管控' ? 'processing' : 'pending'">{{ row.status }}</span>
                    </td>
                    <td class="col-center">
                      <button type="button" class="row-action" @click.stop="toggleRow(row)">
                        {{ selectedRowId === row.rowId ? '取消关注' : '关注' }}
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>

        <aside class="s02-side">
          <section class="panel level-panel">
            <h3>风险等级构成</h3>
            <div class="level-summary">
              <div class="level-row">
                <span class="level-label"><i class="dot major"></i>重大风险点</span>
                <strong class="level-value" :style="{ color: STATUS_COLORS.danger }">{{ levelComposition.major }}</strong>
                <span class="level-unit">项</span>
                <span class="level-ratio">{{ majorRatio }}%</span>
              </div>
              <div class="level-row">
                <span class="level-label"><i class="dot bigger"></i>较大风险点</span>
                <strong class="level-value" :style="{ color: STATUS_COLORS.pending }">{{ levelComposition.bigger }}</strong>
                <span class="level-unit">项</span>
                <span class="level-ratio">{{ biggerRatio }}%</span>
              </div>
              <div class="level-bar">
                <div class="level-bar-major" :style="{ width: `${majorRatio}%` }" />
                <div class="level-bar-bigger" :style="{ width: `${biggerRatio}%` }" />
              </div>
              <div class="level-total">
                <span>当前在管合计</span>
                <strong :style="{ color: THEME_COLOR }">{{ totalManaged }}</strong>
                <small>项</small>
              </div>
            </div>
          </section>

          <section class="panel type-panel">
            <h3>风险类型分布</h3>
            <div class="type-list">
              <div v-for="t in typeDistribution" :key="t.name" class="type-row">
                <span class="type-label">{{ t.name }}</span>
                <div class="type-bar-track">
                  <div class="type-bar-major" :style="{ width: `${(t.major / Math.max(1, totalManaged)) * 100}%` }" />
                  <div class="type-bar-bigger" :style="{ width: `${(t.bigger / Math.max(1, totalManaged)) * 100}%` }" />
                </div>
                <span class="type-value">{{ t.total }}</span>
              </div>
              <div v-if="typeDistribution.length === 0" class="type-empty">暂无可统计的风险类型</div>
            </div>
          </section>

          <section class="panel reminder-panel">
            <h3>重点管控提醒</h3>
            <div class="reminder-list">
              <div
                v-for="r in controlReminders"
                :key="r.label"
                class="reminder-row"
                :class="r.level"
              >
                <span class="reminder-label">{{ r.label }}</span>
                <span class="reminder-value">{{ r.value }}</span>
              </div>
            </div>
          </section>
        </aside>
      </main>

      <footer class="s02-footer">
        <div class="footer-info" :title="data.dataSource">
          <FileCheck :size="14" />
          <span>数据来源：{{ data.dataSource }}</span>
        </div>
        <div class="footer-info">
          <Clock :size="14" />
          <span>更新时间：{{ data.updateTime }}</span>
        </div>
        <div class="footer-info ok">
          <Check :size="14" />
          <span>核验状态：在管合计 = 较大 + 重大 = {{ totalManaged }} 项</span>
        </div>
        <button type="button" class="primary-btn" @click="emit('close')">
          <ShieldAlert :size="14" />
          <span>发起督办</span>
        </button>
        <button type="button" @click="emit('close')">关闭</button>
      </footer>
    </div>
  </div>
</template>

<style scoped lang="scss">
.s02-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: rgba(2, 11, 24, 0.76);
  backdrop-filter: blur(4px);
  animation: s02Fade 0.2s ease;

  &.acceptance { animation: none; }
}

.s02-modal {
  width: 1436px;
  height: 880px;
  flex: 0 0 1436px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(47, 156, 255, 0.35);
  border-radius: 8px;
  outline: none;
  background: linear-gradient(180deg, #07182b, #04101f);
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.64);
  color: #e8f3ff;
  transform: scale(var(--s02-scale));
  transform-origin: center;
  animation: s02Rise 0.25s ease;

  &.acceptance,
  &.acceptance * {
    animation: none !important;
    transition: none !important;
  }

  &:focus,
  &:focus-visible { outline: none; }
}

.s02-header {
  height: 60px;
  flex: 0 0 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
  padding: 0 16px;
  border-bottom: 1px solid rgba(47, 156, 255, 0.16);

  h2 {
    margin: 0;
    display: flex;
    align-items: baseline;
    gap: 12px;
    font-size: 22px;
    font-weight: 600;
    color: #e8f3ff;

    .title-key {
      color: #2f9cff;
      font-family: "DIN Alternate", "Roboto Condensed", sans-serif;
      font-size: 26px;
      font-weight: 700;
      text-shadow: 0 0 8px rgba(47, 156, 255, 0.4);
    }
  }

  button {
    width: 36px;
    height: 36px;
    display: grid;
    place-items: center;
    border: 0;
    border-radius: 4px;
    background: transparent;
    color: #8fa9c8;
    cursor: pointer;

    &:hover,
    &:focus-visible {
      background: rgba(47, 156, 255, 0.08);
      color: #e8f3ff;
      outline: 1px solid rgba(47, 156, 255, 0.28);
    }
  }
}

.s02-summary {
  flex: 0 0 88px;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  box-sizing: border-box;
  padding: 12px 16px 0;

  .summary-card {
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-sizing: border-box;
    padding: 8px 14px;
    border: 1px solid rgba(47, 156, 255, 0.15);
    border-radius: 5px;
    background: rgba(47, 156, 255, 0.035);

    .summary-label {
      color: #b8cce3;
      font-size: 14px;
      line-height: 20px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .summary-value-row {
      min-width: 0;
      display: flex;
      align-items: baseline;
      gap: 5px;
      white-space: nowrap;

      strong {
        min-width: 0;
        font-family: "DIN Alternate", "Roboto Condensed", sans-serif;
        font-size: 28px;
        line-height: 34px;
        font-weight: 700;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      small {
        color: #8fa9c8;
        font-size: 13px;
      }
    }
  }
}

.s02-content {
  min-height: 0;
  flex: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 12px;
  box-sizing: border-box;
  padding: 12px 16px;
}

.s02-main,
.s02-side {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.panel {
  min-width: 0;
  min-height: 0;
  box-sizing: border-box;
  border: 1px solid rgba(47, 156, 255, 0.15);
  border-radius: 6px;
  background: rgba(4, 22, 40, 0.72);

  h3 {
    margin: 0;
    color: #e8f3ff;
    font-size: 15px;
    line-height: 22px;
    font-weight: 600;
  }
}

.panel-heading {
  height: 38px;
  flex: 0 0 38px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  box-sizing: border-box;
  border-bottom: 1px solid rgba(143, 169, 200, 0.1);

  span {
    color: #8fa9c8;
    font-size: 12px;
  }
}

.chart-panel {
  flex: 0 0 320px;
  display: flex;
  flex-direction: column;
}

.s02-chart {
  flex: 1;
  width: 100%;
  min-height: 0;
}

.table-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.table-wrap {
  min-height: 0;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  scrollbar-color: rgba(143, 169, 200, 0.48) rgba(143, 169, 200, 0.08);

  &::-webkit-scrollbar { width: 6px; }
  &::-webkit-scrollbar-track { background: rgba(143, 169, 200, 0.06); }
  &::-webkit-scrollbar-thumb {
    background: rgba(143, 169, 200, 0.4);
    border-radius: 3px;

    &:hover { background: rgba(143, 169, 200, 0.6); }
  }
}

.risk-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 14px;

  th {
    height: 36px;
    padding: 0 10px;
    border-bottom: 1px solid rgba(143, 169, 200, 0.15);
    background: #071b31;
    color: #b8cce3;
    font-size: 14px;
    font-weight: 600;
    vertical-align: middle;
    position: sticky;
    top: 0;
    z-index: 1;

    &.col-left { text-align: left; }
    &.col-center { text-align: center; }
  }

  td {
    height: 38px;
    padding: 0 10px;
    border-bottom: 1px solid rgba(143, 169, 200, 0.08);
    color: #d9e7f5;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    vertical-align: middle;

    &.col-left { text-align: left; }
    &.col-center { text-align: center; }
  }

  tbody tr {
    cursor: pointer;

    &:hover {
      background: rgba(47, 156, 255, 0.05);
    }

    &.row-selected {
      background: rgba(47, 156, 255, 0.1);
      box-shadow: inset 2px 0 0 #2f9cff;
    }
  }

  .cell-name {
    color: #e8f3ff;
    font-weight: 500;
  }

  .empty-row {
    text-align: center;
    color: #8ba6c3;
    height: 60px;
  }
}

.row-action {
  width: 72px;
  height: 26px;
  padding: 0;
  border: 1px solid rgba(47, 156, 255, 0.3);
  border-radius: 3px;
  background: rgba(47, 156, 255, 0.06);
  color: #b8cce3;
  font-size: 12px;
  line-height: 24px;
  cursor: pointer;

  &:hover {
    background: rgba(47, 156, 255, 0.15);
    color: #e8f3ff;
  }
}

.level-tag,
.status-tag {
  display: inline-flex;
  width: 60px;
  height: 22px;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  border: 1px solid;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.03);
  text-align: center;
}

.level-tag {
  &.major {
    color: #ff4f5e;
    border-color: rgba(255, 79, 94, 0.45);
    background: rgba(255, 79, 94, 0.1);
  }
  &.bigger {
    color: #ffb347;
    border-color: rgba(255, 179, 71, 0.45);
    background: rgba(255, 179, 71, 0.1);
  }
}

.status-tag {
  &.processing {
    color: #2f9cff;
    border-color: rgba(47, 156, 255, 0.4);
    background: rgba(47, 156, 255, 0.08);
  }
  &.pending {
    color: #ffb347;
    border-color: rgba(255, 179, 71, 0.4);
    background: rgba(255, 179, 71, 0.08);
  }
}

// 右侧栏
.s02-side .panel { padding: 10px 12px; }

.level-panel { flex: 0 0 200px; }

.level-summary {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.level-row {
  display: grid;
  grid-template-columns: 1fr auto auto 38px;
  align-items: center;
  gap: 6px;
  font-size: 13px;

  .level-label {
    display: flex;
    align-items: center;
    gap: 6px;
    color: #b8cce3;

    .dot {
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 2px;

      &.major { background: #ff4f5e; }
      &.bigger { background: #ffb347; }
    }
  }

  .level-value {
    font-family: "DIN Alternate", "Roboto Condensed", sans-serif;
    font-size: 18px;
    font-weight: 700;
  }

  .level-unit {
    color: #8fa9c8;
    font-size: 12px;
  }

  .level-ratio {
    text-align: right;
    color: #8ba6c3;
    font-size: 12px;
    font-variant-numeric: tabular-nums;
  }
}

.level-bar {
  height: 10px;
  display: flex;
  border-radius: 3px;
  overflow: hidden;
  background: rgba(143, 169, 200, 0.08);

  .level-bar-major {
    background: #ff4f5e;
    transition: width 0.4s;
  }
  .level-bar-bigger {
    background: #ffb347;
    transition: width 0.4s;
  }
}

.level-total {
  display: flex;
  align-items: baseline;
  gap: 6px;
  padding-top: 6px;
  border-top: 1px solid rgba(143, 169, 200, 0.1);
  font-size: 13px;

  span { color: #8fa9c8; }

  strong {
    font-family: "DIN Alternate", "Roboto Condensed", sans-serif;
    font-size: 20px;
    font-weight: 700;
  }

  small {
    color: #8fa9c8;
    font-size: 12px;
  }
}

.type-panel { flex: 1; min-height: 0; display: flex; flex-direction: column; }

.type-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
  min-height: 0;
  flex: 1;
}

.type-row {
  display: grid;
  grid-template-columns: 76px 1fr 24px;
  align-items: center;
  gap: 8px;
  font-size: 13px;

  .type-label {
    color: #b8cce3;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .type-value {
    text-align: right;
    color: #e8f3ff;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }
}

.type-bar-track {
  height: 8px;
  display: flex;
  border-radius: 2px;
  overflow: hidden;
  background: rgba(143, 169, 200, 0.08);

  .type-bar-major { background: #ff4f5e; }
  .type-bar-bigger { background: #ffb347; }
}

.type-empty {
  color: #6d86a3;
  font-size: 12px;
  text-align: center;
  padding: 12px 0;
}

.reminder-panel { flex: 1; min-height: 0; display: flex; flex-direction: column; }

.reminder-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  min-height: 0;
}

.reminder-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 8px;
  border-radius: 3px;
  font-size: 13px;

  &.danger {
    background: rgba(255, 79, 94, 0.08);
    border: 1px solid rgba(255, 79, 94, 0.25);

    .reminder-label { color: #ffb3ba; }
    .reminder-value { color: #ff4f5e; font-weight: 600; }
  }

  &.muted {
    background: rgba(143, 169, 200, 0.04);
    border: 1px solid rgba(143, 169, 200, 0.1);

    .reminder-label { color: #8fa9c8; }
    .reminder-value { color: #6d86a3; }
  }
}

.s02-footer {
  height: 52px;
  flex: 0 0 52px;
  display: flex;
  align-items: center;
  gap: 18px;
  box-sizing: border-box;
  padding: 0 16px;
  border-top: 1px solid rgba(47, 156, 255, 0.12);

  .footer-info {
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 6px;
    color: #8fa9c8;
    font-size: 12px;
    white-space: nowrap;

    &:first-child {
      max-width: 320px;
      overflow: hidden;

      span {
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }

    &.ok { color: #69e36f; }
  }

  button {
    height: 34px;
    padding: 0 16px;
    border: 1px solid rgba(47, 156, 255, 0.35);
    border-radius: 4px;
    background: rgba(47, 156, 255, 0.08);
    color: #e8f3ff;
    font-size: 14px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;

    &:hover,
    &:focus-visible {
      background: rgba(47, 156, 255, 0.15);
      outline: none;
    }

    &.primary-btn {
      margin-left: auto;
      background: rgba(47, 156, 255, 0.2);
      border-color: rgba(47, 156, 255, 0.5);
    }
  }
}

@keyframes s02Fade {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes s02Rise {
  from {
    opacity: 0;
    transform: translateY(12px) scale(var(--s02-scale));
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(var(--s02-scale));
  }
}
</style>
