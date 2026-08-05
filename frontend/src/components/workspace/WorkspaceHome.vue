<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Upload, FolderOpen, ChevronLeft, ChevronRight, ArrowRight } from 'lucide-vue-next'
import {
  workspaceStatusCards as mockWorkspaceStatusCards,
  allUploadTasks,
  todayFocusList,
} from '@/data/workspace.mock'
import { useRouter } from 'vue-router'
import { getWorkspaceSummary, getWorkspaceTasks } from '@/services/api'
import type { UploadTask, StatusCard } from '@/types/workspace'
import { onWorkspaceRefresh } from '@/utils/workspaceRefresh'

const router = useRouter()

const emit = defineEmits<{
  (e: 'navigate', key: string, status?: string): void
  (e: 'openTask', taskId: string): void
}>()
const currentPage = ref(1)
const pageSize = 10
const taskList = ref<UploadTask[]>([...allUploadTasks])
const statusCards = ref<StatusCard[]>([...mockWorkspaceStatusCards])

let stopWorkspaceRefresh: (() => void) | null = null

onMounted(() => {
  loadData()
  stopWorkspaceRefresh = onWorkspaceRefresh(payload => {
    if (payload.scopes.some(scope => ['summary', 'tasks'].includes(scope))) {
      loadData()
    }
  })
})

onUnmounted(() => {
  stopWorkspaceRefresh?.()
})

async function loadData() {
  const [summaryRes, tasksRes] = await Promise.all([
    getWorkspaceSummary(),
    getWorkspaceTasks(),
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
  }
}

function handleStatusCardClick(label: string) {
  let status = ''
  if (label === '待上传') status = '待上传'
  else if (label === '待补正') status = '待补正'
  else if (label === '待提交') status = '待提交'
  emit('navigate', 'tasks', status)
}

function handleUploadClick() {
  emit('navigate', 'smart-upload')
}

function handleBatchImport() {
  emit('navigate', 'smart-upload')
}

function handleTaskClick(taskId: string) {
  emit('openTask', taskId)
}

function goToAssistant() {
  router.push('/assistant')
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
    case '审核退回': return '#ff4f5e'
    default: return '#8fa9c8'
  }
}

const statusPriority: Record<string, number> = {
  '已逾期': 0,
  '审核退回': 1,
  '即将到期': 2,
  '待补正': 3,
  '待上传': 4,
  '待提交': 5,
}

const sortedTasks = computed(() => {
  return [...taskList.value].sort((a, b) => {
    const aType = a.daysOverdue ? '已逾期' : a.status
    const bType = b.daysOverdue ? '已逾期' : b.status
    const aPriority = statusPriority[aType] ?? 9
    const bPriority = statusPriority[bType] ?? 9
    if (aPriority !== bPriority) return aPriority - bPriority
    return new Date(a.deadline).getTime() - new Date(b.deadline).getTime()
  })
})

const totalPages = computed(() => Math.ceil(sortedTasks.value.length / pageSize))

const paginatedTasks = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return sortedTasks.value.slice(start, start + pageSize)
})

watch(sortedTasks, () => {
  currentPage.value = 1
})

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

function getPageNumbers() {
  const pages: number[] = []
  for (let i = 1; i <= totalPages.value; i++) pages.push(i)
  return pages
}

function getFocusTypeClass(type: string) {
  switch (type) {
    case 'overdue': return 'overdue'
    case 'urgent': return 'urgent'
    case 'today': return 'today'
    default: return 'normal'
  }
}
</script>

<template>
  <div class="workspace-home ws-page">
    <div class="main-content">
      <div class="ws-status-cards cols-6">
        <div
          v-for="card in statusCards"
          :key="card.label"
          class="ws-status-card"
          :style="{ '--accent-color': card.color }"
          @click="handleStatusCardClick(card.label)"
        >
          <div class="ws-card-label">{{ card.label }}</div>
          <div class="ws-card-value-row">
            <span class="ws-card-value">{{ card.value }}</span>
            <span class="ws-card-unit">{{ card.unit }}</span>
          </div>
          <div v-if="card.subText" class="ws-card-subtext">{{ card.subText }}</div>
        </div>
      </div>

      <div class="smart-upload-section ws-panel">
        <div class="ws-panel-header">
          <div class="ws-panel-title">ESG 智能入库</div>
        </div>
        <div class="upload-buttons">
          <button class="ws-btn ws-btn-primary" @click="handleUploadClick">
            <Upload :size="16" />
            <span>上传文件</span>
          </button>
          <button class="ws-btn ws-btn-secondary" @click="handleBatchImport">
            <FolderOpen :size="16" />
            <span>批量导入</span>
          </button>
        </div>
      </div>

      <div class="tasks-section ws-panel">
        <div class="ws-panel-header">
          <div class="ws-panel-title">我的上传任务</div>
        </div>
        <div class="ws-table-container home-table">
          <div class="ws-table-scroll no-scroll">
            <table class="ws-table">
              <colgroup>
                <col class="col-task-name" />
                <col class="col-module" />
                <col class="col-deadline" />
                <col class="col-progress" />
                <col class="col-status" />
                <col class="col-next" />
              </colgroup>
              <thead>
                <tr>
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
                  @click="handleTaskClick(task.id)"
                >
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
                    <button class="ws-btn ws-btn-action ws-btn-sm" @click.stop="handleTaskClick(task.id)">
                      {{ task.nextStep }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="ws-pagination-bar">
          <div class="ws-pagination-info">共 <span class="highlight">{{ sortedTasks.length }}</span> 项，每页 {{ pageSize }} 项</div>
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

    <aside class="right-sidebar">
      <div class="assistant-card ws-panel" @click="goToAssistant">
        <div class="card-header">
          <div class="ws-panel-title">ESG 智能助手</div>
        </div>
        <div class="greeting">Hi，项目管理员</div>
        <div class="assistant-entry">
          <span>询问待办任务、缺失资料或上传要求</span>
          <ArrowRight :size="16" />
        </div>
      </div>

      <div class="focus-card ws-panel">
        <div class="card-header">
          <div class="ws-panel-title">今日重点关注</div>
          <div class="ws-panel-count">最多 4 条</div>
        </div>
        <div class="focus-list">
          <div
            v-for="item in todayFocusList"
            :key="item.id"
            class="focus-item"
            :class="getFocusTypeClass(item.type)"
            @click="handleTaskClick(item.id.replace('f', 't'))"
          >
            <span class="focus-name">{{ item.name }}</span>
            <span class="focus-value">{{ item.value }}</span>
          </div>
        </div>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.workspace-home {
  display: grid;
  grid-template-columns: minmax(0, 1fr) clamp(420px, 26vw, 500px);
  gap: var(--ws-section-gap, 12px);
  overflow: hidden;
}

.main-content {
  display: flex;
  flex-direction: column;
  gap: var(--ws-section-gap, 12px);
  min-width: 0;
  min-height: 0;
}

.right-sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--ws-section-gap, 12px);
  min-width: 0;
  min-height: 0;
}

.upload-buttons {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.smart-upload-section {
  flex-shrink: 0;
}

.smart-upload-section .ws-panel-header {
  margin-bottom: 8px;
}

.tasks-section {
  flex: 1;
  min-height: 0;
}

.home-table {
  border: none;
  border-radius: 0;
  background: transparent;
  flex: 1 1 auto;
  min-height: 0;
}

.tasks-section > .ws-pagination-bar {
  border: 1px solid rgba(47, 156, 255, 0.14);
  border-radius: 0 0 8px 8px;
}

.task-name {
  font-weight: 500;
}

.overdue {
  color: #ff4f5e;
}

.assistant-card {
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.assistant-card:hover {
  border-color: rgba(47, 156, 255, 0.35);
  box-shadow: 0 0 16px rgba(47, 156, 255, 0.08);
}

.focus-card {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.greeting {
  font-size: 13px;
  color: #8fa9c8;
  margin-bottom: 8px;
}

.assistant-entry {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(47, 156, 255, 0.15);
  border-radius: 8px;
  color: #5a7a9a;
  font-size: 13px;
  transition: all 0.2s;
}

.assistant-entry span {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.assistant-entry svg {
  color: #2f9cff;
  flex-shrink: 0;
  margin-left: 8px;
}

.assistant-card:hover .assistant-entry {
  border-color: rgba(47, 156, 255, 0.3);
  color: #8fa9c8;
}

.focus-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.focus-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 10px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.focus-item:hover {
  background: rgba(47, 156, 255, 0.08);
}

.focus-name {
  font-size: 12px;
  color: #e8f3ff;
  line-height: 1.4;
  white-space: normal;
}

.focus-value {
  font-size: 11px;
  font-weight: 500;
  flex-shrink: 0;
}

.focus-item.overdue .focus-value {
  color: #ff4f5e;
}

.focus-item.urgent .focus-value {
  color: #ffb347;
}

.focus-item.today .focus-value {
  color: #2f9cff;
}

.focus-item.normal .focus-value {
  color: #69e36f;
}
</style>
