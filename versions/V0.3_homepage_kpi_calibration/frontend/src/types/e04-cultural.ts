/** E04 文物保护管控（首页 KPI + 工作台）类型 */

export type E04CulturalPanelLayer = 'overview' | 'detail'

export interface E04CulturalOverview {
  /** 文物调查状态，如「文物调查已完成」 */
  surveyStatus: string
  objectCount: number
  measureRate: number
  riskCount: number
  /** 风险状态文案，如「正常」；与 status 同义时可并存 */
  riskStatus: string
  status: string
}

export interface E04CulturalObjectItem {
  id: number
  relicCode: string
  relicName: string
  relicType: string
  protectionLevel: string
  locationDesc: string
  riskStatus: string
  responsibleUnit: string
  updateTime: string | null
}

export interface E04CulturalObjectDetail extends E04CulturalObjectItem {
  projectId: string
  sectionId: number | null
  longitude: number | null
  latitude: number | null
  protectionScope: string
  constructionImpact: string
  protectionMeasure: string
  materialStatus: string
}

export interface E04CulturalObjectsPayload {
  overview: E04CulturalOverview
  objects: E04CulturalObjectItem[]
  isDemo?: boolean
}
