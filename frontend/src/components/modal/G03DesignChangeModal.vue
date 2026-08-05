<script setup lang="ts">
/**
 * G03 设计变更管理 — Demo 契约：biz_design_change
 * 禁止绑定整改 / 履约评价语义。
 */
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { getDashboardKpiDetail } from '@/services/api'
import { demoBizStatusLabel, demoDetailSummaryList } from '@/utils/esg-demo'

const props = defineProps<{ focusObjectId?: number | null }>()
const emit = defineEmits<{ (e: 'close'): void }>()

type ChangeRow = {
  rowId: string
  objectId?: number
  name: string
  changeType: string
  approveStatus: string
  implementation: string
  attachment: string
  status: string
  locationDesc?: string
  riskLevel?: string
}

const loading = ref(true)
const loadError = ref('')
const dataSource = ref('biz_design_change')
const updateTime = ref('')
const summaryCards = ref<Array<{ label: string; value: string | number; unit?: string }>>([])
const rows = ref<ChangeRow[]>([])
const selectedId = ref<string | null>(null)

const selected = computed(() => rows.value.find((r) => r.rowId === selectedId.value) || null)

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

function selectFocus(objectId?: number | null) {
  if (objectId != null) {
    const hit = rows.value.find((r) => r.objectId === objectId)
    if (hit) {
      selectedId.value = hit.rowId
      return
    }
  }
  selectedId.value = rows.value[0]?.rowId || null
}

async function loadData(objectId?: number | null) {
  loading.value = true
  loadError.value = ''
  try {
    const resp = (await getDashboardKpiDetail('G03')) as any
    if (!resp) {
      loadError.value = '设计变更数据暂不可用（网络或服务未就绪）'
      rows.value = []
      summaryCards.value = []
      return
    }
    summaryCards.value = demoDetailSummaryList(resp)
    if (!summaryCards.value.length && resp.summary && !Array.isArray(resp.summary)) {
      const s = resp.summary
      summaryCards.value = [
        { label: '设计变更', value: s.total ?? 0, unit: '项' },
        { label: '待审批', value: s.pending ?? 0, unit: '项' },
        { label: '异常/风险', value: s.abnormal ?? 0, unit: '项' },
      ]
    }
    const list: any[] = resp.detailData?.length
      ? resp.detailData
      : (resp.objects || []).map((o: any) => ({
          name: o.objectName,
          changeType: o.fields?.changeType || '设计变更',
          approveStatus: demoBizStatusLabel(o.fields?.approveStatus || o.status),
          implementation: demoBizStatusLabel(o.fields?.implementationStatus || '—'),
          attachment: demoBizStatusLabel(o.fields?.attachmentStatus || '—'),
          status: demoBizStatusLabel(o.status),
          locationDesc: o.fields?.locationDesc,
          objectId: o.objectId,
          riskLevel: o.riskLevel,
        }))
    rows.value = list.map((item, index) => ({
      rowId: `G03-${item.objectId ?? index + 1}`,
      objectId: item.objectId != null ? Number(item.objectId) : undefined,
      name: item.name || '未命名变更',
      changeType: item.changeType || '设计变更',
      approveStatus: demoBizStatusLabel(item.approveStatus || item.status),
      implementation: demoBizStatusLabel(item.implementation),
      attachment: demoBizStatusLabel(item.attachment),
      status: demoBizStatusLabel(item.status || item.approveStatus),
      locationDesc: item.locationDesc,
      riskLevel: item.riskLevel,
    }))
    dataSource.value = resp.dataSource || 'biz_design_change'
    updateTime.value = resp.updateTime || ''
    selectFocus(objectId ?? props.focusObjectId)
  } catch (e) {
    loadError.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

watch(() => props.focusObjectId, (id) => {
  if (id != null && rows.value.length) selectFocus(id)
})

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  void loadData(props.focusObjectId)
})
onUnmounted(() => window.removeEventListener('keydown', handleKeydown))

defineExpose({ reload: loadData })
</script>

<template>
  <div class="g03-change-modal" role="dialog" aria-label="设计变更管理">
    <header class="modal-head">
      <div class="title-row">
        <span class="title-key">G03</span>
        <span class="title-name">设计变更管理</span>
      </div>
      <button type="button" class="close-btn" @click="emit('close')">关闭</button>
    </header>

    <div v-if="loading" class="state">正在加载…</div>
    <div v-else-if="loadError" class="state is-error">
      {{ loadError }}
      <button type="button" class="retry" @click="loadData(focusObjectId)">重试</button>
    </div>
    <template v-else>
      <section class="summary" aria-label="G03摘要">
        <div v-for="card in summaryCards" :key="card.label" class="metric">
          <span class="label">{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
          <span v-if="card.unit" class="unit">{{ card.unit }}</span>
        </div>
      </section>

      <section class="body">
        <div class="list-pane">
          <h3>设计变更清单</h3>
          <button
            v-for="row in rows"
            :key="row.rowId"
            type="button"
            class="row"
            :class="{ active: selectedId === row.rowId }"
            @click="selectedId = selectedId === row.rowId ? null : row.rowId"
          >
            <div class="row-top">
              <span>{{ row.changeType }}</span>
              <em>{{ row.approveStatus }}</em>
            </div>
            <div class="row-title">{{ row.name }}</div>
            <div class="row-meta">
              <span>实施 {{ row.implementation }}</span>
              <span>附件 {{ row.attachment }}</span>
            </div>
          </button>
          <div v-if="!rows.length" class="empty">当前周期无设计变更记录</div>
        </div>
        <div class="detail-pane">
          <h3>变更详情</h3>
          <template v-if="selected">
            <dl>
              <div><dt>名称</dt><dd>{{ selected.name }}</dd></div>
              <div><dt>类型</dt><dd>{{ selected.changeType }}</dd></div>
              <div><dt>审批状态</dt><dd>{{ selected.approveStatus }}</dd></div>
              <div><dt>实施状态</dt><dd>{{ selected.implementation }}</dd></div>
              <div><dt>附件状态</dt><dd>{{ selected.attachment }}</dd></div>
              <div v-if="selected.locationDesc"><dt>位置</dt><dd>{{ selected.locationDesc }}</dd></div>
              <div><dt>对象 ID</dt><dd>{{ selected.objectId ?? '—' }}</dd></div>
            </dl>
          </template>
          <div v-else class="empty">请选择左侧变更项</div>
        </div>
      </section>
    </template>

    <footer class="footer-info" title="正式接口：/api/dashboard/kpi/G03">
      接口：/api/dashboard/kpi/G03 · 来源：{{ dataSource }}
      <span v-if="updateTime"> · {{ updateTime }}</span>
    </footer>
  </div>
</template>

<style scoped lang="scss">
.g03-change-modal {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 420px;
  padding: 16px 18px 12px;
  color: var(--text-primary, #e8f1ff);
}
.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.title-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.title-key {
  color: #b794f6;
  font-size: 18px;
  font-weight: 700;
}
.title-name {
  font-size: 18px;
  font-weight: 650;
}
.close-btn,
.retry {
  border: 1px solid rgba(143, 176, 224, 0.35);
  background: transparent;
  color: var(--text-secondary, #9eb6d4);
  border-radius: 4px;
  padding: 4px 12px;
  cursor: pointer;
}
.summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}
.metric {
  padding: 10px 12px;
  border: 1px solid rgba(143, 176, 224, 0.25);
  border-radius: 6px;
  background: rgba(12, 28, 52, 0.55);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.metric .label {
  font-size: 12px;
  color: var(--text-tertiary, #7f99b8);
}
.metric strong {
  font-size: 22px;
  font-weight: 700;
}
.metric .unit {
  font-size: 12px;
  color: var(--text-secondary, #9eb6d4);
}
.body {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 12px;
  min-height: 260px;
}
.list-pane,
.detail-pane {
  border: 1px solid rgba(143, 176, 224, 0.2);
  border-radius: 6px;
  padding: 10px;
  background: rgba(8, 20, 40, 0.45);
  min-height: 0;
}
h3 {
  margin: 0 0 8px;
  font-size: 14px;
}
.row {
  display: block;
  width: 100%;
  text-align: left;
  border: 1px solid transparent;
  background: transparent;
  color: inherit;
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 6px;
}
.row.active,
.row:hover {
  border-color: rgba(183, 148, 246, 0.45);
  background: rgba(183, 148, 246, 0.08);
}
.row-top {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-tertiary, #7f99b8);
}
.row-title {
  font-size: 13px;
  font-weight: 600;
  margin: 4px 0;
}
.row-meta {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: var(--text-secondary, #9eb6d4);
}
.detail-pane dl {
  display: grid;
  gap: 8px;
  margin: 0;
}
.detail-pane dt {
  font-size: 11px;
  color: var(--text-tertiary, #7f99b8);
}
.detail-pane dd {
  margin: 2px 0 0;
  font-size: 13px;
}
.state,
.empty {
  color: var(--text-secondary, #9eb6d4);
  font-size: 13px;
  padding: 12px 0;
}
.state.is-error {
  color: #ffb4b4;
}
.footer-info {
  font-size: 11px;
  color: var(--text-tertiary, #7f99b8);
}
</style>
