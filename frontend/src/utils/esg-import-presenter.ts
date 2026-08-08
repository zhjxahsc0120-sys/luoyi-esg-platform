import {
  ESG_DATA_CATALOG,
  getCatalogItem,
  type EsgDataTableItem,
} from '@/data/esg-data-catalog'

const FIELD_LABELS: Record<string, string> = {
  point_code: '点位编号',
  point_name: '点位名称',
  monitor_category: '监测类别',
  location_area: '所属区域',
  chainage: '桩号',
  longitude: '经度',
  latitude: '纬度',
  section_name: '标段',
  active_status: '状态',
  responsible_unit: '责任单位',
  remark: '备注',
  sampled_at: '监测日期',
  period_flag: '时段',
  factor_name: '监测指标',
  factor_code: '指标编码',
  detected_value: '监测值',
  unit: '单位',
  limit_value: '标准限值',
  judgement: '评价结果',
  exceed_multiple: '超标倍数',
  lifecycle_status: '生命周期状态',
  deadline: '整改期限',
  is_closed: '是否闭环',
  rectification_desc: '整改说明',
  retest_value: '复测值',
  closed_date: '关闭日期',
  source_report_no: '报告编号',
}

const SHEET_LABELS: Record<string, string> = {
  'E01_监测点位': '环境监测点位表',
  'E01_监测结果': '环境监测结果表',
  'E02_水保风险台账': '水保风险台账表',
  'E03_生态红线台账': '生态红线台账表',
  'E04_文物保护结论': '文物保护结论表',
}

export interface UploadValidationStats {
  readCount: number
  emptyRowCount: number
  passCount: number
  warningCount: number
  errorCount: number
  expectedInsert: number | null
  expectedUpdate: number | null
  skipCount: number
  blockCount: number
}

export interface ValidationDetailRow {
  excelRow: string
  tableName: string
  businessObject: string
  errorField: string
  result: string
  suggestion: string
  ingestAction: string
}

export interface RecognizeOutcome {
  catalogIds: string[]
  ambiguous: boolean
  unrecognized: boolean
  combinedE01: boolean
  message: string
}

export function formatFieldLabel(field?: string): string {
  if (!field) return '—'
  return FIELD_LABELS[field] || field
}

export function formatSheetLabel(sheet?: string): string {
  if (!sheet) return '—'
  return SHEET_LABELS[sheet] || sheet
}

export function humanizeValidationMessage(message: string): string {
  if (!message) return '—'
  let text = message
  for (const [key, label] of Object.entries(FIELD_LABELS)) {
    text = text.replace(new RegExp(`\\b${key}\\b`, 'g'), label)
  }
  text = text.replace(/请先导入 E01 环境监测点位表/g, '请先建立对应点位')
  text = text.replace(/尚未建立/g, '尚未建立')
  return text
}

export function matchCatalogFromUpload(
  fileName: string,
  parsed: Record<string, unknown> | null,
): RecognizeOutcome {
  const preview = (parsed?.preview as Record<string, unknown> | undefined) || {}
  const recognize = (parsed?.recognize as Record<string, unknown> | undefined) || {}
  const sheetNames = (
    Array.isArray(preview.sheet_names)
      ? preview.sheet_names
      : Array.isArray(recognize.sheet_names)
        ? recognize.sheet_names
        : []
  ) as string[]
  const templateCode = String(recognize.template_code || preview.template_code || '').toUpperCase()

  const ids: string[] = []

  if (templateCode === 'E01' || /E01/i.test(fileName)) {
    const hasPoint = sheetNames.some((s) => s.includes('点位'))
    const hasResult = sheetNames.some((s) => s.includes('结果'))
    if (hasPoint) ids.push('e01-env-monitor-point')
    if (hasResult) ids.push('e01-env-monitor-result')
    if (!hasPoint && !hasResult) {
      if (/点位/.test(fileName)) ids.push('e01-env-monitor-point')
      if (/结果/.test(fileName)) ids.push('e01-env-monitor-result')
    }
    if (ids.length === 2) {
      return {
        catalogIds: ids,
        ambiguous: false,
        unrecognized: false,
        combinedE01: true,
        message: '已识别：点位表 + 结果表',
      }
    }
    if (ids.length === 1) {
      const item = getCatalogItem(ids[0])
      return {
        catalogIds: ids,
        ambiguous: false,
        unrecognized: false,
        combinedE01: false,
        message: item ? `已识别：${item.name}` : '已识别 E01 数据表',
      }
    }
  }

  const byCode = ESG_DATA_CATALOG.find((item) => item.templateCode === templateCode && isCatalogUploadable(item))
  if (byCode) {
    return {
      catalogIds: [byCode.id],
      ambiguous: false,
      unrecognized: false,
      combinedE01: false,
      message: `已识别：${byCode.name}`,
    }
  }

  if (templateCode && templateCode !== 'E01') {
    const building = ESG_DATA_CATALOG.find((item) => item.templateCode === templateCode)
    if (building) {
      return {
        catalogIds: [building.id],
        ambiguous: false,
        unrecognized: false,
        combinedE01: false,
        message: `${building.name} 模板已识别，当前目录状态为「${building.status}」`,
      }
    }
  }

  const nameCandidates = ESG_DATA_CATALOG.filter((item) => {
    if (!item.sheetHint) return false
    return sheetNames.includes(item.sheetHint) || fileName.includes(item.name.replace(/表$/, ''))
  })

  if (nameCandidates.length === 1) {
    return {
      catalogIds: [nameCandidates[0].id],
      ambiguous: false,
      unrecognized: false,
      combinedE01: false,
      message: `已识别：${nameCandidates[0].name}`,
    }
  }

  if (nameCandidates.length > 1) {
    return {
      catalogIds: nameCandidates.map((c) => c.id),
      ambiguous: true,
      unrecognized: false,
      combinedE01: false,
      message: '匹配到多个候选数据表，请选择归属',
    }
  }

  return {
    catalogIds: [],
    ambiguous: false,
    unrecognized: true,
    combinedE01: false,
    message: '无法识别数据表归属，请从目录选择目标表后重试',
  }
}

function isCatalogUploadable(item: EsgDataTableItem): boolean {
  return item.status === '可上传' || item.status === '已有数据'
}

export function buildValidationStats(parsed: Record<string, unknown> | null): UploadValidationStats {
  const preview = (parsed?.preview as Record<string, unknown> | undefined) || {}
  const validation = (parsed?.validation as Record<string, unknown> | undefined) || {}
  const errors = (Array.isArray(validation.errors) ? validation.errors : []) as Array<Record<string, unknown>>
  const warnings = (Array.isArray(validation.warnings) ? validation.warnings : []) as Array<Record<string, unknown>>
  const readCount = Number(preview.row_count ?? validation.row_count ?? 0)
  const errorRows = new Set(
    errors.map((e) => `${e.sheet || ''}:${e.row || 0}`).filter((k) => !k.endsWith(':0')),
  )
  const blockCount = errors.filter((e) =>
    ['TEMPLATE_MISMATCH', 'UNKNOWN_TEMPLATE', 'MISSING_SHEET', 'EMPTY_DATA'].includes(String(e.code)),
  ).length
  const rowErrors = errors.filter((e) => Number(e.row || 0) > 0).length
  const passCount = Math.max(0, readCount - errorRows.size)

  return {
    readCount,
    emptyRowCount: 0,
    passCount,
    warningCount: warnings.length,
    errorCount: errors.length,
    expectedInsert: parsed?.ok ? readCount : null,
    expectedUpdate: null,
    skipCount: 0,
    blockCount: blockCount || (parsed?.ok === false && rowErrors === 0 ? 1 : 0),
  }
}

export function buildValidationDetailRows(parsed: Record<string, unknown> | null): ValidationDetailRow[] {
  const validation = (parsed?.validation as Record<string, unknown> | undefined) || {}
  const errors = (Array.isArray(validation.errors) ? validation.errors : []) as Array<Record<string, unknown>>
  const warnings = (Array.isArray(validation.warnings) ? validation.warnings : []) as Array<Record<string, unknown>>

  const rows: ValidationDetailRow[] = []

  for (const err of errors) {
    rows.push(mapValidationItem(err, '错误', '阻断入库'))
  }
  for (const warn of warnings) {
    rows.push(mapValidationItem(warn, '警告', '可继续核对'))
  }

  if (!rows.length && parsed?.ok === false) {
    rows.push({
      excelRow: '—',
      tableName: '—',
      businessObject: '—',
      errorField: '—',
      result: '校验未通过',
      suggestion: humanizeValidationMessage(String(parsed.message || '请检查模板与数据')),
      ingestAction: '阻断',
    })
  }

  return rows
}

function mapValidationItem(
  item: Record<string, unknown>,
  result: string,
  ingestAction: string,
): ValidationDetailRow {
  const sheet = String(item.sheet || '')
  const field = String(item.field || '')
  const rowNo = Number(item.row || 0)
  const message = humanizeValidationMessage(String(item.message || ''))

  return {
    excelRow: rowNo > 0 ? String(rowNo) : '—',
    tableName: formatSheetLabel(sheet),
    businessObject: sheet.includes('结果') ? '监测结果记录' : sheet.includes('点位') ? '监测点位' : '—',
    errorField: formatFieldLabel(field),
    result,
    suggestion: message,
    ingestAction,
  }
}

export function hasPointDependencyError(parsed: Record<string, unknown> | null): boolean {
  const validation = (parsed?.validation as Record<string, unknown> | undefined) || {}
  const errors = (Array.isArray(validation.errors) ? validation.errors : []) as Array<Record<string, unknown>>
  const msg = String(parsed?.message || '')
  if (/尚未建立|请先建立对应点位|请先导入.*点位/.test(msg)) return true
  return errors.some((e) =>
    /尚未建立|请先建立对应点位|请先导入.*点位/.test(String(e.message || '')),
  )
}

export interface RecentBatchRow {
  id: string
  tableName: string
  source: string
  templateVersion: string
  uploadedAt: string
  readCount: number
  successCount: number
  errorCount: number
  status: '处理中' | '待确认' | '已完成' | '部分完成' | '失败' | '跳过'
}

export function mapSessionBatch(
  batchCode: string,
  catalogId: string,
  parsed: Record<string, unknown>,
  confirmed: boolean,
): RecentBatchRow {
  const item = getCatalogItem(catalogId)
  const preview = (parsed.preview as Record<string, unknown> | undefined) || {}
  const recognize = (parsed.recognize as Record<string, unknown> | undefined) || {}
  const validation = (parsed.validation as Record<string, unknown> | undefined) || {}
  const errors = Array.isArray(validation.errors) ? validation.errors.length : 0
  const readCount = Number(preview.row_count ?? 0)
  const ok = Boolean(parsed.ok)

  let status: RecentBatchRow['status'] = '待确认'
  if (confirmed) status = '已完成'
  else if (!ok) status = errors > 0 ? '失败' : '跳过'
  else if (parsed.ingest_status === 'PENDING') status = '待确认'

  return {
    id: batchCode,
    tableName: item?.name || String(recognize.template_name || '未知数据表'),
    source: '人工模板',
    templateVersion: String(recognize.template_version || preview.template_version || item?.templateVersion || '—'),
    uploadedAt: new Date().toLocaleString('zh-CN', { hour12: false }),
    readCount,
    successCount: ok ? readCount : 0,
    errorCount: errors,
    status,
  }
}
