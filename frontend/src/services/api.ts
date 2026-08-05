import type { KpiDetailConfig, KpiGroup } from '@/types/dashboard'
import type { MonthlyReadiness, MonthlyReportOverview } from '@/types/monthly-report'
import type { E01EventDetail, E01EventsPayload, E01PointTrendPayload } from '@/types/e01'
import type { E02IssueDetail, E02IssuesPayload, E02ObjectDetail, E02ObjectsPayload } from '@/types/e02'
import type { E03EcoObjectDetail, E03EcoObjectsPayload, E03IssueDetail, E03IssuesPayload } from '@/types/e03'
import type { S02RiskDetail, S02RisksPayload } from '@/types/s02'
import type { E04CulturalObjectDetail, E04CulturalObjectsPayload } from '@/types/e04-cultural'
import type { AssistantAskResponse } from '@/types/assistant'
import type { EsgHomeStatus } from '@/types/esg-home'
import type { DemoKpiDetail, DemoKpiObjectDetail, DemoKpisResponse, DemoRiskWarningsResponse } from '@/types/esg-demo'
import type {
  ApiMutationResult,
  RectificationTask,
  RectificationTaskList,
  RectificationTaskPatch,
  SpecialPlanApproval,
  SpecialPlanCreatePayload,
  SpecialPlanList,
  SpecialPlanPatchPayload,
} from '@/types/governance'
import { getEsgHomeStatusMock } from '@/data/esg-home.mock'
import {
  getE04CulturalObjectDetailMock,
  getE04CulturalObjectsMock,
} from '@/data/e04-cultural.mock'
import { normalizeDashboardKpis, mapDemoRiskToWarningItems, mapDemoRiskToComplianceMetrics } from '@/utils/esg-demo'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8765'

/**
 * Homepage ESG status.
 * Prefer Demo contract: /api/dashboard/kpis (items) + /api/dashboard/risk-warnings
 * Fallback compose panels; network fail → frontend mock (never pretend live success).
 */
export async function getEsgHomeStatus(): Promise<EsgHomeStatus> {
  const [kpisRaw, panels, risks] = await Promise.all([
    getDashboardKpisRaw(),
    getDashboardPanels(),
    getDashboardRiskWarnings({ status: 'OPEN' }),
  ])
  const normalized = normalizeDashboardKpis(kpisRaw)
  if (normalized?.groups?.length || panels?.compliance || risks?.items?.length) {
    const mock = getEsgHomeStatusMock()
    const compliance = panels?.compliance
    const warningItemsFromRisk = risks?.items?.length
      ? mapDemoRiskToWarningItems(risks)
      : null
    const complianceMetricsFromRisk = risks?.items?.length
      ? mapDemoRiskToComplianceMetrics(risks)
      : null
    const complianceMetrics =
      complianceMetricsFromRisk ||
      (compliance?.metrics as EsgHomeStatus['complianceMetrics']) ||
      mock.complianceMetrics
    const warningItems =
      warningItemsFromRisk ||
      (compliance?.warningItems as EsgHomeStatus['warningItems']) ||
      mock.warningItems
    const apiGroups = normalized?.groups
    const groups = apiGroups?.length
      ? apiGroups.map((g) => {
          const mockG = mock.groups.find((m) => m.key === g.key)
          const rybFromWarnings = countRybBySource(warningItems, g.key)
          return {
            key: g.key,
            title: g.title,
            status: formatGroupStatus(rybFromWarnings, mockG?.status),
            riskCount: rybFromWarnings.red + rybFromWarnings.yellow + rybFromWarnings.blue,
            ryb: rybFromWarnings,
            indicators: g.items.map((item) => ({
              key: item.key,
              label: item.label,
              fullName: item.fullName,
              value: item.value,
              unit: item.unit,
              hint: item.hint,
              displayText: item.displayText,
              ledgerStatus: item.ledgerStatus,
            })),
          }
        })
      : mock.groups

    return {
      ...mock,
      source: 'api',
      updatedAt: new Date().toISOString(),
      groups,
      kpiGroups: apiGroups,
      complianceMetrics,
      effectiveness:
        (compliance?.effectiveness as EsgHomeStatus['effectiveness']) ||
        complianceMetricsFromRisk?.slice(0, 3).map((m) => ({
          label: m.label.replace('预警', '').replace('提醒', ''),
          value: Number(m.value) || 0,
        })) ||
        mock.effectiveness,
      safeguards: compliance?.safeguards || mock.safeguards,
      warningItems,
      ryb: deriveRybFromCompliance(complianceMetrics, mock.ryb),
    }
  }

  return getEsgHomeStatusMock()
}

function countRybBySource(
  items: EsgHomeStatus['warningItems'],
  source: 'E' | 'S' | 'G',
): { red: number; yellow: number; blue: number } {
  const ryb = { red: 0, yellow: 0, blue: 0 }
  for (const row of items) {
    if (row.source !== source) continue
    if (row.level === '红') ryb.red += 1
    else if (row.level === '黄') ryb.yellow += 1
    else if (row.level === '蓝') ryb.blue += 1
  }
  return ryb
}

function formatGroupStatus(
  ryb: { red: number; yellow: number; blue: number },
  fallback?: string,
): string {
  const total = ryb.red + ryb.yellow + ryb.blue
  if (!total && fallback) return fallback
  return `风险 ${total} · 红${ryb.red} 黄${ryb.yellow} 蓝${ryb.blue}`
}

function deriveRybFromCompliance(
  metrics: EsgHomeStatus['complianceMetrics'],
  fallback: EsgHomeStatus['ryb'],
): EsgHomeStatus['ryb'] {
  const find = (tone: string) => {
    const hit = metrics.find((m) => m.tone === tone)
    return typeof hit?.value === 'number' ? hit.value : Number(hit?.value) || 0
  }
  const red = find('red')
  const yellow = find('yellow')
  const blue = find('blue')
  const totalHit = metrics.find((m) => m.tone === 'neutral')
  const total =
    typeof totalHit?.value === 'number'
      ? totalHit.value
      : red + yellow + blue || fallback.total
  if (!red && !yellow && !blue) return { ...fallback }
  return { red, yellow, blue, total }
}

export async function apiGet<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`)
    if (!res.ok) return null
    return (await res.json()) as T
  } catch {
    return null
  }
}

export async function apiHealth(): Promise<{ ok: boolean; service: string; db: string } | null> {
  return apiGet('/health')
}

export async function getDashboardKpisRaw(): Promise<DemoKpisResponse | { groups: KpiGroup[] } | null> {
  return apiGet('/api/dashboard/kpis')
}

export async function getDashboardKpis(): Promise<{ groups: KpiGroup[]; items?: DemoKpisResponse['items']; source?: string } | null> {
  const raw = await getDashboardKpisRaw()
  return normalizeDashboardKpis(raw)
}

export async function getDashboardRiskWarnings(opts?: {
  projectId?: number
  status?: string
  page?: number
  pageSize?: number
}): Promise<DemoRiskWarningsResponse | null> {
  const params = new URLSearchParams()
  params.set('projectId', String(opts?.projectId ?? 1001))
  if (opts?.status) params.set('status', opts.status)
  if (opts?.page) params.set('page', String(opts.page))
  if (opts?.pageSize) params.set('pageSize', String(opts.pageSize))
  const query = params.toString()
  return apiGet(`/api/dashboard/risk-warnings${query ? `?${query}` : ''}`)
}

export async function askAssistant(payload: {
  question?: string
  questionId?: string
}): Promise<AssistantAskResponse | null> {
  const body: Record<string, string> = {}
  if (payload.question) body.question = payload.question
  if (payload.questionId) body.questionId = payload.questionId
  const posted = await apiPost<AssistantAskResponse>('/api/assistant/ask', body)
  if (posted) return posted
  const params = new URLSearchParams()
  if (payload.question) params.set('question', payload.question)
  if (payload.questionId) params.set('questionId', payload.questionId)
  const query = params.toString()
  return apiGet<AssistantAskResponse>(`/api/assistant/qa${query ? `?${query}` : ''}`)
}

export async function getDashboardKpiS01(): Promise<S01Data | null> {
  return apiGet('/api/dashboard/kpi/S01')
}

/**
 * KPI detail — Demo contract shape (trend/summary/objects) preferred.
 * Modal bridge fields (summaryList/detailData) included when Demo API responds.
 * Network fail → null (caller shows loadError; no fake live success).
 */
export async function getDashboardKpiDetail(key: string): Promise<(KpiDetailConfig & DemoKpiDetail) | null> {
  const detail = await apiGet<KpiDetailConfig & DemoKpiDetail>(`/api/dashboard/kpi/${key}`)
  if (!detail) return null
  // Bridge: if Demo returns object summary + summaryList, expose list as summary for legacy modals
  const anyDetail = detail as DemoKpiDetail & { summary?: unknown }
  if (anyDetail.summaryList?.length && !Array.isArray(anyDetail.summary)) {
    return { ...detail, summary: anyDetail.summaryList } as KpiDetailConfig & DemoKpiDetail
  }
  if (anyDetail.summaryCards?.length && !Array.isArray(anyDetail.summary)) {
    return { ...detail, summary: anyDetail.summaryCards } as KpiDetailConfig & DemoKpiDetail
  }
  return detail
}

export async function getDashboardKpiObject(
  key: string,
  objectId: number,
  projectId = 1001,
): Promise<DemoKpiObjectDetail | null> {
  return apiGet(`/api/dashboard/kpi/${key}/objects/${objectId}?projectId=${projectId}`)
}

/**
 * Phase B.1 — E01 环保风险预警.
 * Demo only: GET /api/environment/e01/events. No silent mock fallback.
 */
export async function getE01Events(): Promise<{ code: number; data: E01EventsPayload; meta?: Record<string, unknown> } | null> {
  const res = await apiGet<{ code: number; data: E01EventsPayload & { source?: string }; meta?: Record<string, unknown> }>(
    '/api/environment/e01/events',
  )
  if (res && res.code === 0 && res.data) {
    return {
      ...res,
      data: normalizeE01EventsPayload(res.data),
      meta: { source: res.data.source || res.meta?.source || 'esg_demo' },
    }
  }
  return null
}

export async function getE01EventDetail(eventId: number): Promise<{ code: number; data: E01EventDetail; meta?: Record<string, unknown> } | null> {
  const res = await apiGet<{ code: number; data: E01EventDetail; meta?: Record<string, unknown> }>(
    `/api/environment/e01/events/${eventId}`,
  )
  if (res && res.code === 0 && res.data) {
    return { ...res, meta: { source: res.meta?.source || 'esg_demo' } }
  }
  return null
}

export async function getE01PointTrend(
  pointId: number,
  factorCode?: string | null,
): Promise<{ code: number; data: E01PointTrendPayload; meta?: Record<string, unknown> } | null> {
  const params = new URLSearchParams()
  if (factorCode) params.set('factorCode', factorCode)
  const query = params.toString()
  const res = await apiGet<{ code: number; data: E01PointTrendPayload; meta?: Record<string, unknown> }>(
    `/api/environment/e01/points/${pointId}/trend${query ? `?${query}` : ''}`,
  )
  if (res && res.code === 0 && res.data) {
    return { ...res, meta: { source: res.meta?.source || 'esg_demo' } }
  }
  return null
}

export async function getE02Issues(scope?: 'formal' | 'demo'): Promise<{ code: number; data: E02IssuesPayload; meta?: Record<string, unknown> } | null> {
  const params = new URLSearchParams()
  if (scope) params.set('scope', scope)
  const query = params.toString()
  return apiGet(`/api/environment/e02/issues${query ? `?${query}` : ''}`)
}

export async function getE02IssueDetail(issueId: number): Promise<{ code: number; data: E02IssueDetail; meta?: Record<string, unknown> } | null> {
  return apiGet(`/api/environment/e02/issues/${issueId}`)
}

/**
 * Phase B.1 — E02 水保对象域（弃土场/临时用地/表土剥离/边坡复绿）.
 * Demo only: GET /api/environment/e02/objects. No silent mock fallback.
 */
export async function getE02Objects(): Promise<{ code: number; data: E02ObjectsPayload; meta?: Record<string, unknown> } | null> {
  const res = await apiGet<{ code: number; data: E02ObjectsPayload & { source?: string }; meta?: Record<string, unknown> }>(
    '/api/environment/e02/objects',
  )
  if (res && res.code === 0 && res.data && Array.isArray(res.data.objects)) {
    return { ...res, meta: { source: res.data.source || 'esg_demo' } }
  }
  return null
}

export async function getE02ObjectDetail(
  objectId: number,
): Promise<{ code: number; data: E02ObjectDetail; meta?: Record<string, unknown> } | null> {
  const res = await apiGet<{ code: number; data: E02ObjectDetail; meta?: Record<string, unknown> }>(
    `/api/environment/e02/objects/${objectId}`,
  )
  if (res && res.code === 0 && res.data) {
    return { ...res, meta: { source: res.meta?.source || 'esg_demo' } }
  }
  return null
}

export async function getE03Issues(scope?: 'formal' | 'demo'): Promise<{ code: number; data: E03IssuesPayload; meta?: Record<string, unknown> } | null> {
  const params = new URLSearchParams()
  if (scope) params.set('scope', scope)
  const query = params.toString()
  return apiGet(`/api/environment/e03/issues${query ? `?${query}` : ''}`)
}

export async function getE03IssueDetail(
  issueId: number,
  scope?: 'formal' | 'demo',
): Promise<{ code: number; data: E03IssueDetail; meta?: Record<string, unknown> } | null> {
  const params = new URLSearchParams()
  if (scope) params.set('scope', scope)
  const query = params.toString()
  return apiGet(`/api/environment/e03/issues/${issueId}${query ? `?${query}` : ''}`)
}

/**
 * Phase B.1 — E03 生态敏感区 / 保护对象.
 * Demo only: GET /api/environment/e03/eco-objects. No silent mock fallback.
 */
export async function getE03EcoObjects(): Promise<{ code: number; data: E03EcoObjectsPayload; meta?: Record<string, unknown> } | null> {
  const res = await apiGet<{ code: number; data: E03EcoObjectsPayload & { source?: string }; meta?: Record<string, unknown> }>(
    '/api/environment/e03/eco-objects',
  )
  if (res && res.code === 0 && res.data && Array.isArray(res.data.objects)) {
    return { ...res, meta: { source: res.data.source || 'esg_demo' } }
  }
  return null
}

export async function getE03EcoObjectDetail(
  objectId: number,
): Promise<{ code: number; data: E03EcoObjectDetail; meta?: Record<string, unknown> } | null> {
  const res = await apiGet<{ code: number; data: E03EcoObjectDetail; meta?: Record<string, unknown> }>(
    `/api/environment/e03/eco-objects/${objectId}`,
  )
  if (res && res.code === 0 && res.data) {
    return { ...res, meta: { source: res.meta?.source || 'esg_demo' } }
  }
  return null
}

export async function getE04CulturalObjects(): Promise<{ code: number; data: E04CulturalObjectsPayload; meta?: Record<string, unknown> } | null> {
  const res = await apiGet<{ code: number; data: E04CulturalObjectsPayload & { source?: string }; meta?: Record<string, unknown> }>(
    '/api/environment/e04/cultural-objects',
  )
  if (res && res.code === 0 && res.data) {
    return {
      ...res,
      data: normalizeE04CulturalPayload(res.data),
      meta: { source: res.data.source || res.meta?.source || 'api' },
    }
  }
  return { code: 0, data: getE04CulturalObjectsMock(), meta: { source: 'mock' } }
}

export async function getE04CulturalObjectDetail(
  objectId: number,
): Promise<{ code: number; data: E04CulturalObjectDetail; meta?: Record<string, unknown> } | null> {
  const res = await apiGet<{ code: number; data: E04CulturalObjectDetail; meta?: Record<string, unknown> }>(
    `/api/environment/e04/cultural-objects/${objectId}`,
  )
  if (res && res.code === 0 && res.data) return res
  const mock = getE04CulturalObjectDetailMock(objectId)
  return mock ? { code: 0, data: mock, meta: { source: 'mock' } } : null
}

function normalizeE01EventsPayload(data: E01EventsPayload): E01EventsPayload {
  const ov = data.overview || {
    totalOpenPoints: 0,
    waterCount: 0,
    airCount: 0,
    noiseCount: 0,
  }
  const openPoints = data.openPoints || []
  const monitorPointCount =
    ov.monitorPointCount ?? data.kpi?.pointCount ?? Math.max(openPoints.length, ov.totalOpenPoints)
  const anomalyCount = ov.anomalyCount ?? ov.totalOpenPoints ?? openPoints.length
  const openCount = ov.openCount ?? ov.totalOpenPoints ?? openPoints.length
  const riskLevel =
    ov.riskLevel ||
    (openCount >= 5 ? '红' : openCount >= 2 ? '黄' : openCount > 0 ? '蓝' : '正常')
  return {
    ...data,
    overview: {
      ...ov,
      monitorPointCount,
      anomalyCount,
      openCount,
      riskLevel,
    },
  }
}

function normalizeE04CulturalPayload(data: E04CulturalObjectsPayload): E04CulturalObjectsPayload {
  const ov = data.overview || {
    surveyStatus: '文物调查已完成',
    objectCount: 0,
    measureRate: 100,
    riskCount: 0,
    riskStatus: '正常',
    status: '正常',
  }
  const objectCount = ov.objectCount ?? (data.objects?.length || 0)
  const riskCount = ov.riskCount ?? 0
  const riskStatus = ov.riskStatus || ov.status || (riskCount > 0 ? '关注' : '正常')
  return {
    ...data,
    overview: {
      ...ov,
      surveyStatus: ov.surveyStatus || '文物调查已完成',
      objectCount,
      measureRate: ov.measureRate ?? 100,
      riskCount,
      riskStatus,
      status: ov.status || riskStatus,
    },
  }
}

export async function getS02Risks(): Promise<{ code: number; data: S02RisksPayload; meta?: Record<string, unknown> } | null> {
  return apiGet('/api/social/s02/risks')
}

export async function getS02RiskDetail(riskId: number): Promise<{ code: number; data: S02RiskDetail; meta?: Record<string, unknown> } | null> {
  return apiGet(`/api/social/s02/risks/${riskId}`)
}

export async function getDashboardTopic(topic: 'carbon' | 'monthly-report'): Promise<KpiDetailConfig | null> {
  return apiGet(topic === 'carbon' ? '/api/carbon/benefit-overview' : `/api/dashboard/topics/${topic}`)
}

export async function getDashboardPanels(): Promise<DashboardPanels | null> {
  return apiGet('/api/dashboard/panels')
}

export async function getMonthlyReportReadiness(reportPeriod: string): Promise<MonthlyReadiness | null> {
  const params = new URLSearchParams({ reportPeriod })
  return apiGet<MonthlyReadiness>(`/api/monthly-report/readiness?${params.toString()}`)
}

// Codex 已完成的新版月报概览接口：MySQL → 服务端 JSON 契约快照 → 前端 Mock
export async function getMonthlyReportOverview(reportMonth: string): Promise<MonthlyReportOverview | null> {
  const params = new URLSearchParams({ reportMonth })
  return apiGet<MonthlyReportOverview>(`/api/monthly/report-overview?${params.toString()}`)
}

export async function getWorkspaceSummary(): Promise<WorkspaceSummary | null> {
  return apiGet('/api/workspace/summary')
}

export async function getWorkspaceTasks(params?: {
  module?: string
  status?: string
  keyword?: string
  cycle?: string
  cycleType?: string
  deadlineStart?: string
  deadlineEnd?: string
  assignee?: string
}): Promise<{ total: number; items: UploadTask[] } | null> {
  const qs = new URLSearchParams()
  if (params?.module) qs.set('module', params.module)
  if (params?.status) qs.set('status', params.status)
  if (params?.keyword) qs.set('keyword', params.keyword)
  if (params?.cycle) qs.set('cycle', params.cycle)
  if (params?.cycleType) qs.set('cycleType', params.cycleType)
  if (params?.deadlineStart) qs.set('deadlineStart', params.deadlineStart)
  if (params?.deadlineEnd) qs.set('deadlineEnd', params.deadlineEnd)
  if (params?.assignee) qs.set('assignee', params.assignee)
  const query = qs.toString()
  return apiGet(`/api/workspace/tasks${query ? `?${query}` : ''}`)
}

export async function getDocumentsSummary(): Promise<DocumentsSummary | null> {
  return apiGet('/api/workspace/documents/summary')
}

export async function getDocuments(): Promise<{ total: number; items: DocumentItem[] } | null> {
  return apiGet('/api/workspace/documents')
}

export async function getDocumentDetail(documentId: string | number): Promise<DocumentDetailApi | null> {
  return apiGet(`/api/workspace/documents/${documentId}`)
}

export async function getDocumentVersions(documentId: string | number): Promise<{ items: DocumentVersionApi[] } | null> {
  return apiGet(`/api/workspace/documents/${documentId}/versions`)
}

export async function getDocumentRelations(documentId: string | number): Promise<{ items: DocumentRelationApi[] } | null> {
  return apiGet(`/api/workspace/documents/${documentId}/relations`)
}

export async function getReviews(): Promise<{ statusCards: StatusCard[]; items: ReviewItem[] } | null> {
  return apiGet('/api/workspace/reviews')
}

export async function getTaskDetail(taskId: string): Promise<TaskDetailApi | null> {
  return apiGet(`/api/workspace/tasks/${taskId}/detail`)
}

export async function saveTaskDraft(taskId: string, payload?: {
  comment?: string
  operatorId?: number
  operatorName?: string
}): Promise<TaskActionResponse | null> {
  return apiPost(`/api/workspace/tasks/${taskId}/save`, payload || {})
}

export async function linkTaskDocument(taskId: string, payload: {
  documentId: string | number
  requirementId?: string
  matchScore?: number
  operatorId?: number
  source?: string
}): Promise<TaskActionResponse | null> {
  return apiPost(`/api/workspace/tasks/${taskId}/link-document`, payload)
}

export async function submitTaskReview(taskId: string, payload?: {
  comment?: string
  operatorId?: number
  operatorName?: string
}): Promise<TaskActionResponse | null> {
  return apiPost(`/api/workspace/tasks/${taskId}/submit`, payload || {})
}

export async function getReviewDetail(reviewId: string | number): Promise<ReviewDetailApi | null> {
  return apiGet(`/api/workspace/reviews/${reviewId}`)
}

export async function getReviewTimeline(reviewId: string | number): Promise<{ items: ReviewTimelineApi[] } | null> {
  return apiGet(`/api/workspace/reviews/${reviewId}/timeline`)
}

export async function getReviewRequirements(reviewId: string | number): Promise<{ items: ReviewRequirementApi[] } | null> {
  return apiGet(`/api/workspace/reviews/${reviewId}/requirements`)
}

export async function approveReview(reviewId: string | number, payload?: {
  reviewer?: string
  operatorName?: string
  comment?: string
}): Promise<ReviewActionResponse | null> {
  return apiPost(`/api/workspace/reviews/${reviewId}/approve`, payload || {})
}

export async function returnReview(reviewId: string | number, payload?: {
  reviewer?: string
  operatorName?: string
  comment?: string
  requirements?: string[]
}): Promise<ReviewActionResponse | null> {
  return apiPost(`/api/workspace/reviews/${reviewId}/return`, payload || {})
}

export async function getParseQueue(): Promise<{ items: ParseQueueItem[] } | null> {
  return apiGet('/api/workspace/ai/parse-queue')
}

export async function uploadWorkspaceFile(payload: {
  originalName: string
  fileSize: number
  mimeType?: string
  uploaderId?: number
  uploaderName?: string
}): Promise<UploadFileResponse | null> {
  return apiPost('/api/workspace/files/upload', payload)
}

export async function uploadWorkspaceBinaryFile(file: File, meta?: {
  uploaderId?: number
  uploaderName?: string
}): Promise<UploadFileResponse | null> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    if (meta?.uploaderId) formData.append('uploaderId', String(meta.uploaderId))
    if (meta?.uploaderName) formData.append('uploaderName', meta.uploaderName)
    const res = await fetch(`${API_BASE}/api/workspace/files/upload`, {
      method: 'POST',
      body: formData,
    })
    if (!res.ok) return null
    return (await res.json()) as UploadFileResponse
  } catch {
    return null
  }
}

export async function startParseFile(fileId: number): Promise<ParseJobResponse | null> {
  return apiPost(`/api/workspace/files/${fileId}/parse`, {})
}

export async function getParseJob(jobId: number): Promise<ParseJobDetail | null> {
  return apiGet(`/api/workspace/parse-jobs/${jobId}`)
}

export async function getParseFields(jobId: number): Promise<{ items: ParseFieldItem[] } | null> {
  return apiGet(`/api/workspace/parse-jobs/${jobId}/fields`)
}

export async function getMatchCandidates(jobId: number): Promise<{ items: MatchCandidateItem[] } | null> {
  return apiGet(`/api/workspace/parse-jobs/${jobId}/match-candidates`)
}

export async function confirmParseJob(
  jobId: number,
  payload: {
    confirmedFields: { fieldKey: string; confirmedValue: string }[]
    acceptedCandidateIds: number[]
    operatorId?: number
    operatorName?: string
    comment?: string
  }
): Promise<ConfirmParseResponse | null> {
  return apiPost(`/api/workspace/parse-jobs/${jobId}/confirm`, payload)
}

// ─── V0.4 Governance APIs (do not alter dashboard / KPI contracts above) ───

export async function getRectificationTasks(opts?: {
  taskStatus?: string
  dataNature?: string
  isDemo?: 0 | 1
  completed?: 0 | 1
}): Promise<RectificationTaskList | null> {
  const params = new URLSearchParams()
  if (opts?.taskStatus) params.set('taskStatus', opts.taskStatus)
  if (opts?.dataNature) params.set('dataNature', opts.dataNature)
  if (opts?.isDemo !== undefined) params.set('isDemo', String(opts.isDemo))
  if (opts?.completed !== undefined) params.set('completed', String(opts.completed))
  const query = params.toString()
  return apiGet(`/api/governance/rectification-tasks${query ? `?${query}` : ''}`)
}

export async function getRectificationTask(id: number): Promise<RectificationTask | null> {
  return apiGet(`/api/governance/rectification-tasks/${id}`)
}

export async function patchRectificationTask(
  id: number,
  payload: RectificationTaskPatch,
): Promise<ApiMutationResult<RectificationTask>> {
  return apiPatch(`/api/governance/rectification-tasks/${id}`, payload)
}

export async function getSpecialPlans(opts?: {
  projectId?: number
  riskPointId?: number
  approvalStatus?: string
  riskLevel?: string
  dataNature?: string
  isDemo?: 0 | 1
}): Promise<SpecialPlanList | null> {
  const params = new URLSearchParams()
  if (opts?.projectId != null) params.set('projectId', String(opts.projectId))
  if (opts?.riskPointId != null) params.set('riskPointId', String(opts.riskPointId))
  if (opts?.approvalStatus) params.set('approvalStatus', opts.approvalStatus)
  if (opts?.riskLevel) params.set('riskLevel', opts.riskLevel)
  if (opts?.dataNature) params.set('dataNature', opts.dataNature)
  if (opts?.isDemo !== undefined) params.set('isDemo', String(opts.isDemo))
  const query = params.toString()
  return apiGet(`/api/governance/special-plans${query ? `?${query}` : ''}`)
}

export async function getSpecialPlan(id: number): Promise<SpecialPlanApproval | null> {
  return apiGet(`/api/governance/special-plans/${id}`)
}

export async function createSpecialPlan(
  payload: SpecialPlanCreatePayload,
): Promise<ApiMutationResult<SpecialPlanApproval>> {
  return apiMutate('POST', '/api/governance/special-plans', payload)
}

export async function patchSpecialPlan(
  id: number,
  payload: SpecialPlanPatchPayload,
): Promise<ApiMutationResult<SpecialPlanApproval>> {
  return apiPatch(`/api/governance/special-plans/${id}`, payload)
}

async function apiPost<T>(path: string, payload: unknown): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) return null
    return (await res.json()) as T
  } catch {
    return null
  }
}

export async function apiPatch<T>(path: string, payload: unknown): Promise<ApiMutationResult<T>> {
  return apiMutate('PATCH', path, payload)
}

async function apiMutate<T>(
  method: 'POST' | 'PATCH',
  path: string,
  payload: unknown,
): Promise<ApiMutationResult<T>> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    let body: { message?: string } | T | null = null
    try {
      body = (await res.json()) as { message?: string } | T
    } catch {
      body = null
    }
    if (!res.ok) {
      const message =
        body && typeof body === 'object' && 'message' in body && body.message
          ? String(body.message)
          : `请求失败 (${res.status})`
      return { ok: false, data: null, status: res.status, message }
    }
    return { ok: true, data: body as T, status: res.status }
  } catch {
    return { ok: false, data: null, status: 0, message: '网络异常，请稍后重试' }
  }
}

type S01Data = {
  continuousDays: number | null
  statisticsStart: string | null
  cycleStartDate: string | null
  statisticsAsOf: string | null
  countingStatus: string
  latestInterruptDate: string | null
  latestInterruptReason: string | null
  pendingDeterminationCount: number
  confirmationStatus: string | null
  confirmationBatchId: number | null
  demoBatchCode: string | null
  currentConstructionStage: string | null
  currentStage: string | null
  currentStageDetail: string | null
  dataNature: string
  isDemo: boolean
  scope: string
  conclusion: string
  // 兼容过渡字段
  projectStartDate?: string | null
  currentDate?: string | null
  updateTime?: string | null
  // 旧字段（兼容 KpiDetailModal 等）
  timeline?: {
    startLabel: string
    startDate: string
    message: string
    endLabel: string
    endDate: string
    months: string[]
  }
  constructionStages?: {
    id: string
    name: string
    status: string
    detail?: string
    startDate?: string
    endDate?: string
  }[]
}

type DashboardPanels = {
  compliance?: {
    metrics?: unknown[]
    effectiveness?: unknown[]
    safeguards?: string[]
    warningItems?: unknown[]
  }
  carbon?: {
    metrics?: unknown[]
    sources?: unknown[]
    reductions?: unknown[]
  }
  monthly?: unknown
  timeline?: unknown[]
  gis?: {
    routePoints?: unknown[]
    routeSegments?: unknown[]
    sensitiveAreas?: unknown[]
  }
}

type WorkspaceSummary = {
  currentTodo: number
  pendingUpload: number
  pendingCorrection: number
  pendingSubmit: number
  underReview: number
  dueSoon: number
  completed: number
}

type UploadTask = {
  id: string
  name: string
  module: string
  moduleName: string
  cycle: string
  cycleType: string
  deadline: string
  deadlineDisplay: string
  progressCurrent: number
  progressTotal: number
  status: string
  nextStep: string
  assignee: string
  assigneeDept: string
  priorityCode: string
}

type DocumentsSummary = {
  documentTotal: number
  monthNew: number
  pendingArchive: number
  expiringSoon: number
}

type DocumentItem = {
  id: string
  documentName: string
  documentType: string
  module: string
  period: string
  version: string
  source: string
  relationCount: number
  validityStatus: string
  uploadedAt: string
}

type StatusCard = {
  label: string
  value: number
  unit: string
  color: string
}

type ReviewItem = {
  id: string
  taskId?: string
  taskName: string
  module: string
  moduleName: string
  submitTime: string
  status: string
  reviewer: string
  commentSummary: string
  nextStep: string
}

type ParseQueueItem = {
  id: string
  jobId?: number
  fileId?: number
  fileName: string
  size: string
  progress: number
  status: string
}

export type UploadFileResponse = {
  fileId: number
  fileCode: string
  originalName: string
  fileSize?: number
  storagePath?: string
  sha256Hash: string
  duplicateStatus: string
  matchedFileId?: number | null
  matchedDocumentId?: number | null
  parseStatus: string
}

export type ParseJobResponse = {
  jobId: number
  jobCode: string
  jobStatus: string
  parseSource?: string
  parseEngine?: string
  confidence?: number
  summary?: string
}

export type ParseJobDetail = {
  jobId: number
  jobCode: string
  fileId: number
  fileName: string
  jobStatus: string
  confidence: number
  startedAt: string
  finishedAt: string
  parseEngine?: string
  modelName?: string
  parseSource?: string
  summary?: string
}

export type ParseFieldItem = {
  id: number
  fieldKey: string
  fieldName: string
  fieldValue: string
  normalizedValue: string
  valueType: string
  confidence: number
  confirmStatus: string
  confirmedValue: string | null
}

export type MatchCandidateItem = {
  candidateId: number
  taskId: string
  taskName: string
  module: string
  matchScore: number
  matchReason: string
  reuseCount: number
  candidateStatus: string
}

export type ConfirmParseResponse = {
  documentId: number
  documentCode: string
  documentStatus: string
  linkedTaskCount: number
  linkedTasks?: {
    taskId: string
    taskName: string
    requirementId: string | null
    requirementName: string | null
    progress: {
      completed: number
      total: number
      missing: number
      abnormal: number
      canSubmit: boolean
    }
  }[]
}

export type DocumentDetailApi = {
  id: string
  documentCode: string
  documentName: string
  documentType: string
  module: string
  period: string
  version: string
  source: string
  relationCount: number
  validityStatus: string
  documentStatus: string
  confirmStatus: string
  responsibleUnit: string
  validStartDate: string | null
  validEndDate: string | null
  uploadedAt: string
  file: {
    fileId: number | null
    originalName: string
    fileExt: string | null
    mimeType: string | null
    fileSize: number | null
    fileSizeText: string
    sha256Hash: string | null
    uploadSource: string | null
    uploadTime: string | null
  }
  tags: string[]
  isUnique: boolean
}

export type DocumentVersionApi = {
  id: number | string
  documentId: string
  fileId?: number
  versionNo: string
  versionDesc: string
  changeType: string
  uploadedBy?: number
  uploadedByName: string
  uploadedAt: string
  isCurrent: boolean
}

export type DocumentRelationApi = {
  id: number | string
  documentId: string
  taskId: string
  taskName: string
  module: 'E' | 'S' | 'G'
  moduleName: string
  cycle: string
  status: string
  relationType: string
  relationStatus: string
  matchScore: number
  source: string
  referenceCount: number
  lastReference: string
}

export type ReviewDetailApi = {
  id: string
  taskId: string
  taskName: string
  module: string
  moduleName: string
  cycle: string
  status: string
  submitTime: string
  reviewer: string
  commentSummary: string
  nextStep: string
  rectifyDeadline?: string
  correctionDeadline?: string
}

export type ReviewTimelineApi = {
  id: number | string
  reviewId: string
  action: string
  operatorId?: number
  operatorName: string
  operatedAt: string
}

export type ReviewRequirementApi = {
  id: number | string
  reviewId: string
  requirementText: string
  deadline?: string
  status?: string
}

export type ReviewActionResponse = {
  ok: boolean
  reviewId: string
  taskId: string
  status: string
  taskStatus?: string
  message: string
  requirements?: string[]
}

export type TaskDetailApi = {
  task: UploadTask
  tabs: string[]
  documents: TaskDocumentApi[]
  linkedDocuments: LinkedDocumentApi[]
  validation: {
    completed: number
    missing: number
    abnormal: number
    canSubmit: boolean
  }
  validationIssues: ValidationIssueApi[]
  candidateDocuments: CandidateDocumentApi[]
  aiRecommendation?: {
    fileName: string
    matchRate: number
    text: string
  }
  aiTip?: string
  reviewTimeline: { time: string; action: string }[]
  reviewRecords: TaskReviewRecordApi[]
}

export type TaskDocumentApi = {
  id: string
  name: string
  required: boolean
  format: string
  status: string
  templateAvailable: boolean
}

export type LinkedDocumentApi = {
  relationId: number | string
  documentId: string
  documentName: string
  documentType: string
  period: string
  version: string
  validityStatus: string
  source: string
  relationType: string
  relationStatus: string
  matchScore: number
  linkedAt: string
  uploadedAt: string
}

export type ValidationIssueApi = {
  id: string
  documentRequirementId: string
  documentName: string
  issueType: string
  severity: string
  message: string
  canSubmit: boolean
}

export type CandidateDocumentApi = {
  id: string
  documentId?: string | null
  requirementId?: string | null
  name: string
  cycle: string
  unit: string
  linkCount: number
  matchRate: number
}

export type TaskReviewRecordApi = {
  id: number | string
  taskId: string
  taskName: string
  submitTime: string
  status: string
  reviewer: string
  commentSummary: string
  nextStep: string
}

export type TaskActionResponse = {
  ok: boolean
  taskId?: string
  status?: string
  message?: string
  reviewId?: string
  documentId?: string
  requirementId?: string | null
  requirementName?: string | null
  progress?: {
    completed: number
    total: number
    missing: number
    abnormal: number
    canSubmit: boolean
  }
  validation?: {
    completed: number
    missing: number
    abnormal: number
    canSubmit: boolean
  }
}
