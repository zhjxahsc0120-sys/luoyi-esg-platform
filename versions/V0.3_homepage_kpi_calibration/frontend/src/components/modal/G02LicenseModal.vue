<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { Clock, FileCheck, X, AlertTriangle } from 'lucide-vue-next'
import { getDashboardKpiDetail } from '@/services/api'
import { demoBizStatusLabel, demoDetailSummaryList } from '@/utils/esg-demo'

const THEME_COLOR = '#a66cff'

const STATUS_COLORS = {
  normal: '#69e36f',
  processing: '#2f9cff',
  pending: '#ffb347',
  danger: '#ff4f5e',
  muted: '#8ba6c3',
} as const

interface LicenseRow {
  rowId: string
  objectId?: number
  name: string
  number: string
  type: string
  deadline: string
  department: string
  status: string
  approvalStatus?: string
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
const dataSource = ref('biz_permit + biz_night_construction_record')
const updateTime = ref('')
const selectedRowId = ref<string | null>(null)
const rawRows = ref<LicenseRow[]>([])

const selectedRow = computed<LicenseRow | null>(() => {
  if (!selectedRowId.value) return null
  return sortedRows.value.find(r => r.rowId === selectedRowId.value) || null
})

const sortedRows = computed<LicenseRow[]>(() => {
  return [...rawRows.value].sort((a, b) => {
    const rank = (s: string) => (s.includes('逾期') ? 0 : s.includes('临期') ? 1 : 2)
    const d = rank(a.status) - rank(b.status)
    if (d !== 0) return d
    return a.deadline.localeCompare(b.deadline)
  })
})

/** Derive expiry buckets from live rows — no hardcoded Demo chart. */
const bucketData = computed(() => {
  const buckets = [
    { name: '已逾期', value: 0, color: STATUS_COLORS.danger },
    { name: '临期/7日内', value: 0, color: STATUS_COLORS.pending },
    { name: '有效', value: 0, color: STATUS_COLORS.normal },
    { name: '待审批', value: 0, color: STATUS_COLORS.processing },
    { name: '其他', value: 0, color: STATUS_COLORS.muted },
  ]
  for (const row of rawRows.value) {
    const s = row.status || ''
    if (s.includes('逾期')) buckets[0].value += 1
    else if (s.includes('临期')) buckets[1].value += 1
    else if (s.includes('有效') || s.includes('正常')) buckets[2].value += 1
    else if (s.includes('待')) buckets[3].value += 1
    else buckets[4].value += 1
  }
  return buckets.filter(b => b.value > 0 || rawRows.value.length === 0)
})

const warningData = computed(() => {
  const map = new Map<string, number>()
  for (const row of rawRows.value) {
    const key = row.type || '许可证'
    map.set(key, (map.get(key) || 0) + 1)
  }
  return Array.from(map.entries()).map(([name, value]) => ({ name, value }))
})

const alertText = computed(() => {
  const overdue = rawRows.value.filter(r => r.status.includes('逾期')).length
  const expiring = rawRows.value.filter(r => r.status.includes('临期')).length
  if (!overdue && !expiring) return '当前周期无临期/逾期许可事项'
  const parts: string[] = []
  if (overdue) parts.push(`${overdue} 项已逾期`)
  if (expiring) parts.push(`${expiring} 项临期`)
  return parts.join('，') + '，请关注续期与夜间施工审批'
})

function getStatusColor(status: string): string {
  const s = status || ''
  if (s.includes('逾期') || s.includes('超期')) return STATUS_COLORS.danger
  if (s.includes('临期') || s.includes('即将')) return STATUS_COLORS.pending
  if (s.includes('正常') || s.includes('有效')) return STATUS_COLORS.normal
  if (s.includes('待')) return STATUS_COLORS.processing
  return STATUS_COLORS.muted
}

function cardColor(label: string): string {
  if (label.includes('逾期')) return STATUS_COLORS.danger
  if (label.includes('临期')) return STATUS_COLORS.pending
  if (label.includes('有效')) return STATUS_COLORS.normal
  return THEME_COLOR
}

function handleRowClick(row: LicenseRow) {
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
  if ((e.target as HTMLElement).classList.contains('g02-overlay')) {
    emit('close')
  }
}

function selectFocusRow(objectId?: number | null) {
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
    const resp = await getDashboardKpiDetail('G02') as any
    if (!resp) {
      loadError.value = '许可及施工管控数据暂不可用（网络或服务未就绪）'
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
        { label: '许可/夜施事项', value: s.total ?? 0, unit: '项', color: THEME_COLOR },
        { label: '有效许可', value: s.valid ?? 0, unit: '项', color: STATUS_COLORS.normal },
        { label: '临期许可', value: s.expiring ?? 0, unit: '项', color: STATUS_COLORS.pending },
        { label: '逾期许可', value: s.overdue ?? 0, unit: '项', color: STATUS_COLORS.danger },
        { label: '待审批', value: s.pending ?? 0, unit: '项', color: STATUS_COLORS.processing },
      ]
    }

    const list: any[] = resp.detailData?.length
      ? resp.detailData
      : (resp.objects || []).map((o: any) => ({
          name: o.objectName,
          number: o.fields?.permitId || o.fields?.recordCode || o.objectId || '',
          type: o.objectType === 'biz_night_construction_record' ? '夜间施工许可' : '许可证',
          deadline: o.fields?.endTime || '—',
          department: o.fields?.responsibleUnit || '—',
          status: demoBizStatusLabel(o.status || o.fields?.permitStatus),
          approvalStatus: demoBizStatusLabel(o.fields?.approvalStatus),
          objectId: o.objectId,
        }))

    rawRows.value = list.map((item, index) => ({
      rowId: `G02-D-${item.objectId ?? index + 1}`,
      objectId: item.objectId != null ? Number(item.objectId) : undefined,
      name: item.name || '未命名许可',
      number: String(item.number ?? ''),
      type: item.type || '',
      deadline: item.deadline || '',
      department: item.department || '',
      status: demoBizStatusLabel(item.status),
      approvalStatus: item.approvalStatus ? demoBizStatusLabel(item.approvalStatus) : undefined,
    }))
    dataSource.value = resp.dataSource || 'biz_permit + biz_night_construction_record'
    updateTime.value = resp.updateTime || ''
    selectFocusRow(objectId ?? props.focusObjectId)
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

  const list = bucketData.value
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
        name: '到期分桶',
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
  if (id != null && rawRows.value.length) selectFocusRow(id)
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
  <div class="g02-overlay" :class="{ acceptance: isAcceptanceMode }" @click="handleOverlayClick">
    <div
      ref="modalRef"
      class="g02-modal"
      :class="{ acceptance: isAcceptanceMode }"
      :style="{ '--g02-scale': scale }"
      role="dialog"
      aria-modal="true"
      aria-labelledby="g02-modal-title"
      tabindex="-1"
    >
      <header class="g02-header">
        <h2 id="g02-modal-title">
          <span class="title-key">G02</span>
          <span class="title-name">许可及施工管控</span>
        </h2>
        <button type="button" aria-label="关闭" @click="emit('close')">
          <X :size="22" />
        </button>
      </header>

      <section class="g02-summary" aria-label="G02摘要">
        <div v-for="item in summaryCards" :key="item.label" class="summary-card">
          <span class="summary-label">{{ item.label }}</span>
          <div class="summary-value-row">
            <strong :style="{ color: item.color || '#a66cff' }">{{ item.value }}</strong>
            <small v-if="item.unit">{{ item.unit }}</small>
          </div>
        </div>
      </section>

      <div v-if="loading" class="g02-state">正在加载许可及施工管控数据…</div>
      <div v-else-if="loadError" class="g02-state is-error">
        {{ loadError }}
        <button type="button" class="retry-btn" @click="loadData(focusObjectId)">重试</button>
      </div>

      <main v-else class="g02-content">
        <div class="g02-main">
          <section class="panel chart-panel">
            <h3>许可状态分桶</h3>
            <div ref="chartRef" class="g02-chart" />
          </section>

          <section class="panel table-panel">
            <div class="panel-heading">
              <h3>许可及夜间施工明细</h3>
              <span class="panel-sub">共 {{ rawRows.length }} 项</span>
            </div>
            <div class="table-scroll">
              <table class="license-table">
                <colgroup>
                  <col style="width: 26%" />
                  <col style="width: 20%" />
                  <col style="width: 13%" />
                  <col style="width: 13%" />
                  <col style="width: 15%" />
                  <col style="width: 13%" />
                </colgroup>
                <thead>
                  <tr>
                    <th class="col-left">许可证名称</th>
                    <th class="col-left">许可证编号</th>
                    <th class="col-center">许可类型</th>
                    <th class="col-center">有效期至</th>
                    <th class="col-left">责任部门</th>
                    <th class="col-center">状态</th>
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
                    <td :title="row.number" class="col-left">{{ row.number || '—' }}</td>
                    <td class="col-center">{{ row.type || '—' }}</td>
                    <td class="col-center">{{ row.deadline || '—' }}</td>
                    <td :title="row.department" class="col-left">{{ row.department || '—' }}</td>
                    <td class="col-center">
                      <span
                        class="status-tag"
                        :style="{ color: getStatusColor(row.status), borderColor: getStatusColor(row.status) }"
                      >{{ row.status || '—' }}</span>
                    </td>
                  </tr>
                  <tr v-if="sortedRows.length === 0">
                    <td colspan="6" class="empty-row">当前周期无许可/夜间施工记录</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>

        <aside class="g02-side">
          <section class="panel warning-panel">
            <h3>类型摘要</h3>
            <ul class="warning-list">
              <li v-for="item in warningData" :key="item.name">
                <span class="warning-label">{{ item.name }}</span>
                <div class="warning-bar-wrap">
                  <div
                    class="warning-bar"
                    :style="{ width: `${Math.min(100, (item.value / Math.max(rawRows.length, 1)) * 100)}%` }"
                  ></div>
                </div>
                <span class="warning-value">{{ item.value }}</span>
              </li>
              <li v-if="!warningData.length" class="warning-empty">暂无分类数据</li>
            </ul>
          </section>

          <section class="panel selected-panel">
            <h3>选中事项详情</h3>
            <template v-if="selectedRow">
              <ul class="detail-list">
                <li>
                  <span class="detail-label">许可证名称</span>
                  <span class="detail-value" :title="selectedRow.name">{{ selectedRow.name }}</span>
                </li>
                <li>
                  <span class="detail-label">许可证编号</span>
                  <span class="detail-value" :title="selectedRow.number">{{ selectedRow.number || '—' }}</span>
                </li>
                <li>
                  <span class="detail-label">许可类型</span>
                  <span class="detail-value">{{ selectedRow.type || '—' }}</span>
                </li>
                <li>
                  <span class="detail-label">有效期至</span>
                  <span class="detail-value">{{ selectedRow.deadline || '—' }}</span>
                </li>
                <li>
                  <span class="detail-label">责任部门</span>
                  <span class="detail-value" :title="selectedRow.department">{{ selectedRow.department || '—' }}</span>
                </li>
                <li>
                  <span class="detail-label">状态</span>
                  <span class="detail-value">
                    <span
                      class="status-tag"
                      :style="{ color: getStatusColor(selectedRow.status), borderColor: getStatusColor(selectedRow.status) }"
                    >{{ selectedRow.status || '—' }}</span>
                  </span>
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
              <small>点击明细记录查看许可详情</small>
            </div>
          </section>

          <div class="alert-banner purple">
            <AlertTriangle :size="14" />
            <span>{{ alertText }}</span>
          </div>
        </aside>
      </main>

      <footer class="g02-footer">
        <div class="footer-info" title="正式接口：/api/dashboard/kpi/G02">
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
.g02-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: rgba(2, 11, 24, 0.76);
  backdrop-filter: blur(4px);
  animation: g02Fade 0.2s ease;

  &.acceptance { animation: none; }
}

.g02-modal {
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
  transform: scale(var(--g02-scale));
  transform-origin: center;
  animation: g02Rise 0.25s ease;

  &.acceptance,
  &.acceptance * {
    animation: none !important;
    transition: none !important;
  }

  &:focus,
  &:focus-visible { outline: none; }
}

.g02-header {
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

.g02-summary {
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

.g02-content {
  min-height: 0;
  flex: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 12px;
  box-sizing: border-box;
  padding: 12px 16px;
}

.g02-state {
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
.warning-empty {
  color: #8ba6c3;
  font-size: 13px;
  list-style: none;
}

.g02-main,
.g02-side {
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

.g02-chart {
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

.license-table {
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

.warning-panel {
  flex: 0 0 auto;
  padding: 10px 12px;
}

.warning-list {
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

  .warning-label {
    width: 96px;
    color: #b8cce3;
    flex-shrink: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .warning-bar-wrap {
    flex: 1;
    height: 6px;
    background: rgba(143, 169, 200, 0.08);
    border-radius: 3px;
    overflow: hidden;
  }

  .warning-bar {
    height: 100%;
    background: linear-gradient(90deg, #a66cff, rgba(166, 108, 255, 0.4));
    border-radius: 3px;
    transition: width 0.3s;
  }

  .warning-value {
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
    width: 80px;
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

.g02-footer {
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

@keyframes g02Fade {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes g02Rise {
  from {
    opacity: 0;
    transform: translateY(12px) scale(var(--g02-scale));
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(var(--g02-scale));
  }
}
</style>
