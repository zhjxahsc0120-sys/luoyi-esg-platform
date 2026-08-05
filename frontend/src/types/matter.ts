/** Class B 事项详情五段结构（V1.0） */
export type MatterSectionKey =
  | 'basic'
  | 'businessStatus'
  | 'keyMetrics'
  | 'relatedDocs'
  | 'operationLogs'

export interface MatterField {
  label: string
  value: string
}

export interface MatterDocItem {
  name: string
  kind: string
  status: string
}

export interface MatterLogItem {
  at: string
  action: string
  operator: string
  remark: string
}

export interface MatterDetail {
  id: string
  title: string
  basic: MatterField[]
  businessStatus: MatterField[]
  keyMetrics: MatterField[]
  relatedDocs: MatterDocItem[]
  operationLogs: MatterLogItem[]
}

export interface MatterListRow {
  id: string
  cells: Record<string, string>
  detail: MatterDetail
}

export interface MatterStat {
  label: string
  value: string | number
  unit?: string
}

export interface MatterModuleDemo {
  key: string
  title: string
  theme: 'blue' | 'purple' | 'green'
  stats: MatterStat[]
  columns: Array<{ key: string; label: string; width?: string }>
  rows: MatterListRow[]
  hint?: string
}
