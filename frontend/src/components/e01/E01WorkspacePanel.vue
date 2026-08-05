<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { getE01Events } from '@/services/api'
import type {
  E01BusinessCategory,
  E01CategoryFilter,
  E01EventsPayload,
  E01OpenPoint,
  E01PanelLayer,
  E01PointScope,
} from '@/types/e01'
import { isE01RiskPoint } from '@/utils/e01-points'
import { formatSectionLabel, typeWithSection } from '@/utils/section-label'

const props = defineProps<{
  selectedPointId: number | null
  layer: E01PanelLayer
  categoryFilter: E01CategoryFilter
  pointScope: E01PointScope
}>()

const emit = defineEmits<{
  close: []
  changeCategory: [category: E01CategoryFilter]
  changeScope: [scope: E01PointScope]
  selectPoint: [point: E01OpenPoint]
  clearSelection: []
  overviewReady: [points: E01OpenPoint[]]
}>()

/** Fit enlarged type without internal scrollbar on 1080p workbench right rail. */
const PAGE_SIZE = 3
const loading = ref(false)
const error = ref('')
const payload = ref<E01EventsPayload | null>(null)
const page = ref(1)

const overview = computed(() => payload.value?.overview || {
  totalOpenPoints: 0,
  waterCount: 0,
  airCount: 0,
  noiseCount: 0,
  monitorPointCount: 0,
  anomalyCount: 0,
  openCount: 0,
  riskLevel: '正常',
})

const openPoints = computed(() => payload.value?.openPoints || [])

const scopedPoints = computed(() => {
  if (props.pointScope === 'all') return openPoints.value
  return openPoints.value.filter(isE01RiskPoint)
})

const filteredPoints = computed(() => {
  const cat = props.categoryFilter
  if (cat === 'ALL') return scopedPoints.value
  return scopedPoints.value.filter((p) => p.monitorCategory === cat)
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredPoints.value.length / PAGE_SIZE)))

const pagedPoints = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return filteredPoints.value.slice(start, start + PAGE_SIZE)
})

const pagerSummary = computed(
  () => `共 ${filteredPoints.value.length} 处 · 第 ${page.value}/${totalPages.value} 页`,
)

const showPageControls = computed(() => filteredPoints.value.length > PAGE_SIZE)

const summaryTabs = computed(() => [
  {
    label: '监测点',
    value: overview.value.monitorPointCount ?? overview.value.totalOpenPoints,
    isText: false,
  },
  {
    label: '异常',
    value: overview.value.anomalyCount ?? overview.value.totalOpenPoints,
    isText: false,
  },
  {
    label: '未闭环',
    value: overview.value.openCount ?? overview.value.totalOpenPoints,
    isText: false,
  },
  {
    label: '风险等级',
    value: overview.value.riskLevel || '正常',
    isText: true,
  },
])

function categoryCount(key: E01BusinessCategory) {
  const base = openPoints.value.filter((p) => p.monitorCategory === key)
  const list = props.pointScope === 'all' ? base : base.filter(isE01RiskPoint)
  return list.length
}

const categoryTabs = computed(() => [
  { key: 'AIR' as const, label: '空气监测', value: categoryCount('AIR') },
  { key: 'WATER' as const, label: '水质监测', value: categoryCount('WATER') },
  { key: 'NOISE' as const, label: '噪声监测', value: categoryCount('NOISE') },
])

function riskLabel(point: E01OpenPoint) {
  const multi = primaryFactor(point)?.exceedMultiple
  if (multi != null && Number(multi) >= 1.5) return '红'
  if (multi != null && Number(multi) >= 1.2) return '黄'
  if (point.status && point.status !== '正常') return '蓝'
  return '正常'
}

function display(value: unknown) {
  if (value === null || value === undefined || value === '') return null
  return String(value)
}

function dateOnly(value?: string | null) {
  const text = display(value)
  if (!text) return '—'
  return text.slice(0, 10)
}

function sectionLabel(point: E01OpenPoint) {
  return formatSectionLabel(point.sectionCode || point.sectionName)
}

function typeLabel(point: E01OpenPoint) {
  const map: Record<string, string> = {
    WATER: '水质监测点',
    AIR: '扬尘监测点',
    NOISE: '噪声监测点',
  }
  return map[point.monitorCategory] || `${point.monitorCategoryLabel}监测点`
}

function typeLine(point: E01OpenPoint) {
  return typeWithSection(typeLabel(point), sectionLabel(point))
}

function factorNames(point: E01OpenPoint) {
  return point.factors.map((f) => f.factorName).filter(Boolean).join('/') || '—'
}

function primaryFactor(point: E01OpenPoint) {
  return point.factors[0] || null
}

function valueText(value: unknown, unit?: string | null) {
  const text = display(value)
  if (!text) return '—'
  return unit ? `${text} ${unit}` : text
}

function riskBrief(point: E01OpenPoint) {
  const factor = primaryFactor(point)
  if (factor?.exceedMultiple != null && Number(factor.exceedMultiple) > 1) {
    return `${factor.factorName || '指标'}超标`
  }
  if (point.status && point.status !== '正常') return point.status
  return '异常'
}

async function loadOverview() {
  loading.value = true
  error.value = ''
  try {
    const res = await getE01Events()
    if (!res || res.code !== 0 || !res.data) {
      error.value = 'E01 Demo 数据暂不可用，请检查服务后重试'
      payload.value = null
      emit('overviewReady', [])
      return
    }
    payload.value = res.data
    emit('overviewReady', res.data.openPoints || [])
  } catch {
    error.value = 'E01 数据加载失败，请稍后重试'
    payload.value = null
    emit('overviewReady', [])
  } finally {
    loading.value = false
  }
}

function handleScopeClick(scope: E01PointScope) {
  if (props.pointScope === scope) return
  page.value = 1
  emit('clearSelection')
  emit('changeScope', scope)
}

function handleCategoryClick(key: E01BusinessCategory) {
  page.value = 1
  emit('clearSelection')
  emit('changeCategory', key)
}

function handleSelectPoint(point: E01OpenPoint) {
  emit('selectPoint', point)
}

function goPage(next: number) {
  if (next < 1 || next > totalPages.value) return
  page.value = next
  emit('clearSelection')
}

watch(
  () => [props.categoryFilter, props.pointScope] as const,
  () => {
    page.value = 1
  },
)

watch(filteredPoints, (list) => {
  if (page.value > Math.max(1, Math.ceil(list.length / PAGE_SIZE))) {
    page.value = 1
  }
})

onMounted(() => {
  void loadOverview()
})

defineExpose({ reload: loadOverview, payload, openPoints })
</script>

<template>
  <aside class="e01-panel e01-panel--green">
    <header class="e01-head">
      <h2>环境风险预警</h2>
      <button type="button" class="e01-close" aria-label="关闭E01" @click="emit('close')">×</button>
    </header>

    <div v-if="loading" class="e01-state">正在加载…</div>
    <div v-else-if="error" class="e01-state is-error">
      {{ error }}
      <button type="button" class="e01-retry" @click="loadOverview">重试</button>
    </div>
    <template v-else>
      <section class="e01-stats" aria-label="环保风险摘要">
        <div
          v-for="tab in summaryTabs"
          :key="tab.label"
          class="e01-stats__cell is-static"
        >
          <span>{{ tab.label }}</span>
          <strong :class="{ 'is-text': tab.isText }">{{ tab.value }}</strong>
        </div>
      </section>

      <div class="e01-scope-row" role="tablist" aria-label="监测点范围">
        <button
          type="button"
          role="tab"
          :aria-selected="pointScope === 'risk'"
          class="e01-scope"
          :class="{ active: pointScope === 'risk' }"
          @click="handleScopeClick('risk')"
        >
          风险监测点
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="pointScope === 'all'"
          class="e01-scope"
          :class="{ active: pointScope === 'all' }"
          @click="handleScopeClick('all')"
        >
          全部监测点
        </button>
      </div>

      <div class="e01-cat-row" aria-label="环境监测业务分类">
        <button
          v-for="tab in categoryTabs"
          :key="tab.key"
          type="button"
          class="e01-cat"
          :class="{ active: categoryFilter === tab.key }"
          @click="handleCategoryClick(tab.key)"
        >
          <span class="e01-cat__label">{{ tab.label }}</span>
          <em>{{ tab.value }}</em>
        </button>
      </div>

      <div class="e01-body">
        <div class="e01-list-title">
          {{ pointScope === 'risk' ? '风险监测点列表' : '全部监测点列表' }}
        </div>
        <div class="e01-list">
          <button
            v-for="point in pagedPoints"
            :key="point.pointId"
            type="button"
            class="e01-row"
            :class="{ active: selectedPointId === point.pointId, 'no-locate': !point.canLocate }"
            @click="handleSelectPoint(point)"
          >
            <div class="e01-row__top">
              <span class="e01-row__type">{{ typeLine(point) }}</span>
              <em class="e01-row__status">{{ point.status }} · {{ riskLabel(point) }}</em>
            </div>
            <div class="e01-row__loc">
              <b v-if="point.pointCode">{{ point.pointCode }}</b>
              {{ point.locationText || point.pointName }}
            </div>
            <div class="e01-row__factor">
              <b>{{ factorNames(point) }}</b>
              <span>
                检测值
                <i>{{ valueText(primaryFactor(point)?.detectedValue, primaryFactor(point)?.unit) }}</i>
              </span>
              <span class="muted">
                标准 {{ valueText(primaryFactor(point)?.limitValue, primaryFactor(point)?.unit) }}
              </span>
              <span v-if="pointScope === 'risk'" class="e01-row__multi">{{ riskBrief(point) }}</span>
            </div>
            <div class="e01-row__foot">
              <span>{{ dateOnly(point.discoveredAt) }}</span>
              <span v-if="!point.canLocate" class="warn">无法定位</span>
            </div>
          </button>

          <p v-if="!pagedPoints.length" class="e01-empty">
            {{
              pointScope === 'risk'
                ? '当前分类暂无风险'
                : categoryFilter === 'ALL'
                  ? '暂无监测点'
                  : '当前分类暂无监测点'
            }}
          </p>
        </div>

        <nav class="e01-pager" aria-label="点位分页">
          <span class="e01-pager__summary">{{ pagerSummary }}</span>
          <div v-if="showPageControls" class="e01-pager__controls">
            <button type="button" :disabled="page <= 1" @click="goPage(page - 1)">上一页</button>
            <button
              v-for="n in totalPages"
              :key="n"
              type="button"
              :class="{ active: page === n }"
              @click="goPage(n)"
            >
              {{ n }}
            </button>
            <button type="button" :disabled="page >= totalPages" @click="goPage(page + 1)">下一页</button>
          </div>
        </nav>
      </div>
    </template>
  </aside>
</template>

<style scoped lang="scss">
.e01-panel {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 14px 14px 10px;
  border: 1px solid rgba(105, 227, 111, 0.35);
  border-radius: 8px;
  background: rgba(4, 25, 48, 0.96);
  color: #d7e6f5;
  overflow: hidden;
}

.e01-head {
  flex-shrink: 0;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;

  h2 {
    margin: 0;
    font-size: 22px;
    font-weight: 700;
    color: #f3f8ff;
    letter-spacing: 0.02em;
    &::after {
      content: '';
      display: inline-block;
      width: 9px;
      height: 9px;
      margin-left: 8px;
      border-radius: 50%;
      background: #69e36f;
      box-shadow: 0 0 0 3px rgba(105, 227, 111, 0.18);
      vertical-align: middle;
    }
  }
}

.e01-close {
  width: 30px;
  height: 30px;
  font-size: 18px;
  line-height: 1;
  border: 1px solid rgba(105, 227, 111, 0.35);
  background: rgba(8, 40, 69, 0.72);
  color: #f3f8ff;
  border-radius: 6px;
  cursor: pointer;
}

.e01-state {
  padding: 24px 8px;
  text-align: center;
  color: #8ba6c3;
  font-size: 13px;
  &.is-error { color: #ff9f2f; }
}

.e01-retry {
  display: block;
  margin: 10px auto 0;
  padding: 4px 14px;
  font-size: 13px;
  border: 1px solid rgba(105, 227, 111, 0.35);
  background: rgba(8, 40, 69, 0.72);
  color: #69e36f;
  border-radius: 4px;
  cursor: pointer;
}

.e01-stats {
  flex-shrink: 0;
  height: 64px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1px solid rgba(105, 227, 111, 0.22);
  border-radius: 6px;
  background: rgba(8, 40, 69, 0.4);
  margin-bottom: 10px;
  overflow: hidden;
}

.e01-stats__cell {
  border: 0;
  border-right: 1px solid rgba(105, 227, 111, 0.16);
  background: transparent;
  color: #8ba6c3;
  cursor: default;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  position: relative;

  &:last-child { border-right: 0; }

  span {
    font-size: 14px;
    line-height: 1.2;
  }

  strong {
    font-size: 26px;
    line-height: 1.05;
    font-family: Bahnschrift, "DIN Alternate", Arial, sans-serif;
    color: #69e36f;
    font-weight: 700;

    &.is-text {
      font-size: 18px;
      font-family: inherit;
    }
  }

  &.is-static {
    cursor: default;
  }
}

.e01-scope-row {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin-bottom: 10px;
}

.e01-scope {
  height: 36px;
  border: 1px solid rgba(105, 227, 111, 0.28);
  border-radius: 4px;
  background: rgba(8, 40, 69, 0.45);
  color: #8ba6c3;
  font-size: 15px;
  cursor: pointer;

  &.active {
    color: #69e36f;
    border-color: rgba(105, 227, 111, 0.75);
    background: rgba(105, 227, 111, 0.14);
    font-weight: 700;
  }
}

.e01-cat-row {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  margin-bottom: 10px;
}

.e01-cat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  min-height: 54px;
  border: 1px solid rgba(105, 227, 111, 0.28);
  border-radius: 4px;
  background: rgba(8, 40, 69, 0.45);
  color: #8ba6c3;
  font-size: 14px;
  padding: 7px 4px;
  cursor: pointer;

  em {
    font-style: normal;
    font-size: 20px;
    font-family: Bahnschrift, "DIN Alternate", Arial, sans-serif;
    font-weight: 700;
    color: #c3d4e8;
  }

  &.active {
    color: #69e36f;
    border-color: rgba(105, 227, 111, 0.7);
    background: rgba(105, 227, 111, 0.12);
    font-weight: 600;

    em { color: #69e36f; }
  }
}

.e01-cat__label {
  line-height: 1.2;
}

.e01-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.e01-list-title {
  flex-shrink: 0;
  margin-bottom: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #a8bfd6;
}

.e01-list {
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.e01-row {
  flex: 0 0 auto;
  width: 100%;
  text-align: left;
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 6px;
  background: rgba(8, 40, 69, 0.45);
  color: inherit;
  cursor: pointer;
  padding: 11px 10px 11px 12px;
  position: relative;

  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 8px;
    bottom: 8px;
    width: 2px;
    border-radius: 2px;
    background: transparent;
  }

  &:hover {
    border-color: rgba(105, 227, 111, 0.45);
    background: rgba(12, 52, 42, 0.35);
  }

  &.active {
    border-color: rgba(105, 227, 111, 0.7);
    background: rgba(24, 70, 48, 0.35);
    &::before { background: #69e36f; }
  }
}

.e01-row__top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.e01-row__type {
  font-size: 15px;
  color: #c3d4e8;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.e01-row__status {
  flex-shrink: 0;
  font-style: normal;
  font-size: 13px;
  color: #69e36f;
  border: 1px solid rgba(105, 227, 111, 0.45);
  border-radius: 3px;
  padding: 2px 7px;
  background: rgba(105, 227, 111, 0.08);
}

.e01-row__loc {
  margin-top: 5px;
  font-size: 17px;
  color: #e8f3ff;
  line-height: 1.35;

  b {
    margin-right: 6px;
    font-weight: 700;
    color: #69e36f;
  }
}

.e01-row__factor {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  align-items: baseline;
  font-size: 14px;
  color: #8ba6c3;

  b {
    font-size: 15px;
    font-weight: 600;
    color: #f3f8ff;
  }

  i {
    font-style: normal;
    color: #ff8f5a;
    font-weight: 700;
    font-size: 17px;
  }

  .muted { color: #7f95ad; font-size: 14px; }
}

.e01-row__multi {
  color: #ff8f5a;
  font-weight: 600;
  font-size: 13px;
  border: 1px solid rgba(255, 143, 90, 0.35);
  border-radius: 3px;
  padding: 0 6px;
  line-height: 20px;
}

.e01-row__foot {
  margin-top: 6px;
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #7f95ad;

  .warn { color: #ff9f2f; }
}

.e01-empty {
  margin: 24px 0 0;
  text-align: center;
  font-size: 14px;
  color: #8ba6c3;
}

.e01-pager {
  flex-shrink: 0;
  margin-top: 10px;
  min-height: 34px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.e01-pager__summary {
  font-size: 14px;
  color: #8ba6c3;
  white-space: nowrap;
}

.e01-pager__controls {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;

  button {
    min-width: 30px;
    height: 30px;
    padding: 0 8px;
    border: 1px solid rgba(105, 227, 111, 0.28);
    border-radius: 4px;
    background: rgba(8, 40, 69, 0.5);
    color: #8ba6c3;
    cursor: pointer;
    font-size: 14px;

    &.active {
      color: #69e36f;
      border-color: rgba(105, 227, 111, 0.7);
      background: rgba(105, 227, 111, 0.12);
    }

    &:disabled {
      opacity: 0.35;
      cursor: not-allowed;
    }
  }
}
</style>
