<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { getE02Issues } from '@/services/api'
import { isE02OpenIssue } from '@/data/e02-issues.mock'
import type {
  E02BusinessCategory,
  E02CategoryFilter,
  E02IssueItem,
  E02IssuesPayload,
  E02ObjectScope,
  E02PanelLayer,
} from '@/types/e02'

const props = defineProps<{
  selectedIssueId: number | null
  layer: E02PanelLayer
  categoryFilter: E02CategoryFilter
  objectScope: E02ObjectScope
}>()

const emit = defineEmits<{
  close: []
  changeCategory: [category: E02CategoryFilter]
  changeScope: [scope: E02ObjectScope]
  selectIssue: [issue: E02IssueItem]
  clearSelection: []
  overviewReady: [issues: E02IssueItem[]]
}>()

const PAGE_SIZE = 3
const loading = ref(false)
const error = ref('')
const payload = ref<E02IssuesPayload | null>(null)
const page = ref(1)

const overview = computed(() => payload.value?.overview || {
  total: 0,
  rectifying: 0,
  pendingReview: 0,
  pendingClosure: 0,
  overdueAmong: 0,
  openCount: 0,
  closedCount: 0,
  byCategory: { POLLUTION: 0, WATER_CONS: 0, ECOLOGY: 0, OTHER: 0 },
})

const issues = computed(() => payload.value?.issues || [])

const scopedIssues = computed(() => {
  if (props.objectScope === 'all') return issues.value
  return issues.value.filter(isE02OpenIssue)
})

const filteredIssues = computed(() => {
  if (props.categoryFilter === 'ALL') return scopedIssues.value
  return scopedIssues.value.filter((i) => i.businessCategory === props.categoryFilter)
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredIssues.value.length / PAGE_SIZE)))

const pagedIssues = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return filteredIssues.value.slice(start, start + PAGE_SIZE)
})

const pagerSummary = computed(
  () => `共 ${filteredIssues.value.length} 项 · 第 ${page.value}/${totalPages.value} 页`,
)

const showPageControls = computed(() => filteredIssues.value.length > PAGE_SIZE)

const summaryTabs = computed(() => [
  { label: '未闭环', value: overview.value.openCount ?? overview.value.total, isText: false },
  { label: '整改中', value: overview.value.rectifying, isText: false },
  { label: '待复查', value: overview.value.pendingReview, isText: false },
  { label: '逾期', value: overview.value.overdueAmong, isText: false },
])

function categoryCount(key: E02BusinessCategory) {
  const base = issues.value.filter((i) => i.businessCategory === key)
  return props.objectScope === 'all' ? base.length : base.filter(isE02OpenIssue).length
}

const categoryTabs = computed(() => [
  { key: 'POLLUTION' as const, label: '环境污染', value: categoryCount('POLLUTION') },
  { key: 'WATER_CONS' as const, label: '水保问题', value: categoryCount('WATER_CONS') },
  { key: 'ECOLOGY' as const, label: '生态问题', value: categoryCount('ECOLOGY') },
  { key: 'OTHER' as const, label: '其他', value: categoryCount('OTHER') },
])

function display(value: unknown) {
  if (value === null || value === undefined || value === '') return '—'
  return String(value)
}

function dateOnly(value?: string | null) {
  const text = display(value)
  if (text === '—') return text
  return text.slice(0, 10)
}

async function loadOverview() {
  loading.value = true
  error.value = ''
  try {
    const res = await getE02Issues('demo')
    if (!res || res.code !== 0 || !res.data) {
      error.value = 'E02 Demo 数据暂不可用'
      payload.value = null
      emit('overviewReady', [])
      return
    }
    payload.value = res.data
    emit('overviewReady', res.data.issues || [])
  } catch {
    error.value = 'E02 数据加载失败'
    payload.value = null
    emit('overviewReady', [])
  } finally {
    loading.value = false
  }
}

function handleScopeClick(scope: E02ObjectScope) {
  if (props.objectScope === scope) return
  page.value = 1
  emit('clearSelection')
  emit('changeScope', scope)
}

function handleCategoryClick(key: E02BusinessCategory) {
  page.value = 1
  emit('clearSelection')
  emit('changeCategory', key)
}

function handleSelectIssue(issue: E02IssueItem) {
  emit('selectIssue', issue)
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

watch(filteredIssues, (list) => {
  if (page.value > Math.max(1, Math.ceil(list.length / PAGE_SIZE))) page.value = 1
})

onMounted(() => {
  void loadOverview()
})

defineExpose({ reload: loadOverview, payload, issues })
</script>

<template>
  <aside class="e02-panel">
    <header class="e02-head">
      <h2>环保问题整改</h2>
      <button type="button" class="e02-close" aria-label="关闭E02" @click="emit('close')">×</button>
    </header>

    <div v-if="loading" class="e02-state">正在加载…</div>
    <div v-else-if="error" class="e02-state is-error">
      {{ error }}
      <button type="button" class="e02-retry" @click="loadOverview">重试</button>
    </div>
    <template v-else>
      <section class="e02-stats" aria-label="环保问题摘要">
        <div v-for="tab in summaryTabs" :key="tab.label" class="e02-stats__cell is-static">
          <span>{{ tab.label }}</span>
          <strong>{{ tab.value }}</strong>
        </div>
      </section>

      <div class="e02-scope-row" role="tablist" aria-label="对象范围">
        <button
          type="button"
          role="tab"
          :aria-selected="objectScope === 'key'"
          class="e02-scope"
          :class="{ active: objectScope === 'key' }"
          @click="handleScopeClick('key')"
        >
          重点对象
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="objectScope === 'all'"
          class="e02-scope"
          :class="{ active: objectScope === 'all' }"
          @click="handleScopeClick('all')"
        >
          全部对象
        </button>
      </div>

      <div class="e02-cat-row" aria-label="问题业务分类">
        <button
          v-for="tab in categoryTabs"
          :key="tab.key"
          type="button"
          class="e02-cat"
          :class="{ active: categoryFilter === tab.key }"
          @click="handleCategoryClick(tab.key)"
        >
          <span class="e02-cat__label">{{ tab.label }}</span>
          <em>{{ tab.value }}</em>
        </button>
      </div>

      <div class="e02-body">
        <div class="e02-list-title">
          {{ objectScope === 'key' ? '未闭环问题列表' : '全部问题列表' }}
        </div>
        <div class="e02-list">
          <button
            v-for="issue in pagedIssues"
            :key="issue.id"
            type="button"
            class="e02-row"
            :class="{ active: selectedIssueId === issue.id, 'no-locate': !issue.canLocate }"
            @click="handleSelectIssue(issue)"
          >
            <div class="e02-row__top">
              <span class="e02-row__type">{{ issue.businessCode }}</span>
              <em class="e02-row__status">{{ issue.status }}</em>
            </div>
            <div class="e02-row__loc">
              <b>{{ issue.businessCategoryLabel || issue.issueType }}</b>
              {{ issue.locationText }}
            </div>
            <div class="e02-row__factor">
              <span>发现 {{ dateOnly(issue.foundDate) }}</span>
              <span v-if="issue.overdue" class="warn">逾期</span>
              <span v-if="!issue.canLocate" class="warn">无法定位</span>
            </div>
          </button>
          <p v-if="!pagedIssues.length" class="e02-empty">
            {{ objectScope === 'key' ? '当前分类暂无未闭环问题' : '当前分类暂无问题' }}
          </p>
        </div>

        <nav class="e02-pager" aria-label="问题分页">
          <span class="e02-pager__summary">{{ pagerSummary }}</span>
          <div v-if="showPageControls" class="e02-pager__controls">
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
.e02-panel {
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
.e02-head {
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
  }
}
.e02-close {
  width: 30px;
  height: 30px;
  font-size: 18px;
  border: 1px solid rgba(105, 227, 111, 0.35);
  background: rgba(8, 40, 69, 0.72);
  color: #f3f8ff;
  border-radius: 6px;
  cursor: pointer;
}
.e02-state {
  padding: 24px 8px;
  text-align: center;
  color: #8ba6c3;
  font-size: 13px;
  &.is-error { color: #ff9f2f; }
}
.e02-retry {
  display: block;
  margin: 10px auto 0;
  padding: 4px 14px;
  border: 1px solid rgba(105, 227, 111, 0.35);
  background: rgba(8, 40, 69, 0.72);
  color: #69e36f;
  border-radius: 4px;
  cursor: pointer;
}
.e02-stats {
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
.e02-stats__cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border-right: 1px solid rgba(105, 227, 111, 0.12);
  &:last-child { border-right: 0; }
  span { font-size: 12px; color: #8ba6c3; }
  strong { font-size: 20px; color: #69e36f; font-weight: 700; }
}
.e02-scope-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 10px;
}
.e02-scope {
  height: 34px;
  border: 1px solid rgba(105, 227, 111, 0.25);
  background: rgba(8, 40, 69, 0.45);
  color: #9fb6cd;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  &.active {
    color: #f3f8ff;
    border-color: rgba(105, 227, 111, 0.55);
    background: rgba(105, 227, 111, 0.16);
  }
}
.e02-cat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  margin-bottom: 10px;
}
.e02-cat {
  height: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  border: 1px solid rgba(105, 227, 111, 0.2);
  background: rgba(8, 40, 69, 0.4);
  border-radius: 6px;
  color: #9fb6cd;
  cursor: pointer;
  &.active {
    color: #f3f8ff;
    border-color: rgba(105, 227, 111, 0.5);
    background: rgba(105, 227, 111, 0.14);
  }
  .e02-cat__label { font-size: 11px; }
  em { font-style: normal; font-size: 16px; font-weight: 700; color: #69e36f; }
}
.e02-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.e02-list-title {
  font-size: 13px;
  color: #8ba6c3;
  margin-bottom: 8px;
}
.e02-list {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.e02-row {
  text-align: left;
  padding: 10px 12px;
  border: 1px solid rgba(105, 227, 111, 0.18);
  border-radius: 6px;
  background: rgba(8, 40, 69, 0.5);
  color: inherit;
  cursor: pointer;
  &.active {
    border-color: rgba(105, 227, 111, 0.65);
    background: rgba(105, 227, 111, 0.12);
  }
  &.no-locate { opacity: 0.85; }
}
.e02-row__top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}
.e02-row__type { font-size: 14px; font-weight: 700; color: #f3f8ff; }
.e02-row__status { font-style: normal; font-size: 12px; color: #ffb347; }
.e02-row__loc {
  font-size: 12px;
  color: #9fb6cd;
  margin-bottom: 4px;
  b { color: #69e36f; margin-right: 6px; }
}
.e02-row__factor {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: #8ba6c3;
  .warn { color: #ff9f2f; }
}
.e02-empty {
  margin: 24px 0;
  text-align: center;
  color: #8ba6c3;
  font-size: 13px;
}
.e02-pager {
  flex-shrink: 0;
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.e02-pager__summary { font-size: 12px; color: #8ba6c3; }
.e02-pager__controls {
  display: flex;
  gap: 4px;
  button {
    min-width: 28px;
    height: 26px;
    border: 1px solid rgba(105, 227, 111, 0.25);
    background: rgba(8, 40, 69, 0.5);
    color: #9fb6cd;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    &.active {
      color: #f3f8ff;
      border-color: rgba(105, 227, 111, 0.55);
    }
    &:disabled { opacity: 0.4; cursor: default; }
  }
}
</style>
