export type NavItem = {
  key: string
  label: string
  active?: boolean
}

export type KpiKey =
  | 'E01' | 'E02' | 'E03' | 'E04'
  | 'S01' | 'S02' | 'S03' | 'S04'
  | 'G01' | 'G02' | 'G03' | 'G04'

export type KpiTheme = 'green' | 'blue' | 'purple'

export type KpiItem = {
  key: KpiKey
  label: string
  fullName: string
  value: string | number
  unit?: string
  /** 首页主数字旁的简要口径提示（如达标率） */
  hint?: string
  /** 优先展示文案（如「待评价」），避免无意义「0家」 */
  displayText?: string
  // E04 P2 扩展（demo 闸 / 边界版本 / 批次）
  dataNature?: string
  isDemo?: boolean
  scope?: 'demo' | 'formal'
  formalValue?: number | null
  demoValue?: number | null
  boundaryVersion?: string | null
  accountingBatchId?: number | null
  statisticsAsOf?: string | null
  statisticsStart?: string | null
  diffHint?: string | null
  confirmationStatus?: string | null
  ledgerStatus?: string | null
}

export type KpiGroup = {
  key: 'E' | 'S' | 'G'
  title: string
  theme: KpiTheme
  status: string
  items: KpiItem[]
}

export type RoutePointType = 'compliance' | 'carbon' | 'risk' | 'sensitive' | 'station'

export type RoutePoint = {
  id: string
  name: string
  x: number
  y: number
  type: RoutePointType
}

export type RouteSegment = {
  id: string
  name: string
  points: [number, number][]
  status: 'normal' | 'warning' | 'risk'
}

export type SensitiveArea = {
  id: string
  name: string
  polygon: [number, number][]
}

export type ComplianceMetric = {
  label: string
  value: number | string
  unit: string
  tone?: 'red' | 'yellow' | 'blue' | 'neutral'
}

export type EffectivenessItem = {
  label: string
  value: number
}

export type WarningListItem = {
  level: '红' | '黄' | '蓝'
  title: string
  source: 'E' | 'S' | 'G'
  status: string
  updatedAt: string
  /** Demo contract navigation — never guess from objectName */
  kpiKey?: string
  objectId?: number | null
  objectName?: string
  responsibleUnit?: string
  domain?: string
  reason?: string
  contractLevel?: string
}

export type CarbonSource = {
  name: string
  value: number
  color?: string
}

export type ReductionMeasure = {
  name: string
  level: string
}

export type MonthlyMaterial = {
  name: string
  owner: string
  deadline: string
}

export type MonthlyReport = {
  month: string
  progress: number
  pendingCount: number
  confirmCount: number
  currentStatus?: string
  expectedCompletion?: string
  materials: MonthlyMaterial[]
}

export type TimelineStep = {
  index: number
  label: string
  active?: boolean
  completed?: boolean
}

export interface KpiModalFocusContext {
  sourceTable?: string
  sourceId?: string
  gisFeatureId?: string
  from?: 'gis' | 'dashboard' | 'workspace'
  title?: string
}

// ── 弹窗详情类型 ──

export type KpiDetailSummaryItem = {
  label: string
  value: string | number
  unit?: string
  icon?: string
  extra?: string
}

export type KpiDetailBottomItem = {
  [key: string]: string | number | boolean | null | undefined | KpiDetailBottomItem[]
}

export type E02MainStatus = '整改中' | '待复查' | '待销项'
export type E02DeadlineStatus = '已逾期' | '正常'

export type E02DetailRow = KpiDetailBottomItem & {
  id: string
  rawId: number
  category: string
  name: string
  time: string
  level: string
  department: string
  deadline: string
  mainStatus: E02MainStatus
  overdue: boolean
  deadlineStatus: E02DeadlineStatus
  status?: string
}

export type E03DeadlineStatus = '已逾期' | '正常'
export type E03MainStatus = '未闭环' | '待整改' | '整改中'

export type E03DetailRow = KpiDetailBottomItem & {
  id: number
  name: string
  segment: string
  category: string
  time: string
  department: string
  deadline: string
  mainStatus: E03MainStatus
  overdue: boolean
  deadlineStatus: E03DeadlineStatus
  statusStageKnown: boolean
}

export type E04MonthlyEmission = {
  period: string
  monthlyEmission: number
  cumulativeEmission: number
}

export type E04MaterialDetail = KpiDetailBottomItem & {
  material: string
  activityValue: number
  activityUnit: string
  emissionFactor: number
  factorUnit: string
  emission: number
  factorName: string
  factorVersion: string
  factorSource: string
  factorSnapshotId?: number | null
  factorSnapshotCode?: string | null
  dataNature: string
  verificationStatus: string
  effectiveStatus?: string
  evidenceStatus: string
  monthlyData?: { period: string; activityValue: number; emission: number }[]
}

export type E04SourceDetail = KpiDetailBottomItem & {
  sourceCode: 'diesel' | 'electricity' | 'material' | 'transport'
  source: string
  inBoundary?: boolean
  activityValue: number
  activityUnit: string
  emissionFactor: number | null
  factorUnit: string
  factorName: string
  factorSnapshotId?: number | null
  factorSnapshotCode?: string | null
  emission: number
  share: number
  factorVersion: string
  factorSource: string
  dataNature: string
  verificationStatus: string
  effectiveStatus?: string
  evidenceStatus: string
  materialDetails?: E04MaterialDetail[]
}

export type E04CandidateBoundaryContrast = {
  boundaryVersion: string
  boundaryStatus: string
  estimatedValue: number
  description: string
  excludedSources: { sourceCode: string; sourceLabel: string; inBoundary: boolean }[]
  isKpi: false
}

export type TopicTab = {
  key: string
  label: string
}

export type KpiDetailConfig = {
  key: KpiKey | string
  fullName: string
  theme: KpiTheme
  summary: KpiDetailSummaryItem[]
  chartTitle: string
  detailTitle: string
  detailColumns: { key: string; label: string; width?: string }[]
  detailData: KpiDetailBottomItem[]
  dataSource: string
  updateTime: string
  updateFrequency: string
  completeness: string
  completenessStatus: 'complete' | 'incomplete' | 'pending' | 'empty'
  isMock: boolean
  detailReserved?: boolean
  canSupervise?: boolean
  isTopic?: boolean
  tabs?: TopicTab[]
  topicData?: Record<string, any>
  categoryData?: { name: string; value: number }[]
  statusData?: { name: string; value: number }[]
  statisticsAsOf?: string
  statisticsStart?: string
  monthlyData?: E04MonthlyEmission[]
  materialDetails?: E04MaterialDetail[]
  accountingBoundary?: string[]
  demoNotice?: string
  dataNature?: string
  // E04 P2 扩展字段
  boundaryVersion?: string | null
  accountingBatchId?: number | null
  scope?: 'demo' | 'formal'
  isDemo?: boolean
  verificationStatus?: string
  diffHint?: string | null
  candidateBoundaryContrast?: E04CandidateBoundaryContrast | null
  // P3.3 异常态扩展字段
  loadError?: boolean
  demoDenied?: boolean
  monthlyGaps?: string[]
}
