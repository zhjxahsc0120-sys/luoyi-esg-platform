<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { FilePlus2, Link2, Pencil, Plus, RefreshCw, Save, Shield } from 'lucide-vue-next'
import {
  createSpecialPlan,
  getS02Risks,
  getSpecialPlan,
  getSpecialPlans,
  patchSpecialPlan,
  uploadWorkspaceBinaryFile,
} from '@/services/api'
import type { SpecialPlanApproval } from '@/types/governance'

type RiskOption = { id: number; label: string }

const loading = ref(false)
const saving = ref(false)
const uploading = ref(false)
const pageMessage = ref('')
const pageMessageType = ref<'info' | 'success' | 'error'>('info')
const items = ref<SpecialPlanApproval[]>([])
const selectedId = ref<number | null>(null)
const detail = ref<SpecialPlanApproval | null>(null)
const riskOptions = ref<RiskOption[]>([])

const filterProjectId = ref('')
const filterStatus = ref('')

const mode = ref<'view' | 'create' | 'edit'>('view')

const form = ref({
  projectId: '1001',
  riskPointId: '',
  planCode: '',
  planName: '',
  riskLevel: '重大',
  approvalStatus: '待审批',
  approvalDate: '',
  approvalFileId: '',
  sourceDocRef: '',
  dataNature: 'demo',
  isDemo: true,
})

const statusCards = computed(() => {
  const total = items.value.length
  const approved = items.value.filter((p) => String(p.approvalStatus).includes('已')).length
  const withFile = items.value.filter((p) => p.approvalFileId != null).length
  return [
    { label: '专项方案', value: total, unit: '项', color: '#a66cff' },
    { label: '含“已”状态', value: approved, unit: '项', color: '#69e36f' },
    { label: '已关联文件', value: withFile, unit: '项', color: '#2f9cff' },
  ]
})

function showMessage(type: 'info' | 'success' | 'error', text: string) {
  pageMessageType.value = type
  pageMessage.value = text
}

function resetFormForCreate() {
  mode.value = 'create'
  form.value = {
    projectId: filterProjectId.value || '1001',
    riskPointId: riskOptions.value[0] ? String(riskOptions.value[0].id) : '',
    planCode: '',
    planName: '',
    riskLevel: '重大',
    approvalStatus: '待审批',
    approvalDate: '',
    approvalFileId: '',
    sourceDocRef: '',
    dataNature: 'demo',
    isDemo: true,
  }
  selectedId.value = null
  detail.value = null
}

function fillFormFromDetail(row: SpecialPlanApproval) {
  form.value = {
    projectId: String(row.projectId),
    riskPointId: String(row.riskPointId),
    planCode: row.planCode,
    planName: row.planName,
    riskLevel: row.riskLevel,
    approvalStatus: row.approvalStatus,
    approvalDate: row.approvalDate || '',
    approvalFileId: row.approvalFileId != null ? String(row.approvalFileId) : '',
    sourceDocRef: row.sourceDocRef || '',
    dataNature: row.dataNature || 'demo',
    isDemo: !!row.isDemo,
  }
}

async function loadRisks() {
  const res = await getS02Risks()
  const risks = res?.data?.risks || []
  riskOptions.value = risks.map((r) => ({
    id: r.id,
    label: `${r.businessCode || r.id} · ${r.title || '风险点'}`,
  }))
}

async function loadList(preferId?: number | null) {
  loading.value = true
  pageMessage.value = ''
  try {
    const res = await getSpecialPlans({
      projectId: filterProjectId.value ? Number(filterProjectId.value) : undefined,
      approvalStatus: filterStatus.value || undefined,
    })
    items.value = res?.items || []
    if (!items.value.length) {
      if (mode.value !== 'create') {
        selectedId.value = null
        detail.value = null
        mode.value = 'view'
      }
      showMessage('info', '暂无专项方案记录，可点击「新增」创建')
      return
    }
    const target = preferId && items.value.some((p) => p.id === preferId)
      ? preferId
      : (selectedId.value && items.value.some((p) => p.id === selectedId.value)
        ? selectedId.value
        : items.value[0].id)
    await selectPlan(target)
  } finally {
    loading.value = false
  }
}

async function selectPlan(id: number) {
  selectedId.value = id
  mode.value = 'view'
  const res = await getSpecialPlan(id)
  detail.value = res
  if (res) fillFormFromDetail(res)
}

function startEdit() {
  if (!detail.value) return
  fillFormFromDetail(detail.value)
  mode.value = 'edit'
}

async function onUploadFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  uploading.value = true
  try {
    const uploaded = await uploadWorkspaceBinaryFile(file)
    if (!uploaded?.fileId) {
      showMessage('error', '文件上传失败')
      return
    }
    form.value.approvalFileId = String(uploaded.fileId)
    showMessage('success', `文件已上传，已填入 approvalFileId=${uploaded.fileId}（未删除原文件资产）`)
  } finally {
    uploading.value = false
  }
}

function clearFileLink() {
  form.value.approvalFileId = ''
}

async function saveCreate() {
  const projectId = Number(form.value.projectId)
  const riskPointId = Number(form.value.riskPointId)
  if (!projectId || !riskPointId || !form.value.planCode.trim() || !form.value.planName.trim()) {
    showMessage('error', '请填写项目、风险源、方案编号与名称')
    return
  }
  saving.value = true
  try {
    const result = await createSpecialPlan({
      projectId,
      riskPointId,
      planCode: form.value.planCode.trim(),
      planName: form.value.planName.trim(),
      riskLevel: form.value.riskLevel.trim(),
      approvalStatus: form.value.approvalStatus.trim(),
      approvalDate: form.value.approvalDate.trim() || null,
      approvalFileId: form.value.approvalFileId ? Number(form.value.approvalFileId) : null,
      sourceDocRef: form.value.sourceDocRef.trim() || null,
      dataNature: form.value.dataNature || 'demo',
      isDemo: form.value.isDemo,
    })
    if (!result.ok) {
      showMessage('error', result.message || '创建失败')
      return
    }
    showMessage('success', '专项方案已创建')
    mode.value = 'view'
    await loadList(result.data.id)
  } finally {
    saving.value = false
  }
}

async function saveEdit() {
  if (!detail.value) return
  saving.value = true
  try {
    const result = await patchSpecialPlan(detail.value.id, {
      planName: form.value.planName.trim(),
      riskLevel: form.value.riskLevel.trim(),
      approvalStatus: form.value.approvalStatus.trim(),
      approvalDate: form.value.approvalDate.trim() || null,
      approvalFileId: form.value.approvalFileId.trim() === ''
        ? null
        : Number(form.value.approvalFileId),
      sourceDocRef: form.value.sourceDocRef.trim() || null,
    })
    if (!result.ok) {
      showMessage('error', result.message || '保存失败')
      return
    }
    showMessage('success', '专项方案已更新（不支持删除）')
    mode.value = 'view'
    await loadList(result.data.id)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadRisks()
  await loadList()
})
</script>

<template>
  <div class="ws-page gov-plan-page">
    <div class="ws-page-header">
      <div class="ws-page-title-group">
        <h2 class="ws-page-title">专项方案审批</h2>
        <p class="ws-page-subtitle">风险专项方案 · 审批事实 · 合规证据链（禁止物理删除）</p>
      </div>
      <div class="ws-page-header-extra">
        <button type="button" class="ws-btn ws-btn-secondary ws-btn-sm" :disabled="loading" @click="loadList()">
          <RefreshCw :size="14" />
          刷新
        </button>
        <button type="button" class="ws-btn ws-btn-primary ws-btn-sm" @click="resetFormForCreate">
          <Plus :size="14" />
          新增
        </button>
      </div>
    </div>

    <div v-if="pageMessage" class="ws-page-message" :class="pageMessageType">{{ pageMessage }}</div>

    <div class="ws-status-cards" style="grid-template-columns: repeat(3, minmax(0, 1fr))">
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
        <input v-model="filterProjectId" class="ws-input" type="number" placeholder="projectId" @change="loadList()" />
        <input v-model="filterStatus" class="ws-input" type="text" placeholder="approvalStatus" @change="loadList()" />
        <button type="button" class="ws-btn ws-btn-secondary ws-btn-sm" @click="loadList()">查询</button>
      </div>
    </div>

    <div class="gov-split">
      <section class="ws-panel gov-list-panel">
        <div class="ws-panel-header">
          <div class="ws-panel-title">
            <Shield :size="16" class="ws-panel-title-icon" />
            专项方案列表
          </div>
          <span class="ws-panel-count">{{ items.length }} 条</span>
        </div>
        <div class="ws-table-container">
          <div class="ws-table-scroll">
            <table class="ws-table">
              <thead>
                <tr>
                  <th>方案编号</th>
                  <th>名称</th>
                  <th>风险等级</th>
                  <th>审批状态</th>
                  <th>文件</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="loading">
                  <td colspan="5" class="empty-row">加载中…</td>
                </tr>
                <tr v-else-if="!items.length">
                  <td colspan="5" class="empty-row">暂无数据</td>
                </tr>
                <tr
                  v-for="row in items"
                  v-else
                  :key="row.id"
                  :class="{ selected: row.id === selectedId && mode !== 'create' }"
                  @click="selectPlan(row.id)"
                >
                  <td>{{ row.planCode }}</td>
                  <td class="col-name">{{ row.planName }}</td>
                  <td>{{ row.riskLevel }}</td>
                  <td><span class="ws-tag">{{ row.approvalStatus }}</span></td>
                  <td>{{ row.approvalFile?.originalName || (row.approvalFileId ? `#${row.approvalFileId}` : '—') }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <aside class="ws-detail-panel">
        <div class="ws-detail-header">
          <component :is="mode === 'create' ? FilePlus2 : mode === 'edit' ? Pencil : Shield" :size="16" class="ws-detail-header-icon" />
          <div class="ws-detail-title">
            {{ mode === 'create' ? '新增专项方案' : mode === 'edit' ? '编辑专项方案' : (detail?.planCode || '方案详情') }}
          </div>
          <button
            v-if="mode === 'view' && detail"
            type="button"
            class="ws-btn ws-btn-secondary ws-btn-sm"
            @click="startEdit"
          >
            <Pencil :size="14" />
            编辑
          </button>
        </div>

        <div class="ws-detail-content">
          <template v-if="mode === 'view' && detail">
            <div class="ws-section-title">审批信息</div>
            <div class="gov-kv">
              <div><span>项目 ID</span><strong>{{ detail.projectId }}</strong></div>
              <div><span>风险源 ID</span><strong>{{ detail.riskPointId }}</strong></div>
              <div><span>方案编号</span><strong>{{ detail.planCode }}</strong></div>
              <div><span>方案名称</span><strong>{{ detail.planName }}</strong></div>
              <div><span>风险等级</span><strong>{{ detail.riskLevel }}</strong></div>
              <div><span>审批状态</span><strong>{{ detail.approvalStatus }}</strong></div>
              <div><span>审批日期</span><strong>{{ detail.approvalDate || '—' }}</strong></div>
              <div><span>来源资料</span><strong>{{ detail.sourceDocRef || '—' }}</strong></div>
              <div>
                <span>关联文件</span>
                <strong>
                  <template v-if="detail.approvalFile">
                    {{ detail.approvalFile.originalName }}（{{ detail.approvalFile.fileCode }}）
                  </template>
                  <template v-else-if="detail.approvalFileId">#{{ detail.approvalFileId }}</template>
                  <template v-else>—</template>
                </strong>
              </div>
            </div>
            <p class="gov-hint">本记录属于合规证据链，界面不提供删除。</p>
          </template>

          <template v-else-if="mode === 'create' || mode === 'edit'">
            <div class="ws-section-title">{{ mode === 'create' ? '新增表单' : '可修改字段' }}</div>
            <div class="gov-form">
              <label v-if="mode === 'create'">
                项目 ID
                <input v-model="form.projectId" type="number" class="ws-input" />
              </label>
              <label v-if="mode === 'create'">
                风险源
                <select v-model="form.riskPointId" class="ws-select">
                  <option value="" disabled>请选择 safety_risk_point</option>
                  <option v-for="r in riskOptions" :key="r.id" :value="String(r.id)">{{ r.label }}</option>
                </select>
              </label>
              <label v-if="mode === 'create'">
                方案编号 planCode
                <input v-model="form.planCode" type="text" class="ws-input" />
              </label>
              <label v-else>
                方案编号（不可改）
                <input :value="form.planCode" type="text" class="ws-input" disabled />
              </label>
              <label>
                方案名称
                <input v-model="form.planName" type="text" class="ws-input" />
              </label>
              <label>
                风险等级
                <input v-model="form.riskLevel" type="text" class="ws-input" />
              </label>
              <label>
                审批状态
                <input v-model="form.approvalStatus" type="text" class="ws-input" />
              </label>
              <label>
                审批日期（可空，不自动生成）
                <input v-model="form.approvalDate" type="date" class="ws-input" />
              </label>
              <label>
                来源资料编号
                <input v-model="form.sourceDocRef" type="text" class="ws-input" />
              </label>
              <label>
                关联文件 ID
                <div class="gov-file-row">
                  <input v-model="form.approvalFileId" type="number" class="ws-input" placeholder="approvalFileId" />
                  <label class="ws-btn ws-btn-secondary ws-btn-sm gov-upload-btn">
                    <Link2 :size="14" />
                    {{ uploading ? '上传中…' : '上传关联' }}
                    <input type="file" hidden :disabled="uploading" @change="onUploadFile" />
                  </label>
                  <button type="button" class="ws-btn ws-btn-secondary ws-btn-sm" @click="clearFileLink">解除关联</button>
                </div>
              </label>
              <div class="gov-actions">
                <button
                  type="button"
                  class="ws-btn ws-btn-primary"
                  :disabled="saving"
                  @click="mode === 'create' ? saveCreate() : saveEdit()"
                >
                  <Save :size="14" />
                  {{ saving ? '保存中…' : '保存' }}
                </button>
                <button
                  type="button"
                  class="ws-btn ws-btn-secondary"
                  :disabled="saving"
                  @click="mode === 'create' ? (mode = 'view') : selectPlan(detail!.id)"
                >
                  取消
                </button>
              </div>
            </div>
          </template>

          <div v-else class="gov-empty">请选择左侧方案，或点击「新增」</div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.gov-plan-page {
  min-height: 0;
}

.gov-split {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(340px, 1fr);
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
  margin: 14px 0 0;
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

.gov-file-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.gov-file-row .ws-input {
  flex: 1;
  min-width: 120px;
}

.gov-upload-btn {
  cursor: pointer;
}

.gov-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
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
