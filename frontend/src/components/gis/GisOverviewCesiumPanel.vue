<script setup lang="ts">
import { computed, defineAsyncComponent, onBeforeUnmount, ref, watch } from 'vue'
import { gisConfig } from '@/config/gis.config'
import PanelCard from '@/components/layout/PanelCard.vue'
import E01MapSummaryCard from '@/components/e01/E01MapSummaryCard.vue'
import E02MapSummaryCard from '@/components/e02/E02MapSummaryCard.vue'
import E03MapSummaryCard from '@/components/e03/E03MapSummaryCard.vue'
import S02MapSummaryCard from '@/components/s02/S02MapSummaryCard.vue'
import type { E01OpenPoint } from '@/types/e01'
import type { E02IssueItem, E02SpatialLink } from '@/types/e02'
import type { E03SpatialLink, E03WaterObjectItem } from '@/types/e03'
import type { S02RiskItem } from '@/types/s02'
import type { GisBusinessLinkOpenPayload } from '@/modules/traffic-gis-overview/types'

/** Class A GIS rows: id + spatialLinks (+ display fields for picker). */
type E02GisItem = Partial<E02IssueItem> & {
  id: number
  spatialLinks?: E02SpatialLink[]
  canLocate?: boolean
  title?: string
  objectName?: string
  status?: string
  riskStatus?: string
}
type E03GisItem = Partial<E03WaterObjectItem> & {
  id: number
  spatialLinks?: E03SpatialLink[]
  canLocate?: boolean
  title?: string
  objectName?: string
  status?: string
  riskStatus?: string
}

const props = defineProps<{
  e01Active?: boolean
  e01OpenPoints?: E01OpenPoint[]
  e01VisiblePoints?: E01OpenPoint[]
  e01SelectedPointId?: number | null
  e02Active?: boolean
  e02Issues?: E02GisItem[]
  e02SelectedIssueId?: number | null
  e03Active?: boolean
  e03Issues?: E03GisItem[]
  e03SelectedIssueId?: number | null
  s02Active?: boolean
  s02Risks?: S02RiskItem[]
  s02SelectedRiskId?: number | null
}>()

const emit = defineEmits<{
  openKpiSource: [payload: GisBusinessLinkOpenPayload]
  e01PointSelect: [pointId: number]
  e01ClearSelection: []
  e02IssueSelect: [issueId: number]
  e02ClearSelection: []
  e03IssueSelect: [issueId: number]
  e03ClearSelection: []
  s02RiskSelect: [riskId: number]
  s02ClearSelection: []
  openSpecialPlan: [risk: S02RiskItem]
}>()

const TrafficGisOverview = defineAsyncComponent(() =>
  import('@/modules/traffic-gis-overview').then((module) => module.TrafficGisOverview),
)

/** 交接包 TrafficGisOverview 仅暴露 flyToFeature / flyToSection / refreshLayer / resetView */
const mapRef = ref<{
  flyToFeature: (id: string) => void | Promise<void>
  flyToSection: (sectionId: string) => void | Promise<void>
  refreshLayer: (id: string) => void | Promise<void>
  resetView: () => void
} | null>(null)

/** 首页工作台进出时的相机态（交接包暂无 capture/restore，本地占位避免打断 KPI 流程） */
let savedMapState: unknown = null

const panelRootRef = ref<HTMLElement | null>(null)
const popoverAnchorRef = ref<HTMLElement | null>(null)
const featurePicker = ref<{ featureId: string; issues: E02GisItem[] } | null>(null)
const e03FeaturePicker = ref<{ featureId: string; issues: E03GisItem[] } | null>(null)
const s02FeaturePicker = ref<{ featureId: string; risks: S02RiskItem[] } | null>(null)

const selectedPoint = computed(() => {
  const id = props.e01SelectedPointId
  if (id == null) return null
  return (
    (props.e01VisiblePoints || []).find((p) => p.pointId === id)
    || (props.e01OpenPoints || []).find((p) => p.pointId === id)
    || null
  )
})

const selectedE02Issue = computed(() => {
  const id = props.e02SelectedIssueId
  if (id == null) return null
  return (props.e02Issues || []).find((i) => i.id === id) || null
})

const selectedE03Object = computed(() => {
  const id = props.e03SelectedIssueId
  if (id == null) return null
  return (props.e03Issues || []).find((i) => i.id === id) || null
})

const selectedS02Risk = computed(() => {
  const id = props.s02SelectedRiskId
  if (id == null) return null
  return (props.s02Risks || []).find((r) => r.id === id) || null
})

const e02SelectedFeatureId = computed(() => {
  if (!props.e02Active || props.e02SelectedIssueId == null) return null
  const issue = (props.e02Issues || []).find((i) => i.id === props.e02SelectedIssueId)
  const link = issue?.spatialLinks?.find((sl) => sl.isPrimary) || issue?.spatialLinks?.[0]
  return link?.featureId || null
})

const e03SelectedFeatureId = computed(() => {
  if (!props.e03Active || props.e03SelectedIssueId == null) return null
  const issue = (props.e03Issues || []).find((i) => i.id === props.e03SelectedIssueId)
  const link = issue?.spatialLinks?.find((sl) => sl.isPrimary) || issue?.spatialLinks?.[0]
  return link?.featureId || null
})

const s02SelectedFeatureId = computed(() => {
  if (!props.s02Active || props.s02SelectedRiskId == null) return null
  const risk = (props.s02Risks || []).find((r) => r.id === props.s02SelectedRiskId)
  const link = risk?.spatialLinks?.find((sl) => sl.isPrimary) || risk?.spatialLinks?.[0]
  return link?.featureId || null
})

function issuesForFeature(featureId: string): E02GisItem[] {
  return (props.e02Issues || []).filter((issue) =>
    (issue.spatialLinks || []).some((sl) => sl.featureId === featureId),
  )
}

function applySelectionVisual() {
  // 交接包 designOnly 地图暂不支持业务要素高亮；保留函数供 watch / @ready 调用。
}

function handleE02FeatureSelect(featureId: string) {
  const matched = issuesForFeature(featureId)
  if (!matched.length) {
    featurePicker.value = null
    return
  }
  if (matched.length === 1) {
    featurePicker.value = null
    emit('e02IssueSelect', matched[0].id)
    return
  }
  featurePicker.value = { featureId, issues: matched }
}

function pickIssueFromFeature(issueId: number) {
  featurePicker.value = null
  emit('e02IssueSelect', issueId)
}

function handleE02MapBlankClick() {
  featurePicker.value = null
  emit('e02ClearSelection')
}

function handleE02PopoverClose() {
  featurePicker.value = null
  emit('e02ClearSelection')
}

function e03IssuesForFeature(featureId: string): E03GisItem[] {
  return (props.e03Issues || []).filter((issue) =>
    (issue.spatialLinks || []).some((sl) => sl.featureId === featureId),
  )
}

function handleE03FeatureSelect(featureId: string) {
  if (!props.e03Active) return
  const matched = e03IssuesForFeature(featureId)
  if (!matched.length) {
    e03FeaturePicker.value = null
    return
  }
  if (matched.length === 1) {
    e03FeaturePicker.value = null
    emit('e03IssueSelect', matched[0].id)
    return
  }
  e03FeaturePicker.value = { featureId, issues: matched }
}

function pickE03IssueFromFeature(issueId: number) {
  e03FeaturePicker.value = null
  emit('e03IssueSelect', issueId)
}

function handleE03MapBlankClick() {
  e03FeaturePicker.value = null
  emit('e03ClearSelection')
}

function handleE03PopoverClose() {
  e03FeaturePicker.value = null
  emit('e03ClearSelection')
}

function risksForFeature(featureId: string): S02RiskItem[] {
  return (props.s02Risks || []).filter((risk) =>
    (risk.spatialLinks || []).some((sl) => sl.featureId === featureId),
  )
}

function handleS02FeatureSelect(featureId: string) {
  if (!props.s02Active) return
  const matched = risksForFeature(featureId)
  if (!matched.length) {
    s02FeaturePicker.value = null
    return
  }
  if (matched.length === 1) {
    s02FeaturePicker.value = null
    emit('s02RiskSelect', matched[0].id)
    return
  }
  s02FeaturePicker.value = { featureId, risks: matched }
}

function pickS02RiskFromFeature(riskId: number) {
  s02FeaturePicker.value = null
  emit('s02RiskSelect', riskId)
}

function handleS02MapBlankClick() {
  s02FeaturePicker.value = null
  emit('s02ClearSelection')
}

function handleS02SummaryClose() {
  s02FeaturePicker.value = null
  emit('s02ClearSelection')
}

function handleS02OpenSpecialPlan() {
  if (selectedS02Risk.value) {
    emit('openSpecialPlan', selectedS02Risk.value)
  }
}

function captureMapState() {
  // 交接包地图暂无相机态快照；占位记录避免工作台开关流程中断
  savedMapState = true
  return savedMapState
}

function restoreMapState() {
  if (!savedMapState) return
  mapRef.value?.resetView()
  savedMapState = null
}

function focusPoint(point: E01OpenPoint) {
  // designOnly 底图无业务点；若有关联设计要素 id 则尝试飞入
  const featureId = point.gisFeatureId
  if (featureId) void mapRef.value?.flyToFeature(featureId)
}

function fitPoints(points: E01OpenPoint[]) {
  const featureId = points.map((p) => p.gisFeatureId).find(Boolean)
  if (featureId) void mapRef.value?.flyToFeature(featureId)
}

function resetView() {
  mapRef.value?.resetView()
}

function focusE02Issue(issue: E02GisItem) {
  const primaryLink = issue.spatialLinks?.find((sl) => sl.isPrimary) || issue.spatialLinks?.[0]
  if (!primaryLink?.featureId) return
  void mapRef.value?.flyToFeature(primaryLink.featureId)
}

function fitE02Issues(issues: E02GisItem[]) {
  const featureIds = [
    ...new Set(
      issues
        .flatMap((i) => i.spatialLinks || [])
        .map((sl) => sl.featureId)
        .filter(Boolean),
    ),
  ]
  if (!featureIds.length) return
  void mapRef.value?.flyToFeature(featureIds[0])
}

function focusE03Issue(issue: E03GisItem) {
  const primaryLink = issue.spatialLinks?.find((sl) => sl.isPrimary) || issue.spatialLinks?.[0]
  if (!primaryLink?.featureId) return
  void mapRef.value?.flyToFeature(primaryLink.featureId)
}

function fitE03Issues(issues: E03GisItem[]) {
  const featureIds = [
    ...new Set(
      issues
        .flatMap((i) => i.spatialLinks || [])
        .map((sl) => sl.featureId)
        .filter(Boolean),
    ),
  ]
  if (!featureIds.length) return
  void mapRef.value?.flyToFeature(featureIds[0])
}

function focusS02Risk(risk: S02RiskItem) {
  const primaryLink = risk.spatialLinks?.find((sl) => sl.isPrimary) || risk.spatialLinks?.[0]
  if (!primaryLink?.featureId) return
  void mapRef.value?.flyToFeature(primaryLink.featureId)
}

function fitS02Risks(risks: S02RiskItem[]) {
  const featureIds = [
    ...new Set(
      risks
        .flatMap((r) => r.spatialLinks || [])
        .map((sl) => sl.featureId)
        .filter(Boolean),
    ),
  ]
  if (!featureIds.length) return
  void mapRef.value?.flyToFeature(featureIds[0])
}

watch(
  () => props.e01SelectedPointId,
  (id) => {
    if (!props.e01Active || id == null) return
    const point = (props.e01VisiblePoints || props.e01OpenPoints || []).find((item) => item.pointId === id)
    if (point) focusPoint(point)
  },
)

watch(
  () => [props.e02SelectedIssueId, props.e02Active, e02SelectedFeatureId.value] as const,
  () => {
    if (!props.e02Active) {
      featurePicker.value = null
      return
    }
    if (props.e02SelectedIssueId != null) {
      const issue = (props.e02Issues || []).find((item) => item.id === props.e02SelectedIssueId)
      if (issue) focusE02Issue(issue)
    } else {
      featurePicker.value = null
    }
    applySelectionVisual()
  },
)

watch(
  () => props.e02Issues,
  () => {
    if (props.e02Active) applySelectionVisual()
  },
  { deep: true },
)

watch(
  () => [props.e03SelectedIssueId, props.e03Active, e03SelectedFeatureId.value] as const,
  () => {
    if (!props.e03Active) {
      e03FeaturePicker.value = null
      return
    }
    if (props.e03SelectedIssueId != null) {
      const issue = (props.e03Issues || []).find((item) => item.id === props.e03SelectedIssueId)
      if (issue) focusE03Issue(issue)
    } else {
      e03FeaturePicker.value = null
    }
    applySelectionVisual()
  },
)

watch(
  () => props.e03Issues,
  () => {
    if (props.e03Active) applySelectionVisual()
  },
  { deep: true },
)

watch(
  () => [props.s02SelectedRiskId, props.s02Active, s02SelectedFeatureId.value] as const,
  () => {
    if (!props.s02Active) {
      s02FeaturePicker.value = null
      return
    }
    if (props.s02SelectedRiskId != null) {
      const risk = (props.s02Risks || []).find((item) => item.id === props.s02SelectedRiskId)
      if (risk) focusS02Risk(risk)
    } else {
      s02FeaturePicker.value = null
    }
    applySelectionVisual()
  },
)

watch(
  () => props.s02Risks,
  () => {
    if (props.s02Active) applySelectionVisual()
  },
  { deep: true },
)

onBeforeUnmount(() => {
  // designOnly 底图无业务高亮态需清理
})

defineExpose({
  captureMapState,
  restoreMapState,
  focusPoint,
  fitPoints,
  resetView,
  focusE02Issue,
  fitE02Issues,
  focusE03Issue,
  fitE03Issues,
  focusS02Risk,
  fitS02Risks,
})
</script>

<template>
  <PanelCard flush>
    <div ref="panelRootRef" class="dashboard-gis-cesium-panel">
      <TrafficGisOverview
        ref="mapRef"
        :project-id="gisConfig.projectId"
        :data-mode="gisConfig.dashboardDataMode"
        :show-legend="true"
        :show-mode-switch="false"
        :show-config-button="true"
        :interaction-enabled="true"
        :design-only="true"
        presentation-mode="dashboard"
        @open-kpi-source="(payload) => emit('openKpiSource', payload)"
        @ready="applySelectionVisual"
      />

      <div v-if="e01Active" class="e01-map-legend">
        <span><i class="open" />未闭环超标点</span>
        <span><i class="active" />当前选中</span>
      </div>

      <div v-if="e02Active" class="e02-map-legend">
        <span><i class="hint" />选中高亮本体对象 · 点空白取消</span>
      </div>

      <div v-if="e03Active" class="e03-map-legend">
        <span><i class="hint" />选中高亮本体对象 · 点空白取消</span>
      </div>

      <div v-if="s02Active" class="s02-map-legend">
        <span><i class="hint" />安全风险点高亮 · 点空白取消</span>
      </div>

      <E01MapSummaryCard
        :visible="Boolean(e01Active && selectedPoint)"
        :point="selectedPoint"
        @close="emit('e01ClearSelection')"
      />

      <E02MapSummaryCard
        :visible="Boolean(e02Active && selectedE02Issue)"
        :issue="(selectedE02Issue as any)"
        @close="emit('e02ClearSelection')"
      />

      <E03MapSummaryCard
        :visible="Boolean(e03Active && selectedE03Object)"
        :object="(selectedE03Object as any)"
        @close="emit('e03ClearSelection')"
      />

      <S02MapSummaryCard
        :visible="Boolean(s02Active && selectedS02Risk)"
        :risk="selectedS02Risk"
        @close="handleS02SummaryClose"
        @open-special-plan="handleS02OpenSpecialPlan"
      />

      <div ref="popoverAnchorRef" class="e02-popover-anchor">
        <!-- V1.0 Class A: details only via map summary cards; no duplicate L2 popover -->
      </div>

      <div v-if="featurePicker" class="e02-feature-picker">
        <div class="e02-feature-picker__title">该空间对象关联多条事项</div>
        <button
          v-for="issue in featurePicker.issues"
          :key="issue.id"
          type="button"
          class="e02-feature-picker__row"
          @click="pickIssueFromFeature(issue.id)"
        >
          <span class="e02-feature-picker__status">{{ issue.riskStatus || issue.status || '—' }}</span>
          <span class="e02-feature-picker__name">{{ issue.objectName || issue.title || `对象 #${issue.id}` }}</span>
        </button>
        <button type="button" class="e02-feature-picker__cancel" @click="featurePicker = null">取消</button>
      </div>

      <div v-if="e03FeaturePicker" class="e02-feature-picker is-e03">
        <div class="e02-feature-picker__title">该空间对象关联多条水土保持事项</div>
        <button
          v-for="issue in e03FeaturePicker.issues"
          :key="issue.id"
          type="button"
          class="e02-feature-picker__row"
          @click="pickE03IssueFromFeature(issue.id)"
        >
          <span class="e02-feature-picker__status">{{ issue.riskStatus || issue.status || '—' }}</span>
          <span class="e02-feature-picker__name">{{ issue.objectName || issue.title || `对象 #${issue.id}` }}</span>
        </button>
        <button type="button" class="e02-feature-picker__cancel" @click="e03FeaturePicker = null">取消</button>
      </div>

      <div v-if="s02FeaturePicker" class="e02-feature-picker is-s02">
        <div class="e02-feature-picker__title">该空间对象关联多条安全风险点</div>
        <button
          v-for="risk in s02FeaturePicker.risks"
          :key="risk.id"
          type="button"
          class="e02-feature-picker__row"
          @click="pickS02RiskFromFeature(risk.id)"
        >
          <span class="e02-feature-picker__status">{{ risk.riskLevel }}</span>
          <span class="e02-feature-picker__name">{{ risk.title }}</span>
        </button>
        <button type="button" class="e02-feature-picker__cancel" @click="s02FeaturePicker = null">取消</button>
      </div>
    </div>
  </PanelCard>
</template>

<style scoped>
.dashboard-gis-cesium-panel {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.e02-popover-anchor {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 28;
}

.e02-popover-anchor :deep(.e02-popover),
.e02-popover-anchor :deep(.e03-popover) {
  pointer-events: auto;
}

.e01-map-legend,
.e02-map-legend,
.e03-map-legend,
.s02-map-legend {
  position: absolute;
  left: 12px;
  bottom: 12px;
  z-index: 18;
  display: flex;
  gap: 12px;
  padding: 6px 10px;
  border-radius: 6px;
  background: rgba(4, 25, 48, 0.82);
  font-size: 11px;
  color: #c3d4e8;
}

.e01-map-legend {
  border: 1px solid rgba(255, 159, 47, 0.4);
}

.e02-map-legend {
  border: 1px solid rgba(105, 227, 111, 0.4);
}

.e03-map-legend {
  border: 1px solid rgba(79, 172, 254, 0.4);
}

.s02-map-legend {
  border: 1px solid rgba(47, 156, 255, 0.45);
}

.e01-map-legend i,
.e02-map-legend i,
.e03-map-legend i,
.s02-map-legend i {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 4px;
}

.e01-map-legend i.open { background: #ff9f2f; }
.e01-map-legend i.active {
  background: #ff9f2f;
  box-shadow: 0 0 0 3px rgba(255, 159, 47, 0.4);
}
.e02-map-legend i.hint { background: #69e36f; }
.e03-map-legend i.hint { background: #4facfe; }
.s02-map-legend i.hint { background: #2f9cff; }

.e02-feature-picker {
  position: absolute;
  left: 16px;
  top: 56px;
  z-index: 30;
  width: min(320px, calc(100% - 32px));
  padding: 10px;
  border-radius: 8px;
  border: 1px solid rgba(105, 227, 111, 0.4);
  background: rgba(4, 25, 48, 0.96);
  color: #d7e6f5;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
}

.e02-feature-picker__title {
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #69e36f;
}

.e02-feature-picker__row {
  display: flex;
  gap: 8px;
  width: 100%;
  text-align: left;
  margin-bottom: 6px;
  padding: 8px;
  border-radius: 6px;
  border: 1px solid rgba(105, 227, 111, 0.25);
  background: rgba(8, 40, 69, 0.72);
  color: #d7e6f5;
  cursor: pointer;
}

.e02-feature-picker__row:hover {
  border-color: rgba(105, 227, 111, 0.55);
}

.e02-feature-picker__status {
  flex-shrink: 0;
  font-size: 11px;
  color: #ff9f2f;
}

.e02-feature-picker__name {
  font-size: 12px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.e02-feature-picker.is-e03 {
  border-color: rgba(79, 172, 254, 0.4);
}

.e02-feature-picker.is-e03 .e02-feature-picker__title {
  color: #4facfe;
}

.e02-feature-picker.is-e03 .e02-feature-picker__row {
  border-color: rgba(79, 172, 254, 0.25);
}

.e02-feature-picker.is-e03 .e02-feature-picker__row:hover {
  border-color: rgba(79, 172, 254, 0.55);
}

.e02-feature-picker.is-s02 {
  border-color: rgba(47, 156, 255, 0.45);
}

.e02-feature-picker.is-s02 .e02-feature-picker__title {
  color: #2f9cff;
}

.e02-feature-picker.is-s02 .e02-feature-picker__row {
  border-color: rgba(47, 156, 255, 0.25);
}

.e02-feature-picker.is-s02 .e02-feature-picker__row:hover {
  border-color: rgba(47, 156, 255, 0.55);
}

.e02-feature-picker__cancel {
  margin-top: 4px;
  width: 100%;
  padding: 6px;
  font-size: 12px;
  border-radius: 4px;
  border: 1px solid rgba(139, 166, 195, 0.35);
  background: transparent;
  color: #8ba6c3;
  cursor: pointer;
}
</style>
