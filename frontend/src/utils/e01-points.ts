import type { E01OpenPoint } from '@/types/e01'

const RISK_STATUS_HINTS = ['超标', '异常', '整改', '待复查', '待销项', '未闭环', '风险', '关注']
const CLOSED_STATUS = new Set(['正常', '已闭环', '已销项', 'CLOSED', '正常监测'])
const OPEN_CASE_STATUS = new Set([
  'RECTIFYING',
  'PENDING_REVIEW',
  'PENDING_CLOSURE',
  'OPEN',
  'IN_PROGRESS',
])

/** Client-side risk filter — does not change API payload / KPI caliber. */
export function isE01RiskPoint(point: E01OpenPoint): boolean {
  const status = String(point.status || '').trim()
  if (status && RISK_STATUS_HINTS.some((h) => status.includes(h))) return true
  if (status && !CLOSED_STATUS.has(status) && status.toUpperCase() !== 'NORMAL') return true

  const caseStatus = String(point.caseStatus || '').trim().toUpperCase()
  if (caseStatus && OPEN_CASE_STATUS.has(caseStatus)) return true

  return (point.factors || []).some((f) => {
    const multi = f.exceedMultiple
    return multi != null && Number(multi) > 1
  })
}
