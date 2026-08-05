<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { X } from 'lucide-vue-next'
import type { KpiDetailConfig } from '@/types/dashboard'
import type {
  MonthlyReportOverview,
  MonthlyTaskInstance,
  MonthlyPendingTask,
  MonthlyTaskStatus,
  MonthlyTaskTypeCode,
  MonthlyProcessStageStatus,
} from '@/types/monthly-report'
import { getMonthlyReportOverview } from '@/services/api'

const props = defineProps<{ detail: KpiDetailConfig }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const isAcceptanceMode = new URLSearchParams(window.location.search).get('acceptance') === '1'

type TabKey = 'overview' | 'tasks' | 'pending'
const tabs: { key: TabKey; label: string }[] = [
  { key: 'overview', label: '编制进度' },
  { key: 'tasks', label: '资料任务' },
  { key: 'pending', label: '待处理清单' },
]
const activeTab = ref<TabKey>('overview')

const modalRef = ref<HTMLDivElement | null>(null)
const overview = ref<MonthlyReportOverview | null>(null)
const loadError = ref<string | null>(null)

const REPORT_MONTH = '2026-07'

async function loadOverview() {
  const data = await getMonthlyReportOverview(REPORT_MONTH)
  if (data) {
    overview.value = data
    loadError.value = null
    return
  }
  loadError.value = '月报概览接口请求失败：' + REPORT_MONTH
}

onMounted(() => {
  void loadOverview()
  nextTick(() => modalRef.value?.focus())
})

const reportMonthLabel = computed(() => {
  const value = overview.value?.reportMonth || REPORT_MONTH
  const match = /^(\d{4})-(0[1-9]|1[0-2])$/.exec(value)
  return match ? `${match[1]}年${Number(match[2])}月` : value
})

const deadlineRangeText = computed(() => {
  const range = overview.value?.deadlineRange
  if (!range) return '—'
  return `${range.start}至${range.end}`
})

const summary = computed(() => overview.value?.summary)
const taskInstances = computed<MonthlyTaskInstance[]>(() => overview.value?.taskInstances || [])
const pendingTasks = computed<MonthlyPendingTask[]>(() => overview.value?.pendingTasks || [])
const processStages = computed(() => overview.value?.processStages || [])
const groupProgress = computed(() => overview.value?.groupProgress || [])
const statusCounts = computed(() => overview.value?.statusCounts || [])
const taskTypeCounts = computed(() => overview.value?.taskTypeCounts || [])
const outputStatus = computed(() => overview.value?.outputStatus)

// ===== 页签一：待处理任务摘要分页 =====
const overviewPendingPage = ref(1)
const overviewPendingPageSize = 4

const overviewPendingTotalPages = computed(() => Math.max(1, Math.ceil(sortedPendingTasks.value.length / overviewPendingPageSize)))
const pagedOverviewPending = computed(() => {
  const start = (overviewPendingPage.value - 1) * overviewPendingPageSize
  return sortedPendingTasks.value.slice(start, start + overviewPendingPageSize)
})
const overviewPendingPageNumbers = computed(() => {
  const pages = []
  for (let i = 1; i <= overviewPendingTotalPages.value; i++) {
    pages.push(i)
  }
  return pages
})

// ===== 页签二：资料任务筛选与分页 =====
type GroupFilter = 'all' | 'E' | 'S' | 'G'
type StatusFilter = 'all' | MonthlyTaskStatus
type TaskTypeFilter = 'all' | MonthlyTaskTypeCode

const groupFilter = ref<GroupFilter>('all')
const statusFilter = ref<StatusFilter>('all')
const taskTypeFilter = ref<TaskTypeFilter>('all')
const tasksCurrentPage = ref(1)
const tasksPageSize = 12
const selectedTaskId = ref<string | null>(null)

const filteredTasks = computed(() => {
  return taskInstances.value.filter((task) => {
    if (groupFilter.value !== 'all' && task.groupCode !== groupFilter.value) return false
    if (statusFilter.value !== 'all' && task.status !== statusFilter.value) return false
    if (taskTypeFilter.value !== 'all' && task.taskType !== taskTypeFilter.value) return false
    return true
  })
})

const tasksTotalPages = computed(() => Math.max(1, Math.ceil(filteredTasks.value.length / tasksPageSize)))
const pagedTasks = computed(() => {
  const start = (tasksCurrentPage.value - 1) * tasksPageSize
  return filteredTasks.value.slice(start, start + tasksPageSize)
})

const selectedTask = computed<MonthlyTaskInstance | null>(() => {
  if (!selectedTaskId.value) return null
  return taskInstances.value.find((t) => t.id === selectedTaskId.value) || null
})

function selectTask(id: string) {
  selectedTaskId.value = id
}

function resetTasksPage() {
  tasksCurrentPage.value = 1
}

watch([groupFilter, statusFilter, taskTypeFilter], () => resetTasksPage())

// ===== 页签三：待处理清单 =====
const selectedPendingId = ref<string | null>(null)
const pendingCurrentPage = ref(1)
const pendingPageSize = 8

const selectedPending = computed<MonthlyPendingTask | null>(() => {
  if (!selectedPendingId.value) return null
  return pendingTasks.value.find((t) => t.id === selectedPendingId.value) || null
})

function selectPending(id: string) {
  selectedPendingId.value = id
}

const pendingStatusOrder: Record<string, number> = { '待提交': 0, '待确认': 1, '待补正': 2 }
const sortedPendingTasks = computed(() => {
  return [...pendingTasks.value].sort((a, b) => {
    const d1 = a.deadline || ''
    const d2 = b.deadline || ''
    if (d1 !== d2) return d1.localeCompare(d2)
    return (pendingStatusOrder[a.status] ?? 9) - (pendingStatusOrder[b.status] ?? 9)
  })
})

const pendingTotalPages = computed(() => Math.max(1, Math.ceil(sortedPendingTasks.value.length / pendingPageSize)))
const pagedPendingTasks = computed(() => {
  const start = (pendingCurrentPage.value - 1) * pendingPageSize
  return sortedPendingTasks.value.slice(start, start + pendingPageSize)
})

const topPendingTasks = computed(() => sortedPendingTasks.value.slice(0, 5))

// ===== 页签切换联动 =====
watch(activeTab, (tab) => {
  if (tab === 'tasks' && !selectedTaskId.value && pagedTasks.value.length > 0) {
    selectedTaskId.value = pagedTasks.value[0].id
  }
  if (tab === 'pending' && !selectedPendingId.value && sortedPendingTasks.value.length > 0) {
    selectedPendingId.value = sortedPendingTasks.value[0].id
  }
})

// ===== 验收模式：默认选中第一条任务 =====
watch(
  () => overview.value,
  () => {
    if (isAcceptanceMode && overview.value) {
      if (pagedTasks.value.length > 0 && !selectedTaskId.value) {
        selectedTaskId.value = pagedTasks.value[0].id
      }
      if (sortedPendingTasks.value.length > 0 && !selectedPendingId.value) {
        selectedPendingId.value = sortedPendingTasks.value[0].id
      }
    }
  },
  { immediate: true }
)

// ===== 颜色与文案映射 =====
const STATUS_COLOR: Record<MonthlyTaskStatus, string> = {
  '校验通过': '#69e36f',
  '待提交': '#2f9cff',
  '待确认': '#ffb347',
  '待补正': '#ff4f5e',
  '不适用': '#8ba6c3',
}

const NEXT_ACTION_LABEL: Record<string, string> = {
  SUBMIT_MATERIAL: '提交资料',
  CONFIRM_RESPONSIBILITY: '查看确认',
  CORRECT_MATERIAL: '补正资料',
  VIEW_RESULT: '查看详情',
}

const STAGE_COLOR: Record<MonthlyProcessStageStatus, string> = {
  IN_PROGRESS: '#2f9cff',
  COMPLETED: '#69e36f',
  PENDING: '#ffb347',
  NOT_STARTED: '#6f8ba5',
}

const STAGE_LABEL: Record<MonthlyProcessStageStatus, string> = {
  IN_PROGRESS: '进行中',
  COMPLETED: '已完成',
  PENDING: '待完成',
  NOT_STARTED: '未开始',
}

const GROUP_LABEL: Record<string, string> = { E: 'E组', S: 'S组', G: 'G组' }

const GROUP_BAR_COLOR: Record<string, string> = {
  E: '#69e36f',
  S: '#2f9cff',
  G: '#a66cff',
}

function responsibleDisplay(task: { responsibleUserName: string | null; responsibleRole: string | null }) {
  return task.responsibleUserName || task.responsibleRole || '待配置'
}

function materialStatusLabel(task: { linkedMaterialCount: number; requiredMaterialCount: number }) {
  return `${task.linkedMaterialCount}/${task.requiredMaterialCount}`
}

function taskTypeLabel(task: { taskTypeLabel: string }) {
  return task.taskTypeLabel
}

function fmtDate(value: string | null) {
  if (!value) return '—'
  return value
}

function safeText(value: string | null | undefined, fallback = '暂无') {
  return value && value.trim() ? value : fallback
}

function goToPendingTab() {
  activeTab.value = 'pending'
}

function closeOnOverlay(event: MouseEvent) {
  if (event.target === event.currentTarget) emit('close')
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') emit('close')
}

const dataReady = computed(() => overview.value !== null)
</script>

<template>
  <div class="monthly-overlay" @click="closeOnOverlay">
    <div
      ref="modalRef"
      class="monthly-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="monthly-title"
      tabindex="-1"
      @keydown="onKeydown"
    >
      <!-- ===== 标题区 ===== -->
      <header class="monthly-header">
        <h2 id="monthly-title">
          <b>MONTHLY</b>
          <span>月报准备与输出</span>
        </h2>
        <div class="header-meta">
          <i />
          {{ reportMonthLabel }}
          <span>·</span>
          {{ overview?.updatedAt || detail.updateTime || '—' }}
        </div>
      </header>

      <!-- ===== 页签区 ===== -->
      <nav class="monthly-tabs" aria-label="月报专题页签">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          type="button"
          class="tab-btn"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </nav>

      <!-- ===== 内容区 ===== -->
      <main class="monthly-body">
        <!-- ============================== 页签一：编制进度 ============================== -->
        <section v-if="activeTab === 'overview'" class="page overview-page">
          <!-- 摘要卡 -->
          <div class="summary-grid">
            <article class="summary-card card-blue">
              <span class="card-label">资料归集率</span>
              <div class="card-value-row">
                <strong class="card-value">{{ overview?.readinessRate ?? '—' }}</strong>
                <em class="card-unit">%</em>
              </div>
            </article>
            <article class="summary-card card-green">
              <span class="card-label">已归集</span>
              <div class="card-value-row">
                <strong class="card-value">{{ summary?.collectedCount ?? '—' }}/{{ summary?.totalCount ?? '—' }}</strong>
                <em class="card-unit">项</em>
              </div>
            </article>
            <article class="summary-card card-blue">
              <span class="card-label">待提交</span>
              <div class="card-value-row">
                <strong class="card-value">{{ summary?.pendingSubmitCount ?? '—' }}</strong>
                <em class="card-unit">项</em>
              </div>
            </article>
            <article class="summary-card card-orange">
              <span class="card-label">待确认</span>
              <div class="card-value-row">
                <strong class="card-value">{{ summary?.pendingConfirmCount ?? '—' }}</strong>
                <em class="card-unit">项</em>
              </div>
            </article>
            <article class="summary-card card-red">
              <span class="card-label">待补正</span>
              <div class="card-value-row">
                <strong class="card-value">{{ summary?.pendingCorrectionCount ?? '—' }}</strong>
                <em class="card-unit">项</em>
              </div>
            </article>
          </div>

          <!-- 截止日期横幅 -->
          <div class="deadline-banner">
            <span class="dl-label">任务截止：</span>
            <strong class="dl-range">{{ deadlineRangeText }}</strong>
            <span class="dl-sep">·</span>
            <span class="dl-total">待处理合计 <b>{{ summary?.pendingTotal ?? '—' }}</b> 项</span>
          </div>

          <!-- 主体左右分栏 -->
          <div class="overview-grid">
            <div class="overview-left">
              <!-- E/S/G准备情况 -->
              <div class="panel esg-panel">
                <div class="panel-title">
                  <b>E/S/G 准备情况</b>
                </div>
                <div class="esg-list">
                  <div v-for="g in groupProgress" :key="g.groupCode" class="esg-item">
                    <div class="esg-head">
                      <span class="esg-name">{{ GROUP_LABEL[g.groupCode] || g.groupCode }}</span>
                      <span class="esg-count">{{ g.collectedCount }}/{{ g.totalCount }} · {{ g.progress }}%</span>
                    </div>
                    <div class="esg-bar">
                      <i
                        :style="{
                          width: `${g.progress}%`,
                          background: GROUP_BAR_COLOR[g.groupCode] || '#2f9cff',
                        }"
                      ></i>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 待处理任务摘要 -->
              <div class="panel pending-summary-panel">
                <div class="panel-title">
                  <b>待处理任务摘要</b>
                  <button type="button" class="view-all-btn" @click="goToPendingTab">
                    查看全部{{ summary?.pendingTotal ?? 0 }}项
                  </button>
                </div>
                <div class="table-wrap table-wrap--paged">
                  <table>
                    <thead>
                      <tr>
                        <th style="text-align: left">任务名称</th>
                        <th>所属分组</th>
                        <th>当前状态</th>
                        <th>截止日期</th>
                        <th>下一步</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="task in pagedOverviewPending" :key="task.id">
                        <td class="tal task-name-cell" :title="task.taskName">
                          <span class="task-name-text">{{ task.taskName }}</span>
                        </td>
                        <td>{{ GROUP_LABEL[task.groupCode] || task.groupCode }}</td>
                        <td>
                          <span
                            class="status-tag"
                            :style="{
                              color: STATUS_COLOR[task.status],
                              borderColor: STATUS_COLOR[task.status],
                            }"
                            >{{ task.status }}</span
                          >
                        </td>
                        <td>{{ fmtDate(task.deadline) }}</td>
                        <td>
                          <button type="button" class="action-btn">
                            {{ NEXT_ACTION_LABEL[task.nextActionType] || '—' }}
                          </button>
                        </td>
                      </tr>
                      <tr v-if="pagedOverviewPending.length === 0">
                        <td colspan="5" class="empty">本期无待处理任务</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div class="pagination">
                  <span class="page-info"
                    >第 {{ overviewPendingPage }}/{{ overviewPendingTotalPages }} 页 · 共 {{ sortedPendingTasks.length }} 项 · 每页 {{ overviewPendingPageSize }} 项</span
                  >
                  <div class="page-actions">
                    <button
                      type="button"
                      class="page-btn"
                      :disabled="overviewPendingPage === 1"
                      @click="overviewPendingPage--"
                    >
                      上一页
                    </button>
                    <template v-for="pg in overviewPendingPageNumbers" :key="pg">
                      <button
                        type="button"
                        class="page-btn"
                        :class="{ active: pg === overviewPendingPage }"
                        @click="overviewPendingPage = pg"
                      >
                        {{ pg }}
                      </button>
                    </template>
                    <button
                      type="button"
                      class="page-btn"
                      :disabled="overviewPendingPage === overviewPendingTotalPages"
                      @click="overviewPendingPage++"
                    >
                      下一页
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- 右侧 -->
            <aside class="overview-right">
              <div class="panel">
                <div class="panel-title">
                  <b>任务状态构成</b>
                </div>
                <div class="bar-list">
                  <div v-for="item in statusCounts" :key="item.status" class="bar-row">
                    <span class="bar-label">{{ item.status }}</span>
                    <div class="bar-track">
                      <i
                        :style="{
                          width: `${(item.count / (summary?.totalCount || 1)) * 100}%`,
                          background: STATUS_COLOR[item.status as MonthlyTaskStatus] || '#6f8ba5',
                        }"
                      ></i>
                    </div>
                    <span class="bar-value">{{ item.count }}</span>
                  </div>
                </div>
              </div>

              <div class="panel">
                <div class="panel-title">
                  <b>任务类型构成</b>
                </div>
                <div class="bar-list">
                  <div v-for="item in taskTypeCounts" :key="item.taskType" class="bar-row">
                    <span class="bar-label">{{ item.label }}</span>
                    <div class="bar-track">
                      <i
                        :style="{
                          width: `${(item.count / (summary?.totalCount || 1)) * 100}%`,
                          background: '#2f9cff',
                        }"
                      ></i>
                    </div>
                    <span class="bar-value">{{ item.count }}</span>
                  </div>
                </div>
              </div>

              <div class="panel reminder-panel">
                <div class="panel-title">
                  <b>截止日期与处理提醒</b>
                </div>
                <div class="reminder-body">
                  <p>
                    截止区间：<strong>{{ deadlineRangeText }}</strong>
                  </p>
                  <p>
                    待处理合计：<strong class="text-red">{{ summary?.pendingTotal ?? 0 }} 项</strong>
                  </p>
                  <p>
                    影响月报输出：
                    <strong class="text-orange">{{ pendingTasks.filter((t) => t.status !== '不适用').length }} 项</strong>
                  </p>
                  <p v-if="outputStatus && outputStatus.status === 'NOT_CREATED'" class="text-muted">
                    月报输出：待资料任务完成后生成
                  </p>
                </div>
              </div>
            </aside>
          </div>
        </section>

        <!-- ============================== 页签二：资料任务 ============================== -->
        <section v-else-if="activeTab === 'tasks'" class="page tasks-page">
          <div class="page-grid">
            <div class="panel tasks-table-panel">
              <div class="panel-title">
                <b>资料任务清单</b>
                <span>共 {{ taskInstances.length }} 项</span>
              </div>
              <div class="filter-bar">
                <div class="filter-group">
                  <span class="filter-label">分组</span>
                  <button
                    v-for="opt in [
                      { k: 'all', l: '全部' },
                      { k: 'E', l: 'E组' },
                      { k: 'S', l: 'S组' },
                      { k: 'G', l: 'G组' },
                    ]"
                    :key="opt.k"
                    type="button"
                    class="filter-btn"
                    :class="{ active: groupFilter === opt.k }"
                    @click="groupFilter = opt.k as GroupFilter"
                  >
                    {{ opt.l }}
                  </button>
                </div>
                <div class="filter-group">
                  <span class="filter-label">状态</span>
                  <button
                    v-for="opt in [
                      { k: 'all', l: '全部' },
                      { k: '校验通过', l: '校验通过' },
                      { k: '待提交', l: '待提交' },
                      { k: '待确认', l: '待确认' },
                      { k: '待补正', l: '待补正' },
                    ]"
                    :key="opt.k"
                    type="button"
                    class="filter-btn"
                    :class="{ active: statusFilter === opt.k }"
                    @click="statusFilter = opt.k as StatusFilter"
                  >
                    {{ opt.l }}
                  </button>
                </div>
                <div class="filter-group">
                  <span class="filter-label">类型</span>
                  <button
                    v-for="opt in [
                      { k: 'all', l: '全部' },
                      { k: 'MONTHLY_FIXED', l: '固定月度' },
                      { k: 'CONDITIONAL', l: '条件触发' },
                      { k: 'PERIODIC_REFERENCE', l: '周期引用' },
                    ]"
                    :key="opt.k"
                    type="button"
                    class="filter-btn"
                    :class="{ active: taskTypeFilter === opt.k }"
                    @click="taskTypeFilter = opt.k as TaskTypeFilter"
                  >
                    {{ opt.l }}
                  </button>
                </div>
              </div>
              <div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th style="text-align: left">任务名称</th>
                      <th>所属分组</th>
                      <th>任务类型</th>
                      <th style="text-align: left">责任单位</th>
                      <th style="text-align: left">责任角色</th>
                      <th>当前状态</th>
                      <th>截止日期</th>
                      <th>资料情况</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="task in pagedTasks"
                      :key="task.id"
                      :class="{ selected: selectedTaskId === task.id }"
                      @click="selectTask(task.id)"
                    >
                      <td class="tal task-name-cell" :title="task.taskName">
                        <span class="task-name-text">{{ task.taskName }}</span>
                      </td>
                      <td>{{ GROUP_LABEL[task.groupCode] || task.groupCode }}</td>
                      <td>{{ taskTypeLabel(task) }}</td>
                      <td class="tal" :title="task.responsibleDepartment || '—'">
                        <span class="ellipsis-text">{{ task.responsibleDepartment || '—' }}</span>
                      </td>
                      <td class="tal" :title="responsibleDisplay(task)">
                        <span class="ellipsis-text">{{ responsibleDisplay(task) }}</span>
                      </td>
                      <td>
                        <span
                          class="status-tag"
                          :style="{
                            color: STATUS_COLOR[task.status],
                            borderColor: STATUS_COLOR[task.status],
                          }"
                          >{{ task.status }}</span
                        >
                      </td>
                      <td>{{ fmtDate(task.deadline) }}</td>
                      <td>{{ materialStatusLabel(task) }}</td>
                      <td>
                        <button type="button" class="action-btn">
                          {{ NEXT_ACTION_LABEL[task.nextActionType] || '查看' }}
                        </button>
                      </td>
                    </tr>
                    <tr v-if="pagedTasks.length === 0">
                      <td colspan="9" class="empty">当前筛选条件下无匹配任务</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div class="pagination">
                <span class="page-info"
                  >第 {{ tasksCurrentPage }}/{{ tasksTotalPages }} 页 · 共 {{ filteredTasks.length }} 项 · 每页 {{ tasksPageSize }} 项</span
                >
                <div class="page-actions">
                  <button
                    type="button"
                    class="page-btn"
                    :disabled="tasksCurrentPage === 1"
                    @click="tasksCurrentPage--"
                  >
                    上一页
                  </button>
                  <button
                    type="button"
                    class="page-btn"
                    :disabled="tasksCurrentPage === tasksTotalPages"
                    @click="tasksCurrentPage++"
                  >
                    下一页
                  </button>
                </div>
              </div>
            </div>

            <aside class="side-detail">
              <div class="panel detail-panel">
                <div class="detail-scroll">
                  <div v-if="selectedTask" class="detail-content">
                    <!-- 基本信息 -->
                    <div class="detail-section">
                      <div class="detail-section-title">基本信息</div>
                      <div class="detail-row">
                        <span class="dl-key">任务编号</span>
                        <span class="dl-val">{{ selectedTask.taskCode }}</span>
                      </div>
                      <div class="detail-row">
                        <span class="dl-key">任务名称</span>
                        <span class="dl-val" :title="selectedTask.taskName">{{ selectedTask.taskName }}</span>
                      </div>
                      <div class="detail-row">
                        <span class="dl-key">所属分组</span>
                        <span class="dl-val">{{ GROUP_LABEL[selectedTask.groupCode] || selectedTask.groupCode }}</span>
                      </div>
                      <div class="detail-row">
                        <span class="dl-key">任务类型</span>
                        <span class="dl-val">{{ selectedTask.taskTypeLabel }}</span>
                      </div>
                      <div class="detail-row">
                        <span class="dl-key">责任单位</span>
                        <span class="dl-val">{{ selectedTask.responsibleDepartment || '暂无' }}</span>
                      </div>
                      <div class="detail-row">
                        <span class="dl-key">责任角色</span>
                        <span class="dl-val">{{ responsibleDisplay(selectedTask) }}</span>
                      </div>
                      <div class="detail-row">
                        <span class="dl-key">当前状态</span>
                        <span class="dl-val">
                          <span
                            class="status-tag"
                            :style="{
                              color: STATUS_COLOR[selectedTask.status],
                              borderColor: STATUS_COLOR[selectedTask.status],
                            }"
                            >{{ selectedTask.status }}</span
                          >
                        </span>
                      </div>
                      <div class="detail-row">
                        <span class="dl-key">截止日期</span>
                        <span class="dl-val">{{ fmtDate(selectedTask.deadline) }}</span>
                      </div>
                    </div>

                    <!-- 资料信息 -->
                    <div class="detail-section">
                      <div class="detail-section-title">资料信息</div>
                      <div v-if="selectedTask.issueDescription && selectedTask.issueDescription.trim()" class="detail-row">
                        <span class="dl-key">资料提交要求</span>
                        <span class="dl-val">{{ selectedTask.issueDescription }}</span>
                      </div>
                      <div class="detail-row">
                        <span class="dl-key">所需资料数量</span>
                        <span class="dl-val">{{ selectedTask.requiredMaterialCount }} 份</span>
                      </div>
                      <div class="detail-row">
                        <span class="dl-key">当前资料情况</span>
                        <span class="dl-val"
                          >{{ selectedTask.linkedMaterialCount }} / {{ selectedTask.requiredMaterialCount }}</span
                        >
                      </div>
                      <div v-if="selectedTask.linkedMaterialCount > 0" class="detail-row">
                        <span class="dl-key">已关联资料数量</span>
                        <span class="dl-val">{{ selectedTask.linkedMaterialCount }} 份</span>
                      </div>
                      <div v-if="selectedTask.linkedMaterialNames && selectedTask.linkedMaterialNames.length > 0" class="detail-row">
                        <span class="dl-key">已关联资料名称</span>
                        <span class="dl-val">{{ selectedTask.linkedMaterialNames.join('；') }}</span>
                      </div>
                      <div v-if="selectedTask.validationResult && selectedTask.validationResult.trim()" class="detail-row">
                        <span class="dl-key">最近一次校验结果</span>
                        <span class="dl-val">{{ selectedTask.validationResult }}</span>
                      </div>
                      <div v-if="selectedTask.lastValidationAt" class="detail-row">
                        <span class="dl-key">最近校验时间</span>
                        <span class="dl-val">{{ fmtDate(selectedTask.lastValidationAt) }}</span>
                      </div>
                    </div>
                  </div>
                  <div v-else class="empty-detail">请点击左侧任务查看详情</div>
                </div>
              </div>
            </aside>
          </div>
        </section>

        <!-- ============================== 页签三：待处理清单 ============================== -->
        <section v-else class="page pending-page">
          <div class="page-grid">
            <div class="panel pending-list-panel">
              <div class="panel-title">
                <b>待处理清单</b>
                <span
                  >{{ pendingTasks.length }} 项 · 待提交 {{ summary?.pendingSubmitCount ?? 0 }} · 待确认
                  {{ summary?.pendingConfirmCount ?? 0 }} · 待补正 {{ summary?.pendingCorrectionCount ?? 0 }}</span
                >
              </div>
              <div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th style="text-align: left">任务名称</th>
                      <th>所属分组</th>
                      <th>当前状态</th>
                      <th style="text-align: left">责任单位</th>
                      <th style="text-align: left">责任角色</th>
                      <th>截止日期</th>
                      <th style="text-align: left">问题摘要</th>
                      <th>下一步操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="task in pagedPendingTasks"
                      :key="task.id"
                      :class="{ selected: selectedPendingId === task.id }"
                      @click="selectPending(task.id)"
                    >
                      <td class="tal task-name-cell" :title="task.taskName">
                        <span class="task-name-text">{{ task.taskName }}</span>
                      </td>
                      <td>{{ GROUP_LABEL[task.groupCode] || task.groupCode }}</td>
                      <td>
                        <span
                          class="status-tag"
                          :style="{
                            color: STATUS_COLOR[task.status],
                            borderColor: STATUS_COLOR[task.status],
                          }"
                          >{{ task.status }}</span
                        >
                      </td>
                      <td class="tal">—</td>
                      <td class="tal">{{ task.responsibleRole || '待配置' }}</td>
                      <td>{{ fmtDate(task.deadline) }}</td>
                      <td class="tal issue-cell" :title="task.issueDescription || '—'">
                        <span class="ellipsis-text">{{ task.issueDescription || '—' }}</span>
                      </td>
                      <td>
                        <button type="button" class="action-btn">
                          {{ NEXT_ACTION_LABEL[task.nextActionType] || '—' }}
                        </button>
                      </td>
                    </tr>
                    <tr v-if="pagedPendingTasks.length === 0">
                      <td colspan="8" class="empty">本期无待处理任务</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div class="pagination">
                <span class="page-info"
                  >第 {{ pendingCurrentPage }}/{{ pendingTotalPages }} 页 · 共 {{ sortedPendingTasks.length }} 项 · 每页
                  {{ pendingPageSize }} 项</span
                >
                <div class="page-actions">
                  <button
                    type="button"
                    class="page-btn"
                    :disabled="pendingCurrentPage === 1"
                    @click="pendingCurrentPage--"
                  >
                    上一页
                  </button>
                  <button
                    type="button"
                    class="page-btn"
                    :disabled="pendingCurrentPage === pendingTotalPages"
                    @click="pendingCurrentPage++"
                  >
                    下一页
                  </button>
                </div>
              </div>
            </div>

            <aside class="pending-right">
              <div class="panel order-panel">
                <div class="panel-title">
                  <b>处理顺序</b>
                  <span class="panel-sub">优先处理前5项</span>
                </div>
                <div class="order-list">
                  <div
                    v-for="(task, idx) in topPendingTasks"
                    :key="task.id"
                    class="order-item"
                    :class="{ selected: selectedPendingId === task.id }"
                    @click="selectPending(task.id)"
                  >
                    <span class="order-no">{{ idx + 1 }}</span>
                    <div class="order-info">
                      <b class="order-name" :title="task.taskName">{{ task.taskName }}</b>
                      <small
                        >{{ GROUP_LABEL[task.groupCode] || task.groupCode }} · 截止
                        {{ fmtDate(task.deadline) }}</small
                      >
                    </div>
                    <span
                      class="status-tag status-tag-sm"
                      :style="{
                        color: STATUS_COLOR[task.status],
                        borderColor: STATUS_COLOR[task.status],
                      }"
                      >{{ task.status }}</span
                    >
                  </div>
                  <div v-if="topPendingTasks.length === 0" class="empty-order">暂无待处理任务</div>
                </div>
              </div>

              <div class="panel chain-panel">
                <div class="panel-title">
                  <b>选中任务资料链</b>
                </div>
                <div class="chain-scroll">
                  <div v-if="selectedPending" class="chain-list">
                    <div class="chain-item">
                      <div class="chain-head">
                        <span class="chain-dot chain-dot-blue"></span>
                        <span class="chain-label">任务要求</span>
                      </div>
                      <div class="chain-value" :title="safeText(selectedPending.requirement, '暂无')">
                        {{ safeText(selectedPending.requirement, '暂无') }}
                      </div>
                    </div>

                    <div class="chain-item">
                      <div class="chain-head">
                        <span class="chain-dot chain-dot-green"></span>
                        <span class="chain-label">已关联资料</span>
                      </div>
                      <div class="chain-value">
                        {{
                          selectedPending.materialChain.status === 'LINKED'
                            ? `已关联 ${selectedPending.materialChain.linkedDocumentIds.length} 份`
                            : '暂未关联资料'
                        }}
                      </div>
                    </div>

                    <div class="chain-item">
                      <div class="chain-head">
                        <span class="chain-dot chain-dot-orange"></span>
                        <span class="chain-label">校验结果</span>
                      </div>
                      <div class="chain-value" :title="safeText(selectedPending.issueDescription, '暂无')">
                        {{ safeText(selectedPending.issueDescription, '暂无') }}
                      </div>
                    </div>

                    <div class="chain-item">
                      <div class="chain-head">
                        <span class="chain-dot chain-dot-red"></span>
                        <span class="chain-label">补正或确认要求</span>
                      </div>
                      <div class="chain-value" :title="safeText(selectedPending.issueDescription, '暂无')">
                        {{ safeText(selectedPending.issueDescription, '暂无') }}
                      </div>
                    </div>

                    <div class="chain-item">
                      <div class="chain-head">
                        <span
                          class="chain-dot"
                          :class="
                            selectedPending.materialChain.status === 'LINKED'
                              ? 'chain-dot-green'
                              : 'chain-dot-gray'
                          "
                        ></span>
                        <span class="chain-label">月报引用状态</span>
                      </div>
                      <div
                        class="chain-value"
                        :style="{
                          color:
                            selectedPending.materialChain.status === 'LINKED' ? '#69e36f' : '#8ba6c3',
                        }"
                      >
                        {{ selectedPending.materialChain.status === 'LINKED' ? '已引用' : '未引用' }}
                      </div>
                    </div>
                  </div>
                  <div v-else class="empty-detail">请点击左侧任务查看资料链</div>
                </div>
              </div>
            </aside>
          </div>
        </section>
      </main>

      <!-- ===== 底部 ===== -->
      <footer class="monthly-footer">
        <span
          class="source-text"
          :title="detail.dataSource || 'monthly_report_cycle / monthly_report_task_instance / monthly_report_task_validation'"
        >
          数据来源：MySQL月报周期与任务实例
        </span>
        <span class="footer-notice">当前数据用于功能验证，不作为正式月报或财务确认依据</span>
        <button type="button" class="close-btn" aria-label="关闭" @click="emit('close')">
          <X :size="18" />
        </button>
      </footer>
    </div>
  </div>
</template>

<style scoped lang="scss">
.monthly-overlay {
  position: fixed;
  inset: 0;
  z-index: 10020;
  display: grid;
  place-items: center;
  background: rgba(2, 10, 22, 0.78);
  backdrop-filter: blur(4px);
  font-family: 'Microsoft YaHei', sans-serif;
  color: #e8f3ff;
}

.monthly-modal {
  width: 1436px;
  height: 880px;
  max-width: calc(100vw - 24px);
  max-height: calc(100vh - 24px);
  box-sizing: border-box;
  display: grid;
  grid-template-rows: 58px 48px 1fr 50px;
  overflow: hidden;
  border: 1px solid rgba(47, 156, 255, 0.32);
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(7, 25, 45, 0.99), rgba(3, 15, 30, 0.99));
  box-shadow: 0 20px 70px rgba(0, 0, 0, 0.45);
  outline: none;
}

/* ===== 标题区 ===== */
.monthly-header {
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-bottom: 1px solid rgba(47, 156, 255, 0.15);

  h2 {
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 0;
    font-size: 22px;
    font-weight: 600;

    b {
      color: #2f9cff;
      font-size: 26px;
      font-weight: 700;
      letter-spacing: 1.5px;
    }

    span {
      font-weight: 600;
    }
  }
}

.header-meta {
  margin-left: auto;
  color: #7892aa;
  font-size: 12px;

  i {
    display: inline-block;
    width: 8px;
    height: 8px;
    margin-right: 8px;
    border-radius: 50%;
    background: #2f9cff;
    box-shadow: 0 0 8px #2f9cff;
    vertical-align: middle;
  }

  span {
    margin: 0 8px;
  }
}

/* ===== 页签区 ===== */
.monthly-tabs {
  display: flex;
  padding: 0 20px;
  border-bottom: 1px solid rgba(47, 156, 255, 0.12);
  background: rgba(1, 12, 26, 0.42);

  .tab-btn {
    position: relative;
    min-width: 120px;
    height: 100%;
    border: 0;
    background: transparent;
    color: #8fa9c8;
    font-size: 15px;
    cursor: pointer;
    padding: 0 16px;

    &:focus {
      outline: none;
    }

    &:focus-visible {
      outline: 1px solid rgba(47, 156, 255, 0.6);
      outline-offset: -2px;
      border-radius: 2px;
    }

    &.active {
      color: #2f9cff;
      font-weight: 600;

      &:after {
        content: '';
        position: absolute;
        right: 20px;
        bottom: 0;
        left: 20px;
        height: 2px;
        background: #2f9cff;
        box-shadow: 0 0 8px rgba(47, 156, 255, 0.7);
      }
    }
  }
}

/* ===== 内容区 ===== */
.monthly-body {
  min-height: 0;
  padding: 16px;
  overflow: hidden;
}

.page {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

/* ===== 通用面板 ===== */
.panel {
  min-height: 0;
  box-sizing: border-box;
  border: 1px solid rgba(47, 156, 255, 0.12);
  background: rgba(7, 28, 49, 0.62);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.panel-title {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
  padding: 0 14px;
  border-bottom: 1px solid rgba(47, 156, 255, 0.1);
  flex-shrink: 0;

  b {
    font-size: 15px;
    font-weight: 600;
  }

  span {
    color: #6f8ba5;
    font-size: 13px;
  }

  .panel-sub {
    font-size: 12px;
  }
}

/* ===== 页签一：编制进度 ===== */
.overview-page {
  .summary-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    flex-shrink: 0;
  }
}

.summary-card {
  padding: 12px 16px;
  box-sizing: border-box;
  border: 1px solid rgba(47, 156, 255, 0.18);
  background: linear-gradient(135deg, rgba(47, 156, 255, 0.07), rgba(47, 156, 255, 0.025));

  .card-label {
    color: #8fa9c8;
    font-size: 14px;
    line-height: 1;
    display: block;
  }

  .card-value-row {
    margin-top: 8px;
    display: flex;
    align-items: baseline;
    gap: 6px;
  }

  .card-value {
    font-size: 28px;
    line-height: 1.1;
    font-weight: 700;
  }

  .card-unit {
    color: #8fa9c8;
    font-size: 13px;
    font-style: normal;
  }
}

.card-blue .card-value {
  color: #2f9cff;
}
.card-green .card-value {
  color: #69e36f;
}
.card-orange .card-value {
  color: #ffb347;
}
.card-red .card-value {
  color: #ff4f5e;
}

.deadline-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 36px;
  padding: 0 16px;
  border: 1px solid rgba(47, 156, 255, 0.18);
  background: rgba(47, 156, 255, 0.06);
  color: #c8d8e7;
  font-size: 13px;
  flex-shrink: 0;

  .dl-label {
    color: #8fa9c8;
  }
  .dl-range {
    color: #2f9cff;
    font-weight: 600;
  }
  .dl-sep {
    color: #6f8ba5;
  }
  .dl-total {
    color: #a9bbcc;
  }
  .dl-total b {
    color: #ff4f5e;
    font-weight: 600;
  }
}

.overview-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 12px;
  min-height: 0;
  flex: 1;
}

.overview-left {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

.overview-right {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

/* ===== 流程面板 ===== */
.process-panel {
  flex-shrink: 0;
  .process-flow {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 20px 8px;
    gap: 4px;
    min-height: 0;
  }
}

.process-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  min-width: 80px;
  text-align: center;

  .node-circle {
    width: 26px;
    height: 26px;
    border: 2px solid #6f8ba5;
    border-radius: 50%;
    background: rgba(7, 28, 49, 0.8);
    display: grid;
    place-items: center;
    position: relative;

    .check-icon {
      display: block;
      width: 10px;
      height: 6px;
      border-left: 2px solid currentColor;
      border-bottom: 2px solid currentColor;
      transform: rotate(-45deg);
      margin-top: -2px;
    }

    .pulse-icon {
      display: block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: currentColor;
    }
  }

  .node-label {
    color: #e8f3ff;
    font-size: 13px;
    font-weight: 600;
    margin-top: 2px;
  }

  .node-detail {
    color: #8fa9c8;
    font-size: 12px;
    line-height: 1.3;
    max-width: 100px;
  }

  &.is-not-started {
    .node-label,
    .node-detail {
      color: #6f8ba5;
    }
  }
}

.process-connector {
  flex: 1;
  height: 2px;
  background: rgba(47, 156, 255, 0.2);
  margin-bottom: 18px;
  align-self: center;
  min-width: 16px;

  &.is-done {
    background: #69e36f;
  }
}

/* ===== ESG 准备情况 ===== */
.esg-panel {
  flex-shrink: 0;

  .esg-list {
    padding: 10px 14px 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
}

.esg-item {
  .esg-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 4px;
  }

  .esg-name {
    color: #e8f3ff;
    font-size: 14px;
    font-weight: 600;
  }

  .esg-count {
    color: #8fa9c8;
    font-size: 12px;
  }

  .esg-bar {
    height: 8px;
    background: rgba(143, 169, 200, 0.1);
    border-radius: 4px;
    overflow: hidden;

    i {
      display: block;
      height: 100%;
      border-radius: 4px;
    }
  }
}

/* ===== 待处理任务摘要 ===== */
.pending-summary-panel {
  flex: 1;
  min-height: 0;

  .view-all-btn {
    border: 0;
    background: transparent;
    color: #2f9cff;
    font-size: 13px;
    cursor: pointer;
    padding: 0;

    &:hover {
      text-decoration: underline;
    }

    &:focus {
      outline: none;
    }

    &:focus-visible {
      outline: 1px solid rgba(47, 156, 255, 0.6);
      outline-offset: 2px;
      border-radius: 2px;
    }
  }
}

/* ===== 通用表格 ===== */
.table-wrap {
  flex: 1;
  min-height: 0;
  overflow: auto;

  &::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: rgba(47, 156, 255, 0.22);
    border-radius: 3px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }

  th {
    position: sticky;
    top: 0;
    z-index: 1;
    height: 36px;
    padding: 0 10px;
    background: #0c2943;
    color: #90a9c0;
    font-weight: 500;
    font-size: 14px;
    white-space: nowrap;
    text-align: center;
  }

  td {
    height: 38px;
    padding: 0 10px;
    border-bottom: 1px solid rgba(143, 169, 200, 0.07);
    color: #c8d8e7;
    text-align: center;
    vertical-align: middle;
    white-space: nowrap;
  }

  td.tal {
    text-align: left;
  }

  tbody tr {
    cursor: pointer;
    transition: background 0.15s;

    &:hover td {
      background: rgba(47, 156, 255, 0.04);
    }

    &.selected td {
      background: rgba(47, 156, 255, 0.1);
      box-shadow: inset 2px 0 0 #2f9cff;
    }
  }
}

.task-name-cell {
  max-width: 200px;

  .task-name-text {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #e8f3ff;
    font-weight: 500;
  }
}

.ellipsis-text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.issue-cell {
  max-width: 180px;
}

.status-tag {
  display: inline-block;
  padding: 3px 10px;
  border: 1px solid currentColor;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(7, 28, 49, 0.4);
  white-space: nowrap;
}

.status-tag-sm {
  padding: 2px 8px;
  font-size: 11px;
}

.action-btn {
  height: 26px;
  padding: 0 12px;
  border: 1px solid rgba(47, 156, 255, 0.3);
  background: rgba(47, 156, 255, 0.08);
  color: #2f9cff;
  font-size: 13px;
  border-radius: 3px;
  cursor: pointer;
  white-space: nowrap;

  &:hover {
    background: rgba(47, 156, 255, 0.16);
  }

  &:focus {
    outline: none;
  }

  &:focus-visible {
    outline: 1px solid rgba(47, 156, 255, 0.6);
    outline-offset: -1px;
  }
}

.empty,
.empty-detail {
  text-align: center;
  color: #6f8ba5;
  font-size: 13px;
  padding: 24px 12px;
}

/* ===== 右侧条形图 ===== */
.bar-list {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
}

.bar-row {
  display: grid;
  grid-template-columns: 72px 1fr 36px;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  width: 100%;
  box-sizing: border-box;
  overflow: hidden;

  .bar-label {
    color: #9fb4c8;
    font-size: 12px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    min-width: 0;
  }

  .bar-track {
    height: 8px;
    background: rgba(143, 169, 200, 0.1);
    border-radius: 4px;
    overflow: hidden;
    min-width: 0;

    i {
      display: block;
      height: 100%;
      border-radius: 4px;
    }
  }

  .bar-value {
    color: #dce8f5;
    font-weight: 600;
    text-align: right;
    font-size: 12px;
    white-space: nowrap;
    min-width: 0;
  }
}

.reminder-panel {
  .reminder-body {
    padding: 12px 14px;

    p {
      margin: 0 0 8px;
      color: #a9bbcc;
      font-size: 13px;
      line-height: 1.6;

      &:last-child {
        margin-bottom: 0;
      }

      strong {
        color: #dce8f5;
        font-weight: 600;
      }
    }

    .text-red {
      color: #ff4f5e !important;
    }
    .text-orange {
      color: #ffb347 !important;
    }
    .text-muted {
      color: #6f8ba5 !important;
    }
  }
}

/* ===== 页签二：资料任务 ===== */
.tasks-page .page-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 12px;
  min-height: 0;
  flex: 1;
}

.tasks-table-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(47, 156, 255, 0.08);
  flex-wrap: wrap;
  flex-shrink: 0;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;

  .filter-label {
    color: #6f8ba5;
    font-size: 13px;
    margin-right: 4px;
  }
}

.filter-btn {
  height: 24px;
  padding: 0 10px;
  border: 1px solid rgba(47, 156, 255, 0.18);
  background: transparent;
  color: #8fa9c8;
  font-size: 12px;
  border-radius: 2px;
  cursor: pointer;

  &:hover {
    border-color: rgba(47, 156, 255, 0.4);
    color: #c8d8e7;
  }

  &.active {
    border-color: #2f9cff;
    background: rgba(47, 156, 255, 0.12);
    color: #2f9cff;
  }

  &:focus {
    outline: none;
  }

  &:focus-visible {
    outline: 1px solid rgba(47, 156, 255, 0.6);
    outline-offset: -1px;
  }
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  border-top: 1px solid rgba(47, 156, 255, 0.08);
  font-size: 12px;
  flex-shrink: 0;

  .page-info {
    color: #8fa9c8;
  }
  .page-actions {
    display: flex;
    gap: 6px;
  }
}

.page-btn {
  height: 26px;
  padding: 0 12px;
  border: 1px solid rgba(47, 156, 255, 0.2);
  background: transparent;
  color: #c8d8e7;
  font-size: 12px;
  border-radius: 2px;
  cursor: pointer;

  &:hover:not(:disabled) {
    border-color: #2f9cff;
    color: #2f9cff;
  }

  &:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  &:focus {
    outline: none;
  }

  &:focus-visible {
    outline: 1px solid rgba(47, 156, 255, 0.6);
    outline-offset: -1px;
  }
}

/* ===== 右侧详情 ===== */
.side-detail {
  min-height: 0;
}

.detail-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.detail-scroll {
  flex: 1;
  overflow: auto;
  min-height: 0;

  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: rgba(47, 156, 255, 0.22);
    border-radius: 3px;
  }
}

.detail-content {
  padding: 4px 0;
}

.detail-section {
  padding: 12px 14px;
  border-bottom: 1px solid rgba(47, 156, 255, 0.08);

  &:last-child {
    border-bottom: 0;
  }
}

.detail-section-title {
  color: #2f9cff;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(47, 156, 255, 0.12);
}

.detail-row {
  display: grid;
  grid-template-columns: 88px 1fr;
  gap: 8px;
  padding: 5px 0;
  font-size: 13px;

  .dl-key {
    color: #8fa9c8;
  }
  .dl-val {
    color: #dce8f5;
    word-break: break-word;
    line-height: 1.5;
  }
}

/* ===== 页签三：待处理清单 ===== */
.pending-page .page-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 12px;
  min-height: 0;
  flex: 1;
}

.pending-list-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.pending-right {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

.order-panel {
  flex-shrink: 0;
  .order-list {
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .empty-order {
    text-align: center;
    color: #6f8ba5;
    font-size: 13px;
    padding: 16px 12px;
  }
}

.order-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border: 1px solid rgba(143, 169, 200, 0.08);
  background: rgba(7, 28, 49, 0.5);
  cursor: pointer;
  border-radius: 3px;

  &:hover {
    border-color: rgba(47, 156, 255, 0.3);
  }

  &.selected {
    border-color: #2f9cff;
    background: rgba(47, 156, 255, 0.08);
  }

  .order-no {
    flex-shrink: 0;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: rgba(47, 156, 255, 0.18);
    color: #2f9cff;
    font-size: 12px;
    font-weight: 600;
    display: grid;
    place-items: center;
  }

  .order-info {
    flex: 1;
    min-width: 0;

    .order-name {
      display: block;
      color: #e8f3ff;
      font-size: 13px;
      font-weight: 600;
      line-height: 1.3;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    small {
      display: block;
      margin-top: 2px;
      color: #8fa9c8;
      font-size: 11px;
    }
  }
}

/* ===== 资料链 ===== */
.chain-panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.chain-scroll {
  flex: 1;
  overflow: auto;
  min-height: 0;

  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: rgba(47, 156, 255, 0.22);
    border-radius: 3px;
  }
}

.chain-list {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chain-item {
  padding: 10px 12px;
  border-left: 2px solid #2f9cff;
  background: rgba(47, 156, 255, 0.04);

  .chain-head {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 6px;
  }

  .chain-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .chain-dot-blue {
    background: #2f9cff;
  }
  .chain-dot-green {
    background: #69e36f;
  }
  .chain-dot-orange {
    background: #ffb347;
  }
  .chain-dot-red {
    background: #ff4f5e;
  }
  .chain-dot-gray {
    background: #8ba6c3;
  }

  .chain-label {
    color: #8fa9c8;
    font-size: 12px;
    font-weight: 500;
  }

  .chain-value {
    color: #dce8f5;
    font-size: 13px;
    line-height: 1.5;
    word-break: break-word;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
}

/* ===== 底部 ===== */
.monthly-footer {
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-top: 1px solid rgba(47, 156, 255, 0.12);
  color: #6f879d;
  font-size: 12px;
  gap: 16px;

  .source-text {
    overflow: hidden;
    text-overflow: ellipsis;
    cursor: help;
    flex-shrink: 0;
    white-space: nowrap;
  }

  .footer-notice {
    flex: 1;
    text-align: center;
    color: #ffb347;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .close-btn {
    display: grid;
    place-items: center;
    width: 28px;
    height: 28px;
    border: 0;
    background: transparent;
    color: #9fb4ca;
    cursor: pointer;
    flex-shrink: 0;
    border-radius: 3px;

    &:hover {
      background: rgba(47, 156, 255, 0.1);
      color: #e8f3ff;
    }

    &:focus {
      outline: none;
    }

    &:focus-visible {
      outline: 1px solid rgba(47, 156, 255, 0.6);
      outline-offset: -1px;
    }
  }
}
</style>
