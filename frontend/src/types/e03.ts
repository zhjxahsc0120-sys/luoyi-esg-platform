export interface E03SpatialLink {
  featureId: string
  geometryType: string
  role: string
  isPrimary: boolean
}

export interface E03IssueOverview {
  total: number
  rectifying: number
  pendingReview: number
  pendingClosure: number
  overdueAmong: number
}

export interface E03IssueItem {
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
  spatialLinks: E03SpatialLink[]
}

export interface E03HistoryItem {
  fromStatus: string | null
  toStatus: string
  actionCode: string | null
  actionAt: string | null
  operatorName: string
  operatorOrgName: string
  comment: string
  transitionResult: string
}

export interface E03PartyItem {
  role: string
  roleLabel: string
  orgName: string
  userName: string
}

export interface E03EvidenceItem {
  role: string
  roleLabel: string
  kind: string
  title: string
  description: string
  validityStatus: string
  createdAt: string | null
  rectificationRoundId: number | null
  documentId?: number | string | null
  hasAttachment?: boolean
}

export interface E03MaterialCompleteness {
  requiredRoles: string[]
  coveredRoles: string[]
  pendingRoles: string[]
  ratio: string
  notes: string[]
}

export interface E03CaseInfo {
  caseId: number | null
  caseCode: string | null
  caseStatus: string | null
  caseStatusGroup: string | null
  openedAt: string | null
  closedAt: string | null
}

export interface E03IssueDetail {
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
  description: string
  discoveryBasis: string
  case: E03CaseInfo | null
  history: E03HistoryItem[]
  parties: E03PartyItem[]
  evidence: E03EvidenceItem[]
  materialCompleteness: E03MaterialCompleteness
  spatialLinks: E03SpatialLink[]
  reconcileWarning: string | null
  gisDisclaimer: string | null
}

export interface E03IssuesPayload {
  overview: E03IssueOverview
  issues: E03IssueItem[]
  spatialLinks: E03SpatialLink[]
  scope: string
  isDemo: boolean
}

/** @deprecated Phase B 主路径改为生态对象域筛选 */
export type E03IssueCategoryFilter = 'ALL' | 'RECTIFYING' | 'PENDING_REVIEW' | 'PENDING_CLOSURE'

export type E03EcoObjectKind = 'SENSITIVE' | 'PROTECTED'

export type E03CategoryFilter = 'ALL' | E03EcoObjectKind

export type E03PanelLayer = 'overview' | 'detail'

export interface E03EcoOverview {
  areaCount: number
  protectedCount: number
  riskCount: number
  riskStatus: string
}

export interface E03EcoObjectItem {
  id: number
  objectCode: string
  objectName: string
  objectKind: E03EcoObjectKind
  objectKindLabel: string
  locationText: string
  sectionCode?: string | null
  riskLevel: string
  riskStatus: string
  protectionRequirement: string
  responsibleUnit: string
  relatedMatter: string
  canLocate: boolean
  spatialLinks: E03SpatialLink[]
  updateTime: string | null
}

export interface E03EcoObjectDetail extends E03EcoObjectItem {}

export interface E03EcoObjectsPayload {
  overview: E03EcoOverview
  objects: E03EcoObjectItem[]
  scope: string
  isDemo: boolean
}
