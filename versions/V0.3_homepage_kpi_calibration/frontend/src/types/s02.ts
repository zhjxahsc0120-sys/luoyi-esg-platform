export interface S02SpatialLink {
  featureId: string
  geometryType: string
  role: string
  isPrimary: boolean
}

export interface S02RiskOverview {
  total: number
  major: number
  larger: number
  newThisMonth: number
  cancelledThisMonth: number
  locationCount: number
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
  parties?: S02PartyItem[]
  history?: S02HistoryItem[]
  evidence?: S02EvidenceItem[]
}

export interface S02RisksPayload {
  overview: S02RiskOverview
  risks: S02RiskItem[]
  spatialLinks: S02SpatialLink[]
  scope: string
}

export type S02CategoryFilter = 'ALL' | 'MAJOR' | 'LARGER'

export type S02PanelLayer = 'overview' | 'detail'
