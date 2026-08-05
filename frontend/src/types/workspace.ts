export type EsgModule = 'E' | 'S' | 'G'

export type TaskStatus =
  | '待上传'
  | '待补正'
  | '待提交'
  | '审核中'
  | '审核退回'
  | '已通过'
  | '已退回'
  | '已归档'
  | '已完成'

export type TaskSourceType =
  | 'KPI指标'
  | '月报任务'
  | '业务事项'
  | '周期任务'
  | '审核补正'
  | '临时任务'

export type ReviewStatus = '待审核' | '已通过' | '已退回' | '已归档'

export type ParseStatus =
  | '解析中'
  | '待确认'
  | '疑似重复'
  | '解析失败'
  | '已入库'

export type DocumentValidityStatus = '有效' | '即将失效' | '已失效'

export type DocumentSourceType =
  | '智能入库'
  | '任务上传'
  | '审核归档'
  | '系统生成'
  | '历史迁移'

export interface StatusCard {
  label: string
  value: number
  unit?: string
  subText?: string
  subText2?: string
  color: string
}

export interface RelatedKpi {
  code: string
  name: string
  module: EsgModule
}

export interface UploadTask {
  id: string
  name: string
  module: EsgModule
  moduleName: string
  deadline: string
  deadlineDisplay: string
  progressCurrent: number
  progressTotal: number
  status: TaskStatus
  nextStep: string
  daysOverdue?: number
  daysRemaining?: number
  hoursRemaining?: number
  cycle?: string
  cycleType?: '月度' | '季度' | '年度' | '一次性'
  assignee?: string
  assigneeDept?: string
  sourceType?: TaskSourceType
  sourceName?: string
  sourceKpiCode?: string
  sourceKpiName?: string
  relatedReport?: string
  isOverdue?: boolean
  isUrgent?: boolean
}

export interface DocumentRelatedTask {
  module: EsgModule
  name: string
  cycle: string
  status: string
  referenceCount: number
  lastReference: string
  type: 'KPI指标' | '月报' | '业务事项' | '上传任务'
}

export interface DocumentVersion {
  version: string
  uploader: string
  uploadTime: string
  changeDesc: string
  reviewStatus: string
  isCurrent: boolean
}

export interface Document {
  id: string
  name: string
  type: string
  module?: string
  cycle: string
  version: string
  source: DocumentSourceType
  relatedTaskCount: number
  status: DocumentValidityStatus
  size?: string
  uploadTime?: string
  creator?: string
  format?: string
  pages?: number
  tags?: string[]
  isUnique?: boolean
  relatedTasks?: DocumentRelatedTask[]
  versions?: DocumentVersion[]
  fileHash?: string
  validPeriod?: string
  responsibilityUnit?: string
}

export interface ParseQueueItem {
  id: string
  jobId?: number
  fileId?: number
  fileName: string
  size: string
  progress: number
  status: ParseStatus | string
  uploadTime?: string
  fileHash?: string
}

export interface DuplicateFileInfo {
  id: string
  fileName: string
  fileHash: string
  fileSize: string
  cycle: string
  uploadTime: string
  relatedTasks: string[]
  similarity: number
}

export interface AiParseResult {
  documentType: string
  cycle: string
  module: EsgModule
  moduleName: string
  responsibilityUnit: string
  projectSection?: string
  engineeringObject?: string
  validPeriod: string
  suggestedTask: string
  suggestedKpiCode: string
  suggestedKpiName: string
  suggestedReport: string
  confidence: number
  duplicateCount: number
  duplicateTip: string
}

export interface SuggestedTask {
  id: string
  documentName: string
  taskName: string
  module: EsgModule
  moduleName: string
  matchRate: number
  reuseCount: number
  confirmStatus: string
  matchBasis?: string
}

export interface ReviewRecord {
  id: string
  taskId?: string
  taskName: string
  module: EsgModule
  moduleName: string
  submitTime: string
  status: ReviewStatus
  reviewer: string
  commentSummary: string
  nextStep: string
  sourceType?: TaskSourceType
  sourceName?: string
  correctionDueDate?: string
  correctionRemaining?: string
  correctionOverdue?: boolean
}

export interface ReviewTimeline {
  time: string
  action: string
}

export interface ReviewRequirement {
  id: string
  requirement: string
  status?: string
}

export interface TaskDocument {
  id: string
  name: string
  required: boolean
  format: string
  status: '已关联' | '缺失' | '格式异常' | '待上传' | '审核通过'
  templateAvailable: boolean
}

export interface TodayFocus {
  id: string
  name: string
  type: 'remaining' | 'overdue' | 'urgent' | 'today'
  value: string
  status?: string
}

export interface QuickQuestion {
  id: string
  question: string
}

export const TASK_STATUS_COLORS: Record<string, string> = {
  '待上传': '#2f9cff',
  '待补正': '#ffb347',
  '待提交': '#a66cff',
  '审核中': '#a66cff',
  '审核退回': '#ff4f5e',
  '已通过': '#69e36f',
  '已退回': '#ff4f5e',
  '已归档': '#69e36f',
  '已完成': '#69e36f',
  '已逾期': '#ff4f5e',
  '即将到期': '#ffb347',
}

export const REVIEW_STATUS_COLORS: Record<string, string> = {
  '待审核': '#2f9cff',
  '已通过': '#69e36f',
  '已退回': '#ff4f5e',
  '已归档': '#69e36f',
}

export const MODULE_COLORS: Record<string, string> = {
  'E': '#69e36f',
  'S': '#2f9cff',
  'G': '#a66cff',
}

export const KPI_CODE_MAP: Record<string, { name: string; module: EsgModule }> = {
  'E01': { name: '环境监测超标项次', module: 'E' },
  'E02': { name: '当前未闭环环保问题事项数', module: 'E' },
  'E03': { name: '当前未闭环水土保持问题事项数', module: 'E' },
  'E04': { name: '文物保护管控', module: 'E' },
  'S01': { name: '连续安全生产天数', module: 'S' },
  'S02': { name: '当前在管较大及以上安全风险点数', module: 'S' },
  'S03': { name: '当前未办结劳务用工纠纷事项数', module: 'S' },
  'S04': { name: '当前未办结群众诉求事项数', module: 'S' },
  'G01': { name: '当前未完成法定报批报建事项数', module: 'G' },
  'G02': { name: '临期及逾期许可事项数', module: 'G' },
  'G03': { name: '当前未关闭检查整改事项数', module: 'G' },
  'G04': { name: '当前待补齐关键合规资料项数', module: 'G' },
}

export const STATUS_TO_NEXT_STEP: Record<string, string> = {
  '待上传': '开始办理',
  '待补正': '继续补正',
  '待提交': '提交',
  '审核中': '查看进度',
  '审核退回': '进入补正',
  '已通过': '查看结果',
  '已退回': '进入补正',
  '已归档': '查看归档资料',
  '已完成': '查看结果',
}
