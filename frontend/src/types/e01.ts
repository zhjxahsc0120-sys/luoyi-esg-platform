export interface E01KpiStats {
  exceedItemCount: number
  eventCount: number
  pointCount: number
  openEventCount: number
}

export interface E01OverviewStats {
  totalOpenPoints: number
  waterCount: number
  airCount: number
  noiseCount: number
  /** Phase B 任务书：监测点数量 */
  monitorPointCount?: number
  /** Phase B 任务书：异常数量 */
  anomalyCount?: number
  /** Phase B 任务书：未闭环数量 */
  openCount?: number
  /** Phase B 任务书：当前风险等级 */
  riskLevel?: string
}

export interface E01NamedCount {
  name: string
  value: number
}

export interface E01FactorBrief {
  factorCode: string
  factorName: string
  detectedValue?: string | number | null
  limitValue?: string | number | null
  unit?: string | null
  exceedMultiple?: number | null
  resultId: number
  eventId: number
}

export interface E01OpenPoint {
  pointId: number
  pointCode: string
  pointName: string
  sectionCode?: string | null
  sectionName?: string | null
  locationText?: string | null
  monitorCategory: string
  monitorCategoryLabel: string
  status: string
  caseStatus?: string | null
  discoveredAt?: string | null
  longitude?: number | null
  latitude?: number | null
  gisFeatureId?: string | null
  canLocate: boolean
  primaryEventId: number
  eventIds: number[]
  factors: E01FactorBrief[]
}

export type E01CategoryFilter = 'ALL' | 'WATER' | 'AIR' | 'NOISE'

/** Business categories shown in E01 workbench (no "全部" chip). */
export type E01BusinessCategory = 'WATER' | 'AIR' | 'NOISE'

/** List/GIS scope: risk points only vs all monitor points from payload. */
export type E01PointScope = 'risk' | 'all'

export interface E01EventSummary {
  eventId: number
  eventCode: string
  title: string
  pointId: number
  pointCode: string
  pointName: string
  sectionCode?: string | null
  sectionName?: string | null
  chainage?: string | null
  locationText?: string | null
  engineeringObject?: string | null
  engineeringObjectCode?: string | null
  monitorCategory: string
  monitorCategoryLabel: string
  factorCode: string
  factorName: string
  detectedValue?: string | number | null
  limitValue?: string | number | null
  unit?: string | null
  exceedMultiple?: number | null
  status: string
  caseStatus?: string | null
  caseStatusLabel?: string | null
  retestOutcome?: string | null
  retestRound?: number
  isOpen: boolean
  discoveredAt?: string | null
  longitude?: number | null
  latitude?: number | null
  gisFeatureId?: string | null
  resultId: number
  resultCode: string
  sampleId: number
  caseId?: number | null
  caseCode?: string | null
  closedAt?: string | null
  standardName?: string | null
  currentNode?: string | null
  nextNode?: string | null
  responsibleOrg?: { code?: string | null; name?: string | null } | null
}

export interface E01MapPoint {
  pointId: number
  pointCode: string
  pointName: string
  longitude?: number | null
  latitude?: number | null
  gisFeatureId?: string | null
  openCount: number
  eventCount: number
  eventIds: number[]
  primaryStatus: string
  monitorCategory: string
}

export interface E01EventsPayload {
  kpi: E01KpiStats
  overview: E01OverviewStats
  byCategory: E01NamedCount[]
  byStatus: E01NamedCount[]
  events: E01EventSummary[]
  openPoints: E01OpenPoint[]
  mapPoints: E01MapPoint[]
  isDemo?: boolean
}

export interface E01FactorResult {
  resultId: number
  resultCode: string
  testStage: string
  factorCode: string
  factorName: string
  judgement?: string | null
  detectedValue?: string | number | null
  limitValue?: string | number | null
  unit?: string | null
  exceedMultiple?: number | null
  standardCode?: string | null
  standardName?: string | null
  standardVersion?: string | null
}

export interface E01RectificationRound {
  id: number
  roundNo: number
  startedAt?: string | null
  submittedAt?: string | null
  summary?: string | null
  reviewStatus?: string | null
}

export interface E01RetestRound {
  id: number
  roundNo: number
  outcome?: string | null
  reviewStatus?: string | null
  requestedAt?: string | null
  plannedSampleAt?: string | null
  actualSampleAt?: string | null
  reviewedAt?: string | null
  batchCode?: string | null
  reportNo?: string | null
  results: E01FactorResult[]
}

export interface E01StatusHistoryItem {
  sequenceNo: number
  fromStatus?: string | null
  fromStatusLabel?: string | null
  toStatus?: string | null
  toStatusLabel?: string | null
  actionCode?: string | null
  actionAt?: string | null
  operatorName?: string | null
  operatorOrgName?: string | null
  comment?: string | null
  transitionResult?: string | null
}

export interface E01EvidenceItem {
  id: number
  role?: string | null
  documentId?: number | null
  fileId?: number | null
  documentCode?: string | null
  documentName?: string | null
  validityStatus?: string | null
  verificationStatus?: string | null
  createdAt?: string | null
}

export interface E01EventDetail {
  summary: E01EventSummary
  initialFactors: E01FactorResult[]
  allSampleFactors: E01FactorResult[]
  rectificationRounds: E01RectificationRound[]
  retestRounds: E01RetestRound[]
  statusHistory: E01StatusHistoryItem[]
  evidence: E01EvidenceItem[]
  closure: {
    caseCode?: string | null
    status?: string | null
    statusLabel?: string | null
    closedAt?: string | null
    openedAt?: string | null
  }
}

export type E01PanelLayer = 'overview' | 'summary' | 'detail'

export interface E01TrendSeriesPoint {
  at?: string | null
  value?: string | number | null
  valueNum?: number | null
  limitValue?: string | number | null
  judgement?: string | null
  exceeded: boolean
  exceedMultiple?: number | null
  resultId: number
  sampleId: number
  testStage?: string | null
}

export interface E01TrendFactorOption {
  factorCode: string
  factorName: string
  unit?: string | null
  sampleCount: number
  exceedCount: number
}

export interface E01PointTrendPayload {
  point: {
    pointId: number
    pointCode: string
    pointName: string
    monitorCategory: string
    monitorCategoryLabel: string
    sectionCode?: string | null
    sectionName?: string | null
    locationText?: string | null
    status?: string | null
    discoveredAt?: string | null
    longitude?: number | null
    latitude?: number | null
    primaryEventId?: number
    factors?: E01FactorBrief[]
  }
  factor: {
    factorCode: string
    factorName: string
    unit?: string | null
    limitValue?: string | number | null
    limitValueNum?: number | null
    limitOperator?: string | null
    standardName?: string | null
  }
  series: E01TrendSeriesPoint[]
  companionSeries?: {
    factorCode: string
    factorName: string
    points: E01TrendSeriesPoint[]
  } | null
  stats: {
    sampleCount: number
    exceedCount: number
    latestValue?: string | number | null
    latestAt?: string | null
    latestExceeded: boolean
  }
  factorOptions: E01TrendFactorOption[]
}
