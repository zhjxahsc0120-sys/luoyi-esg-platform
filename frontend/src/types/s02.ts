export interface S02SpatialLink {
  featureId: string
  geometryType: string
  role: string
  isPrimary: boolean
}

/** V1.0：重大风险源 / 危大工程 / 一般风险源 */
export type S02BusinessCategory = 'MAJOR_SOURCE' | 'HAZARDOUS_ENG' | 'GENERAL'

export type S02CategoryFilter = 'ALL' | S02BusinessCategory

/** 重点对象 = 重大风险源；全部对象 = 全量 */
export type S02ObjectScope = 'key' | 'all'

export type S02PanelLayer = 'overview' | 'detail'

export interface S02RiskOverview {
  total: number
  major: number
  larger: number
  newThisMonth: number
  cancelledThisMonth: number
  locationCount: number
  /** V1.0 */
  majorSourceCount?: number
  hazardousEngCount?: number
  generalCount?: number
}

export interface S02RiskItem {
  id: number
  businessCode: string
  title: string
  riskLevel: string
  riskType: string
  locationText: string
  status: string
  controlStartDate: string | null
  controlMeasure: string
  canLocate: boolean
  spatialLinks: S02SpatialLink[]
  /** V1.0 display */
  businessCategory?: S02BusinessCategory
  businessCategoryLabel?: string
  sectionCode?: string | null
  description?: string
  specialPlanName?: string | null
  specialPlanStatus?: string | null
  approvalStatus?: string | null
  responsibleOrgName?: string | null
}

export interface S02HistoryItem {
  fromStatus: string | null
  toStatus: string
  actionCode: string | null
  actionAt: string | null
  operatorName: string
  operatorOrgName: string
  comment: string
  transitionResult: string
}

export interface S02PartyItem {
  role: string
  roleLabel: string
  orgName: string
  userName: string
}

export interface S02EvidenceItem {
  role: string
  roleLabel: string
  kind: string
  title: string
  description: string
  validityStatus: string
  createdAt: string | null
}

export interface S02RiskDetail {
  id: number
  businessCode: string
  title: string
  riskLevel: string
  riskType: string
  locationText: string
  status: string
  controlStartDate: string | null
  cancelledDate: string | null
  controlMeasure: string
  canLocate: boolean
  spatialLinks: S02SpatialLink[]
  sourceTable: string
  responsibleOrgName?: string
  confirmOrgName?: string
  confirmStatus?: string
  reviewCycle?: string
  description?: string
  specialPlanName?: string | null
  specialPlanStatus?: string | null
  approvalStatus?: string | null
  businessCategory?: S02BusinessCategory
  businessCategoryLabel?: string
  sectionCode?: string | null
  parties?: S02PartyItem[]
  history?: S02HistoryItem[]
  evidence?: S02EvidenceItem[]
}

export interface S02RisksPayload {
  overview: S02RiskOverview
  risks: S02RiskItem[]
  spatialLinks: S02SpatialLink[]
  scope: string
  isDemo?: boolean
}
