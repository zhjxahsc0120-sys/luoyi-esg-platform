/**
 * S02 重大风险源管控 — 前端展示 Demo 与归一化。
 */
import type {
  S02BusinessCategory,
  S02RiskDetail,
  S02RiskItem,
  S02RisksPayload,
} from '@/types/s02'

const details: S02RiskDetail[] = [
  {
    id: 82001,
    businessCode: 'SR-2026-001',
    title: '隧道施工塌方风险',
    riskLevel: '重大',
    riskType: '重大风险源',
    locationText: 'K25+300 隧道出口',
    status: '在控',
    controlStartDate: '2026-06-01',
    cancelledDate: null,
    controlMeasure: '超前支护、监控量测、限制进尺',
    canLocate: true,
    spatialLinks: [
      { featureId: 'LY-SEC-TJ2', geometryType: 'LineString', role: 'section', isPrimary: true },
    ],
    sourceTable: 'demo',
    responsibleOrgName: '第二合同段项目部',
    description: '围岩较差段塌方风险，纳入重大风险源台账。',
    specialPlanName: '隧道塌方重大风险专项方案',
    specialPlanStatus: '审查中',
    approvalStatus: '待审批',
    businessCategory: 'MAJOR_SOURCE',
    businessCategoryLabel: '重大风险源',
    sectionCode: 'TJ-2',
  },
  {
    id: 82002,
    businessCode: 'SR-2026-002',
    title: '桥梁挂篮悬浇危大工程',
    riskLevel: '较大',
    riskType: '危大工程',
    locationText: 'K32+500 大桥 8#墩',
    status: '在控',
    controlStartDate: '2026-06-15',
    cancelledDate: null,
    controlMeasure: '挂篮验收、专项交底、旁站监理',
    canLocate: true,
    spatialLinks: [
      { featureId: 'LY-SEC-TJ2', geometryType: 'LineString', role: 'section', isPrimary: true },
    ],
    sourceTable: 'demo',
    responsibleOrgName: '第二合同段项目部',
    description: '挂篮悬浇作业属危大工程清单。',
    specialPlanName: '挂篮施工专项方案',
    specialPlanStatus: '已审查',
    approvalStatus: '已审批',
    businessCategory: 'HAZARDOUS_ENG',
    businessCategoryLabel: '危大工程',
    sectionCode: 'TJ-2',
  },
  {
    id: 82003,
    businessCode: 'SR-2026-003',
    title: '深基坑临边防护',
    riskLevel: '一般',
    riskType: '一般风险源',
    locationText: 'K12+800 涵洞基坑',
    status: '在控',
    controlStartDate: '2026-07-01',
    cancelledDate: null,
    controlMeasure: '临边护栏、排水与监测',
    canLocate: true,
    spatialLinks: [
      { featureId: 'LY-SEC-TJ1', geometryType: 'LineString', role: 'section', isPrimary: true },
    ],
    sourceTable: 'demo',
    responsibleOrgName: '第一合同段项目部',
    description: '一般风险源，按日常管控执行。',
    specialPlanName: null,
    specialPlanStatus: null,
    approvalStatus: '不适用',
    businessCategory: 'GENERAL',
    businessCategoryLabel: '一般风险源',
    sectionCode: 'TJ-1',
  },
  {
    id: 82004,
    businessCode: 'SR-2026-004',
    title: '高边坡坍塌风险',
    riskLevel: '重大',
    riskType: '重大风险源',
    locationText: 'K18+200 路基边坡',
    status: '在控',
    controlStartDate: '2026-05-20',
    cancelledDate: null,
    controlMeasure: '分级开挖、锚索监测、截排水',
    canLocate: true,
    spatialLinks: [
      { featureId: 'LY-SEC-TJ1', geometryType: 'LineString', role: 'section', isPrimary: true },
    ],
    sourceTable: 'demo',
    responsibleOrgName: '第一合同段项目部',
    description: '高边坡重大风险源。',
    specialPlanName: '高边坡专项施工方案',
    specialPlanStatus: '已编制',
    approvalStatus: '审批中',
    businessCategory: 'MAJOR_SOURCE',
    businessCategoryLabel: '重大风险源',
    sectionCode: 'TJ-1',
  },
]

function toItem(d: S02RiskDetail): S02RiskItem {
  return {
    id: d.id,
    businessCode: d.businessCode,
    title: d.title,
    riskLevel: d.riskLevel,
    riskType: d.riskType,
    locationText: d.locationText,
    status: d.status,
    controlStartDate: d.controlStartDate,
    controlMeasure: d.controlMeasure,
    canLocate: d.canLocate,
    spatialLinks: d.spatialLinks,
    businessCategory: d.businessCategory,
    businessCategoryLabel: d.businessCategoryLabel,
    sectionCode: d.sectionCode,
    description: d.description,
    specialPlanName: d.specialPlanName,
    specialPlanStatus: d.specialPlanStatus,
    approvalStatus: d.approvalStatus,
    responsibleOrgName: d.responsibleOrgName,
  }
}

export function mapS02Category(risk: Pick<S02RiskItem, 'riskLevel' | 'riskType' | 'businessCategory'>): {
  category: S02BusinessCategory
  label: string
} {
  if (risk.businessCategory) {
    const labels: Record<S02BusinessCategory, string> = {
      MAJOR_SOURCE: '重大风险源',
      HAZARDOUS_ENG: '危大工程',
      GENERAL: '一般风险源',
    }
    return { category: risk.businessCategory, label: labels[risk.businessCategory] }
  }
  const type = risk.riskType || ''
  if (/危大/.test(type)) return { category: 'HAZARDOUS_ENG', label: '危大工程' }
  if (risk.riskLevel === '重大' || /重大风险/.test(type)) {
    return { category: 'MAJOR_SOURCE', label: '重大风险源' }
  }
  if (risk.riskLevel === '一般' || /一般/.test(type)) {
    return { category: 'GENERAL', label: '一般风险源' }
  }
  if (risk.riskLevel === '较大') return { category: 'HAZARDOUS_ENG', label: '危大工程' }
  return { category: 'GENERAL', label: '一般风险源' }
}

export function isS02KeyRisk(risk: Pick<S02RiskItem, 'businessCategory' | 'riskLevel' | 'riskType'>): boolean {
  const { category } = mapS02Category(risk)
  return category === 'MAJOR_SOURCE'
}

export function normalizeS02RisksPayload(data: S02RisksPayload): S02RisksPayload {
  const risks = (data.risks || []).map((r) => {
    const mapped = mapS02Category(r)
    return {
      ...r,
      businessCategory: mapped.category,
      businessCategoryLabel: r.businessCategoryLabel || mapped.label,
      sectionCode: r.sectionCode || null,
    }
  })
  return {
    ...data,
    risks,
    overview: {
      ...data.overview,
      total: data.overview?.total ?? risks.length,
      majorSourceCount: risks.filter((r) => r.businessCategory === 'MAJOR_SOURCE').length,
      hazardousEngCount: risks.filter((r) => r.businessCategory === 'HAZARDOUS_ENG').length,
      generalCount: risks.filter((r) => r.businessCategory === 'GENERAL').length,
      major: data.overview?.major ?? risks.filter((r) => r.riskLevel === '重大').length,
      larger: data.overview?.larger ?? risks.filter((r) => r.riskLevel === '较大').length,
    },
  }
}

export function getS02RisksMock(): S02RisksPayload {
  const risks = details.map(toItem)
  return normalizeS02RisksPayload({
    overview: {
      total: risks.length,
      major: risks.filter((r) => r.riskLevel === '重大').length,
      larger: risks.filter((r) => r.riskLevel === '较大').length,
      newThisMonth: 1,
      cancelledThisMonth: 0,
      locationCount: risks.filter((r) => r.canLocate).length,
    },
    risks,
    spatialLinks: risks.flatMap((r) => r.spatialLinks),
    scope: 'demo',
    isDemo: true,
  })
}

export function getS02RiskDetailMock(riskId: number): S02RiskDetail | null {
  return details.find((d) => d.id === riskId) || null
}
