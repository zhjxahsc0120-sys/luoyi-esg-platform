import type { KpiGroup, KpiItem, KpiKey, WarningListItem } from '@/types/dashboard'
import type {
  DemoKpiDetail,
  DemoKpiItem,
  DemoKpisResponse,
  DemoRiskWarning,
  DemoRiskWarningsResponse,
} from '@/types/esg-demo'
import { KPI_HOME_CATALOG } from '@/data/kpi-catalog'

const GROUP_META: Record<'E' | 'S' | 'G', { title: string; theme: 'green' | 'blue' | 'purple' }> = {
  E: { title: '环境环保组', theme: 'green' },
  S: { title: '社会责任组', theme: 'blue' },
  G: { title: '治理合规组', theme: 'purple' },
}

const LEVEL_TO_RYB: Record<string, WarningListItem['level']> = {
  CRITICAL: '红',
  HIGH: '红',
  MEDIUM: '黄',
  LOW: '蓝',
  NORMAL: '蓝',
}

const SURVEY_LABEL: Record<string, string> = {
  COMPLETED: '文物调查已完成',
  IN_PROGRESS: '文物调查进行中',
  PENDING: '文物调查待开展',
}

const RISK_CN: Record<string, string> = {
  NORMAL: '正常',
  LOW: '低',
  MEDIUM: '关注',
  HIGH: '较高',
  CRITICAL: '严重',
}

export function isDemoKpisPayload(data: unknown): data is DemoKpisResponse {
  if (!data || typeof data !== 'object') return false
  const d = data as DemoKpisResponse
  return Array.isArray(d.items) && d.items.length > 0
}

export function isDemoKpiDetail(data: unknown): data is DemoKpiDetail {
  if (!data || typeof data !== 'object') return false
  const d = data as DemoKpiDetail
  return typeof d.key === 'string' && (Array.isArray(d.objects) || d.riskLevel != null || d.objectCount != null)
}

/** Contract items[] → existing KpiGroup[] for TopKpiGroups / KpiCard. */
export function demoItemsToKpiGroups(items: DemoKpiItem[]): KpiGroup[] {
  const groups: Record<'E' | 'S' | 'G', KpiGroup> = {
    E: { key: 'E', title: GROUP_META.E.title, theme: GROUP_META.E.theme, status: '总体可控', items: [] },
    S: { key: 'S', title: GROUP_META.S.title, theme: GROUP_META.S.theme, status: '总体可控', items: [] },
    G: { key: 'G', title: GROUP_META.G.title, theme: GROUP_META.G.theme, status: '总体可控', items: [] },
  }

  for (const item of items) {
    const g = item.key?.[0] as 'E' | 'S' | 'G'
    if (!groups[g]) continue
    const cat = KPI_HOME_CATALOG[item.key as keyof typeof KPI_HOME_CATALOG]
    const mapped: KpiItem = {
      key: item.key as KpiKey,
      label: cat?.label || item.name,
      fullName: cat?.fullName || item.name,
      value: item.value,
      unit: item.unit || cat?.unit,
      hint: item.hint,
    }
    groups[g].items.push(mapped)
  }

  for (const g of Object.values(groups)) {
    // Status filled later from risk warnings when available
    void g
  }
  return [groups.E, groups.S, groups.G]
}

export function normalizeDashboardKpis(
  data: DemoKpisResponse | { groups: KpiGroup[] } | null,
): { groups: KpiGroup[]; items?: DemoKpiItem[]; source?: string } | null {
  if (!data) return null
  if (isDemoKpisPayload(data)) {
    const groups = data.groups?.length ? data.groups : demoItemsToKpiGroups(data.items || [])
    return { groups, items: data.items, source: data.source || 'esg_demo' }
  }
  if ('groups' in data && Array.isArray(data.groups) && data.groups.length) {
    return { groups: data.groups, source: 'legacy' }
  }
  return null
}

/** Prefer summaryList / summaryCards; if summary is object, leave for callers. */
export function demoDetailSummaryList(
  detail: DemoKpiDetail | null | undefined,
): Array<{ label: string; value: string | number; unit?: string }> {
  if (!detail) return []
  if (Array.isArray(detail.summaryList) && detail.summaryList.length) return detail.summaryList
  if (Array.isArray(detail.summaryCards) && detail.summaryCards.length) return detail.summaryCards
  if (Array.isArray(detail.summary)) return detail.summary
  return []
}

const BIZ_STATUS_CN: Record<string, string> = {
  VALID: '有效',
  EXPIRING: '临期',
  OVERDUE: '逾期',
  PENDING: '待审批',
  APPROVED: '已审批',
  OPEN: '未关闭',
  CLOSED: '已关闭',
  COMPLETE: '齐全',
  MISSING: '缺失',
  IMPLEMENTED: '已实施',
  NOT_STARTED: '未开始',
  IN_PROGRESS: '进行中',
  NORMAL: '正常',
  HIGH: '较高',
  MEDIUM: '关注',
  LOW: '低',
  CRITICAL: '严重',
}

/** Map Demo enum-like status codes to Chinese labels for G/S modal tables. */
export function demoBizStatusLabel(value: unknown): string {
  if (value == null || value === '') return '—'
  const text = String(value)
  return BIZ_STATUS_CN[text.toUpperCase()] || text
}

/** Parse focusContext.sourceId → numeric objectId for risk drill. */
export function parseFocusObjectId(sourceId?: string | null): number | null {
  if (sourceId == null || sourceId === '') return null
  const n = Number(sourceId)
  return Number.isFinite(n) ? n : null
}

export function e04SurveyLabel(status?: string | null): string {
  if (!status) return '文物调查已完成'
  return SURVEY_LABEL[String(status).toUpperCase()] || status
}

export function e04RiskLabel(status?: string | null): string {
  if (!status) return '正常'
  return RISK_CN[String(status).toUpperCase()] || status
}

export function mapDemoRiskToWarningItems(
  payload: DemoRiskWarningsResponse | null | undefined,
): WarningListItem[] {
  if (!payload?.items?.length) return []
  return payload.items.map((item: DemoRiskWarning) => {
    const level = LEVEL_TO_RYB[String(item.level || '').toUpperCase()] || '蓝'
    const domain = String(item.domain || 'E').slice(0, 1).toUpperCase()
    const source = (domain === 'S' || domain === 'G' ? domain : 'E') as WarningListItem['source']
    const trigger = item.triggerTime || ''
    const updatedAt =
      typeof trigger === 'string' && trigger.length >= 16
        ? trigger.slice(5, 16).replace(/-/g, '/')
        : String(trigger).slice(0, 16)
    return {
      level,
      title: item.objectName || item.reason || '风险事项',
      source,
      status: item.status || 'OPEN',
      updatedAt,
      kpiKey: item.kpiKey,
      objectId: item.objectId ?? undefined,
      objectName: item.objectName,
      responsibleUnit: item.responsibleUnit,
      domain: item.domain,
      reason: item.reason,
      contractLevel: item.level,
    } as WarningListItem
  })
}

export function mapDemoRiskToComplianceMetrics(payload: DemoRiskWarningsResponse | null | undefined) {
  const items = payload?.items || []
  let red = 0
  let yellow = 0
  let blue = 0
  for (const item of items) {
    const badge = LEVEL_TO_RYB[String(item.level || '').toUpperCase()] || '蓝'
    if (badge === '红') red += 1
    else if (badge === '黄') yellow += 1
    else blue += 1
  }
  return [
    { label: '红色预警', value: red, unit: '项', tone: 'red' as const },
    { label: '黄色预警', value: yellow, unit: '项', tone: 'yellow' as const },
    { label: '蓝色提醒', value: blue, unit: '项', tone: 'blue' as const },
    { label: '预警合计', value: red + yellow + blue, unit: '项', tone: 'neutral' as const },
  ]
}
