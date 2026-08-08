<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  catalogStatusRank,
  ESG_ACCESS_MODES,
  ESG_DATA_CATALOG,
  ESG_DATA_DOMAINS,
  ESG_DATA_NATURES,
  ESG_DATA_STATUSES,
  formatDependencyHint,
  getCatalogItem,
  getCatalogStatusSummary,
  getUploadableCatalog,
  isCatalogUploadable,
  resolveTemplateDownloadUrl,
  WORKBENCH_UPLOADABLE_LIMIT,
  type EsgDataTableItem,
} from '@/data/esg-data-catalog'
import { confirmEsgExcelImport, uploadEsgExcelImport } from '@/services/api'
import { useDashboardStore } from '@/stores/dashboard.store'
import {
  buildValidationDetailRows,
  buildValidationStats,
  hasPointDependencyError,
  mapSessionBatch,
  matchCatalogFromUpload,
  type RecentBatchRow,
  type RecognizeOutcome,
} from '@/utils/esg-import-presenter'
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  Download,
  FileSpreadsheet,
  LayoutGrid,
  List,
  LoaderCircle,
  Search,
  UploadCloud,
  X,
} from 'lucide-vue-next'

type PageView = 'workbench' | 'catalog'

interface UploadSession {
  id: string
  file: File
  catalogId: string | null
  recognize: RecognizeOutcome | null
  parsed: Record<string, unknown> | null
  recognizing: boolean
  confirmed: boolean
  insertedCount?: number
  updatedCount?: number
}

const dashboardStore = useDashboardStore()

const pageView = ref<PageView>('workbench')
const searchKeyword = ref('')
const filterDomain = ref('')
const filterNature = ref('')
const filterAccess = ref('')
const filterStatus = ref('')
const filterAssociation = ref('')

const activeCatalogId = ref<string | null>(null)
const uploadSessions = ref<UploadSession[]>([])
const pendingCatalogPick = ref<string[]>([])
const pendingFile = ref<File | null>(null)
const isDragging = ref(false)
const pageError = ref('')
const pageMessage = ref('')
const confirming = ref(false)
const recentBatches = ref<RecentBatchRow[]>([])

const fileInputRef = ref<HTMLInputElement | null>(null)

const activeCatalog = computed(() =>
  activeCatalogId.value ? getCatalogItem(activeCatalogId.value) : undefined,
)

const uploadableTables = computed(() => getUploadableCatalog())

const workbenchTables = computed(() => {
  const all = uploadableTables.value
  if (all.length <= WORKBENCH_UPLOADABLE_LIMIT) return all
  const recentIds = new Set(
    uploadSessions.value
      .map((s) => s.catalogId)
      .filter((id): id is string => Boolean(id)),
  )
  const prioritized = all.filter((item) => recentIds.has(item.id))
  const rest = all.filter((item) => !recentIds.has(item.id))
  return [...prioritized, ...rest].slice(0, WORKBENCH_UPLOADABLE_LIMIT)
})

const catalogSummary = computed(() => getCatalogStatusSummary())

const pendingTasks = computed(() => {
  const tasks: Array<{
    id: string
    title: string
    tableName: string
    status: string
    tone: 'wait' | 'bad' | 'ok' | 'warn'
  }> = []

  for (const session of uploadSessions.value) {
    const tableName = session.catalogId
      ? getCatalogItem(session.catalogId)?.name || '待识别数据表'
      : '待识别数据表'
    if (session.recognizing) {
      tasks.push({ id: session.id, title: session.file.name, tableName, status: '识别中', tone: 'wait' })
      continue
    }
    if (session.recognize?.unrecognized) {
      tasks.push({ id: session.id, title: session.file.name, tableName, status: '待识别', tone: 'warn' })
      continue
    }
    if (session.confirmed) continue
    if (session.parsed && !session.parsed.ok) {
      tasks.push({ id: session.id, title: session.file.name, tableName, status: '校验失败', tone: 'bad' })
      continue
    }
    if (session.parsed?.ok && session.parsed.batch_code) {
      tasks.push({ id: session.id, title: session.file.name, tableName, status: '待确认入库', tone: 'ok' })
    }
  }
  return tasks
})

const filteredCatalog = computed(() => {
  let list = [...ESG_DATA_CATALOG]
  const kw = searchKeyword.value.trim().toLowerCase()
  if (kw) {
    list = list.filter(
      (item) =>
        item.name.toLowerCase().includes(kw)
        || item.description.toLowerCase().includes(kw)
        || item.displayAssociations.some((a) => a.toLowerCase().includes(kw)),
    )
  }
  if (filterDomain.value) list = list.filter((item) => item.domain === filterDomain.value)
  if (filterNature.value) list = list.filter((item) => item.nature === filterNature.value)
  if (filterAccess.value) list = list.filter((item) => item.accessMode === filterAccess.value)
  if (filterStatus.value) list = list.filter((item) => item.status === filterStatus.value)
  if (filterAssociation.value) {
    const assoc = filterAssociation.value.toLowerCase()
    list = list.filter((item) =>
      item.displayAssociations.some((a) => a.toLowerCase().includes(assoc)),
    )
  }
  list.sort((a, b) => {
    const rank = catalogStatusRank(a.status) - catalogStatusRank(b.status)
    if (rank !== 0) return rank
    return (a.sortOrder ?? 99) - (b.sortOrder ?? 99)
  })
  return list
})

const catalogGroups = computed(() => {
  const map = new Map<string, EsgDataTableItem[]>()
  for (const item of filteredCatalog.value) {
    const bucket = map.get(item.domain) || []
    bucket.push(item)
    map.set(item.domain, bucket)
  }
  return [...map.entries()]
})

const activeSessions = computed(() =>
  activeCatalogId.value
    ? uploadSessions.value.filter((s) => s.catalogId === activeCatalogId.value)
    : uploadSessions.value,
)

const latestSession = computed(() => activeSessions.value[activeSessions.value.length - 1])

const aggregateStats = computed(() => {
  const sessions = activeSessions.value.filter((s) => s.parsed && !s.recognizing)
  if (!sessions.length) return null
  return sessions.reduce(
    (acc, s) => {
      const stats = buildValidationStats(s.parsed)
      acc.readCount += stats.readCount
      acc.emptyRowCount += stats.emptyRowCount
      acc.passCount += stats.passCount
      acc.warningCount += stats.warningCount
      acc.errorCount += stats.errorCount
      acc.skipCount += stats.skipCount
      acc.blockCount += stats.blockCount
      return acc
    },
    {
      readCount: 0,
      emptyRowCount: 0,
      passCount: 0,
      warningCount: 0,
      errorCount: 0,
      expectedInsert: null as number | null,
      expectedUpdate: null as number | null,
      skipCount: 0,
      blockCount: 0,
    },
  )
})

const validationRows = computed(() =>
  activeSessions.value.flatMap((s) => buildValidationDetailRows(s.parsed)),
)

const canConfirm = computed(() => {
  const sessions = activeSessions.value
  if (!sessions.length) return false
  if (sessions.some((s) => s.recognizing || s.confirmed)) return false
  if (sessions.some((s) => s.recognize?.unrecognized)) return false
  if (sessions.some((s) => !s.parsed?.ok)) return false
  if (sessions.some((s) => hasPointDependencyError(s.parsed))) return false
  return sessions.every((s) => Boolean(s.parsed?.batch_code))
})

const showE01DualOrder = computed(() => {
  const ids = new Set(uploadSessions.value.map((s) => s.catalogId).filter(Boolean))
  return ids.has('e01-env-monitor-point') && ids.has('e01-env-monitor-result')
})

const confirmBlockedReason = computed(() => {
  if (activeSessions.value.some((s) => s.recognize?.unrecognized)) {
    return '文件尚未识别到数据表，无法确认入库'
  }
  if (activeSessions.value.some((s) => hasPointDependencyError(s.parsed))) {
    return '结果表引用了尚未建立的点位，请先导入环境监测点位表'
  }
  if (activeSessions.value.some((s) => s.parsed && !s.parsed.ok)) {
    return '存在校验错误，已阻断确认入库'
  }
  return ''
})

function statusClass(status: EsgDataTableItem['status']): string {
  if (status === '可上传') return 'status-ready'
  if (status === '已有数据') return 'status-has-data'
  if (status === '建设中') return 'status-building'
  if (status === '仅自动接入') return 'status-auto'
  return 'status-muted'
}

function openUploadFor(item: EsgDataTableItem) {
  if (!isCatalogUploadable(item)) return
  activeCatalogId.value = item.id
  pageError.value = ''
  fileInputRef.value?.click()
}

function selectCatalog(item: EsgDataTableItem) {
  activeCatalogId.value = item.id
  pageError.value = ''
}

function openGenericUpload() {
  activeCatalogId.value = null
  fileInputRef.value?.click()
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files?.length) void ingestFiles(Array.from(input.files))
  input.value = ''
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  isDragging.value = false
  if (event.dataTransfer?.files?.length) void ingestFiles(Array.from(event.dataTransfer.files))
}

async function ingestFiles(files: File[]) {
  pageError.value = ''
  pageMessage.value = ''
  for (const file of files) {
    const ext = file.name.split('.').pop()?.toLowerCase() || ''
    if (!['xlsx', 'xls'].includes(ext)) {
      pageError.value = `暂不支持该格式：${file.name}（请使用 Excel 模板）`
      continue
    }
    await processOneFile(file)
  }
}

async function processOneFile(file: File, forcedCatalogId?: string) {
  const session: UploadSession = {
    id: `${Date.now()}-${file.name}`,
    file,
    catalogId: forcedCatalogId || activeCatalogId.value,
    recognize: null,
    parsed: null,
    recognizing: true,
    confirmed: false,
  }
  uploadSessions.value = [...uploadSessions.value, session]

  const expected = session.catalogId
    ? getCatalogItem(session.catalogId)?.templateCode
    : undefined

  const parsed = await uploadEsgExcelImport(file, expected)
  session.parsed = parsed
  session.recognizing = false

  if (!parsed) {
    session.recognize = {
      catalogIds: [],
      ambiguous: false,
      unrecognized: true,
      combinedE01: false,
      message: '上传服务不可用，请确认 API 已启动',
    }
    pageError.value = session.recognize.message
    return
  }

  const outcome = matchCatalogFromUpload(file.name, parsed)

  if (outcome.ambiguous && !forcedCatalogId) {
    pendingCatalogPick.value = outcome.catalogIds
    pendingFile.value = file
    uploadSessions.value = uploadSessions.value.filter((s) => s.id !== session.id)
    return
  }

  if (outcome.unrecognized && !forcedCatalogId && !activeCatalogId.value) {
    session.recognize = outcome
    session.catalogId = null
    pageError.value = outcome.message
    return
  }

  const catalogId = forcedCatalogId || activeCatalogId.value || outcome.catalogIds[0] || null
  session.catalogId = catalogId
  session.recognize = outcome
  if (catalogId) activeCatalogId.value = catalogId

  if (!parsed.ok) {
    pageError.value = hasPointDependencyError(parsed)
      ? '请先建立对应点位，再上传监测结果表'
      : String(parsed.message || '校验未通过')
  }

  const batchCode = String(parsed.batch_code || '')
  if (batchCode && catalogId) {
    recentBatches.value = [
      mapSessionBatch(batchCode, catalogId, parsed, false),
      ...recentBatches.value.filter((b) => b.id !== batchCode),
    ].slice(0, 20)
  }
}

function resolvePendingPick(catalogId: string) {
  const file = pendingFile.value
  pendingCatalogPick.value = []
  pendingFile.value = null
  if (file) {
    activeCatalogId.value = catalogId
    void processOneFile(file, catalogId)
  }
}

function cancelPendingPick() {
  pendingCatalogPick.value = []
  pendingFile.value = null
}

function removeSession(id: string) {
  uploadSessions.value = uploadSessions.value.filter((s) => s.id !== id)
}

function clearWorkspace() {
  uploadSessions.value = []
  activeCatalogId.value = null
  pageError.value = ''
  pageMessage.value = ''
}

async function confirmIngestion() {
  if (!canConfirm.value || confirming.value) return
  confirming.value = true
  pageError.value = ''
  pageMessage.value = '正在确认入库…'

  const messages: string[] = []
  for (const session of activeSessions.value) {
    const batchCode = String(session.parsed?.batch_code || '')
    if (!batchCode) continue
    const result = await confirmEsgExcelImport(batchCode)
    if (!result?.ok) {
      const rawMsg = String(result?.message || '确认入库失败')
      pageError.value = /尚未建立|点位/.test(rawMsg) ? '请先建立对应点位' : rawMsg
      pageMessage.value = ''
      confirming.value = false
      return
    }
    session.confirmed = true
    session.insertedCount = Number(result.inserted_count ?? 0)
    session.updatedCount = Number(result.updated_count ?? 0)
    messages.push(`新增 ${session.insertedCount} / 更新 ${session.updatedCount}`)
    recentBatches.value = recentBatches.value.map((b) =>
      b.id === batchCode ? { ...b, status: '已完成' as const, successCount: b.readCount } : b,
    )
  }

  await Promise.all([dashboardStore.loadKpis(), dashboardStore.loadEsgHomeStatus()])
  pageMessage.value = `已确认入库（${messages.join('；')}）`
  confirming.value = false
}

function dependencyNames(item: EsgDataTableItem): string {
  return formatDependencyHint(item) || '无前置依赖'
}

function openCatalogView() {
  pageView.value = 'catalog'
}

function backToWorkbench() {
  pageView.value = 'workbench'
}

function focusPendingTask(taskId: string) {
  const session = uploadSessions.value.find((s) => s.id === taskId)
  if (session?.catalogId) activeCatalogId.value = session.catalogId
}
</script>

<template>
  <section class="smart-entry-catalog ws-page ws-page-scroll" data-testid="smart-entry-workbench">
    <input
      ref="fileInputRef"
      class="visually-hidden"
      type="file"
      multiple
      accept=".xlsx,.xls"
      data-testid="file-input"
      @change="handleFileChange"
    />

    <header class="catalog-header">
      <div>
        <h2 class="catalog-title">ESG 智能入库</h2>
        <p class="catalog-subtitle">标准数据表上传、校验与入库确认</p>
      </div>
      <div v-if="activeCatalog" class="active-table-chip">
        当前：{{ activeCatalog.name }}
        <button type="button" class="chip-close" aria-label="清除当前数据表" @click="activeCatalogId = null">
          <X :size="14" />
        </button>
      </div>
    </header>

    <div v-if="pageError" class="page-alert" role="alert">{{ pageError }}</div>
    <div v-else-if="pageMessage" class="page-success" role="status">{{ pageMessage }}</div>

    <!-- 默认工作台：可上传数据表 + 待处理 -->
    <template v-if="pageView === 'workbench'">
      <section class="panel-block" aria-labelledby="workbench-title">
        <div class="block-head">
          <h3 id="workbench-title">当前可上传数据表</h3>
          <button type="button" class="view-switch-btn" @click="openCatalogView">
            <List :size="15" />查看全部数据表
          </button>
        </div>
        <p class="block-lead">按数据表上传与校验，不对单一模块做特殊突出。</p>

        <div class="table-card-grid">
          <article
            v-for="item in workbenchTables"
            :key="item.id"
            class="table-card"
            :class="{ 'is-active': activeCatalogId === item.id }"
          >
            <div class="table-card-head">
              <strong>{{ item.name }}</strong>
              <span class="status-pill status-ready">{{ item.status }}</span>
            </div>
            <p class="table-card-desc">{{ item.description }}</p>
            <p v-if="formatDependencyHint(item)" class="table-card-dep">{{ formatDependencyHint(item) }}</p>
            <p v-else class="table-card-dep muted">无前置依赖</p>
            <div class="table-card-meta">
              <span>{{ item.templateVersion || '—' }} · 含填写示例</span>
              <span>{{ item.accessMode }}</span>
            </div>
            <div class="table-card-actions">
              <a
                v-if="item.templateUrl"
                class="link-btn"
                :href="resolveTemplateDownloadUrl(item.templateUrl)"
                download
              >
                <Download :size="14" />下载模板
              </a>
              <button type="button" class="primary-btn" @click="openUploadFor(item)">
                <UploadCloud :size="14" />上传数据
              </button>
            </div>
          </article>
        </div>

        <p
          v-if="catalogSummary.building || catalogSummary.autoAccess || catalogSummary.other"
          class="catalog-summary-line"
        >
          另有
          <template v-if="catalogSummary.building">{{ catalogSummary.building }} 张建设中</template>
          <template v-if="catalogSummary.autoAccess">
            <template v-if="catalogSummary.building">、</template>{{ catalogSummary.autoAccess }} 张仅自动接入
          </template>
          <template v-if="catalogSummary.other">
            <template v-if="catalogSummary.building || catalogSummary.autoAccess">、</template>{{ catalogSummary.other }} 张暂未开放
          </template>
          ——
          <button type="button" class="inline-link" @click="openCatalogView">在全部目录中查看</button>
        </p>
      </section>

      <section v-if="pendingTasks.length" class="panel-block" aria-labelledby="pending-title">
        <div class="block-head">
          <h3 id="pending-title">最近上传 / 待处理</h3>
        </div>
        <div class="pending-list">
          <button
            v-for="task in pendingTasks"
            :key="task.id"
            type="button"
            class="pending-row"
            @click="focusPendingTask(task.id)"
          >
            <FileSpreadsheet :size="16" />
            <span class="pending-main">
              <strong>{{ task.title }}</strong>
              <small>{{ task.tableName }}</small>
            </span>
            <span class="pending-status" :class="task.tone">{{ task.status }}</span>
          </button>
        </div>
      </section>
    </template>

    <!-- 完整目录：二级视图 -->
    <section v-else class="panel-block" aria-labelledby="catalog-title">
      <div class="block-head">
        <h3 id="catalog-title">全部数据表目录</h3>
        <button type="button" class="view-switch-btn" @click="backToWorkbench">
          <LayoutGrid :size="15" />返回工作台
        </button>
      </div>
      <p class="block-lead">完整目录含建设中与自动接入登记项，供管理与扩展使用。</p>

      <div class="filter-bar">
        <label class="search-field">
          <Search :size="15" />
          <input v-model="searchKeyword" type="search" placeholder="搜索数据表名称…" />
        </label>
        <select v-model="filterDomain" class="filter-select">
          <option value="">全部数据域</option>
          <option v-for="d in ESG_DATA_DOMAINS" :key="d" :value="d">{{ d }}</option>
        </select>
        <select v-model="filterNature" class="filter-select">
          <option value="">全部数据性质</option>
          <option v-for="n in ESG_DATA_NATURES" :key="n" :value="n">{{ n }}</option>
        </select>
        <select v-model="filterAccess" class="filter-select">
          <option value="">全部接入方式</option>
          <option v-for="a in ESG_ACCESS_MODES" :key="a" :value="a">{{ a }}</option>
        </select>
        <select v-model="filterStatus" class="filter-select">
          <option value="">全部状态</option>
          <option v-for="s in ESG_DATA_STATUSES" :key="s" :value="s">{{ s }}</option>
        </select>
        <input
          v-model="filterAssociation"
          class="filter-input filter-advanced"
          type="text"
          placeholder="高级：首页/专题关联"
        />
      </div>

      <div class="catalog-table-wrap">
        <table class="catalog-table">
          <thead>
            <tr>
              <th>数据表</th>
              <th>数据域</th>
              <th>数据性质</th>
              <th>接入方式</th>
              <th>状态</th>
              <th class="col-advanced">关联展示</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="[domain, items] in catalogGroups" :key="domain">
              <tr class="group-row">
                <td colspan="7">{{ domain }}</td>
              </tr>
              <tr
                v-for="item in items"
                :key="item.id"
                :class="{ 'is-active': activeCatalogId === item.id, 'is-disabled': !isCatalogUploadable(item) }"
              >
                <td>
                  <button type="button" class="table-name-btn" @click="selectCatalog(item)">
                    <strong>{{ item.name }}</strong>
                    <small>{{ item.description }}</small>
                  </button>
                </td>
                <td>{{ item.domain }}</td>
                <td>{{ item.nature }}</td>
                <td>{{ item.accessMode }}</td>
                <td><span class="status-pill" :class="statusClass(item.status)">{{ item.status }}</span></td>
                <td class="col-advanced">
                  <span v-for="assoc in item.displayAssociations" :key="assoc" class="assoc-tag">{{ assoc }}</span>
                  <span v-if="!item.displayAssociations.length" class="muted">—</span>
                </td>
                <td class="action-cell">
                  <template v-if="isCatalogUploadable(item)">
                    <a
                      v-if="item.templateUrl"
                      class="link-btn"
                      :href="resolveTemplateDownloadUrl(item.templateUrl)"
                      download
                      @click.stop
                    >
                      <Download :size="14" />模板
                    </a>
                    <button type="button" class="primary-btn" @click="openUploadFor(item)">上传数据</button>
                  </template>
                  <span v-else-if="item.status === '建设中'" class="status-disabled-label">建设中 · 暂未开放</span>
                  <span v-else-if="item.status === '仅自动接入'" class="status-disabled-label">仅自动接入</span>
                  <span v-else class="status-disabled-label">暂未开放</span>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </section>

    <!-- 候选数据表选择 -->
    <div v-if="pendingCatalogPick.length" class="candidate-panel panel-block">
      <h3>请选择数据表归属</h3>
      <p>{{ pendingFile?.name }}</p>
      <div class="candidate-actions">
        <button
          v-for="id in pendingCatalogPick"
          :key="id"
          type="button"
          class="primary-btn"
          @click="resolvePendingPick(id)"
        >
          {{ getCatalogItem(id)?.name }}
        </button>
        <button type="button" class="text-btn" @click="cancelPendingPick">取消</button>
      </div>
    </div>

    <!-- 新建上传区 -->
    <section class="panel-block upload-workspace" aria-labelledby="upload-title">
      <div class="block-head">
        <h3 id="upload-title">新建上传区</h3>
        <button v-if="uploadSessions.length" type="button" class="text-btn" @click="clearWorkspace">清空</button>
      </div>

      <div v-if="activeCatalog" class="upload-context">
        <div><small>目标数据表</small><strong>{{ activeCatalog.name }}</strong></div>
        <div><small>模板版本</small><strong>{{ activeCatalog.templateVersion || '—' }}</strong></div>
        <div><small>依赖关系</small><strong>{{ dependencyNames(activeCatalog) }}</strong></div>
      </div>

      <div v-if="showE01DualOrder" class="e01-dual-hint">
        <strong>已识别：点位表 + 结果表</strong>
        <p>系统处理顺序：</p>
        <ol>
          <li>点位表</li>
          <li>结果表及点位引用关系</li>
        </ol>
      </div>

      <button
        type="button"
        class="drop-zone"
        :class="{ dragging: isDragging }"
        @click="openGenericUpload"
        @dragenter.prevent="isDragging = true"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop="handleDrop"
      >
        <UploadCloud :size="28" />
        <span>
          <strong>拖拽 Excel 到此处，或点击选择文件</strong>
          <small>将自动识别数据表；也可先从目录点击「上传数据」锁定目标表</small>
        </span>
      </button>

      <div v-if="uploadSessions.length" class="session-list">
        <article v-for="session in uploadSessions" :key="session.id" class="session-row">
          <FileSpreadsheet :size="18" />
          <div class="session-main">
            <strong>{{ session.file.name }}</strong>
            <small>
              <template v-if="session.recognizing">正在识别数据表…</template>
              <template v-else-if="session.recognize">{{ session.recognize.message }}</template>
              <template v-else>待处理</template>
              <template v-if="session.catalogId"> · {{ getCatalogItem(session.catalogId)?.name }}</template>
            </small>
          </div>
          <span
            class="session-status"
            :class="{
              ok: session.parsed?.ok,
              bad: session.parsed && !session.parsed.ok,
              wait: session.recognizing,
            }"
          >
            <LoaderCircle v-if="session.recognizing" :size="14" class="spin" />
            <CheckCircle2 v-else-if="session.confirmed" :size="14" />
            <AlertTriangle v-else-if="session.parsed && !session.parsed.ok" :size="14" />
            {{
              session.confirmed
                ? '已入库'
                : session.recognizing
                  ? '识别中'
                  : session.parsed?.ok
                    ? '校验通过'
                    : session.recognize?.unrecognized
                      ? '待识别'
                      : '校验失败'
            }}
          </span>
          <button type="button" class="icon-btn" aria-label="移除" @click="removeSession(session.id)">
            <X :size="15" />
          </button>
        </article>
      </div>
    </section>

    <!-- 校验结果 -->
    <section v-if="aggregateStats" class="panel-block" aria-labelledby="validation-title">
      <div class="block-head">
        <h3 id="validation-title">校验结果</h3>
      </div>
      <div class="stats-grid">
        <div class="stat-card"><small>读取记录数</small><b>{{ aggregateStats.readCount }}</b></div>
        <div class="stat-card"><small>空行数</small><b>{{ aggregateStats.emptyRowCount }}</b></div>
        <div class="stat-card"><small>校验通过数</small><b class="ok">{{ aggregateStats.passCount }}</b></div>
        <div class="stat-card"><small>警告数</small><b class="warn">{{ aggregateStats.warningCount }}</b></div>
        <div class="stat-card"><small>错误数</small><b class="bad">{{ aggregateStats.errorCount }}</b></div>
        <div class="stat-card"><small>阻断数</small><b class="bad">{{ aggregateStats.blockCount }}</b></div>
      </div>

      <div v-if="validationRows.length" class="detail-table-wrap">
        <table class="detail-table">
          <thead>
            <tr>
              <th>Excel行号</th>
              <th>数据表</th>
              <th>业务对象</th>
              <th>错误字段</th>
              <th>校验结果</th>
              <th>修改建议</th>
              <th>入库动作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in validationRows" :key="idx">
              <td>{{ row.excelRow }}</td>
              <td>{{ row.tableName }}</td>
              <td>{{ row.businessObject }}</td>
              <td>{{ row.errorField }}</td>
              <td :class="row.result === '错误' ? 'is-fail' : 'is-warn'">{{ row.result }}</td>
              <td>{{ row.suggestion }}</td>
              <td>{{ row.ingestAction }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <button type="button" class="text-btn disabled-hint" disabled title="后端错误明细下载接口待接入">
        下载错误明细（后续接入）
      </button>
    </section>

    <!-- 入库影响预览 -->
    <section v-if="aggregateStats" class="panel-block" aria-labelledby="impact-title">
      <div class="block-head">
        <h3 id="impact-title">入库影响预览</h3>
      </div>
      <div class="stats-grid impact-grid">
        <div class="stat-card"><small>预计新增数</small><b>{{ aggregateStats.expectedInsert ?? '确认后统计' }}</b></div>
        <div class="stat-card"><small>预计更新数</small><b>{{ aggregateStats.expectedUpdate ?? '确认后统计' }}</b></div>
        <div class="stat-card"><small>跳过数</small><b>{{ aggregateStats.skipCount }}</b></div>
      </div>
      <p v-if="activeCatalog?.displayAssociations.length" class="impact-hint">
        入库后将影响首页展示：{{ activeCatalog.displayAssociations.join('、') }}
      </p>
      <p v-if="confirmBlockedReason" class="block-hint-text">
        <AlertTriangle :size="14" /> {{ confirmBlockedReason }}
      </p>
      <button
        type="button"
        class="confirm-btn"
        :disabled="!canConfirm || confirming"
        @click="confirmIngestion"
      >
        <LoaderCircle v-if="confirming" :size="16" class="spin" />
        <CheckCircle2 v-else :size="16" />
        {{ latestSession?.confirmed ? '已确认入库' : '确认入库' }}
      </button>
    </section>

    <!-- 最近入库批次 -->
    <section class="panel-block" aria-labelledby="recent-title">
      <div class="block-head">
        <h3 id="recent-title">最近入库批次</h3>
      </div>
      <div v-if="recentBatches.length" class="detail-table-wrap">
        <table class="detail-table">
          <thead>
            <tr>
              <th>数据表</th>
              <th>来源</th>
              <th>模板版本</th>
              <th>上传时间</th>
              <th>读取</th>
              <th>成功</th>
              <th>错误</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="batch in recentBatches" :key="batch.id">
              <td>{{ batch.tableName }}</td>
              <td>{{ batch.source }}</td>
              <td>{{ batch.templateVersion }}</td>
              <td>{{ batch.uploadedAt }}</td>
              <td>{{ batch.readCount }}</td>
              <td>{{ batch.successCount }}</td>
              <td>{{ batch.errorCount }}</td>
              <td>{{ batch.status }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="empty-batch">
        <ChevronDown :size="20" />
        <span>暂无历史批次记录（当前会话上传后将显示于此；历史 API 待接入）</span>
      </div>
    </section>
  </section>
</template>

<style scoped>
.smart-entry-catalog {
  color: var(--ws-text-primary, #edf6ff);
  font-size: 14px;
  gap: 12px;
}

.visually-hidden {
  position: fixed;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.catalog-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid rgba(35, 169, 255, 0.22);
  border-left: 3px solid #23a9ff;
  border-radius: 6px;
  background: linear-gradient(100deg, rgba(7, 26, 42, 0.96), rgba(10, 34, 52, 0.78));
}

.catalog-title {
  margin: 0;
  font-size: 24px;
  line-height: 1.2;
}

.catalog-subtitle {
  margin: 6px 0 0;
  color: #87a4b9;
  font-size: 13px;
}

.active-table-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid rgba(35, 169, 255, 0.35);
  border-radius: 4px;
  background: rgba(35, 169, 255, 0.08);
  color: #8bd4ff;
  font-size: 13px;
}

.chip-close {
  display: grid;
  place-items: center;
  padding: 0;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.page-alert,
.page-success {
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 13px;
}

.page-alert {
  border: 1px solid rgba(244, 182, 74, 0.35);
  background: rgba(244, 182, 74, 0.08);
  color: #ffd68a;
}

.page-success {
  border: 1px solid rgba(55, 201, 133, 0.35);
  background: rgba(55, 201, 133, 0.08);
  color: #8fe0b6;
}

.panel-block {
  padding: 14px 16px;
  border: 1px solid rgba(24, 58, 82, 0.85);
  border-radius: 6px;
  background: linear-gradient(180deg, rgba(7, 26, 42, 0.98), rgba(5, 22, 36, 0.98));
}

.block-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.block-head h3 {
  margin: 0;
  font-size: 18px;
}

.block-hint {
  color: #6f8da2;
  font-size: 12px;
}

.block-lead {
  margin: -4px 0 12px;
  color: #6f8da2;
  font-size: 13px;
  line-height: 1.5;
}

.view-switch-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  padding: 0 12px;
  border: 1px solid rgba(35, 169, 255, 0.35);
  border-radius: 4px;
  background: rgba(35, 169, 255, 0.08);
  color: #8bd4ff;
  font-size: 13px;
  cursor: pointer;
}

.table-card-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.table-card {
  padding: 14px;
  border: 1px solid rgba(24, 58, 82, 0.78);
  border-radius: 6px;
  background: rgba(10, 34, 52, 0.55);
}

.table-card.is-active {
  border-color: rgba(35, 169, 255, 0.45);
  background: rgba(35, 169, 255, 0.06);
}

.table-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.table-card-head strong {
  font-size: 16px;
  color: #dcecf6;
}

.table-card-desc {
  margin: 0 0 8px;
  color: #9ab0bf;
  font-size: 13px;
  line-height: 1.5;
}

.table-card-dep {
  margin: 0 0 8px;
  color: #e6c57a;
  font-size: 12px;
}

.table-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
  color: #6f8da2;
  font-size: 12px;
}

.table-card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.catalog-summary-line {
  margin: 14px 0 0;
  color: #6f8da2;
  font-size: 13px;
  line-height: 1.5;
}

.inline-link {
  padding: 0;
  border: none;
  background: transparent;
  color: #8bd4ff;
  font-size: inherit;
  text-decoration: underline;
  cursor: pointer;
}

.pending-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pending-row {
  display: grid;
  grid-template-columns: 20px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  width: 100%;
  padding: 10px 12px;
  border: 1px solid rgba(24, 58, 82, 0.78);
  border-radius: 4px;
  background: rgba(10, 34, 52, 0.62);
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.pending-main {
  min-width: 0;
}

.pending-main strong {
  display: block;
  overflow: hidden;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pending-main small {
  color: #6f8da2;
  font-size: 11px;
}

.pending-status {
  font-size: 12px;
  font-weight: 600;
}

.pending-status.wait {
  color: #69c9ff;
}

.pending-status.bad {
  color: #f0a0a0;
}

.pending-status.ok {
  color: #78e0ad;
}

.pending-status.warn {
  color: #f2c66e;
}

.catalog-table tr.is-disabled td {
  opacity: 0.88;
}

.status-disabled-label {
  color: #6f8da2;
  font-size: 12px;
}

.col-advanced,
.filter-advanced {
  /* 高级信息：完整目录模式才突出 */
}

.filter-advanced::placeholder {
  color: #55778f;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.search-field {
  flex: 1 1 220px;
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 34px;
  padding: 0 10px;
  border: 1px solid rgba(24, 58, 82, 0.9);
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.25);
  color: #8fa9c8;
}

.search-field input,
.filter-select,
.filter-input {
  min-height: 32px;
  border: none;
  background: transparent;
  color: #e8f3ff;
  font-size: 13px;
  outline: none;
}

.search-field input {
  flex: 1;
}

.filter-select,
.filter-input {
  padding: 0 10px;
  border: 1px solid rgba(24, 58, 82, 0.9);
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.25);
}

.catalog-table-wrap,
.detail-table-wrap {
  overflow: auto;
  border: 1px solid rgba(24, 58, 82, 0.72);
  border-radius: 4px;
}

.catalog-table,
.detail-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 960px;
  font-size: 13px;
}

.catalog-table th,
.catalog-table td,
.detail-table th,
.detail-table td {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(24, 58, 82, 0.58);
  text-align: left;
  vertical-align: top;
}

.catalog-table th,
.detail-table th {
  color: #8fd7ff;
  background: rgba(9, 38, 58, 0.78);
  font-weight: 600;
}

.group-row td {
  color: #73cdff;
  font-size: 12px;
  font-weight: 600;
  background: rgba(35, 169, 255, 0.06);
}

.catalog-table tr.is-active td {
  background: rgba(35, 169, 255, 0.06);
}

.table-name-btn {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 0;
  border: none;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.table-name-btn strong {
  font-size: 14px;
  color: #dcecf6;
}

.table-name-btn small {
  color: #6f8da2;
  font-size: 12px;
  line-height: 1.4;
}

.status-pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 12px;
}

.status-ready {
  color: #78e0ad;
  background: rgba(55, 201, 133, 0.12);
}

.status-has-data {
  color: #8bd4ff;
  background: rgba(35, 169, 255, 0.12);
}

.status-building {
  color: #f2c66e;
  background: rgba(244, 182, 74, 0.12);
}

.status-auto {
  color: #b39cff;
  background: rgba(166, 108, 255, 0.12);
}

.status-muted {
  color: #8fa9c8;
  background: rgba(143, 169, 200, 0.1);
}

.assoc-tag {
  display: inline-block;
  margin: 0 4px 4px 0;
  padding: 2px 6px;
  border-radius: 3px;
  background: rgba(35, 169, 255, 0.1);
  color: #73ccff;
  font-size: 11px;
}

.action-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.link-btn,
.primary-btn,
.text-btn,
.template-btn,
.confirm-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  text-decoration: none;
}

.link-btn {
  border: 1px solid rgba(35, 169, 255, 0.35);
  background: rgba(35, 169, 255, 0.08);
  color: #8bd4ff;
}

.primary-btn {
  border: 1px solid rgba(35, 169, 255, 0.45);
  background: rgba(35, 169, 255, 0.14);
  color: #d8f0ff;
}

.text-btn {
  border: 1px solid rgba(24, 58, 82, 0.8);
  background: transparent;
  color: #8fa9c8;
}

.template-download-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed rgba(24, 58, 82, 0.72);
}

.template-btn {
  border: 1px solid rgba(55, 201, 133, 0.45);
  background: rgba(55, 201, 133, 0.1);
  color: #b8f0d2;
}

.template-meta,
.template-note,
.muted {
  color: #6f8da2;
  font-size: 12px;
}

.upload-context {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.upload-context small {
  display: block;
  margin-bottom: 4px;
  color: #6f8da2;
  font-size: 11px;
}

.upload-context strong {
  font-size: 15px;
  color: #dcecf6;
}

.e01-dual-hint {
  margin-bottom: 12px;
  padding: 10px 12px;
  border: 1px solid rgba(55, 201, 133, 0.3);
  border-radius: 4px;
  background: rgba(55, 201, 133, 0.06);
  color: #b7ebcf;
  font-size: 13px;
}

.e01-dual-hint ol {
  margin: 6px 0 0;
  padding-left: 20px;
}

.drop-zone {
  width: 100%;
  min-height: 88px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border: 1px dashed rgba(35, 169, 255, 0.46);
  border-radius: 5px;
  background: rgba(10, 34, 52, 0.52);
  color: #dcecf6;
  text-align: left;
  cursor: pointer;
}

.drop-zone.dragging {
  border-color: #23a9ff;
  background: rgba(10, 42, 67, 0.72);
}

.drop-zone strong {
  display: block;
  margin-bottom: 4px;
  font-size: 14px;
}

.drop-zone small {
  color: #87a4b9;
  font-size: 12px;
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.session-row {
  display: grid;
  grid-template-columns: 24px minmax(0, 1fr) auto 28px;
  gap: 10px;
  align-items: center;
  padding: 8px 10px;
  border: 1px solid rgba(24, 58, 82, 0.78);
  border-radius: 4px;
  background: rgba(10, 34, 52, 0.62);
}

.session-main {
  min-width: 0;
}

.session-main strong {
  display: block;
  overflow: hidden;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-main small {
  color: #6f8da2;
  font-size: 11px;
}

.session-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #8aa4b8;
}

.session-status.ok {
  color: #78e0ad;
}

.session-status.bad {
  color: #f0a0a0;
}

.session-status.wait {
  color: #69c9ff;
}

.icon-btn {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 3px;
  background: transparent;
  color: #6f8da2;
  cursor: pointer;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.impact-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.stat-card {
  padding: 12px;
  border: 1px solid rgba(24, 58, 82, 0.72);
  border-radius: 4px;
  background: rgba(6, 25, 40, 0.48);
}

.stat-card small {
  display: block;
  margin-bottom: 6px;
  color: #6f8da2;
  font-size: 12px;
}

.stat-card b {
  font-size: 22px;
  font-weight: 700;
  color: #e8f3ff;
}

.stat-card b.ok {
  color: #78e0ad;
}

.stat-card b.warn {
  color: #f2c66e;
}

.stat-card b.bad {
  color: #f0a0a0;
}

.is-fail {
  color: #f0a0a0;
}

.is-warn {
  color: #f2c66e;
}

.disabled-hint {
  opacity: 0.65;
  cursor: not-allowed;
}

.impact-hint,
.block-hint-text {
  margin: 0 0 12px;
  color: #9ab4c5;
  font-size: 13px;
  line-height: 1.5;
}

.block-hint-text {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #ffd68a;
}

.confirm-btn {
  min-height: 44px;
  border: 1px solid rgba(55, 201, 133, 0.45);
  background: linear-gradient(180deg, rgba(55, 201, 133, 0.22), rgba(55, 201, 133, 0.12));
  color: #b8f0d2;
  font-size: 15px;
  font-weight: 650;
}

.confirm-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.empty-batch {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px;
  color: #6f8da2;
  font-size: 13px;
}

.candidate-panel {
  border-color: rgba(244, 182, 74, 0.35);
}

.candidate-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.spin {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1450px) {
  .stats-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .upload-context {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1080px) {
  .catalog-header {
    flex-direction: column;
  }

  .table-card-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid,
  .impact-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
