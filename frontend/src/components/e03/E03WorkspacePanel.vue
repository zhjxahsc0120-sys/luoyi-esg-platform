<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { getE03EcoObjectDetail, getE03EcoObjects } from '@/services/api'
import type {
  E03CategoryFilter,
  E03EcoObjectDetail,
  E03EcoObjectItem,
  E03EcoObjectsPayload,
  E03PanelLayer,
} from '@/types/e03'
import { typeWithSection } from '@/utils/section-label'

const props = defineProps<{
  selectedIssueId: number | null
  layer: E03PanelLayer
  categoryFilter: E03CategoryFilter
}>()

const emit = defineEmits<{
  close: []
  changeCategory: [category: E03CategoryFilter]
  selectIssue: [issue: E03EcoObjectItem]
  clearSelection: []
  overviewReady: [issues: E03EcoObjectItem[]]
}>()

const PAGE_SIZE = 3
const loading = ref(false)
const error = ref('')
const payload = ref<E03EcoObjectsPayload | null>(null)
const detail = ref<E03EcoObjectDetail | null>(null)
const detailLoading = ref(false)
const page = ref(1)

const overview = computed(() => payload.value?.overview || {
  areaCount: 0,
  protectedCount: 0,
  riskCount: 0,
  riskStatus: '正常',
})

const objects = computed(() => payload.value?.objects || [])

const filteredObjects = computed(() => {
  if (props.categoryFilter === 'ALL') return objects.value
  return objects.value.filter((o) => o.objectKind === props.categoryFilter)
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

const selected = computed(() => {
  if (props.selectedIssueId == null) return null
  return objects.value.find((o) => o.id === props.selectedIssueId) || null
})

const statsCells = computed(() => [
  {
    key: 'ALL' as E03CategoryFilter,
    label: '全部对象',
    value: String(overview.value.areaCount + overview.value.protectedCount),
    clickable: true,
  },
  {
    key: 'SENSITIVE' as E03CategoryFilter,
    label: '敏感区域',
    value: String(overview.value.areaCount),
    clickable: true,
  },
  {
    key: 'PROTECTED' as E03CategoryFilter,
    label: '保护对象',
    value: String(overview.value.protectedCount),
    clickable: true,
  },
  {
    key: null as E03CategoryFilter | null,
    label: '风险状态',
    value: overview.value.riskStatus || '正常',
    clickable: false,
  },
])

function display(value: unknown) {
  if (value === null || value === undefined || value === '') return '—'
  return String(value)
}

function typeLine(item: E03EcoObjectItem) {
  return typeWithSection(item.objectKindLabel || '生态对象', item.sectionCode || '')
}

async function loadOverview() {
  loading.value = true
  error.value = ''
  try {
    const res = await getE03EcoObjects()
    if (!res || res.code !== 0 || !res.data) {
      error.value = 'E03 Demo 生态对象暂不可用，请检查服务后重试'
      payload.value = null
      emit('overviewReady', [])
      return
    }
    payload.value = res.data
    emit('overviewReady', res.data.objects || [])
  } catch {
    error.value = 'E03 数据加载失败，请稍后重试'
    payload.value = null
    emit('overviewReady', [])
  } finally {
    loading.value = false
  }
}

async function loadDetail(id: number) {
  detailLoading.value = true
  detail.value = null
  try {
    const res = await getE03EcoObjectDetail(id)
    if (res && res.code === 0 && res.data) detail.value = res.data
  } finally {
    detailLoading.value = false
  }
}

function handleCategoryClick(key: E03CategoryFilter | null) {
  if (!key) return
  if (props.categoryFilter === key) {
    emit('clearSelection')
    emit('changeCategory', key)
    return
  }
  page.value = 1
  emit('clearSelection')
  emit('changeCategory', key)
}

function handleSelectIssue(issue: E03EcoObjectItem) {
  emit('selectIssue', issue)
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

watch(filteredObjects, (list) => {
  if (page.value > Math.max(1, Math.ceil(list.length / PAGE_SIZE))) {
    page.value = 1
  }
})

watch(
  () => props.selectedIssueId,
  (id) => {
    if (id == null) {
      detail.value = null
      return
    }
    void loadDetail(id)
  },
)

onMounted(() => {
  void loadOverview()
})

defineExpose({ reload: loadOverview, payload, objects })
</script>

<template>
  <aside class="e03-panel">
    <header class="e03-head">
      <h2>生态保护管控</h2>
      <button type="button" class="e03-close" aria-label="关闭E03" @click="emit('close')">×</button>
    </header>

    <div v-if="loading" class="e03-state">正在加载…</div>
    <div v-else-if="error" class="e03-state is-error">
      {{ error }}
      <button class="e03-retry" @click="loadOverview">重试</button>
    </div>
    <template v-else>
      <section class="e03-stats" aria-label="生态保护摘要">
        <button
          v-for="tab in statsCells"
          :key="tab.label"
          type="button"
          class="e03-stats__cell"
          :class="{ active: tab.clickable && categoryFilter === tab.key, 'is-static': !tab.clickable }"
          :disabled="!tab.clickable"
          @click="handleCategoryClick(tab.key)"
        >
          <span>{{ tab.label }}</span>
          <strong :class="{ 'is-text': !tab.clickable }">{{ tab.value }}</strong>
        </button>
      </section>

      <div class="e03-body">
        <div class="e03-col e03-col--list">
          <div class="e03-list-title">生态敏感区 / 保护对象</div>
          <div class="e03-list">
            <button
              v-for="item in pagedObjects"
              :key="item.id"
              type="button"
              class="e03-row"
              :class="{ active: selectedIssueId === item.id }"
              @click="handleSelectIssue(item)"
            >
              <div class="e03-row__top">
                <span class="e03-row__type">{{ typeLine(item) }}</span>
                <em class="e03-row__status">风险 {{ item.riskLevel }}</em>
              </div>
              <div class="e03-row__title">{{ item.objectName }}</div>
              <div class="e03-row__loc">{{ item.locationText || '—' }}</div>
              <div class="e03-row__meta">
                <span>{{ item.riskStatus }}</span>
                <span>{{ item.responsibleUnit }}</span>
              </div>
            </button>

            <p v-if="!pagedObjects.length" class="e03-empty">当前分类暂无生态保护对象</p>
          </div>

          <nav class="e03-pager" aria-label="对象分页">
            <span class="e03-pager__summary">{{ pagerSummary }}</span>
            <div v-if="showPageControls" class="e03-pager__controls">
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

        <div class="e03-col e03-col--detail">
          <div class="e03-list-title">对象详情</div>
          <div v-if="!selected" class="e03-empty e03-empty--detail">请选择左侧对象查看详情</div>
          <div v-else-if="detailLoading" class="e03-state">正在加载详情…</div>
          <div v-else class="e03-detail">
            <section class="e03-section">
              <h3>对象信息</h3>
              <dl>
                <div><dt>名称</dt><dd>{{ display(detail?.objectName || selected.objectName) }}</dd></div>
                <div><dt>编码</dt><dd>{{ display(detail?.objectCode || selected.objectCode) }}</dd></div>
                <div><dt>类型</dt><dd>{{ display(detail?.objectKindLabel || selected.objectKindLabel) }}</dd></div>
                <div><dt>责任单位</dt><dd>{{ display(detail?.responsibleUnit || selected.responsibleUnit) }}</dd></div>
              </dl>
            </section>
            <section class="e03-section">
              <h3>位置</h3>
              <p>{{ display(detail?.locationText || selected.locationText) }}</p>
            </section>
            <section class="e03-section">
              <h3>保护要求</h3>
              <p>{{ display(detail?.protectionRequirement || selected.protectionRequirement) }}</p>
            </section>
            <section class="e03-section">
              <h3>风险状态</h3>
              <p>
                {{ display(detail?.riskLevel || selected.riskLevel) }}
                ·
                {{ display(detail?.riskStatus || selected.riskStatus) }}
              </p>
            </section>
            <section class="e03-section">
              <h3>关联事项</h3>
              <p>{{ display(detail?.relatedMatter || selected.relatedMatter) }}</p>
            </section>
          </div>
        </div>
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
      background: #69e36f;
      box-shadow: 0 0 0 3px rgba(105, 227, 111, 0.18);
    }
  }
}

.e03-close {
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
  font-size: 13px;
  border: 1px solid rgba(105, 227, 111, 0.35);
  background: rgba(8, 40, 69, 0.72);
  color: #69e36f;
  border-radius: 4px;
  cursor: pointer;
}

.e03-stats {
  flex-shrink: 0;
  height: 58px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border: 1px solid rgba(105, 227, 111, 0.22);
  border-radius: 6px;
  background: rgba(8, 40, 69, 0.4);
  margin-bottom: 10px;
  overflow: hidden;
}

.e03-stats__cell {
  border: 0;
  border-right: 1px solid rgba(105, 227, 111, 0.16);
  background: transparent;
  color: #8ba6c3;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  position: relative;
  min-width: 0;
  padding: 0 4px;

  &:last-child { border-right: 0; }

  span {
    font-size: 12px;
    line-height: 1.2;
  }

  strong {
    font-size: 18px;
    line-height: 1.1;
    font-family: Bahnschrift, "DIN Alternate", Arial, sans-serif;
    color: #d7e6f5;
    font-weight: 700;

    &.is-text {
      font-size: 14px;
      font-family: inherit;
      color: #69e36f;
    }
  }

  &.active {
    color: #c8f5cb;
    strong { color: #69e36f; }
    &::after {
      content: '';
      position: absolute;
      left: 18%;
      right: 18%;
      bottom: 0;
      height: 2px;
      background: #69e36f;
    }
  }

  &.is-static {
    cursor: default;
  }

  &:disabled {
    cursor: default;
  }
}

.e03-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.e03-col {
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  &--list { flex: 0 1 48%; }
  &--detail { flex: 1 1 52%; }
}

.e03-list-title {
  flex-shrink: 0;
  margin-bottom: 8px;
  font-size: 14px;
  color: #8ba6c3;
}

.e03-list,
.e03-detail {
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.e03-row {
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

.e03-row__top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.e03-row__type {
  font-size: 13px;
  color: #c3d4e8;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.e03-row__status {
  flex-shrink: 0;
  font-style: normal;
  font-size: 12px;
  color: #69e36f;
  border: 1px solid rgba(105, 227, 111, 0.45);
  border-radius: 3px;
  padding: 1px 6px;
  background: rgba(105, 227, 111, 0.08);
}

.e03-row__title {
  margin-top: 5px;
  font-size: 14px;
  font-weight: 600;
  color: #e8f3ff;
  line-height: 1.4;
}

.e03-row__loc,
.e03-row__meta {
  margin-top: 3px;
  font-size: 12px;
  color: #8ba6c3;
}

.e03-row__meta {
  display: flex;
  justify-content: space-between;
  gap: 6px;
}

.e03-empty {
  margin: 16px 0 0;
  text-align: center;
  font-size: 13px;
  color: #8ba6c3;

  &--detail { margin-top: 24px; }
}

.e03-pager {
  flex-shrink: 0;
  margin-top: 8px;
  min-height: 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.e03-pager__summary {
  font-size: 12px;
  color: #8ba6c3;
  white-space: nowrap;
}

.e03-pager__controls {
  display: flex;
  gap: 6px;

  button {
    min-width: 26px;
    height: 26px;
    border: 1px solid rgba(105, 227, 111, 0.28);
    border-radius: 4px;
    background: rgba(8, 40, 69, 0.5);
    color: #8ba6c3;
    cursor: pointer;
    font-size: 12px;

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

.e03-section {
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

  dl {
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 6px;

    div {
      display: grid;
      grid-template-columns: 64px 1fr;
      gap: 6px;
      font-size: 12px;
    }

    dt { color: #8ba6c3; }
    dd { margin: 0; color: #e8f3ff; }
  }
}
</style>
