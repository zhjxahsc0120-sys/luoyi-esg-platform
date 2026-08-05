/**
 * E02 环保问题整改 — 前端展示 Demo（不改变正式 API 契约）。
 * 优先使用 GET /api/environment/e02/issues；不可用时回退本 Demo。
 */
import type {
  E02BusinessCategory,
  E02IssueDetail,
  E02IssueItem,
  E02IssuesPayload,
} from '@/types/e02'

const details: E02IssueDetail[] = [
  {
    id: 21001,
    businessCode: 'EP-2026-001',
    title: '一标拌合站扬尘超标未闭环',
    issueType: '扬尘污染',
    locationText: 'K18+450 一标拌合站',
    status: '整改中',
    statusGroup: 'rectifying',
    overdue: false,
    deadline: '2026-08-15',
    responsibleOrgName: '第一合同段项目部',
    foundDate: '2026-07-18',
    closedDate: null,
    isDemo: true,
    dataNature: 'demo',
    description: '现场扬尘监测连续超标，围挡与喷淋落实不完整。',
    businessCategory: 'POLLUTION',
    businessCategoryLabel: '环境污染',
    case: null,
    history: [],
    parties: [],
    evidence: [],
    materialCompleteness: {
      requiredRoles: ['整改照片', '复查记录'],
      coveredRoles: ['整改照片'],
      pendingRoles: ['复查记录'],
      ratio: '50%',
      notes: [],
    },
    spatialLinks: [
      { featureId: 'LY-SEC-TJ1', geometryType: 'LineString', role: 'section', isPrimary: true },
    ],
  },
  {
    id: 21002,
    businessCode: 'EP-2026-002',
    title: '二标弃土场排水沟淤塞',
    issueType: '水保设施失效',
    locationText: 'K52+100 二标弃土场东侧',
    status: '待整改',
    statusGroup: 'rectifying',
    overdue: true,
    deadline: '2026-08-05',
    responsibleOrgName: '第二合同段项目部',
    foundDate: '2026-07-22',
    closedDate: null,
    isDemo: true,
    dataNature: 'demo',
    description: '截排水沟淤积导致坡面冲刷风险上升。',
    businessCategory: 'WATER_CONS',
    businessCategoryLabel: '水保问题',
    case: null,
    history: [],
    parties: [],
    evidence: [],
    materialCompleteness: {
      requiredRoles: ['整改方案', '整改照片'],
      coveredRoles: [],
      pendingRoles: ['整改方案', '整改照片'],
      ratio: '0%',
      notes: [],
    },
    spatialLinks: [
      { featureId: 'LY-SEC-TJ2', geometryType: 'LineString', role: 'section', isPrimary: true },
    ],
  },
  {
    id: 21003,
    businessCode: 'EP-2026-003',
    title: '三标临河段植被破损',
    issueType: '生态扰动',
    locationText: 'K88+200 临河路基段',
    status: '待复查',
    statusGroup: 'pendingReview',
    overdue: false,
    deadline: '2026-08-20',
    responsibleOrgName: '第三合同段项目部',
    foundDate: '2026-07-10',
    closedDate: null,
    isDemo: true,
    dataNature: 'demo',
    description: '施工便道侵占河岸缓冲带，已完成补植待复查。',
    businessCategory: 'ECOLOGY',
    businessCategoryLabel: '生态问题',
    case: null,
    history: [],
    parties: [],
    evidence: [],
    materialCompleteness: {
      requiredRoles: ['补植记录', '复查意见'],
      coveredRoles: ['补植记录'],
      pendingRoles: ['复查意见'],
      ratio: '50%',
      notes: [],
    },
    spatialLinks: [
      { featureId: 'LY-SEC-TJ3', geometryType: 'LineString', role: 'section', isPrimary: true },
    ],
  },
  {
    id: 21004,
    businessCode: 'EP-2026-004',
    title: '噪声投诉点位整改闭环',
    issueType: '其他环境问题',
    locationText: 'K35+800 居民点旁施工段',
    status: '已闭环',
    statusGroup: 'terminal',
    overdue: false,
    deadline: '2026-07-30',
    responsibleOrgName: '安全环保部',
    foundDate: '2026-07-01',
    closedDate: '2026-07-28',
    isDemo: true,
    dataNature: 'demo',
    description: '夜间施工噪声投诉，已调整作业时段并完成复查销项。',
    businessCategory: 'OTHER',
    businessCategoryLabel: '其他',
    case: {
      caseId: 9004,
      caseCode: 'CASE-EP-004',
      caseStatus: 'CLOSED',
      caseStatusGroup: 'terminal',
      openedAt: '2026-07-01',
      closedAt: '2026-07-28',
    },
    history: [],
    parties: [],
    evidence: [],
    materialCompleteness: {
      requiredRoles: ['整改照片', '复查记录', '销项单'],
      coveredRoles: ['整改照片', '复查记录', '销项单'],
      pendingRoles: [],
      ratio: '100%',
      notes: [],
    },
    spatialLinks: [
      { featureId: 'LY-SEC-TJ2', geometryType: 'LineString', role: 'section', isPrimary: true },
    ],
  },
  {
    id: 21005,
    businessCode: 'EP-2026-005',
    title: '隧道口泥浆排放不规范',
    issueType: '水污染',
    locationText: 'K101+050 隧道进口沉淀池',
    status: '整改中',
    statusGroup: 'rectifying',
    overdue: false,
    deadline: '2026-08-25',
    responsibleOrgName: '第三合同段项目部',
    foundDate: '2026-07-25',
    closedDate: null,
    isDemo: true,
    dataNature: 'demo',
    description: '沉淀池溢流风险，需完善三级沉淀与清运频次。',
    businessCategory: 'POLLUTION',
    businessCategoryLabel: '环境污染',
    case: null,
    history: [],
    parties: [],
    evidence: [],
    materialCompleteness: {
      requiredRoles: ['整改方案', '整改照片'],
      coveredRoles: ['整改方案'],
      pendingRoles: ['整改照片'],
      ratio: '50%',
      notes: [],
    },
    spatialLinks: [
      { featureId: 'LY-SEC-TJ3', geometryType: 'LineString', role: 'section', isPrimary: true },
    ],
  },
]

function toItem(d: E02IssueDetail): E02IssueItem {
  return {
    id: d.id,
    businessCode: d.businessCode,
    title: d.title,
    issueType: d.issueType,
    locationText: d.locationText,
    status: d.status,
    statusGroup: d.statusGroup as E02IssueItem['statusGroup'],
    overdue: d.overdue,
    deadline: d.deadline,
    responsibleOrgName: d.responsibleOrgName,
    canLocate: d.spatialLinks.length > 0,
    spatialLinks: d.spatialLinks,
    businessCategory: d.businessCategory,
    businessCategoryLabel: d.businessCategoryLabel,
    foundDate: d.foundDate,
    description: d.description,
    closedDate: d.closedDate,
  }
}

export function mapIssueTypeToCategory(issueType: string): {
  category: E02BusinessCategory
  label: string
} {
  const t = issueType || ''
  if (/扬尘|噪声|污水|污染|排放|废气|废水/.test(t)) {
    return { category: 'POLLUTION', label: '环境污染' }
  }
  if (/水保|弃土|表土|排水|拦挡/.test(t)) {
    return { category: 'WATER_CONS', label: '水保问题' }
  }
  if (/生态|植被|敏感|保护/.test(t)) {
    return { category: 'ECOLOGY', label: '生态问题' }
  }
  return { category: 'OTHER', label: '其他' }
}

export function isE02OpenIssue(issue: Pick<E02IssueItem, 'status' | 'statusGroup'>): boolean {
  if (issue.statusGroup === 'terminal') return false
  if (issue.status === '已闭环' || issue.status === '已销项' || issue.status === '已撤销') return false
  return true
}

export function normalizeE02IssuesPayload(data: E02IssuesPayload): E02IssuesPayload {
  const issues = (data.issues || []).map((raw) => {
    const mapped = mapIssueTypeToCategory(raw.issueType || raw.businessCategoryLabel || '')
    const category = raw.businessCategory || mapped.category
    const label = raw.businessCategoryLabel || mapped.label
    return {
      ...raw,
      businessCategory: category,
      businessCategoryLabel: label,
      foundDate: raw.foundDate ?? null,
      closedDate: raw.closedDate ?? null,
      canLocate: raw.canLocate ?? (raw.spatialLinks?.length > 0),
    }
  })
  const byCategory: Record<E02BusinessCategory, number> = {
    POLLUTION: 0,
    WATER_CONS: 0,
    ECOLOGY: 0,
    OTHER: 0,
  }
  for (const i of issues) {
    if (i.businessCategory) byCategory[i.businessCategory] += 1
  }
  const openCount = issues.filter(isE02OpenIssue).length
  const closedCount = issues.length - openCount
  return {
    ...data,
    issues,
    overview: {
      ...data.overview,
      total: data.overview?.total ?? issues.length,
      openCount: data.overview?.openCount ?? openCount,
      closedCount: data.overview?.closedCount ?? closedCount,
      byCategory: data.overview?.byCategory || byCategory,
    },
  }
}

export function getE02IssuesMock(): E02IssuesPayload {
  const issues = details.map(toItem)
  return normalizeE02IssuesPayload({
    overview: {
      total: issues.length,
      rectifying: issues.filter((i) => i.status === '整改中' || i.status === '待整改').length,
      pendingReview: issues.filter((i) => i.status === '待复查').length,
      pendingClosure: 0,
      overdueAmong: issues.filter((i) => i.overdue).length,
    },
    issues,
    spatialLinks: issues.flatMap((i) => i.spatialLinks),
    scope: 'demo',
    isDemo: true,
  })
}

export function getE02IssueDetailMock(issueId: number): E02IssueDetail | null {
  return details.find((d) => d.id === issueId) || null
}
