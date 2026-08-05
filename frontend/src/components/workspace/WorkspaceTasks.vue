<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Search, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { allUploadTasks, taskStatusCards as mockTaskStatusCards } from '@/data/workspace.mock'
import { getWorkspaceSummary, getWorkspaceTasks } from '@/services/api'
import type { UploadTask, StatusCard } from '@/types/workspace'
import { onWorkspaceRefresh } from '@/utils/workspaceRefresh'

const props = defineProps<{
  initialStatus?: string
}>()

const emit = defineEmits<{
  (e: 'openTask', taskId: string): void
}>()

const searchKeyword = ref('')
const selectedStatus = ref('当前待办')
const selectedIds = ref<string[]>(['t1', 't6'])
const taskList = ref<UploadTask[]>([...allUploadTasks])
const statusCards = ref<StatusCard[]>([...mockTaskStatusCards])

const hasSearch = ref(false)
const searchResultHint = ref('')

const filterModule = ref('')
const filterCycle = ref('')
const filterCycleType = ref('')
const filterDeadlineStart = ref('')
const filterDeadlineEnd = ref('')
const filterAssignee = ref('')

let stopWorkspaceRefresh: (() => void) | null = null

onMounted(() => {
  if (props.initialStatus) {
    selectedStatus.value = props.initialStatus
  }
  loadData()
  stopWorkspaceRefresh = onWorkspaceRefresh(payload => {
    if (!payload.scopes.some(scope => ['summary', 'tasks'].includes(scope))) return
    if (hasSearch.value) {
      handleAiSearch()
    } else {
      loadData()
    }
  })
})

onUnmounted(() => {
  stopWorkspaceRefresh?.()
})

async function loadData() {
  await loadDataWithParams({})
}

async function loadDataWithParams(params: {
  module?: string
  status?: string
  keyword?: string
  cycle?: string
  cycleType?: string
  deadlineStart?: string
  deadlineEnd?: string
  assignee?: string
}) {
  const [summaryRes, tasksRes] = await Promise.all([
    getWorkspaceSummary(),
    getWorkspaceTasks(params),
  ])
  
  if (summaryRes) {
    statusCards.value = [
      { label: '当前待办', value: summaryRes.currentTodo, unit: '项', color: '#8fa9c8' },
      { label: '待上传', value: summaryRes.pendingUpload, unit: '项', color: '#2f9cff' },
      { label: '待补正', value: summaryRes.pendingCorrection, unit: '项', color: '#ffb347' },
      { label: '待提交', value: summaryRes.pendingSubmit, unit: '项', color: '#a66cff' },
      { label: '审核中', value: summaryRes.underReview, unit: '项', color: '#a66cff' },
      { label: '已完成', value: summaryRes.completed, unit: '项', color: '#69e36f' },
    ]
  }
  
  if (tasksRes && tasksRes.items && tasksRes.items.length > 0) {
    taskList.value = tasksRes.items.map(item => ({
      ...item,
      daysOverdue: undefined,
      priorityCode: item.priorityCode || 'NORMAL',
    })) as UploadTask[]
  } else {
    taskList.value = [...allUploadTasks]
  }
}

const filteredTasks = computed(() => {
  if (!hasSearch.value) {
    if (selectedStatus.value === '当前待办') {
      return taskList.value.filter(t => ['待上传', '待补正', '待提交', '审核中', '审核退回'].includes(t.status))
    }
    return taskList.value.filter(t => t.status === selectedStatus.value)
  }
  
  const query = searchKeyword.value.toLowerCase()
  let results = taskList.value
  
  if (query.includes('逾期') || query.includes('过期')) {
    results = results.filter(t => t.daysOverdue)
  } else if (query.includes('待上传') || query.includes('需要上传')) {
    results = results.filter(t => t.status === '待上传')
  } else if (query.includes('退回') || query.includes('审核退回')) {
    results = results.filter(t => t.status === '审核退回')
  } else if (query.includes('补正') || query.includes('重新提交')) {
    results = results.filter(t => t.status === '待补正')
  } else if (query.includes('待提交')) {
    results = results.filter(t => t.status === '待提交')
  } else if (query.includes('审核中')) {
    results = results.filter(t => t.status === '审核中')
  } else if (query.includes('已完成')) {
    results = results.filter(t => t.status === '已完成')
  }
  
  if (query.includes('e组') || query.includes('环境')) {
    results = results.filter(t => t.module === 'E')
  } else if (query.includes('s组') || query.includes('社会')) {
    results = results.filter(t => t.module === 'S')
  } else if (query.includes('g组') || query.includes('治理')) {
    results = results.filter(t => t.module === 'G')
  }
  
  if (query.includes('本月') || query.includes('7月')) {
    results = results.filter(t => t.cycle.includes('2026-07') || t.cycle.includes('2026-Q3'))
  } else if (query.includes('本周')) {
    results = results.filter(t => {
      const deadline = new Date(t.deadline)
      const now = new Date()
      const diffDays = Math.ceil((deadline.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
      return diffDays >= 0 && diffDays <= 7
    })
  }
  
  if (!query.match(/(逾期|上传|退回|补正|待提交|审核中|已完成|e组|s组|g组|本月|本周|7月)/)) {
    results = taskList.value.filter(t => 
      t.name.toLowerCase().includes(query) || 
      t.moduleName.toLowerCase().includes(query)
    )
  }
  
  return results
})

const selectedCount = computed(() => selectedIds.value.length)

const currentPage = ref(1)
const pageSize = 10

const totalPages = computed(() => Math.max(1, Math.ceil(filteredTasks.value.length / pageSize)))

const paginatedTasks = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredTasks.value.slice(start, start + pageSize)
})

watch(filteredTasks, () => {
  currentPage.value = 1
})

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

function getPageNumbers() {
  const pages: number[] = []
  const maxPages = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxPages / 2))
  let end = Math.min(totalPages.value, start + maxPages - 1)
  if (end - start + 1 < maxPages) {
    start = Math.max(1, end - maxPages + 1)
  }
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
}

const canBatchSubmit = computed(() => {
  return selectedIds.value.length > 0 && selectedIds.value.every(id => {
    const task = taskList.value.find(t => t.id === id)
    return task?.progressCurrent === task?.progressTotal
  })
})

const batchSubmitDisabledReason = computed(() => {
  if (selectedIds.value.length === 0) return '请先选择任务'
  const incomplete = selectedIds.value.filter(id => {
    const task = taskList.value.find(t => t.id === id)
    return task?.progressCurrent !== task?.progressTotal
  })
  if (incomplete.length > 0) return `所选任务存在资料缺失或格式异常，暂不可提交（${incomplete.length} 项未满足）`
  return ''
})

function handleStatusCardClick(status: string) {
  selectedStatus.value = status
  hasSearch.value = false
  searchKeyword.value = ''
}

function toggleSelect(taskId: string) {
  const index = selectedIds.value.indexOf(taskId)
  if (index > -1) {
    selectedIds.value.splice(index, 1)
  } else {
    selectedIds.value.push(taskId)
  }
}

function toggleSelectAll() {
  if (selectedIds.value.length === filteredTasks.value.length) {
    selectedIds.value = []
  } else {
    selectedIds.value = filteredTasks.value.map(t => t.id)
  }
}

function handleAiSearch() {
  hasSearch.value = true
  searchResultHint.value = ''

  const params: {
    module?: string
    status?: string
    keyword?: string
    cycle?: string
    cycleType?: string
    deadlineStart?: string
    deadlineEnd?: string
    assignee?: string
  } = {}

  if (filterModule.value) params.module = filterModule.value
  if (filterCycle.value) params.cycle = filterCycle.value
  if (filterCycleType.value) params.cycleType = filterCycleType.value
  if (filterDeadlineStart.value) params.deadlineStart = filterDeadlineStart.value
  if (filterDeadlineEnd.value) params.deadlineEnd = filterDeadlineEnd.value
  if (filterAssignee.value) params.assignee = filterAssignee.value

  if (searchKeyword.value.trim()) {
    params.keyword = searchKeyword.value.trim()
  }

  if (selectedStatus.value !== '当前待办') {
    params.status = selectedStatus.value
  }

  loadDataWithParams(params)
}

function handleClearSearch() {
  hasSearch.value = false
  searchKeyword.value = ''
  searchResultHint.value = ''
  selectedStatus.value = '当前待办'
  filterModule.value = ''
  filterCycle.value = ''
  filterCycleType.value = ''
  filterDeadlineStart.value = ''
  filterDeadlineEnd.value = ''
  filterAssignee.value = ''
  loadData()
}

function handleBatchLink() {
  hasSearch.value = true
  searchResultHint.value = `已选择 ${selectedCount.value} 项任务。批量关联资料为原型预留功能，暂未接入批量办理流程。`
}

function handleBatchSubmit() {
  if (!canBatchSubmit.value) {
    hasSearch.value = true
    searchResultHint.value = batchSubmitDisabledReason.value
    return
  }
  hasSearch.value = true
  searchResultHint.value = `已选择 ${selectedCount.value} 项任务。批量提交为原型预留功能，暂未接入批量审核流程。`
}

function getModuleColor(module: string) {
  switch (module) {
    case 'E': return '#69e36f'
    case 'S': return '#2f9cff'
    case 'G': return '#a66cff'
    default: return '#8fa9c8'
  }
}

function getStatusColor(status: string) {
  switch (status) {
    case '待上传': return '#2f9cff'
    case '待补正': return '#ffb347'
    case '待提交': return '#a66cff'
    case '审核中': return '#a66cff'
    case '审核退回': return '#ff4f5e'
    case '已完成': return '#69e36f'
    default: return '#8fa9c8'
  }
}

function isSelected(taskId: string) {
  return selectedIds.value.includes(taskId)
}
</script>

<template>
  <div class="workspace-tasks ws-page">
    <div class="ws-status-cards cols-6">
      <div
        v-for="card in statusCards"
        :key="card.label"
        class="ws-status-card"
        :class="{ active: selectedStatus === card.label }"
        :style="{ '--accent-color': card.color }"
        @click="handleStatusCardClick(card.label)"
      >
        <div class="ws-card-label">{{ card.label }}</div>
        <div class="ws-card-value-row">
          <span class="ws-card-value">{{ card.value }}</span>
          <span class="ws-card-unit">{{ card.unit }}</span>
        </div>
      </div>
    </div>

    <div class="ws-filter-bar">
      <div class="ws-filter-row filter-search-row">
        <span class="ws-filter-title">任务检索</span>
        <div class="ws-search-box search-main">
          <Search :size="16" />
          <input
            v-model="searchKeyword"
            type="text"
            placeholder="询问待办任务、缺失资料、截止时间或任务状态"
            @keyup.enter="handleAiSearch"
          />
          <button class="ws-btn ws-btn-primary ws-btn-sm" @click="handleAiSearch">搜索</button>
        </div>
        <button v-if="hasSearch" class="ws-btn ws-btn-danger ws-btn-sm" @click="handleClearSearch">清除搜索</button>
      </div>
      <div class="ws-filter-row">
        <select v-model="filterModule" class="ws-select" @change="handleAiSearch">
          <option value="">全部模块</option>
          <option value="E">E-环境环保</option>
          <option value="S">S-社会责任</option>
          <option value="G">G-公司治理</option>
        </select>
        <input v-model="filterCycle" type="text" class="ws-input" placeholder="资料周期" @keyup.enter="handleAiSearch" />
        <select v-model="filterCycleType" class="ws-select" @change="handleAiSearch">
          <option value="">周期类型</option>
          <option value="MONTHLY">月度</option>
          <option value="QUARTERLY">季度</option>
          <option value="ANNUAL">年度</option>
        </select>
        <input v-model="filterDeadlineStart" type="date" class="ws-input" @change="handleAiSearch" />
        <input v-model="filterDeadlineEnd" type="date" class="ws-input" @change="handleAiSearch" />
        <input v-model="filterAssignee" type="text" class="ws-input" placeholder="经办人" @keyup.enter="handleAiSearch" />
      </div>
      <div v-if="hasSearch" class="search-result-hint">{{ searchResultHint }}</div>
    </div>

    <div class="batch-section ws-panel">
      <div class="batch-info">
        <label class="select-all">
          <input type="checkbox" :checked="selectedCount === filteredTasks.length && filteredTasks.length > 0" @change="toggleSelectAll" />
          已选择 {{ selectedCount }} 项
        </label>
        <button class="ws-btn ws-btn-danger ws-btn-sm" v-if="selectedCount > 0" @click="selectedIds = []">清空</button>
      </div>
      <div class="batch-actions">
        <button class="ws-btn ws-btn-secondary" @click="handleBatchLink">批量关联资料</button>
        <button class="ws-btn ws-btn-primary" :class="{ disabled: !canBatchSubmit }" :disabled="!canBatchSubmit">
          批量提交（条件不满足）
        </button>
      </div>
    </div>

    <div class="tasks-table-section ws-panel">
      <div class="ws-panel-header">
        <div class="ws-panel-title">我的上传任务</div>
      </div>
      <div class="ws-table-container tasks-table">
        <div class="ws-table-scroll no-scroll">
          <table class="ws-table">
            <colgroup>
              <col class="col-check" />
              <col class="col-task-name" />
              <col class="col-module" />
              <col class="col-deadline" />
              <col class="col-progress" />
              <col class="col-status" />
              <col class="col-next" />
            </colgroup>
            <thead>
              <tr>
                <th class="col-check checkbox-col">
                  <input type="checkbox" :checked="selectedCount === filteredTasks.length && filteredTasks.length > 0" @change="toggleSelectAll" />
                </th>
                <th class="col-task-name">任务名称</th>
                <th class="col-module">ESG模块</th>
                <th class="col-deadline">截止时间</th>
                <th class="col-progress">资料进度</th>
                <th class="col-status">状态</th>
                <th class="col-next">下一步</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="task in paginatedTasks"
                :key="task.id"
                :class="{ selected: isSelected(task.id) }"
                @click="emit('openTask', task.id)"
              >
                <td class="col-check checkbox-col">
                  <input type="checkbox" :checked="isSelected(task.id)" @click.stop="toggleSelect(task.id)" />
                </td>
                <td class="col-task-name task-name">{{ task.name }}</td>
                <td class="col-module">
                  <span class="module-tag" :style="{ background: `${getModuleColor(task.module)}20`, color: getModuleColor(task.module) }">
                    {{ task.module }} {{ task.moduleName }}
                  </span>
                </td>
                <td class="col-deadline" :class="{ overdue: task.daysOverdue }">{{ task.deadlineDisplay }}</td>
                <td class="col-progress">
                  <div class="ws-progress">
                    <div class="ws-progress-bar">
                      <div class="ws-progress-fill" :style="{ width: `${(task.progressCurrent / task.progressTotal) * 100}%` }"></div>
                    </div>
                    <span class="ws-progress-text">{{ task.progressCurrent }}/{{ task.progressTotal }}</span>
                  </div>
                </td>
                <td class="col-status">
                  <span class="status-tag" :style="{ background: `${getStatusColor(task.status)}20`, color: getStatusColor(task.status) }">
                    {{ task.status }}
                  </span>
                </td>
                <td class="col-next">
                  <button class="ws-btn ws-btn-action ws-btn-sm" @click.stop="emit('openTask', task.id)">
                    {{ task.nextStep }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="ws-pagination-bar">
        <div class="ws-pagination-info">共 <span class="highlight">{{ filteredTasks.length }}</span> 项，每页 {{ pageSize }} 项</div>
        <div class="ws-pagination-controls">
          <button class="ws-page-btn" :disabled="currentPage === 1" @click="goToPage(currentPage - 1)">
            <ChevronLeft :size="14" />
          </button>
          <button
            v-for="p in getPageNumbers()"
            :key="p"
            class="ws-page-btn"
            :class="{ active: currentPage === p }"
            @click="goToPage(p)"
          >
            {{ p }}
          </button>
          <button class="ws-page-btn" :disabled="currentPage === totalPages" @click="goToPage(currentPage + 1)">
            <ChevronRight :size="14" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workspace-tasks {
  min-height: 0;
}

.filter-search-row {
  flex-wrap: nowrap;
}

.search-main {
  flex: 1;
  min-width: 0;
}

.search-main .ws-btn {
  flex-shrink: 0;
}

.search-result-hint {
  font-size: 11px;
  color: #69e36f;
}

.batch-section {
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  padding: 8px 12px;
}

.batch-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.select-all {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #e8f3ff;
  cursor: pointer;
}

.batch-actions {
  display: flex;
  gap: 10px;
}

.tasks-table-section {
  flex: 1 1 auto;
  min-height: 0;
}

.tasks-table {
  border: none;
  border-radius: 0;
  background: transparent;
  flex: 1 1 auto;
  min-height: 0;
}

.tasks-table-section > .ws-pagination-bar {
  border: 1px solid rgba(47, 156, 255, 0.14);
  border-radius: 0 0 8px 8px;
}

.checkbox-col {
  width: 40px;
  text-align: center;
}

.task-name {
  font-weight: 500;
}

.overdue {
  color: #ff4f5e;
}

.ws-btn.disabled,
.ws-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
