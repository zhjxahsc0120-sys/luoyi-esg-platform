<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { getS02Risks } from '@/services/api'
import type {
  S02CategoryFilter,
  S02PanelLayer,
  S02RiskItem,
  S02RisksPayload,
} from '@/types/s02'
import { extractSectionLabel, typeWithSection } from '@/utils/section-label'

const props = defineProps<{
  selectedRiskId: number | null
  layer: S02PanelLayer
  categoryFilter: S02CategoryFilter
}>()

const emit = defineEmits<{
  close: []
  changeCategory: [category: S02CategoryFilter]
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
})

const risks = computed(() => payload.value?.risks || [])

const filteredRisks = computed(() => {
  if (props.categoryFilter === 'ALL') return risks.value
  if (props.categoryFilter === 'MAJOR') {
    return risks.value.filter((r) => r.riskLevel === '重大')
  }
  return risks.value.filter((r) => r.riskLevel === '较大')
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

const categoryTabs = computed(() => [
  { key: 'ALL' as const, label: '全部', value: overview.value.total },
  { key: 'MAJOR' as const, label: '重大', value: overview.value.major },
  { key: 'LARGER' as const, label: '较大', value: overview.value.larger },
])

function display(value: unknown) {
  if (value === null || value === undefined || value === '') return null
  return String(value)
}

function dateOnly(value?: string | null) {
  const text = display(value)
  if (!text) return '—'
  return text.slice(0, 10)
}

function riskSection(risk: S02RiskItem) {
  return extractSectionLabel(risk.title, risk.locationText) || '未分区'
}

function riskTypeLine(risk: S02RiskItem) {
  return typeWithSection(risk.riskType || '安全风险', riskSection(risk))
}

function levelClass(level: string) {
  return level === '重大' ? 'major' : 'larger'
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

function handleCategoryClick(key: S02CategoryFilter) {
  if (props.categoryFilter === key) {
    emit('clearSelection')
    emit('changeCategory', key)
    return
  }
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
}

watch(
  () => props.categoryFilter,
  () => {
    page.value = 1
  },
)

watch(filteredRisks, (list) => {
  if (page.value > Math.max(1, Math.ceil(list.length / PAGE_SIZE))) {
    page.value = 1
  }
})

onMounted(() => {
  void loadOverview()
})

defineExpose({ reload: loadOverview, payload, risks })
</script>

<template>
  <aside class="s02-panel">
    <header class="s02-head">
      <h2>在管安全风险点</h2>
      <button type="button" class="s02-close" aria-label="关闭S02" @click="emit('close')">×</button>
    </header>

    <div v-if="loading" class="s02-state">正在加载…</div>
    <div v-else-if="error" class="s02-state is-error">
      {{ error }}
      <button class="s02-retry" @click="loadOverview">重试</button>
    </div>
    <template v-else>
      <section class="s02-stats" aria-label="风险等级统计">
        <button
          v-for="tab in categoryTabs"
          :key="tab.key"
          type="button"
          class="s02-stats__cell"
          :class="{ active: categoryFilter === tab.key }"
          @click="handleCategoryClick(tab.key)"
        >
          <span>{{ tab.label }}</span>
          <strong>{{ tab.value }}</strong>
        </button>
      </section>

      <div class="s02-meta-hint">
        本月新增 <strong>{{ overview.newThisMonth }}</strong>
        · 本月销号 <strong>{{ overview.cancelledThisMonth }}</strong>
        · 涉及工点 <strong>{{ overview.locationCount }}</strong>
      </div>

      <div class="s02-list-title">当前在管风险点</div>

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
            <span class="s02-row__type">{{ riskTypeLine(risk) }}</span>
            <em class="s02-row__level" :class="levelClass(risk.riskLevel)">{{ risk.riskLevel }}</em>
          </div>
          <div class="s02-row__title">{{ risk.title || '—' }}</div>
          <div class="s02-row__loc">{{ risk.locationText || '—' }}</div>
          <div class="s02-row__meta">
            <span>{{ risk.status || '—' }}</span>
            <span>起控：{{ dateOnly(risk.controlStartDate) }}</span>
          </div>
          <div v-if="!risk.canLocate" class="s02-row__foot">
            <span class="warn">无法定位</span>
          </div>
        </button>

        <p v-if="!pagedRisks.length" class="s02-empty">当前筛选暂无在管风险点</p>
      </div>

      <nav class="s02-pager" aria-label="风险点分页">
        <span class="s02-pager__summary">{{ pagerSummary }}</span>
        <div v-if="showPageControls" class="s02-pager__controls">
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
    display: flex;
    align-items: center;
    gap: 8px;

    &::before {
      content: '';
      display: inline-block;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #2f9cff;
      box-shadow: 0 0 0 3px rgba(47, 156, 255, 0.18);
    }
  }
}

.s02-close {
  width: 30px;
  height: 30px;
  font-size: 18px;
  line-height: 1;
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
  font-size: 13px;
  border: 1px solid rgba(47, 156, 255, 0.4);
  background: rgba(8, 40, 69, 0.72);
  color: #2f9cff;
  border-radius: 4px;
  cursor: pointer;
}

.s02-stats {
  flex-shrink: 0;
  height: 58px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border: 1px solid rgba(47, 156, 255, 0.25);
  border-radius: 6px;
  background: rgba(8, 40, 69, 0.4);
  margin-bottom: 8px;
  overflow: hidden;
}

.s02-stats__cell {
  border: 0;
  border-right: 1px solid rgba(47, 156, 255, 0.18);
  background: transparent;
  color: #8ba6c3;
  cursor: pointer;
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
    color: #d7e6f5;
    font-weight: 700;
  }

  &.active {
    color: #b8ddff;
    strong { color: #2f9cff; }
    &::after {
      content: '';
      position: absolute;
      left: 18%;
      right: 18%;
      bottom: 0;
      height: 2px;
      background: #2f9cff;
    }
  }
}

.s02-meta-hint {
  flex-shrink: 0;
  margin-bottom: 8px;
  font-size: 12px;
  color: #8ba6c3;

  strong {
    font-family: Bahnschrift, "DIN Alternate", Arial, sans-serif;
    font-weight: 700;
    color: #c3d4e8;
  }
}

.s02-list-title {
  flex-shrink: 0;
  margin-bottom: 8px;
  font-size: 14px;
  color: #8ba6c3;
}

.s02-list {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.s02-row {
  flex-shrink: 0;
  width: 100%;
  text-align: left;
  border: 1px solid rgba(47, 156, 255, 0.22);
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
    border-color: rgba(47, 156, 255, 0.5);
    background: rgba(12, 42, 72, 0.45);
  }

  &.active {
    border-color: rgba(47, 156, 255, 0.75);
    background: rgba(18, 56, 96, 0.4);
    &::before { background: #2f9cff; }
  }
}

.s02-row__top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.s02-row__type {
  font-size: 14px;
  color: #c3d4e8;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.s02-row__level {
  flex-shrink: 0;
  font-style: normal;
  font-size: 12px;
  border-radius: 3px;
  padding: 1px 6px;

  &.major {
    color: #ff4f5e;
    border: 1px solid rgba(255, 79, 94, 0.45);
    background: rgba(255, 79, 94, 0.08);
  }

  &.larger {
    color: #ffb347;
    border: 1px solid rgba(255, 179, 71, 0.45);
    background: rgba(255, 179, 71, 0.08);
  }
}

.s02-row__title {
  margin-top: 5px;
  font-size: 15px;
  font-weight: 600;
  color: #e8f3ff;
  line-height: 1.4;
}

.s02-row__loc {
  margin-top: 3px;
  font-size: 13px;
  color: #8ba6c3;
}

.s02-row__meta {
  margin-top: 5px;
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #7f95ad;
}

.s02-row__foot {
  margin-top: 6px;
  font-size: 13px;
  .warn { color: #ff9f2f; }
}

.s02-empty {
  margin: 16px 0 0;
  text-align: center;
  font-size: 13px;
  color: #8ba6c3;
}

.s02-pager {
  flex-shrink: 0;
  margin-top: 10px;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.s02-pager__summary {
  font-size: 13px;
  color: #8ba6c3;
  white-space: nowrap;
}

.s02-pager__controls {
  display: flex;
  gap: 6px;

  button {
    min-width: 28px;
    height: 28px;
    border: 1px solid rgba(47, 156, 255, 0.3);
    border-radius: 4px;
    background: rgba(8, 40, 69, 0.5);
    color: #8ba6c3;
    cursor: pointer;
    font-size: 13px;

    &.active {
      color: #2f9cff;
      border-color: rgba(47, 156, 255, 0.75);
      background: rgba(47, 156, 255, 0.12);
    }

    &:disabled {
      opacity: 0.35;
      cursor: not-allowed;
    }
  }
}
</style>
