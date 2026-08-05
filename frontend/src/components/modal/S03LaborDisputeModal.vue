<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { Clock, FileCheck, X, AlertCircle } from 'lucide-vue-next'
import { getDashboardKpiDetail } from '@/services/api'

const THEME_COLOR = '#2f9cff'
const THEME_RGB = '47, 156, 255'

const STATUS_COLORS = {
  normal: '#69e36f',
  processing: '#2f9cff',
  pending: '#ffb347',
  danger: '#ff4f5e',
  muted: '#8ba6c3',
} as const

interface LaborDisputeRow {
  rowId: string
  name: string
  type: string
  segment: string
  status: string
  deadlineStatus: string
  department: string
  deadline: string
  amount: string
  people: string
  time: string
}

interface S03Data {
  summary: {
    pendingTotal: number
    newThisMonth: number
    closedThisMonth: number
    peopleCount: number
    amount: number
  }
  detailData: LaborDisputeRow[]
  dataSource: string
  updateTime: string
}

const emit = defineEmits<{ (e: 'close'): void }>()

const isAcceptanceMode = new URLSearchParams(window.location.search).get('acceptance') === '1'
const modalRef = ref<HTMLDivElement | null>(null)
const chartRef = ref<HTMLDivElement | null>(null)
const scale = ref(1)
let chart: echarts.ECharts | null = null

const data = ref<S03Data>({
  summary: { pendingTotal: 2, newThisMonth: 1, closedThisMonth: 1, peopleCount: 11, amount: 35 },
  detailData: [],
  dataSource: '劳务用工纠纷台账（农民工工资）',
  updateTime: '2026-07-13 10:00',
})

const selectedRowId = ref<string | null>(null)
const rawRows = ref<LaborDisputeRow[]>([])

const selectedRow = computed<LaborDisputeRow | null>(() => {
  if (!selectedRowId.value) return null
  return sortedRows.value.find(r => r.rowId === selectedRowId.value) || null
})

const sortedRows = computed<LaborDisputeRow[]>(() => {
  return [...rawRows.value]
})

const summaryCards = computed(() => [
  { label: '当前未办结', value: data.value.summary.pendingTotal, unit: '项', color: THEME_COLOR },
  { label: '本月新增', value: data.value.summary.newThisMonth, unit: '项', color: '#ffb347' },
  { label: '本月办结', value: data.value.summary.closedThisMonth, unit: '项', color: '#69e36f' },
  { label: '涉及人数', value: data.value.summary.peopleCount, unit: '人', color: THEME_COLOR },
  { label: '涉及金额', value: data.value.summary.amount, unit: '万元', color: '#a66cff' },
])

const statusDistribution = computed(() => {
  const map = new Map<string, number>()
  rawRows.value.forEach(r => {
    const label = mapS03StatusLabel(r.status)
    map.set(label, (map.get(label) || 0) + 1)
  })
  return Array.from(map.entries())
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
})

const typeDistribution = computed(() => {
  const map = new Map<string, number>()
  rawRows.value.forEach(r => {
    if (r.type) map.set(r.type, (map.get(r.type) || 0) + 1)
  })
  return Array.from(map.entries())
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
})

const hasTypeData = computed(() => typeDistribution.value.length > 0)

const concernItems = computed(() => {
  const items: { label: string; value: string; icon: string }[] = []
  const overdue = rawRows.value.filter(r => r.deadlineStatus === '已逾期').length
  const dueSoon = rawRows.value.filter(r => r.deadlineStatus === '临期').length
  if (overdue > 0) items.push({ label: '已逾期事项', value: `${overdue} 项`, icon: 'danger' })
  if (dueSoon > 0) items.push({ label: '临期事项', value: `${dueSoon} 项`, icon: 'pending' })
  return items
})

/** S03 办理状态展示映射（库值不改，仅前端展示层） */
const S03_STATUS_DISPLAY_MAP: Record<string, string> = {
  '调查中': '核查中',
  '协调中': '协商化解中',
}
function mapS03StatusLabel(status: unknown): string {
  if (typeof status !== 'string') return String(status ?? '')
  return S03_STATUS_DISPLAY_MAP[status] || status
}

function getStatusColor(status: string): string {
  const s = mapS03StatusLabel(status).toLowerCase()
  if (s.includes('逾期') || s.includes('超期')) return STATUS_COLORS.danger
  if (s.includes('临期') || s.includes('待')) return STATUS_COLORS.pending
  if (s.includes('完成') || s.includes('办结') || s.includes('闭环')) return STATUS_COLORS.normal
  return STATUS_COLORS.processing
}

function handleRowClick(row: LaborDisputeRow) {
  selectedRowId.value = selectedRowId.value === row.rowId ? null : row.rowId
}

function updateScale() {
  scale.value = Math.min(1, window.innerWidth / 1920, window.innerHeight / 1080)
}

function handleResize() {
  updateScale()
  chart?.resize()
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

function handleOverlayClick(e: MouseEvent) {
  if ((e.target as HTMLElement).classList.contains('s03-overlay')) {
    emit('close')
  }
}

async function loadData() {
  const resp = await getDashboardKpiDetail('S03') as any
  if (!resp) return
  const list: any[] = resp.detailData || []
  const rows: LaborDisputeRow[] = list.map((item, index) => ({
    rowId: `S03-D-${index + 1}`,
    name: item.name || item.title || '未命名事项',
    type: item.type || item.category || '',
    segment: item.segment || item.location || item.workPoint || '',
    status: item.status || '待处理',
    deadlineStatus: item.deadlineStatus || item.overdueStatus || '',
    department: item.department || item.responsible || '',
    deadline: item.deadline || item.dueDate || '',
    amount: item.amount || '',
    people: item.people || '',
    time: item.time || item.date || '',
  }))
  rawRows.value = rows
  if (rows.length > 0) selectedRowId.value = rows[0].rowId

  const summary = resp.summary || []
  const getSummary = (label: string) => {
    const item = summary.find((s: any) => s.label === label)
    return item ? item.value : 0
  }
  data.value = {
    summary: {
      pendingTotal: getSummary('未办结纠纷') || list.length,
      newThisMonth: getSummary('本月新增'),
      closedThisMonth: getSummary('本月办结'),
      peopleCount: getSummary('涉及人数') || 0,
      amount: getSummary('涉及金额') || 0,
    },
    detailData: rows,
    dataSource: resp.dataSource || '劳务用工纠纷台账（农民工工资）',
    updateTime: resp.updateTime || '',
  }

  await nextTick()
  initChart()
}

function initChart() {
  if (!chartRef.value) return
  chart?.dispose()
  chart = echarts.init(chartRef.value)

  const list = statusDistribution.value
  const yAxisData = [...list].reverse().map(d => d.name)
  const values = [...list].reverse().map(d => d.value)

  const maxVal = Math.max(...values, 0)
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
        const value = params[0]?.value ?? 0
        const total = rawRows.value.length
        const pct = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0'
        return `${name}<br/>数量：${value} 项<br/>占比：${pct}%`
      },
    },
    grid: { left: 72, right: 50, top: 10, bottom: 24 },
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
        type: 'bar',
        data: values.map((v, i) => ({
          value: v,
          itemStyle: { color: getStatusColor(yAxisData[i]), borderRadius: [0, 3, 3, 0] },
        })),
        barWidth: 14,
        label: {
          show: true,
          position: 'right',
          color: '#b8cce3',
          fontSize: 12,
          formatter: '{c}项',
        },
      },
    ],
  })
}

watch(() => data.value.detailData.length, () => nextTick(initChart), { immediate: false })

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
  <div class="s03-overlay" :class="{ acceptance: isAcceptanceMode }" @click="handleOverlayClick">
    <div
      ref="modalRef"
      class="s03-modal"
      :class="{ acceptance: isAcceptanceMode }"
      :style="{ '--s03-scale': scale }"
      role="dialog"
      aria-modal="true"
      aria-labelledby="s03-modal-title"
      tabindex="-1"
    >
      <header class="s03-header">
        <h2 id="s03-modal-title">
          <span class="title-key">S03</span>
          <span class="title-name">农民工权益保障</span>
        </h2>
        <button type="button" aria-label="关闭" @click="emit('close')">
          <X :size="22" />
        </button>
      </header>

      <section class="s03-summary" aria-label="S03摘要">
        <div v-for="item in summaryCards" :key="item.label" class="summary-card">
          <span class="summary-label">{{ item.label }}</span>
          <div class="summary-value-row">
            <strong :style="{ color: item.color }">{{ item.value }}</strong>
            <small v-if="item.unit">{{ item.unit }}</small>
          </div>
        </div>
      </section>

      <main class="s03-content">
        <div class="s03-main">
          <section class="panel chart-panel">
            <h3>未办结劳务纠纷办理状态分布</h3>
            <div ref="chartRef" class="s03-chart" />
          </section>

          <section class="panel table-panel">
            <div class="panel-heading">
              <h3>未办结劳务纠纷明细</h3>
              <span class="panel-sub">共 {{ rawRows.length }} 项</span>
            </div>
            <div class="table-scroll">
              <table class="dispute-table">
                <colgroup>
                  <col style="width: 26%" />
                  <col style="width: 13%" />
                  <col style="width: 18%" />
                  <col style="width: 10%" />
                  <col style="width: 12%" />
                  <col style="width: 11%" />
                  <col style="width: 10%" />
                </colgroup>
                <thead>
                  <tr>
                    <th class="col-left">纠纷事项</th>
                    <th class="col-center">办理状态</th>
                    <th class="col-left">责任部门</th>
                    <th class="col-center">涉及人数</th>
                    <th class="col-center">涉及金额</th>
                    <th class="col-center">发生时间</th>
                    <th class="col-center">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="row in sortedRows"
                    :key="row.rowId"
                    :class="{ 'row-selected': selectedRowId === row.rowId }"
                    @click="handleRowClick(row)"
                  >
                    <td :title="row.name" class="cell-name col-left">{{ row.name }}</td>
                    <td class="col-center">
                      <span class="status-tag" :style="{ color: getStatusColor(row.status), borderColor: getStatusColor(row.status) }">{{ mapS03StatusLabel(row.status) }}</span>
                    </td>
                    <td :title="row.department" class="col-left">{{ row.department || '—' }}</td>
                    <td class="col-center">{{ row.people || '—' }}</td>
                    <td class="col-center">{{ row.amount || '—' }}</td>
                    <td class="col-center">{{ row.time || '—' }}</td>
                    <td class="col-center">
                      <button type="button" class="row-action" @click.stop="handleRowClick(row)">
                        查看详情
                      </button>
                    </td>
                  </tr>
                  <tr v-if="sortedRows.length === 0">
                    <td colspan="7" class="empty-row">暂无数据</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>

        <aside class="s03-side">
          <section class="panel status-panel">
            <h3>办理状态构成</h3>
            <div class="compose-bar">
              <div class="compose-bar-fill">
                <template v-for="item in statusDistribution" :key="item.name">
                  <div
                    class="compose-seg"
                    :style="{
                      width: rawRows.length > 0 ? (item.value / rawRows.length * 100) + '%' : '0%',
                      backgroundColor: getStatusColor(item.name),
                    }"
                    :title="`${item.name}：${item.value} 项`"
                  ></div>
                </template>
              </div>
              <div class="compose-total">
                当前未办结合计 <strong>{{ rawRows.length }}</strong> 项
              </div>
            </div>
            <ul class="compose-list">
              <li v-for="item in statusDistribution" :key="item.name">
                <span class="dot" :style="{ backgroundColor: getStatusColor(item.name) }"></span>
                <span class="name">{{ item.name }}</span>
                <span class="value">{{ item.value }} 项</span>
              </li>
            </ul>
          </section>

          <section class="panel type-panel">
            <h3>纠纷类型分布</h3>
            <template v-if="hasTypeData">
              <ul class="type-bar-list">
                <li v-for="item in typeDistribution.slice(0, 5)" :key="item.name">
                  <span class="type-name">{{ item.name }}</span>
                  <div class="type-bar-wrap">
                    <div
                      class="type-bar"
                      :style="{ width: typeDistribution[0] ? (item.value / typeDistribution[0].value * 100) + '%' : '0%' }"
                    ></div>
                  </div>
                  <span class="type-num">{{ item.value }}</span>
                </li>
              </ul>
            </template>
            <div v-else class="side-empty">
              <AlertCircle :size="22" />
              <p>暂无可分类数据</p>
              <small>当前数据中缺少纠纷类型字段</small>
            </div>
          </section>

          <section class="panel concern-panel">
            <h3>重点办理提醒</h3>
            <template v-if="concernItems.length > 0">
              <ul class="concern-list">
                <li v-for="item in concernItems" :key="item.label">
                  <span class="concern-dot" :class="item.icon"></span>
                  <span class="concern-label">{{ item.label }}</span>
                  <span class="concern-value">{{ item.value }}</span>
                </li>
              </ul>
            </template>
            <div v-else class="side-empty">
              <AlertCircle :size="22" />
              <p>暂无可判定提醒</p>
              <small>缺少时限、更新时间或责任单位字段</small>
            </div>
          </section>
        </aside>
      </main>

      <footer class="s03-footer">
        <div class="footer-info" title="正式接口：/api/dashboard/kpi/S03">
          <FileCheck :size="13" />
          <span>数据来源：{{ data.dataSource }}</span>
        </div>
        <div class="footer-info">
          <Clock :size="13" />
          <span>更新时间：{{ data.updateTime }}</span>
        </div>
        <button type="button" class="btn-primary" @click="emit('close')">关闭</button>
      </footer>
    </div>
  </div>
</template>

<style scoped lang="scss">
.s03-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: rgba(2, 11, 24, 0.76);
  backdrop-filter: blur(4px);
  animation: s03Fade 0.2s ease;

  &.acceptance { animation: none; }
}

.s03-modal {
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
  transform: scale(var(--s03-scale));
  transform-origin: center;
  animation: s03Rise 0.25s ease;

  &.acceptance,
  &.acceptance * {
    animation: none !important;
    transition: none !important;
  }

  &:focus,
  &:focus-visible { outline: none; }
}

.s03-header {
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

.s03-summary {
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

.s03-content {
  min-height: 0;
  flex: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 12px;
  box-sizing: border-box;
  padding: 12px 16px;
}

.s03-main,
.s03-side {
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

.chart-panel {
  flex: 0 0 260px;
  padding: 10px 12px;
}

.s03-chart {
  width: 100%;
  height: 216px;
}

.table-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-heading {
  height: 38px;
  flex: 0 0 38px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
  padding: 0 12px;
  border-bottom: 1px solid rgba(143, 169, 200, 0.1);

  h3 { font-size: 15px; }

  .panel-sub {
    font-size: 13px;
    color: #8fa9c8;
  }
}

.table-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0;

  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: rgba(47, 156, 255, 0.2);
    border-radius: 3px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
}

.dispute-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 14px;

  th {
    height: 36px;
    padding: 0 10px;
    border-bottom: 1px solid rgba(143, 169, 200, 0.15);
    background: rgba(7, 27, 49, 0.85);
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
      background: rgba(47, 156, 255, 0.04);
    }

    &.row-selected {
      background: rgba(47, 156, 255, 0.08);
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

.status-panel,
.type-panel,
.concern-panel {
  flex: 1;
  padding: 10px 12px;
}

.compose-bar {
  margin-top: 10px;
}

.compose-bar-fill {
  height: 10px;
  border-radius: 5px;
  background: rgba(143, 169, 200, 0.1);
  overflow: hidden;
  display: flex;
}

.compose-seg {
  height: 100%;
  transition: width 0.3s;
}

.compose-total {
  margin-top: 8px;
  font-size: 13px;
  color: #b8cce3;

  strong {
    color: #e8f3ff;
    font-size: 16px;
    font-weight: 700;
    margin: 0 2px;
  }
}

.compose-list {
  list-style: none;
  padding: 0;
  margin: 12px 0 0;
  display: flex;
  flex-direction: column;
  gap: 8px;

  li {
    display: flex;
    align-items: center;
    font-size: 13px;
    color: #b8cce3;
  }

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 8px;
    flex-shrink: 0;
  }

  .name {
    flex: 1;
    color: #b8cce3;
  }

  .value {
    color: #d9e7f5;
    font-weight: 500;
  }
}

.type-bar-list {
  list-style: none;
  padding: 0;
  margin: 10px 0 0;
  display: flex;
  flex-direction: column;
  gap: 10px;

  li {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
  }

  .type-name {
    width: 64px;
    color: #b8cce3;
    flex-shrink: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .type-bar-wrap {
    flex: 1;
    height: 6px;
    background: rgba(143, 169, 200, 0.08);
    border-radius: 3px;
    overflow: hidden;
  }

  .type-bar {
    height: 100%;
    background: linear-gradient(90deg, #2f9cff, rgba(47, 156, 255, 0.4));
    border-radius: 3px;
    transition: width 0.3s;
  }

  .type-num {
    width: 24px;
    text-align: right;
    color: #d9e7f5;
    font-weight: 500;
    font-variant-numeric: tabular-nums;
    flex-shrink: 0;
  }
}

.concern-list {
  list-style: none;
  padding: 0;
  margin: 10px 0 0;
  display: flex;
  flex-direction: column;
  gap: 10px;

  li {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    padding: 10px 12px;
    border: 1px solid rgba(143, 169, 200, 0.1);
    border-radius: 4px;
    background: rgba(255, 255, 255, 0.01);
  }

  .concern-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;

    &.danger { background: #ff4f5e; box-shadow: 0 0 6px rgba(255, 79, 94, 0.5); }
    &.pending { background: #ffb347; box-shadow: 0 0 6px rgba(255, 179, 71, 0.5); }
  }

  .concern-label {
    flex: 1;
    color: #b8cce3;
  }

  .concern-value {
    color: #e8f3ff;
    font-weight: 600;
  }
}

.side-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #8ba6c3;
  padding: 16px 0 8px;

  p {
    margin: 0;
    font-size: 14px;
    color: #a0b8d0;
  }

  small {
    font-size: 12px;
    color: #6b86a5;
    text-align: center;
  }
}

.s03-footer {
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
      max-width: 360px;
      overflow: hidden;

      span {
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }
  }

  button {
    width: 120px;
    height: 34px;
    margin-left: auto;
    border: 1px solid rgba(47, 156, 255, 0.35);
    border-radius: 4px;
    background: rgba(47, 156, 255, 0.08);
    color: #e8f3ff;
    font-size: 14px;
    cursor: pointer;

    &:hover,
    &:focus-visible {
      background: rgba(47, 156, 255, 0.15);
      outline: none;
    }
  }
}

@keyframes s03Fade {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes s03Rise {
  from {
    opacity: 0;
    transform: translateY(12px) scale(var(--s03-scale));
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(var(--s03-scale));
  }
}
</style>
