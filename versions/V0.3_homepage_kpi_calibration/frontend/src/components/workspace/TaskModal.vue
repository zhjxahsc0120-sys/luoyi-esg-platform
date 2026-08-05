<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { X, Download, Upload, Link2, AlertCircle, Check } from 'lucide-vue-next'
import type { UploadTask } from '@/types/workspace'
import { taskDocuments as mockTaskDocuments, taskTabs } from '@/data/workspace.mock'
import { getTaskDetail, saveTaskDraft, linkTaskDocument, submitTaskReview } from '@/services/api'
import { emitWorkspaceRefresh } from '@/utils/workspaceRefresh'
import type {
  TaskDocumentApi,
  LinkedDocumentApi,
  ValidationIssueApi,
  CandidateDocumentApi,
  TaskReviewRecordApi,
} from '@/services/api'

const props = defineProps<{
  task: UploadTask
  forceTab?: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const activeTab = ref('资料要求')
const showDocumentSelector = ref(false)
const submitMessage = ref('')
const submitMessageType = ref<'success' | 'error' | 'info'>('error')

const apiDocuments = ref<TaskDocumentApi[]>([])
const apiLinkedDocuments = ref<LinkedDocumentApi[]>([])
const apiValidationIssues = ref<ValidationIssueApi[]>([])
const apiCandidateDocuments = ref<CandidateDocumentApi[]>([])
const apiReviewRecords = ref<TaskReviewRecordApi[]>([])
const apiReviewTimeline = ref<{ time: string; action: string }[]>([])
const apiAiTip = ref('')
const apiCanSubmit = ref<boolean | null>(null)
const apiTask = ref<UploadTask | null>(null)

const mockCandidateDocuments = [
  { id: 'c1', documentId: null, requirementId: null, name: '弃渣场巡查记录_2026-07.pdf', cycle: '2026-07', unit: '水保监测单位', linkCount: 2, matchRate: 96 },
  { id: 'c2', documentId: null, requirementId: null, name: '水保监测记录_2026-07.xlsx', cycle: '2026-07', unit: '水保监测单位', linkCount: 1, matchRate: 92 },
  { id: 'c3', documentId: null, requirementId: null, name: '水保监测实施方案_2026.pdf', cycle: '2026年度', unit: '水保监测单位', linkCount: 3, matchRate: 88 },
  { id: 'c4', documentId: null, requirementId: null, name: '复绿恢复统计表_2026-07.xlsx', cycle: '2026-07', unit: '工程管理部', linkCount: 0, matchRate: 85 },
  { id: 'c5', documentId: null, requirementId: null, name: '扰动面积变化表_2026-07.xlsx', cycle: '2026-07', unit: '工程管理部', linkCount: 1, matchRate: 82 },
]

const selectedCandidate = ref('c1')

const displayDocuments = computed(() => {
  return apiDocuments.value.length > 0 ? apiDocuments.value : mockTaskDocuments
})

const displayCandidateDocuments = computed(() => {
  return apiCandidateDocuments.value.length > 0 ? apiCandidateDocuments.value : mockCandidateDocuments
})

const displayReviewTimeline = computed(() => {
  return apiReviewTimeline.value.length > 0 ? apiReviewTimeline.value : [
    { time: '2026-08-05 18:00', action: '提交上传（张建国 提交任务）' },
    { time: '2026-08-05 18:05', action: '完整性校验（系统校验通过，共5/7项资料完整）' },
  ]
})

const currentTask = computed(() => apiTask.value || props.task)

const defaultTab = computed(() => {
  if (currentTask.value.status === '待上传') return '资料要求'
  if (currentTask.value.status === '待补正' || currentTask.value.status === '审核退回') return '校验问题'
  if (currentTask.value.status === '待提交') return '已关联资料'
  return '资料要求'
})

async function loadTaskDetail() {
  const res = await getTaskDetail(props.task.id)
  if (!res) return

  if (res.task) {
    apiTask.value = res.task as UploadTask
    if (!props.forceTab) {
      activeTab.value = defaultTab.value
    }
  }

  if (res.documents && res.documents.length > 0) {
    apiDocuments.value = res.documents
  }
  if (res.linkedDocuments) {
    apiLinkedDocuments.value = res.linkedDocuments
  }
  if (res.validationIssues) {
    apiValidationIssues.value = res.validationIssues
  }
  if (res.candidateDocuments && res.candidateDocuments.length > 0) {
    apiCandidateDocuments.value = res.candidateDocuments
  }
  if (res.reviewRecords) {
    apiReviewRecords.value = res.reviewRecords
  }
  if (res.reviewTimeline) {
    apiReviewTimeline.value = res.reviewTimeline
  }
  if (res.aiTip) {
    apiAiTip.value = res.aiTip
  }
  if (res.validation) {
    apiCanSubmit.value = res.validation.canSubmit
  }
}

onMounted(() => {
  activeTab.value = props.forceTab || defaultTab.value
  loadTaskDetail()
})

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

function getDocStatusColor(status: string) {
  switch (status) {
    case '已关联': return '#69e36f'
    case '已上传': return '#69e36f'
    case '缺失': return '#ff4f5e'
    case '格式异常': return '#ffb347'
    case '待上传': return '#2f9cff'
    case '审核通过': return '#69e36f'
    default: return '#8fa9c8'
  }
}

const completedCount = computed(() => {
  return displayDocuments.value.filter((d: any) => d.status === '已关联' || d.status === '审核通过').length
})

const missingCount = computed(() => {
  return displayDocuments.value.filter((d: any) => d.status === '缺失').length
})

const abnormalCount = computed(() => {
  return displayDocuments.value.filter((d: any) => d.status === '格式异常').length
})

const canSubmit = computed(() => {
  if (apiCanSubmit.value !== null) return apiCanSubmit.value
  return missingCount.value === 0 && abnormalCount.value === 0
})

function showSubmitMessage(message: string, type: 'success' | 'error' | 'info' = 'info') {
  submitMessage.value = message
  submitMessageType.value = type
}

function handleDownloadTemplate(docName: string) {
  showSubmitMessage(`模板下载为原型预留：${docName}｜适用任务：${currentTask.value.name}｜模板版本：V1.0。`, 'info')
}

function handleUpload(docName: string) {
  showSubmitMessage(`上传文件功能为原型预留：${docName}，后续接入真实文件上传服务。`, 'info')
}

function handleLink(docName: string) {
  showDocumentSelector.value = true
}

function handleView(docName: string) {
  showSubmitMessage(`文件查看功能为原型预留：${docName}。`, 'info')
}

async function handleConfirmLink() {
  const candidate = displayCandidateDocuments.value.find(c => c.id === selectedCandidate.value)
  if (!candidate) {
    showDocumentSelector.value = false
    return
  }

  const res = await linkTaskDocument(props.task.id, {
    documentId: candidate.documentId || candidate.id,
    requirementId: candidate.requirementId || undefined,
    matchScore: candidate.matchRate,
    source: 'MANUAL',
  })

  showDocumentSelector.value = false

  if (res && res.ok) {
    submitMessage.value = res.message || '已确认关联资料到当前任务'
    submitMessageType.value = 'success'
    await loadTaskDetail()
    emitWorkspaceRefresh({ source: 'task-modal', scopes: ['summary', 'tasks'], taskId: props.task.id })
  } else if (res && !res.ok) {
    submitMessage.value = res.message || '关联资料失败'
    submitMessageType.value = 'error'
  } else {
    submitMessage.value = '关联资料接口未响应，已保留当前展示数据'
    submitMessageType.value = 'error'
  }
}

function handleCancelLink() {
  showDocumentSelector.value = false
}

function handleLinkFromCenter() {
  showDocumentSelector.value = true
}

function handleUploadNew() {
  showSubmitMessage('上传新资料功能为原型预留，后续接入真实文件上传流程。', 'info')
}

async function handleSave() {
  const res = await saveTaskDraft(props.task.id)
  if (res && res.ok) {
    submitMessage.value = res.message || '已暂存'
    submitMessageType.value = 'success'
  } else if (res && !res.ok) {
    submitMessage.value = res.message || '暂存失败'
    submitMessageType.value = 'error'
  } else {
    submitMessage.value = '暂存接口未响应，已保留当前展示数据'
    submitMessageType.value = 'error'
  }
}

async function handleSubmit() {
  submitMessage.value = ''

  const res = await submitTaskReview(props.task.id)
  if (res && res.ok) {
    submitMessage.value = res.message || '已提交审核'
    submitMessageType.value = 'success'
    await loadTaskDetail()
    emitWorkspaceRefresh({ source: 'task-modal', scopes: ['summary', 'tasks', 'reviews'], taskId: props.task.id })
  } else if (res && !res.ok) {
    submitMessage.value = res.message || '提交审核失败'
    submitMessageType.value = 'error'
    if (res.validation) {
      apiCanSubmit.value = res.validation.canSubmit
    }
  } else {
    submitMessage.value = '提交审核接口未响应，已保留当前展示数据'
    submitMessageType.value = 'error'
  }
}

function handleClose() {
  emit('close')
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    handleClose()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

watch(() => props.task, () => {
  activeTab.value = props.forceTab || defaultTab.value
  apiDocuments.value = []
  apiLinkedDocuments.value = []
  apiValidationIssues.value = []
  apiCandidateDocuments.value = []
  apiReviewRecords.value = []
  apiReviewTimeline.value = []
  apiCanSubmit.value = null
  submitMessage.value = ''
  loadTaskDetail()
})
</script>

<template>
  <Teleport to="body">
    <div class="modal-overlay" @click="handleClose">
      <div class="task-modal" @click.stop>
        <div class="modal-header">
          <div class="modal-title">任务办理｜{{ currentTask.name }}</div>
          <button class="close-btn" @click="handleClose">
            <X :size="18" />
          </button>
        </div>

        <div class="modal-info-bar">
          <span class="info-tag" :style="{ background: `${getModuleColor(currentTask.module)}20`, color: getModuleColor(currentTask.module) }">
            {{ currentTask.module }} {{ currentTask.moduleName }}
          </span>
          <span class="info-tag" :style="{ background: `${getStatusColor(currentTask.status)}20`, color: getStatusColor(currentTask.status) }">
            {{ currentTask.status }}
          </span>
          <span class="info-text">资料周期 {{ currentTask.cycle }}</span>
          <span class="info-text">截止 {{ currentTask.deadline }}</span>
          <span class="info-tag highlight" v-if="currentTask.daysRemaining">剩余 {{ currentTask.daysRemaining }} 天</span>
          <span class="info-tag highlight" v-else-if="currentTask.daysOverdue">已逾期 {{ currentTask.daysOverdue }} 天</span>
          <span class="info-tag">完整度 {{ currentTask.progressCurrent }}/{{ currentTask.progressTotal }}</span>
        </div>

        <div class="modal-tabs">
          <button
            v-for="tab in taskTabs"
            :key="tab"
            :class="{ active: activeTab === tab }"
            @click="activeTab = tab"
          >
            {{ tab }}
          </button>
        </div>

        <div class="modal-body">
          <div class="main-content" v-if="activeTab === '资料要求'">
            <div class="left-panel">
              <div class="panel-header">
                <span class="panel-title">本任务需提交资料（{{ displayDocuments.length }}项）</span>
              </div>
              <div class="documents-table-wrapper">
                <table class="documents-table">
                  <thead>
                    <tr>
                      <th>资料名称</th>
                      <th>必填性</th>
                      <th>格式与要求</th>
                      <th>当前状态</th>
                      <th>模板</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="doc in displayDocuments" :key="doc.id">
                      <td class="doc-name">{{ doc.name }}</td>
                      <td>
                        <span :class="['required-tag', doc.required ? 'required' : 'optional']">
                          {{ doc.required ? '必填' : '选填' }}
                        </span>
                      </td>
                      <td>{{ doc.format }}</td>
                      <td>
                        <span class="doc-status-tag" :style="{ color: getDocStatusColor(doc.status) }">
                          {{ doc.status }}
                        </span>
                      </td>
                      <td>
                        <button v-if="doc.templateAvailable" class="template-btn" @click="handleDownloadTemplate(doc.name)">
                          <Download :size="14" />
                          下载模板
                        </button>
                        <span v-else class="no-template">无需模板</span>
                      </td>
                      <td>
                        <div class="action-btns">
                          <template v-if="doc.status === '已关联' || doc.status === '审核通过'">
                            <button class="action-btn view" @click="handleView(doc.name)">查看</button>
                          </template>
                          <template v-else>
                            <button v-if="doc.status === '缺失' || doc.status === '待上传'" class="action-btn upload" @click="handleUpload(doc.name)">上传新资料</button>
                            <button v-if="doc.status === '格式异常'" class="action-btn upload" @click="handleUpload(doc.name)">重新上传</button>
                            <button v-if="doc.status === '缺失' || doc.status === '格式异常' || doc.status === '待上传'" class="action-btn link" @click="handleLink(doc.name)">引用已有资料</button>
                          </template>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div class="right-panel">
              <div class="check-card">
                <div class="card-header">
                  <span class="card-title">完整性校验</span>
                  <span class="progress-text">{{ currentTask.progressCurrent }}/{{ currentTask.progressTotal }}</span>
                </div>
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: `${(currentTask.progressCurrent / currentTask.progressTotal) * 100}%` }"></div>
                </div>
                <div class="check-stats">
                  <span class="stat-item"><span class="stat-dot" style="background: #69e36f"></span>已满足 {{ completedCount }}</span>
                  <span class="stat-item"><span class="stat-dot" style="background: #ff4f5e"></span>缺失 {{ missingCount }}</span>
                  <span class="stat-item"><span class="stat-dot" style="background: #ffb347"></span>格式异常 {{ abnormalCount }}</span>
                </div>
              </div>

              <div class="ai-recommend-card">
                <div class="card-header">
                  <span class="card-title">AI 智能推荐</span>
                </div>
                <div class="recommend-content">
                  <div class="recommend-file">
                    <span class="file-name">弃渣场巡查记录_2026-07.pdf</span>
                    <span class="match-rate">匹配度：96%</span>
                  </div>
                  <p class="recommend-text">该资料已用于其他流程，无需重复上传</p>
                  <div class="recommend-buttons">
                    <button class="btn confirm-btn" @click="handleConfirmLink">确认关联</button>
                    <button class="btn view-btn" @click="handleView('弃渣场巡查记录_2026-07.pdf')">查看文件</button>
                  </div>
                </div>
              </div>

              <div class="ai-tip-card">
                <div class="tip-header">
                  <span class="tip-icon">AI</span>
                  <span class="tip-title">AI提示</span>
                </div>
                <p class="tip-content">{{ apiAiTip || '还缺少「审核确认单」，建议下载模板后补充签章。' }}</p>
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === '已关联资料'" class="tab-content">
            <div class="empty-state">
              <Upload :size="48" />
              <div class="empty-title">已关联资料列表</div>
              <div class="empty-desc">当前任务已关联 {{ apiLinkedDocuments.length || completedCount }} 项资料</div>
              <div class="linked-list" v-if="apiLinkedDocuments.length">
                <div v-for="doc in apiLinkedDocuments" :key="doc.relationId" class="linked-item">
                  <Check :size="16" class="check-icon" />
                  <span class="linked-name">{{ doc.documentName }}</span>
                  <span class="linked-meta">{{ doc.period }} · V{{ doc.version }}</span>
                </div>
              </div>
              <div class="linked-list" v-else>
                <div v-for="doc in displayDocuments.filter(d => d.status === '已关联')" :key="doc.id" class="linked-item">
                  <Check :size="16" class="check-icon" />
                  <span class="linked-name">{{ doc.name }}</span>
                </div>
              </div>
              <div class="submit-warning" v-if="!canSubmit">
                <AlertCircle :size="16" />
                <span>还有 {{ missingCount }} 项缺失，{{ abnormalCount }} 项格式异常，无法提交</span>
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === '校验问题'" class="tab-content">
            <div class="empty-state">
              <AlertCircle :size="48" class="alert-icon" />
              <div class="empty-title">校验问题</div>
              <div class="empty-desc">当前任务存在 {{ apiValidationIssues.length || missingCount + abnormalCount }} 项校验问题</div>
              <div class="issue-list" v-if="apiValidationIssues.length">
                <div v-for="issue in apiValidationIssues" :key="issue.id" class="issue-item">
                  <span class="issue-dot" :style="{ background: issue.issueType === '缺失' ? '#ff4f5e' : '#ffb347' }"></span>
                  <span class="issue-name">{{ issue.documentName }}</span>
                  <span class="issue-status">{{ issue.issueType }}</span>
                </div>
              </div>
              <div class="issue-list" v-else>
                <div v-for="doc in displayDocuments.filter(d => d.status === '缺失' || d.status === '格式异常')" :key="doc.id" class="issue-item">
                  <span class="issue-dot" :style="{ background: doc.status === '缺失' ? '#ff4f5e' : '#ffb347' }"></span>
                  <span class="issue-name">{{ doc.name }}</span>
                  <span class="issue-status">{{ doc.status }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="activeTab === '审核记录'" class="tab-content">
            <div class="empty-state">
              <AlertCircle :size="48" class="alert-icon" />
              <div class="empty-title">审核记录</div>
              <div class="empty-desc" v-if="apiReviewRecords.length">共 {{ apiReviewRecords.length }} 条审核记录</div>
              <div class="empty-desc" v-else>暂无审核记录</div>
              <div class="review-record-list" v-if="apiReviewRecords.length">
                <div v-for="record in apiReviewRecords" :key="record.id" class="review-record-item">
                  <div class="review-record-header">
                    <span class="review-record-status" :style="{ color: getStatusColor(record.status) }">{{ record.status }}</span>
                    <span class="review-record-time">{{ record.submitTime }}</span>
                  </div>
                  <div class="review-record-reviewer">审核人：{{ record.reviewer || '-' }}</div>
                  <div class="review-record-comment" v-if="record.commentSummary">{{ record.commentSummary }}</div>
                </div>
              </div>
              <div class="timeline-preview">
                <div v-for="(item, index) in displayReviewTimeline" :key="index" class="timeline-item">
                  <span class="timeline-time">{{ item.time }}</span>
                  <span class="timeline-action">{{ item.action }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <div v-if="submitMessage" :class="['submit-message', submitMessageType]">
            {{ submitMessage }}
          </div>
          <div class="flow-tips">
            <span class="tip-item"><span class="tip-number">1</span>查看要求</span>
            <span class="tip-arrow">→</span>
            <span class="tip-item"><span class="tip-number">2</span>关联/上传</span>
            <span class="tip-arrow">→</span>
            <span class="tip-item"><span class="tip-number">3</span>完整性校验</span>
            <span class="tip-arrow">→</span>
            <span class="tip-item"><span class="tip-number">4</span>提交</span>
          </div>
          <div class="footer-buttons">
            <button class="footer-btn" @click="handleLinkFromCenter">从资料中心关联</button>
            <button class="footer-btn" @click="handleUploadNew">上传新资料</button>
            <button class="footer-btn" @click="handleSave">暂存</button>
            <button class="footer-btn submit" :class="{ disabled: !canSubmit }" @click="handleSubmit">
              {{ currentTask.status === '待补正' ? '重新提交审核' : '提交审核' }}
            </button>
            <button class="footer-btn" @click="handleClose">关闭</button>
          </div>
        </div>

        <div v-if="showDocumentSelector" class="document-selector-overlay" @click="handleCancelLink">
          <div class="document-selector" @click.stop>
            <div class="selector-header">
              <span class="selector-title">关联已有资料</span>
              <button class="close-btn" @click="handleCancelLink">
                <X :size="16" />
              </button>
            </div>
            <div class="selector-content">
              <div class="candidate-list">
                <div
                  v-for="doc in displayCandidateDocuments"
                  :key="doc.id"
                  class="candidate-item"
                  :class="{ selected: selectedCandidate === doc.id }"
                  @click="selectedCandidate = doc.id"
                >
                  <input type="radio" :value="doc.id" v-model="selectedCandidate" name="document" />
                  <span class="candidate-name">{{ doc.name }}</span>
                  <span class="candidate-meta">{{ doc.cycle }} · {{ doc.unit }} · 已关联 {{ doc.linkCount }} 个流程</span>
                  <span class="match-rate">匹配度 {{ doc.matchRate }}%</span>
                </div>
              </div>
            </div>
            <div class="selector-footer">
              <button class="btn cancel" @click="handleCancelLink">取消</button>
              <button class="btn confirm" @click="handleConfirmLink">确认关联</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(2, 11, 24, 0.72);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: taskOverlayIn var(--duration-normal, 0.25s) var(--ease-out, cubic-bezier(0.16, 1, 0.3, 1));
}

@keyframes taskOverlayIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.task-modal {
  width: 66vw;
  max-height: 80vh;
  background: linear-gradient(180deg, #051a32 0%, #031020 100%);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 0 0 1px rgba(0, 174, 255, 0.3), 0 8px 32px rgba(0, 0, 0, 0.5);
  animation: taskPanelIn var(--duration-normal, 0.25s) var(--ease-out, cubic-bezier(0.16, 1, 0.3, 1));
}

@keyframes taskPanelIn {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(105, 227, 111, 0.1);
}

.modal-title {
  font-size: 16px;
  font-weight: 600;
  color: #e8f3ff;
}

.close-btn {
  width: 32px;
  height: 32px;
  background: rgba(105, 227, 111, 0.1);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 6px;
  color: #8fa9c8;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-info-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  background: rgba(0, 0, 0, 0.2);
  border-bottom: 1px solid rgba(105, 227, 111, 0.1);
  flex-wrap: wrap;
}

.info-tag {
  padding: 4px 12px;
  background: rgba(105, 227, 111, 0.1);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.info-tag.highlight {
  background: rgba(255, 79, 94, 0.15);
  color: #ff4f5e;
}

.info-text {
  font-size: 12px;
  color: #8fa9c8;
}

.modal-tabs {
  display: flex;
  gap: 4px;
  padding: 12px 24px;
  background: rgba(0, 0, 0, 0.2);
  border-bottom: 1px solid rgba(105, 227, 111, 0.1);
}

.modal-tabs button {
  padding: 8px 24px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  color: #8fa9c8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-tabs button.active {
  background: rgba(105, 227, 111, 0.15);
  border-color: rgba(105, 227, 111, 0.3);
  color: #69e36f;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}

.main-content {
  display: flex;
  gap: 20px;
}

.left-panel {
  flex: 1;
}

.panel-header {
  margin-bottom: 16px;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #e8f3ff;
}

.documents-table-wrapper {
  overflow-x: auto;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
}

.documents-table {
  width: 100%;
  border-collapse: collapse;
}

.documents-table th {
  text-align: left;
  padding: 10px 14px;
  font-size: 12px;
  color: #8fa9c8;
  font-weight: 500;
  border-bottom: 1px solid rgba(105, 227, 111, 0.1);
}

.documents-table td {
  padding: 12px 14px;
  font-size: 13px;
  color: #e8f3ff;
  border-bottom: 1px solid rgba(105, 227, 111, 0.05);
}

.doc-name {
  font-weight: 500;
}

.required-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.required-tag.required {
  background: rgba(255, 79, 94, 0.15);
  color: #ff4f5e;
}

.required-tag.optional {
  background: rgba(47, 156, 255, 0.15);
  color: #2f9cff;
}

.doc-status-tag {
  font-size: 12px;
  font-weight: 500;
}

.template-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: rgba(105, 227, 111, 0.1);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 4px;
  color: #69e36f;
  font-size: 11px;
  cursor: pointer;
}

.no-template {
  font-size: 11px;
  color: #5a7a9a;
}

.action-btns {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
}

.action-btn.view {
  background: rgba(105, 227, 111, 0.05);
  border: 1px solid rgba(105, 227, 111, 0.2);
  color: #8fa9c8;
}

.action-btn.upload {
  background: rgba(105, 227, 111, 0.1);
  border: 1px solid rgba(105, 227, 111, 0.3);
  color: #69e36f;
}

.action-btn.link {
  background: rgba(47, 156, 255, 0.1);
  border: 1px solid rgba(47, 156, 255, 0.3);
  color: #2f9cff;
}

.right-panel {
  width: 320px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.check-card, .ai-recommend-card, .ai-tip-card {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 8px;
  padding: 14px;
}

.check-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-title {
  font-size: 13px;
  font-weight: 600;
  color: #e8f3ff;
}

.progress-text {
  font-size: 12px;
  color: #69e36f;
}

.check-card .progress-bar {
  height: 8px;
  background: rgba(105, 227, 111, 0.1);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 12px;
}

.check-card .progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #69e36f, #2f9cff);
  border-radius: 4px;
}

.check-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #e8f3ff;
}

.stat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.recommend-content {
  margin-top: 12px;
}

.recommend-file {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.recommend-file .file-name {
  font-size: 12px;
  color: #e8f3ff;
}

.match-rate {
  font-size: 11px;
  color: #69e36f;
}

.recommend-text {
  font-size: 11px;
  color: #8fa9c8;
  margin: 0 0 12px 0;
}

.recommend-buttons {
  display: flex;
  gap: 10px;
}

.recommend-buttons .btn {
  flex: 1;
  padding: 8px;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
}

.recommend-buttons .confirm-btn {
  background: linear-gradient(135deg, #69e36f, #2f9cff);
  border: none;
  color: #031020;
  font-weight: 600;
}

.recommend-buttons .view-btn {
  background: rgba(105, 227, 111, 0.1);
  border: 1px solid rgba(105, 227, 111, 0.2);
  color: #8fa9c8;
}

.tip-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.tip-icon {
  padding: 2px 6px;
  background: linear-gradient(135deg, #69e36f, #2f9cff);
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  color: #031020;
}

.tip-title {
  font-size: 12px;
  color: #2f9cff;
  font-weight: 500;
}

.tip-content {
  font-size: 11px;
  color: #8fa9c8;
  margin: 0;
  line-height: 1.5;
}

.tab-content {
  padding: 40px;
}

.empty-state {
  text-align: center;
}

.empty-state .alert-icon {
  color: #ffb347;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 16px;
  font-weight: 600;
  color: #e8f3ff;
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 13px;
  color: #8fa9c8;
  margin-bottom: 20px;
}

.linked-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 400px;
  margin: 0 auto;
}

.linked-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: rgba(105, 227, 111, 0.1);
  border-radius: 6px;
}

.check-icon {
  color: #69e36f;
}

.linked-name {
  font-size: 13px;
  color: #e8f3ff;
}

.submit-warning {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: rgba(255, 79, 94, 0.1);
  border: 1px solid rgba(255, 79, 94, 0.2);
  border-radius: 8px;
  margin-top: 20px;
  font-size: 12px;
  color: #ff4f5e;
}

.issue-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 400px;
  margin: 0 auto;
}

.issue-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
}

.issue-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.issue-name {
  flex: 1;
  font-size: 13px;
  color: #e8f3ff;
}

.issue-status {
  font-size: 12px;
  color: #ff4f5e;
}

.timeline-preview {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 400px;
  margin: 0 auto;
  padding: 16px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
}

.timeline-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
}

.timeline-time {
  font-size: 11px;
  color: #5a7a9a;
}

.timeline-action {
  font-size: 12px;
  color: #e8f3ff;
}

.modal-footer {
  padding: 16px 24px;
  background: rgba(0, 0, 0, 0.3);
  border-top: 1px solid rgba(105, 227, 111, 0.1);
}

.flow-tips {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.tip-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #8fa9c8;
}

.tip-number {
  width: 18px;
  height: 18px;
  background: rgba(105, 227, 111, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: #69e36f;
}

.tip-arrow {
  color: #5a7a9a;
  font-size: 12px;
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.footer-btn {
  padding: 10px 20px;
  background: rgba(105, 227, 111, 0.1);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 6px;
  color: #8fa9c8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.footer-btn:hover {
  background: rgba(105, 227, 111, 0.15);
}

.footer-btn:active:not(.disabled) {
  transform: scale(0.97);
  transition-duration: 0.08s;
}

.footer-btn.submit {
  background: linear-gradient(135deg, #69e36f, #2f9cff);
  border: none;
  color: #031020;
  font-weight: 600;
}

.footer-btn.submit.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.document-selector-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
}

.document-selector {
  width: 500px;
  background: rgba(5, 26, 50, 0.95);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 10px;
  overflow: hidden;
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(105, 227, 111, 0.1);
}

.selector-title {
  font-size: 14px;
  font-weight: 600;
  color: #e8f3ff;
}

.selector-content {
  padding: 16px;
  max-height: 300px;
  overflow-y: auto;
}

.candidate-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.candidate-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
}

.candidate-item input {
  width: 16px;
  height: 16px;
}

.candidate-name {
  flex: 1;
  font-size: 13px;
  color: #e8f3ff;
}

.candidate-meta {
  font-size: 11px;
  color: #5a7a9a;
}

.candidate-item .match-rate {
  font-size: 11px;
  color: #69e36f;
}

.selector-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 16px;
  border-top: 1px solid rgba(105, 227, 111, 0.1);
}

.selector-footer .btn {
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
}

.selector-footer .cancel {
  background: rgba(105, 227, 111, 0.1);
  border: 1px solid rgba(105, 227, 111, 0.2);
  color: #8fa9c8;
}

.selector-footer .confirm {
  background: linear-gradient(135deg, #69e36f, #2f9cff);
  border: none;
  color: #031020;
  font-weight: 600;
}

.submit-message {
  padding: 8px 14px;
  border-radius: 6px;
  font-size: 12px;
  margin-bottom: 12px;
  text-align: center;
}

.submit-message.success {
  background: rgba(105, 227, 111, 0.1);
  border: 1px solid rgba(105, 227, 111, 0.3);
  color: #69e36f;
}

.submit-message.error {
  background: rgba(255, 79, 94, 0.1);
  border: 1px solid rgba(255, 79, 94, 0.3);
  color: #ff4f5e;
}

.submit-message.info {
  background: rgba(47, 156, 255, 0.1);
  border: 1px solid rgba(47, 156, 255, 0.3);
  color: #9fc7ff;
}

.linked-meta {
  font-size: 11px;
  color: #5a7a9a;
  margin-left: auto;
}

.review-record-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 500px;
  margin: 0 auto 20px;
}

.review-record-item {
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  text-align: left;
}

.review-record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.review-record-status {
  font-size: 12px;
  font-weight: 600;
}

.review-record-time {
  font-size: 11px;
  color: #5a7a9a;
}

.review-record-reviewer {
  font-size: 12px;
  color: #8fa9c8;
  margin-bottom: 4px;
}

.review-record-comment {
  font-size: 12px;
  color: #e8f3ff;
  line-height: 1.5;
}
</style>
