/** Class A 右侧二级分析区 — 展示层模型 */

export type EsgRiskLevel = 'normal' | 'warning' | 'danger' | 'info'

export type EsgObjectFilter = 'risk' | 'all' | 'normal'

export type EsgTrendChartMode = 'line' | 'bar'

export interface EsgMonitorFactorRow {
  name: string
  detectedValue: string
  unit: string
  limitValue: string
  resultLabel: string
  isAbnormal: boolean
}

export interface EsgRiskObjectCard {
  id: number
  code: string
  name: string
  statusLabel: string
  statusLevel: EsgRiskLevel
  locationText: string
  monitorTypeLabel: string
  latestTime: string
  primaryEventId: number
  canLocate: boolean
  latestResult?: string
  latestUnit?: string
  latestFactorName?: string
  latestLimit?: string
  latestJudgementLabel?: string
  latestJudgementLevel?: EsgRiskLevel
  trendLabel?: string
  responsibleUnit?: string
}

export interface EsgRiskObjectDetail {
  pointName: string
  pointCode: string
  monitorType: string
  location: string
  statusLabel: string
  statusLevel: EsgRiskLevel
  latestTime: string
  dataSource: string
  factors: EsgMonitorFactorRow[]
  abnormalFactor?: string
  abnormalValue?: string
  abnormalLimit?: string
  exceedMultiple?: string
  disposalStatus?: string
  rectificationMeasure?: string
  lifecycleStage?: string
  responsibleUnit?: string
  deadline?: string
  nextNode?: string
  evidenceCount?: number
}

export interface EsgClassAPanelConfig {
  moduleKey: string
  title: string
  theme: 'green' | 'blue' | 'purple'
}
