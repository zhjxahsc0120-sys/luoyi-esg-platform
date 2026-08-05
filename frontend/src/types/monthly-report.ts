export type MonthlyReadinessStatus =
  | '待提交'
  | '待确认'
  | '待补正'
  | '校验通过'
  | '不适用（已确认）'

export type MonthlyReadinessTask = {
  taskCode: string
  taskName: string
  responsibleUnit: string
  deadline: string
  monthlyStatus: MonthlyReadinessStatus
}

export type MonthlyReadiness = {
  metricName: string
  reportPeriod: string
  numerator: number
  denominator: number
  exactProgress: number
  progress: number
  deadlineStart: string
  deadlineEnd: string
  statusCounts: Record<MonthlyReadinessStatus, number>
  exceptionTasks: MonthlyReadinessTask[]
}

// ===== Codex 已完成的新版月报概览接口契约 =====

export type MonthlyTaskStatus = '待提交' | '待确认' | '待补正' | '校验通过' | '不适用'

export type MonthlyTaskTypeCode = 'MONTHLY_FIXED' | 'CONDITIONAL' | 'PERIODIC_REFERENCE'

export type MonthlyNextActionType =
  | 'SUBMIT_MATERIAL'
  | 'CONFIRM_RESPONSIBILITY'
  | 'CORRECT_MATERIAL'
  | 'VIEW_RESULT'

export type MonthlyProcessStageStatus = 'IN_PROGRESS' | 'PENDING' | 'NOT_STARTED' | 'COMPLETED'

export type MonthlyMaterialChainStatus = 'LINKED' | 'UNLINKED'

export type MonthlyMaterialChain = {
  sourceTaskId: string | null
  linkedDocumentIds: number[]
  manualEvidenceOnly: boolean
  status: MonthlyMaterialChainStatus
}

export type MonthlyTaskInstance = {
  id: string
  taskCode: string
  taskName: string
  groupCode: 'E' | 'S' | 'G'
  taskType: MonthlyTaskTypeCode
  taskTypeLabel: '固定月度' | '条件触发' | '周期引用'
  responsibleDepartment: string | null
  responsibleRole: string | null
  responsibleUserId: string | number | null
  responsibleUserName: string | null
  status: MonthlyTaskStatus
  deadline: string | null
  requiredMaterialCount: number
  linkedMaterialCount: number
  validationResult: MonthlyTaskStatus
  affectsReport: boolean
  nextActionType: MonthlyNextActionType
  materialChain: MonthlyMaterialChain
  issueDescription: string | null
  correctionRequirement: string | null
  dataNature: string
  updatedAt: string | null
  linkedMaterialNames: string[] | null
  lastValidationAt: string | null
}

export type MonthlyPendingTask = {
  id: string
  taskCode: string
  taskName: string
  groupCode: 'E' | 'S' | 'G'
  status: MonthlyTaskStatus
  issueDescription: string | null
  requirement: string | null
  deadline: string | null
  responsibleRole: string | null
  nextActionType: MonthlyNextActionType
  materialChain: MonthlyMaterialChain
}

export type MonthlyReportSummary = {
  collectedCount: number
  totalCount: number
  pendingSubmitCount: number
  pendingConfirmCount: number
  pendingCorrectionCount: number
  pendingTotal: number
  notApplicableCount: number
}

export type MonthlyStatusCount = {
  status: MonthlyTaskStatus
  count: number
}

export type MonthlyTaskTypeCount = {
  taskType: MonthlyTaskTypeCode
  label: '固定月度' | '条件触发' | '周期引用'
  count: number
}

export type MonthlyGroupProgress = {
  groupCode: 'E' | 'S' | 'G'
  collectedCount: number
  totalCount: number
  progress: number
}

export type MonthlyProcessStage = {
  key: 'collection' | 'validation' | 'confirmation' | 'generation' | 'finalization'
  label: '资料归集' | '完整性校验' | '责任确认' | '月报生成' | '审核定稿'
  status: MonthlyProcessStageStatus
  detail: string
}

export type MonthlyOutputStatus = {
  status: 'NOT_CREATED' | 'DRAFT' | 'FINALIZED'
  label: string
  hasOutputRecord: boolean
  outputCount: number
}

export type MonthlyReportOverview = {
  reportMonth: string
  summary: MonthlyReportSummary
  readinessRate: number
  exactReadinessRate: number
  deadlineRange: { start: string; end: string }
  statusCounts: MonthlyStatusCount[]
  taskTypeCounts: MonthlyTaskTypeCount[]
  groupProgress: MonthlyGroupProgress[]
  processStages: MonthlyProcessStage[]
  taskInstances: MonthlyTaskInstance[]
  pendingTasks: MonthlyPendingTask[]
  outputStatus: MonthlyOutputStatus
  sourceMode: 'mysql' | 'snapshot' | 'mock'
  isMock: boolean
  dataNature: string
  updatedAt: string | null
}
