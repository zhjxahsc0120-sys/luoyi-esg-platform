<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { Clock, FileCheck, X, AlertTriangle } from 'lucide-vue-next'
import { getDashboardKpiDetail } from '@/services/api'
import { demoBizStatusLabel, demoDetailSummaryList } from '@/utils/esg-demo'

const THEME_COLOR = '#a66cff'

const STATUS_COLORS: Record<string, string> = {
  normal: '#69e36f',
  processing: '#2f9cff',
  pending: '#ffb347',
  danger: '#ff4f5e',
  muted: '#8ba6c3',
}

interface ComplianceRow {
  rowId: string
  objectId?: number
  name: string
  module: string
  issueLevel: string
  deadline: string
  owner: string
  status: string
  action: string
}

const props = defineProps<{ focusObjectId?: number | null }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const isAcceptanceMode = new URLSearchParams(window.location.search).get('acceptance') === '1'
const modalRef = ref<HTMLDivElement | null>(null)
const scale = ref(1)

const loading = ref(true)
const loadError = ref('')
const summaryCards = ref<Array<{ label: string; value: string | number | null; unit?: string; color?: string }>>([])
const dataSource = ref('biz_internal_control_issue')
const updateTime = ref('')
const selectedRowId = ref<string | null>(null)
const activeStatusFilter = ref<string>('全部')
const rawRows = ref<ComplianceRow[]>([])

const selectedRow = computed<ComplianceRow | null>(() => {
  if (!selectedRowId.value) return null
  return sortedRows.value.find(r => r.rowId === selectedRowId.value) || null
})

const sortedRows = computed<ComplianceRow[]>(() => {
  return [...rawRows.value].sort((a, b) => {
    const rank = (s: string) => (s.includes('未关闭') || s.includes('OPEN') ? 0 : s.includes('逾期') ? 0 : 1)
    const d = rank(a.status) - rank(b.status)
    if (d !== 0) return d
    return a.deadline.localeCompare(b.deadline)
  })
})

const statusFilterOptions = computed(() => {
  const set = new Set<string>()
  rawRows.value.forEach(r => { if (r.status) set.add(r.status) })
  return ['全部', ...Array.from(set)]
})

const filteredRows = computed<ComplianceRow[]>(() => {
  if (activeStatusFilter.value === '全部') return sortedRows.value
  return sortedRows.value.filter(r => r.status === activeStatusFilter.value)
})

const statusDistribution = computed(() => {
  const map = new Map<string, number>()
  rawRows.value.forEach(r => {
    const key = r.status || '—'
    map.set(key, (map.get(key) || 0) + 1)
  })
  return Array.from(map.entries())
    .map(([name, value]) => {
      let color = STATUS_COLORS.muted
      if (name.includes('未关闭') || name.includes('逾期') || name.includes('OPEN')) color = STATUS_COLORS.danger
      else if (name.includes('待')) color = STATUS_COLORS.pending
      else if (name.includes('已关闭') || name.includes('CLOSED')) color = STATUS_COLORS.normal
      return { name, value, color }
    })
    .sort((a, b) => b.value - a.value)
})

const moduleDistribution = computed(() => {
  const map = new Map<string, number>()
  rawRows.value.forEach(r => {
    const key = r.module || '—'
    map.set(key, (map.get(key) || 0) + 1)
  })
  return Array.from(map.entries())
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
})

const alertText = computed(() => {
  const open = rawRows.value.filter(r => r.status.includes('未关闭')).length
  const missing = rawRows.value.filter(r => (r.action || '').includes('缺失')).length
  if (!open && !missing) return '当前周期内控事项均已关闭'
  const parts: string[] = []
  if (open) parts.push(`${open} 项未关闭`)
  if (missing) parts.push(`${missing} 项证据缺失`)
  return parts.join('，') + '，请尽快闭环'
})

function getStatusColor(status: string): string {
  const s = status || ''
  if (s.includes('未关闭') || s.includes('逾期')) return STATUS_COLORS.danger
  if (s.includes('待')) return STATUS_COLORS.pending
  if (s.includes('已关闭')) return STATUS_COLORS.normal
  return STATUS_COLORS.muted
}

function cardColor(label: string): string {
  if (label.includes('风险') || label.includes('未关闭')) return STATUS_COLORS.danger
  if (label.includes('已关闭')) return STATUS_COLORS.normal
  return THEME_COLOR
}

function handleRowClick(row: ComplianceRow) {
  selectedRowId.value = selectedRowId.value === row.rowId ? null : row.rowId
}

function setStatusFilter(filter: string) {
  activeStatusFilter.value = filter
  const first = filteredRows.value[0]
  selectedRowId.value = first ? first.rowId : null
}

function updateScale() {
  scale.value = Math.min(1, window.innerWidth / 1920, window.innerHeight / 1080)
}

function handleResize() {
  updateScale()
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

function handleOverlayClick(e: MouseEvent) {
  if ((e.target as HTMLElement).classList.contains('g04-overlay')) {
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
    const resp = await getDashboardKpiDetail('G04') as any
    if (!resp) {
      loadError.value = '内控与廉洁数据暂不可用（网络或服务未就绪）'
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
        { label: '内控事项', value: s.total ?? 0, unit: '项', color: THEME_COLOR },
        { label: '未关闭', value: s.open ?? 0, unit: '项', color: STATUS_COLORS.danger },
        { label: '已关闭', value: s.closed ?? 0, unit: '项', color: STATUS_COLORS.normal },
        { label: '风险事项', value: s.abnormal ?? 0, unit: '项', color: STATUS_COLORS.danger },
      ]
    }

    const list: any[] = resp.detailData?.length
      ? resp.detailData
      : (resp.objects || []).map((o: any) => ({
          name: o.objectName,
          module: o.fields?.issueType || '内控廉洁',
          issueLevel: o.fields?.issueLevel || '—',
          deadline: o.fields?.deadline || '—',
          owner: o.fields?.responsibleUnit || '—',
          status: demoBizStatusLabel(o.status),
          action: demoBizStatusLabel(o.fields?.evidenceStatus),
          objectId: o.objectId,
        }))

    rawRows.value = list.map((item, index) => ({
      rowId: `G04-D-${item.objectId ?? index + 1}`,
      objectId: item.objectId != null ? Number(item.objectId) : undefined,
      name: item.name || '未命名事项',
      module: item.module || '',
      issueLevel: item.issueLevel || '—',
      deadline: item.deadline || '',
      owner: item.owner || '',
      status: demoBizStatusLabel(item.status),
      action: demoBizStatusLabel(item.action),
    }))
    dataSource.value = resp.dataSource || 'biz_internal_control_issue'
    updateTime.value = resp.updateTime || ''
    activeStatusFilter.value = '全部'
    selectFocus(objectId ?? props.focusObjectId)
  } catch (e) {
    loadError.value = e instanceof Error ? e.message : '加载失败'
    rawRows.value = []
  } finally {
    loading.value = false
    await nextTick()
  }
}

watch(() => props.focusObjectId, (id) => {
  if (id != null && rawRows.value.length) selectFocus(id)
})

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
})
</script>

<template>
  <div class="g04-overlay" :class="{ acceptance: isAcceptanceMode }" @click="handleOverlayClick">
    <div
      ref="modalRef"
      class="g04-modal"
      :class="{ acceptance: isAcceptanceMode }"
      :style="{ '--g04-scale': scale }"
      role="dialog"
      aria-modal="true"
      aria-labelledby="g04-modal-title"
      tabindex="-1"
    >
      <header class="g04-header">
        <h2 id="g04-modal-title">
          <span class="title-key">G04</span>
          <span class="title-name">内控与廉洁</span>
        </h2>
        <button type="button" aria-label="关闭" @click="emit('close')">
          <X :size="22" />
        </button>
      </header>

      <section class="g04-summary" aria-label="G04摘要">
        <div v-for="item in summaryCards" :key="item.label" class="summary-card">
          <span class="summary-label">{{ item.label }}</span>
          <div class="summary-value-row">
            <strong :style="{ color: item.color || '#a66cff' }">{{ item.value === null || item.value === undefined ? '--' : item.value }}</strong>
            <small v-if="item.unit && item.value !== null && item.value !== undefined">{{ item.unit }}</small>
          </div>
        </div>
      </section>

      <div v-if="loading" class="g04-state">正在加载内控与廉洁数据…</div>
      <div v-else-if="loadError" class="g04-state is-error">
        {{ loadError }}
        <button type="button" class="retry-btn" @click="loadData(focusObjectId)">重试</button>
      </div>

      <main v-else class="g04-content">
        <div class="g04-main">
          <section class="panel table-panel">
            <div class="panel-heading">
              <h3>内控廉洁问题清单</h3>
              <div class="filter-row">
                <button
                  v-for="opt in statusFilterOptions"
                  :key="opt"
                  type="button"
                  class="filter-chip"
                  :class="{ active: activeStatusFilter === opt }"
                  @click="setStatusFilter(opt)"
                >{{ opt }}</button>
                <span class="panel-sub">共 {{ filteredRows.length }} 项</span>
              </div>
            </div>
            <div class="table-scroll">
              <table class="compliance-table">
                <colgroup>
                  <col style="width: 28%" />
                  <col style="width: 14%" />
                  <col style="width: 10%" />
                  <col style="width: 14%" />
                  <col style="width: 14%" />
                  <col style="width: 10%" />
                  <col style="width: 10%" />
                </colgroup>
                <thead>
                  <tr>
                    <th class="col-left">问题描述</th>
                    <th class="col-center">问题类型</th>
                    <th class="col-center">等级</th>
                    <th class="col-center">办理时限</th>
                    <th class="col-left">责任单位</th>
                    <th class="col-center">状态</th>
                    <th class="col-center">证据</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="row in filteredRows"
                    :key="row.rowId"
                    :class="{ 'row-selected': selectedRowId === row.rowId }"
                    @click="handleRowClick(row)"
                  >
                    <td :title="row.name" class="cell-name col-left">{{ row.name }}</td>
                    <td class="col-center">
                      <span class="module-tag" :title="row.module">{{ row.module || '—' }}</span>
                    </td>
                    <td class="col-center">{{ row.issueLevel || '—' }}</td>
                    <td class="col-center">{{ row.deadline || '—' }}</td>
                    <td :title="row.owner" class="col-left">{{ row.owner || '—' }}</td>
                    <td class="col-center">
                      <span
                        class="status-tag"
                        :style="{ color: getStatusColor(row.status), borderColor: getStatusColor(row.status) }"
                      >{{ row.status || '—' }}</span>
                    </td>
                    <td class="col-center">{{ row.action || '—' }}</td>
                  </tr>
                  <tr v-if="filteredRows.length === 0">
                    <td colspan="7" class="empty-row">当前周期无内控廉洁问题记录</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>

        <aside class="g04-side">
          <section class="panel status-panel">
            <h3>问题状态构成</h3>
            <ul class="status-list">
              <li v-for="item in statusDistribution" :key="item.name">
                <span class="status-dot" :style="{ background: item.color }"></span>
                <span class="status-label">{{ item.name }}</span>
                <span class="status-value" :style="{ color: item.color }">{{ item.value }}</span>
              </li>
              <li v-if="!statusDistribution.length" class="status-label">暂无分布数据</li>
            </ul>
          </section>

          <section class="panel module-panel">
            <h3>问题类型分布（项）</h3>
            <ul class="module-list">
              <li v-for="item in moduleDistribution" :key="item.name">
                <span class="module-label" :title="item.name">{{ item.name }}</span>
                <div class="module-bar-wrap">
                  <div
                    class="module-bar"
                    :style="{ width: `${Math.min(100, (item.value / Math.max(rawRows.length, 1)) * 100)}%` }"
                  ></div>
                </div>
                <span class="module-value">{{ item.value }}</span>
              </li>
            </ul>
          </section>

          <section class="panel selected-panel">
            <h3>选中问题详情</h3>
            <template v-if="selectedRow">
              <ul class="detail-list">
                <li>
                  <span class="detail-label">问题描述</span>
                  <span class="detail-value" :title="selectedRow.name">{{ selectedRow.name }}</span>
                </li>
                <li>
                  <span class="detail-label">问题类型</span>
                  <span class="detail-value">{{ selectedRow.module || '—' }}</span>
                </li>
                <li>
                  <span class="detail-label">问题等级</span>
                  <span class="detail-value">{{ selectedRow.issueLevel || '—' }}</span>
                </li>
                <li>
                  <span class="detail-label">办理时限</span>
                  <span class="detail-value">{{ selectedRow.deadline || '—' }}</span>
                </li>
                <li>
                  <span class="detail-label">责任单位</span>
                  <span class="detail-value" :title="selectedRow.owner">{{ selectedRow.owner || '—' }}</span>
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
                  <span class="detail-label">证据状态</span>
                  <span class="detail-value">{{ selectedRow.action || '—' }}</span>
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
              <small>点击明细记录查看内控问题详情</small>
            </div>
          </section>

          <div class="alert-banner purple">
            <AlertTriangle :size="14" />
            <span>{{ alertText }}</span>
          </div>
        </aside>
      </main>

      <footer class="g04-footer">
        <div class="footer-info" title="正式接口：/api/dashboard/kpi/G04">
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
.g04-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: rgba(2, 11, 24, 0.76);
  backdrop-filter: blur(4px);
  animation: g04Fade 0.2s ease;

  &.acceptance { animation: none; }
}

.g04-modal {
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
  transform: scale(var(--g04-scale));
  transform-origin: center;
  animation: g04Rise 0.25s ease;

  &.acceptance,
  &.acceptance * {
    animation: none !important;
    transition: none !important;
  }

  &:focus,
  &:focus-visible { outline: none; }
}

.g04-header {
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

.g04-summary {
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

.g04-content {
  min-height: 0;
  flex: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 12px;
  box-sizing: border-box;
  padding: 12px 16px;
}

.g04-state {
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

.module-tag {
  display: inline-flex;
  max-width: 100%;
  height: 22px;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  padding: 0 6px;
  border: 1px solid rgba(166, 108, 255, 0.3);
  border-radius: 3px;
  background: rgba(166, 108, 255, 0.08);
  color: #c9b3ff;
  font-size: 12px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.module-label {
  width: 96px;
  color: #b8cce3;
  flex-shrink: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.g04-main,
.g04-side {
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

.table-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-heading {
  min-height: 38px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  box-sizing: border-box;
  padding: 6px 12px;
  border-bottom: 1px solid rgba(143, 169, 200, 0.1);

  h3 { font-size: 15px; }

  .filter-row {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }

  .filter-chip {
    height: 24px;
    padding: 0 10px;
    border: 1px solid rgba(143, 169, 200, 0.2);
    border-radius: 12px;
    background: transparent;
    color: #b8cce3;
    font-size: 12px;
    cursor: pointer;

    &:hover {
      border-color: rgba(166, 108, 255, 0.4);
      color: #e8f3ff;
    }

    &.active {
      border-color: #a66cff;
      background: rgba(166, 108, 255, 0.12);
      color: #e8f3ff;
    }
  }

  .panel-sub {
    font-size: 13px;
    color: #8fa9c8;
    margin-left: 4px;
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

.compliance-table {
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

.status-panel {
  flex: 0 0 auto;
  padding: 10px 12px;
}

.status-list {
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
    padding: 4px 0;
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .status-label {
    flex: 1;
    color: #b8cce3;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .status-value {
    width: 28px;
    text-align: right;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    flex-shrink: 0;
  }
}

.module-panel {
  flex: 0 0 auto;
  padding: 10px 12px;
}

.module-list {
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

  .module-label {
    width: 96px;
    color: #b8cce3;
    flex-shrink: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .module-bar-wrap {
    flex: 1;
    height: 6px;
    background: rgba(143, 169, 200, 0.08);
    border-radius: 3px;
    overflow: hidden;
  }

  .module-bar {
    height: 100%;
    background: linear-gradient(90deg, #a66cff, rgba(166, 108, 255, 0.4));
    border-radius: 3px;
    transition: width 0.3s;
  }

  .module-value {
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

.g04-footer {
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

@keyframes g04Fade {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes g04Rise {
  from {
    opacity: 0;
    transform: translateY(12px) scale(var(--g04-scale));
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(var(--g04-scale));
  }
}
</style>
