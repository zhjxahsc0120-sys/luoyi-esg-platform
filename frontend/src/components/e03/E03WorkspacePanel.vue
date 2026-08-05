<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { getE03WaterObjects } from '@/services/api'
import { isE03KeyObject } from '@/data/e03-water.mock'
import type {
  E03CategoryFilter,
  E03ObjectScope,
  E03ObjectType,
  E03PanelLayer,
  E03WaterObjectItem,
  E03WaterObjectsPayload,
} from '@/types/e03'

const props = defineProps<{
  selectedIssueId: number | null
  layer: E03PanelLayer
  categoryFilter: E03CategoryFilter
  objectScope: E03ObjectScope
}>()

const emit = defineEmits<{
  close: []
  changeCategory: [category: E03CategoryFilter]
  changeScope: [scope: E03ObjectScope]
  selectIssue: [issue: E03WaterObjectItem]
  clearSelection: []
  overviewReady: [issues: E03WaterObjectItem[]]
}>()

const PAGE_SIZE = 3
const loading = ref(false)
const error = ref('')
const payload = ref<E03WaterObjectsPayload | null>(null)
const page = ref(1)

const overview = computed(() => payload.value?.overview || {
  objectCount: 0,
  keyCount: 0,
  areaTotalHa: 0,
  pendingApproval: 0,
  byType: { SPOIL: 0, TEMP_LAND: 0, TOPSOIL: 0, REGREEN: 0 },
})

const objects = computed(() => payload.value?.objects || [])

const scopedObjects = computed(() => {
  if (props.objectScope === 'all') return objects.value
  return objects.value.filter(isE03KeyObject)
})

const filteredObjects = computed(() => {
  if (props.categoryFilter === 'ALL') return scopedObjects.value
  return scopedObjects.value.filter((o) => o.objectType === props.categoryFilter)
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredObjects.value.length / PAGE_SIZE)))

const pagedObjects = computed(() => {
  const start = (page.value - 1) * PAGE_SIZE
  return filteredObjects.value.slice(start, start + PAGE_SIZE)
})

const pagerSummary = computed(
  () => `共 ${filteredObjects.value.length} 处 · 第 ${page.value}/${totalPages.value} 页`,
)

const showPageControls = computed(() => filteredObjects.value.length > PAGE_SIZE)

const summaryTabs = computed(() => [
  { label: '对象', value: overview.value.objectCount },
  { label: '重点', value: overview.value.keyCount },
  { label: '面积ha', value: overview.value.areaTotalHa },
  { label: '待批', value: overview.value.pendingApproval },
])

function categoryCount(key: E03ObjectType) {
  const base = objects.value.filter((o) => o.objectType === key)
  return props.objectScope === 'all' ? base.length : base.filter(isE03KeyObject).length
}

const categoryTabs = computed(() => [
  { key: 'SPOIL' as const, label: '弃土场', value: categoryCount('SPOIL') },
  { key: 'TEMP_LAND' as const, label: '临时占地', value: categoryCount('TEMP_LAND') },
  { key: 'TOPSOIL' as const, label: '表土剥离', value: categoryCount('TOPSOIL') },
  { key: 'REGREEN' as const, label: '复绿区域', value: categoryCount('REGREEN') },
])

async function loadOverview() {
  loading.value = true
  error.value = ''
  try {
    const res = await getE03WaterObjects()
    if (!res || res.code !== 0 || !res.data) {
      error.value = 'E03 Demo 数据暂不可用'
      payload.value = null
      emit('overviewReady', [])
      return
    }
    payload.value = res.data
    emit('overviewReady', res.data.objects || [])
  } catch {
    error.value = 'E03 数据加载失败'
    payload.value = null
    emit('overviewReady', [])
  } finally {
    loading.value = false
  }
}

function handleScopeClick(scope: E03ObjectScope) {
  if (props.objectScope === scope) return
  page.value = 1
  emit('clearSelection')
  emit('changeScope', scope)
}

function handleCategoryClick(key: E03ObjectType) {
  page.value = 1
  emit('clearSelection')
  emit('changeCategory', key)
}

function handleSelectIssue(issue: E03WaterObjectItem) {
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

watch(filteredObjects, (list) => {
  if (page.value > Math.max(1, Math.ceil(list.length / PAGE_SIZE))) page.value = 1
})

onMounted(() => {
  void loadOverview()
})

defineExpose({ reload: loadOverview, payload, objects })
</script>

<template>
  <aside class="e03-panel">
    <header class="e03-head">
      <h2>水保与复绿</h2>
      <button type="button" class="e03-close" aria-label="关闭E03" @click="emit('close')">×</button>
    </header>

    <div v-if="loading" class="e03-state">正在加载…</div>
    <div v-else-if="error" class="e03-state is-error">
      {{ error }}
      <button type="button" class="e03-retry" @click="loadOverview">重试</button>
    </div>
    <template v-else>
      <section class="e03-stats" aria-label="水保对象摘要">
        <div v-for="tab in summaryTabs" :key="tab.label" class="e03-stats__cell">
          <span>{{ tab.label }}</span>
          <strong>{{ tab.value }}</strong>
        </div>
      </section>

      <div class="e03-scope-row" role="tablist" aria-label="对象范围">
        <button
          type="button"
          role="tab"
          class="e03-scope"
          :class="{ active: objectScope === 'key' }"
          @click="handleScopeClick('key')"
        >
          重点对象
        </button>
        <button
          type="button"
          role="tab"
          class="e03-scope"
          :class="{ active: objectScope === 'all' }"
          @click="handleScopeClick('all')"
        >
          全部对象
        </button>
      </div>

      <div class="e03-cat-row" aria-label="水保业务分类">
        <button
          v-for="tab in categoryTabs"
          :key="tab.key"
          type="button"
          class="e03-cat"
          :class="{ active: categoryFilter === tab.key }"
          @click="handleCategoryClick(tab.key)"
        >
          <span>{{ tab.label }}</span>
          <em>{{ tab.value }}</em>
        </button>
      </div>

      <div class="e03-body">
        <div class="e03-list-title">
          {{ objectScope === 'key' ? '重点水保对象' : '全部水保对象' }}
        </div>
        <div class="e03-list">
          <button
            v-for="item in pagedObjects"
            :key="item.id"
            type="button"
            class="e03-row"
            :class="{ active: selectedIssueId === item.id, 'no-locate': !item.canLocate }"
            @click="handleSelectIssue(item)"
          >
            <div class="e03-row__top">
              <span class="e03-row__type">{{ item.objectName }}</span>
              <em class="e03-row__status">{{ item.status }}</em>
            </div>
            <div class="e03-row__loc">
              <b>{{ item.objectTypeLabel }}</b>
              {{ item.locationText }}
            </div>
            <div class="e03-row__factor">
              <span>面积 {{ item.areaHa }} ha</span>
              <span v-if="!item.canLocate" class="warn">无法定位</span>
            </div>
          </button>
          <p v-if="!pagedObjects.length" class="e03-empty">当前分类暂无对象</p>
        </div>

        <nav class="e03-pager" aria-label="对象分页">
          <span class="e03-pager__summary">{{ pagerSummary }}</span>
          <div v-if="showPageControls" class="e03-pager__controls">
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
.e03-panel {
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
.e03-head {
  flex-shrink: 0;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  h2 { margin: 0; font-size: 22px; font-weight: 700; color: #f3f8ff; }
}
.e03-close {
  width: 30px;
  height: 30px;
  font-size: 18px;
  border: 1px solid rgba(105, 227, 111, 0.35);
  background: rgba(8, 40, 69, 0.72);
  color: #f3f8ff;
  border-radius: 6px;
  cursor: pointer;
}
.e03-state {
  padding: 24px 8px;
  text-align: center;
  color: #8ba6c3;
  font-size: 13px;
  &.is-error { color: #ff9f2f; }
}
.e03-retry {
  display: block;
  margin: 10px auto 0;
  padding: 4px 14px;
  border: 1px solid rgba(105, 227, 111, 0.35);
  background: rgba(8, 40, 69, 0.72);
  color: #69e36f;
  border-radius: 4px;
  cursor: pointer;
}
.e03-stats {
  flex-shrink: 0;
  height: 64px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1px solid rgba(105, 227, 111, 0.22);
  border-radius: 6px;
  background: rgba(8, 40, 69, 0.4);
  margin-bottom: 10px;
}
.e03-stats__cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border-right: 1px solid rgba(105, 227, 111, 0.12);
  &:last-child { border-right: 0; }
  span { font-size: 12px; color: #8ba6c3; }
  strong { font-size: 18px; color: #69e36f; font-weight: 700; }
}
.e03-scope-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 10px;
}
.e03-scope {
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
.e03-cat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  margin-bottom: 10px;
}
.e03-cat {
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
  font-size: 11px;
  &.active {
    color: #f3f8ff;
    border-color: rgba(105, 227, 111, 0.5);
    background: rgba(105, 227, 111, 0.14);
  }
  em { font-style: normal; font-size: 16px; font-weight: 700; color: #69e36f; }
}
.e03-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.e03-list-title { font-size: 13px; color: #8ba6c3; margin-bottom: 8px; }
.e03-list {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: hidden;
}
.e03-row {
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
}
.e03-row__top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}
.e03-row__type { font-size: 14px; font-weight: 700; color: #f3f8ff; }
.e03-row__status { font-style: normal; font-size: 12px; color: #ffb347; }
.e03-row__loc {
  font-size: 12px;
  color: #9fb6cd;
  margin-bottom: 4px;
  b { color: #69e36f; margin-right: 6px; }
}
.e03-row__factor {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: #8ba6c3;
  .warn { color: #ff9f2f; }
}
.e03-empty {
  margin: 24px 0;
  text-align: center;
  color: #8ba6c3;
  font-size: 13px;
}
.e03-pager {
  flex-shrink: 0;
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.e03-pager__summary { font-size: 12px; color: #8ba6c3; }
.e03-pager__controls {
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
    &.active { color: #f3f8ff; border-color: rgba(105, 227, 111, 0.55); }
    &:disabled { opacity: 0.4; cursor: default; }
  }
}
</style>
