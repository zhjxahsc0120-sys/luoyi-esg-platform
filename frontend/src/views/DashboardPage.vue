<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import type { KpiKey, KpiDetailConfig, KpiModalFocusContext } from '@/types/dashboard'
import type { E01CategoryFilter, E01OpenPoint, E01PanelLayer } from '@/types/e01'
import type { E02CategoryFilter, E02ObjectItem, E02PanelLayer } from '@/types/e02'
import type { E03CategoryFilter, E03EcoObjectItem, E03PanelLayer } from '@/types/e03'
import type { S02CategoryFilter, S02PanelLayer, S02RiskItem } from '@/types/s02'
import type { E04CulturalObjectItem, E04CulturalPanelLayer } from '@/types/e04-cultural'
import { kpiDetails, carbonTopicDetail, monthlyTopicDetail } from '@/data/dashboard.mock'
import { getDashboardKpiDetail, getDashboardTopic } from '@/services/api'
import HeaderNav from '@/components/layout/HeaderNav.vue'
import TopKpiGroups from '@/components/kpi/TopKpiGroups.vue'
import GisOverviewPanel from '@/components/gis/GisOverviewPanel.vue'
import GisOverviewCesiumPanel from '@/components/gis/GisOverviewCesiumPanel.vue'
import { gisConfig } from '@/config/gis.config'
import ComplianceRiskPanel from '@/components/panels/ComplianceRiskPanel.vue'
import CarbonBenefitPanel from '@/components/panels/CarbonBenefitPanel.vue'
import MonthlyReportPanel from '@/components/panels/MonthlyReportPanel.vue'
import ConstructionTimeline from '@/components/panels/ConstructionTimeline.vue'
import KpiDetailModal from '@/components/modal/KpiDetailModal.vue'
import E01WorkspacePanel from '@/components/e01/E01WorkspacePanel.vue'
import E02WorkspacePanel from '@/components/e02/E02WorkspacePanel.vue'
import E03WorkspacePanel from '@/components/e03/E03WorkspacePanel.vue'
import E04CulturalRelicWorkspacePanel from '@/components/e04/E04CulturalRelicWorkspacePanel.vue'
import S02WorkspacePanel from '@/components/s02/S02WorkspacePanel.vue'

const router = useRouter()

const SCREEN_WIDTH = 1920
const SCREEN_HEIGHT = 1080

const windowWidth = ref(SCREEN_WIDTH)
const windowHeight = ref(SCREEN_HEIGHT)

const scale = computed(() => {
  const scaleX = windowWidth.value / SCREEN_WIDTH
  const scaleY = windowHeight.value / SCREEN_HEIGHT
  return Math.min(scaleX, scaleY)
})

const translateX = computed(() => {
  const scaledWidth = SCREEN_WIDTH * scale.value
  return (windowWidth.value - scaledWidth) / 2
})

const translateY = computed(() => {
  const scaledHeight = SCREEN_HEIGHT * scale.value
  return (windowHeight.value - scaledHeight) / 2
})

function handleResize() {
  windowWidth.value = window.innerWidth
  windowHeight.value = window.innerHeight
}

const activeKpiKey = ref<KpiKey | null>(null)
const activeTopicDetail = ref<KpiDetailConfig | null>(null)
const apiKpiDetails = ref<Partial<Record<KpiKey, KpiDetailConfig>>>({})
const kpiFocusContext = ref<KpiModalFocusContext | null>(null)

const e01Active = ref(false)
const e01Layer = ref<E01PanelLayer>('overview')
const e01CategoryFilter = ref<E01CategoryFilter>('ALL')
const e01SelectedPointId = ref<number | null>(null)
const e01OpenPoints = ref<E01OpenPoint[]>([])

const e02Active = ref(false)
const e02Layer = ref<E02PanelLayer>('overview')
const e02CategoryFilter = ref<E02CategoryFilter>('ALL')
const e02SelectedIssueId = ref<number | null>(null)
const e02Issues = ref<E02ObjectItem[]>([])

const e03Active = ref(false)
const e03Layer = ref<E03PanelLayer>('overview')
const e03CategoryFilter = ref<E03CategoryFilter>('ALL')
const e03SelectedIssueId = ref<number | null>(null)
const e03Issues = ref<E03EcoObjectItem[]>([])

const s02Active = ref(false)
const s02Layer = ref<S02PanelLayer>('overview')
const s02CategoryFilter = ref<S02CategoryFilter>('ALL')
const s02SelectedRiskId = ref<number | null>(null)
const s02Risks = ref<S02RiskItem[]>([])
const s02PendingSelectCode = ref<string | null>(null)

const e04Active = ref(false)
const e04Layer = ref<E04CulturalPanelLayer>('overview')
const e04SelectedObjectId = ref<number | null>(null)
const e04Objects = ref<E04CulturalObjectItem[]>([])

const gisPanelRef = ref<{
  captureMapState: () => unknown
  restoreMapState: () => void
  focusPoint: (point: E01OpenPoint) => void
  fitPoints: (points: E01OpenPoint[]) => void
  resetView: () => void
  focusE02Issue: (issue: { spatialLinks?: E02ObjectItem['spatialLinks'] }) => void
  fitE02Issues: (issues: Array<{ spatialLinks?: E02ObjectItem['spatialLinks'] }>) => void
  focusE03Issue: (issue: { spatialLinks?: E03EcoObjectItem['spatialLinks'] }) => void
  fitE03Issues: (issues: Array<{ spatialLinks?: E03EcoObjectItem['spatialLinks'] }>) => void
  focusS02Risk: (risk: S02RiskItem) => void
  fitS02Risks: (risks: S02RiskItem[]) => void
} | null>(null)

const isKpiModalOpen = computed(
  () => !e01Active.value && !e02Active.value && !e03Active.value && !e04Active.value && !s02Active.value
    && (activeKpiKey.value !== null || activeTopicDetail.value !== null),
)
const activeDetail = computed(() => {
  if (activeTopicDetail.value) return activeTopicDetail.value
  if (activeKpiKey.value) return apiKpiDetails.value[activeKpiKey.value] || kpiDetails[activeKpiKey.value]
  return null
})

const e01VisiblePoints = computed(() => {
  if (e01CategoryFilter.value === 'ALL') return e01OpenPoints.value
  return e01OpenPoints.value.filter((p) => p.monitorCategory === e01CategoryFilter.value)
})

const e02VisibleIssues = computed(() => {
  if (e02CategoryFilter.value === 'ALL') return e02Issues.value
  return e02Issues.value.filter((i) => i.objectType === e02CategoryFilter.value)
})

const e03VisibleIssues = computed(() => {
  if (e03CategoryFilter.value === 'ALL') return e03Issues.value
  return e03Issues.value.filter((i) => i.objectKind === e03CategoryFilter.value)
})

const s02VisibleRisks = computed(() => {
  if (s02CategoryFilter.value === 'ALL') return s02Risks.value
  if (s02CategoryFilter.value === 'MAJOR') {
    return s02Risks.value.filter((r) => r.riskLevel === '重大')
  }
  return s02Risks.value.filter((r) => r.riskLevel === '较大')
})

let bodyOverflow = ''

function fitCurrentCategory() {
  nextTick(() => {
    gisPanelRef.value?.fitPoints(e01VisiblePoints.value)
  })
}

function fitCurrentE02Category() {
  nextTick(() => {
    gisPanelRef.value?.fitE02Issues(e02VisibleIssues.value)
  })
}

function fitCurrentE03Category() {
  nextTick(() => {
    gisPanelRef.value?.fitE03Issues(e03VisibleIssues.value)
  })
}

function fitCurrentS02Category() {
  nextTick(() => {
    gisPanelRef.value?.fitS02Risks(s02VisibleRisks.value)
  })
}

async function openE01Workspace() {
  if (e02Active.value) closeE02Workspace()
  if (e03Active.value) closeE03Workspace()
  if (e04Active.value) closeE04Workspace()
  if (s02Active.value) closeS02Workspace()
  if (!e01Active.value) {
    gisPanelRef.value?.captureMapState()
  }
  e01Active.value = true
  e01Layer.value = 'overview'
  e01CategoryFilter.value = 'ALL'
  e01SelectedPointId.value = null
  activeKpiKey.value = null
  activeTopicDetail.value = null
  kpiFocusContext.value = null
}

function closeE01Workspace() {
  e01Active.value = false
  e01Layer.value = 'overview'
  e01CategoryFilter.value = 'ALL'
  e01SelectedPointId.value = null
  e01OpenPoints.value = []
  gisPanelRef.value?.restoreMapState()
}

async function openE02Workspace() {
  if (e01Active.value) closeE01Workspace()
  if (e03Active.value) closeE03Workspace()
  if (e04Active.value) closeE04Workspace()
  if (s02Active.value) closeS02Workspace()
  if (!e02Active.value) {
    gisPanelRef.value?.captureMapState()
  }
  e02Active.value = true
  e02Layer.value = 'overview'
  e02CategoryFilter.value = 'ALL'
  e02SelectedIssueId.value = null
  activeKpiKey.value = null
  activeTopicDetail.value = null
  kpiFocusContext.value = null
}

function closeE02Workspace() {
  e02Active.value = false
  e02Layer.value = 'overview'
  e02CategoryFilter.value = 'ALL'
  e02SelectedIssueId.value = null
  e02Issues.value = []
  gisPanelRef.value?.restoreMapState()
}

async function openE03Workspace() {
  if (e01Active.value) closeE01Workspace()
  if (e02Active.value) closeE02Workspace()
  if (e04Active.value) closeE04Workspace()
  if (s02Active.value) closeS02Workspace()
  if (!e03Active.value) {
    gisPanelRef.value?.captureMapState()
  }
  e03Active.value = true
  e03Layer.value = 'overview'
  e03CategoryFilter.value = 'ALL'
  e03SelectedIssueId.value = null
  activeKpiKey.value = null
  activeTopicDetail.value = null
  kpiFocusContext.value = null
}

function closeE03Workspace() {
  e03Active.value = false
  e03Layer.value = 'overview'
  e03CategoryFilter.value = 'ALL'
  e03SelectedIssueId.value = null
  e03Issues.value = []
  gisPanelRef.value?.restoreMapState()
}

async function openE04Workspace(options?: { objectId?: number | null }) {
  if (e01Active.value) closeE01Workspace()
  if (e02Active.value) closeE02Workspace()
  if (e03Active.value) closeE03Workspace()
  if (s02Active.value) closeS02Workspace()
  if (!e04Active.value) {
    gisPanelRef.value?.captureMapState()
  }
  e04Active.value = true
  e04Layer.value = options?.objectId != null ? 'detail' : 'overview'
  e04SelectedObjectId.value = options?.objectId ?? null
  activeKpiKey.value = null
  activeTopicDetail.value = null
  kpiFocusContext.value = null
}

function closeE04Workspace() {
  e04Active.value = false
  e04Layer.value = 'overview'
  e04SelectedObjectId.value = null
  e04Objects.value = []
  gisPanelRef.value?.restoreMapState()
}

function handleE04OverviewReady(objects: E04CulturalObjectItem[]) {
  e04Objects.value = objects
  e04SelectedObjectId.value = null
}

function handleE04SelectObject(item: E04CulturalObjectItem) {
  if (e04SelectedObjectId.value === item.id) {
    handleE04ClearSelection()
    return
  }
  e04Layer.value = 'detail'
  e04SelectedObjectId.value = item.id
}

function handleE04ClearSelection() {
  e04SelectedObjectId.value = null
  e04Layer.value = 'overview'
}

async function openS02Workspace(options?: { sourceId?: string | null }) {
  if (e01Active.value) closeE01Workspace()
  if (e02Active.value) closeE02Workspace()
  if (e03Active.value) closeE03Workspace()
  if (e04Active.value) closeE04Workspace()
  if (!s02Active.value) {
    gisPanelRef.value?.captureMapState()
  }
  s02Active.value = true
  s02Layer.value = 'overview'
  s02CategoryFilter.value = 'ALL'
  s02SelectedRiskId.value = null
  s02PendingSelectCode.value = options?.sourceId || null
  activeKpiKey.value = null
  activeTopicDetail.value = null
  kpiFocusContext.value = null
}

function closeS02Workspace() {
  s02Active.value = false
  s02Layer.value = 'overview'
  s02CategoryFilter.value = 'ALL'
  s02SelectedRiskId.value = null
  s02Risks.value = []
  s02PendingSelectCode.value = null
  gisPanelRef.value?.restoreMapState()
}

function handleE03OverviewReady(issues: E03EcoObjectItem[]) {
  e03Issues.value = issues
  e03SelectedIssueId.value = null
  fitCurrentE03Category()
}

function handleE03ChangeCategory(category: E03CategoryFilter) {
  e03CategoryFilter.value = category
  e03SelectedIssueId.value = null
  e03Layer.value = 'overview'
  fitCurrentE03Category()
}

function handleE03SelectIssue(issue: E03EcoObjectItem) {
  if (e03SelectedIssueId.value === issue.id) {
    handleE03ClearSelection()
    return
  }
  e03Layer.value = 'detail'
  e03SelectedIssueId.value = issue.id
  if (issue.canLocate) {
    gisPanelRef.value?.focusE03Issue(issue)
  }
}

function handleE03IssueSelectFromMap(issueId: number) {
  const issue = e03VisibleIssues.value.find((item) => item.id === issueId)
    || e03Issues.value.find((item) => item.id === issueId)
  if (issue) handleE03SelectIssue(issue)
}

function handleE03ClearSelection() {
  e03SelectedIssueId.value = null
  e03Layer.value = 'overview'
}

function handleE02OverviewReady(issues: E02ObjectItem[]) {
  e02Issues.value = issues
  e02SelectedIssueId.value = null
  fitCurrentE02Category()
}

function handleE02ChangeCategory(category: E02CategoryFilter) {
  e02CategoryFilter.value = category
  e02SelectedIssueId.value = null
  e02Layer.value = 'overview'
  fitCurrentE02Category()
}

function handleE02SelectIssue(issue: E02ObjectItem) {
  if (e02SelectedIssueId.value === issue.id) {
    handleE02ClearSelection()
    return
  }
  e02Layer.value = 'detail'
  e02SelectedIssueId.value = issue.id
  if (issue.canLocate) {
    gisPanelRef.value?.focusE02Issue(issue)
  }
}

function handleE02IssueSelectFromMap(issueId: number) {
  const issue = e02VisibleIssues.value.find((item) => item.id === issueId)
    || e02Issues.value.find((item) => item.id === issueId)
  if (issue) handleE02SelectIssue(issue)
}

function handleE02ClearSelection() {
  e02SelectedIssueId.value = null
  e02Layer.value = 'overview'
}

function handleS02OverviewReady(risks: S02RiskItem[]) {
  s02Risks.value = risks
  s02SelectedRiskId.value = null
  fitCurrentS02Category()
  const pending = s02PendingSelectCode.value
  if (pending) {
    s02PendingSelectCode.value = null
    const matched = risks.find((r) => r.businessCode === pending)
      || risks.find((r) => String(r.id) === pending)
    if (matched) handleS02SelectRisk(matched)
  }
}

function handleS02ChangeCategory(category: S02CategoryFilter) {
  s02CategoryFilter.value = category
  s02SelectedRiskId.value = null
  s02Layer.value = 'overview'
  fitCurrentS02Category()
}

function handleS02SelectRisk(risk: S02RiskItem) {
  if (s02SelectedRiskId.value === risk.id) {
    handleS02ClearSelection()
    return
  }
  s02Layer.value = 'overview'
  s02SelectedRiskId.value = risk.id
  if (risk.canLocate) {
    gisPanelRef.value?.focusS02Risk(risk)
  }
}

function handleS02RiskSelectFromMap(riskId: number) {
  const risk = s02VisibleRisks.value.find((item) => item.id === riskId)
    || s02Risks.value.find((item) => item.id === riskId)
  if (risk) handleS02SelectRisk(risk)
}

function handleS02ClearSelection() {
  s02SelectedRiskId.value = null
  s02Layer.value = 'overview'
}

function handleE01OverviewReady(points: E01OpenPoint[]) {
  e01OpenPoints.value = points
  e01SelectedPointId.value = null
  fitCurrentCategory()
}

function handleE01ChangeCategory(category: E01CategoryFilter) {
  const same = e01CategoryFilter.value === category
  e01CategoryFilter.value = category
  e01SelectedPointId.value = null
  e01Layer.value = 'overview'
  if (same) {
    fitCurrentCategory()
  } else {
    fitCurrentCategory()
  }
}

function handleE01SelectPoint(point: E01OpenPoint) {
  if (e01SelectedPointId.value === point.pointId) {
    handleE01ClearSelection()
    return
  }
  e01Layer.value = 'overview'
  e01SelectedPointId.value = point.pointId
  if (point.canLocate) {
    gisPanelRef.value?.focusPoint(point)
  }
}

function handleE01PointSelectFromMap(pointId: number) {
  const point = e01VisiblePoints.value.find((item) => item.pointId === pointId)
    || e01OpenPoints.value.find((item) => item.pointId === pointId)
  if (point) handleE01SelectPoint(point)
}

function handleE01ClearSelection() {
  e01SelectedPointId.value = null
  e01Layer.value = 'overview'
  fitCurrentCategory()
}

async function handleKpiSelect(key: string) {
  const kpiKey = key as KpiKey
  if (kpiKey === 'E01') {
    await openE01Workspace()
    return
  }
  if (kpiKey === 'E02') {
    await openE02Workspace()
    return
  }
  if (kpiKey === 'E03') {
    await openE03Workspace()
    return
  }
  if (kpiKey === 'E04') {
    await openE04Workspace()
    return
  }
  if (kpiKey === 'S02') {
    await openS02Workspace()
    return
  }
  if (e01Active.value) closeE01Workspace()
  if (e02Active.value) closeE02Workspace()
  if (e03Active.value) closeE03Workspace()
  if (e04Active.value) closeE04Workspace()
  if (s02Active.value) closeS02Workspace()
  if (kpiDetails[kpiKey]) {
    if (kpiKey !== 'S01') {
      const detail = await getDashboardKpiDetail(kpiKey)
      if (detail) {
        apiKpiDetails.value[kpiKey] = detail
      } else {
        // B2-fix: API 失败时写入 loadError 错误壳
        const base = kpiDetails[kpiKey]
        apiKpiDetails.value[kpiKey] = { ...base, loadError: true } as KpiDetailConfig
      }
    }
    kpiFocusContext.value = null
    activeKpiKey.value = kpiKey
    activeTopicDetail.value = null
    lockBodyScroll()
  }
}

/** Risk list click: navigate by kpiKey + objectId only (contract). */
async function handleRiskWarningSelect(payload: { kpiKey: string; objectId: number | null }) {
  const kpiKey = payload.kpiKey as KpiKey
  const objectId = payload.objectId
  if (!kpiKey) return

  if (kpiKey === 'E01') {
    await openE01Workspace()
    return
  }
  if (kpiKey === 'E02') {
    await openE02Workspace()
    return
  }
  if (kpiKey === 'E03') {
    await openE03Workspace()
    return
  }
  if (kpiKey === 'E04') {
    await openE04Workspace({ objectId })
    return
  }
  if (kpiKey === 'S02') {
    await openS02Workspace({ sourceId: objectId != null ? String(objectId) : null })
    return
  }

  // Modal KPIs: open detail and pass object focus via focusContext
  if (e01Active.value) closeE01Workspace()
  if (e02Active.value) closeE02Workspace()
  if (e03Active.value) closeE03Workspace()
  if (e04Active.value) closeE04Workspace()
  if (s02Active.value) closeS02Workspace()
  if (kpiDetails[kpiKey] || ['G02', 'G03', 'G04', 'S01', 'S03', 'S04', 'G01'].includes(kpiKey)) {
    if (kpiKey !== 'S01') {
      const detail = await getDashboardKpiDetail(kpiKey)
      if (detail) {
        apiKpiDetails.value[kpiKey] = detail
      } else if (kpiDetails[kpiKey]) {
        apiKpiDetails.value[kpiKey] = { ...kpiDetails[kpiKey], loadError: true } as KpiDetailConfig
      }
    }
    kpiFocusContext.value = {
      sourceId: objectId != null ? String(objectId) : undefined,
      from: 'dashboard',
      title: `${kpiKey} 风险对象`,
    }
    activeKpiKey.value = kpiKey
    activeTopicDetail.value = null
    lockBodyScroll()
  }
}

async function handleRetryKpi() {
  const kpiKey = activeKpiKey.value
  if (!kpiKey || kpiKey === 'S01') return
  const detail = await getDashboardKpiDetail(kpiKey)
  if (detail) {
    apiKpiDetails.value[kpiKey] = detail
  } else {
    // B2-fix: 重试仍失败，保持错误态
    const existing = apiKpiDetails.value[kpiKey] || kpiDetails[kpiKey]
    if (existing) {
      apiKpiDetails.value[kpiKey] = { ...existing, loadError: true } as KpiDetailConfig
    }
  }
}

async function openKpiFromBusinessLink(payload: {
  targetType: 'E02' | 'E03' | 'S02'
  sourceId: string
  sourceTable?: string
  gisFeatureId?: string
  title?: string
}) {
  if (e01Active.value) closeE01Workspace()
  if (e02Active.value) closeE02Workspace()
  if (e03Active.value) closeE03Workspace()
  if (e04Active.value) closeE04Workspace()
  if (s02Active.value) closeS02Workspace()
  const kpiKey = payload.targetType as KpiKey
  if (kpiKey === 'E02') {
    await openE02Workspace()
    return
  }
  if (kpiKey === 'E03') {
    await openE03Workspace()
    return
  }
  if (kpiKey === 'S02') {
    await openS02Workspace({ sourceId: payload.sourceId })
    return
  }
  if (!kpiDetails[kpiKey]) return
  if (kpiKey !== 'S01') {
    const detail = await getDashboardKpiDetail(kpiKey)
    if (detail) {
      apiKpiDetails.value[kpiKey] = detail
    }
  }
  kpiFocusContext.value = {
    sourceId: payload.sourceId,
    sourceTable: payload.sourceTable,
    gisFeatureId: payload.gisFeatureId,
    from: 'gis',
    title: payload.title,
  }
  activeKpiKey.value = kpiKey
  activeTopicDetail.value = null
  lockBodyScroll()
}

async function handleTopicSelect(topicKey: string) {
  if (e01Active.value) closeE01Workspace()
  if (e02Active.value) closeE02Workspace()
  if (e03Active.value) closeE03Workspace()
  if (e04Active.value) closeE04Workspace()
  if (s02Active.value) closeS02Workspace()
  if (topicKey === 'CARBON') {
    activeTopicDetail.value = await getDashboardTopic('carbon') || carbonTopicDetail
  } else if (topicKey === 'MONTHLY') {
    activeTopicDetail.value = await getDashboardTopic('monthly-report') || monthlyTopicDetail
  } else {
    return
  }
  kpiFocusContext.value = null
  activeKpiKey.value = null
  lockBodyScroll()
}

function handleNavClick(key: string) {
  if (key === 'dashboard') {
    // already here
  } else if (key === 'assistant') {
    if (e01Active.value) closeE01Workspace()
    if (e02Active.value) closeE02Workspace()
    if (e03Active.value) closeE03Workspace()
    if (e04Active.value) closeE04Workspace()
    if (s02Active.value) closeS02Workspace()
    router.push('/assistant')
  } else if (key === 'workspace') {
    if (e01Active.value) closeE01Workspace()
    if (e02Active.value) closeE02Workspace()
    if (e03Active.value) closeE03Workspace()
    if (e04Active.value) closeE04Workspace()
    if (s02Active.value) closeS02Workspace()
    router.push('/workspace')
  }
}

function handleCloseModal() {
  activeKpiKey.value = null
  activeTopicDetail.value = null
  kpiFocusContext.value = null
  unlockBodyScroll()
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    if (e01Active.value) {
      if (e01SelectedPointId.value != null) {
        handleE01ClearSelection()
      } else {
        closeE01Workspace()
      }
      return
    }
    if (e02Active.value) {
      if (e02SelectedIssueId.value != null) {
        handleE02ClearSelection()
      } else {
        closeE02Workspace()
      }
      return
    }
    if (e03Active.value) {
      if (e03SelectedIssueId.value != null) {
        handleE03ClearSelection()
      } else {
        closeE03Workspace()
      }
      return
    }
    if (s02Active.value) {
      if (s02SelectedRiskId.value != null) {
        handleS02ClearSelection()
      } else {
        closeS02Workspace()
      }
      return
    }
    if (e04Active.value) {
      if (e04SelectedObjectId.value != null) {
        handleE04ClearSelection()
      } else {
        closeE04Workspace()
      }
      return
    }
    if (isKpiModalOpen.value) handleCloseModal()
  }
}

function lockBodyScroll() {
  bodyOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
}

function unlockBodyScroll() {
  document.body.style.overflow = bodyOverflow
}

watch(e01Active, (active) => {
  if (active) lockBodyScroll()
  else if (!e02Active.value && !e03Active.value && !s02Active.value) unlockBodyScroll()
})

watch(e02Active, (active) => {
  if (active) lockBodyScroll()
  else if (!e01Active.value && !e03Active.value && !s02Active.value) unlockBodyScroll()
})

watch(e03Active, (active) => {
  if (active) lockBodyScroll()
  else if (!e01Active.value && !e02Active.value && !s02Active.value) unlockBodyScroll()
})

watch(s02Active, (active) => {
  if (active) lockBodyScroll()
  else if (!e01Active.value && !e02Active.value && !e03Active.value) unlockBodyScroll()
})

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleKeydown)
  if (isKpiModalOpen.value || e01Active.value || e02Active.value || e03Active.value || s02Active.value) {
    unlockBodyScroll()
  }
})
</script>

<template>
  <div class="screen-wrapper">
    <div
      class="screen-canvas"
      :style="{
        transform: `translate(${translateX}px, ${translateY}px) scale(${scale})`,
      }"
    >
      <div class="dashboard-page" :class="{ 'is-e01-mode': e01Active, 'is-e02-mode': e02Active, 'is-e03-mode': e03Active, 'is-s02-mode': s02Active }">
        <div class="dashboard-header">
          <HeaderNav active-key="dashboard" @navigate="handleNavClick" />
        </div>
        <div class="dashboard-body" :class="{ 'is-e01-mode': e01Active, 'is-e02-mode': e02Active, 'is-e03-mode': e03Active, 'is-s02-mode': s02Active }">
          <div class="dashboard-left">
            <div class="dashboard-kpi">
              <TopKpiGroups :group-keys="['E', 'S']" @select="handleKpiSelect" />
            </div>
            <div class="dashboard-gis">
              <GisOverviewCesiumPanel
                v-if="gisConfig.useRealGisOnDashboard"
                ref="gisPanelRef"
                :e01-active="e01Active"
                :e01-open-points="e01OpenPoints"
                :e01-visible-points="e01VisiblePoints"
                :e01-selected-point-id="e01SelectedPointId"
                :e02-active="e02Active"
                :e02-issues="e02Issues"
                :e02-selected-issue-id="e02SelectedIssueId"
                :e03-active="e03Active"
                :e03-issues="e03Issues"
                :e03-selected-issue-id="e03SelectedIssueId"
                :s02-active="s02Active"
                :s02-risks="s02Risks"
                :s02-selected-risk-id="s02SelectedRiskId"
                @open-kpi-source="openKpiFromBusinessLink"
                @e01-point-select="handleE01PointSelectFromMap"
                @e01-clear-selection="handleE01ClearSelection"
                @e02-issue-select="handleE02IssueSelectFromMap"
                @e02-clear-selection="handleE02ClearSelection"
                @e03-issue-select="handleE03IssueSelectFromMap"
                @e03-clear-selection="handleE03ClearSelection"
                @s02-risk-select="handleS02RiskSelectFromMap"
                @s02-clear-selection="handleS02ClearSelection"
              />
              <GisOverviewPanel v-else />
            </div>
            <div class="dashboard-timeline">
              <ConstructionTimeline />
            </div>
          </div>
          <div class="dashboard-right" :class="{ 'is-e01-workspace': e01Active, 'is-e02-workspace': e02Active, 'is-e03-workspace': e03Active, 'is-e04-workspace': e04Active, 'is-s02-workspace': s02Active }">
            <div class="dashboard-kpi">
              <TopKpiGroups :group-keys="['G']" @select="handleKpiSelect" />
            </div>
            <div class="dashboard-e01-slot">
              <E01WorkspacePanel
                v-if="e01Active"
                :selected-point-id="e01SelectedPointId"
                :layer="e01Layer"
                :category-filter="e01CategoryFilter"
                @close="closeE01Workspace"
                @change-category="handleE01ChangeCategory"
                @select-point="handleE01SelectPoint"
                @clear-selection="handleE01ClearSelection"
                @overview-ready="handleE01OverviewReady"
              />
              <E02WorkspacePanel
                v-else-if="e02Active"
                :selected-issue-id="e02SelectedIssueId"
                :layer="e02Layer"
                :category-filter="e02CategoryFilter"
                @close="closeE02Workspace"
                @change-category="handleE02ChangeCategory"
                @select-issue="handleE02SelectIssue"
                @clear-selection="handleE02ClearSelection"
                @overview-ready="handleE02OverviewReady"
              />
              <E03WorkspacePanel
                v-else-if="e03Active"
                :selected-issue-id="e03SelectedIssueId"
                :layer="e03Layer"
                :category-filter="e03CategoryFilter"
                @close="closeE03Workspace"
                @change-category="handleE03ChangeCategory"
                @select-issue="handleE03SelectIssue"
                @clear-selection="handleE03ClearSelection"
                @overview-ready="handleE03OverviewReady"
              />
              <E04CulturalRelicWorkspacePanel
                v-else-if="e04Active"
                :selected-object-id="e04SelectedObjectId"
                :layer="e04Layer"
                @close="closeE04Workspace"
                @select-object="handleE04SelectObject"
                @clear-selection="handleE04ClearSelection"
                @overview-ready="handleE04OverviewReady"
              />
              <S02WorkspacePanel
                v-else-if="s02Active"
                :selected-risk-id="s02SelectedRiskId"
                :layer="s02Layer"
                :category-filter="s02CategoryFilter"
                @close="closeS02Workspace"
                @change-category="handleS02ChangeCategory"
                @select-risk="handleS02SelectRisk"
                @clear-selection="handleS02ClearSelection"
                @overview-ready="handleS02OverviewReady"
              />
              <template v-else>
                <div class="dashboard-compliance">
                  <ComplianceRiskPanel @select-warning="handleRiskWarningSelect" />
                </div>
                <div class="dashboard-carbon" style="cursor: pointer;" @click="handleTopicSelect('CARBON')">
                  <CarbonBenefitPanel />
                </div>
                <div class="dashboard-monthly" style="cursor: pointer;" @click="handleTopicSelect('MONTHLY')">
                  <MonthlyReportPanel />
                </div>
              </template>
            </div>
          </div>
        </div>

        <Teleport to="body">
          <KpiDetailModal
            v-if="isKpiModalOpen && activeDetail"
            :detail="activeDetail"
            :focus-context="kpiFocusContext"
            @close="handleCloseModal"
            @retry="handleRetryKpi"
          />
        </Teleport>
      </div>
    </div>
  </div>
</template>

<style scoped>
.screen-wrapper {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at 18% 12%, rgba(0, 174, 255, 0.05) 0%, transparent 30%),
    radial-gradient(circle at 85% 88%, rgba(166, 108, 255, 0.04) 0%, transparent 30%),
    #020b18;
}

.screen-canvas {
  width: 1920px;
  height: 1080px;
  transform-origin: top left;
  will-change: transform;
}

.dashboard-page {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>
