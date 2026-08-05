/**
 * ESG 智能数据填报 - 隔离的前端演示适配层。
 *
 * 本模块不调用正式上传、解析或入库接口，也不会修改数据库。
 * 后续接入正式能力时，只需在此处替换 load/run/write 三个边界函数，
 * 页面组件不需要感知后端契约变化。
 */

export type DemoFormat = 'xlsx' | 'pdf'
export type BusinessCategory = '环境监测' | '水保整改' | '碳排放' | '待识别'

export interface DemoFileDefinition {
  id: string
  category: Exclude<BusinessCategory, '待识别'>
  xlsxName: string
  pdfName: string
  records: number
  fields: number
  confidence: number
  ledger: string
}

export interface SmartEntryFile {
  id: string
  file: File
  name: string
  size: number
  category: BusinessCategory
  records: number
  status: '已就绪'
  source: 'demo' | 'local'
}

export interface AnalysisCard {
  id: string
  category: BusinessCategory
  fileName: string
  confidence: number
  records: number
  mappedFields: number
  pending: number
  ledger: string
}

export interface ReviewItem {
  id: 'noise-limit' | 'org-match'
  category: Exclude<BusinessCategory, '待识别'>
  sourceName: string
  businessObject: string
  fieldName: string
  value: string
  validation: string
  detail: string
  status: '待确认' | '已确认'
}

export interface DemoWriteResult {
  batchCode: string
  recordCount: number
  completedAt: string
  message: string
}

export const DEMO_BASE_URL = '/test-data/esg-smart-entry'

export const DEMO_FILE_DEFINITIONS: DemoFileDefinition[] = [
  {
    id: 'environment',
    category: '环境监测',
    xlsxName: '01_环境监测原始记录_2026年6月.xlsx',
    pdfName: '01_环境监测原始记录_2026年6月.pdf',
    records: 12,
    fields: 11,
    confidence: 97.4,
    ledger: '环境监测结果台账',
  },
  {
    id: 'water',
    category: '水保整改',
    xlsxName: '02_水保问题整改台账_2026年6月.xlsx',
    pdfName: '02_水保问题整改台账_2026年6月.pdf',
    records: 8,
    fields: 11,
    confidence: 95.8,
    ledger: '水保问题闭环台账',
  },
  {
    id: 'carbon',
    category: '碳排放',
    xlsxName: '03_碳排放活动数据_2026年6月.xlsx',
    pdfName: '03_碳排放活动数据_2026年6月.pdf',
    records: 10,
    fields: 10,
    confidence: 96.9,
    ledger: '碳排放活动量台账',
  },
]

const TYPE_BY_EXTENSION: Record<string, string> = {
  xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  xls: 'application/vnd.ms-excel',
  csv: 'text/csv',
  pdf: 'application/pdf',
  doc: 'application/msword',
  docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  txt: 'text/plain',
  zip: 'application/zip',
}

function extensionOf(name: string): string {
  return name.split('.').pop()?.toLowerCase() || ''
}

export function inferBusinessCategory(name: string): BusinessCategory {
  const normalized = name.toLowerCase()
  if (normalized.includes('环境') || normalized.includes('监测') || normalized.includes('噪声')) return '环境监测'
  if (normalized.includes('水保') || normalized.includes('整改') || normalized.includes('弃土场')) return '水保整改'
  if (normalized.includes('碳') || normalized.includes('排放') || normalized.includes('活动量')) return '碳排放'
  return '待识别'
}

export function definitionForCategory(category: BusinessCategory): DemoFileDefinition | undefined {
  return DEMO_FILE_DEFINITIONS.find(item => item.category === category)
}

export function toSmartEntryFile(file: File, source: 'demo' | 'local' = 'local', index = 0): SmartEntryFile {
  const category = inferBusinessCategory(file.name)
  return {
    id: `${source}-${Date.now()}-${index}-${file.name}`,
    file,
    name: file.name,
    size: file.size,
    category,
    records: definitionForCategory(category)?.records || 0,
    status: '已就绪',
    source,
  }
}

export async function loadDemoFiles(format: DemoFormat): Promise<SmartEntryFile[]> {
  const files = await Promise.all(DEMO_FILE_DEFINITIONS.map(async (definition, index) => {
    const name = format === 'xlsx' ? definition.xlsxName : definition.pdfName
    const url = `${DEMO_BASE_URL}/${name}`
    const response = await fetch(url)
    if (!response.ok) throw new Error(`无法载入演示文件：${name}`)
    const blob = await response.blob()
    const type = blob.type || TYPE_BY_EXTENSION[extensionOf(name)] || 'application/octet-stream'
    const file = new File([blob], name, { type, lastModified: Date.now() })
    return toSmartEntryFile(file, 'demo', index)
  }))
  return files
}

export function buildAnalysisCards(files: SmartEntryFile[]): AnalysisCard[] {
  return files.map((file, index) => {
    const definition = definitionForCategory(file.category)
    return {
      id: `${file.id}-analysis`,
      category: file.category,
      fileName: file.name,
      confidence: definition?.confidence || 86.5,
      records: definition?.records || Math.max(1, file.records),
      mappedFields: definition?.fields || 6,
      pending: file.category === '环境监测' || file.category === '水保整改' ? 1 : 0,
      ledger: definition?.ledger || '待人工指定业务台账',
    }
  })
}

export async function runDemoAnalysis(
  files: SmartEntryFile[],
  onProgress: (progress: number, label: string) => void,
): Promise<AnalysisCard[]> {
  const stages = [
    [16, '读取文件与页表结构'],
    [38, '识别资料类型'],
    [64, '抽取结构化字段'],
    [84, '执行规则校验'],
    [100, '生成可核对结果'],
  ] as const

  for (const [progress, label] of stages) {
    onProgress(progress, label)
    await new Promise(resolve => window.setTimeout(resolve, 180))
  }
  return buildAnalysisCards(files)
}

export function buildReviewItems(files: SmartEntryFile[]): ReviewItem[] {
  const sourceFor = (category: BusinessCategory) =>
    files.find(file => file.category === category)?.name || definitionForCategory(category)?.xlsxName || '演示资料'

  const items: ReviewItem[] = []
  if (files.some(file => file.category === '环境监测')) {
    items.push({
      id: 'noise-limit',
      category: '环境监测',
      sourceName: sourceFor('环境监测'),
      businessObject: 'K12+450 施工便道',
      fieldName: '昼间噪声值',
      value: '68.2 dB(A)',
      validation: '待确认',
      detail: '执行限值 65 dB(A)，识别值超出 3.2 dB(A)',
      status: '待确认',
    })
  }
  if (files.some(file => file.category === '水保整改')) {
    items.push({
      id: 'org-match',
      category: '水保整改',
      sourceName: sourceFor('水保整改'),
      businessObject: '2#弃土场',
      fieldName: '责任单位',
      value: '第三标段项目部',
      validation: '待确认',
      detail: '平台标准名称：TJ-03 标项目部｜近似匹配 92%',
      status: '待确认',
    })
  }
  return items
}

export async function writeDemoBatch(recordCount: number): Promise<DemoWriteResult> {
  await new Promise(resolve => window.setTimeout(resolve, 420))
  return {
    batchCode: 'DEMO-20260726-001',
    recordCount,
    completedAt: new Intl.DateTimeFormat('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    }).format(new Date()),
    message: '前端演示写入完成，未写入正式业务库',
  }
}
