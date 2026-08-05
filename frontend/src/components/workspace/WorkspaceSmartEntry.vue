<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import analysisMock from '@/data/esg-smart-entry-analysis.mock.json'
import {
  CheckCircle2,
  Database,
  FileCheck2,
  FileSpreadsheet,
  FileText,
  LoaderCircle,
  ScanText,
  Sparkles,
  Trash2,
  UploadCloud,
} from 'lucide-vue-next'

type ProcessStatus = 'idle' | 'analyzing' | 'preparing' | 'complete'
type StageState = 'pending' | 'active' | 'done'
type StagePace = 'fast' | 'medium' | 'slow' | 'instant'

interface ProcessStage {
  key: string
  label: string
  hint: string
  activeCopy: string
  /** Nominal dwell before advancing; confirm stage is instant. */
  durationMs: number
  /** Random +/- jitter so runs are not lockstep. */
  jitterMs: number
  pace: StagePace
  /** Optional rotating status lines while this stage is active (extract). */
  extractTicks?: string[]
}

interface EntryFile {
  id: string
  name: string
  size: number
}

interface StructuredField {
  label: string
  value: string
}

interface HighlightItem {
  name: string
  type: string
  content: string
  focus: string
}

interface DocumentUnderstanding {
  fileType: string
  project: string
  period: string
  constructionStage: string
}

interface RecognitionNotes {
  chapterCount: number
  tableCount: number
  keyItemCount: number
  confirmHint: string
}

interface DocumentMock {
  id: string
  matchKeywords: string[]
  documentType: string
  period: string
  confidence: string
  coverage: string[]
  documentUnderstanding: DocumentUnderstanding
  aiSummary: string[]
  highlightItems: HighlightItem[]
  structuredData: {
    engineering: StructuredField[]
    safety: StructuredField[]
    environment: StructuredField[]
  }
  recognitionNotes: RecognitionNotes
}

interface AnalysisMockData {
  project: {
    name: string
    fullName?: string
    stage: string
  }
  documents: DocumentMock[]
  ingestionSuggestion: {
    title: string
    parseStatus: string
    status: string
    statusLabel: string
    objects: string[]
    usage: string
  }
}

interface DocumentInsight extends DocumentMock {
  fileId: string
  fileName: string
}

const mockData = analysisMock as AnalysisMockData
const ACCEPTED_EXTENSIONS = ['xlsx', 'xls', 'csv', 'pdf', 'doc', 'docx', 'txt', 'zip']
/**
 * Uneven pipeline timings (nominal ± jitter) — no equal-interval timer:
 * receive 650±150 → 500–800ms
 * classify 1500±300 → 1200–1800ms
 * extract 3500±700 → 2800–4200ms (+rotating sub-ticks)
 * suggest 1900±300 → 1600–2200ms
 * confirm instant (lands when suggest finishes)
 */
const PROCESS_STAGES: ProcessStage[] = [
  {
    key: 'receive',
    label: '接收文件',
    hint: '文件已进入解析队列',
    activeCopy: '正在接收并核对上传文件…',
    durationMs: 650,
    jitterMs: 150,
    pace: 'fast',
  },
  {
    key: 'classify',
    label: '识别文档类型',
    hint: '已判定资料类型与周期',
    activeCopy: '正在识别文档类型与业务归属…',
    durationMs: 1500,
    jitterMs: 300,
    pace: 'medium',
  },
  {
    key: 'extract',
    label: '抽取业务数据',
    hint: '已提取工程与 ESG 关键字段',
    activeCopy: '正在抽取工程 / 环保 / 安全字段…',
    durationMs: 3500,
    jitterMs: 700,
    pace: 'slow',
    extractTicks: [
      '正在抽取工程进展与标段字段…',
      '正在抽取环保水保相关指标…',
      '正在抽取安全管控关键数据…',
      '正在汇总业务数据并校验字段…',
    ],
  },
  {
    key: 'suggest',
    label: '生成入库建议',
    hint: '已生成可确认的业务对象',
    activeCopy: '正在对照台账生成入库建议…',
    durationMs: 1900,
    jitterMs: 300,
    pace: 'medium',
  },
  {
    key: 'confirm',
    label: '待确认',
    hint: '请核对结果后确认入库',
    activeCopy: '解析完成，等待确认入库',
    durationMs: 0,
    jitterMs: 0,
    pace: 'instant',
  },
]
const EXTRACT_TICK_MS = 880
const fileInputRef = ref<HTMLInputElement | null>(null)
const uploadedFiles = ref<EntryFile[]>([])
const isDragging = ref(false)
const processStatus = ref<ProcessStatus>('idle')
const currentStageIndex = ref(-1)
const activeStatusCopy = ref('')
const confirmed = ref(false)
const pageMessage = ref('')
const pageError = ref('')
let pipelineTimer: ReturnType<typeof setTimeout> | null = null
let extractTickTimer: ReturnType<typeof setInterval> | null = null
let pipelineGeneration = 0

const isProcessing = computed(() => processStatus.value === 'analyzing' || processStatus.value === 'preparing')
const isReady = computed(() => processStatus.value === 'complete')
const insights = computed(() => uploadedFiles.value.map(buildDocumentInsight))
const primaryInsight = computed(() => insights.value[0] ?? null)
const completedStageCount = computed(() => {
  if (currentStageIndex.value < 0) return 0
  if (confirmed.value) return PROCESS_STAGES.length
  return currentStageIndex.value
})
const stageCounterLabel = computed(() => {
  if (currentStageIndex.value < 0) return ''
  if (confirmed.value) return `${PROCESS_STAGES.length}/${PROCESS_STAGES.length} 步`
  return `${currentStageIndex.value + 1}/${PROCESS_STAGES.length} 步`
})
const stageMeterPercent = computed(() => {
  if (currentStageIndex.value < 0) return 0
  if (confirmed.value) return 100
  return (completedStageCount.value / PROCESS_STAGES.length) * 100
})
const flowHeadline = computed(() => {
  if (confirmed.value) return '处理完成，已确认入库'
  if (isReady.value) return '解析完成，等待确认'
  if (isProcessing.value) return activeStatusCopy.value || 'AI 正在分阶段处理'
  return '上传后自动开始处理'
})
const activeStageHint = computed(() => {
  if (confirmed.value) return '资料已确认入库，可继续核对或重新选择文件'
  if (currentStageIndex.value < 0) return '上传后将按阶段自动识别，无需额外操作'
  if (isProcessing.value && activeStatusCopy.value) return activeStatusCopy.value
  return PROCESS_STAGES[currentStageIndex.value]?.hint ?? ''
})
const activeStagePace = computed(() => PROCESS_STAGES[currentStageIndex.value]?.pace ?? 'medium')
const confirmSummary = computed(() => {
  const count = uploadedFiles.value.length
  const usage = mockData.ingestionSuggestion.usage || 'ESG 月报填报与项目资料管理'
  if (!count) return `上传工程资料后，AI 将整理解析报告，用于${usage}。`
  return `已解析 ${count} 份资料。识别结果用于${usage}。请阅读 AI 解析报告后确认入库。`
})
const ingestionStatusLabel = computed(() => {
  if (confirmed.value) return '已确认入库'
  if (isReady.value) return mockData.ingestionSuggestion.statusLabel || '待业务确认'
  if (isProcessing.value) return '解析中'
  return '待上传'
})
const resultTitle = computed(() => {
  if (confirmed.value) return '已确认入库'
  if (processStatus.value === 'complete') return mockData.ingestionSuggestion.parseStatus || '解析完成'
  if (isProcessing.value) return activeStatusCopy.value || 'AI 正在分阶段处理'
  return '等待上传文件'
})
const resultPanelClass = computed(() => {
  if (confirmed.value) return 'confirmed'
  return processStatus.value
})

function highlightTypeClass(type: string): string {
  if (type === '安全') return 'type-safety'
  if (type === '环境') return 'type-environment'
  return 'type-engineering'
}

function fieldValue(value?: string): string {
  const trimmed = value?.trim()
  return trimmed ? trimmed : '未识别'
}

function stageState(index: number): StageState {
  if (currentStageIndex.value < 0) return 'pending'
  if (confirmed.value) return 'done'
  if (index < currentStageIndex.value) return 'done'
  if (index === currentStageIndex.value) return 'active'
  return 'pending'
}

function stageDetailText(index: number): string {
  const stage = PROCESS_STAGES[index]
  if (!stage) return ''
  if (stageState(index) === 'active' && isProcessing.value) {
    return activeStatusCopy.value || stage.activeCopy
  }
  return stage.hint
}

function resolveStageDuration(stage: ProcessStage): number {
  if (stage.durationMs <= 0) return 0
  const delta = Math.round((Math.random() * 2 - 1) * stage.jitterMs)
  const minMs = stage.durationMs - stage.jitterMs
  return Math.max(minMs, stage.durationMs + delta)
}

function openFilePicker() {
  fileInputRef.value?.click()
}

function fileIcon(name: string) {
  return name.toLowerCase().endsWith('.pdf') ? FileText : FileSpreadsheet
}

function fileTypeLabel(name: string): string {
  return name.split('.').pop()?.toUpperCase() || 'FILE'
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function extractPeriod(name: string): string {
  const singleMonth = name.match(/(20\d{2})年(\d{1,2})月/)
  if (singleMonth) return `${singleMonth[1]}年${singleMonth[2]}月`
  return '本期'
}

function matchDocumentMock(name: string): DocumentMock {
  const safetyDocument = mockData.documents.find(item => item.documentType === '安全监理月报')
  if ((name.includes('安全监理') || name.includes('安全月报')) && safetyDocument) return safetyDocument

  const matched = mockData.documents.find(item => item.matchKeywords.some(keyword => name.includes(keyword)))
  if (matched) return matched

  const fallback = mockData.documents[0]
  const period = extractPeriod(name)
  const documentType = name.toLowerCase().endsWith('.pdf') ? '工程业务资料' : '项目数据文件'
  return {
    ...fallback,
    id: 'general-document',
    documentType,
    period,
    confidence: '96.8%',
    documentUnderstanding: {
      fileType: documentType,
      project: mockData.project.name || '待确认',
      period,
      constructionStage: mockData.project.stage || '待确认',
    },
    aiSummary: [
      'AI 已识别项目、周期、建设阶段及主要施工事项，并整理工程业务摘要。',
      '结构化字段已提取为辅助核对信息；未识别项将标注为「未识别」或「待确认」，不编造事实。',
    ],
  }
}

function buildDocumentInsight(file: EntryFile): DocumentInsight {
  const definition = matchDocumentMock(file.name)
  return {
    ...definition,
    fileId: file.id,
    fileName: file.name,
  }
}

function clearExtractTicks() {
  if (extractTickTimer) {
    clearInterval(extractTickTimer)
    extractTickTimer = null
  }
}

function clearPipelineTimer() {
  if (pipelineTimer) {
    clearTimeout(pipelineTimer)
    pipelineTimer = null
  }
  clearExtractTicks()
}

function syncProcessStatusFromStage(index: number) {
  if (index < 0) {
    processStatus.value = 'idle'
    return
  }
  if (index >= PROCESS_STAGES.length - 1) {
    processStatus.value = 'complete'
    return
  }
  processStatus.value = index >= 3 ? 'preparing' : 'analyzing'
}

function startExtractTicks(stage: ProcessStage, generation: number) {
  clearExtractTicks()
  const ticks = stage.extractTicks
  if (!ticks?.length) return

  let tickIndex = 0
  activeStatusCopy.value = ticks[0]
  extractTickTimer = setInterval(() => {
    if (generation !== pipelineGeneration) return
    tickIndex = (tickIndex + 1) % ticks.length
    activeStatusCopy.value = ticks[tickIndex]
  }, EXTRACT_TICK_MS)
}

function finishPipeline(generation: number) {
  if (generation !== pipelineGeneration) return
  clearPipelineTimer()
  currentStageIndex.value = PROCESS_STAGES.length - 1
  processStatus.value = 'complete'
  activeStatusCopy.value = PROCESS_STAGES[PROCESS_STAGES.length - 1].activeCopy
}

function scheduleStageHold(index: number, generation: number) {
  if (generation !== pipelineGeneration) return
  const stage = PROCESS_STAGES[index]
  if (!stage) return

  // Confirm stage is a terminal wait-for-user state — no auto dwell.
  if (stage.pace === 'instant' || stage.durationMs <= 0) {
    finishPipeline(generation)
    return
  }

  currentStageIndex.value = index
  syncProcessStatusFromStage(index)
  activeStatusCopy.value = stage.activeCopy
  startExtractTicks(stage, generation)

  const dwellMs = resolveStageDuration(stage)
  pipelineTimer = setTimeout(() => {
    if (generation !== pipelineGeneration) return
    clearExtractTicks()

    const nextIndex = index + 1
    if (nextIndex >= PROCESS_STAGES.length - 1) {
      finishPipeline(generation)
      return
    }

    scheduleStageHold(nextIndex, generation)
  }, dwellMs)
}

function startAutomaticProcessing() {
  clearPipelineTimer()
  pageMessage.value = ''
  confirmed.value = false
  activeStatusCopy.value = ''
  pipelineGeneration += 1
  const generation = pipelineGeneration

  if (!uploadedFiles.value.length) {
    resetResults()
    return
  }

  scheduleStageHold(0, generation)
}

function confirmIngestion() {
  if (processStatus.value !== 'complete' || confirmed.value) return
  confirmed.value = true
  pageMessage.value = '已确认入库。关键数据已纳入本页核对结果，可继续添加资料或重新选择。'
}

function addFiles(files: File[]) {
  pageError.value = ''
  const rejected: string[] = []
  const additions: EntryFile[] = []

  files.forEach((file, index) => {
    const extension = file.name.split('.').pop()?.toLowerCase() || ''
    if (!ACCEPTED_EXTENSIONS.includes(extension)) {
      rejected.push(file.name)
      return
    }
    const duplicate = uploadedFiles.value.some(item => item.name === file.name && item.size === file.size)
    if (!duplicate) {
      additions.push({ id: `${Date.now()}-${index}-${file.name}`, name: file.name, size: file.size })
    }
  })

  if (additions.length) {
    uploadedFiles.value = [...uploadedFiles.value, ...additions]
    startAutomaticProcessing()
  }
  if (rejected.length) pageError.value = `以下文件格式暂不支持：${rejected.join('、')}`
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files) addFiles(Array.from(input.files))
  input.value = ''
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  isDragging.value = false
  if (event.dataTransfer?.files) addFiles(Array.from(event.dataTransfer.files))
}

function removeFile(id: string) {
  uploadedFiles.value = uploadedFiles.value.filter(file => file.id !== id)
  startAutomaticProcessing()
}

function resetResults() {
  clearPipelineTimer()
  pipelineGeneration += 1
  processStatus.value = 'idle'
  currentStageIndex.value = -1
  activeStatusCopy.value = ''
  confirmed.value = false
  pageMessage.value = ''
}

function clearFiles() {
  uploadedFiles.value = []
  pageError.value = ''
  resetResults()
}

onBeforeUnmount(clearPipelineTimer)
</script>

<template>
  <section class="smart-entry" data-testid="smart-entry-workbench">
    <input
      ref="fileInputRef"
      class="visually-hidden"
      type="file"
      multiple
      accept=".xlsx,.xls,.csv,.pdf,.doc,.docx,.txt,.zip"
      data-testid="file-input"
      @change="handleFileChange"
    />

    <header class="entry-heading">
      <div>
        <h2>ESG 智能数据填报</h2>
        <p>上传工程资料后，AI 自动识别项目、施工事项及 ESG 业务数据</p>
      </div>
      <span class="automatic-badge"><Sparkles :size="14" />AI智能解析</span>
    </header>

    <div v-if="pageError" class="page-alert" role="alert">{{ pageError }}</div>
    <div v-else-if="pageMessage" class="page-success" role="status">{{ pageMessage }}</div>

    <main class="one-page-workbench" :class="{ 'is-ready': isReady }">
      <section class="upload-panel panel-surface" :class="{ compact: isReady }" aria-labelledby="upload-title">
        <div class="panel-heading">
          <div class="heading-icon"><UploadCloud :size="18" /></div>
          <div><h3 id="upload-title">上传文件</h3><p>可选择 1 份或多份文件，选择后自动开始识别</p></div>
          <span v-if="uploadedFiles.length" class="file-count">已选择 {{ uploadedFiles.length }} 份</span>
          <button v-if="uploadedFiles.length" type="button" class="text-btn" @click="clearFiles">重新选择</button>
        </div>

        <div class="upload-content">
          <button
            type="button"
            class="drop-zone"
            :class="{ dragging: isDragging, compact: uploadedFiles.length }"
            @click="openFilePicker"
            @dragenter.prevent="isDragging = true"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop="handleDrop"
          >
            <span class="drop-icon"><UploadCloud :size="27" /></span>
            <span><strong>{{ uploadedFiles.length ? '继续添加文件' : '拖拽文件到此处，或点击选择' }}</strong><small>支持 PDF、Word、Excel、CSV、TXT 与压缩包</small></span>
          </button>

          <div v-if="uploadedFiles.length" class="file-list" data-testid="uploaded-file-list">
            <article v-for="file in uploadedFiles" :key="file.id" class="file-row">
              <span class="file-type-icon"><component :is="fileIcon(file.name)" :size="17" /><small>{{ fileTypeLabel(file.name) }}</small></span>
              <span class="file-primary"><strong :title="file.name">{{ file.name }}</strong><small>{{ formatFileSize(file.size) }}</small></span>
              <span class="file-ready"><FileCheck2 :size="14" />已接收</span>
              <button type="button" class="icon-btn" :aria-label="`移除 ${file.name}`" @click.stop="removeFile(file.id)"><Trash2 :size="15" /></button>
            </article>
          </div>

          <div v-else class="upload-empty-note">
            <ScanText :size="20" />
            <span>文件只会在您上传后出现在本页</span>
          </div>
        </div>

        <div
          class="stage-flow"
          :class="{
            active: uploadedFiles.length,
            complete: isReady,
            confirmed,
            processing: isProcessing,
            [`pace-${activeStagePace}`]: isProcessing,
          }"
          aria-live="polite"
        >
          <div class="stage-flow-head">
            <span class="stage-flow-title">
              <LoaderCircle v-if="isProcessing" :size="15" class="spin" />
              <CheckCircle2 v-else-if="confirmed || isReady" :size="15" />
              <Sparkles v-else :size="15" />
              {{ flowHeadline }}
            </span>
            <b v-if="stageCounterLabel">{{ stageCounterLabel }}</b>
          </div>

          <ol class="stage-list">
            <li
              v-for="(stage, index) in PROCESS_STAGES"
              :key="stage.key"
              class="stage-item"
              :class="[
                stageState(index),
                stageState(index) === 'active' ? `pace-${stage.pace}` : '',
                stage.key,
              ]"
            >
              <span class="stage-marker">
                <CheckCircle2 v-if="stageState(index) === 'done'" :size="14" />
                <LoaderCircle v-else-if="stageState(index) === 'active' && isProcessing" :size="14" class="spin" />
                <span v-else class="stage-index">{{ index + 1 }}</span>
              </span>
              <span class="stage-copy">
                <strong>{{ stage.label }}</strong>
                <small>{{ stageDetailText(index) }}</small>
              </span>
            </li>
          </ol>

          <div class="stage-meter" aria-hidden="true">
            <span :style="{ width: `${stageMeterPercent}%` }"></span>
          </div>
          <p class="stage-hint">{{ activeStageHint }}</p>
        </div>
      </section>

      <section class="report-panel panel-surface" aria-labelledby="report-title">
        <div class="panel-heading compact-heading">
          <div class="heading-icon"><Sparkles :size="18" /></div>
          <div>
            <h3 id="report-title">AI解析报告</h3>
            <p>文档理解、摘要、识别重点与辅助结构化数据</p>
          </div>
        </div>

        <div v-if="processStatus === 'complete' && primaryInsight" class="report-scroll" data-testid="ai-parse-report">
          <article
            v-for="insight in insights"
            :key="insight.fileId"
            class="report-article"
          >
            <header class="report-file-head">
              <strong :title="insight.fileName">{{ insight.fileName }}</strong>
              <small>识别置信度 {{ insight.confidence || '待确认' }}</small>
            </header>

            <section class="report-section" aria-labelledby="understand-title">
              <h4 id="understand-title">文档理解</h4>
              <div class="understand-grid">
                <div>
                  <small>文件类型</small>
                  <b>{{ fieldValue(insight.documentUnderstanding?.fileType || insight.documentType) }}</b>
                </div>
                <div>
                  <small>项目</small>
                  <b>{{ fieldValue(insight.documentUnderstanding?.project || mockData.project.name) }}</b>
                </div>
                <div>
                  <small>周期</small>
                  <b>{{ fieldValue(insight.documentUnderstanding?.period || insight.period) }}</b>
                </div>
                <div>
                  <small>建设阶段</small>
                  <b>{{ fieldValue(insight.documentUnderstanding?.constructionStage || mockData.project.stage) }}</b>
                </div>
              </div>
            </section>

            <section class="report-section" aria-labelledby="summary-title">
              <h4 id="summary-title">AI摘要</h4>
              <div v-if="insight.aiSummary?.length" class="ai-summary">
                <p v-for="(paragraph, index) in insight.aiSummary" :key="`${insight.fileId}-p-${index}`">
                  {{ paragraph }}
                </p>
              </div>
              <p v-else class="muted-empty">未识别</p>
            </section>

            <section class="report-section" aria-labelledby="highlights-title">
              <h4 id="highlights-title">AI识别重点</h4>
              <div v-if="insight.highlightItems?.length" class="highlight-list">
                <article
                  v-for="(item, index) in insight.highlightItems"
                  :key="`${insight.fileId}-h-${index}`"
                  class="highlight-card"
                  :class="highlightTypeClass(item.type)"
                >
                  <div class="highlight-card-head">
                    <strong>{{ item.name || '待确认' }}</strong>
                    <span>{{ item.type || '待确认' }}</span>
                  </div>
                  <p><small>内容</small>{{ fieldValue(item.content) }}</p>
                  <p class="highlight-focus"><small>关注点</small>{{ fieldValue(item.focus) }}</p>
                </article>
              </div>
              <p v-else class="muted-empty">未识别</p>
            </section>

            <section class="report-section auxiliary-section" aria-labelledby="structured-title">
              <h4 id="structured-title">结构化数据（辅助）</h4>
              <p class="section-note">以下为 AI 提取字段，用于支撑摘要核对，非主展示内容。</p>
              <div class="structured-groups">
                <article class="structured-group">
                  <strong><span>工</span>工程</strong>
                  <div v-if="insight.structuredData?.engineering?.length">
                    <div v-for="item in insight.structuredData.engineering" :key="`eng-${item.label}`">
                      <small>{{ item.label }}</small>
                      <b>{{ fieldValue(item.value) }}</b>
                    </div>
                  </div>
                  <p v-else class="muted-empty">未识别</p>
                </article>
                <article class="structured-group safety-group">
                  <strong><span>安</span>安全</strong>
                  <div v-if="insight.structuredData?.safety?.length">
                    <div v-for="item in insight.structuredData.safety" :key="`saf-${item.label}`">
                      <small>{{ item.label }}</small>
                      <b>{{ fieldValue(item.value) }}</b>
                    </div>
                  </div>
                  <p v-else class="muted-empty">未识别</p>
                </article>
                <article class="structured-group environment-group">
                  <strong><span>环</span>环境</strong>
                  <div v-if="insight.structuredData?.environment?.length">
                    <div v-for="item in insight.structuredData.environment" :key="`env-${item.label}`">
                      <small>{{ item.label }}</small>
                      <b>{{ fieldValue(item.value) }}</b>
                    </div>
                  </div>
                  <p v-else class="muted-empty">未识别</p>
                </article>
              </div>
            </section>

            <section class="report-section" aria-labelledby="notes-title">
              <h4 id="notes-title">AI识别说明</h4>
              <div class="notes-grid">
                <div>
                  <small>识别章节</small>
                  <b>{{ insight.recognitionNotes?.chapterCount ?? '未识别' }}{{ insight.recognitionNotes ? ' 个' : '' }}</b>
                </div>
                <div>
                  <small>识别表格</small>
                  <b>{{ insight.recognitionNotes?.tableCount ?? '未识别' }}{{ insight.recognitionNotes ? ' 张' : '' }}</b>
                </div>
                <div>
                  <small>关键事项</small>
                  <b>{{ insight.recognitionNotes?.keyItemCount ?? '未识别' }}{{ insight.recognitionNotes ? ' 项' : '' }}</b>
                </div>
              </div>
              <p class="confirm-hint">
                {{ insight.recognitionNotes?.confirmHint || '以下内容建议业务人员确认后入库' }}
              </p>
            </section>
          </article>
        </div>

        <div v-else-if="isProcessing" class="loading-state">
          <LoaderCircle :size="27" class="spin" />
          <strong>正在生成 AI 解析报告</strong>
          <span>先理解文档，再整理摘要与识别重点</span>
          <div class="skeleton-lines"><i></i><i></i><i></i></div>
        </div>

        <div v-else class="empty-state">
          <FileText :size="28" />
          <strong>AI 解析报告将在这里显示</strong>
          <span>当前未上传任何文件</span>
        </div>
      </section>

      <section class="result-panel panel-surface" :class="resultPanelClass" aria-labelledby="result-title">
        <div class="panel-heading compact-heading">
          <div class="heading-icon"><Database :size="18" /></div>
          <div><h3 id="result-title">入库建议</h3><p>解析完成后生成业务对象，待确认入库</p></div>
        </div>

        <div class="result-status">
          <span class="result-icon">
            <CheckCircle2 v-if="confirmed" :size="32" />
            <CheckCircle2 v-else-if="isReady" :size="32" />
            <LoaderCircle v-else-if="isProcessing" :size="32" class="spin" />
            <Database v-else :size="30" />
          </span>
          <strong>{{ resultTitle }}</strong>
          <p v-if="confirmed">入库已确认，可继续在本页核对资料</p>
          <p v-else-if="isReady">已整理 {{ mockData.ingestionSuggestion.objects.length }} 类业务对象</p>
          <p v-else-if="isProcessing">AI 正在按阶段识别资料并生成结果</p>
          <p v-else>上传文件后自动开始解析</p>
          <div v-if="isReady || confirmed" class="status-chip" :class="{ confirmed }">
            当前状态：{{ ingestionStatusLabel }}
          </div>
        </div>

        <section v-if="isReady" class="generated-objects">
          <h4>生成业务对象</h4>
          <ul>
            <li v-for="item in mockData.ingestionSuggestion.objects" :key="item"><CheckCircle2 :size="14" />{{ item }}</li>
          </ul>
        </section>

        <div class="confirm-block">
          <p class="confirm-summary">{{ confirmSummary }}</p>
          <button
            type="button"
            class="confirm-btn"
            :disabled="!isReady || confirmed"
            @click="confirmIngestion"
          >
            <CheckCircle2 :size="16" />
            <span>{{ confirmed ? '已确认入库' : '确认入库' }}</span>
          </button>
        </div>
      </section>
    </main>
  </section>
</template>

<style scoped>
.smart-entry,
.smart-entry * { box-sizing: border-box; }

.smart-entry {
  --entry-surface: #071a2a;
  --entry-card: #0a2234;
  --entry-border: #183a52;
  --entry-blue: #23a9ff;
  --entry-green: #37c985;
  --entry-text: #edf6ff;
  --entry-muted: #87a4b9;
  width: 100%;
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-bottom: 18px;
  color: var(--entry-text);
  font-size: 14px;
}

button, input { font: inherit; }
button { color: inherit; }
.visually-hidden { position: fixed; width: 1px; height: 1px; opacity: 0; pointer-events: none; }

.entry-heading {
  min-height: 62px;
  flex: 0 0 62px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 18px;
  border: 1px solid rgba(35, 169, 255, .2);
  border-left: 3px solid var(--entry-blue);
  border-radius: 5px;
  background: linear-gradient(100deg, rgba(7, 26, 42, .96), rgba(10, 34, 52, .78));
}
.entry-heading h2 { margin: 0; font-size: 22px; line-height: 1; letter-spacing: .03em; }
.entry-heading p { margin: 7px 0 0; color: var(--entry-muted); font-size: 13px; }
.automatic-badge { display: inline-flex; align-items: center; gap: 7px; padding: 8px 12px; border: 1px solid rgba(55, 201, 133, .34); border-radius: 4px; background: rgba(55, 201, 133, .08); color: #78e0ad; font-size: 12px; }

.page-alert { min-height: 34px; padding: 8px 12px; border: 1px solid rgba(244, 182, 74, .35); border-radius: 4px; background: rgba(244, 182, 74, .08); color: #ffd68a; }
.page-success { min-height: 34px; padding: 8px 12px; border: 1px solid rgba(55, 201, 133, .35); border-radius: 4px; background: rgba(55, 201, 133, .08); color: #8fe0b6; }
.panel-surface { border: 1px solid var(--entry-border); border-radius: 5px; background: linear-gradient(180deg, rgba(7, 26, 42, .98), rgba(5, 22, 36, .98)); }

.one-page-workbench {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) minmax(280px, .78fr);
  grid-template-rows: auto minmax(0, 1fr);
  gap: 14px;
}
.upload-panel { grid-column: 1 / -1; padding: 13px 15px; }
.report-panel, .result-panel {
  min-height: 0;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

/* Ready: shrink upload band so results dominate the lower viewport */
.one-page-workbench.is-ready {
  grid-template-rows: auto minmax(0, 1.4fr);
  gap: 12px;
}
.upload-panel.compact { padding: 8px 14px 10px; }
.upload-panel.compact .panel-heading { min-height: 34px; }
.upload-panel.compact .panel-heading p { display: none; }
.upload-panel.compact .upload-content {
  min-height: 0;
  margin-top: 6px;
  gap: 10px;
}
.upload-panel.compact .drop-zone,
.upload-panel.compact .drop-zone.compact {
  min-height: 52px;
  padding: 8px 12px;
  gap: 10px;
}
.upload-panel.compact .drop-icon {
  width: 34px;
  height: 34px;
  flex-basis: 34px;
}
.upload-panel.compact .drop-zone small { display: none; }
.upload-panel.compact .drop-zone strong { font-size: 13px; }
.upload-panel.compact .file-list { max-height: 56px; gap: 4px; }
.upload-panel.compact .file-row { min-height: 36px; padding: 3px 8px; }
.upload-panel.compact .stage-flow {
  margin-top: 8px;
  padding: 8px 10px;
}
.upload-panel.compact .stage-copy small,
.upload-panel.compact .stage-hint { display: none; }
.upload-panel.compact .stage-list { gap: 6px; }
.upload-panel.compact .stage-item { padding: 5px 6px; }
.upload-panel.compact .stage-copy strong { font-size: 12px; }

.panel-heading { min-height: 44px; display: flex; align-items: center; gap: 10px; }
.compact-heading { flex: 0 0 48px; padding-bottom: 12px; border-bottom: 1px solid rgba(24, 58, 82, .72); }
.heading-icon { width: 36px; height: 36px; flex: 0 0 36px; display: grid; place-items: center; border-radius: 4px; background: rgba(35, 169, 255, .1); color: #69c9ff; }
.panel-heading h3 { margin: 0; font-size: 16px; }
.panel-heading p { margin: 4px 0 0; color: #6f8da2; font-size: 12px; }
.file-count { margin-left: auto; color: #79d4ff; font-size: 12px; }
.text-btn { min-height: 30px; padding: 0 10px; border: 1px solid rgba(35, 169, 255, .3); border-radius: 4px; background: rgba(35, 169, 255, .07); color: #8bd4ff; font-size: 12px; cursor: pointer; }
.text-btn:hover { border-color: var(--entry-blue); color: #fff; }

.upload-content { min-height: 96px; display: grid; grid-template-columns: minmax(360px, .8fr) minmax(0, 1.7fr); gap: 12px; margin-top: 10px; }
.drop-zone { min-height: 96px; display: flex; align-items: center; gap: 13px; padding: 15px 18px; border: 1px dashed rgba(35, 169, 255, .46); border-radius: 5px; background: radial-gradient(circle at 14% 50%, rgba(35, 169, 255, .1), transparent 38%), rgba(10, 34, 52, .52); text-align: left; cursor: pointer; transition: .18s ease; }
.drop-zone:hover, .drop-zone.dragging { border-color: var(--entry-blue); background-color: rgba(10, 42, 67, .72); }
.drop-zone.compact { min-height: 72px; padding: 12px 14px; }
.drop-icon { width: 48px; height: 48px; flex: 0 0 48px; display: grid; place-items: center; border: 1px solid rgba(35, 169, 255, .42); border-radius: 50%; background: rgba(35, 169, 255, .09); color: var(--entry-blue); }
.drop-zone > span:last-child { min-width: 0; display: flex; flex-direction: column; gap: 7px; }
.drop-zone strong { font-size: 14px; }
.drop-zone small { color: var(--entry-muted); font-size: 11px; }
.upload-empty-note { min-height: 96px; display: flex; align-items: center; justify-content: center; gap: 9px; border: 1px solid rgba(24, 58, 82, .62); border-radius: 4px; background: rgba(6, 25, 40, .42); color: #5f8198; font-size: 12px; }

.file-list { max-height: 148px; display: flex; flex-direction: column; gap: 6px; overflow: auto; padding-right: 3px; }
.file-row { min-height: 45px; display: grid; grid-template-columns: 40px minmax(0, 1fr) 70px 30px; align-items: center; gap: 9px; padding: 5px 8px; border: 1px solid rgba(24, 58, 82, .78); border-radius: 4px; background: rgba(10, 34, 52, .62); }
.file-type-icon { width: 36px; height: 34px; display: flex; align-items: center; justify-content: center; flex-direction: column; gap: 1px; border-radius: 3px; background: rgba(35, 169, 255, .09); color: #69c8ff; }
.file-type-icon small { font-size: 8px; font-weight: 800; }
.file-primary { min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.file-primary strong { overflow: hidden; color: #ddecf7; font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.file-primary small { color: #6e8ba0; font-size: 11px; }
.file-ready { display: flex; align-items: center; gap: 4px; color: #70dda9; font-size: 12px; }
.icon-btn { width: 28px; height: 28px; display: grid; place-items: center; border: 1px solid transparent; border-radius: 3px; background: transparent; color: #6f8da2; cursor: pointer; }
.icon-btn:hover { border-color: rgba(255, 103, 111, .35); background: rgba(255, 79, 94, .08); color: #ff7b83; }

.stage-flow {
  margin-top: 11px;
  padding: 12px 12px 10px;
  border: 1px solid rgba(24, 58, 82, .72);
  border-radius: 4px;
  background: rgba(6, 25, 40, .48);
}
.stage-flow.active { border-color: rgba(35, 169, 255, .26); }
.stage-flow.complete { border-color: rgba(55, 201, 133, .28); }
.stage-flow.confirmed { border-color: rgba(55, 201, 133, .4); }
.stage-flow-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
  color: #7fa0b6;
  font-size: 12px;
}
.stage-flow-title { display: inline-flex; align-items: center; gap: 7px; }
.stage-flow.complete .stage-flow-title,
.stage-flow.confirmed .stage-flow-title { color: var(--entry-green); }
.stage-flow-head b { color: #73cdff; font-variant-numeric: tabular-nums; }
.stage-list {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.stage-item {
  min-width: 0;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 8px;
  border: 1px solid rgba(24, 58, 82, .7);
  border-radius: 4px;
  background: rgba(10, 34, 52, .45);
  transition: border-color .18s ease, background .18s ease;
}
.stage-item.done {
  border-color: rgba(55, 201, 133, .28);
  background: rgba(55, 201, 133, .06);
}
.stage-item.active {
  border-color: rgba(35, 169, 255, .45);
  background: rgba(35, 169, 255, .08);
}
.stage-item.active.pace-fast { animation: stage-pulse .85s ease-in-out infinite; }
.stage-item.active.pace-medium { animation: stage-pulse 1.35s ease-in-out infinite; }
.stage-item.active.pace-slow { animation: stage-pulse 2.15s ease-in-out infinite; }
.stage-item.active.extract {
  border-color: rgba(55, 201, 133, .38);
  background: rgba(35, 169, 255, .07);
}
.stage-item.active.suggest {
  border-color: rgba(244, 182, 74, .42);
  background: rgba(244, 182, 74, .07);
}
.stage-item.active.confirm {
  border-color: rgba(55, 201, 133, .4);
  background: rgba(55, 201, 133, .07);
  animation: none;
}
.stage-item.pending { opacity: .72; }
.stage-marker {
  width: 22px;
  height: 22px;
  flex: 0 0 22px;
  display: grid;
  place-items: center;
  margin-top: 1px;
  border-radius: 50%;
  border: 1px solid rgba(24, 58, 82, .8);
  color: #6f8da2;
  background: rgba(5, 22, 36, .55);
}
.stage-item.done .stage-marker {
  border-color: rgba(55, 201, 133, .45);
  color: #65dfa4;
  background: rgba(55, 201, 133, .1);
}
.stage-item.active .stage-marker {
  border-color: rgba(35, 169, 255, .5);
  color: #69c9ff;
  background: rgba(35, 169, 255, .12);
}
.stage-index { font-size: 11px; font-weight: 700; line-height: 1; }
.stage-copy { min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.stage-copy strong {
  overflow: hidden;
  color: #d5e8f4;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.stage-item.active .stage-copy strong { color: #8fd7ff; }
.stage-item.active.extract .stage-copy strong { color: #8fe0b6; }
.stage-item.active.suggest .stage-copy strong { color: #f2c66e; }
.stage-item.done .stage-copy strong { color: #b7ebcf; }
.stage-copy small {
  overflow: hidden;
  color: #6f8da2;
  font-size: 10px;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  min-height: 2.7em;
}
.stage-item.active .stage-copy small { color: #8eafc3; }
.stage-meter {
  height: 4px;
  margin-top: 10px;
  overflow: hidden;
  border-radius: 8px;
  background: #102e43;
}
.stage-meter span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #198fd4, #39c4ff, #52d9a0);
  transition: width .28s ease;
}
.stage-hint {
  margin: 8px 0 0;
  color: #5f7f96;
  font-size: 11px;
  line-height: 1.45;
}

.report-scroll {
  min-height: 0;
  flex: 1;
  overflow: auto;
  padding: 12px 6px 4px 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.report-article {
  padding: 14px 16px 16px;
  border: 1px solid rgba(24, 58, 82, .78);
  border-left: 3px solid rgba(35, 169, 255, .65);
  border-radius: 4px;
  background: rgba(10, 34, 52, .62);
}
.report-file-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 4px;
}
.report-file-head strong {
  min-width: 0;
  overflow: hidden;
  color: #dcecf6;
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.report-file-head small { flex: 0 0 auto; color: #6f91a8; font-size: 12px; }

.report-section {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed rgba(24, 58, 82, .72);
}
.report-section h4,
.generated-objects h4 {
  margin: 0 0 10px;
  color: #8fd7ff;
  font-size: 13px;
  letter-spacing: .06em;
}
.section-note {
  margin: -2px 0 10px;
  color: #6f8da2;
  font-size: 12px;
  line-height: 1.5;
}
.muted-empty {
  margin: 0;
  color: #66889f;
  font-size: 13px;
}

.understand-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}
.understand-grid > div,
.notes-grid > div {
  min-width: 0;
  padding: 10px 12px;
  border: 1px solid rgba(24, 58, 82, .68);
  border-radius: 3px;
  background: rgba(5, 22, 36, .48);
}
.understand-grid small,
.notes-grid small {
  display: block;
  margin-bottom: 5px;
  color: #66889f;
  font-size: 11px;
}
.understand-grid b,
.notes-grid b {
  display: block;
  overflow: hidden;
  color: #d7ebf7;
  font-size: 15px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ai-summary {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.ai-summary p {
  margin: 0;
  color: #b7c9d6;
  font-size: 14px;
  line-height: 1.75;
}

.highlight-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.highlight-card {
  min-width: 0;
  padding: 12px 12px 11px;
  border: 1px solid rgba(24, 58, 82, .75);
  border-radius: 4px;
  background: rgba(5, 22, 36, .5);
}
.highlight-card.type-safety { border-left: 3px solid rgba(244, 182, 74, .7); }
.highlight-card.type-environment { border-left: 3px solid rgba(55, 201, 133, .65); }
.highlight-card.type-engineering { border-left: 3px solid rgba(35, 169, 255, .65); }
.highlight-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}
.highlight-card-head strong {
  min-width: 0;
  overflow: hidden;
  color: #e5f3fb;
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.highlight-card-head span {
  flex: 0 0 auto;
  padding: 2px 8px;
  border-radius: 3px;
  background: rgba(35, 169, 255, .12);
  color: #73ccff;
  font-size: 11px;
}
.highlight-card.type-safety .highlight-card-head span {
  background: rgba(244, 182, 74, .12);
  color: #f2c66e;
}
.highlight-card.type-environment .highlight-card-head span {
  background: rgba(55, 201, 133, .12);
  color: #78e0ad;
}
.highlight-card > p {
  margin: 0;
  color: #9ab0bf;
  font-size: 13px;
  line-height: 1.55;
}
.highlight-card > p + p { margin-top: 7px; }
.highlight-card small {
  display: inline-block;
  margin-right: 6px;
  color: #66889f;
  font-size: 11px;
}
.highlight-focus { color: #a9becb !important; }

.auxiliary-section { opacity: .96; }
.structured-groups {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}
.structured-group {
  padding: 11px 12px;
  border: 1px solid rgba(24, 58, 82, .7);
  border-radius: 4px;
  background: rgba(6, 25, 40, .42);
}
.structured-group > strong {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  color: #c2d6e3;
  font-size: 13px;
}
.structured-group > strong span {
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  border-radius: 3px;
  background: rgba(35, 169, 255, .12);
  color: #69c9ff;
  font-size: 11px;
}
.safety-group > strong span {
  background: rgba(244, 182, 74, .12);
  color: #f4c56c;
}
.environment-group > strong span {
  background: rgba(55, 201, 133, .13);
  color: #66dca2;
}
.structured-group > div > div {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  padding: 7px 0;
  border-top: 1px dashed rgba(24, 58, 82, .55);
}
.structured-group small {
  color: #718fa4;
  font-size: 12px;
  line-height: 1.4;
}
.structured-group b {
  max-width: 58%;
  color: #d5e8f3;
  font-size: 13px;
  font-weight: 600;
  text-align: right;
  line-height: 1.4;
}

.notes-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}
.confirm-hint {
  margin: 12px 0 0;
  padding: 10px 12px;
  border: 1px solid rgba(244, 182, 74, .28);
  border-radius: 4px;
  background: rgba(244, 182, 74, .07);
  color: #e6c57a;
  font-size: 13px;
  line-height: 1.5;
}

.empty-state, .loading-state { flex: 1; min-height: 170px; display: flex; align-items: center; justify-content: center; flex-direction: column; gap: 9px; color: #55778f; text-align: center; }
.empty-state strong, .loading-state strong { color: #819eb1; font-size: 14px; }
.empty-state span, .loading-state span { color: #58778e; font-size: 12px; }
.loading-state { color: var(--entry-blue); }
.skeleton-lines { width: min(300px, 75%); display: grid; gap: 7px; margin-top: 8px; }
.skeleton-lines i { height: 6px; border-radius: 6px; background: linear-gradient(90deg, rgba(35, 169, 255, .06), rgba(35, 169, 255, .2), rgba(35, 169, 255, .06)); background-size: 200% 100%; animation: shimmer 1.3s infinite; }
.skeleton-lines i:nth-child(2) { width: 86%; }
.skeleton-lines i:nth-child(3) { width: 68%; }

.result-panel { border-color: rgba(35, 169, 255, .2); }
.result-panel.complete,
.result-panel.confirmed {
  background: radial-gradient(circle at 50% 18%, rgba(244, 182, 74, .08), transparent 38%), linear-gradient(180deg, rgba(7, 26, 42, .98), rgba(5, 22, 36, .98));
}
.result-panel.confirmed {
  background: radial-gradient(circle at 50% 18%, rgba(55, 201, 133, .1), transparent 38%), linear-gradient(180deg, rgba(7, 26, 42, .98), rgba(5, 22, 36, .98));
}
.result-status { display: flex; align-items: center; flex-direction: column; padding: 18px 10px 12px; text-align: center; }
.result-icon { width: 64px; height: 64px; display: grid; place-items: center; margin-bottom: 12px; border: 1px solid rgba(55, 201, 133, .32); border-radius: 50%; background: rgba(55, 201, 133, .08); color: #65dfa4; }
.result-panel.complete .result-icon { border-color: rgba(244, 182, 74, .38); background: rgba(244, 182, 74, .08); color: #f2c66e; }
.result-panel.confirmed .result-icon { border-color: rgba(55, 201, 133, .42); background: rgba(55, 201, 133, .1); color: #65dfa4; }
.result-panel.idle .result-icon { border-color: #2d5068; background: rgba(35, 169, 255, .05); color: #55798f; }
.result-panel.analyzing .result-icon, .result-panel.preparing .result-icon { border-color: rgba(35, 169, 255, .38); color: #5fc9ff; }
.result-status strong { font-size: 16px; }
.result-status p { margin: 8px 0 0; color: #7694a9; font-size: 12px; line-height: 1.55; }
.status-chip {
  margin-top: 12px;
  padding: 6px 12px;
  border: 1px solid rgba(244, 182, 74, .4);
  border-radius: 4px;
  background: rgba(244, 182, 74, .1);
  color: #f2c66e;
  font-size: 13px;
  font-weight: 600;
}
.status-chip.confirmed {
  border-color: rgba(55, 201, 133, .4);
  background: rgba(55, 201, 133, .1);
  color: #78e0ad;
}
.generated-objects { margin: 2px 0 12px; padding: 12px 12px; border: 1px solid rgba(24, 58, 82, .7); border-radius: 4px; background: rgba(6, 25, 40, .46); }
.generated-objects ul { display: grid; grid-template-columns: 1fr; gap: 9px; margin: 0; padding: 0; list-style: none; }
.generated-objects li { display: flex; align-items: center; gap: 6px; min-width: 0; color: #a9c1cf; font-size: 12px; line-height: 1.4; }
.generated-objects li svg { flex: 0 0 auto; color: #65dca2; }
.confirm-block {
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid rgba(24, 58, 82, .7);
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.confirm-summary {
  margin: 0;
  color: #9ab4c5;
  font-size: 13px;
  line-height: 1.6;
}
.confirm-btn {
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 16px;
  border: 1px solid rgba(55, 201, 133, .45);
  border-radius: 4px;
  background: linear-gradient(180deg, rgba(55, 201, 133, .22), rgba(55, 201, 133, .12));
  color: #b8f0d2;
  font-size: 15px;
  font-weight: 650;
  cursor: pointer;
  transition: border-color .15s ease, background .15s ease, opacity .15s ease;
}
.confirm-btn:hover:not(:disabled) {
  border-color: rgba(55, 201, 133, .7);
  background: linear-gradient(180deg, rgba(55, 201, 133, .32), rgba(55, 201, 133, .16));
  color: #e8fff3;
}
.confirm-btn:disabled {
  cursor: default;
  opacity: .55;
  border-color: rgba(24, 58, 82, .8);
  background: rgba(10, 34, 52, .55);
  color: #6f8da2;
}
.result-panel.confirmed .confirm-btn:disabled {
  opacity: 1;
  border-color: rgba(55, 201, 133, .35);
  background: rgba(55, 201, 133, .1);
  color: #78e0ad;
}

.spin { animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes shimmer { to { background-position: -200% 0; } }
@keyframes stage-pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(35, 169, 255, 0);
    transform: translateY(0);
  }
  50% {
    box-shadow: 0 0 0 3px rgba(35, 169, 255, .14);
    transform: translateY(-1px);
  }
}

@media (max-width: 1450px) {
  .entry-heading { min-height: 56px; flex-basis: 56px; }
  .upload-content { grid-template-columns: minmax(320px, .7fr) minmax(0, 1.5fr); }
  .one-page-workbench { grid-template-columns: minmax(0, 1.55fr) minmax(260px, .78fr); gap: 11px; }
  .report-panel, .result-panel { padding: 14px; }
  .understand-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .structured-groups { grid-template-columns: 1fr; }
  .highlight-list { grid-template-columns: 1fr; }
  .stage-list { gap: 6px; }
  .stage-copy small { -webkit-line-clamp: 1; }
}

@media (max-width: 1080px) {
  .smart-entry { overflow: auto; }
  .one-page-workbench { grid-template-columns: 1fr; grid-template-rows: auto auto auto; }
  .one-page-workbench.is-ready { grid-template-rows: auto auto auto; }
  .upload-panel { grid-column: 1 / -1; }
  .upload-content { grid-template-columns: 1fr; }
  .stage-list { grid-template-columns: 1fr 1fr; }
  .understand-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .notes-grid { grid-template-columns: 1fr; }
}
</style>
