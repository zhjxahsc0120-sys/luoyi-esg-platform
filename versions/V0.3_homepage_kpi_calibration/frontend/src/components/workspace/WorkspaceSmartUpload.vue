<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  Upload,
  FileText,
  FileSpreadsheet,
  FileImage,
  AlertTriangle,
  RefreshCw,
  CheckCircle,
  Eye,
  ChevronLeft,
  ChevronRight,
  Search,
  Sparkles,
  Link2,
  Archive,
  Loader2,
  XCircle,
  FileWarning,
} from 'lucide-vue-next'
import {
  startParseFile,
  getParseJob,
  getParseFields,
  getMatchCandidates,
  confirmParseJob,
} from '@/services/api'
import type {
  ParseFieldItem,
  MatchCandidateItem,
  ParseJobDetail,
  UploadFileResponse,
  ConfirmParseResponse,
} from '@/services/api'
import { emitWorkspaceRefresh, onWorkspaceRefresh } from '@/utils/workspaceRefresh'

// ─── Types ───
type WorkbenchState = 'idle' | 'uploading' | 'parsing' | 'ready' | 'done' | 'failed'
type RightTab = 'summary' | 'data' | 'anomaly'

interface UploadedFileInfo {
  name: string
  size: number
  type: string
  fileId?: number
}

// ─── Constants ───
const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8765'

const PARSE_STAGES = [
  { key: 'file_read', label: '文件读取完成', progress: 15 },
  { key: 'classification', label: '文档分类完成', progress: 30 },
  { key: 'extraction', label: '正文与表格提取完成', progress: 60 },
  { key: 'field_identify', label: '业务字段识别完成', progress: 80 },
  { key: 'match_complete', label: '异常检查与关联推荐完成', progress: 100 },
] as const

const FLOW_STEPS = [
  { key: 'upload', label: '上传资料' },
  { key: 'parse', label: 'AI解析' },
  { key: 'review', label: '核对结果' },
  { key: 'confirm', label: '确认入库' },
] as const

const FIELD_STATUS_MAP: Record<string, { label: string; color: string; bg: string }> = {
  identified: { label: '已识别', color: '#69e36f', bg: 'rgba(105,227,111,0.12)' },
  review: { label: '建议核对', color: '#ffb347', bg: 'rgba(255,179,71,0.12)' },
  conflict: { label: '存在冲突', color: '#ff4f5e', bg: 'rgba(255,79,94,0.12)' },
  missing: { label: '待补充', color: '#8fa9c8', bg: 'rgba(143,169,200,0.1)' },
  corrected: { label: '已人工修正', color: '#2f9cff', bg: 'rgba(47,156,255,0.12)' },
}

const CLASSIFICATION_OPTIONS: Array<{ value: 'E' | 'S' | 'G' | '综合' | '暂不确定'; label: string; color: string }> = [
  { value: 'E', label: 'E·环境', color: '#69e36f' },
  { value: 'S', label: 'S·社会', color: '#2f9cff' },
  { value: 'G', label: 'G·治理', color: '#a66cff' },
  { value: '综合', label: '综合', color: '#8fa9c8' },
  { value: '暂不确定', label: '暂不确定', color: '#5a7a9a' },
]

// ─── State ───
const workbenchState = ref<WorkbenchState>('idle')
const pageMessage = ref('')
const pageMessageType = ref<'success' | 'error' | 'info'>('info')
const fileInputRef = ref<HTMLInputElement | null>(null)

const uploadProgress = ref(0)
const uploadLoaded = ref(0)
const uploadTotal = ref(0)
const uploadedFiles = ref<UploadedFileInfo[]>([])

const parseProgress = ref(0)
const parseStageLabel = ref('')
const currentJobId = ref<number | null>(null)
const currentFileId = ref<number | null>(null)
const currentJob = ref<ParseJobDetail | null>(null)
const extractedFields = ref<ParseFieldItem[]>([])
const matchCandidates = ref<MatchCandidateItem[]>([])

const rightTab = ref<RightTab>('summary')
const selectedFieldKey = ref<string | null>(null)
const editingFieldKey = ref<string | null>(null)
const editFieldValue = ref('')
const editReason = ref('')

const esgClassification = ref<'E' | 'S' | 'G' | '综合' | '暂不确定'>('E')
const selectedCandidateIds = ref<number[]>([])
const acknowledgedWarnings = ref(false)

const doneResult = ref<ConfirmParseResponse | null>(null)
const doneSummary = ref('')

const activeFileIndex = ref(0)
const sourcePage = ref(1)
const sourceTotalPages = ref(1)
const sourceSearchKeyword = ref('')

let parsePollTimer: ReturnType<typeof setInterval> | null = null
let stageTimer: ReturnType<typeof setInterval> | null = null
let stopWorkspaceRefresh: (() => void) | null = null

// ─── Lifecycle ───
onMounted(() => {
  stopWorkspaceRefresh = onWorkspaceRefresh(() => {
    // External refresh trigger - no action needed for one-page workbench
  })
})

onUnmounted(() => {
  if (parsePollTimer) clearInterval(parsePollTimer)
  if (stageTimer) clearInterval(stageTimer)
  stopWorkspaceRefresh?.()
})

// ─── Helpers ───
function showMessage(msg: string, type: 'success' | 'error' | 'info' = 'info') {
  pageMessage.value = msg
  pageMessageType.value = type
}

function getModuleColor(module: string): string {
  switch (module) {
    case 'E': return '#69e36f'
    case 'S': return '#2f9cff'
    case 'G': return '#a66cff'
    default: return '#8fa9c8'
  }
}

function getModuleLabel(module: string): string {
  switch (module) {
    case 'E': return '环境环保'
    case 'S': return '社会责任'
    case 'G': return '治理合规'
    default: return '综合'
  }
}

function getFileIcon(fileName: string) {
  if (fileName.endsWith('.pdf')) return FileText
  if (fileName.endsWith('.xlsx') || fileName.endsWith('.xls') || fileName.endsWith('.csv')) return FileSpreadsheet
  if (fileName.endsWith('.jpg') || fileName.endsWith('.png') || fileName.endsWith('.jpeg')) return FileImage
  return FileText
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// ─── Flow Bar ───
const currentFlowStep = computed(() => {
  switch (workbenchState.value) {
    case 'idle': return 0
    case 'uploading': return 0
    case 'parsing': return 1
    case 'ready': return 2
    case 'done': return 3
    case 'failed': return 1
    default: return 0
  }
})

function getFlowStepClass(index: number): string {
  const current = currentFlowStep.value
  if (index < current) return 'completed'
  if (index === current) return 'active'
  return 'pending'
}

// ─── Upload ───
function handleSelectFile() {
  fileInputRef.value?.click()
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  const files = event.dataTransfer?.files
  if (files && files.length > 0) {
    handleFiles(files)
  }
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
}

async function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files) {
    await handleFiles(input.files)
  }
  input.value = ''
}

async function handleFiles(files: FileList) {
  if (!files || files.length === 0) return

  workbenchState.value = 'uploading'
  uploadProgress.value = 0
  uploadLoaded.value = 0
  uploadTotal.value = 0
  uploadedFiles.value = []
  pageMessage.value = ''

  for (const file of Array.from(files)) {
    const fileInfo: UploadedFileInfo = {
      name: file.name,
      size: file.size,
      type: file.type || 'unknown',
    }
    uploadedFiles.value.push(fileInfo)

    try {
      const uploadRes = await uploadWithProgress(file, (loaded, total) => {
        uploadLoaded.value = loaded
        uploadTotal.value = total
        uploadProgress.value = total > 0 ? Math.round((loaded / total) * 100) : 0
      })

      if (uploadRes) {
        fileInfo.fileId = uploadRes.fileId
        currentFileId.value = uploadRes.fileId

        if (uploadRes.duplicateStatus === 'DUPLICATE') {
          showMessage(`检测到疑似重复文件：${file.name}，匹配文件ID：${uploadRes.matchedFileId || '-'}`, 'info')
        }
      } else {
        workbenchState.value = 'failed'
        showMessage(`文件上传失败：${file.name}。请确认后端服务已启动。`, 'error')
        return
      }
    } catch {
      workbenchState.value = 'failed'
      showMessage(`文件上传异常：${file.name}`, 'error')
      return
    }
  }

  if (currentFileId.value) {
    await startParsing(currentFileId.value)
  }
}

function uploadWithProgress(
  file: File,
  onProgress: (loaded: number, total: number) => void,
): Promise<UploadFileResponse | null> {
  return new Promise(resolve => {
    const xhr = new XMLHttpRequest()
    const formData = new FormData()
    formData.append('file', file)
    formData.append('uploaderId', '10001')
    formData.append('uploaderName', '项目管理员')

    xhr.upload.addEventListener('progress', e => {
      if (e.lengthComputable) {
        onProgress(e.loaded, e.total)
      }
    })

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText) as UploadFileResponse)
        } catch {
          resolve(null)
        }
      } else {
        resolve(null)
      }
    })

    xhr.addEventListener('error', () => resolve(null))
    xhr.addEventListener('abort', () => resolve(null))

    xhr.open('POST', `${API_BASE}/api/workspace/files/upload`)
    xhr.send(formData)
  })
}

// ─── Parse ───
async function startParsing(fileId: number) {
  workbenchState.value = 'parsing'
  parseProgress.value = 0
  parseStageLabel.value = '正在启动解析任务'

  const parseRes = await startParseFile(fileId)
  if (!parseRes) {
    workbenchState.value = 'failed'
    showMessage('解析任务启动失败，请确认后端服务已启动。', 'error')
    return
  }

  currentJobId.value = parseRes.jobId

  let stageIndex = 0
  parseStageLabel.value = PARSE_STAGES[0].label
  parseProgress.value = PARSE_STAGES[0].progress

  stageTimer = setInterval(() => {
    stageIndex++
    if (stageIndex < PARSE_STAGES.length) {
      parseStageLabel.value = PARSE_STAGES[stageIndex].label
      parseProgress.value = PARSE_STAGES[stageIndex].progress
    }
  }, 800)

  parsePollTimer = setInterval(async () => {
    const job = await getParseJob(parseRes.jobId)
    if (!job) return

    currentJob.value = job
    const status = job.jobStatus?.toUpperCase()

    if (status === 'WAIT_CONFIRM' || status === 'SUCCESS') {
      if (parsePollTimer) { clearInterval(parsePollTimer); parsePollTimer = null }
      if (stageTimer) { clearInterval(stageTimer); stageTimer = null }
      parseProgress.value = 100
      parseStageLabel.value = '解析完成'
      await loadParseResults(parseRes.jobId)
    } else if (status === 'FAILED') {
      if (parsePollTimer) { clearInterval(parsePollTimer); parsePollTimer = null }
      if (stageTimer) { clearInterval(stageTimer); stageTimer = null }
      workbenchState.value = 'failed'
      showMessage(`解析失败：${job.summary || '未知原因'}`, 'error')
    }
  }, 1500)
}

async function loadParseResults(jobId: number) {
  const [jobRes, fieldsRes, candidatesRes] = await Promise.all([
    getParseJob(jobId),
    getParseFields(jobId),
    getMatchCandidates(jobId),
  ])

  if (jobRes) currentJob.value = jobRes
  if (fieldsRes && fieldsRes.items.length > 0) {
    extractedFields.value = fieldsRes.items
  }
  if (candidatesRes) {
    matchCandidates.value = candidatesRes.items
  }

  const moduleField = extractedFields.value.find(
    f => f.fieldKey === 'esg_module' || f.fieldKey === 'module'
  )
  if (moduleField && moduleField.fieldValue) {
    const mod = moduleField.fieldValue as 'E' | 'S' | 'G'
    if (['E', 'S', 'G'].includes(mod)) {
      esgClassification.value = mod
    }
  }

  selectedCandidateIds.value = []
  acknowledgedWarnings.value = false

  sourceTotalPages.value = Math.max(1, Math.ceil(extractedFields.value.length / 6))
  sourcePage.value = 1
  activeFileIndex.value = 0

  workbenchState.value = 'ready'
  rightTab.value = 'summary'

  const fieldCount = extractedFields.value.length
  const candidateCount = matchCandidates.value.length
  const conflictCount = extractedFields.value.filter(f => getFieldStatus(f) === 'conflict').length
  const reviewCount = extractedFields.value.filter(f => getFieldStatus(f) === 'review').length

  let msg = `AI解析完成，识别 ${fieldCount} 项数据`
  if (reviewCount > 0) msg += `，其中 ${reviewCount} 项建议核对`
  if (conflictCount > 0) msg += `，${conflictCount} 项存在冲突`
  if (candidateCount > 0) msg += `，推荐 ${candidateCount} 项业务关联`
  msg += '。'
  showMessage(msg, 'success')
}

// ─── Field Status ───
function getFieldStatus(field: ParseFieldItem): string {
  const status = field.confirmStatus?.toUpperCase()
  if (status === 'CONFIRMED' || status === 'ACCEPTED') return 'corrected'
  if (status === 'CONFLICT') return 'conflict'
  if (status === 'REVIEW' || status === 'PENDING') {
    if (!field.fieldValue || field.fieldValue === '—' || field.fieldValue === '') return 'missing'
    return 'review'
  }
  return 'identified'
}

function getFieldStatusInfo(status: string) {
  return FIELD_STATUS_MAP[status] || FIELD_STATUS_MAP.identified
}

// ─── Field Editing ───
function startEditField(field: ParseFieldItem) {
  editingFieldKey.value = field.fieldKey
  editFieldValue.value = field.confirmedValue || field.fieldValue
  editReason.value = ''
}

function saveEditField() {
  if (!editingFieldKey.value) return

  const idx = extractedFields.value.findIndex(f => f.fieldKey === editingFieldKey.value)
  if (idx > -1) {
    const isConflict = getFieldStatus(extractedFields.value[idx]) === 'conflict'
    if (isConflict && !editReason.value.trim()) {
      showMessage('存在冲突的字段必须填写修改原因', 'error')
      return
    }
    extractedFields.value[idx] = {
      ...extractedFields.value[idx],
      confirmedValue: editFieldValue.value,
      confirmStatus: 'CONFIRMED',
    }
  }

  editingFieldKey.value = null
  editFieldValue.value = ''
  editReason.value = ''
  showMessage('已保存修改', 'success')
}

function cancelEditField() {
  editingFieldKey.value = null
  editFieldValue.value = ''
  editReason.value = ''
}

// ─── Source Linking ───
function handleViewSource(field: ParseFieldItem) {
  selectedFieldKey.value = field.fieldKey
  const fieldIndex = extractedFields.value.findIndex(f => f.fieldKey === field.fieldKey)
  sourcePage.value = Math.max(1, Math.ceil((fieldIndex + 1) / 6))
}

// ─── Business Association ───
function toggleCandidate(candidateId: number) {
  const idx = selectedCandidateIds.value.indexOf(candidateId)
  if (idx > -1) {
    selectedCandidateIds.value.splice(idx, 1)
  } else {
    selectedCandidateIds.value.push(candidateId)
  }
}

// ─── Validation ───
const conflictFields = computed(() =>
  extractedFields.value.filter(f => getFieldStatus(f) === 'conflict' && !f.confirmedValue)
)

const missingFields = computed(() =>
  extractedFields.value.filter(f => getFieldStatus(f) === 'missing')
)

const reviewFields = computed(() =>
  extractedFields.value.filter(f => getFieldStatus(f) === 'review')
)

const hasUnresolvedConflicts = computed(() => conflictFields.value.length > 0)
const hasMissingRequired = computed(() => missingFields.value.length > 0)
const hasWarnings = computed(() => reviewFields.value.length > 0)

const canConfirm = computed(() => {
  if (hasUnresolvedConflicts.value) return false
  if (hasMissingRequired.value) return false
  if (hasWarnings.value && !acknowledgedWarnings.value) return false
  return true
})

const confirmButtonText = computed(() => {
  if (selectedCandidateIds.value.length > 0) return '确认入库并关联'
  return '确认入库'
})

// ─── Confirm ───
async function handleConfirm() {
  if (!currentJobId.value || !canConfirm.value) return

  const confirmedFields = extractedFields.value
    .filter(f => f.confirmedValue)
    .map(f => ({
      fieldKey: f.fieldKey,
      confirmedValue: f.confirmedValue as string,
    }))

  const acceptedCandidateIds = selectedCandidateIds.value.filter(id => !isNaN(id))

  const res = await confirmParseJob(currentJobId.value, {
    confirmedFields,
    acceptedCandidateIds,
    operatorId: 10001,
    operatorName: '项目管理员',
    comment: acknowledgedWarnings.value ? '已核对提醒项' : '前端确认入库',
  })

  if (res) {
    doneResult.value = res
    workbenchState.value = 'done'

    const linkedNames = res.linkedTasks && res.linkedTasks.length > 0
      ? res.linkedTasks.map(task => task.taskName).join('、')
      : ''

    doneSummary.value = `已形成 1 份资料档案（DocumentID：${res.documentId}）` +
      (linkedNames ? `，关联 ${linkedNames}` : '，未关联业务事项') +
      '，写入经人工确认的结构化数据。'

    emitWorkspaceRefresh({
      source: 'smart-upload',
      scopes: ['summary', 'tasks', 'documents', 'parse-queue'],
    })
  } else {
    showMessage('确认入库接口未响应，请确认后端服务已启动。', 'error')
  }
}

function handleReParse() {
  resetToIdle()
}

function handleSaveDraft() {
  showMessage('已暂存当前解析结果，可稍后继续确认。', 'info')
}

function handleContinue() {
  resetToIdle()
}

function handleRetry() {
  resetToIdle()
}

function resetToIdle() {
  if (parsePollTimer) { clearInterval(parsePollTimer); parsePollTimer = null }
  if (stageTimer) { clearInterval(stageTimer); stageTimer = null }
  workbenchState.value = 'idle'
  uploadedFiles.value = []
  extractedFields.value = []
  matchCandidates.value = []
  selectedCandidateIds.value = []
  acknowledgedWarnings.value = false
  currentJobId.value = null
  currentFileId.value = null
  currentJob.value = null
  doneResult.value = null
  doneSummary.value = ''
  pageMessage.value = ''
  selectedFieldKey.value = null
  editingFieldKey.value = null
}

// ─── Source Preview ───
const activeFile = computed(() => uploadedFiles.value[activeFileIndex.value] || null)

const sourceFieldsForPage = computed(() => {
  const start = (sourcePage.value - 1) * 6
  return extractedFields.value.slice(start, start + 6)
})

function goToSourcePage(page: number) {
  if (page < 1 || page > sourceTotalPages.value) return
  sourcePage.value = page
}

function selectFile(index: number) {
  activeFileIndex.value = index
  sourcePage.value = 1
}

// ─── Summary ───
const summaryText = computed(() => {
  if (currentJob.value?.summary) return currentJob.value.summary
  const docType = extractedFields.value.find(f => f.fieldKey === 'document_type')?.fieldValue
  const period = extractedFields.value.find(f => f.fieldKey === 'period')?.fieldValue
  if (docType && period) return `本资料为${period}的${docType}。`
  return '解析完成，请核对以下结构化结果。'
})

const metadataFields = computed(() => {
  const map: Record<string, string> = {}
  for (const f of extractedFields.value) {
    map[f.fieldKey] = f.confirmedValue || f.fieldValue
  }
  return {
    documentType: map['document_type'] || '—',
    period: map['period'] || '—',
    module: map['esg_module'] || map['module'] || 'E',
    responsibleUnit: map['responsible_unit'] || map['responsibility_unit'] || '—',
    projectSection: map['project_section'] || '—',
    engineeringObject: map['engineering_object'] || '—',
  }
})

const totalSizeText = computed(() => {
  const total = uploadedFiles.value.reduce((sum, f) => sum + f.size, 0)
  return formatFileSize(total)
})

// ─── Anomaly Tab ───
const anomalies = computed(() => {
  const list: Array<{ type: string; severity: string; message: string; fieldKey?: string }> = []
  for (const f of extractedFields.value) {
    const status = getFieldStatus(f)
    if (status === 'conflict') {
      list.push({
        type: '字段冲突',
        severity: 'blocking',
        message: `字段「${f.fieldName}」存在冲突，AI识别值为「${f.fieldValue}」，需人工确认。`,
        fieldKey: f.fieldKey,
      })
    }
    if (status === 'missing') {
      list.push({
        type: '字段缺失',
        severity: 'warning',
        message: `字段「${f.fieldName}」未识别到值，待人工补充。`,
        fieldKey: f.fieldKey,
      })
    }
  }
  return list
})

// ─── Editable metadata ───
const editingMeta = ref<string | null>(null)
const metaEditValue = ref('')

function startEditMeta(key: string, value: string) {
  editingMeta.value = key
  metaEditValue.value = value === '—' ? '' : value
}

function saveEditMeta(key: string) {
  const fieldKeyMap: Record<string, string> = {
    documentType: 'document_type',
    period: 'period',
    responsibleUnit: 'responsible_unit',
    projectSection: 'project_section',
    engineeringObject: 'engineering_object',
  }
  const actualKey = fieldKeyMap[key] || key
  const idx = extractedFields.value.findIndex(f => f.fieldKey === actualKey)
  if (idx > -1) {
    extractedFields.value[idx] = {
      ...extractedFields.value[idx],
      confirmedValue: metaEditValue.value,
      confirmStatus: 'CONFIRMED',
    }
  }
  editingMeta.value = null
  showMessage('已保存修改', 'success')
}

function cancelEditMeta() {
  editingMeta.value = null
  metaEditValue.value = ''
}
</script>

<template>
  <div class="ws-smart-upload ws-page">
    <input
      ref="fileInputRef"
      class="hidden-file-input"
      type="file"
      multiple
      accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.jpg,.jpeg,.png,.zip,.rar"
      @change="handleFileChange"
    />

    <!-- Page message -->
    <div v-if="pageMessage" class="ws-page-message" :class="pageMessageType">{{ pageMessage }}</div>

    <!-- Top flow bar -->
    <div class="flow-bar">
      <div
        v-for="(step, i) in FLOW_STEPS"
        :key="step.key"
        class="flow-step"
        :class="getFlowStepClass(i)"
      >
        <span class="flow-step-num">{{ i + 1 }}</span>
        <span class="flow-step-label">{{ step.label }}</span>
        <CheckCircle v-if="i < currentFlowStep" :size="14" class="flow-step-check" />
      </div>
    </div>

    <!-- ─── IDLE: Large upload zone ─── -->
    <div v-if="workbenchState === 'idle'" class="idle-zone ws-panel" @click="handleSelectFile" @drop="handleDrop" @dragover="handleDragOver">
      <div class="idle-upload-inner">
        <div class="idle-upload-icon">
          <Upload :size="48" />
        </div>
        <div class="idle-upload-title">将文件拖拽到此处，或点击选择文件上传</div>
        <div class="idle-upload-desc">
          支持 PDF、Word、Excel、CSV、TXT、图片及压缩包。可多选文件作为一个资料包解析。
        </div>
        <button class="ws-btn ws-btn-primary idle-upload-btn" @click.stop="handleSelectFile">
          <Upload :size="16" />
          <span>选择本地文件</span>
        </button>
      </div>
    </div>

    <!-- ─── UPLOADING: Progress ─── -->
    <div v-else-if="workbenchState === 'uploading'" class="progress-zone ws-panel">
      <div class="progress-header">
        <Loader2 :size="20" class="spin-icon" />
        <span class="progress-title">正在上传文件</span>
      </div>
      <div class="progress-file-list">
        <div v-for="(file, i) in uploadedFiles" :key="i" class="progress-file-item">
          <component :is="getFileIcon(file.name)" :size="16" class="file-icon" />
          <span class="file-name-text">{{ file.name }}</span>
          <span class="file-size-text">{{ formatFileSize(file.size) }}</span>
          <CheckCircle v-if="file.fileId" :size="16" class="file-done-icon" />
        </div>
      </div>
      <div class="progress-bar-wrap">
        <div class="progress-bar-track">
          <div class="progress-bar-fill upload" :style="{ width: `${uploadProgress}%` }"></div>
        </div>
        <div class="progress-bar-info">
          <span>{{ uploadProgress }}%</span>
          <span v-if="uploadTotal > 0">{{ formatFileSize(uploadLoaded) }} / {{ formatFileSize(uploadTotal) }}</span>
        </div>
      </div>
    </div>

    <!-- ─── PARSING: Progress ─── -->
    <div v-else-if="workbenchState === 'parsing'" class="progress-zone ws-panel">
      <div class="progress-header">
        <Loader2 :size="20" class="spin-icon" />
        <span class="progress-title">AI解析中</span>
      </div>
      <div class="parse-stage-list">
        <div
          v-for="(stage, i) in PARSE_STAGES"
          :key="stage.key"
          class="parse-stage-item"
          :class="{
            done: parseProgress > stage.progress || (i === PARSE_STAGES.length - 1 && parseProgress === 100),
            active: parseProgress === stage.progress || (parseProgress < stage.progress && (i === 0 || parseProgress >= PARSE_STAGES[i - 1].progress)),
          }"
        >
          <div class="parse-stage-dot"></div>
          <span class="parse-stage-label">{{ stage.label }}</span>
          <span class="parse-stage-pct">{{ stage.progress }}%</span>
        </div>
      </div>
      <div class="progress-bar-wrap">
        <div class="progress-bar-track">
          <div class="progress-bar-fill parse" :style="{ width: `${parseProgress}%` }"></div>
        </div>
        <div class="progress-bar-info">
          <span>流程进度 {{ parseProgress }}%</span>
          <span>{{ parseStageLabel }}</span>
        </div>
      </div>
    </div>

    <!-- ─── READY: Dual column ─── -->
    <div v-else-if="workbenchState === 'ready'" class="ready-zone">
      <!-- Left: Source preview (~55%) -->
      <div class="source-preview-panel ws-panel">
        <div class="ws-panel-header">
          <div class="ws-panel-title">
            <FileText :size="16" class="ws-panel-title-icon" />
            <span>原文预览</span>
          </div>
          <div class="source-file-tabs">
            <button
              v-for="(file, i) in uploadedFiles"
              :key="i"
              class="source-file-tab"
              :class="{ active: activeFileIndex === i }"
              @click="selectFile(i)"
            >
              <component :is="getFileIcon(file.name)" :size="12" />
              <span>{{ file.name.length > 16 ? file.name.slice(0, 14) + '…' : file.name }}</span>
            </button>
          </div>
        </div>

        <div class="source-toolbar">
          <div class="source-page-nav">
            <button class="ws-btn ws-btn-secondary ws-btn-sm" :disabled="sourcePage <= 1" @click="goToSourcePage(sourcePage - 1)">
              <ChevronLeft :size="14" />
            </button>
            <span class="source-page-text">{{ sourcePage }} / {{ sourceTotalPages }}</span>
            <button class="ws-btn ws-btn-secondary ws-btn-sm" :disabled="sourcePage >= sourceTotalPages" @click="goToSourcePage(sourcePage + 1)">
              <ChevronRight :size="14" />
            </button>
          </div>
          <div class="ws-search-box source-search">
            <Search :size="14" />
            <input v-model="sourceSearchKeyword" type="text" placeholder="搜索原文..." />
          </div>
        </div>

        <div class="source-content-area">
          <div v-if="activeFile" class="source-file-info-bar">
            <component :is="getFileIcon(activeFile.name)" :size="16" class="file-icon" />
            <span class="source-file-name">{{ activeFile.name }}</span>
            <span class="source-file-size">{{ formatFileSize(activeFile.size) }}</span>
          </div>

          <div class="source-text-area">
            <div v-if="sourceFieldsForPage.length === 0" class="source-empty">
              暂无可展示的原文内容
            </div>
            <div
              v-for="field in sourceFieldsForPage"
              :key="field.id"
              class="source-field-block"
              :class="{ highlighted: selectedFieldKey === field.fieldKey }"
              @click="selectedFieldKey = field.fieldKey"
            >
              <div class="source-field-label">
                <span class="source-field-name">{{ field.fieldName }}</span>
                <button class="source-locate-btn" @click.stop="handleViewSource(field)">
                  <Eye :size="12" />
                  <span>定位</span>
                </button>
              </div>
              <div class="source-field-value">{{ field.fieldValue || '—' }}</div>
              <div v-if="field.confirmedValue && field.confirmedValue !== field.fieldValue" class="source-field-confirmed">
                人工确认值：{{ field.confirmedValue }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Structured results (~45%) -->
      <div class="result-panel ws-panel">
        <div class="ws-panel-header">
          <div class="ws-panel-title">
            <Sparkles :size="16" class="ws-panel-title-icon" />
            <span>解析结果确认单</span>
          </div>
          <span v-if="currentJob" class="parse-engine-badge">
            {{ currentJob.parseSource === 'content' ? '已识别' : '规则识别' }}
          </span>
        </div>

        <!-- Right tabs -->
        <div class="right-tabs">
          <button
            v-for="tab in [
              { key: 'summary', label: '摘要与归属' },
              { key: 'data', label: `关键数据${extractedFields.length > 0 ? `(${extractedFields.length})` : ''}` },
              { key: 'anomaly', label: `异常与关联${anomalies.length + matchCandidates.length > 0 ? `(${anomalies.length + matchCandidates.length})` : ''}` },
            ]"
            :key="tab.key"
            class="right-tab-btn"
            :class="{ active: rightTab === tab.key }"
            @click="rightTab = tab.key as RightTab"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- Tab content -->
        <div class="right-tab-content">
          <!-- Tab 1: Summary & Classification -->
          <div v-if="rightTab === 'summary'" class="tab-summary">
            <div class="summary-text-block">
              <div class="summary-label">资料摘要</div>
              <div class="summary-text">{{ summaryText }}</div>
            </div>

            <div class="meta-section">
              <div class="meta-section-title">关键元数据（可修改）</div>
              <div class="meta-grid">
                <div class="meta-item" v-for="key in ['documentType', 'period', 'responsibleUnit', 'projectSection', 'engineeringObject']" :key="key">
                  <span class="meta-label">{{ { documentType: '资料类型', period: '所属周期', responsibleUnit: '责任单位', projectSection: '所属标段', engineeringObject: '工程对象' }[key] }}</span>
                  <div v-if="editingMeta === key" class="meta-edit">
                    <input v-model="metaEditValue" class="meta-edit-input" @keyup.enter="saveEditMeta(key)" @blur="saveEditMeta(key)" />
                  </div>
                  <div v-else class="meta-value-wrap" @dblclick="startEditMeta(key, metadataFields[key])">
                    <span class="meta-value">{{ metadataFields[key] }}</span>
                    <span class="meta-edit-hint">双击编辑</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="meta-section">
              <div class="meta-section-title">ESG归属分类</div>
              <div class="classification-options">
                <button
                  v-for="opt in CLASSIFICATION_OPTIONS"
                  :key="opt.value"
                  class="classification-btn"
                  :class="{ active: esgClassification === opt.value }"
                  :style="esgClassification === opt.value ? { borderColor: opt.color, color: opt.color, background: opt.color + '15' } : {}"
                  @click="esgClassification = opt.value"
                >
                  {{ opt.label }}
                </button>
              </div>
            </div>

            <div class="meta-section">
              <div class="meta-section-title">解析置信度</div>
              <div class="confidence-wrap">
                <div class="confidence-bar">
                  <div class="confidence-fill" :style="{ width: `${currentJob?.confidence ? Math.round(Number(currentJob.confidence)) : 0}%` }"></div>
                </div>
                <span class="confidence-text">{{ currentJob?.confidence ? Math.round(Number(currentJob.confidence)) : 0 }}%</span>
              </div>
            </div>
          </div>

          <!-- Tab 2: Key Data -->
          <div v-else-if="rightTab === 'data'" class="tab-data">
            <div v-if="extractedFields.length === 0" class="tab-empty">暂无识别到的数据字段</div>
            <div v-else class="field-list">
              <div
                v-for="field in extractedFields"
                :key="field.id"
                class="field-card"
                :class="{ selected: selectedFieldKey === field.fieldKey }"
                @click="selectedFieldKey = field.fieldKey"
              >
                <div class="field-card-header">
                  <span class="field-card-name">{{ field.fieldName }}</span>
                  <span
                    class="field-status-tag"
                    :style="{
                      color: getFieldStatusInfo(getFieldStatus(field)).color,
                      background: getFieldStatusInfo(getFieldStatus(field)).bg,
                      borderColor: getFieldStatusInfo(getFieldStatus(field)).color + '40',
                    }"
                  >
                    {{ getFieldStatusInfo(getFieldStatus(field)).label }}
                  </span>
                </div>

                <div v-if="editingFieldKey === field.fieldKey" class="field-edit-area">
                  <div class="field-edit-row">
                    <span class="field-edit-label">AI值：</span>
                    <span class="field-edit-ai-value">{{ field.fieldValue }}</span>
                  </div>
                  <input v-model="editFieldValue" class="field-edit-input" placeholder="输入确认值" />
                  <textarea
                    v-model="editReason"
                    class="field-edit-reason"
                    placeholder="修改原因（冲突字段必填）"
                    rows="2"
                  ></textarea>
                  <div class="field-edit-actions">
                    <button class="ws-btn ws-btn-primary ws-btn-sm" @click.stop="saveEditField">保存</button>
                    <button class="ws-btn ws-btn-secondary ws-btn-sm" @click.stop="cancelEditField">取消</button>
                  </div>
                </div>

                <div v-else class="field-value-display">
                  <div class="field-value-row">
                    <span class="field-value-label">AI值：</span>
                    <span class="field-value-text">{{ field.fieldValue || '—' }}</span>
                  </div>
                  <div v-if="field.confirmedValue" class="field-value-row confirmed">
                    <span class="field-value-label">确认值：</span>
                    <span class="field-value-text">{{ field.confirmedValue }}</span>
                  </div>
                  <div class="field-actions">
                    <button class="field-action-btn" @click.stop="startEditField(field)">
                      <RefreshCw :size="12" />
                      <span>修改</span>
                    </button>
                    <button class="field-action-btn" @click.stop="handleViewSource(field)">
                      <Eye :size="12" />
                      <span>查看来源</span>
                    </button>
                  </div>
                </div>

                <div class="field-confidence">
                  <span>置信度 {{ Math.round(Number(field.confidence) || 0) }}%</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Tab 3: Anomaly & Association -->
          <div v-else-if="rightTab === 'anomaly'" class="tab-anomaly">
            <!-- Anomalies -->
            <div class="anomaly-section">
              <div class="anomaly-section-title">
                <FileWarning :size="14" />
                <span>异常记录</span>
                <span class="anomaly-count">{{ anomalies.length }}</span>
              </div>
              <div v-if="anomalies.length === 0" class="anomaly-empty">暂无异常</div>
              <div v-else class="anomaly-list">
                <div
                  v-for="(anomaly, i) in anomalies"
                  :key="i"
                  class="anomaly-item"
                  :class="{ blocking: anomaly.severity === 'blocking' }"
                >
                  <div class="anomaly-item-header">
                    <AlertTriangle :size="14" class="anomaly-icon" />
                    <span class="anomaly-type">{{ anomaly.type }}</span>
                    <span class="anomaly-severity" :class="anomaly.severity">
                      {{ anomaly.severity === 'blocking' ? '阻断' : '提醒' }}
                    </span>
                  </div>
                  <div class="anomaly-message">{{ anomaly.message }}</div>
                  <button v-if="anomaly.fieldKey" class="anomaly-action" @click="rightTab = 'data'; selectedFieldKey = anomaly.fieldKey">
                    去处理 →
                  </button>
                </div>
              </div>
            </div>

            <!-- Business Candidates -->
            <div class="anomaly-section">
              <div class="anomaly-section-title">
                <Link2 :size="14" />
                <span>业务关联推荐</span>
                <span class="anomaly-count">{{ matchCandidates.length }}</span>
              </div>

              <div v-if="matchCandidates.length === 0" class="no-candidate-hint">
                暂未发现可关联的业务事项，可先确认入库，后续补充关联。
              </div>

              <div v-else class="candidate-list">
                <div
                  v-for="candidate in matchCandidates"
                  :key="candidate.candidateId"
                  class="candidate-item"
                  :class="{ selected: selectedCandidateIds.includes(candidate.candidateId) }"
                >
                  <label class="candidate-checkbox" @click.stop="toggleCandidate(candidate.candidateId)">
                    <input
                      type="checkbox"
                      :checked="selectedCandidateIds.includes(candidate.candidateId)"
                      @change="toggleCandidate(candidate.candidateId)"
                    />
                    <span class="checkbox-custom"></span>
                  </label>
                  <div class="candidate-content">
                    <div class="candidate-header">
                      <span class="candidate-name">{{ candidate.taskName }}</span>
                      <span class="candidate-module" :style="{ color: getModuleColor(candidate.module) }">
                        {{ candidate.module }} · {{ getModuleLabel(candidate.module) }}
                      </span>
                    </div>
                    <div class="candidate-meta">
                      <span class="candidate-score" :style="{ color: candidate.matchScore >= 90 ? '#69e36f' : '#ffb347' }">
                        匹配度 {{ candidate.matchScore }}%
                      </span>
                      <span class="candidate-reason">{{ candidate.matchReason || '内容关键词匹配' }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Archive metadata -->
            <div class="anomaly-section">
              <div class="anomaly-section-title">
                <Archive :size="14" />
                <span>资料归档</span>
              </div>
              <div class="archive-grid">
                <div class="archive-item">
                  <span class="archive-label">资料类型</span>
                  <span class="archive-value">{{ metadataFields.documentType }}</span>
                </div>
                <div class="archive-item">
                  <span class="archive-label">所属周期</span>
                  <span class="archive-value">{{ metadataFields.period }}</span>
                </div>
                <div class="archive-item">
                  <span class="archive-label">责任单位</span>
                  <span class="archive-value">{{ metadataFields.responsibleUnit }}</span>
                </div>
                <div class="archive-item">
                  <span class="archive-label">ESG归属</span>
                  <span class="archive-value" :style="{ color: getModuleColor(esgClassification) }">
                    {{ esgClassification }} · {{ getModuleLabel(esgClassification) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ─── DONE: Summary ─── -->
    <div v-else-if="workbenchState === 'done'" class="done-zone ws-panel">
      <div class="done-inner">
        <div class="done-icon">
          <CheckCircle :size="48" />
        </div>
        <div class="done-title">入库成功</div>
        <div class="done-summary">{{ doneSummary }}</div>
        <div v-if="doneResult?.linkedTasks && doneResult.linkedTasks.length > 0" class="done-linked">
          <div class="done-linked-title">关联结果</div>
          <div v-for="task in doneResult.linkedTasks" :key="task.taskId" class="done-linked-item">
            <CheckCircle :size="14" class="done-linked-icon" />
            <span>{{ task.taskName }}</span>
            <span v-if="task.progress" class="done-linked-progress">
              完整度 {{ task.progress.completed }}/{{ task.progress.total }}
            </span>
          </div>
        </div>
        <button class="ws-btn ws-btn-primary done-continue-btn" @click="handleContinue">
          <Upload :size="16" />
          <span>继续上传</span>
        </button>
      </div>
    </div>

    <!-- ─── FAILED: Error ─── -->
    <div v-else-if="workbenchState === 'failed'" class="failed-zone ws-panel">
      <div class="failed-inner">
        <div class="failed-icon">
          <XCircle :size="48" />
        </div>
        <div class="failed-title">处理失败</div>
        <div class="failed-message">{{ pageMessage || '未知错误' }}</div>
        <button class="ws-btn ws-btn-primary failed-retry-btn" @click="handleRetry">
          <RefreshCw :size="16" />
          <span>重新选择文件</span>
        </button>
      </div>
    </div>

    <!-- ─── Bottom action bar (ready state only) ─── -->
    <div v-if="workbenchState === 'ready'" class="ws-bottom-actions smart-upload-actions">
      <div class="action-left">
        <button class="ws-btn ws-btn-secondary" @click="handleReParse">
          <RefreshCw :size="14" />
          <span>重新解析</span>
        </button>
        <button class="ws-btn ws-btn-view" @click="handleSaveDraft">
          <Archive :size="14" />
          <span>暂存待确认</span>
        </button>
      </div>
      <div class="action-right">
        <label v-if="hasWarnings && !hasUnresolvedConflicts && !hasMissingRequired" class="ack-checkbox" @click="acknowledgedWarnings = !acknowledgedWarnings">
          <input type="checkbox" v-model="acknowledgedWarnings" />
          <span class="ack-text">我已核对上述提醒，确认采用当前结果</span>
        </label>
        <button class="ws-btn ws-btn-primary" :disabled="!canConfirm" @click="handleConfirm">
          <CheckCircle :size="14" />
          <span>{{ confirmButtonText }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ─── Flow bar ─── */
.flow-bar {
  display: flex;
  align-items: center;
  gap: 0;
  flex-shrink: 0;
  padding: 0 4px;
}

.flow-step {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  font-size: 13px;
  color: #5a7a9a;
  position: relative;
  flex: 1;
}

.flow-step:not(:last-child)::after {
  content: '';
  position: absolute;
  right: -4px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 1px;
  background: rgba(143, 169, 200, 0.2);
}

.flow-step-num {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  border: 1px solid rgba(143, 169, 200, 0.3);
  color: #5a7a9a;
  flex-shrink: 0;
}

.flow-step-label {
  font-weight: 500;
  white-space: nowrap;
}

.flow-step-check {
  color: #69e36f;
  flex-shrink: 0;
}

.flow-step.completed {
  color: #69e36f;
}

.flow-step.completed .flow-step-num {
  background: rgba(105, 227, 111, 0.15);
  border-color: rgba(105, 227, 111, 0.4);
  color: #69e36f;
}

.flow-step.active {
  color: #2f9cff;
}

.flow-step.active .flow-step-num {
  background: rgba(47, 156, 255, 0.15);
  border-color: rgba(47, 156, 255, 0.5);
  color: #2f9cff;
  box-shadow: 0 0 8px rgba(47, 156, 255, 0.3);
}

/* ─── IDLE ─── */
.idle-zone {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border: 2px dashed rgba(105, 227, 111, 0.2);
  transition: border-color 0.2s, background 0.2s;
  min-height: 0;
}

.idle-zone:hover {
  border-color: rgba(105, 227, 111, 0.5);
  background: rgba(105, 227, 111, 0.03);
}

.idle-upload-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
}

.idle-upload-icon {
  color: #69e36f;
  opacity: 0.8;
}

.idle-upload-title {
  font-size: 16px;
  font-weight: 600;
  color: #e8f3ff;
}

.idle-upload-desc {
  font-size: 13px;
  color: #8fa9c8;
  text-align: center;
  line-height: 1.5;
  max-width: 400px;
}

.idle-upload-btn {
  margin-top: 8px;
}

/* ─── Progress zone ─── */
.progress-zone {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 40px;
  min-height: 0;
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.spin-icon {
  color: #2f9cff;
  animation: spin 1.2s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.progress-title {
  font-size: 16px;
  font-weight: 600;
  color: #e8f3ff;
}

.progress-file-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
  max-width: 500px;
}

.progress-file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  font-size: 13px;
}

.progress-file-item .file-icon {
  color: #8fa9c8;
  flex-shrink: 0;
}

.progress-file-item .file-name-text {
  color: #e8f3ff;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.progress-file-item .file-size-text {
  color: #8fa9c8;
  font-size: 12px;
  flex-shrink: 0;
}

.file-done-icon {
  color: #69e36f;
  flex-shrink: 0;
}

.progress-bar-wrap {
  width: 100%;
  max-width: 500px;
}

.progress-bar-track {
  height: 8px;
  background: rgba(47, 156, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-bar-fill.upload {
  background: linear-gradient(90deg, #69e36f, #2f9cff);
}

.progress-bar-fill.parse {
  background: linear-gradient(90deg, #2f9cff, #a66cff);
}

.progress-bar-info {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #8fa9c8;
}

/* ─── Parse stages ─── */
.parse-stage-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  max-width: 500px;
}

.parse-stage-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  font-size: 13px;
  color: #5a7a9a;
  border-radius: 6px;
  transition: all 0.3s;
}

.parse-stage-item.done {
  color: #69e36f;
}

.parse-stage-item.active {
  color: #2f9cff;
  background: rgba(47, 156, 255, 0.08);
}

.parse-stage-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(143, 169, 200, 0.3);
  flex-shrink: 0;
  transition: all 0.3s;
}

.parse-stage-item.done .parse-stage-dot {
  background: #69e36f;
}

.parse-stage-item.active .parse-stage-dot {
  background: #2f9cff;
  box-shadow: 0 0 8px rgba(47, 156, 255, 0.5);
}

.parse-stage-label {
  flex: 1;
}

.parse-stage-pct {
  font-size: 12px;
  color: #5a7a9a;
  font-variant-numeric: tabular-nums;
}

/* ─── Ready zone ─── */
.ready-zone {
  flex: 1;
  display: flex;
  gap: 8px;
  min-height: 0;
}

.source-preview-panel {
  width: 55%;
  min-height: 0;
  overflow: hidden;
}

.result-panel {
  width: 45%;
  min-height: 0;
  overflow: hidden;
}

/* ─── Source preview ─── */
.source-file-tabs {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.source-file-tab {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  font-size: 12px;
  color: #8fa9c8;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.source-file-tab.active {
  color: #2f9cff;
  border-color: rgba(47, 156, 255, 0.4);
  background: rgba(47, 156, 255, 0.1);
}

.source-file-tab span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.source-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
  flex-shrink: 0;
}

.source-page-nav {
  display: flex;
  align-items: center;
  gap: 6px;
}

.source-page-text {
  font-size: 12px;
  color: #8fa9c8;
  font-variant-numeric: tabular-nums;
}

.source-search {
  width: 160px;
}

.source-content-area {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.source-file-info-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  margin-bottom: 8px;
  flex-shrink: 0;
}

.source-file-info-bar .file-icon {
  color: #8fa9c8;
}

.source-file-name {
  font-size: 13px;
  color: #e8f3ff;
  font-weight: 500;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-file-size {
  font-size: 12px;
  color: #8fa9c8;
  flex-shrink: 0;
}

.source-text-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow-y: auto;
  min-height: 0;
}

.source-empty {
  text-align: center;
  color: #5a7a9a;
  padding: 40px;
  font-size: 13px;
}

.source-field-block {
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(47, 156, 255, 0.08);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.source-field-block:hover {
  border-color: rgba(47, 156, 255, 0.2);
}

.source-field-block.highlighted {
  border-color: rgba(255, 179, 71, 0.5);
  background: rgba(255, 179, 71, 0.06);
  box-shadow: 0 0 12px rgba(255, 179, 71, 0.15);
}

.source-field-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.source-field-name {
  font-size: 12px;
  color: #8fa9c8;
  font-weight: 500;
}

.source-locate-btn {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 2px 6px;
  font-size: 11px;
  color: #2f9cff;
  background: transparent;
  border: none;
  cursor: pointer;
  border-radius: 3px;
}

.source-locate-btn:hover {
  background: rgba(47, 156, 255, 0.1);
}

.source-field-value {
  font-size: 14px;
  color: #e8f3ff;
  font-weight: 500;
  line-height: 1.5;
}

.source-field-confirmed {
  font-size: 12px;
  color: #2f9cff;
  margin-top: 4px;
  padding-top: 4px;
  border-top: 1px solid rgba(47, 156, 255, 0.1);
}

/* ─── Right tabs ─── */
.right-tabs {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
  margin-bottom: 6px;
}

.right-tab-btn {
  padding: 6px 12px;
  font-size: 13px;
  color: #8fa9c8;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.right-tab-btn:hover {
  color: #e8f3ff;
}

.right-tab-btn.active {
  color: #2f9cff;
  border-bottom-color: #2f9cff;
}

.right-tab-content {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.parse-engine-badge {
  font-size: 11px;
  color: #69e36f;
  border: 1px solid rgba(105, 227, 111, 0.35);
  background: rgba(105, 227, 111, 0.1);
  border-radius: 4px;
  padding: 2px 8px;
  white-space: nowrap;
}

/* ─── Tab: Summary ─── */
.tab-summary {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 2px 0;
}

.summary-text-block {
  padding: 10px 12px;
  background: rgba(47, 156, 255, 0.08);
  border: 1px solid rgba(47, 156, 255, 0.15);
  border-radius: 6px;
}

.summary-label {
  font-size: 12px;
  color: #8fa9c8;
  margin-bottom: 4px;
}

.summary-text {
  font-size: 13px;
  color: #e8f3ff;
  line-height: 1.5;
}

.meta-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-section-title {
  font-size: 12px;
  color: #8fa9c8;
  font-weight: 600;
  padding-bottom: 4px;
  border-bottom: 1px solid rgba(47, 156, 255, 0.08);
}

.meta-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.meta-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.meta-label {
  font-size: 12px;
  color: #8fa9c8;
  flex-shrink: 0;
  width: 80px;
}

.meta-value-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  flex: 1;
  justify-content: flex-end;
}

.meta-value-wrap:hover .meta-edit-hint {
  opacity: 1;
}

.meta-value {
  font-size: 13px;
  color: #e8f3ff;
  font-weight: 500;
  text-align: right;
}

.meta-edit-hint {
  font-size: 10px;
  color: #5a7a9a;
  opacity: 0;
  transition: opacity 0.2s;
  flex-shrink: 0;
}

.meta-edit {
  flex: 1;
  display: flex;
  justify-content: flex-end;
}

.meta-edit-input {
  width: 160px;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(47, 156, 255, 0.3);
  border-radius: 4px;
  color: #e8f3ff;
  font-size: 13px;
  outline: none;
  text-align: right;
}

.meta-edit-input:focus {
  border-color: #2f9cff;
}

.classification-options {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.classification-btn {
  padding: 4px 10px;
  font-size: 12px;
  color: #8fa9c8;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(143, 169, 200, 0.2);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.classification-btn:hover {
  border-color: rgba(143, 169, 200, 0.4);
  color: #e8f3ff;
}

.confidence-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.confidence-bar {
  flex: 1;
  height: 6px;
  background: rgba(105, 227, 111, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  background: linear-gradient(90deg, #69e36f, #2f9cff);
  border-radius: 3px;
  transition: width 0.3s;
}

.confidence-text {
  font-size: 12px;
  color: #69e36f;
  font-weight: 600;
  width: 40px;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

/* ─── Tab: Data ─── */
.tab-data {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tab-empty {
  text-align: center;
  color: #5a7a9a;
  padding: 40px;
  font-size: 13px;
}

.field-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-card {
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(47, 156, 255, 0.08);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.field-card:hover {
  border-color: rgba(47, 156, 255, 0.2);
}

.field-card.selected {
  border-color: rgba(47, 156, 255, 0.4);
  background: rgba(47, 156, 255, 0.05);
}

.field-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.field-card-name {
  font-size: 13px;
  color: #e8f3ff;
  font-weight: 500;
}

.field-status-tag {
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 600;
  border: 1px solid;
  border-radius: 4px;
  white-space: nowrap;
}

.field-value-display {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-value-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.field-value-label {
  color: #8fa9c8;
  flex-shrink: 0;
}

.field-value-text {
  color: #e8f3ff;
  font-weight: 500;
}

.field-value-row.confirmed .field-value-text {
  color: #2f9cff;
}

.field-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.field-action-btn {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 2px 6px;
  font-size: 11px;
  color: #8fa9c8;
  background: transparent;
  border: 1px solid rgba(143, 169, 200, 0.15);
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.2s;
}

.field-action-btn:hover {
  color: #2f9cff;
  border-color: rgba(47, 156, 255, 0.3);
}

.field-confidence {
  margin-top: 4px;
  font-size: 11px;
  color: #5a7a9a;
}

.field-edit-area {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 4px;
}

.field-edit-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.field-edit-label {
  color: #8fa9c8;
}

.field-edit-ai-value {
  color: #e8f3ff;
  font-weight: 500;
}

.field-edit-input {
  width: 100%;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(47, 156, 255, 0.3);
  border-radius: 4px;
  color: #e8f3ff;
  font-size: 13px;
  outline: none;
  box-sizing: border-box;
}

.field-edit-input:focus {
  border-color: #2f9cff;
}

.field-edit-reason {
  width: 100%;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 79, 94, 0.2);
  border-radius: 4px;
  color: #e8f3ff;
  font-size: 12px;
  outline: none;
  resize: none;
  box-sizing: border-box;
  font-family: inherit;
}

.field-edit-reason:focus {
  border-color: rgba(255, 79, 94, 0.5);
}

.field-edit-actions {
  display: flex;
  gap: 6px;
}

/* ─── Tab: Anomaly ─── */
.tab-anomaly {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 2px 0;
}

.anomaly-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.anomaly-section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #8fa9c8;
  font-weight: 600;
  padding-bottom: 4px;
  border-bottom: 1px solid rgba(47, 156, 255, 0.08);
}

.anomaly-count {
  margin-left: auto;
  font-size: 11px;
  color: #5a7a9a;
  background: rgba(143, 169, 200, 0.1);
  padding: 1px 6px;
  border-radius: 3px;
}

.anomaly-empty {
  font-size: 12px;
  color: #5a7a9a;
  padding: 8px 0;
}

.anomaly-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.anomaly-item {
  padding: 8px 10px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 79, 94, 0.15);
  border-radius: 6px;
}

.anomaly-item.blocking {
  border-color: rgba(255, 79, 94, 0.3);
  background: rgba(255, 79, 94, 0.05);
}

.anomaly-item-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.anomaly-icon {
  color: #ff4f5e;
  flex-shrink: 0;
}

.anomaly-type {
  font-size: 12px;
  color: #e8f3ff;
  font-weight: 500;
}

.anomaly-severity {
  margin-left: auto;
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 3px;
  font-weight: 600;
}

.anomaly-severity.blocking {
  color: #ff4f5e;
  background: rgba(255, 79, 94, 0.15);
}

.anomaly-severity.warning {
  color: #ffb347;
  background: rgba(255, 179, 71, 0.15);
}

.anomaly-message {
  font-size: 12px;
  color: #8fa9c8;
  line-height: 1.5;
}

.anomaly-action {
  margin-top: 4px;
  font-size: 11px;
  color: #2f9cff;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
}

.anomaly-action:hover {
  text-decoration: underline;
}

.no-candidate-hint {
  font-size: 12px;
  color: #8fa9c8;
  padding: 8px 10px;
  background: rgba(47, 156, 255, 0.08);
  border: 1px solid rgba(47, 156, 255, 0.15);
  border-radius: 6px;
  line-height: 1.5;
}

.candidate-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.candidate-item {
  display: flex;
  gap: 10px;
  padding: 8px 10px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(47, 156, 255, 0.08);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.candidate-item:hover {
  border-color: rgba(47, 156, 255, 0.2);
}

.candidate-item.selected {
  border-color: rgba(47, 156, 255, 0.4);
  background: rgba(47, 156, 255, 0.05);
}

.candidate-checkbox {
  display: flex;
  align-items: flex-start;
  cursor: pointer;
  padding-top: 2px;
}

.candidate-checkbox input {
  display: none;
}

.checkbox-custom {
  width: 16px;
  height: 16px;
  border: 1px solid rgba(143, 169, 200, 0.3);
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.candidate-checkbox input:checked + .checkbox-custom {
  background: #2f9cff;
  border-color: #2f9cff;
}

.candidate-checkbox input:checked + .checkbox-custom::after {
  content: '✓';
  color: #031020;
  font-size: 11px;
  font-weight: 700;
}

.candidate-content {
  flex: 1;
  min-width: 0;
}

.candidate-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-bottom: 4px;
}

.candidate-name {
  font-size: 13px;
  color: #e8f3ff;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.candidate-module {
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}

.candidate-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
}

.candidate-score {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.candidate-reason {
  color: #8fa9c8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.archive-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.archive-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 4px 0;
}

.archive-label {
  font-size: 12px;
  color: #8fa9c8;
}

.archive-value {
  font-size: 13px;
  color: #e8f3ff;
  font-weight: 500;
  text-align: right;
}

/* ─── Done zone ─── */
.done-zone {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0;
}

.done-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
  max-width: 500px;
}

.done-icon {
  color: #69e36f;
}

.done-title {
  font-size: 20px;
  font-weight: 700;
  color: #e8f3ff;
}

.done-summary {
  font-size: 14px;
  color: #8fa9c8;
  text-align: center;
  line-height: 1.6;
}

.done-linked {
  width: 100%;
  margin-top: 8px;
}

.done-linked-title {
  font-size: 13px;
  color: #e8f3ff;
  font-weight: 600;
  margin-bottom: 8px;
}

.done-linked-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: rgba(105, 227, 111, 0.05);
  border: 1px solid rgba(105, 227, 111, 0.15);
  border-radius: 6px;
  font-size: 13px;
  color: #e8f3ff;
  margin-bottom: 4px;
}

.done-linked-icon {
  color: #69e36f;
  flex-shrink: 0;
}

.done-linked-progress {
  margin-left: auto;
  font-size: 11px;
  color: #8fa9c8;
}

.done-continue-btn {
  margin-top: 12px;
}

/* ─── Failed zone ─── */
.failed-zone {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0;
}

.failed-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
  max-width: 500px;
}

.failed-icon {
  color: #ff4f5e;
}

.failed-title {
  font-size: 20px;
  font-weight: 700;
  color: #e8f3ff;
}

.failed-message {
  font-size: 14px;
  color: #8fa9c8;
  text-align: center;
  line-height: 1.6;
}

.failed-retry-btn {
  margin-top: 8px;
}

/* ─── Bottom actions ─── */
.smart-upload-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-left {
  display: flex;
  gap: 8px;
}

.action-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ack-checkbox {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 12px;
  color: #ffb347;
}

.ack-checkbox input {
  width: 14px;
  height: 14px;
  cursor: pointer;
  accent-color: #ffb347;
}

.ack-text {
  white-space: nowrap;
}

/* ─── Hidden ─── */
.hidden-file-input {
  display: none;
}
</style>
