import type {
  ComplianceMetric,
  EffectivenessItem,
  KpiGroup,
  KpiKey,
  WarningListItem,
} from '@/types/dashboard'

/** Per-indicator homepage status (feeds KpiCard value/hint/displayText). */
export type EsgIndicatorHomeStatus = {
  key: KpiKey
  label: string
  fullName?: string
  value: string | number
  unit?: string
  hint?: string
  displayText?: string
  ledgerStatus?: string | null
  /** Indicator-level risk tone for future strip; unused by layout this phase */
  statusTone?: 'normal' | 'attention' | 'risk' | 'pending'
}

/** E / S / G group rollup for homepage headers + risk counts. */
export type EsgGroupHomeStatus = {
  key: 'E' | 'S' | 'G'
  title: string
  status: string
  /** Open risk / warning items attributed to this group */
  riskCount: number
  ryb: { red: number; yellow: number; blue: number }
  indicators: EsgIndicatorHomeStatus[]
}

/**
 * Homepage ESG summary contract.
 * Real Demo API (planned): GET /api/dashboard/esg-home-status
 * Interim: compose from GET /api/dashboard/kpis + GET /api/dashboard/panels
 * or frontend mock when HTTP fails.
 */
export type EsgHomeStatus = {
  groups: EsgGroupHomeStatus[]
  /** Project-wide red / yellow / blue counts (ComplianceRiskPanel metrics) */
  ryb: { red: number; yellow: number; blue: number; total: number }
  complianceMetrics: ComplianceMetric[]
  effectiveness: EffectivenessItem[]
  safeguards: string[]
  warningItems: WarningListItem[]
  /** Optional full KPI groups when API returns them in one shot */
  kpiGroups?: KpiGroup[]
  source: 'api' | 'mock'
  updatedAt: string
}
