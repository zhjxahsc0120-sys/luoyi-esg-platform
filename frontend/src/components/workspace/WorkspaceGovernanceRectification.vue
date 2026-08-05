<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ClipboardList, RefreshCw, Save } from 'lucide-vue-next'
import {
  getRectificationTask,
  getRectificationTasks,
  patchRectificationTask,
} from '@/services/api'
import type { RectificationTask } from '@/types/governance'

const loading = ref(false)
const saving = ref(false)
const pageMessage = ref('')
const pageMessageType = ref<'info' | 'success' | 'error'>('info')
const items = ref<RectificationTask[]>([])
const selectedId = ref<number | null>(null)
const detail = ref<RectificationTask | null>(null)

const filterCompleted = ref<'' | '0' | '1'>('')
const filterStatus = ref('')

const editDate = ref('')
const editBy = ref('')

const pendingLabel = '待甲方填报'

const statusCards = computed(() => {
  const total = items.value.length
  const pending = items.value.filter((t) => !t.rectificationCompletedDate).length
  const done = total - pending
  return [
    { label: '整改任务', value: total, unit: '项', color: '#2f9cff' },
    { label: '待甲方填报', value: pending, unit: '项', color: '#ffb347' },
    { label: '已填报完成日期', value: done, unit: '项', color: '#69e36f' },
  ]
})

function formatCompletedDate(value: string | null | undefined): string {
  if (!value) return pendingLabel
  return value
}

function showMessage(type: 'info' | 'success' | 'error', text: string) {
  pageMessageType.value = type
  pageMessage.value = text
}

async function loadList() {
  loading.value = true
  pageMessage.value = ''
  try {
    const res = await getRectificationTasks({
      completed: filterCompleted.value === '' ? undefined : (Number(filterCompleted.value) as 0 | 1),
      taskStatus: filterStatus.value || undefined,
    })
    items.value = res?.items || []
    if (!items.value.length) {
      selectedId.value = null
      detail.value = null
      showMessage('info', '暂无整改任务数据')
      return
    }
    const keep = selectedId.value && items.value.some((t) => t.id === selectedId.value)
    await selectTask(keep ? selectedId.value! : items.value[0].id)
  } finally {
    loading.value = false
  }
}

async function selectTask(id: number) {
  selectedId.value = id
  const res = await getRectificationTask(id)
  detail.value = res
  // Never auto-fill date: only mirror server value into editable fields.
  editDate.value = res?.rectificationCompletedDate || ''
  editBy.value = res?.rectificationCompletedBy != null ? String(res.rectificationCompletedBy) : ''
}

async function saveCompletion() {
  if (!detail.value) return
  const dateRaw = editDate.value.trim()
  const byRaw = editBy.value.trim()

  const payload: { rectificationCompletedDate: string | null; rectificationCompletedBy: number | null } = {
    rectificationCompletedDate: dateRaw ? dateRaw : null,
    rectificationCompletedBy: byRaw ? Number(byRaw) : null,
  }

  if (payload.rectificationCompletedDate && !payload.rectificationCompletedBy) {
    showMessage('error', '已填写完成日期时，必须同时填写填报人用户 ID')
    return
  }
  if (payload.rectificationCompletedBy != null && Number.isNaN(payload.rectificationCompletedBy)) {
    showMessage('error', '填报人用户 ID 必须为数字')
    return
  }

  saving.value = true
  try {
    const result = await patchRectificationTask(detail.value.id, payload)
    if (!result.ok) {
      showMessage('error', result.message || '保存失败')
      return
    }
    detail.value = result.data
    editDate.value = result.data.rectificationCompletedDate || ''
    editBy.value = result.data.rectificationCompletedBy != null ? String(result.data.rectificationCompletedBy) : ''
    const idx = items.value.findIndex((t) => t.id === result.data.id)
    if (idx >= 0) items.value[idx] = result.data
    showMessage('success', '整改完成信息已保存（未自动生成日期）')
  } finally {
    saving.value = false
  }
}

watch([filterCompleted, filterStatus], () => {
  void loadList()
})

onMounted(() => {
  void loadList()
})
</script>

<template>
  <div class="ws-page gov-rect-page">
    <div class="ws-page-header">
      <div class="ws-page-title-group">
        <h2 class="ws-page-title">治理整改</h2>
        <p class="ws-page-subtitle">整改任务台账 · 甲方填报完成日期（禁止系统自动填充）</p>
      </div>
      <div class="ws-page-header-extra">
        <button type="button" class="ws-btn ws-btn-secondary ws-btn-sm" :disabled="loading" @click="loadList">
          <RefreshCw :size="14" />
          刷新
        </button>
      </div>
    </div>

    <div v-if="pageMessage" class="ws-page-message" :class="pageMessageType">{{ pageMessage }}</div>

    <div class="ws-status-cards cols-4" style="grid-template-columns: repeat(3, minmax(0, 1fr))">
      <div v-for="card in statusCards" :key="card.label" class="ws-status-card" :style="{ '--accent-color': card.color }">
        <div class="ws-card-label">{{ card.label }}</div>
        <div class="ws-card-value-row">
          <span class="ws-card-value">{{ card.value }}</span>
          <span class="ws-card-unit">{{ card.unit }}</span>
        </div>
      </div>
    </div>

    <div class="ws-filter-bar">
      <div class="ws-filter-row">
        <span class="ws-filter-title">筛选</span>
        <select v-model="filterCompleted" class="ws-select">
          <option value="">完成日期：全部</option>
          <option value="0">仅待甲方填报</option>
          <option value="1">仅已填报</option>
        </select>
        <select v-model="filterStatus" class="ws-select">
          <option value="">任务状态：全部</option>
          <option value="PENDING">PENDING</option>
          <option value="IN_PROGRESS">IN_PROGRESS</option>
          <option value="SUBMITTED">SUBMITTED</option>
          <option value="COMPLETED">COMPLETED</option>
        </select>
      </div>
    </div>

    <div class="gov-split">
      <section class="ws-panel gov-list-panel">
        <div class="ws-panel-header">
          <div class="ws-panel-title">
            <ClipboardList :size="16" class="ws-panel-title-icon" />
            整改任务列表
          </div>
          <span class="ws-panel-count">{{ items.length }} 条</span>
        </div>
        <div class="ws-table-container">
          <div class="ws-table-scroll">
            <table class="ws-table">
              <thead>
                <tr>
                  <th>任务编号</th>
                  <th>标题</th>
                  <th>状态</th>
                  <th>完成日期</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="loading">
                  <td colspan="4" class="empty-row">加载中…</td>
                </tr>
                <tr v-else-if="!items.length">
                  <td colspan="4" class="empty-row">暂无数据</td>
                </tr>
                <tr
                  v-for="row in items"
                  v-else
                  :key="row.id"
                  :class="{ selected: row.id === selectedId }"
                  @click="selectTask(row.id)"
                >
                  <td>{{ row.taskCode }}</td>
                  <td class="col-name">{{ row.title }}</td>
                  <td><span class="ws-tag">{{ row.taskStatus }}</span></td>
                  <td :class="{ 'is-pending': !row.rectificationCompletedDate }">
                    {{ formatCompletedDate(row.rectificationCompletedDate) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <aside class="ws-detail-panel">
        <div class="ws-detail-header">
          <ClipboardList :size="16" class="ws-detail-header-icon" />
          <div class="ws-detail-title">{{ detail?.taskCode || '任务详情' }}</div>
        </div>
        <div v-if="detail" class="ws-detail-content">
          <div class="ws-section-title">基本信息</div>
          <div class="gov-kv">
            <div><span>标题</span><strong>{{ detail.title }}</strong></div>
            <div><span>状态</span><strong>{{ detail.taskStatus }}</strong></div>
            <div><span>期限</span><strong>{{ detail.deadline || '—' }}</strong></div>
            <div>
              <span>完成日期</span>
              <strong :class="{ 'is-pending': !detail.rectificationCompletedDate }">
                {{ formatCompletedDate(detail.rectificationCompletedDate) }}
              </strong>
            </div>
            <div>
              <span>填报人 ID</span>
              <strong>{{ detail.rectificationCompletedBy ?? '—' }}</strong>
            </div>
          </div>

          <div class="ws-section-title" style="margin-top: 18px">甲方填报</div>
          <p class="gov-hint">仅可修改完成日期与填报人；留空日期表示清空，界面显示「待甲方填报」。不会使用当前日期自动填充。</p>
          <div class="gov-form">
            <label>
              整改完成日期
              <input v-model="editDate" type="date" class="ws-input" />
            </label>
            <label>
              填报人用户 ID（user_account.id，当前 Demo 可用 10001）
              <input v-model="editBy" type="number" min="1" step="1" class="ws-input" placeholder="例如 10001" />
            </label>
            <button type="button" class="ws-btn ws-btn-primary" :disabled="saving" @click="saveCompletion">
              <Save :size="14" />
              {{ saving ? '保存中…' : '保存填报' }}
            </button>
          </div>
        </div>
        <div v-else class="ws-detail-content gov-empty">请选择左侧整改任务</div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.gov-rect-page {
  min-height: 0;
}

.gov-split {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(320px, 0.9fr);
  gap: 8px;
}

.gov-list-panel {
  min-height: 0;
}

.gov-list-panel .ws-table-container {
  flex: 1;
  min-height: 0;
}

.gov-list-panel tbody tr {
  cursor: pointer;
}

.gov-kv {
  display: grid;
  gap: 8px;
}

.gov-kv > div {
  display: grid;
  grid-template-columns: 96px 1fr;
  gap: 8px;
  font-size: 13px;
}

.gov-kv span {
  color: var(--ws-text-secondary);
}

.gov-kv strong {
  color: var(--ws-text-primary);
  font-weight: 500;
  word-break: break-all;
}

.gov-hint {
  margin: 0 0 10px;
  font-size: 12px;
  color: var(--ws-text-muted);
  line-height: 1.5;
}

.gov-form {
  display: grid;
  gap: 10px;
}

.gov-form label {
  display: grid;
  gap: 4px;
  font-size: 12px;
  color: var(--ws-text-secondary);
}

.is-pending {
  color: #ffb347 !important;
}

.gov-empty {
  color: var(--ws-text-muted);
  font-size: 13px;
}

.empty-row {
  text-align: center;
  color: var(--ws-text-muted);
}
</style>
