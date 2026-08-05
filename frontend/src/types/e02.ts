export interface E02SpatialLink {
  featureId: string
  geometryType: string
  role: string
  isPrimary: boolean
}

export interface E02IssueOverview {
  total: number
  rectifying: number
  pendingReview: number
  pendingClosure: number
  overdueAmong: number
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

/** @deprecated Phase B 主路径改为水保对象类型筛选 */
export type E02IssueCategoryFilter = 'ALL' | 'RECTIFYING' | 'PENDING_REVIEW' | 'PENDING_CLOSURE'

/** Phase B：水保对象类型 */
export type E02ObjectType = 'SPOIL' | 'TEMP_LAND' | 'TOPSOIL' | 'SLOPE'

export type E02CategoryFilter = 'ALL' | E02ObjectType

export type E02PanelLayer = 'overview' | 'detail'

export interface E02ObjectOverview {
  objectCount: number
  riskCount: number
  completionRate: number
  restoreNormalCount: number
  byType: Record<E02ObjectType, number>
}

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

export interface E02ObjectDetail extends E02ObjectItem {
  measureRequirement: string
  rectificationStatus: string
  spaceDesc: string
}

export interface E02ObjectsPayload {
  overview: E02ObjectOverview
  objects: E02ObjectItem[]
  scope: string
  isDemo: boolean
}
