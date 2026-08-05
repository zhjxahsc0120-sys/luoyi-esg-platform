import { defineStore } from 'pinia'
import { ref } from 'vue'
import type {
  NavItem,
  KpiGroup,
  RoutePoint,
  RouteSegment,
  SensitiveArea,
  ComplianceMetric,
  EffectivenessItem,
  WarningListItem,
  CarbonSource,
  ReductionMeasure,
  MonthlyReport,
  TimelineStep,
} from '@/types/dashboard'
import type { MonthlyReadiness } from '@/types/monthly-report'
import type { EsgHomeStatus } from '@/types/esg-home'
import {
  navItems,
  kpiGroups,
  routePoints,
  routeSegments,
  sensitiveAreas,
  complianceMetrics,
  effectivenessItems,
  safeguardItems,
  warningListItems,
  carbonMetrics,
  carbonSources,
  reductionMeasures,
  monthlyReport,
  timelineSteps,
} from '@/data/dashboard.mock'
import { createMonthlyReadinessMock } from '@/data/monthly-readiness.mock'
import { getDashboardKpis, getDashboardPanels, getDashboardRiskWarnings, getEsgHomeStatus, getMonthlyReportReadiness } from '@/services/api'
import { validateMonthlyReadiness } from '@/utils/monthly-readiness'
import { applyKpiHomeCatalogLabels, mergeEsgHomeIntoKpiGroups } from '@/utils/esg-home'
import { mapDemoRiskToComplianceMetrics, mapDemoRiskToWarningItems } from '@/utils/esg-demo'

export const useDashboardStore = defineStore('dashboard', () => {
  const navs = ref<NavItem[]>(navItems)
  const kpis = ref<KpiGroup[]>(applyKpiHomeCatalogLabels(kpiGroups))
  const points = ref<RoutePoint[]>(routePoints)
  const segments = ref<RouteSegment[]>(routeSegments)
  const areas = ref<SensitiveArea[]>(sensitiveAreas)
  const compliance = ref<ComplianceMetric[]>(complianceMetrics)
  const effectiveness = ref<EffectivenessItem[]>(effectivenessItems)
  const safeguards = ref<string[]>(safeguardItems)
  const warningItems = ref<WarningListItem[]>(warningListItems)
  const carbon = ref(carbonMetrics)
  const carbonSrc = ref<CarbonSource[]>(carbonSources)
  const reductions = ref<ReductionMeasure[]>(reductionMeasures)
  const monthly = ref<MonthlyReport>(monthlyReport)
  const monthlyReadiness = ref<MonthlyReadiness>(createMonthlyReadinessMock())
  const monthlyReadinessError = ref<string | null>(null)
  const timeline = ref<TimelineStep[]>(timelineSteps)
  /** Phase A: last ESG home summary (api or mock fallback) */
  const esgHome = ref<EsgHomeStatus | null>(null)
  const esgHomeSource = ref<'api' | 'mock' | null>(null)
  const esgHomeLoadError = ref<string | null>(null)

  const activeLayers = ref<string[]>(['all', 'environment', 'risk'])

  async function loadKpis() {
    const data = await getDashboardKpis()
    if (data && data.groups && data.groups.length > 0) {
      kpis.value = applyKpiHomeCatalogLabels(data.groups as KpiGroup[])
    } else {
      kpis.value = applyKpiHomeCatalogLabels(kpiGroups)
    }
  }

  async function loadPanels() {
    const [data, risks] = await Promise.all([
      getDashboardPanels(),
      getDashboardRiskWarnings({ status: 'OPEN' }),
    ])
    if (risks?.items?.length) {
      warningItems.value = mapDemoRiskToWarningItems(risks)
      compliance.value = mapDemoRiskToComplianceMetrics(risks)
      effectiveness.value = compliance.value.slice(0, 3).map((m) => ({
        label: String(m.label).replace('预警', '').replace('提醒', ''),
        value: Number(m.value) || 0,
      }))
    }
    if (!data) return
    if (!risks?.items?.length) {
      if (data.compliance?.metrics) compliance.value = data.compliance.metrics as ComplianceMetric[]
      if (data.compliance?.effectiveness) effectiveness.value = data.compliance.effectiveness as EffectivenessItem[]
      if (data.compliance?.warningItems) warningItems.value = data.compliance.warningItems as WarningListItem[]
    }
    if (data.compliance?.safeguards) safeguards.value = data.compliance.safeguards
    if (data.carbon?.metrics) carbon.value = data.carbon.metrics as typeof carbonMetrics
    if (data.carbon?.sources) carbonSrc.value = data.carbon.sources as CarbonSource[]
    if (data.carbon?.reductions) reductions.value = data.carbon.reductions as ReductionMeasure[]
    if (data.monthly) monthly.value = data.monthly as MonthlyReport
    if (data.timeline) timeline.value = data.timeline as TimelineStep[]
    if (data.gis?.routePoints) points.value = data.gis.routePoints as RoutePoint[]
    if (data.gis?.routeSegments) segments.value = data.gis.routeSegments as RouteSegment[]
    if (data.gis?.sensitiveAreas) areas.value = data.gis.sensitiveAreas as SensitiveArea[]
  }

  /**
   * Phase A: load ESG homepage status via service layer.
   * Always ends with usable mock if HTTP fails; catalog labels always applied.
   */
  async function loadEsgHomeStatus() {
    try {
      const status = await getEsgHomeStatus()
      esgHome.value = status
      esgHomeSource.value = status.source
      esgHomeLoadError.value = status.source === 'mock' ? 'Demo API 未就绪，已使用前端 mock' : null

      if (status.kpiGroups?.length) {
        kpis.value = mergeEsgHomeIntoKpiGroups(status.kpiGroups, status)
      } else {
        kpis.value = mergeEsgHomeIntoKpiGroups(kpis.value, status)
      }

      if (status.complianceMetrics?.length) {
        compliance.value = status.complianceMetrics
      }
      if (status.effectiveness?.length) {
        effectiveness.value = status.effectiveness
      }
      if (status.safeguards?.length) {
        safeguards.value = status.safeguards
      }
      if (status.warningItems) {
        warningItems.value = status.warningItems
      }
    } catch (error) {
      esgHomeLoadError.value = error instanceof Error ? error.message : String(error)
      if (import.meta.env.DEV) {
        console.warn('[esg-home]', esgHomeLoadError.value)
      }
    }
  }

  async function loadMonthlyReadiness(reportPeriod = '2026-07') {
    try {
      const data = await getMonthlyReportReadiness(reportPeriod)
      if (!data) {
        throw new Error(`月报资料归集率接口请求失败：${reportPeriod}`)
      }

      const validationErrors = validateMonthlyReadiness(data)
      if (validationErrors.length > 0) {
        throw new Error(`月报资料归集率数据校验失败：${validationErrors.join('；')}`)
      }

      monthlyReadiness.value = data
      monthlyReadinessError.value = null
    } catch (error) {
      monthlyReadiness.value = createMonthlyReadinessMock()
      monthlyReadinessError.value = error instanceof Error ? error.message : String(error)
      if (import.meta.env.DEV) {
        console.warn('[monthly-readiness]', monthlyReadinessError.value)
      }
    }
  }

  function toggleLayer(layer: string) {
    const idx = activeLayers.value.indexOf(layer)
    if (idx > -1) {
      activeLayers.value.splice(idx, 1)
    } else {
      activeLayers.value.push(layer)
    }
  }

  async function bootstrapHome() {
    await Promise.all([loadKpis(), loadPanels()])
    await loadEsgHomeStatus()
  }

  void bootstrapHome()
  void loadMonthlyReadiness()

  return {
    navs,
    kpis,
    points,
    segments,
    areas,
    compliance,
    effectiveness,
    safeguards,
    warningItems,
    carbon,
    carbonSrc,
    reductions,
    monthly,
    monthlyReadiness,
    monthlyReadinessError,
    timeline,
    esgHome,
    esgHomeSource,
    esgHomeLoadError,
    activeLayers,
    toggleLayer,
    loadKpis,
    loadPanels,
    loadEsgHomeStatus,
    loadMonthlyReadiness,
    bootstrapHome,
  }
})
