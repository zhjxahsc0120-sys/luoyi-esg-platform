<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { getE01EventDetail, getE01Events } from '@/services/api'
import type {
  E01CategoryFilter,
  E01EventDetail,
  E01EventsPayload,
  E01OpenPoint,
  E01PanelLayer,
} from '@/types/e01'
import { formatSectionLabel, typeWithSection } from '@/utils/section-label'

const props = defineProps<{
  selectedPointId: number | null
  layer: E01PanelLayer
  categoryFilter: E01CategoryFilter
}>()

const emit = defineEmits<{
  close: []
  changeCategory: [category: E01CategoryFilter]
  selectPoint: [point: E01OpenPoint]
  clearSelection: []
  overviewReady: [points: E01OpenPoint[]]
}>()

const PAGE_SIZE = 3
const loading = ref(false)
const error = ref('')
const payload = ref<E01EventsPayload | null>(null)
const page = ref(1)
const detail = ref<E01EventDetail | null>(null)
const detailLoading = ref(false)

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

const filteredPoints = computed(() => {
  if (props.categoryFilter === 'ALL') return openPoints.value
  return openPoints.value.filter((p) => p.monitorCategory === props.categoryFilter)
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

const selectedPoint = computed(() => {
  if (props.selectedPointId == null) return null
  return openPoints.value.find((p) => p.pointId === props.selectedPointId) || null
})

/** Phase B 顶部：监测点 / 异常 / 未闭环 / 风险等级；分类筛选保留在列表标题旁 */
const summaryTabs = computed(() => [
  {
    key: 'ALL' as const,
    label: '监测点',
    value: overview.value.monitorPointCount ?? overview.value.totalOpenPoints,
    filterable: true,
  },
  {
    key: 'ALL' as const,
    label: '异常',
    value: overview.value.anomalyCount ?? overview.value.totalOpenPoints,
    filterable: false,
  },
  {
    key: 'ALL' as const,
    label: '未闭环',
    value: overview.value.openCount ?? overview.value.totalOpenPoints,
    filterable: false,
  },
  {
    key: null,
    label: '风险等级',
    value: overview.value.riskLevel || '正常',
    filterable: false,
    isText: true,
  },
])

const categoryTabs = computed(() => [
  { key: 'ALL' as const, label: '全部', value: overview.value.totalOpenPoints },
  { key: 'WATER' as const, label: '水质', value: overview.value.waterCount },
  { key: 'AIR' as const, label: '空气', value: overview.value.airCount },
  { key: 'NOISE' as const, label: '噪声', value: overview.value.noiseCount },
])

function riskLabel(point: E01OpenPoint) {
  const multi = primaryFactor(point)?.exceedMultiple
  if (multi != null && Number(multi) >= 1.5) return '红'
  if (multi != null && Number(multi) >= 1.2) return '黄'
  if (point.status) return '蓝'
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

function handleCategoryClick(key: E01CategoryFilter) {
  if (props.categoryFilter === key) {
    emit('clearSelection')
    emit('changeCategory', key)
    return
  }
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
}

async function loadDetailForPoint(point: E01OpenPoint) {
  detailLoading.value = true
  detail.value = null
  try {
    const eventId = point.primaryEventId || point.eventIds[0]
    if (!eventId) return
    const res = await getE01EventDetail(eventId)
    if (res && res.code === 0 && res.data) detail.value = res.data
  } finally {
    detailLoading.value = false
  }
}

watch(
  () => props.categoryFilter,
  () => {
    page.value = 1
  },
)

watch(filteredPoints, (list) => {
  if (page.value > Math.max(1, Math.ceil(list.length / PAGE_SIZE))) {
    page.value = 1
  }
})

watch(
  () => props.selectedPointId,
  (id) => {
    if (id == null) {
      detail.value = null
      return
    }
    const point = openPoints.value.find((p) => p.pointId === id)
    if (point) void loadDetailForPoint(point)
  },
)

onMounted(() => {
  void loadOverview()
})

defineExpose({ reload: loadOverview, payload, openPoints })
</script>

<template>
  <aside class="e01-panel e01-panel--green">
    <header class="e01-head">
      <h2>环保风险预警</h2>
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

      <div class="e01-cat-row" aria-label="监测类型筛选">
        <button
          v-for="tab in categoryTabs"
          :key="tab.key"
          type="button"
          class="e01-cat"
          :class="{ active: categoryFilter === tab.key }"
          @click="handleCategoryClick(tab.key)"
        >
          {{ tab.label }} {{ tab.value }}
        </button>
      </div>

      <div class="e01-body">
        <div class="e01-col e01-col--list">
          <div class="e01-list-title">监测点列表</div>
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
              <div class="e01-row__loc">{{ point.locationText || point.pointName }}</div>
              <div class="e01-row__factor">
                <b>{{ factorNames(point) }}</b>
                <span>
                  检测值
                  <i>{{ valueText(primaryFactor(point)?.detectedValue, primaryFactor(point)?.unit) }}</i>
                </span>
                <span class="muted">
                  标准 {{ valueText(primaryFactor(point)?.limitValue, primaryFactor(point)?.unit) }}
                </span>
              </div>
              <div class="e01-row__foot">
                <span>{{ dateOnly(point.discoveredAt) }}</span>
                <span v-if="!point.canLocate" class="warn">无法定位</span>
              </div>
            </button>

            <p v-if="!pagedPoints.length" class="e01-empty">当前分类暂无异常监测点</p>
          </div>

          <nav class="e01-pager" aria-label="点位分页">
            <span class="e01-pager__summary">{{ pagerSummary }}</span>
            <div v-if="showPageControls" class="e01-pager__controls">
              <button type="button" :disabled="page <= 1" @click="goPage(page - 1)">‹</button>
              <button
                v-for="n in totalPages"
                :key="n"
                type="button"
                :class="{ active: page === n }"
                @click="goPage(n)"
              >
                {{ n }}
              </button>
              <button type="button" :disabled="page >= totalPages" @click="goPage(page + 1)">›</button>
            </div>
          </nav>
        </div>

        <div class="e01-col e01-col--detail">
          <div class="e01-list-title">监测点详情</div>
          <div v-if="!selectedPoint" class="e01-empty e01-empty--detail">请选择左侧监测点查看详情（地图可看趋势）</div>
          <div v-else-if="detailLoading" class="e01-state">正在加载详情…</div>
          <div v-else class="e01-detail">
            <section class="e01-section">
              <h3>基础信息</h3>
              <dl>
                <div><dt>监测点</dt><dd>{{ selectedPoint.pointName }}</dd></div>
                <div><dt>类型</dt><dd>{{ typeLabel(selectedPoint) }}</dd></div>
                <div><dt>位置</dt><dd>{{ selectedPoint.locationText || '—' }}</dd></div>
                <div><dt>状态</dt><dd>{{ selectedPoint.status }}</dd></div>
                <div><dt>风险</dt><dd>{{ riskLabel(selectedPoint) }}</dd></div>
              </dl>
            </section>
            <section class="e01-section">
              <h3>检测值</h3>
              <p>
                {{ factorNames(selectedPoint) }}：
                {{ valueText(primaryFactor(selectedPoint)?.detectedValue, primaryFactor(selectedPoint)?.unit) }}
                （标准 {{ valueText(primaryFactor(selectedPoint)?.limitValue, primaryFactor(selectedPoint)?.unit) }}）
              </p>
              <p class="muted">历史趋势请在地图侧摘要卡查看</p>
            </section>
            <section class="e01-section">
              <h3>整改记录</h3>
              <template v-if="detail?.rectificationRounds?.length">
                <p
                  v-for="round in detail.rectificationRounds"
                  :key="round.id"
                >
                  第{{ round.roundNo }}轮 · {{ round.summary || round.reviewStatus || '—' }}
                </p>
              </template>
              <p v-else>{{ detail?.closure?.statusLabel || selectedPoint.status || '整改推进中' }}</p>
            </section>
          </div>
        </div>
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
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;

  h2 {
    margin: 0;
    font-size: 19px;
    font-weight: 700;
    color: #f3f8ff;
    &::after {
      content: '';
      display: inline-block;
      width: 8px;
      height: 8px;
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
  height: 58px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1px solid rgba(105, 227, 111, 0.22);
  border-radius: 6px;
  background: rgba(8, 40, 69, 0.4);
  margin-bottom: 12px;
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
  gap: 2px;
  position: relative;

  &:last-child { border-right: 0; }

  span {
    font-size: 13px;
    line-height: 1.2;
  }

  strong {
    font-size: 21px;
    line-height: 1.1;
    font-family: Bahnschrift, "DIN Alternate", Arial, sans-serif;
    color: #69e36f;
    font-weight: 700;

    &.is-text {
      font-size: 16px;
      font-family: inherit;
    }
  }

  &.is-static {
    cursor: default;
  }
}

.e01-cat-row {
  flex-shrink: 0;
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.e01-cat {
  border: 1px solid rgba(105, 227, 111, 0.28);
  border-radius: 4px;
  background: rgba(8, 40, 69, 0.45);
  color: #8ba6c3;
  font-size: 12px;
  padding: 3px 8px;
  cursor: pointer;

  &.active {
    color: #69e36f;
    border-color: rgba(105, 227, 111, 0.7);
    background: rgba(105, 227, 111, 0.12);
  }
}

.e01-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.e01-col {
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  &--list { flex: 0 1 48%; }
  &--detail { flex: 1 1 52%; }
}

.e01-list-title {
  flex-shrink: 0;
  margin-bottom: 8px;
  font-size: 14px;
  color: #8ba6c3;
}

.e01-list {
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.e01-row {
  flex-shrink: 0;
  width: 100%;
  text-align: left;
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 6px;
  background: rgba(8, 40, 69, 0.45);
  color: inherit;
  cursor: pointer;
  padding: 10px 10px 10px 12px;
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
  font-size: 14px;
  color: #c3d4e8;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.e01-row__status {
  flex-shrink: 0;
  font-style: normal;
  font-size: 12px;
  color: #69e36f;
  border: 1px solid rgba(105, 227, 111, 0.45);
  border-radius: 3px;
  padding: 1px 6px;
  background: rgba(105, 227, 111, 0.08);
}

.e01-row__loc {
  margin-top: 5px;
  font-size: 15px;
  color: #e8f3ff;
  line-height: 1.4;
}

.e01-row__factor {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px 10px;
  align-items: baseline;
  font-size: 13px;
  color: #8ba6c3;

  b {
    font-size: 14px;
    font-weight: 600;
    color: #f3f8ff;
  }

  i {
    font-style: normal;
    color: #ff8f5a;
    font-weight: 700;
    font-size: 15px;
  }

  .muted { color: #7f95ad; font-size: 13px; }
}

.e01-row__multi {
  color: #ff8f5a;
  font-weight: 600;
  font-size: 12px;
  border: 1px solid rgba(255, 143, 90, 0.35);
  border-radius: 3px;
  padding: 0 5px;
  line-height: 18px;
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
  margin: 16px 0 0;
  text-align: center;
  font-size: 13px;
  color: #8ba6c3;

  &--detail {
    margin-top: 24px;
  }
}

.e01-detail {
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.e01-section {
  border: 1px solid rgba(105, 227, 111, 0.18);
  border-radius: 6px;
  background: rgba(8, 40, 69, 0.4);
  padding: 10px;

  h3 {
    margin: 0 0 8px;
    font-size: 13px;
    color: #69e36f;
    font-weight: 600;
  }

  p {
    margin: 0;
    font-size: 13px;
    color: #d7e6f5;
    line-height: 1.5;
  }

  .muted {
    margin-top: 6px;
    color: #8ba6c3;
    font-size: 12px;
  }

  dl {
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 6px;

    div {
      display: grid;
      grid-template-columns: 52px 1fr;
      gap: 6px;
      font-size: 12px;
    }

    dt { color: #8ba6c3; }
    dd { margin: 0; color: #e8f3ff; }
  }
}

.e01-pager {
  flex-shrink: 0;
  margin-top: 10px;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.e01-pager__summary {
  font-size: 13px;
  color: #8ba6c3;
  white-space: nowrap;
}

.e01-pager__controls {
  display: flex;
  gap: 6px;

  button {
    min-width: 28px;
    height: 28px;
    border: 1px solid rgba(105, 227, 111, 0.28);
    border-radius: 4px;
    background: rgba(8, 40, 69, 0.5);
    color: #8ba6c3;
    cursor: pointer;
    font-size: 13px;

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
