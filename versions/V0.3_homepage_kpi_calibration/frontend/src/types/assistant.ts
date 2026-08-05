export type BusinessStatusLevel = '正常' | '基本受控' | '存在风险' | '需重点关注'



export type AssistantAnswerType = 'indicator' | 'inspection' | 'overview' | 'carbon' | 'generic'



export interface ChatMessage {

  id: string

  role: 'user' | 'assistant'

  content: string

  time: string

  /** 业务状态等级（卡片角标） */

  statusLevel?: BusinessStatusLevel

  /** 状态结论首段（项目经理汇报口径） */

  statusConclusion?: string

  answerType?: AssistantAnswerType

  kpiCards?: AssistantKpiCard[]

  /** 重点关注 / 缺失资料 / 风险事项 */

  riskItems?: AssistantRiskItem[]

  riskSectionTitle?: string

  tableData?: AssistantTableData

  dataBasis?: AssistantDataBasis

  /** 建议操作（优先于纯追问文案） */

  nextActions?: AssistantNextAction[]

  followUps?: string[]

  packageCard?: AssistantPackageCard

  loading?: boolean

}



export interface AssistantKpiCard {

  label: string

  value: string | number

  unit?: string

  color?: 'green' | 'blue' | 'purple' | 'orange' | 'red' | 'cyan'

  /** 业务含义，禁止只甩数字 */

  meaning?: string

  /** 指标状态文案 */

  statusText?: string

}



export interface AssistantRiskItem {

  title: string

  section?: string

  status: string

}



export interface AssistantNextAction {

  label: string

  question?: string

}



export interface AssistantTableColumn {

  key: string

  label: string

  width?: string

  align?: 'left' | 'center' | 'right'

}



export interface AssistantTableData {

  title: string

  total?: number

  columns: AssistantTableColumn[]

  rows: Record<string, string | number>[]

  viewAllText?: string

}



export interface AssistantDataBasis {

  itemName: string

  scope: string

  updateTime: string

  dataPeriod: string

  verifyStatus: string

  stableId: string

  sources: Array<{

    name: string

    time: string

    status: string

  }>

  caliber: string

}



export interface AssistantPackageFile {

  name: string

  path: string

  kind: 'report' | 'ledger' | 'checklist' | 'other'

  sizeHint?: string

}



export interface AssistantPackageStats {

  categoryCount?: number

  requiredFileCount?: number

  collectedCount?: number

  pendingCount?: number

  openIssueCount?: number

  closureRate?: string

  closedCount?: number

  historicalTotal?: number

}



export interface AssistantPackageCard {

  packageId: string

  title: string

  inspectionType: 'env' | 'safety' | 'comprehensive'

  nature: 'sample' | 'formal'

  files: AssistantPackageFile[]

  downloadUrl: string

  requiredCount: number

  updatedAt: string

  subtitle?: string

  stats?: AssistantPackageStats

}



export interface ChatSession {

  id: string

  title: string

  lastTime: string

  active?: boolean

}



export interface QuickCategory {

  key: string

  name: string

  desc: string

  color: string

  icon: string

}



export interface AssistantAskResponse {

  code: number

  message?: string

  data: {

    questionId?: string | null

    intentKey?: string | null

    matched?: boolean

    registeredQuestions?: Array<{ id: string; text: string }>

    message: Omit<ChatMessage, 'id' | 'time'> & { role: 'assistant' }

  }

}


