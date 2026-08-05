<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { getS02Risks } from '@/services/api'
import { isS02KeyRisk } from '@/data/s02-risks.mock'
import type {
  S02BusinessCategory,
  S02CategoryFilter,
  S02ObjectScope,
  S02PanelLayer,
  S02RiskItem,
  S02RisksPayload,
} from '@/types/s02'
import { extractSectionLabel, typeWithSection } from '@/utils/section-label'

const props = defineProps<{
  selectedRiskId: number | null
  layer: S02PanelLayer
  categoryFilter: S02CategoryFilter
  objectScope: S02ObjectScope
}>()

const emit = defineEmits<{
  close: []
  changeCategory: [category: S02CategoryFilter]
  changeScope: [scope: S02ObjectScope]
  selectRisk: [risk: S02RiskItem]
  clearSelection: []
  overviewReady: [risks: S02RiskItem[]]
}>()

const PAGE_SIZE = 3
const loading = ref(false)
const error = ref('')
const payload = ref<S02RisksPayload | null>(null)
const page = ref(1)

const overview = computed(() => payload.value?.overview || {
  total: 0,
  major: 0,
  larger: 0,
  newThisMonth: 0,
  cancelledThisMonth: 0,
  locationCount: 0,
  majorSourceCount: 0,
  hazardousEngCount: 0,
  generalCount: 0,
})

const risks = computed(() => payload.value?.risks || [])

const scopedRisks = computed(() => {
  if (props.objectScope === 'all') return risks.value
  return risks.value.filter(isS02KeyRisk)
})

const filteredRisks = computed(() => {
  if (props.categoryFilter === 'ALL') return scopedRisks.value
  return scopedRisks.value.filter((r) => r.businessCategory === props.categoryFilter)
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredRisks.value.length / PAGE_SIZE)))

const pagedRisks = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return filteredRisks.value.slice(start, start + PAGE_SIZE)
})

const pagerSummary = computed(
  () => `共 ${filteredRisks.value.length} 项 · 第 ${page.value}/${totalPages.value} 页`,
)

const showPageControls = computed(() => filteredRisks.value.length > PAGE_SIZE)

const summaryTabs = computed(() => [
  { label: '合计', value: overview.value.total },
  { label: '重大源', value: overview.value.majorSourceCount ?? overview.value.major },
  { label: '危大', value: overview.value.hazardousEngCount ?? 0 },
  { label: '一般', value: overview.value.generalCount ?? 0 },
])

function categoryCount(key: S02BusinessCategory) {
  const base = risks.value.filter((r) => r.businessCategory === key)
  return props.objectScope === 'all' ? base.length : base.filter(isS02KeyRisk).length
}

const categoryTabs = computed(() => [
  { key: 'MAJOR_SOURCE' as const, label: '重大风险源', value: categoryCount('MAJOR_SOURCE') },
  { key: 'HAZARDOUS_ENG' as const, label: '危大工程', value: categoryCount('HAZARDOUS_ENG') },
  { key: 'GENERAL' as const, label: '一般风险源', value: categoryCount('GENERAL') },
])

function riskSection(risk: S02RiskItem) {
  return risk.sectionCode || extractSectionLabel(risk.title, risk.locationText) || '未分区'
}

function riskTypeLine(risk: S02RiskItem) {
  return typeWithSection(risk.businessCategoryLabel || risk.riskType || '风险源', riskSection(risk))
}

function levelClass(level: string) {
  if (level === '重大') return 'major'
  if (level === '较大') return 'larger'
  return 'general'
}

async function loadOverview() {
  loading.value = true
  error.value = ''
  try {
    const res = await getS02Risks()
    if (!res || res.code !== 0 || !res.data) {
      error.value = 'S02 数据暂不可用'
      payload.value = null
      emit('overviewReady', [])
      return
    }
    payload.value = res.data
    emit('overviewReady', res.data.risks || [])
  } catch {
    error.value = 'S02 数据加载失败'
    payload.value = null
    emit('overviewReady', [])
  } finally {
    loading.value = false
  }
}

function handleScopeClick(scope: S02ObjectScope) {
  if (props.objectScope === scope) return
  page.value = 1
  emit('clearSelection')
  emit('changeScope', scope)
}

function handleCategoryClick(key: S02BusinessCategory) {
  page.value = 1
  emit('clearSelection')
  emit('changeCategory', key)
}

function handleSelectRisk(risk: S02RiskItem) {
  emit('selectRisk', risk)
}

function goPage(next: number) {
  if (next < 1 || next > totalPages.value) return
  page.value = next
  emit('clearSelection')
}

watch(
  () => [props.categoryFilter, props.objectScope] as const,
  () => {
    page.value = 1
  },
)

watch(filteredRisks, (list) => {
  if (page.value > Math.max(1, Math.ceil(list.length / PAGE_SIZE))) page.value = 1
})

onMounted(() => {
  void loadOverview()
})

defineExpose({ reload: loadOverview, payload, risks })
</script>

<template>
  <aside class="s02-panel">
    <header class="s02-head">
      <h2>重大风险源管控</h2>
      <button type="button" class="s02-close" aria-label="关闭S02" @click="emit('close')">×</button>
    </header>

    <div v-if="loading" class="s02-state">正在加载…</div>
    <div v-else-if="error" class="s02-state is-error">
      {{ error }}
      <button class="s02-retry" @click="loadOverview">重试</button>
    </div>
    <template v-else>
      <section class="s02-stats" aria-label="风险源摘要">
        <div v-for="tab in summaryTabs" :key="tab.label" class="s02-stats__cell">
          <span>{{ tab.label }}</span>
          <strong>{{ tab.value }}</strong>
        </div>
      </section>

      <div class="s02-scope-row" role="tablist" aria-label="对象范围">
        <button
          type="button"
          role="tab"
          class="s02-scope"
          :class="{ active: objectScope === 'key' }"
          @click="handleScopeClick('key')"
        >
          重点对象
        </button>
        <button
          type="button"
          role="tab"
          class="s02-scope"
          :class="{ active: objectScope === 'all' }"
          @click="handleScopeClick('all')"
        >
          全部对象
        </button>
      </div>

      <div class="s02-cat-row" aria-label="风险业务分类">
        <button
          v-for="tab in categoryTabs"
          :key="tab.key"
          type="button"
          class="s02-cat"
          :class="{ active: categoryFilter === tab.key }"
          @click="handleCategoryClick(tab.key)"
        >
          <span>{{ tab.label }}</span>
          <em>{{ tab.value }}</em>
        </button>
      </div>

      <div class="s02-body">
        <div class="s02-list-title">
          {{ objectScope === 'key' ? '重大风险源列表' : '全部风险源列表' }}
        </div>
        <div class="s02-list">
          <button
            v-for="risk in pagedRisks"
            :key="risk.id"
            type="button"
            class="s02-row"
            :class="{ active: selectedRiskId === risk.id, 'no-locate': !risk.canLocate }"
            @click="handleSelectRisk(risk)"
          >
            <div class="s02-row__top">
              <span class="s02-row__type">{{ risk.title }}</span>
              <em class="s02-row__level" :class="levelClass(risk.riskLevel)">{{ risk.riskLevel }}</em>
            </div>
            <div class="s02-row__loc">
              <b>{{ riskTypeLine(risk) }}</b>
            </div>
            <div class="s02-row__factor">
              <span>标段 {{ riskSection(risk) }}</span>
              <span>管控 {{ risk.status || '—' }}</span>
              <span v-if="!risk.canLocate" class="warn">无法定位</span>
            </div>
          </button>
          <p v-if="!pagedRisks.length" class="s02-empty">当前分类暂无风险源</p>
        </div>

        <nav class="s02-pager" aria-label="风险分页">
          <span class="s02-pager__summary">{{ pagerSummary }}</span>
          <div v-if="showPageControls" class="s02-pager__controls">
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
.s02-panel {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 14px 14px 10px;
  border: 1px solid rgba(47, 156, 255, 0.4);
  border-radius: 8px;
  background: rgba(4, 25, 48, 0.96);
  color: #d7e6f5;
  overflow: hidden;
}
.s02-head {
  flex-shrink: 0;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  h2 { margin: 0; font-size: 22px; font-weight: 700; color: #f3f8ff; }
}
.s02-close {
  width: 30px;
  height: 30px;
  font-size: 18px;
  border: 1px solid rgba(47, 156, 255, 0.4);
  background: rgba(8, 40, 69, 0.72);
  color: #f3f8ff;
  border-radius: 6px;
  cursor: pointer;
}
.s02-state {
  padding: 24px 8px;
  text-align: center;
  color: #8ba6c3;
  font-size: 13px;
  &.is-error { color: #ff9f2f; }
}
.s02-retry {
  display: block;
  margin: 10px auto 0;
  padding: 4px 14px;
  border: 1px solid rgba(47, 156, 255, 0.4);
  background: rgba(8, 40, 69, 0.72);
  color: #2f9cff;
  border-radius: 4px;
  cursor: pointer;
}
.s02-stats {
  flex-shrink: 0;
  height: 64px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1px solid rgba(47, 156, 255, 0.25);
  border-radius: 6px;
  background: rgba(8, 40, 69, 0.4);
  margin-bottom: 10px;
}
.s02-stats__cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border-right: 1px solid rgba(47, 156, 255, 0.12);
  &:last-child { border-right: 0; }
  span { font-size: 12px; color: #8ba6c3; }
  strong { font-size: 18px; color: #2f9cff; font-weight: 700; }
}
.s02-scope-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 10px;
}
.s02-scope {
  height: 34px;
  border: 1px solid rgba(47, 156, 255, 0.3);
  background: rgba(8, 40, 69, 0.45);
  color: #9fb6cd;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  &.active {
    color: #f3f8ff;
    border-color: rgba(47, 156, 255, 0.65);
    background: rgba(47, 156, 255, 0.16);
  }
}
.s02-cat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  margin-bottom: 10px;
}
.s02-cat {
  height: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  border: 1px solid rgba(47, 156, 255, 0.25);
  background: rgba(8, 40, 69, 0.4);
  border-radius: 6px;
  color: #9fb6cd;
  cursor: pointer;
  font-size: 11px;
  &.active {
    color: #f3f8ff;
    border-color: rgba(47, 156, 255, 0.6);
    background: rgba(47, 156, 255, 0.14);
  }
  em { font-style: normal; font-size: 16px; font-weight: 700; color: #2f9cff; }
}
.s02-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.s02-list-title { font-size: 13px; color: #8ba6c3; margin-bottom: 8px; }
.s02-list {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: hidden;
}
.s02-row {
  text-align: left;
  padding: 10px 12px;
  border: 1px solid rgba(47, 156, 255, 0.2);
  border-radius: 6px;
  background: rgba(8, 40, 69, 0.5);
  color: inherit;
  cursor: pointer;
  &.active {
    border-color: rgba(47, 156, 255, 0.7);
    background: rgba(47, 156, 255, 0.12);
  }
}
.s02-row__top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}
.s02-row__type { font-size: 14px; font-weight: 700; color: #f3f8ff; }
.s02-row__level {
  font-style: normal;
  font-size: 12px;
  &.major { color: #ff4f5e; }
  &.larger { color: #ffb347; }
  &.general { color: #2f9cff; }
}
.s02-row__loc {
  font-size: 12px;
  color: #9fb6cd;
  margin-bottom: 4px;
  b { font-weight: 600; color: #cfe6ff; }
}
.s02-row__factor {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: #8ba6c3;
  .warn { color: #ff9f2f; }
}
.s02-empty {
  margin: 24px 0;
  text-align: center;
  color: #8ba6c3;
  font-size: 13px;
}
.s02-pager {
  flex-shrink: 0;
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.s02-pager__summary { font-size: 12px; color: #8ba6c3; }
.s02-pager__controls {
  display: flex;
  gap: 4px;
  button {
    min-width: 28px;
    height: 26px;
    border: 1px solid rgba(47, 156, 255, 0.3);
    background: rgba(8, 40, 69, 0.5);
    color: #9fb6cd;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    &.active { color: #f3f8ff; border-color: rgba(47, 156, 255, 0.65); }
    &:disabled { opacity: 0.4; cursor: default; }
  }
}
</style>
