export interface E02SpatialLink {
  featureId: string
  geometryType: string
  role: string
  isPrimary: boolean
}

/** V1.0 业务分类：环境污染 / 水保问题 / 生态问题 / 其他 */
export type E02BusinessCategory = 'POLLUTION' | 'WATER_CONS' | 'ECOLOGY' | 'OTHER'

export type E02CategoryFilter = 'ALL' | E02BusinessCategory

/** 重点对象 = 未闭环问题；全部对象 = 含已闭环 */
export type E02ObjectScope = 'key' | 'all'

export type E02PanelLayer = 'overview' | 'detail'

/** 整改状态口径 */
export type E02RectifyStatus = '待整改' | '整改中' | '待复查' | '已闭环'

export interface E02IssueOverview {
  total: number
  rectifying: number
  pendingReview: number
  pendingClosure: number
  overdueAmong: number
  /** V1.0 展示用 */
  openCount?: number
  closedCount?: number
  byCategory?: Record<E02BusinessCategory, number>
}

export interface E02IssueItem {
  id: number
  businessCode: string
  title: string
  issueType: string
  locationText: string
  status: string
  statusGroup: 'rectifying' | 'pendingReview' | 'pendingClosure' | 'terminal'
  overdue: boolean
  deadline: string | null
  responsibleOrgName: string
  canLocate: boolean
  spatialLinks: E02SpatialLink[]
  /** V1.0 display */
  businessCategory?: E02BusinessCategory
  businessCategoryLabel?: string
  foundDate?: string | null
  description?: string
  /** 整改完成时间：仅使用客户端/接口回报字段，不前端推算 */
  closedDate?: string | null
}

export interface E02HistoryItem {
  fromStatus: string | null
  toStatus: string
  actionCode: string | null
  actionAt: string | null
  operatorName: string
  operatorOrgName: string
  comment: string
  transitionResult: string
}

export interface E02PartyItem {
  role: string
  roleLabel: string
  orgName: string
  userName: string
}

export interface E02EvidenceItem {
  role: string
  roleLabel: string
  kind: string
  title: string
  description: string
  validityStatus: string
  createdAt: string | null
}

export interface E02MaterialCompleteness {
  requiredRoles: string[]
  coveredRoles: string[]
  pendingRoles: string[]
  ratio: string
  notes: string[]
}

export interface E02CaseInfo {
  caseId: number | null
  caseCode: string | null
  caseStatus: string | null
  caseStatusGroup: string | null
  openedAt: string | null
  closedAt: string | null
}

export interface E02IssueDetail {
  id: number
  businessCode: string
  title: string
  issueType: string
  locationText: string
  status: string
  statusGroup: string
  overdue: boolean
  deadline: string | null
  responsibleOrgName: string
  foundDate: string | null
  closedDate: string | null
  isDemo: boolean
  dataNature: string
  description?: string
  businessCategory?: E02BusinessCategory
  businessCategoryLabel?: string
  case: E02CaseInfo | null
  history: E02HistoryItem[]
  parties: E02PartyItem[]
  evidence: E02EvidenceItem[]
  materialCompleteness: E02MaterialCompleteness
  spatialLinks: E02SpatialLink[]
}

export interface E02IssuesPayload {
  overview: E02IssueOverview
  issues: E02IssueItem[]
  spatialLinks: E02SpatialLink[]
  scope: string
  isDemo: boolean
}

/** @deprecated Phase B 水保对象域；V1.0 E03 接管水保对象展示 */
export type E02ObjectType = 'SPOIL' | 'TEMP_LAND' | 'TOPSOIL' | 'SLOPE'

/** @deprecated */
export interface E02ObjectOverview {
  objectCount: number
  riskCount: number
  completionRate: number
  restoreNormalCount: number
  byType: Record<E02ObjectType, number>
}

/** @deprecated */
export interface E02ObjectItem {
  id: number
  objectCode: string
  objectName: string
  objectType: E02ObjectType
  objectTypeLabel: string
  locationText: string
  sectionCode?: string | null
  riskLevel: string
  riskStatus: string
  restoreStatus: string
  measureStatus: string
  completionRate: number
  responsibleUnit: string
  canLocate: boolean
  spatialLinks: E02SpatialLink[]
  updateTime: string | null
}

/** @deprecated */
export interface E02ObjectDetail extends E02ObjectItem {
  measureRequirement: string
  rectificationStatus: string
  spaceDesc: string
}

/** @deprecated */
export interface E02ObjectsPayload {
  overview: E02ObjectOverview
  objects: E02ObjectItem[]
  scope: string
  isDemo: boolean
}
