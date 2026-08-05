<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { Clock, FileCheck, X, AlertCircle, AlertTriangle } from 'lucide-vue-next'
import { getDashboardKpiDetail } from '@/services/api'

// S 组业务主色：蓝色（与 S01/S02/S03 一致）
const THEME_COLOR = '#2f9cff'
const THEME_RGB = '47, 156, 255'

// 语义状态色
const STATUS_COLORS = {
  normal: '#69e36f',
  processing: '#2f9cff',
  pending: '#ffb347',
  danger: '#ff4f5e',
  muted: '#8ba6c3',
} as const

interface MassAppealRow {
  rowId: string
  content: string
  source: string
  location: string
  acceptDate: string
  deadline: string
  processStatus: string
  deadlineStatus: string
}

interface S04Data {
  summary: {
    pendingTotal: number
    newThisMonth: number
    closedThisMonth: number
    overdueCount: number
    avgProcessDays: number
  }
  detailData: MassAppealRow[]
  dataSource: string
  updateTime: string
}

const emit = defineEmits<{ (e: 'close'): void }>()

const isAcceptanceMode = new URLSearchParams(window.location.search).get('acceptance') === '1'
const modalRef = ref<HTMLDivElement | null>(null)
const chartRef = ref<HTMLDivElement | null>(null)
const scale = ref(1)
let chart: echarts.ECharts | null = null

const data = ref<S04Data>({
  summary: { pendingTotal: 3, newThisMonth: 2, closedThisMonth: 4, overdueCount: 1, avgProcessDays: 7 },
  detailData: [],
  dataSource: '群众诉求台账',
  updateTime: '2026-07-13 09:30',
})

const selectedRowId = ref<string | null>(null)
const rawRows = ref<MassAppealRow[]>([])

const selectedRow = computed<MassAppealRow | null>(() => {
  if (!selectedRowId.value) return null
  return sortedRows.value.find(r => r.rowId === selectedRowId.value) || null
})

// 默认排序：已逾期优先，其次按办理期限升序
const sortedRows = computed<MassAppealRow[]>(() => {
  return [...rawRows.value].sort((a, b) => {
    const aOverdue = a.deadlineStatus === '已逾期' ? 0 : 1
    const bOverdue = b.deadlineStatus === '已逾期' ? 0 : 1
    if (aOverdue !== bOverdue) return aOverdue - bOverdue
    return a.deadline.localeCompare(b.deadline)
  })
})

const summaryCards = computed(() => [
  { label: '当前未办结', value: data.value.summary.pendingTotal, unit: '项', color: THEME_COLOR },
  { label: '本月新增', value: data.value.summary.newThisMonth, unit: '项', color: '#ffb347' },
  { label: '本月办结', value: data.value.summary.closedThisMonth, unit: '项', color: '#69e36f' },
  { label: '已逾期', value: data.value.summary.overdueCount, unit: '项', color: STATUS_COLORS.danger },
  { label: '平均办理时长', value: data.value.summary.avgProcessDays, unit: '天', color: THEME_COLOR },
])

// 诉求来源分布（按真实来源字段聚合）
const sourceDistribution = computed(() => {
  const map = new Map<string, number>()
  rawRows.value.forEach(r => {
    if (r.source) map.set(r.source, (map.get(r.source) || 0) + 1)
  })
  return Array.from(map.entries())
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
})

// 办理状态构成
const processStatusDistribution = computed(() => {
  const map = new Map<string, number>()
  rawRows.value.forEach(r => {
    const key = r.processStatus || '—'
    map.set(key, (map.get(key) || 0) + 1)
  })
  return Array.from(map.entries())
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
})

// 时限状态构成
const deadlineStatusDistribution = computed(() => {
  const map = new Map<string, number>()
  rawRows.value.forEach(r => {
    const key = r.deadlineStatus || '—'
    map.set(key, (map.get(key) || 0) + 1)
  })
  return Array.from(map.entries())
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
})

const overdueCount = computed(() => rawRows.value.filter(r => r.deadlineStatus === '已逾期').length)
const processUnknownCount = computed(() => rawRows.value.filter(r => !r.processStatus || r.processStatus === '—').length)
const deadlineUnknownCount = computed(() => rawRows.value.filter(r => !r.deadlineStatus || r.deadlineStatus === '—').length)

// 最早受理日期与最近办理期限
const earliestAcceptDate = computed(() => {
  const dates = rawRows.value.map(r => r.acceptDate).filter(Boolean).sort()
  return dates[0] || '—'
})

const latestDeadline = computed(() => {
  const dates = rawRows.value.map(r => r.deadline).filter(Boolean).sort()
  return dates[dates.length - 1] || '—'
})

function getProcessStatusColor(status: string): string {
  if (status === '—' || !status) return STATUS_COLORS.muted
  if (status.includes('办理中')) return STATUS_COLORS.processing
  if (status.includes('待')) return STATUS_COLORS.pending
  if (status.includes('完成') || status.includes('办结')) return STATUS_COLORS.normal
  return STATUS_COLORS.processing
}

function getDeadlineStatusColor(status: string): string {
  if (status === '—' || !status) return STATUS_COLORS.muted
  if (status.includes('逾期')) return STATUS_COLORS.danger
  if (status.includes('临期')) return STATUS_COLORS.pending
  if (status.includes('正常')) return STATUS_COLORS.normal
  return STATUS_COLORS.muted
}

function handleRowClick(row: MassAppealRow) {
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
  if ((e.target as HTMLElement).classList.contains('s04-overlay')) {
    emit('close')
  }
}

// 将混合状态字段拆分为办理状态和时限状态
// 规则：可确认的"办理中"放入办理状态；可确认的"逾期"放入时限状态；
// 无法确认的另一维显示"—"，不推测办理阶段。
function splitStatus(rawStatus: string): { processStatus: string; deadlineStatus: string } {
  const s = rawStatus || ''
  let processStatus = '—'
  let deadlineStatus = '—'
  if (s.includes('逾期') || s.includes('超期')) {
    deadlineStatus = '已逾期'
  } else if (s.includes('临期')) {
    deadlineStatus = '临期'
  } else if (s.includes('办理中') || s.includes('处理中') || s.includes('跟进中')) {
    processStatus = '办理中'
  } else if (s.includes('待回复') || s.includes('待确认')) {
    processStatus = s
  } else if (s.includes('办理中')) {
    processStatus = '办理中'
  }
  // 若状态同时包含办理阶段和逾期信息，分别提取
  if (s.includes('办理中') && s.includes('逾期')) {
    processStatus = '办理中'
    deadlineStatus = '已逾期'
  }
  return { processStatus, deadlineStatus }
}

async function loadData() {
  const resp = await getDashboardKpiDetail('S04') as any
  if (!resp) return
  const list: any[] = resp.detailData || []
  const rows: MassAppealRow[] = list.map((item, index) => {
    const rawStatus = String(item.status || '')
    const { processStatus, deadlineStatus } = splitStatus(rawStatus)
    return {
      rowId: `S04-D-${index + 1}`,
      content: item.content || item.name || '未命名事项',
      source: item.source || '',
      location: item.location || '',
      acceptDate: item.time || item.acceptDate || '',
      deadline: item.deadline || '',
      processStatus,
      deadlineStatus,
    }
  })
  rawRows.value = rows
  if (rows.length > 0) selectedRowId.value = rows[0].rowId

  const summary = resp.summary || []
  const getSummary = (label: string) => {
    const item = summary.find((s: any) => s.label === label)
    return item ? Number(item.value) : 0
  }
  data.value = {
    summary: {
      pendingTotal: getSummary('未办结诉求') || list.length,
      newThisMonth: getSummary('本月新增'),
      closedThisMonth: getSummary('本月办结'),
      overdueCount: getSummary('已逾期') || getSummary('逾期未办'),
      avgProcessDays: getSummary('平均办理时长'),
    },
    detailData: rows,
    dataSource: resp.dataSource || '群众诉求台账',
    updateTime: resp.updateTime || '',
  }

  await nextTick()
  initChart()
}

function initChart() {
  if (!chartRef.value) return
  chart?.dispose()
  chart = echarts.init(chartRef.value)

  const list = sourceDistribution.value
  const yAxisData = [...list].reverse().map(d => d.name)
  const values = [...list].reverse().map(d => d.value)

  const actualMax = Math.max(...values, 0)
  const xAxisMax = Math.max(2, Math.ceil(actualMax * 1.15))

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
        data: values.map(v => ({
          value: v,
          itemStyle: { color: THEME_COLOR, borderRadius: [0, 3, 3, 0] },
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
  <div class="s04-overlay" :class="{ acceptance: isAcceptanceMode }" @click="handleOverlayClick">
    <div
      ref="modalRef"
      class="s04-modal"
      :class="{ acceptance: isAcceptanceMode }"
      :style="{ '--s04-scale': scale }"
      role="dialog"
      aria-modal="true"
      aria-labelledby="s04-modal-title"
      tabindex="-1"
    >
      <header class="s04-header">
        <h2 id="s04-modal-title">
          <span class="title-key">S04</span>
          <span class="title-name">群众诉求闭环</span>
        </h2>
        <button type="button" aria-label="关闭" @click="emit('close')">
          <X :size="22" />
        </button>
      </header>

      <section class="s04-summary" aria-label="S04摘要">
        <div v-for="item in summaryCards" :key="item.label" class="summary-card">
          <span class="summary-label">{{ item.label }}</span>
          <div class="summary-value-row">
            <strong :style="{ color: item.color }">{{ item.value }}</strong>
            <small v-if="item.unit">{{ item.unit }}</small>
          </div>
        </div>
      </section>

      <main class="s04-content">
        <div class="s04-main">
          <section class="panel chart-panel">
            <h3>未办结群众诉求来源分布</h3>
            <div ref="chartRef" class="s04-chart" />
          </section>

          <section class="panel table-panel">
            <div class="panel-heading">
              <h3>未办结群众诉求明细</h3>
              <span class="panel-sub">共 {{ rawRows.length }} 项</span>
            </div>
            <div class="table-scroll">
              <table class="appeal-table">
                <colgroup>
                  <col style="width: 22%" />
                  <col style="width: 11%" />
                  <col style="width: 18%" />
                  <col style="width: 11%" />
                  <col style="width: 11%" />
                  <col style="width: 9%" />
                  <col style="width: 9%" />
                  <col style="width: 9%" />
                </colgroup>
                <thead>
                  <tr>
                    <th class="col-left">诉求事项</th>
                    <th class="col-center">诉求来源</th>
                    <th class="col-left">涉及地点</th>
                    <th class="col-center">受理日期</th>
                    <th class="col-center">办理期限</th>
                    <th class="col-center">办理状态</th>
                    <th class="col-center">时限状态</th>
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
                    <td :title="row.content" class="cell-name col-left">{{ row.content }}</td>
                    <td class="col-center">{{ row.source || '—' }}</td>
                    <td :title="row.location" class="cell-name col-left">{{ row.location || '—' }}</td>
                    <td class="col-center">{{ row.acceptDate || '—' }}</td>
                    <td class="col-center">{{ row.deadline || '—' }}</td>
                    <td class="col-center">
                      <span
                        class="status-tag"
                        :style="{ color: getProcessStatusColor(row.processStatus), borderColor: getProcessStatusColor(row.processStatus) }"
                      >{{ row.processStatus }}</span>
                    </td>
                    <td class="col-center">
                      <span
                        class="status-tag"
                        :style="{ color: getDeadlineStatusColor(row.deadlineStatus), borderColor: getDeadlineStatusColor(row.deadlineStatus) }"
                      >{{ row.deadlineStatus }}</span>
                    </td>
                    <td class="col-center">
                      <button type="button" class="row-action" @click.stop="handleRowClick(row)">
                        查看详情
                      </button>
                    </td>
                  </tr>
                  <tr v-if="sortedRows.length === 0">
                    <td colspan="8" class="empty-row">暂无数据</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>

        <aside class="s04-side">
          <!-- 当前办理构成 -->
          <section class="panel process-panel">
            <h3>当前办理构成</h3>
            <div class="compose-total">
              当前未办结合计 <strong>{{ rawRows.length }}</strong> 项
            </div>
            <ul class="compose-list">
              <li v-for="item in processStatusDistribution" :key="item.name">
                <span class="dot" :style="{ backgroundColor: getProcessStatusColor(item.name) }"></span>
                <span class="name">{{ item.name }}</span>
                <span class="value">{{ item.value }} 项</span>
              </li>
            </ul>
            <div v-if="processUnknownCount > 0" class="compose-note">
              部分记录办理阶段待补充
            </div>
          </section>

          <!-- 时限关注 -->
          <section class="panel deadline-panel">
            <h3>时限关注</h3>
            <div class="compose-bar">
              <div class="compose-bar-fill">
                <template v-for="item in deadlineStatusDistribution" :key="item.name">
                  <div
                    class="compose-seg"
                    :style="{
                      width: rawRows.length > 0 ? (item.value / rawRows.length * 100) + '%' : '0%',
                      backgroundColor: getDeadlineStatusColor(item.name),
                    }"
                    :title="`${item.name}：${item.value} 项`"
                  ></div>
                </template>
              </div>
            </div>
            <ul class="compose-list">
              <li>
                <span class="dot" :style="{ backgroundColor: STATUS_COLORS.danger }"></span>
                <span class="name">已逾期</span>
                <span class="value">{{ overdueCount }} 项</span>
              </li>
              <li>
                <span class="dot" :style="{ backgroundColor: STATUS_COLORS.muted }"></span>
                <span class="name">未判定</span>
                <span class="value">{{ deadlineUnknownCount }} 项</span>
              </li>
            </ul>
          </section>

          <!-- 重点办理提醒 / 选中事项详情 -->
          <section class="panel concern-panel">
            <h3>{{ selectedRow ? '选中事项详情' : '重点办理提醒' }}</h3>
            <template v-if="selectedRow">
              <dl class="detail-dl">
                <div><dt>诉求事项</dt><dd :title="selectedRow.content">{{ selectedRow.content }}</dd></div>
                <div><dt>来源渠道</dt><dd>{{ selectedRow.source || '—' }}</dd></div>
                <div><dt>涉及地点</dt><dd :title="selectedRow.location">{{ selectedRow.location || '—' }}</dd></div>
                <div><dt>受理日期</dt><dd>{{ selectedRow.acceptDate || '—' }}</dd></div>
                <div><dt>办理期限</dt><dd>{{ selectedRow.deadline || '—' }}</dd></div>
                <div><dt>办理状态</dt><dd>{{ selectedRow.processStatus }}</dd></div>
                <div><dt>时限状态</dt><dd>{{ selectedRow.deadlineStatus }}</dd></div>
              </dl>
            </template>
            <template v-else>
              <div class="concern-summary">
                <div class="concern-item danger" v-if="overdueCount > 0">
                  <AlertTriangle :size="14" />
                  <span>已逾期事项：{{ overdueCount }} 项</span>
                </div>
                <dl class="detail-dl">
                  <div><dt>最早受理日期</dt><dd>{{ earliestAcceptDate }}</dd></div>
                  <div><dt>最近办理期限</dt><dd>{{ latestDeadline }}</dd></div>
                  <div v-if="processUnknownCount > 0"><dt>待补充字段</dt><dd>办理状态（{{ processUnknownCount }} 项）</dd></div>
                  <div v-if="deadlineUnknownCount > 0"><dt>待补充字段</dt><dd>时限状态（{{ deadlineUnknownCount }} 项）</dd></div>
                </dl>
                <div class="concern-tip" title="S04-D-* 为前端按列表顺序生成的临时标识，非后端稳定ID">
                  标识说明：S04-D-* 为前端临时标识
                </div>
              </div>
            </template>
          </section>
        </aside>
      </main>

      <footer class="s04-footer">
        <div class="footer-info" title="正式接口：/api/dashboard/kpi/S04">
          <FileCheck :size="13" />
          <span>数据来源：{{ data.dataSource }}</span>
        </div>
        <div class="footer-info">
          <Clock :size="13" />
          <span>更新时间：{{ data.updateTime }}</span>
        </div>
        <div class="footer-info">
          <AlertCircle :size="13" />
          <span>重复投诉关联原事项不计重；逾期口径取自状态字段</span>
        </div>
        <button type="button" class="btn-primary" @click="emit('close')">关闭</button>
      </footer>
    </div>
  </div>
</template>

<style scoped lang="scss">
.s04-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: rgba(2, 11, 24, 0.76);
  backdrop-filter: blur(4px);
  animation: s04Fade 0.2s ease;

  &.acceptance { animation: none; }
}

.s04-modal {
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
  transform: scale(var(--s04-scale));
  transform-origin: center;
  animation: s04Rise 0.25s ease;

  &.acceptance,
  &.acceptance * {
    animation: none !important;
    transition: none !important;
  }

  &:focus,
  &:focus-visible { outline: none; }
}

.s04-header {
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

.s04-summary {
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

.s04-content {
  min-height: 0;
  flex: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 12px;
  box-sizing: border-box;
  padding: 12px 16px;
}

.s04-main,
.s04-side {
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
  flex: 0 0 290px;
  padding: 10px 12px;
}

.s04-chart {
  width: 100%;
  height: 246px;
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
  padding: 0 12px;
  box-sizing: border-box;
  border-bottom: 1px solid rgba(143, 169, 200, 0.1);

  .panel-sub {
    color: #8fa9c8;
    font-size: 12px;
  }
}

.table-scroll {
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

.appeal-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 14px;

  th {
    height: 36px;
    padding: 0 8px;
    border-bottom: 1px solid rgba(143, 169, 200, 0.15);
    background: #071b31;
    color: #b8cce3;
    font-size: 14px;
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 1;
  }

  td {
    height: 38px;
    padding: 0 8px;
    border-bottom: 1px solid rgba(143, 169, 200, 0.08);
    color: #d9e7f5;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .col-left { text-align: left; }
  .col-center { text-align: center; }

  tbody tr {
    cursor: pointer;

    &:hover {
      background: rgba(47, 156, 255, 0.035);
    }

    &.row-selected {
      background: rgba(47, 156, 255, 0.08);
      box-shadow: inset 3px 0 0 #2f9cff;
    }
  }

  .cell-name {
    max-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .empty-row {
    text-align: center;
    color: #8fa9c8;
    font-size: 13px;
  }
}

.status-tag {
  display: inline-flex;
  min-width: 56px;
  height: 24px;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  padding: 0 7px;
  border: 1px solid;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.03);
}

.row-action {
  height: 26px;
  padding: 0 10px;
  border: 1px solid rgba(47, 156, 255, 0.3);
  border-radius: 3px;
  background: rgba(47, 156, 255, 0.06);
  color: #b8cce3;
  font-size: 12px;
  cursor: pointer;

  &:hover,
  &:focus-visible {
    background: rgba(47, 156, 255, 0.14);
    color: #e8f3ff;
    outline: none;
  }
}

.s04-side .panel { padding: 10px 12px; }

.process-panel { flex: 1; }
.deadline-panel { flex: 1; }
.concern-panel { flex: 1.2; }

.compose-total {
  margin-top: 6px;
  color: #b8cce3;
  font-size: 13px;

  strong {
    color: #e8f3ff;
    font-family: "DIN Alternate", "Roboto Condensed", sans-serif;
    font-size: 15px;
    font-weight: 700;
    margin: 0 2px;
  }
}

.compose-list {
  list-style: none;
  margin: 8px 0 0;
  padding: 0;

  li {
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 28px;
    border-bottom: 1px solid rgba(143, 169, 200, 0.07);
    font-size: 13px;

    &:last-child { border-bottom: 0; }

    .dot {
      width: 8px;
      height: 8px;
      flex: none;
      border-radius: 50%;
    }

    .name {
      flex: 1;
      min-width: 0;
      color: #d9e7f5;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .value {
      flex: none;
      color: #8fa9c8;
    }
  }
}

.compose-note {
  margin-top: 8px;
  padding: 6px 8px;
  border-radius: 3px;
  background: rgba(255, 179, 71, 0.08);
  border: 1px solid rgba(255, 179, 71, 0.2);
  color: #ffb347;
  font-size: 12px;
  line-height: 1.4;
}

.compose-bar {
  margin-top: 8px;

  .compose-bar-fill {
    display: flex;
    height: 8px;
    border-radius: 4px;
    overflow: hidden;
    background: rgba(143, 169, 200, 0.08);
  }

  .compose-seg {
    min-width: 2px;
    transition: width 0.2s;
  }
}

.detail-dl {
  margin: 8px 0 0;
  padding: 0;

  div {
    min-height: 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    border-bottom: 1px solid rgba(143, 169, 200, 0.07);
    font-size: 13px;

    &:last-child { border-bottom: 0; }
  }

  dt { color: #8fa9c8; flex: 0 0 auto; }
  dd {
    margin: 0;
    color: #d9e7f5;
    text-align: right;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.concern-summary {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 6px;
}

.concern-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border-radius: 3px;
  font-size: 13px;

  &.danger {
    background: rgba(255, 79, 94, 0.08);
    border: 1px solid rgba(255, 79, 94, 0.2);
    color: #ff4f5e;
  }
}

.concern-tip {
  padding: 6px 8px;
  border-radius: 3px;
  background: rgba(143, 169, 200, 0.06);
  color: #8fa9c8;
  font-size: 12px;
  line-height: 1.4;
  cursor: help;
}

.s04-footer {
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
  }

  .btn-primary {
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

@keyframes s04Fade {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes s04Rise {
  from {
    opacity: 0;
    transform: translateY(12px) scale(var(--s04-scale));
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(var(--s04-scale));
  }
}
</style>
