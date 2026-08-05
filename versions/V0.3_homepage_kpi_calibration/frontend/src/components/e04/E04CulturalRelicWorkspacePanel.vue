<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { getE04CulturalObjectDetail, getE04CulturalObjects } from '@/services/api'
import type {
  E04CulturalObjectDetail,
  E04CulturalObjectItem,
  E04CulturalObjectsPayload,
  E04CulturalPanelLayer,
} from '@/types/e04-cultural'

const props = defineProps<{
  selectedObjectId: number | null
  layer: E04CulturalPanelLayer
}>()

const emit = defineEmits<{
  close: []
  selectObject: [item: E04CulturalObjectItem]
  clearSelection: []
  overviewReady: [objects: E04CulturalObjectItem[]]
}>()

const loading = ref(false)
const error = ref('')
const payload = ref<E04CulturalObjectsPayload | null>(null)
const detail = ref<E04CulturalObjectDetail | null>(null)
const detailLoading = ref(false)

const overview = computed(() => payload.value?.overview || {
  surveyStatus: '文物调查已完成',
  objectCount: 0,
  measureRate: 100,
  riskCount: 0,
  riskStatus: '正常',
  status: '正常',
})

const objects = computed(() => payload.value?.objects || [])
const isZeroObjects = computed(() => objects.value.length === 0)

const selected = computed(() => {
  if (props.selectedObjectId == null) return null
  return objects.value.find((o) => o.id === props.selectedObjectId) || null
})

const summaryTabs = computed(() => [
  { label: '文物调查状态', value: overview.value.surveyStatus || '文物调查已完成' },
  { label: '当前保护对象数量', value: `${overview.value.objectCount}` },
  { label: '措施落实率', value: `${overview.value.measureRate}%` },
  {
    label: '风险状态',
    value: overview.value.riskStatus || overview.value.status || '正常',
  },
])

function display(value: unknown) {
  if (value === null || value === undefined || value === '') return '—'
  return String(value)
}

async function loadOverview() {
  loading.value = true
  error.value = ''
  try {
    const res = await getE04CulturalObjects()
    if (!res || res.code !== 0 || !res.data) {
      error.value = 'E04 文物保护数据暂不可用'
      payload.value = null
      emit('overviewReady', [])
      return
    }
    payload.value = res.data
    emit('overviewReady', res.data.objects || [])
  } catch {
    error.value = 'E04 数据加载失败'
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
    const res = await getE04CulturalObjectDetail(id)
    if (res && res.code === 0 && res.data) {
      detail.value = res.data
    }
  } finally {
    detailLoading.value = false
  }
}

function handleSelect(item: E04CulturalObjectItem) {
  if (props.selectedObjectId === item.id) {
    emit('clearSelection')
    return
  }
  emit('selectObject', item)
}

watch(
  () => props.selectedObjectId,
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
  <aside class="e04-panel">
    <header class="e04-head">
      <h2>文物保护管控</h2>
      <button type="button" class="e04-close" aria-label="关闭E04" @click="emit('close')">×</button>
    </header>

    <div v-if="loading" class="e04-state">正在加载…</div>
    <div v-else-if="error" class="e04-state is-error">
      {{ error }}
      <button class="e04-retry" @click="loadOverview">重试</button>
    </div>
    <template v-else>
      <section class="e04-stats" aria-label="文物保护摘要">
        <div v-for="tab in summaryTabs" :key="tab.label" class="e04-stats__cell">
          <span>{{ tab.label }}</span>
          <strong :class="{ 'is-text': tab.label === '文物调查状态' || tab.label === '风险状态' }">
            {{ tab.value }}
          </strong>
        </div>
      </section>

      <div v-if="isZeroObjects" class="e04-zero" role="status">
        <p>文物调查已完成</p>
        <p>当前保护对象数量 {{ overview.objectCount }}</p>
        <p>风险状态 {{ overview.riskStatus || overview.status || '正常' }}</p>
      </div>

      <div v-else class="e04-body">
        <div class="e04-col e04-col--list">
          <div class="e04-list-title">文物保护对象列表</div>
          <div class="e04-list">
            <button
              v-for="item in objects"
              :key="item.id"
              type="button"
              class="e04-row"
              :class="{ active: selectedObjectId === item.id }"
              @click="handleSelect(item)"
            >
              <div class="e04-row__top">
                <span class="e04-row__type">{{ item.relicType || '—' }}</span>
                <em class="e04-row__status">{{ item.riskStatus || '正常' }}</em>
              </div>
              <div class="e04-row__title">{{ item.relicName || '—' }}</div>
              <div class="e04-row__loc">{{ item.locationDesc || '—' }}</div>
              <div class="e04-row__meta">
                <span>{{ item.protectionLevel || '—' }}</span>
                <span>{{ item.responsibleUnit || '—' }}</span>
              </div>
            </button>
          </div>
        </div>

        <div class="e04-col e04-col--detail">
          <div class="e04-list-title">对象详情</div>
          <div v-if="!selected" class="e04-empty e04-empty--detail">请选择左侧保护对象查看详情</div>
          <div v-else-if="detailLoading" class="e04-state">正在加载详情…</div>
          <div v-else class="e04-detail">
            <section class="e04-section">
              <h3>基础信息</h3>
              <dl>
                <div><dt>名称</dt><dd>{{ display(detail?.relicName || selected.relicName) }}</dd></div>
                <div><dt>编码</dt><dd>{{ display(detail?.relicCode || selected.relicCode) }}</dd></div>
                <div><dt>类型</dt><dd>{{ display(detail?.relicType || selected.relicType) }}</dd></div>
                <div><dt>位置</dt><dd>{{ display(detail?.locationDesc || selected.locationDesc) }}</dd></div>
                <div><dt>责任单位</dt><dd>{{ display(detail?.responsibleUnit || selected.responsibleUnit) }}</dd></div>
              </dl>
            </section>
            <section class="e04-section">
              <h3>保护等级</h3>
              <p>{{ display(detail?.protectionLevel || selected.protectionLevel) }}</p>
            </section>
            <section class="e04-section">
              <h3>施工影响分析</h3>
              <p>{{ display(detail?.constructionImpact) }}</p>
              <p class="muted">保护范围：{{ display(detail?.protectionScope) }}</p>
            </section>
            <section class="e04-section">
              <h3>保护措施</h3>
              <p>{{ display(detail?.protectionMeasure) }}</p>
            </section>
            <section class="e04-section">
              <h3>风险状态</h3>
              <p>{{ display(detail?.riskStatus || selected.riskStatus || '正常') }}</p>
            </section>
            <section class="e04-section">
              <h3>资料情况</h3>
              <p>{{ display(detail?.materialStatus) }}</p>
              <p class="muted">更新：{{ display(detail?.updateTime || selected.updateTime) }}</p>
            </section>
          </div>
        </div>
      </div>
    </template>
  </aside>
</template>

<style scoped lang="scss">
.e04-panel {
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

.e04-head {
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

.e04-close {
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

.e04-state {
  padding: 24px 8px;
  text-align: center;
  color: #8ba6c3;
  font-size: 13px;
  &.is-error { color: #ff9f2f; }
}

.e04-retry {
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

.e04-stats {
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

.e04-stats__cell {
  border-right: 1px solid rgba(105, 227, 111, 0.16);
  color: #8ba6c3;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: 0 4px;
  min-width: 0;

  &:last-child { border-right: 0; }

  span {
    font-size: 12px;
    line-height: 1.2;
  }

  strong {
    font-size: 18px;
    line-height: 1.1;
    font-family: Bahnschrift, "DIN Alternate", Arial, sans-serif;
    color: #69e36f;
    font-weight: 700;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;

    &.is-text {
      font-size: 13px;
      font-family: inherit;
      font-weight: 600;
    }
  }
}

.e04-zero {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border: 1px solid rgba(105, 227, 111, 0.22);
  border-radius: 6px;
  background: rgba(8, 40, 69, 0.35);
  color: #c8f5cb;
  font-size: 15px;
  line-height: 1.5;

  p {
    margin: 0;
  }
}

.e04-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.e04-col {
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  &--list {
    flex: 0 1 46%;
  }

  &--detail {
    flex: 1 1 54%;
  }
}

.e04-list-title {
  flex-shrink: 0;
  margin-bottom: 8px;
  font-size: 14px;
  color: #8ba6c3;
}

.e04-list,
.e04-detail {
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.e04-row {
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

.e04-row__top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.e04-row__type {
  font-size: 13px;
  color: #c3d4e8;
}

.e04-row__status {
  flex-shrink: 0;
  font-style: normal;
  font-size: 12px;
  color: #69e36f;
  border: 1px solid rgba(105, 227, 111, 0.45);
  border-radius: 3px;
  padding: 1px 6px;
  background: rgba(105, 227, 111, 0.08);
}

.e04-row__title {
  margin-top: 5px;
  font-size: 14px;
  font-weight: 600;
  color: #e8f3ff;
  line-height: 1.4;
}

.e04-row__loc,
.e04-row__meta {
  margin-top: 3px;
  font-size: 12px;
  color: #8ba6c3;
}

.e04-row__meta {
  display: flex;
  justify-content: space-between;
  gap: 6px;
}

.e04-empty {
  margin: 16px 0 0;
  text-align: center;
  font-size: 13px;
  color: #8ba6c3;

  &--detail {
    margin-top: 24px;
  }
}

.e04-section {
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
      grid-template-columns: 64px 1fr;
      gap: 6px;
      font-size: 12px;
    }

    dt {
      color: #8ba6c3;
    }

    dd {
      margin: 0;
      color: #e8f3ff;
    }
  }
}
</style>
