<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import {
  Search,
  Clock,
  CheckCircle,
  XCircle,
  Archive,
  ArrowRight,
  Calendar,
  User,
  FileText,
  AlertTriangle,
  RotateCcw,
  ChevronRight,
} from 'lucide-vue-next'
import {
  reviewRecords as mockReviewRecords,
  reviewTimeline,
  reviewRequirements,
} from '@/data/workspace.mock'
import {
  getReviews,
  getReviewDetail,
  getReviewTimeline,
  getReviewRequirements,
  approveReview,
  returnReview,
} from '@/services/api'
import type {
  StatusCard,
  ReviewRecord,
  ReviewTimeline,
  TaskSourceType,
  ReviewStatus,
} from '@/types/workspace'
import {
  REVIEW_STATUS_COLORS,
  MODULE_COLORS,
} from '@/types/workspace'
import type { ReviewTimelineApi, ReviewRequirementApi } from '@/services/api'
import { emitWorkspaceRefresh, onWorkspaceRefresh } from '@/utils/workspaceRefresh'

const emit = defineEmits<{
  (e: 'openTask', taskId: string, forceTab?: string): void
}>()

const searchKeyword = ref('')
const selectedModule = ref('全部')
const selectedSourceType = ref('全部')
const startDate = ref('')
const endDate = ref('')
const selectedStatus = ref('全部')
const reviewerFilter = ref('')

const reviewRecordList = ref<ReviewRecord[]>([...mockReviewRecords])
const selectedRecordId = ref(mockReviewRecords[0]?.id || '')
const recordTimelines = ref<Record<string, ReviewTimelineApi[]>>({})
const recordRequirements = ref<Record<string, ReviewRequirementApi[]>>({})
const recordDeadlines = ref<Record<string, string>>({})
const pageMessage = ref('')
const pageMessageType = ref<'info' | 'success' | 'error'>('info')

const statusCards = computed<StatusCard[]>(() => {
  const list = reviewRecordList.value
  const pending = list.filter(r => r.status === '待审核').length
  const passed = list.filter(r => r.status === '已通过').length
  const returned = list.filter(r => r.status === '已退回').length
  const archived = list.filter(r => r.status === '已归档').length
  const overdueCorrections = list.filter(r => r.status === '已退回' && r.correctionOverdue).length
  return [
    { label: '待审核', value: pending, unit: '项', color: '#2f9cff' },
    { label: '已通过', value: passed, unit: '项', color: '#69e36f' },
    { label: '已退回', value: returned, unit: '项', subText: `其中补正逾期 ${overdueCorrections} 项`, color: '#ff4f5e' },
    { label: '已归档', value: archived, unit: '项', color: '#69e36f' },
  ]
})

let stopWorkspaceRefresh: (() => void) | null = null

const sourceTypeOptions: TaskSourceType[] = [
  'KPI指标',
  '月报任务',
  '业务事项',
  '周期任务',
  '审核补正',
  '临时任务',
]

const statusOptions: ReviewStatus[] = ['待审核', '已通过', '已退回', '已归档']

onMounted(() => {
  loadData()
  stopWorkspaceRefresh = onWorkspaceRefresh(payload => {
    if (payload.source === 'review-action') return
    if (payload.scopes.some(scope => ['reviews'].includes(scope))) {
      reloadAll()
    }
  })
})

onUnmounted(() => {
  stopWorkspaceRefresh?.()
})

async function loadData() {
  const data = await getReviews()
  if (data) {
    if (data.items && data.items.length > 0) {
      reviewRecordList.value = data.items.map((item, index) => {
        const mockRecord = mockReviewRecords[index] || mockReviewRecords[0]
        return {
          id: item.id,
          taskId: item.taskId,
          taskName: item.taskName,
          module: item.module as ReviewRecord['module'],
          moduleName: item.moduleName,
          submitTime: item.submitTime,
          status: item.status as ReviewRecord['status'],
          reviewer: item.reviewer,
          commentSummary: item.commentSummary,
          nextStep: item.nextStep,
          sourceType: mockRecord.sourceType,
          sourceName: mockRecord.sourceName,
          correctionDueDate: mockRecord.correctionDueDate,
          correctionRemaining: mockRecord.correctionRemaining,
          correctionOverdue: mockRecord.correctionOverdue,
        }
      }) as ReviewRecord[]
    }
  }
}

function showMessage(message: string, type: 'info' | 'success' | 'error' = 'info') {
  pageMessage.value = message
  pageMessageType.value = type
}

function formatTime(time: string): string {
  if (!time) return '-'
  const normalized = time.includes('T') ? time.replace('T', ' ') : time
  // Prefer full YYYY-MM-DD HH:mm:ss when present; otherwise HH:mm
  const match = normalized.match(/^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?/)
  return match ? match[0].replace('T', ' ') : normalized
}

const currentPage = ref(1)
const pageSize = ref(10)

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

function changePageSize(size: number) {
  pageSize.value = size
  currentPage.value = 1
}

function getPageNumbers(): number[] {
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

const filteredRecords = computed(() => {
  return reviewRecordList.value.filter(record => {
    if (searchKeyword.value && !record.taskName.includes(searchKeyword.value)) return false
    if (selectedModule.value !== '全部' && record.module !== selectedModule.value) return false
    if (selectedSourceType.value !== '全部' && record.sourceType !== selectedSourceType.value) return false
    if (selectedStatus.value !== '全部' && record.status !== selectedStatus.value) return false
    if (reviewerFilter.value && !record.reviewer.includes(reviewerFilter.value)) return false
    return true
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredRecords.value.length / pageSize.value)))

const paginatedRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredRecords.value.slice(start, start + pageSize.value)
})

watch(filteredRecords, () => {
  currentPage.value = 1
})

const selectedRecord = computed(() => {
  return (
    reviewRecordList.value.find(r => r.id === selectedRecordId.value) ||
    reviewRecordList.value[0]
  )
})

function getModuleColor(module: string) {
  return MODULE_COLORS[module] || '#8fa9c8'
}

function getStatusColor(status: string) {
  return REVIEW_STATUS_COLORS[status] || '#8fa9c8'
}

function getTimelineIcon(action: string) {
  if (action.includes('提交')) return ArrowRight
  if (action.includes('校验')) return CheckCircle
  if (action.includes('退回')) return XCircle
  if (action.includes('通过')) return CheckCircle
  return Clock
}

function handleReset() {
  searchKeyword.value = ''
  selectedModule.value = '全部'
  selectedSourceType.value = '全部'
  startDate.value = ''
  endDate.value = ''
  selectedStatus.value = '全部'
  reviewerFilter.value = ''
}

async function loadReviewDetail(reviewId: string) {
  const [detailRes, timelineRes, requirementsRes] = await Promise.all([
    getReviewDetail(reviewId),
    getReviewTimeline(reviewId),
    getReviewRequirements(reviewId),
  ])

  if (timelineRes && timelineRes.items) {
    recordTimelines.value[reviewId] = timelineRes.items
  }

  if (requirementsRes && requirementsRes.items) {
    recordRequirements.value[reviewId] = requirementsRes.items
  }

  const deadline = detailRes?.rectifyDeadline || detailRes?.correctionDeadline
  if (deadline) {
    recordDeadlines.value[reviewId] = deadline
  }
}

function getTimelineForRecord(recordId: string): ReviewTimeline[] {
  const apiTimeline = recordTimelines.value[recordId]
  if (apiTimeline && apiTimeline.length > 0) {
    return apiTimeline.map(item => ({
      time: item.operatedAt,
      action: item.action,
    }))
  }
  const mockTimelines: Record<string, ReviewTimeline[]> = {
    r1: [
      { time: '2026-08-05 18:00', action: '提交上传（张建国 提交任务）' },
      { time: '2026-08-05 18:05', action: '完整性校验（系统校验通过，共5/7项资料完整）' },
      { time: '2026-08-07 09:15', action: '审核退回（审核人：李安全）' },
    ],
    r2: [
      { time: '2026-08-04 14:00', action: '提交上传（王佳 提交任务）' },
      { time: '2026-08-04 14:10', action: '完整性校验（系统校验通过，共4/5项资料完整）' },
      { time: '2026-08-06 16:40', action: '审核退回（审核人：王财务）' },
    ],
    r3: [
      { time: '2026-08-03 10:00', action: '提交上传（刘淑芬 提交任务）' },
      { time: '2026-08-03 10:05', action: '完整性校验（系统校验通过，共2/3项资料完整）' },
      { time: '2026-08-06 10:20', action: '审核退回（审核人：陈质量）' },
    ],
    r4: [
      { time: '2026-07-28 16:00', action: '提交上传（陈志强 提交任务）' },
      { time: '2026-07-28 16:10', action: '完整性校验（系统校验通过，共3/4项资料完整）' },
      { time: '2026-08-05 14:30', action: '审核退回（审核人：吴质量）' },
    ],
    r5: [
      { time: '2026-08-06 09:30', action: '提交上传（赵宇航 提交任务）' },
      { time: '2026-08-06 09:35', action: '完整性校验（系统校验通过）' },
      { time: '2026-08-06 10:00', action: '进入审核队列（等待分配审核人）' },
    ],
    r6: [
      { time: '2026-08-05 17:25', action: '提交上传（孙德明 提交任务）' },
      { time: '2026-08-05 17:30', action: '完整性校验（系统校验通过）' },
      { time: '2026-08-06 09:00', action: '进入审核队列（等待分配审核人）' },
    ],
    r7: [
      { time: '2026-08-02 10:00', action: '提交上传（赵环保 提交任务）' },
      { time: '2026-08-02 10:10', action: '完整性校验（系统校验通过）' },
      { time: '2026-08-03 14:00', action: '审核通过（审核人：赵环保）' },
    ],
    r8: [
      { time: '2026-08-01 16:00', action: '提交上传（张建国 提交任务）' },
      { time: '2026-08-01 16:05', action: '完整性校验（系统校验通过）' },
      { time: '2026-08-03 16:10', action: '审核通过（审核人：赵环保）' },
    ],
    r9: [
      { time: '2026-07-15 10:00', action: '提交上传（王财务 提交任务）' },
      { time: '2026-07-15 10:10', action: '完整性校验（系统校验通过）' },
      { time: '2026-07-18 14:00', action: '审核通过（审核人：李主管）' },
      { time: '2026-07-20 10:00', action: '已归档（归档人：系统）' },
    ],
  }
  return mockTimelines[recordId] || reviewTimeline
}

function getRequirementsForRecord(recordId: string): { text: string; status?: string }[] {
  const apiRequirements = recordRequirements.value[recordId]
  if (apiRequirements && apiRequirements.length > 0) {
    return apiRequirements.map(item => ({
      text: item.requirementText,
      status: item.status,
    }))
  }
  const mockRequirements: Record<string, { text: string; status?: string }[]> = {
    r1: [
      { text: '审批签章页缺失，请补充完整并加盖单位公章。', status: '待补正' },
      { text: '附件日期与资料周期不一致，请核对后重新上传。', status: '待补正' },
    ],
    r2: [
      { text: '工资表需加盖公章，当前扫描件公章不清晰。', status: '待补正' },
      { text: '部分附件清晰度不足，建议重新扫描后上传。', status: '待补正' },
    ],
    r3: [
      { text: '土地权属证明不完整，需补充用地批复文件。', status: '待补正' },
      { text: '临时用地范围图缺失，请补充红线图。', status: '待补正' },
    ],
    r4: [
      { text: '整改证据不充分，缺少复查确认记录。', status: '待补正' },
      { text: '需补充整改前后对比照片。', status: '待补正' },
    ],
  }
  return mockRequirements[recordId] || []
}

function getMissingDocsForRecord(recordId: string): string[] {
  const mockMissing: Record<string, string[]> = {
    r1: ['审批签章页', '附件日期核对说明'],
    r2: ['工资表公章页', '高清扫描件'],
    r3: ['用地批复文件', '临时用地红线图'],
    r4: ['复查确认记录', '整改对比照片'],
  }
  return mockMissing[recordId] || []
}

function handleRectify() {
  const record = selectedRecord.value
  if (!record) return
  const taskIdMap: Record<string, string> = {
    r1: 't2',
    r2: 't3',
    r3: 't4',
    r4: 't4',
  }
  const taskId = record.taskId || taskIdMap[record.id] || 't2'
  emit('openTask', taskId, '审核记录')
}

function handleViewResult() {
  showMessage('查看结果功能为原型预留，后续可接入任务详情页面。', 'info')
}

function handleViewArchive() {
  showMessage('查看归档资料功能为原型预留，后续可接入资料详情页面。', 'info')
}

function handleViewProgress() {
  showMessage('查看进度功能为原型预留，后续可接入审核进度页面。', 'info')
}

function handleEnterReview() {
  showMessage('进入审核功能为原型预留，后续可接入审核操作页面。', 'info')
}

async function handleApprove() {
  const reviewId = selectedRecord.value?.id
  if (!reviewId) return

  const res = await approveReview(reviewId, {
    reviewer: '项目审核人',
    comment: '资料完整，审核通过',
  })

  if (res && res.ok) {
    showMessage(res.message || '审核通过成功', 'success')
    await reloadAll()
    emitWorkspaceRefresh({
      source: 'review-action',
      scopes: ['summary', 'tasks', 'reviews'],
      reviewId,
    })
  } else if (res && !res.ok) {
    showMessage(res.message || '审核通过失败', 'error')
  } else {
    showMessage('审核接口未响应，已保留当前展示数据', 'error')
  }
}

async function handleReturn() {
  const reviewId = selectedRecord.value?.id
  if (!reviewId) return

  if (!confirm('确认退回该审核记录？将生成补正要求。')) return

  const res = await returnReview(reviewId, {
    reviewer: '项目审核人',
    comment: '附件签章和日期信息需补正',
    requirements: ['请补充资料签章页。', '请重新上传日期清晰的扫描件。'],
  })

  if (res && res.ok) {
    showMessage(res.message || '审核退回成功', 'success')
    await reloadAll()
    emitWorkspaceRefresh({
      source: 'review-action',
      scopes: ['summary', 'tasks', 'reviews'],
      reviewId,
    })
  } else if (res && !res.ok) {
    showMessage(res.message || '审核退回失败', 'error')
  } else {
    showMessage('审核接口未响应，已保留当前展示数据', 'error')
  }
}

async function reloadAll() {
  const reviewId = selectedRecord.value?.id
  await loadData()
  if (reviewId) {
    await loadReviewDetail(reviewId)
  }
}

function handleNextStep(record: ReviewRecord) {
  switch (record.status) {
    case '待审核':
      handleEnterReview()
      break
    case '已通过':
      handleViewResult()
      break
    case '已退回':
      handleRectify()
      break
    case '已归档':
      handleViewArchive()
      break
  }
}

function getNextStepText(status: string): string {
  switch (status) {
    case '待审核':
      return '进入审核'
    case '已通过':
      return '查看结果'
    case '已退回':
      return '进入补正'
    case '已归档':
      return '查看归档资料'
    default:
      return '查看详情'
  }
}
</script>

<template>
  <div class="workspace-review ws-page">
    <div v-if="pageMessage" :class="['ws-page-message', pageMessageType]">
      {{ pageMessage }}
    </div>

    <div class="ws-status-cards cols-4">
      <div
        v-for="card in statusCards"
        :key="card.label"
        class="ws-status-card with-icon"
        :style="{ '--accent-color': card.color }"
        @click="selectedStatus = card.label"
      >
        <div class="ws-card-icon">
          <Clock v-if="card.label === '待审核'" :size="18" />
          <CheckCircle v-else-if="card.label === '已通过'" :size="18" />
          <XCircle v-else-if="card.label === '已退回'" :size="18" />
          <Archive v-else-if="card.label === '已归档'" :size="18" />
        </div>
        <div class="ws-card-body">
          <div class="ws-card-label">{{ card.label }}</div>
          <div class="ws-card-value-row">
            <span class="ws-card-value">{{ card.value }}</span>
            <span class="ws-card-unit">{{ card.unit }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="main-content">
      <div class="left-section">
        <div class="ws-filter-bar filter-panel">
          <div class="ws-filter-row filter-row">
            <div class="filter-item">
              <span class="filter-label">任务名称</span>
              <div class="filter-input-wrap">
                <Search :size="14" class="filter-icon" />
                <input v-model="searchKeyword" type="text" placeholder="请输入任务名称" />
              </div>
            </div>
            <div class="filter-item">
              <span class="filter-label">ESG模块</span>
              <select v-model="selectedModule">
                <option value="全部">全部</option>
                <option value="E">E 环境环保</option>
                <option value="S">S 社会责任</option>
                <option value="G">G 治理合规</option>
              </select>
            </div>
            <div class="filter-item">
              <span class="filter-label">来源类型</span>
              <select v-model="selectedSourceType">
                <option value="全部">全部</option>
                <option v-for="src in sourceTypeOptions" :key="src" :value="src">
                  {{ src }}
                </option>
              </select>
            </div>
          </div>
          <div class="ws-filter-row filter-row">
            <div class="filter-item">
              <span class="filter-label">提交日期</span>
              <div class="date-range">
                <div class="filter-input-wrap">
                  <Calendar :size="14" class="filter-icon" />
                  <input v-model="startDate" type="text" placeholder="开始日期" />
                </div>
                <span class="date-separator">~</span>
                <div class="filter-input-wrap">
                  <Calendar :size="14" class="filter-icon" />
                  <input v-model="endDate" type="text" placeholder="结束日期" />
                </div>
              </div>
            </div>
            <div class="filter-item">
              <span class="filter-label">审核状态</span>
              <select v-model="selectedStatus">
                <option value="全部">全部</option>
                <option v-for="st in statusOptions" :key="st" :value="st">
                  {{ st }}
                </option>
              </select>
            </div>
            <div class="filter-item">
              <span class="filter-label">审核人</span>
              <div class="filter-input-wrap">
                <User :size="14" class="filter-icon" />
                <input v-model="reviewerFilter" type="text" placeholder="请输入审核人" />
              </div>
            </div>
            <button class="ws-btn ws-btn-secondary" @click="handleReset">
              <RotateCcw :size="14" />
              重置
            </button>
          </div>
        </div>

        <div class="ws-table-container">
          <div class="ws-table-scroll" :class="{ 'no-scroll': pageSize <= 10 }">
            <table class="ws-table">
              <colgroup>
                <col class="col-task-name" />
                <col class="col-source" />
                <col class="col-module" />
                <col class="col-time" />
                <col class="col-status" />
                <col class="col-reviewer" />
                <col class="col-comment" />
                <col class="col-action" />
              </colgroup>
              <thead>
                <tr>
                  <th class="col-task-name">任务名称</th>
                  <th class="col-source">来源/关联事项</th>
                  <th class="col-module">ESG模块</th>
                  <th class="col-time">提交时间</th>
                  <th class="col-status">审核状态</th>
                  <th class="col-reviewer">审核人</th>
                  <th class="col-comment">审核意见摘要</th>
                  <th class="col-action">下一步</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="record in paginatedRecords"
                  :key="record.id"
                  :class="{ selected: selectedRecordId === record.id }"
                  @click="selectedRecordId = record.id; loadReviewDetail(record.id)"
                >
                  <td class="col-task-name">
                    <span class="task-name-text">{{ record.taskName }}</span>
                  </td>
                  <td class="col-source">
                    <div class="source-cell">
                      <span class="source-type-tag">{{ record.sourceType }}</span>
                      <span class="source-name" :title="record.sourceName">
                        {{ record.sourceName || '-' }}
                      </span>
                    </div>
                  </td>
                  <td class="col-module">
                    <span
                      class="module-tag"
                      :style="{
                        background: `${getModuleColor(record.module)}20`,
                        color: getModuleColor(record.module),
                      }"
                    >
                      {{ record.module }} {{ record.moduleName }}
                    </span>
                  </td>
                  <td class="col-time">{{ formatTime(record.submitTime) }}</td>
                  <td class="col-status">
                    <span
                      class="status-tag"
                      :style="{
                        background: `${getStatusColor(record.status)}20`,
                        color: getStatusColor(record.status),
                      }"
                    >
                      {{ record.status }}
                    </span>
                  </td>
                  <td class="col-reviewer">{{ record.reviewer || '-' }}</td>
                  <td class="col-comment">
                    <div class="comment-text">{{ record.commentSummary || '-' }}</div>
                  </td>
                  <td class="col-action">
                    <button
                      class="next-step-btn"
                      :style="{ color: getStatusColor(record.status) }"
                      @click.stop="handleNextStep(record)"
                    >
                      {{ getNextStepText(record.status) }}
                      <ChevronRight :size="14" />
                    </button>
                  </td>
                </tr>
                <tr v-if="paginatedRecords.length === 0">
                  <td colspan="8" class="empty-row">暂无审核记录</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="ws-pagination-bar">
          <div class="ws-pagination-info">
            共 <span class="highlight">{{ filteredRecords.length }}</span> 条记录，第 {{ currentPage }}/{{ totalPages }} 页
          </div>
          <div class="ws-pagination-controls">
            <select v-model.number="pageSize" class="ws-page-size-select" @change="changePageSize(pageSize)">
              <option :value="10">10 条/页</option>
              <option :value="20">20 条/页</option>
              <option :value="30">30 条/页</option>
            </select>
            <button class="ws-page-btn" :disabled="currentPage === 1" @click="goToPage(currentPage - 1)">上一页</button>
            <button
              v-for="p in getPageNumbers()"
              :key="p"
              class="ws-page-btn"
              :class="{ active: currentPage === p }"
              @click="goToPage(p)"
            >
              {{ p }}
            </button>
            <button class="ws-page-btn" :disabled="currentPage === totalPages" @click="goToPage(currentPage + 1)">下一页</button>
          </div>
        </div>
      </div>

      <div class="right-section">
        <div class="ws-detail-panel">
          <div class="ws-detail-header">
            <FileText :size="18" class="ws-detail-header-icon" />
            <span class="ws-detail-title">审核详情</span>
          </div>

          <div class="ws-detail-content">
            <div class="ws-detail-section">
              <div class="ws-section-title">基本信息</div>
              <div class="info-grid">
                <div class="info-item">
                  <span class="info-label">任务名称</span>
                  <span class="info-value task-name-full">{{ selectedRecord?.taskName }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">来源类型</span>
                  <span class="info-value">{{ selectedRecord?.sourceType || '-' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">关联事项</span>
                  <span class="info-value">{{ selectedRecord?.sourceName || '-' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">ESG模块</span>
                  <span
                    class="module-tag-sm"
                    :style="{
                      background: `${getModuleColor(selectedRecord?.module || '')}20`,
                      color: getModuleColor(selectedRecord?.module || ''),
                    }"
                  >
                    {{ selectedRecord?.module }} {{ selectedRecord?.moduleName }}
                  </span>
                </div>
                <div class="info-item">
                  <span class="info-label">提交时间</span>
                  <span class="info-value">{{ formatTime(selectedRecord?.submitTime || '') }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">审核状态</span>
                  <span
                    class="status-tag-sm"
                    :style="{
                      background: `${getStatusColor(selectedRecord?.status || '')}20`,
                      color: getStatusColor(selectedRecord?.status || ''),
                    }"
                  >
                    {{ selectedRecord?.status }}
                  </span>
                </div>
                <div class="info-item">
                  <span class="info-label">审核人</span>
                  <span class="info-value">{{ selectedRecord?.reviewer || '-' }}</span>
                </div>
              </div>
            </div>

            <div class="ws-detail-section">
              <div class="ws-section-title">审核轨迹</div>
              <div class="timeline">
                <div
                  v-for="(item, index) in getTimelineForRecord(selectedRecord?.id || '')"
                  :key="index"
                  class="timeline-item"
                >
                  <div
                    class="timeline-dot"
                    :class="{
                      last:
                        index ===
                        getTimelineForRecord(selectedRecord?.id || '').length - 1,
                    }"
                  >
                    <component :is="getTimelineIcon(item.action)" :size="12" />
                  </div>
                  <div class="timeline-content">
                    <span class="timeline-action">{{ item.action }}</span>
                    <span class="timeline-time">{{ formatTime(item.time) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="selectedRecord?.status === '已通过' || selectedRecord?.status === '已归档'" class="ws-detail-section">
              <div class="ws-section-title">审核结论</div>
              <div class="conclusion-box">
                <div class="conclusion-text">
                  {{ selectedRecord?.commentSummary || '资料完整，符合填报要求' }}
                </div>
              </div>
              <div class="conclusion-meta">
                <div class="meta-item">
                  <span class="meta-label">审核人</span>
                  <span class="meta-value">{{ selectedRecord?.reviewer || '-' }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">审核时间</span>
                  <span class="meta-value">
                    {{ formatTime(getTimelineForRecord(selectedRecord?.id || '').find(t => t.action.includes('通过'))?.time || '') }}
                  </span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">归档状态</span>
                  <span
                    class="archive-status"
                    :class="{ archived: selectedRecord?.status === '已归档' }"
                  >
                    {{ selectedRecord?.status === '已归档' ? '已归档' : '待归档' }}
                  </span>
                </div>
              </div>
              <button
                v-if="selectedRecord?.status === '已归档'"
                class="ws-btn ws-btn-primary action-btn"
                @click="handleViewArchive"
              >
                <Archive :size="16" />
                查看归档资料
              </button>
              <button
                v-else
                class="ws-btn ws-btn-primary action-btn"
                @click="handleViewResult"
              >
                <CheckCircle :size="16" />
                查看结果
              </button>
            </div>

            <div v-if="selectedRecord?.status === '已退回'" class="ws-detail-section">
              <div class="ws-section-title">退回原因</div>
              <div class="return-reason-box">
                <AlertTriangle :size="16" class="return-icon" />
                <span class="return-reason-text">
                  {{ selectedRecord?.commentSummary || '资料不完整，需补正后重新提交' }}
                </span>
              </div>
            </div>

            <div v-if="selectedRecord?.status === '已退回'" class="ws-detail-section">
              <div class="ws-section-title">缺失资料</div>
              <div class="missing-docs-list">
                <div
                  v-for="(doc, idx) in getMissingDocsForRecord(selectedRecord?.id || '')"
                  :key="idx"
                  class="missing-doc-item"
                >
                  <XCircle :size="14" class="missing-icon" />
                  <span>{{ doc }}</span>
                </div>
              </div>
            </div>

            <div v-if="selectedRecord?.status === '已退回'" class="ws-detail-section">
              <div class="ws-section-title">
                补正要求
                <span class="requirement-count">
                  {{ getRequirementsForRecord(selectedRecord?.id || '').length }} 条
                </span>
              </div>
              <div class="requirements-list">
                <div
                  v-for="(req, idx) in getRequirementsForRecord(selectedRecord?.id || '')"
                  :key="idx"
                  class="requirement-item"
                >
                  <span class="requirement-number">{{ idx + 1 }}</span>
                  <span class="requirement-text">{{ req.text }}</span>
                </div>
              </div>
            </div>

            <div v-if="selectedRecord?.status === '已退回'" class="ws-detail-section">
              <div class="deadline-card">
                <div class="deadline-row">
                  <span class="deadline-label">补正截止时间</span>
                  <span class="deadline-value">
                    {{ formatTime(selectedRecord?.correctionDueDate || '2026-08-10 18:00') }}
                  </span>
                </div>
                <div class="deadline-row">
                  <span class="deadline-label">剩余时间</span>
                  <span
                    class="remaining-time"
                    :class="{ overdue: selectedRecord?.correctionOverdue }"
                  >
                    {{ selectedRecord?.correctionRemaining || '剩余 3 天' }}
                  </span>
                </div>
              </div>
            </div>

            <div v-if="selectedRecord?.status === '待审核'" class="ws-detail-section">
              <div class="ws-section-title">审核结论</div>
              <div class="pending-tip">
                <Clock :size="20" class="pending-icon" />
                <span>该任务正在等待审核，请耐心等待或进入审核页面处理。</span>
              </div>
              <div class="review-actions">
                <button class="ws-btn ws-btn-danger action-btn return-action" @click="handleReturn">
                  <XCircle :size="16" />
                  审核退回
                </button>
                <button class="ws-btn ws-btn-primary action-btn approve-action" @click="handleApprove">
                  <CheckCircle :size="16" />
                  审核通过
                </button>
              </div>
            </div>
          </div>

          <div v-if="selectedRecord?.status === '已退回'" class="ws-detail-footer">
            <button class="ws-btn ws-btn-warn action-btn" @click="handleRectify">
              <RotateCcw :size="16" />
              进入补正
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workspace-review {
  min-height: 0;
}

.main-content {
  display: flex;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.left-section {
  flex: 0 0 65%;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  gap: var(--ws-section-gap, 8px);
}

.left-section > .ws-table-container {
  flex: 1 1 auto;
  min-height: 0;
}

.left-section > .ws-table-container + .ws-pagination-bar {
  flex: 0 0 auto;
  margin-top: calc(-1 * var(--ws-section-gap, 12px));
}

.right-section {
  flex: 1;
  min-width: 0;
}

.filter-panel {
  /* chrome from .ws-filter-bar */
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 0;
  margin-bottom: 0;
  flex-shrink: 0;
  gap: 6px;
}

.filter-row {
  /* spacing from .ws-filter-row */
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-row + .filter-row {
  margin-top: 0;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.filter-label {
  font-size: 12px;
  color: #8fa9c8;
  white-space: nowrap;
  flex-shrink: 0;
}

.filter-input-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 6px;
  padding: 6px 10px;
  color: #8fa9c8;
  flex: 1;
  min-width: 0;
}

.filter-icon {
  flex-shrink: 0;
}

.filter-input-wrap input {
  background: transparent;
  border: none;
  color: #e8f3ff;
  font-size: 12px;
  flex: 1;
  outline: none;
  min-width: 0;
}

.filter-item select {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 6px;
  padding: 6px 10px;
  color: #e8f3ff;
  font-size: 12px;
  outline: none;
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.date-range {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.date-separator {
  color: #8fa9c8;
  font-size: 12px;
  flex-shrink: 0;
}

.reset-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: rgba(105, 227, 111, 0.08);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 6px;
  color: #8fa9c8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
  white-space: nowrap;
}

.reset-btn:hover {
  color: #69e36f;
  border-color: rgba(105, 227, 111, 0.4);
}

.ws-table {
  table-layout: fixed;
}

/* Review 列宽：名称/意见吃剩余；时间列保证完整 datetime */
.col-task-name {
  width: auto;
}

.col-source {
  width: 160px;
}

.col-module {
  width: 130px;
}

.col-time {
  width: 176px;
}

.col-status {
  width: 96px;
}

.col-reviewer {
  width: 88px;
}

.col-comment {
  width: 18%;
}

.col-action {
  width: 120px;
}

.task-name-text {
  font-weight: 500;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.source-type-tag {
  display: inline-block;
  padding: 2px 6px;
  background: rgba(166, 108, 255, 0.15);
  color: #a66cff;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  align-self: flex-start;
  white-space: nowrap;
}

.source-name {
  font-size: 12px;
  color: #8fa9c8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

.module-tag,
.status-tag {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.comment-text {
  font-size: 12px;
  color: #8fa9c8;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-all;
  white-space: normal;
}

.ws-table td.col-action {
  text-align: left;
}

.next-step-btn {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 4px 8px;
  background: transparent;
  border: 1px solid currentColor;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  opacity: 0.8;
  transition: all 0.2s;
  white-space: nowrap;
}

.next-step-btn:hover {
  opacity: 1;
  background: color-mix(in srgb, currentColor 10%, transparent);
}

.empty-row {
  text-align: center;
  color: #5a7a9a;
  padding: 40px !important;
  font-size: 12px;
}

.requirement-count {
  font-size: 11px;
  color: #ff4f5e;
  font-weight: 500;
  background: rgba(255, 79, 94, 0.15);
  padding: 2px 8px;
  border-radius: 10px;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.info-label {
  font-size: 12px;
  color: #8fa9c8;
  flex-shrink: 0;
  width: 70px;
  padding-top: 1px;
}

.info-value {
  font-size: 13px;
  color: #e8f3ff;
  flex: 1;
  word-break: break-all;
}

.task-name-full {
  font-weight: 500;
}

.module-tag-sm,
.status-tag-sm {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.timeline {
  position: relative;
  padding-left: 20px;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 6px;
  top: 4px;
  bottom: 4px;
  width: 2px;
  background: rgba(105, 227, 111, 0.15);
}

.timeline-item {
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
  position: relative;
}

.timeline-item:last-child {
  margin-bottom: 0;
}

.timeline-dot {
  position: absolute;
  left: -20px;
  top: 2px;
  width: 14px;
  height: 14px;
  background: rgba(5, 26, 50, 0.8);
  border: 2px solid #69e36f;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #69e36f;
  z-index: 1;
}

.timeline-dot.last {
  border-color: #ff4f5e;
  color: #ff4f5e;
}

.timeline-content {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
}

.timeline-action {
  font-size: 12px;
  color: #e8f3ff;
  line-height: 1.4;
}

.timeline-time {
  font-size: 11px;
  color: #5a7a9a;
}

.conclusion-box {
  background: rgba(105, 227, 111, 0.08);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.conclusion-text {
  font-size: 13px;
  color: #69e36f;
  line-height: 1.5;
}

.conclusion-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.meta-label {
  font-size: 12px;
  color: #8fa9c8;
  width: 70px;
  flex-shrink: 0;
}

.meta-value {
  font-size: 12px;
  color: #e8f3ff;
  flex: 1;
}

.archive-status {
  display: inline-block;
  padding: 2px 8px;
  background: rgba(143, 169, 200, 0.15);
  color: #8fa9c8;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.archive-status.archived {
  background: rgba(105, 227, 111, 0.15);
  color: #69e36f;
}

.action-btn {
  width: 100%;
  padding: 10px 16px;
  border-radius: 8px;
  gap: 6px;
}

.return-reason-box {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: rgba(255, 79, 94, 0.08);
  border: 1px solid rgba(255, 79, 94, 0.2);
  border-radius: 8px;
  padding: 12px;
}

.return-icon {
  color: #ff4f5e;
  flex-shrink: 0;
  margin-top: 1px;
}

.return-reason-text {
  font-size: 13px;
  color: #ff8894;
  line-height: 1.5;
  flex: 1;
}

.missing-docs-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.missing-doc-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  font-size: 12px;
  color: #e8f3ff;
}

.missing-icon {
  color: #ff4f5e;
  flex-shrink: 0;
}

.requirements-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.requirement-item {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  align-items: flex-start;
}

.requirement-number {
  width: 18px;
  height: 18px;
  background: rgba(255, 79, 94, 0.2);
  border: 1px solid rgba(255, 79, 94, 0.4);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: #ff4f5e;
  flex-shrink: 0;
  font-weight: 600;
}

.requirement-text {
  font-size: 12px;
  color: #e8f3ff;
  line-height: 1.5;
  flex: 1;
}

.deadline-card {
  background: rgba(255, 79, 94, 0.08);
  border: 1px solid rgba(255, 79, 94, 0.2);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.deadline-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.deadline-row + .deadline-row {
  margin-top: 8px;
}

.deadline-label {
  font-size: 12px;
  color: #8fa9c8;
}

.deadline-value {
  font-size: 12px;
  color: #e8f3ff;
  font-weight: 500;
}

.remaining-time {
  font-size: 13px;
  color: #ffb347;
  font-weight: 600;
}

.remaining-time.overdue {
  color: #ff4f5e;
}

.pending-tip {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px;
  background: rgba(47, 156, 255, 0.08);
  border: 1px solid rgba(47, 156, 255, 0.2);
  border-radius: 8px;
  margin-bottom: 16px;
}

.pending-icon {
  color: #2f9cff;
  flex-shrink: 0;
  margin-top: 1px;
}

.pending-tip span {
  font-size: 12px;
  color: #9fc7ff;
  line-height: 1.5;
  flex: 1;
}

.review-actions {
  display: flex;
  gap: 12px;
}

.return-action {
  flex: 1;
}

.approve-action {
  flex: 1;
}

.ws-table-scroll::-webkit-scrollbar,
.ws-detail-content::-webkit-scrollbar {
  width: 6px;
}

.ws-table-scroll::-webkit-scrollbar-track,
.ws-detail-content::-webkit-scrollbar-track {
  background: transparent;
}

.ws-table-scroll::-webkit-scrollbar-thumb,
.ws-detail-content::-webkit-scrollbar-thumb {
  background: rgba(105, 227, 111, 0.2);
  border-radius: 3px;
}

.ws-table-scroll::-webkit-scrollbar-thumb:hover,
.ws-detail-content::-webkit-scrollbar-thumb:hover {
  background: rgba(105, 227, 111, 0.3);
}
</style>
