<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { getE01Events } from '@/services/api'
import type { E01CategoryFilter, E01EventsPayload, E01OpenPoint, E01OverviewStats, E01PointScope } from '@/types/e01'
import type {
  EsgClassAPanelConfig,
} from '@/types/esg-class-a'
import { isE01AbnormalPoint, mapE01PointToCard } from '@/utils/esg-e01-presenter'
import type { EsgRiskObjectCard } from '@/types/esg-class-a'

const props = defineProps<{
  config: EsgClassAPanelConfig
  summaryValue: string
  selectedPointId: number | null
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
  statsReady: [overview: E01OverviewStats, isDemo?: boolean]
}>()

const loading = ref(false)
const error = ref('')
const allPoints = ref<E01OpenPoint[]>([])
const overview = ref<E01OverviewStats | null>(null)
const sourceLabel = ref('')
const scopeFilter = ref<E01PointScope>(props.pointScope)

const categoryOptions: { key: E01CategoryFilter; label: string }[] = [
  { key: 'ALL', label: '全部' },
  { key: 'WATER', label: '水质' },
  { key: 'AIR', label: '扬尘' },
  { key: 'NOISE', label: '噪声' },
]

const visiblePoints = computed(() => {
  if (props.categoryFilter === 'ALL') return allPoints.value
  return allPoints.value.filter((point) => point.monitorCategory === props.categoryFilter)
})

const riskCount = computed(() => visiblePoints.value.filter(isE01AbnormalPoint).length)
const effectiveRiskCount = computed(() => props.categoryFilter === 'ALL' ? (overview.value?.anomalyCount ?? riskCount.value) : riskCount.value)
const isClearRiskState = computed(() => scopeFilter.value === 'risk' && visiblePoints.value.length > 0 && effectiveRiskCount.value === 0)
const scopedPoints = computed(() => scopeFilter.value === 'risk'
  ? visiblePoints.value.filter(isE01AbnormalPoint)
  : visiblePoints.value)
const directoryCards = computed(() => [...scopedPoints.value]
  .sort((a, b) => Number(isE01AbnormalPoint(b)) - Number(isE01AbnormalPoint(a)))
  .map(mapE01PointToCard))
const locatableCount = computed(() => visiblePoints.value.filter((point) => point.canLocate).length)
const displaySourceLabel = computed(() => {
  if (sourceLabel.value.toLowerCase() === 'e01_actual_baseline') return '实际基线数据'
  if (!sourceLabel.value) return '当前接口'
  return sourceLabel.value.toLowerCase() === 'esg_demo' ? '演示数据' : sourceLabel.value
})
const directoryPage = ref(1)
const directoryPageSize = 4
const directoryTotalPages = computed(() => Math.max(1, Math.ceil(directoryCards.value.length / directoryPageSize)))
const pagedDirectoryCards = computed(() => {
  const start = (directoryPage.value - 1) * directoryPageSize
  return directoryCards.value.slice(start, start + directoryPageSize)
})

const summaryCards = computed(() => [
  { label: '全局风险', value: effectiveRiskCount.value, tone: panelStatus.value.tone },
  { label: '监测点位', value: overview.value?.monitorPointCount ?? allPoints.value.length, tone: 'info' },
      { label: '待处置点位', value: overview.value?.openCount ?? 0, tone: (overview.value?.openCount || 0) > 0 ? 'warning' : 'normal' },
  { label: '当前基线记录', value: overview.value?.eventCount ?? 0, tone: 'info' },
])

const panelStatus = computed(() => {
  const risk = props.categoryFilter === 'ALL' ? String(overview.value?.riskLevel || '').toUpperCase() : ''
  if (risk.includes('红') || risk.includes('RED') || risk.includes('HIGH') || effectiveRiskCount.value >= 3) {
    return { label: '高风险', tone: 'danger' as const }
  }
  if (risk.includes('黄') || risk.includes('YELLOW') || risk.includes('WARN') || effectiveRiskCount.value >= 1) {
    return { label: '关注', tone: 'warning' as const }
  }
  return { label: '正常', tone: 'normal' as const }
})

async function loadEvents() {
  loading.value = true
  error.value = ''
  try {
    const res = await getE01Events()
    if (!res?.data) {
      error.value = '监测数据暂不可用'
      allPoints.value = []
      emit('overviewReady', [])
      return
    }
    const payload = res.data as E01EventsPayload & { source?: string }
    overview.value = {
      ...payload.overview,
      eventCount: payload.kpi?.eventCount,
    }
    emit('statsReady', overview.value, Boolean(payload.isDemo))
    sourceLabel.value = String(res.meta?.source || payload.source || '')
    allPoints.value = payload.openPoints || []
    emit('overviewReady', allPoints.value)
  } catch {
    error.value = '数据加载失败'
    allPoints.value = []
    overview.value = null
    sourceLabel.value = ''
    emit('overviewReady', [])
  } finally {
    loading.value = false
  }
}

function onScopeChange(scope: E01PointScope) {
  scopeFilter.value = scope
  emit('changeScope', scope)
}

function onCategoryChange(category: E01CategoryFilter) {
  emit('changeCategory', category)
}

function selectDirectoryCard(card: EsgRiskObjectCard) {
  const point = allPoints.value.find((item) => item.pointId === card.id)
  if (point) emit('selectPoint', point)
}

function changeDirectoryPage(page: number) {
  directoryPage.value = Math.min(Math.max(page, 1), directoryTotalPages.value)
}

watch(() => props.pointScope, (scope) => {
  scopeFilter.value = scope
})

watch(() => [props.categoryFilter, props.pointScope, directoryCards.value.length] as const, () => {
  directoryPage.value = 1
})

watch(directoryTotalPages, (total) => {
  if (directoryPage.value > total) directoryPage.value = total
})

onMounted(() => void loadEvents())
</script>

<template>
  <aside class="e01-panel esg-risk-panel" :class="[`theme-${config.theme}`, `status-${panelStatus.tone}`]">
    <header class="panel-head">
      <div class="title-wrap">
        <h2>{{ config.title }}</h2>
        <span class="status-pill" :class="`tone-${panelStatus.tone}`">{{ panelStatus.label }}</span>
      </div>
      <button type="button" class="close-btn" aria-label="关闭" @click="emit('close')">×</button>
    </header>

    <div class="summary-row">
      <div v-for="item in summaryCards" :key="item.label" class="summary-card" :class="`tone-${item.tone}`">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </div>
      <div class="summary-source">
        <span>数据源</span>
        <strong>{{ displaySourceLabel }}</strong>
      </div>
    </div>

    <div class="category-row" role="tablist" aria-label="监测类别">
      <button
        v-for="item in categoryOptions"
        :key="item.key"
        type="button"
        :class="{ active: props.categoryFilter === item.key }"
        @click="onCategoryChange(item.key)"
      >{{ item.label }}</button>
    </div>

    <div v-if="error" class="state error">
      {{ error }}
      <button type="button" @click="loadEvents">重试</button>
    </div>
    <div v-else-if="loading" class="state">正在加载…</div>

    <template v-else>
      <div class="scope-row" role="tablist" aria-label="地图点位筛选">
        <button type="button" :class="{ active: scopeFilter === 'risk' }" @click="onScopeChange('risk')">异常点位</button>
        <button type="button" :class="{ active: scopeFilter === 'all' }" @click="onScopeChange('all')">全部点位</button>
      </div>

      <section v-if="directoryCards.length" class="point-directory">
        <header class="directory-head">
          <div>
            <h3>{{ scopeFilter === 'all' ? '监测点总览' : '异常点位' }}</h3>
            <p>
              点击点位查看详情 · 全局风险 {{ effectiveRiskCount }} 项
              <span v-if="locatableCount"> · 已配置地图 {{ locatableCount }} 个</span>
              <span v-else> · 地图坐标待配置</span>
            </p>
          </div>
          <strong>{{ directoryCards.length }} 个</strong>
        </header>
        <div class="directory-grid">
          <button
            v-for="card in pagedDirectoryCards"
            :key="card.id"
            type="button"
            class="directory-card"
            @click="selectDirectoryCard(card)"
          >
            <div class="directory-card-head">
              <span class="directory-dot" :class="`dot-${card.statusLevel}`" />
              <div class="directory-card-identity">
                <strong>{{ card.code }}</strong>
                <span class="directory-card-type">{{ card.monitorTypeLabel }}</span>
              </div>
              <em :class="`text-${card.statusLevel}`">{{ card.statusLabel }}</em>
            </div>
            <p class="directory-card-location"><span>位置</span>{{ card.locationText }}</p>
            <div class="directory-card-metric">
              <div class="directory-card-factor">{{ card.latestFactorName || '监测值' }}</div>
              <strong v-if="card.latestResult" class="directory-result">{{ card.latestResult }}<small>{{ card.latestUnit ? ` ${card.latestUnit}` : '' }}</small></strong>
              <strong v-else class="directory-result is-empty">暂无数值</strong>
              <span class="directory-card-limit">限值 {{ card.latestLimit || '未设置' }}</span>
              <span class="directory-card-judgement" :class="`text-${card.latestJudgementLevel || card.statusLevel}`">{{ card.latestJudgementLabel || card.statusLabel }}</span>
            </div>
          </button>
        </div>
        <footer v-if="directoryTotalPages > 1" class="directory-pagination" aria-label="监测点目录分页">
          <button type="button" :disabled="directoryPage <= 1" @click="changeDirectoryPage(directoryPage - 1)">上一页</button>
          <span>第 <strong>{{ directoryPage }}</strong> / {{ directoryTotalPages }} 页</span>
          <button type="button" :disabled="directoryPage >= directoryTotalPages" @click="changeDirectoryPage(directoryPage + 1)">下一页</button>
        </footer>
      </section>

      <section v-else class="map-hint" :class="{ 'is-clear': isClearRiskState }">
        <div class="map-hint-icon">{{ isClearRiskState ? '✓' : '⌖' }}</div>
        <h3>{{ isClearRiskState ? '暂无异常风险' : '点击地图风险点查看详情' }}</h3>
        <p v-if="isClearRiskState">
          当前 {{ visiblePoints.length }} 个监测点均未发现超标或异常，系统持续监测中。
        </p>
        <p v-else>监测点详情、异常指标、责任单位和趋势已集中到左侧地图弹窗。</p>
        <div class="map-hint-stats">
          <template v-if="isClearRiskState">
            <span>异常点位 <strong>{{ effectiveRiskCount }}</strong> 个</span>
            <span>全部监测点 <strong>{{ visiblePoints.length }}</strong> 个</span>
          </template>
          <template v-else>
            <span>当前筛选 <strong>{{ scopeFilter === 'risk' ? effectiveRiskCount : (overview?.monitorPointCount ?? allPoints.length) }}</strong> 个</span>
            <span>地图联动 <strong>{{ visiblePoints.filter((point) => point.canLocate).length }}</strong> 个</span>
          </template>
        </div>
        <button v-if="isClearRiskState" type="button" class="map-hint-action" @click="onScopeChange('all')">查看全部点位</button>
      </section>
    </template>
  </aside>
</template>

<style scoped lang="scss">
.esg-risk-panel {
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

.panel-head {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;

  h2 {
    margin: 0;
    font-size: 24px;
    font-weight: 700;
    color: #f3f8ff;

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

.status-warning .title-wrap h2::after { background: #ffc857; box-shadow: 0 0 0 3px rgba(255, 200, 87, 0.18); }
.status-danger .title-wrap h2::after { background: #ff5a7a; box-shadow: 0 0 0 3px rgba(255, 90, 122, 0.18); }

.status-pill {
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 600;
  border: 1px solid rgba(255, 255, 255, 0.12);

  &.tone-normal { color: #69e36f; border-color: rgba(105, 227, 111, 0.4); }
  &.tone-warning { color: #ffc857; border-color: rgba(255, 200, 87, 0.4); }
  &.tone-danger { color: #ff7a96; border-color: rgba(255, 122, 150, 0.4); }
}

.close-btn {
  width: 30px;
  height: 30px;
  font-size: 18px;
  border: 1px solid rgba(105, 227, 111, 0.35);
  background: rgba(8, 40, 69, 0.72);
  color: #f3f8ff;
  border-radius: 6px;
  cursor: pointer;
}

.summary-row {
  flex-shrink: 0;
  display: flex;
  align-items: stretch;
  gap: 10px;
  margin-bottom: 12px;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid rgba(105, 227, 111, 0.22);
  background: rgba(8, 40, 69, 0.4);
}

.summary-card,
.summary-source {
  min-width: 0;
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
  min-height: 62px;
  padding: 10px 12px;
  border-radius: 6px;
  background: rgba(8, 40, 69, 0.62);
  border: 1px solid rgba(255, 255, 255, 0.08);

  span { color: #9db6d1; font-size: 16px; line-height: 1.2; white-space: nowrap; }
  strong {
    color: #f3f8ff;
    font-family: var(--font-num, Bahnschrift, sans-serif);
    font-size: 32px;
    font-variant-numeric: tabular-nums;
    line-height: 1;
  }
  &.tone-danger strong { color: #ff7a96; }
  &.tone-warning strong { color: #ffc857; }
  &.tone-normal strong { color: #69e36f; }
  &.tone-info strong { color: #67b8ff; }
}

.category-row {
  flex-shrink: 0;
  display: flex;
  gap: 6px;
  margin: -4px 0 8px;

  button {
    flex: 1;
    height: 28px;
    border: 1px solid rgba(47, 156, 255, 0.28);
    border-radius: 5px;
    background: rgba(8, 40, 69, 0.45);
    color: #9db6d1;
    cursor: pointer;
    font-size: 14px;

    &.active {
      color: #fff;
      border-color: rgba(47, 156, 255, 0.72);
      background: rgba(47, 156, 255, 0.2);
    }
  }
}

.summary-source {
  flex: 0 0 132px;
  align-items: flex-start;
  gap: 6px;
  border-color: rgba(103, 184, 255, 0.18);
  background: rgba(8, 40, 69, 0.35);

  span { font-size: 14px; }
  strong {
    overflow: hidden;
    color: #d7e6f5;
    font-size: 15px;
    line-height: 1.3;
    text-overflow: ellipsis;
    white-space: normal;
  }
}

.summary-label {
  font-size: 18px;
  color: #b8cfe6;
}

.summary-value {
  font-size: 36px;
  font-weight: 700;
  font-family: var(--font-num, Bahnschrift, sans-serif);
  color: #69e36f;
  line-height: 1;
}

.state {
  padding: 20px;
  text-align: center;
  color: #8ba6c3;
  font-size: 16px;

  &.error { color: #ffc857; }

  button {
    display: block;
    margin: 10px auto 0;
    padding: 4px 14px;
    border: 1px solid rgba(105, 227, 111, 0.35);
    background: rgba(8, 40, 69, 0.72);
    color: #69e36f;
    border-radius: 4px;
    cursor: pointer;
  }
}

.scope-row {
  display: flex;
  gap: 8px;
  margin: 0 0 14px;

  button {
    flex: 1;
    height: 34px;
    border: 1px solid rgba(47, 156, 255, 0.3);
    border-radius: 6px;
    background: rgba(8, 40, 69, 0.5);
    color: #b8cfe6;
    cursor: pointer;
    font-size: 15px;

    &.active {
      border-color: rgba(47, 156, 255, 0.8);
      background: rgba(47, 156, 255, 0.22);
      color: #fff;
    }
  }
}

.map-hint {
  flex: 1;
  min-height: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 28px 24px;
  border: 1px dashed rgba(103, 184, 255, 0.35);
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(8, 40, 69, 0.62), rgba(4, 25, 48, 0.3));
  text-align: center;

  &.is-clear {
    border-color: rgba(105, 227, 111, 0.34);
    background: linear-gradient(180deg, rgba(20, 75, 68, 0.34), rgba(4, 25, 48, 0.3));

    .map-hint-icon {
      border-color: rgba(105, 227, 111, 0.58);
      color: #69e36f;
    }

    h3 { color: #dfffe2; }
  }

  .map-hint-icon {
    display: grid;
    place-items: center;
    width: 54px;
    height: 54px;
    margin-bottom: 14px;
    border: 1px solid rgba(103, 184, 255, 0.55);
    border-radius: 50%;
    color: #67b8ff;
    font-size: 30px;
  }

  h3 { margin: 0; color: #f3f8ff; font-size: 22px; }
  p { max-width: 320px; margin: 10px 0 18px; color: #9db6d1; font-size: 16px; line-height: 1.6; }
}

.point-directory {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 12px;
  border: 1px solid rgba(103, 184, 255, 0.28);
  border-radius: 10px;
  background: rgba(8, 40, 69, 0.38);
}

.directory-head {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;

  h3 { margin: 0; color: #f3f8ff; font-size: 22px; }
  p { margin: 5px 0 0; color: #9db6d1; font-size: 15px; line-height: 1.45; }
  strong { color: #67b8ff; font-size: 32px; white-space: nowrap; }
}

.directory-grid {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  grid-template-rows: repeat(4, minmax(0, 1fr));
  align-content: stretch;
  gap: 10px;
}

.directory-card {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 14px 16px;
  border: 1px solid rgba(103, 184, 255, 0.18);
  border-radius: 7px;
  background: rgba(4, 25, 48, 0.58);
  color: #d7e6f5;
  text-align: left;
  cursor: pointer;

  &:hover { border-color: rgba(103, 184, 255, 0.68); background: rgba(47, 156, 255, 0.12); }
}

.directory-card-head {
  display: flex;
  align-items: center;
  gap: 6px;

  strong { color: #f3f8ff; font-size: 21px; line-height: 1; }
  em { flex-shrink: 0; font-size: 16px; font-style: normal; }
}

.directory-card-identity {
  min-width: 0;
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.directory-card-type {
  padding: 3px 8px;
  border: 1px solid rgba(103, 184, 255, 0.36);
  border-radius: 4px;
  color: #9ed0ff;
  font-size: 14px;
  white-space: nowrap;
}

.directory-card-location {
  display: flex;
  gap: 6px;
  margin: 12px 0 0;
  overflow: hidden;
  color: #9db6d1;
  font-size: 15px;
  text-overflow: ellipsis;
  white-space: nowrap;

  span { flex-shrink: 0; color: #6f9bc1; }
}

.directory-card-metric {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.directory-card-factor {
  min-width: 96px;
  color: #c7d9eb;
  font-size: 16px;
  font-weight: 600;
}

.directory-card-limit {
  margin-left: auto;
  color: #86a5c4;
  font-size: 14px;
  white-space: nowrap;
}

.directory-card-judgement {
  flex-shrink: 0;
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
}

.directory-dot { width: 7px; height: 7px; flex-shrink: 0; border-radius: 50%; }
.dot-danger { background: #ff5a7a; }
.dot-warning { background: #ffc857; }
.dot-normal { background: #69e36f; }
.dot-info { background: #67b8ff; }
.text-danger { color: #ff7a96; }
.text-warning { color: #ffc857; }
.text-normal { color: #69e36f; }
.text-info { color: #67b8ff; }
.directory-result { display: inline-flex; align-items: baseline; color: #f3f8ff; font-size: 28px; font-weight: 700; line-height: 1; }
.directory-result small { margin-left: 3px; color: #9db6d1; font-size: 14px; font-weight: 400; }
.directory-result.is-empty { color: #67b8ff; font-size: 16px; }

.directory-pagination {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  color: #9db6d1;
  font-size: 14px;

  button {
    min-width: 64px;
    height: 28px;
    border: 1px solid rgba(103, 184, 255, 0.35);
    border-radius: 5px;
    background: rgba(8, 40, 69, 0.62);
    color: #d7e6f5;
    font-size: 14px;
    cursor: pointer;

    &:disabled { cursor: not-allowed; opacity: 0.35; }
  }

  strong { color: #67b8ff; }
}

.map-hint-stats {
  display: flex;
  gap: 18px;
  color: #8ba6c3;
  font-size: 14px;

  strong { color: #e8f3ff; font-size: 18px; }
}

.map-hint-action {
  min-width: 132px;
  height: 34px;
  margin-top: 20px;
  padding: 0 18px;
  border: 1px solid rgba(105, 227, 111, 0.52);
  border-radius: 6px;
  background: rgba(105, 227, 111, 0.12);
  color: #bfffc4;
  font-size: 15px;
  cursor: pointer;

  &:hover {
    background: rgba(105, 227, 111, 0.2);
  }
}
</style>
