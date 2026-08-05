/**
 * ESG Demo API contract V0.1 types.
 * Source: esg_demo_api_contract_v0.1.md
 */

export type DemoRiskLevel = 'NORMAL' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | string

export type DemoKpiItem = {
  key: string
  name: string
  value: number | string
  unit: string
  hint: string
  riskLevel: DemoRiskLevel
}

export type DemoKpisResponse = {
  projectId?: number
  periodEnd?: string
  items?: DemoKpiItem[]
  /** Bridge for existing TopKpiGroups */
  groups?: import('@/types/dashboard').KpiGroup[]
  source?: string
}

export type DemoKpiObject = {
  objectType: string
  objectId: number | null
  objectName: string
  status?: string
  riskLevel?: DemoRiskLevel
  fields?: Record<string, unknown>
}

export type DemoKpiDetail = {
  key: string
  name: string
  fullName?: string
  value: number | string
  unit: string
  hint?: string
  riskLevel?: DemoRiskLevel
  trend?: Array<{ periodEnd: string; value: number | string }>
  summary?: Record<string, unknown> | Array<{ label: string; value: string | number; unit?: string }>
  objects?: DemoKpiObject[]
  /** E04 contract fields */
  objectCount?: number
  surveyStatus?: string
  measureRate?: number
  riskStatus?: string
  /** Modal bridges */
  summaryList?: Array<{ label: string; value: string | number; unit?: string }>
  summaryCards?: Array<{ label: string; value: string | number; unit?: string }>
  detailData?: Array<Record<string, unknown>>
  theme?: string
  dataSource?: string
  updateTime?: string
  isDemo?: boolean
  source?: string
  loadError?: boolean
}

export type DemoRiskWarning = {
  level: string
  domain: string
  kpiKey: string
  objectId: number | null
  objectName: string
  responsibleUnit: string
  status: string
  reason?: string
  triggerTime?: string
}

export type DemoRiskWarningsResponse = {
  items: DemoRiskWarning[]
  total: number
  page?: number
  pageSize?: string | number
  source?: string
}

export type DemoKpiObjectDetail = {
  kpiKey: string
  objectId: number
  objectType: string
  objectName: string
  responsibleUnit?: string
  status?: string
  riskLevel?: DemoRiskLevel
  fields?: Record<string, unknown>
  evidence?: unknown[]
  riskWarnings?: DemoRiskWarning[]
  source?: string
}
