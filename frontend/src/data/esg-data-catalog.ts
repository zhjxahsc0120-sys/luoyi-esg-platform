/**
 * ESG 智能入库 — 数据表/数据集目录（前端配置）
 * 首页指标仅作为 displayAssociations 下游提示，不作为上传前置选择。
 */

export type EsgDataDomain =
  | '环境监测'
  | '水土保持'
  | '生态与文物'
  | '安全生产'
  | '工资与诉求'
  | '社会效益'
  | '治理合规'
  | '碳排与低碳'
  | '项目基础与资料'
  | '扩展数据'

export type EsgDataNature =
  | '基础主数据'
  | '事实数据'
  | '事件数据'
  | '结果汇总'
  | '整改闭环'
  | '参考配置'
  | '来源资料'

export type EsgDataTableStatus =
  | '可上传'
  | '已有数据'
  | '建设中'
  | '仅自动接入'
  | '暂未关联首页'

export type EsgAccessMode = '人工模板' | '智能体' | 'API' | '定时连接'

export type EsgDataTableItem = {
  id: string
  name: string
  domain: EsgDataDomain
  nature: EsgDataNature
  description: string
  status: EsgDataTableStatus
  accessMode: EsgAccessMode
  templateVersion?: string
  templateUrl?: string
  /** 后端识别模板编码（上传 API expectedTemplate） */
  templateCode?: string
  /** 用于从工作表名识别归属 */
  sheetHint?: string
  dependencies?: string[]
  displayAssociations: string[]
  recordCount?: number
  lastSyncAt?: string
  /** 目录排序权重，越小越靠前 */
  sortOrder?: number
}

const V12_BASE = '/templates/esg/split_V1.2_业务录入'

export const ESG_DATA_DOMAINS: EsgDataDomain[] = [
  '环境监测',
  '水土保持',
  '生态与文物',
  '安全生产',
  '工资与诉求',
  '社会效益',
  '治理合规',
  '碳排与低碳',
  '项目基础与资料',
  '扩展数据',
]

export const ESG_DATA_NATURES: EsgDataNature[] = [
  '基础主数据',
  '事实数据',
  '事件数据',
  '结果汇总',
  '整改闭环',
  '参考配置',
  '来源资料',
]

export const ESG_DATA_STATUSES: EsgDataTableStatus[] = [
  '可上传',
  '已有数据',
  '建设中',
  '仅自动接入',
  '暂未关联首页',
]

export const ESG_ACCESS_MODES: EsgAccessMode[] = ['人工模板', '智能体', 'API', '定时连接']

/** 正式 V1.2 E01 模板静态路径（由后端 /templates/esg/ 提供） */
export const E01_POINT_TEMPLATE_URL = `${V12_BASE}/E01_环境监测点位表.xlsx`
export const E01_RESULT_TEMPLATE_URL = `${V12_BASE}/E01_环境监测结果表.xlsx`

export const ESG_DATA_CATALOG: EsgDataTableItem[] = [
  {
    id: 'e01-env-monitor-point',
    name: '环境监测点位表',
    domain: '环境监测',
    nature: '基础主数据',
    description: '维护地表水、废水、噪声等监测点位基础信息及坐标，为监测结果与风险分析提供主数据。',
    status: '可上传',
    accessMode: '人工模板',
    templateVersion: 'V1.2',
    templateUrl: E01_POINT_TEMPLATE_URL,
    templateCode: 'E01',
    sheetHint: 'E01_监测点位',
    dependencies: [],
    displayAssociations: ['E01 环保风险预警'],
    sortOrder: 10,
  },
  {
    id: 'e01-env-monitor-result',
    name: '环境监测结果表',
    domain: '环境监测',
    nature: '事实数据',
    description: '录入已发生的监测指标、检测值、标准限值与评价结果；须先建立对应监测点位。',
    status: '可上传',
    accessMode: '人工模板',
    templateVersion: 'V1.2',
    templateUrl: E01_RESULT_TEMPLATE_URL,
    templateCode: 'E01',
    sheetHint: 'E01_监测结果',
    dependencies: ['e01-env-monitor-point'],
    displayAssociations: ['E01 环保风险预警'],
    sortOrder: 11,
  },
  {
    id: 'e02-soil-conservation-ledger',
    name: '水保风险台账表',
    domain: '水土保持',
    nature: '事实数据',
    description: '弃渣场、临时用地、表土剥离、施工边坡等水保对象台账（V1.1 过程录入）。',
    status: '建设中',
    accessMode: '人工模板',
    templateVersion: 'V1.1',
    templateCode: 'E02',
    sheetHint: 'E02_水保风险台账',
    displayAssociations: ['E02 水保风险预警'],
    sortOrder: 20,
  },
  {
    id: 'e03-ecological-redline',
    name: '生态红线台账表',
    domain: '生态与文物',
    nature: '事实数据',
    description: '生态保护对象与敏感区风险台账。',
    status: '建设中',
    accessMode: '人工模板',
    templateCode: 'E03',
    displayAssociations: ['E03 生态红线预警'],
    sortOrder: 30,
  },
  {
    id: 'e04-cultural-relic',
    name: '文物保护结论表',
    domain: '生态与文物',
    nature: '结果汇总',
    description: '文物保护专项调查与结论汇总。',
    status: '建设中',
    accessMode: '人工模板',
    templateCode: 'E04',
    displayAssociations: ['E04 文物保护情况'],
    sortOrder: 31,
  },
  {
    id: 's01-safety-incident',
    name: '安全生产事故与培训表',
    domain: '安全生产',
    nature: '事件数据',
    description: '安全事故、培训、演练与重大风险源（多 Sheet V1.1）。',
    status: '建设中',
    accessMode: '人工模板',
    templateCode: 'S01',
    displayAssociations: ['S01 安全生产天数'],
    sortOrder: 40,
  },
  {
    id: 's02-worker-payment',
    name: '农民工工资发放表',
    domain: '工资与诉求',
    nature: '结果汇总',
    description: '工资汇总与欠薪诉求台账。',
    status: '建设中',
    accessMode: '人工模板',
    templateCode: 'S02',
    displayAssociations: ['S02 农民工工资按时发放率'],
    sortOrder: 50,
  },
  {
    id: 's03-public-appeal',
    name: '群众诉求台账表',
    domain: '工资与诉求',
    nature: '事件数据',
    description: '群众投诉与办理闭环记录。',
    status: '建设中',
    accessMode: '人工模板',
    templateCode: 'S03',
    displayAssociations: ['S03 群众诉求管理'],
    sortOrder: 51,
  },
  {
    id: 's04-social-benefit',
    name: '社会效益成果表',
    domain: '社会效益',
    nature: '事实数据',
    description: '公益帮扶、就业带动等社会效益事项。',
    status: '建设中',
    accessMode: '人工模板',
    templateCode: 'S04',
    displayAssociations: ['S04 社会效益'],
    sortOrder: 60,
  },
  {
    id: 'g01-compliance-procedure',
    name: '合规手续许可表',
    domain: '治理合规',
    nature: '基础主数据',
    description: '环评、水保、施工许可等手续台账。',
    status: '建设中',
    accessMode: '人工模板',
    templateCode: 'G01',
    displayAssociations: ['G01 合规手续管理'],
    sortOrder: 70,
  },
  {
    id: 'g02-design-special-plan',
    name: '设计与专项方案表',
    domain: '治理合规',
    nature: '事实数据',
    description: '设计变更与重大专项方案审批记录。',
    status: '建设中',
    accessMode: '人工模板',
    templateCode: 'G02',
    displayAssociations: ['G02 设计与专项方案管理'],
    sortOrder: 71,
  },
  {
    id: 'g03-quality-compliance',
    name: '质量合规检查表',
    domain: '治理合规',
    nature: '事实数据',
    description: '合规检查发现问题与月度汇总。',
    status: '建设中',
    accessMode: '人工模板',
    templateCode: 'G03',
    displayAssociations: ['G03 项目质量合规管理'],
    sortOrder: 72,
  },
  {
    id: 'g04-integrity',
    name: '廉洁合规事件表',
    domain: '治理合规',
    nature: '事件数据',
    description: '廉洁事件与廉政教育记录。',
    status: '建设中',
    accessMode: '人工模板',
    templateCode: 'G04',
    displayAssociations: ['G04 廉洁合规天数'],
    sortOrder: 73,
  },
  {
    id: 'carbon-activity',
    name: '碳排放活动数据采集表',
    domain: '碳排与低碳',
    nature: '事实数据',
    description: '标段碳排放活动量与因子快照（独立碳模块）。',
    status: '仅自动接入',
    accessMode: 'API',
    templateVersion: 'V1.0',
    displayAssociations: ['碳排核算'],
    sortOrder: 80,
  },
  {
    id: 'carbon-measure',
    name: '低碳措施填报表',
    domain: '碳排与低碳',
    nature: '事实数据',
    description: '减排措施与月度绩效（独立碳模块）。',
    status: '仅自动接入',
    accessMode: 'API',
    templateVersion: 'V1.0',
    displayAssociations: ['低碳措施'],
    sortOrder: 81,
  },
  {
    id: 'ext-project-archive',
    name: '项目基础资料归档表',
    domain: '扩展数据',
    nature: '来源资料',
    description: '非结构化资料索引与归档元数据（规划中）。',
    status: '暂未关联首页',
    accessMode: '智能体',
    displayAssociations: [],
    sortOrder: 90,
  },
]

export function getCatalogItem(id: string): EsgDataTableItem | undefined {
  return ESG_DATA_CATALOG.find((item) => item.id === id)
}

/** 工作台首屏默认可展示的可上传表数量上限 */
export const WORKBENCH_UPLOADABLE_LIMIT = 6

export function resolveTemplateDownloadUrl(relativePath: string): string {
  const apiBase = (import.meta.env.VITE_API_BASE as string | undefined)?.replace(/\/$/, '') || ''
  // 后端静态服务按文件名从 templates/esg/ 根目录读取，嵌套路径取 basename
  const fileName = relativePath.split('/').filter(Boolean).pop() || relativePath
  return `${apiBase}/templates/esg/${encodeURIComponent(fileName)}`
}

export function getUploadableCatalog(): EsgDataTableItem[] {
  return ESG_DATA_CATALOG.filter(isCatalogUploadable).sort(
    (a, b) => (a.sortOrder ?? 99) - (b.sortOrder ?? 99),
  )
}

export function formatDependencyHint(item: EsgDataTableItem): string | null {
  if (!item.dependencies?.length) return null
  const names = item.dependencies
    .map((id) => getCatalogItem(id)?.name)
    .filter((name): name is string => Boolean(name))
  if (!names.length) return null
  return `需先完成：${names.join('、')}`
}

export function getCatalogStatusSummary(): {
  uploadable: number
  building: number
  autoAccess: number
  other: number
} {
  let uploadable = 0
  let building = 0
  let autoAccess = 0
  let other = 0
  for (const item of ESG_DATA_CATALOG) {
    if (isCatalogUploadable(item)) uploadable += 1
    else if (item.status === '建设中') building += 1
    else if (item.status === '仅自动接入') autoAccess += 1
    else other += 1
  }
  return { uploadable, building, autoAccess, other }
}

export function isCatalogUploadable(item: EsgDataTableItem): boolean {
  return item.status === '可上传' || item.status === '已有数据'
}

export function catalogStatusRank(status: EsgDataTableStatus): number {
  switch (status) {
    case '可上传':
      return 0
    case '已有数据':
      return 1
    case '建设中':
      return 2
    case '仅自动接入':
      return 3
    default:
      return 4
  }
}
