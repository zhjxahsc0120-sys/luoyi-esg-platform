import type { E01EventDetail, E01FactorBrief, E01FactorResult, E01OpenPoint } from '@/types/e01'
import type {
  EsgMonitorFactorRow,
  EsgRiskLevel,
  EsgRiskObjectCard,
  EsgRiskObjectDetail,
} from '@/types/esg-class-a'

const CASE_STATUS_LABELS: Record<string, string> = {
  OPEN: '待处置',
  RECTIFYING: '整改中',
  PENDING_REVIEW: '待复查',
  PENDING_CLOSURE: '待销项',
  CLOSED: '已闭环',
  NO_ISSUE: '正常',
  COMPLIANT: '达标',
  NORMAL: '正常',
}

const OPEN_CASE_STATUS = new Set(['RECTIFYING', 'PENDING_REVIEW', 'PENDING_CLOSURE', 'OPEN', 'IN_PROGRESS'])
const RISK_STATUS_HINTS = ['超标', '异常', '整改', '待复查', '待销项', '未闭环', '风险', '关注']

const MONITOR_TYPE_LABELS: Record<string, string> = {
  WATER: '地表水监测',
  AIR: '环境空气监测',
  NOISE: '声环境监测',
}

export function formatJudgement(value?: string | null): string {
  const raw = String(value || '').trim().toUpperCase()
  if (!raw) return '—'
  if (raw === 'PASS' || raw === 'COMPLIANT' || raw === 'NORMAL' || raw === '达标') return '正常'
  if (raw === 'FAIL' || raw === 'EXCEEDED' || raw === 'STILL_EXCEEDED') return '异常'
  if (raw === 'NO_STANDARD' || raw === 'NOT_EVALUATED' || raw === '未评价' || raw === '未评估') return '未评价'
  return value || '—'
}

export function formatCaseStatus(value?: string | null): string {
  if (!value) return '—'
  const key = String(value).trim().toUpperCase()
  if (CASE_STATUS_LABELS[key]) return CASE_STATUS_LABELS[key]
  const raw = String(value).trim()
  // 屏蔽 PASS / NO_ISSUE 等系统码直出
  if (/^[A-Z][A-Z0-9_]*$/.test(raw)) return '—'
  return raw
}

function humanizePointStatus(status?: string | null): string {
  const text = String(status || '').trim()
  if (!text) return '正常'
  if (RISK_STATUS_HINTS.some((h) => text.includes(h))) return text
  if (text.includes('正常') || text.includes('达标')) return '正常'
  if (/^[A-Z][A-Z0-9_]*$/.test(text)) return formatCaseStatus(text)
  return text
}

export function formatMonitorType(category?: string | null, label?: string | null): string {
  const key = String(category || '').trim().toUpperCase()
  if (MONITOR_TYPE_LABELS[key]) return MONITOR_TYPE_LABELS[key]
  if (label) return `${label}监测`
  return '环境监测'
}

function formatDateTime(value?: string | null): string {
  if (!value) return '—'
  const text = String(value).trim().slice(0, 10)
  const parts = text.split('-')
  if (parts.length === 3) return `${parts[0]}年${Number(parts[1])}月${Number(parts[2])}日`
  return text
}

function shorten(text?: string | null, max = 56): string {
  if (!text) return '—'
  const clean = String(text).replace(/\s+/g, ' ').trim()
  return clean.length <= max ? clean : `${clean.slice(0, max)}…`
}

export function formatLocationText(value?: string | null): string {
  if (!value) return '—'
  const raw = String(value).replace(/\s+/g, ' ').trim()
  let location = raw.split(/[;；]/)[0]?.trim() || raw
  const trailingChainage = location.match(/\s+([A-Za-z]\d+\+\d+)$/)
  if (trailingChainage && location.slice(0, -trailingChainage[0].length).includes(trailingChainage[1])) {
    location = location.slice(0, -trailingChainage[0].length).trim()
  }
  return shorten(location, 48)
}

function splitUnit(value: unknown, unit?: string | null): { value: string; unit: string } {
  if (value === null || value === undefined || value === '') return { value: '—', unit: unit || '—' }
  const text = String(value).trim()
  return { value: text, unit: unit?.trim() || '—' }
}

function hasMeasuredValue(value: unknown): boolean {
  return value !== null && value !== undefined && String(value).trim() !== ''
}

function formatFactorLimit(factor?: E01FactorBrief | null): string {
  if (!factor || factor.limitValue === null || factor.limitValue === undefined || factor.limitValue === '') return '未设置'
  const unit = factor.unit && factor.unit !== '无量纲' ? ` ${factor.unit}` : ''
  return `${factor.limitValue}${unit}`
}

function formatFactorStatus(factor?: E01FactorBrief | null): { label: string; level: EsgRiskLevel } {
  if (!factor || !hasMeasuredValue(factor.detectedValue)) return { label: '数据待补录', level: 'info' }
  if (formatJudgement(factor.judgement) === '异常' || Number(factor.exceedMultiple) > 1) {
    return { label: '超标', level: 'danger' }
  }
  if (factor.limitValue === null || factor.limitValue === undefined || factor.limitValue === '') {
    return { label: '未评价', level: 'info' }
  }
  return { label: '正常', level: 'normal' }
}

export function isE01AbnormalPoint(point: E01OpenPoint): boolean {
  if ((point.factors || []).some((f) => {
    if (f.exceedMultiple != null && Number(f.exceedMultiple) > 1) return true
    const detected = Number(f.detectedValue)
    const limit = Number(f.limitValue)
    return Number.isFinite(detected) && Number.isFinite(limit) && limit > 0 && detected > limit
  })) return true
  const status = String(point.status || '')
  if (RISK_STATUS_HINTS.some((h) => status.includes(h))) return true
  const caseStatus = String(point.caseStatus || '').trim().toUpperCase()
  if (caseStatus && OPEN_CASE_STATUS.has(caseStatus)) return true
  return false
}

function mapFactorRow(f: E01FactorResult): EsgMonitorFactorRow {
  const hasData = hasMeasuredValue(f.detectedValue)
  const isAbnormal = hasData && formatJudgement(f.judgement) === '异常'
  const hasLimit = f.limitValue !== null && f.limitValue !== undefined && f.limitValue !== ''
  const detected = splitUnit(f.detectedValue, f.unit)
  const limit = splitUnit(f.limitValue, f.unit)
  return {
    name: f.factorName || f.factorCode || '—',
    detectedValue: hasData ? detected.value : '暂无实测值',
    unit: hasData ? detected.unit : '',
    limitValue: hasLimit ? (limit.unit !== '—' ? `${limit.value}${limit.unit === '无量纲' ? '' : limit.unit}` : limit.value) : '未设置',
    resultLabel: !hasData ? '数据待补录' : isAbnormal ? '异常' : !hasLimit ? '未评价' : formatJudgement(f.judgement),
    isAbnormal,
  }
}

export function mapE01PointToCard(point: E01OpenPoint): EsgRiskObjectCard {
  const abnormal = (point.factors || []).find((f) => {
    if (f.exceedMultiple != null && Number(f.exceedMultiple) > 1) return true
    const detected = Number(f.detectedValue)
    const limit = Number(f.limitValue)
    return Number.isFinite(detected) && Number.isFinite(limit) && limit > 0 && detected > limit
  })
  const latest = point.factors?.[0]
  const latestFactorStatus = formatFactorStatus(latest)
  const isRisk = isE01AbnormalPoint(point)
  const hasData = (point.factors || []).some((factor) => hasMeasuredValue(factor.detectedValue))
  let statusLabel = '正常'
  let statusLevel: EsgRiskLevel = 'normal'
  if (isRisk) {
    statusLabel = abnormal?.factorName
      ? `${abnormal.factorName}超标`
      : humanizePointStatus(point.status)
    if (statusLabel === '—' || statusLabel === '正常') statusLabel = '异常'
    statusLevel = statusLabel.includes('超标') || statusLabel.includes('异常') ? 'danger' : 'warning'
  } else if (!hasData) {
    statusLabel = '数据待补录'
    statusLevel = 'info'
  }

  return {
    id: point.pointId,
    code: point.pointCode,
    name: point.pointName,
    statusLabel,
    statusLevel,
    locationText: formatLocationText(point.locationText),
    monitorTypeLabel: formatMonitorType(point.monitorCategory, point.monitorCategoryLabel),
    latestTime: formatDateTime(point.discoveredAt),
    primaryEventId: point.primaryEventId,
    canLocate: Boolean(point.canLocate),
    latestResult: latest?.detectedValue == null ? undefined : String(latest.detectedValue),
    latestUnit: latest?.detectedValue == null ? undefined : (latest?.unit || undefined),
    latestFactorName: latest?.factorName || latest?.factorCode,
    latestLimit: formatFactorLimit(latest),
    latestJudgementLabel: latestFactorStatus.label,
    latestJudgementLevel: latestFactorStatus.level,
    trendLabel: latest ? '查看趋势' : '暂无趋势',
  }
}

export function mapE01DetailToView(detail: E01EventDetail): EsgRiskObjectDetail {
  const summary = detail.summary
  const initial = detail.initialFactors?.length ? detail.initialFactors : detail.allSampleFactors
  const factors = initial.map(mapFactorRow)
  const hasData = initial.some((factor) => hasMeasuredValue(factor.detectedValue))
  const primaryAbnormal = detail.initialFactors.find((f) => {
    const detected = Number(f.detectedValue)
    const limit = Number(f.limitValue)
    return formatJudgement(f.judgement) === '异常'
      || (f.exceedMultiple != null && Number(f.exceedMultiple) > 1)
      || (Number.isFinite(detected) && Number.isFinite(limit) && limit > 0 && detected > limit)
  })
  const rectRound = detail.rectificationRounds[detail.rectificationRounds.length - 1]
  const isRisk = Boolean(primaryAbnormal)
  const responsibleUnit = summary.responsibleOrg?.name || undefined

  const caseLabel = formatCaseStatus(summary.caseStatusLabel)
  const caseStatus = formatCaseStatus(summary.caseStatus)
  const pointStatus = humanizePointStatus(summary.status)
  const meaningful = (value?: string) => Boolean(value && value !== '—' && value !== '暂无')
  const statusLabel = isRisk
    ? (caseLabel && caseLabel.includes('整改') ? caseLabel : '高风险')
    : !hasData
      ? '数据待补录'
      : (meaningful(caseLabel) ? caseLabel : meaningful(caseStatus) ? caseStatus : pointStatus)
  const statusLevel: EsgRiskLevel = isRisk
    ? (statusLabel.includes('整改') ? 'warning' : 'danger')
    : !hasData ? 'info' : 'normal'
  const lifecycleStage = meaningful(summary.currentNode || undefined)
    ? summary.currentNode || undefined
    : isRisk ? '待整改' : hasData ? '持续监测' : '数据待补录'

  return {
    pointName: summary.pointName || '—',
    pointCode: summary.pointCode || '—',
    monitorType: formatMonitorType(summary.monitorCategory, summary.monitorCategoryLabel),
    location: formatLocationText(summary.chainage || summary.locationText || summary.engineeringObject),
    statusLabel,
    statusLevel,
    latestTime: formatDateTime(summary.discoveredAt),
    dataSource: summary.standardName || '第三方环境检测报告',
    factors,
    abnormalFactor: primaryAbnormal?.factorName,
    abnormalValue: primaryAbnormal ? splitUnit(primaryAbnormal.detectedValue, primaryAbnormal.unit).value : undefined,
    abnormalLimit: primaryAbnormal ? `${splitUnit(primaryAbnormal.limitValue, primaryAbnormal.unit).value}${primaryAbnormal.unit || ''}` : undefined,
    exceedMultiple: primaryAbnormal?.exceedMultiple != null && Number(primaryAbnormal.exceedMultiple) > 1
      ? Number(primaryAbnormal.exceedMultiple).toFixed(2) : undefined,
    disposalStatus: meaningful(caseLabel) ? caseLabel : meaningful(caseStatus) ? caseStatus : statusLabel,
    rectificationMeasure: rectRound?.summary || undefined,
    lifecycleStage,
    responsibleUnit,
    deadline: undefined,
    nextNode: summary.nextNode || undefined,
    evidenceCount: detail.evidence?.length || 0,
  }
}
