<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { Clock, FileCheck, X, AlertTriangle } from 'lucide-vue-next'
import { getDashboardKpiDetail } from '@/services/api'
import { demoBizStatusLabel, demoDetailSummaryList } from '@/utils/esg-demo'

const THEME_COLOR = '#a66cff'

const STATUS_COLORS = {
  normal: '#69e36f',
  processing: '#a66cff',
  pending: '#ffb347',
  danger: '#ff4f5e',
  muted: '#8ba6c3',
} as const

interface ApprovalRow {
  rowId: string
  objectId?: number
  name: string
  type: string
  status: string
  deadline: string
  department: string
  progress: string
}

const props = defineProps<{ focusObjectId?: number | null }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const isAcceptanceMode = new URLSearchParams(window.location.search).get('acceptance') === '1'
const modalRef = ref<HTMLDivElement | null>(null)
const chartRef = ref<HTMLDivElement | null>(null)
const scale = ref(1)
let chart: echarts.ECharts | null = null

const loading = ref(true)
const loadError = ref('')
const summaryCards = ref<Array<{ label: string; value: string | number; unit?: string; color?: string }>>([])
const dataSource = ref('biz_project_approval + biz_approval_catalog')
const updateTime = ref('')
const selectedRowId = ref<string | null>(null)
const rawRows = ref<ApprovalRow[]>([])

const selectedRow = computed<ApprovalRow | null>(() => {
  if (!selectedRowId.value) return null
  return sortedRows.value.find(r => r.rowId === selectedRowId.value) || null
})

const sortedRows = computed<ApprovalRow[]>(() => {
  return [...rawRows.value].sort((a, b) => {
    const aDone = a.status.includes('完成') || a.status.includes('办结') ? 1 : 0
    const bDone = b.status.includes('完成') || b.status.includes('办结') ? 1 : 0
    if (aDone !== bDone) return aDone - bDone
    return a.deadline.localeCompare(b.deadline)
  })
})

const statusDistribution = computed(() => {
  const map = new Map<string, number>()
  rawRows.value.forEach(r => {
    const key = r.status || '—'
    map.set(key, (map.get(key) || 0) + 1)
  })
  return Array.from(map.entries()).map(([name, value]) => {
    let color: string = STATUS_COLORS.muted
    if (name.includes('逾期')) color = STATUS_COLORS.danger
    else if (name.includes('待') || name.includes('补正')) color = STATUS_COLORS.pending
    else if (name.includes('完成') || name.includes('办结') || name.includes('通过')) color = STATUS_COLORS.normal
    else color = STATUS_COLORS.processing
    return { name, value, color }
  })
})

const nodeImpact = computed(() => {
  const map = new Map<string, number>()
  rawRows.value.forEach(r => {
    const key = r.type || '报批报建'
    map.set(key, (map.get(key) || 0) + 1)
  })
  return Array.from(map.entries()).map(([name, value]) => ({ name, value }))
})

const alertText = computed(() => {
  const pending = rawRows.value.filter(r => !(r.status.includes('完成') || r.status.includes('办结'))).length
  const overdue = rawRows.value.filter(r => r.status.includes('逾期')).length
  if (!pending && !overdue) return '当前适用审批事项均已完成'
  const parts: string[] = []
  if (overdue) parts.push(`${overdue} 项已逾期`)
  if (pending) parts.push(`${pending} 项未完成`)
  return parts.join('，')
})

function getStatusColor(status: string): string {
  const s = status || ''
  if (s.includes('逾期') || s.includes('超期')) return STATUS_COLORS.danger
  if (s.includes('待') || s.includes('补正')) return STATUS_COLORS.pending
  if (s.includes('完成') || s.includes('办结') || s.includes('通过')) return STATUS_COLORS.normal
  return STATUS_COLORS.processing
}

function cardColor(label: string): string {
  if (label.includes('异常') || label.includes('逾期') || label.includes('未完成')) return STATUS_COLORS.danger
  if (label.includes('已完成')) return STATUS_COLORS.normal
  return THEME_COLOR
}

function handleRowClick(row: ApprovalRow) {
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
  if ((e.target as HTMLElement).classList.contains('g01-overlay')) {
    emit('close')
  }
}

function selectFocus(objectId?: number | null) {
  if (objectId != null) {
    const hit = rawRows.value.find(r => r.objectId === objectId)
    if (hit) {
      selectedRowId.value = hit.rowId
      return
    }
  }
  selectedRowId.value = sortedRows.value[0]?.rowId || null
}

async function loadData(objectId?: number | null) {
  loading.value = true
  loadError.value = ''
  try {
    const resp = await getDashboardKpiDetail('G01') as any
    if (!resp) {
      loadError.value = '合规审批数据暂不可用（网络或服务未就绪）'
      rawRows.value = []
      summaryCards.value = []
      return
    }
    const cards = demoDetailSummaryList(resp)
    summaryCards.value = cards.length
      ? cards.map(c => ({ ...c, color: cardColor(c.label) }))
      : []
    if (!summaryCards.value.length && resp.summary && typeof resp.summary === 'object' && !Array.isArray(resp.summary)) {
      const s = resp.summary
      summaryCards.value = [
        { label: '审批事项', value: s.total ?? 0, unit: '项', color: THEME_COLOR },
        { label: '已完成', value: s.completed ?? 0, unit: '项', color: STATUS_COLORS.normal },
        { label: '未完成', value: s.pending ?? 0, unit: '项', color: STATUS_COLORS.pending },
        { label: '异常', value: s.abnormal ?? 0, unit: '项', color: STATUS_COLORS.danger },
      ]
    }

    const list: any[] = resp.detailData?.length
      ? resp.detailData
      : (resp.objects || []).map((o: any) => ({
          name: o.objectName,
          type: o.fields?.approvalType || o.fields?.catalogName || '报批报建',
          status: demoBizStatusLabel(o.status),
          deadline: o.fields?.deadline || '—',
          department: o.fields?.responsibleUnit || '—',
          progress: demoBizStatusLabel(o.fields?.progress || o.status),
          objectId: o.objectId,
        }))

    rawRows.value = list.map((item, index) => ({
      rowId: `G01-D-${item.objectId ?? index + 1}`,
      objectId: item.objectId != null ? Number(item.objectId) : undefined,
      name: item.name || '未命名事项',
      type: item.type || '报批报建',
      status: demoBizStatusLabel(item.status),
      deadline: item.deadline || '—',
      department: item.department || '—',
      progress: demoBizStatusLabel(item.progress || item.status),
    }))
    dataSource.value = resp.dataSource || 'biz_project_approval + biz_approval_catalog'
    updateTime.value = resp.updateTime || ''
    selectFocus(objectId ?? props.focusObjectId)
  } catch (e) {
    loadError.value = e instanceof Error ? e.message : '加载失败'
    rawRows.value = []
  } finally {
    loading.value = false
    await nextTick()
    initChart()
  }
}

function initChart() {
  if (!chartRef.value) return
  chart?.dispose()
  chart = echarts.init(chartRef.value)

  const list = statusDistribution.value.length
    ? statusDistribution.value
    : [{ name: '暂无', value: 0, color: STATUS_COLORS.muted }]
  const yAxisData = [...list].reverse().map(d => d.name)
  const values = [...list].reverse().map(d => d.value)
  const colors = [...list].reverse().map(d => d.color)
  const actualMax = Math.max(...values, 0)
  const xAxisMax = Math.max(2, Math.ceil(actualMax * 1.15))

  chart.setOption({
    animation: !isAcceptanceMode,
    animationDuration: 450,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(5,18,38,0.92)',
      borderColor: 'rgba(166,108,255,0.3)',
      textStyle: { color: '#e8f3ff', fontSize: 13 },
      formatter: (params: any[]) => {
        const name = params[0]?.axisValue ?? ''
        const value = params[0]?.value ?? 0
        const total = list.reduce((sum, d) => sum + d.value, 0) || 1
        const pct = ((value / total) * 100).toFixed(1)
        return `${name}<br/>数量：${value} 项<br/>占比：${pct}%`
      },
    },
    grid: { left: 72, right: 50, top: 10, bottom: 24 },
    xAxis: {
      type: 'value',
      max: xAxisMax,
      minInterval: 1,
      axisLine: { show: false },
      axisLabel: {
        color: '#8fa9c8',
        fontSize: 13,
        formatter: (v: number) => (Number.isInteger(v) ? v : ''),
      },
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
          itemStyle: { color: colors[i], borderRadius: [0, 3, 3, 0] },
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

watch(() => props.focusObjectId, (id) => {
  if (id != null && rawRows.value.length) selectFocus(id)
})
watch(() => rawRows.value.length, () => nextTick(initChart), { immediate: false })

onMounted(() => {
  updateScale()
  nextTick(() => { modalRef.value?.focus() })
  window.addEventListener('resize', handleResize)
  window.addEventListener('keydown', handleKeydown)
  void loadData(props.focusObjectId)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleKeydown)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div class="g01-overlay" :class="{ acceptance: isAcceptanceMode }" @click="handleOverlayClick">
    <div
      ref="modalRef"
      class="g01-modal"
      :class="{ acceptance: isAcceptanceMode }"
      :style="{ '--g01-scale': scale }"
      role="dialog"
      aria-modal="true"
      aria-labelledby="g01-modal-title"
      tabindex="-1"
    >
      <header class="g01-header">
        <h2 id="g01-modal-title">
          <span class="title-key">G01</span>
          <span class="title-name">合规审批事项</span>
        </h2>
        <button type="button" aria-label="关闭" @click="emit('close')">
          <X :size="22" />
        </button>
      </header>

      <section class="g01-summary" aria-label="G01摘要">
        <div v-for="item in summaryCards" :key="item.label" class="summary-card">
          <span class="summary-label">{{ item.label }}</span>
          <div class="summary-value-row">
            <strong :style="{ color: item.color || '#a66cff' }">{{ item.value }}</strong>
            <small v-if="item.unit">{{ item.unit }}</small>
          </div>
        </div>
      </section>

      <div v-if="loading" class="g01-state">正在加载合规审批数据…</div>
      <div v-else-if="loadError" class="g01-state is-error">
        {{ loadError }}
        <button type="button" class="retry-btn" @click="loadData(focusObjectId)">重试</button>
      </div>

      <main v-else class="g01-content">
        <div class="g01-main">
          <section class="panel chart-panel">
            <h3>办理状态分布</h3>
            <div ref="chartRef" class="g01-chart" />
          </section>

          <section class="panel table-panel">
            <div class="panel-heading">
              <h3>报批报建明细</h3>
              <span class="panel-sub">共 {{ rawRows.length }} 项</span>
            </div>
            <div class="table-scroll">
              <table class="approval-table">
                <colgroup>
                  <col style="width: 28%" />
                  <col style="width: 13%" />
                  <col style="width: 13%" />
                  <col style="width: 13%" />
                  <col style="width: 15%" />
                  <col style="width: 10%" />
                  <col style="width: 8%" />
                </colgroup>
                <thead>
                  <tr>
                    <th class="col-left">事项名称</th>
                    <th class="col-center">审批类型</th>
                    <th class="col-center">当前状态</th>
                    <th class="col-center">完成时限</th>
                    <th class="col-left">责任部门</th>
                    <th class="col-center">办理进度</th>
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
                    <td class="col-center">{{ row.type || '—' }}</td>
                    <td class="col-center">
                      <span
                        class="status-tag"
                        :style="{ color: getStatusColor(row.status), borderColor: getStatusColor(row.status) }"
                      >{{ row.status || '—' }}</span>
                    </td>
                    <td class="col-center">{{ row.deadline || '—' }}</td>
                    <td :title="row.department" class="col-left">{{ row.department || '—' }}</td>
                    <td class="col-center">{{ row.progress || '—' }}</td>
                    <td class="col-center">
                      <button type="button" class="row-action" @click.stop="handleRowClick(row)">
                        查看详情
                      </button>
                    </td>
                  </tr>
                  <tr v-if="sortedRows.length === 0">
                    <td colspan="7" class="empty-row">当前周期无报批报建记录</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>

        <aside class="g01-side">
          <section class="panel node-panel">
            <h3>审批类型分布（项）</h3>
            <ul class="node-list">
              <li v-for="item in nodeImpact" :key="item.name">
                <span class="node-label" :title="item.name">{{ item.name }}</span>
                <div class="node-bar-wrap">
                  <div
                    class="node-bar"
                    :style="{ width: `${Math.min(100, (item.value / Math.max(rawRows.length, 1)) * 100)}%` }"
                  ></div>
                </div>
                <span class="node-value">{{ item.value }}</span>
              </li>
              <li v-if="!nodeImpact.length" class="node-label">暂无分布</li>
            </ul>
          </section>

          <section class="panel selected-panel">
            <h3>选中事项详情</h3>
            <template v-if="selectedRow">
              <ul class="detail-list">
                <li>
                  <span class="detail-label">事项名称</span>
                  <span class="detail-value" :title="selectedRow.name">{{ selectedRow.name }}</span>
                </li>
                <li>
                  <span class="detail-label">审批类型</span>
                  <span class="detail-value">{{ selectedRow.type || '—' }}</span>
                </li>
                <li>
                  <span class="detail-label">当前状态</span>
                  <span class="detail-value">
                    <span
                      class="status-tag"
                      :style="{ color: getStatusColor(selectedRow.status), borderColor: getStatusColor(selectedRow.status) }"
                    >{{ selectedRow.status || '—' }}</span>
                  </span>
                </li>
                <li>
                  <span class="detail-label">完成时限</span>
                  <span class="detail-value">{{ selectedRow.deadline || '—' }}</span>
                </li>
                <li>
                  <span class="detail-label">责任部门</span>
                  <span class="detail-value" :title="selectedRow.department">{{ selectedRow.department || '—' }}</span>
                </li>
                <li>
                  <span class="detail-label">办理进度</span>
                  <span class="detail-value">{{ selectedRow.progress || '—' }}</span>
                </li>
                <li v-if="selectedRow.objectId != null">
                  <span class="detail-label">对象 ID</span>
                  <span class="detail-value">{{ selectedRow.objectId }}</span>
                </li>
              </ul>
            </template>
            <div v-else class="side-empty">
              <AlertTriangle :size="22" />
              <p>未选择记录</p>
              <small>点击明细记录查看事项详情</small>
            </div>
          </section>

          <div class="alert-banner purple">
            <AlertTriangle :size="14" />
            <span>{{ alertText }}</span>
          </div>
        </aside>
      </main>

      <footer class="g01-footer">
        <div class="footer-info" title="正式接口：/api/dashboard/kpi/G01">
          <FileCheck :size="13" />
          <span>数据来源：{{ dataSource }}</span>
        </div>
        <div class="footer-info">
          <Clock :size="13" />
          <span>更新时间：{{ updateTime || '—' }}</span>
        </div>
        <button type="button" class="btn-primary" @click="emit('close')">关闭</button>
      </footer>
    </div>
  </div>
</template>

<style scoped lang="scss">
.g01-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: rgba(2, 11, 24, 0.76);
  backdrop-filter: blur(4px);
  animation: g01Fade 0.2s ease;

  &.acceptance { animation: none; }
}

.g01-modal {
  width: 1436px;
  height: 880px;
  flex: 0 0 1436px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(166, 108, 255, 0.35);
  border-radius: 8px;
  outline: none;
  background: linear-gradient(180deg, #07182b, #04101f);
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.64);
  color: #e8f3ff;
  transform: scale(var(--g01-scale));
  transform-origin: center;
  animation: g01Rise 0.25s ease;

  &.acceptance,
  &.acceptance * {
    animation: none !important;
    transition: none !important;
  }

  &:focus,
  &:focus-visible { outline: none; }
}

.g01-header {
  height: 60px;
  flex: 0 0 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
  padding: 0 16px;
  border-bottom: 1px solid rgba(166, 108, 255, 0.16);

  h2 {
    margin: 0;
    display: flex;
    align-items: baseline;
    gap: 12px;
    font-size: 22px;
    font-weight: 600;
    color: #e8f3ff;

    .title-key {
      color: #a66cff;
      font-family: "DIN Alternate", "Roboto Condensed", sans-serif;
      font-size: 26px;
      font-weight: 700;
      text-shadow: 0 0 8px rgba(166, 108, 255, 0.4);
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
      background: rgba(166, 108, 255, 0.08);
      color: #e8f3ff;
      outline: 1px solid rgba(166, 108, 255, 0.28);
    }
  }
}

.g01-summary {
  flex: 0 0 88px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
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
    border: 1px solid rgba(166, 108, 255, 0.15);
    border-radius: 5px;
    background: rgba(166, 108, 255, 0.035);

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

.g01-content {
  min-height: 0;
  flex: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 12px;
  box-sizing: border-box;
  padding: 12px 16px;
}

.g01-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #8fa9c8;
  font-size: 14px;
  &.is-error { color: #ffb0b6; }
}
.retry-btn {
  border: 1px solid rgba(166, 108, 255, 0.35);
  background: rgba(166, 108, 255, 0.08);
  color: #e8f3ff;
  border-radius: 4px;
  padding: 6px 14px;
  cursor: pointer;
}

.g01-main,
.g01-side {
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
  border: 1px solid rgba(166, 108, 255, 0.15);
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

.g01-chart {
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
    background: rgba(166, 108, 255, 0.2);
    border-radius: 3px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
}

.approval-table {
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
      background: rgba(166, 108, 255, 0.04);
    }

    &.row-selected {
      background: rgba(166, 108, 255, 0.08);
      box-shadow: inset 2px 0 0 #a66cff;
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
  width: 64px;
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
  border: 1px solid rgba(166, 108, 255, 0.3);
  border-radius: 3px;
  background: rgba(166, 108, 255, 0.06);
  color: #b8cce3;
  font-size: 12px;
  line-height: 24px;
  cursor: pointer;

  &:hover {
    background: rgba(166, 108, 255, 0.15);
    color: #e8f3ff;
  }
}

.node-panel {
  flex: 0 0 auto;
  padding: 10px 12px;
}

.node-list {
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

  .node-label {
    width: 72px;
    color: #b8cce3;
    flex-shrink: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .node-bar-wrap {
    flex: 1;
    height: 6px;
    background: rgba(143, 169, 200, 0.08);
    border-radius: 3px;
    overflow: hidden;
  }

  .node-bar {
    height: 100%;
    background: linear-gradient(90deg, #a66cff, rgba(166, 108, 255, 0.4));
    border-radius: 3px;
    transition: width 0.3s;
  }

  .node-value {
    width: 24px;
    text-align: right;
    color: #d9e7f5;
    font-weight: 500;
    font-variant-numeric: tabular-nums;
    flex-shrink: 0;
  }
}

.selected-panel {
  flex: 1;
  padding: 10px 12px;
  overflow: hidden;
}

.detail-list {
  list-style: none;
  padding: 0;
  margin: 10px 0 0;
  display: flex;
  flex-direction: column;
  gap: 8px;

  li {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    padding: 6px 8px;
    border: 1px solid rgba(143, 169, 200, 0.08);
    border-radius: 3px;
    background: rgba(255, 255, 255, 0.01);
  }

  .detail-label {
    width: 72px;
    color: #8fa9c8;
    flex-shrink: 0;
  }

  .detail-value {
    flex: 1;
    color: #d9e7f5;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
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

.alert-banner {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid rgba(255, 79, 94, 0.3);
  border-radius: 4px;
  background: rgba(255, 79, 94, 0.06);
  color: #ffb0b6;
  font-size: 13px;
  line-height: 18px;

  &.purple {
    border-color: rgba(166, 108, 255, 0.3);
    background: rgba(166, 108, 255, 0.06);
    color: #c9b3ff;
  }
}

.g01-footer {
  height: 52px;
  flex: 0 0 52px;
  display: flex;
  align-items: center;
  gap: 18px;
  box-sizing: border-box;
  padding: 0 16px;
  border-top: 1px solid rgba(166, 108, 255, 0.12);

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
    border: 1px solid rgba(166, 108, 255, 0.35);
    border-radius: 4px;
    background: rgba(166, 108, 255, 0.08);
    color: #e8f3ff;
    font-size: 14px;
    cursor: pointer;

    &:hover,
    &:focus-visible {
      background: rgba(166, 108, 255, 0.15);
      outline: none;
    }
  }
}

@keyframes g01Fade {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes g01Rise {
  from {
    opacity: 0;
    transform: translateY(12px) scale(var(--g01-scale));
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(var(--g01-scale));
  }
}
</style>
