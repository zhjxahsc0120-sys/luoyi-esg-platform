<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { getE03WaterObjectDetail } from '@/services/api'
import type { E03WaterObjectDetail, E03WaterObjectItem } from '@/types/e03'

const props = defineProps<{
  object: E03WaterObjectItem | null
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const loading = ref(false)
const error = ref('')
const detail = ref<E03WaterObjectDetail | null>(null)
let loadSeq = 0

const title = computed(() => detail.value?.objectName || props.object?.objectName || '水保对象')
const location = computed(() => detail.value?.locationText || props.object?.locationText || '—')
const area = computed(() => {
  const v = detail.value?.areaHa ?? props.object?.areaHa
  return v != null ? `${v} ha` : '—'
})
const approval = computed(() => detail.value?.approvalStatus || props.object?.approvalStatus || '—')
const regreen = computed(() => detail.value?.regreenStatus || props.object?.regreenStatus || '—')
const imagery = computed(() => detail.value?.imageryNote || props.object?.imageryNote || '—')

async function loadDetail(id: number) {
  const seq = ++loadSeq
  loading.value = true
  error.value = ''
  try {
    const res = await getE03WaterObjectDetail(id)
    if (seq !== loadSeq) return
    if (!res || res.code !== 0 || !res.data) {
      detail.value = null
      error.value = '详情暂不可用'
      return
    }
    detail.value = res.data
  } catch {
    if (seq !== loadSeq) return
    detail.value = null
    error.value = '详情加载失败'
  } finally {
    if (seq === loadSeq) loading.value = false
  }
}

watch(
  () => [props.visible, props.object?.id] as const,
  ([visible, id]) => {
    if (!visible || id == null) {
      detail.value = null
      error.value = ''
      return
    }
    void loadDetail(id)
  },
  { immediate: true },
)
</script>

<template>
  <aside v-if="visible && object" class="e03-map-summary" aria-label="水保对象摘要">
    <header class="e03-map-summary__head">
      <div>
        <p>{{ object.objectTypeLabel }} · {{ object.objectCode }}</p>
        <h3>{{ title }}</h3>
      </div>
      <button type="button" class="e03-map-summary__close" aria-label="关闭" @click="emit('close')">×</button>
    </header>

    <div v-if="loading && !detail" class="e03-map-summary__state">加载详情…</div>
    <div v-else-if="error && !detail" class="e03-map-summary__state is-error">{{ error }}</div>
    <div v-else class="e03-map-summary__metrics">
      <div class="full">
        <span>位置</span>
        <strong>{{ location }}</strong>
      </div>
      <div>
        <span>面积</span>
        <strong>{{ area }}</strong>
      </div>
      <div>
        <span>审批状态</span>
        <strong>{{ approval }}</strong>
      </div>
      <div class="full">
        <span>复绿情况</span>
        <strong>{{ regreen }}</strong>
      </div>
      <div class="full">
        <span>影像资料</span>
        <strong>{{ imagery }}</strong>
      </div>
    </div>
  </aside>
</template>

<style scoped lang="scss">
.e03-map-summary {
  position: absolute;
  right: 18px;
  bottom: 18px;
  z-index: 20;
  width: 360px;
  max-height: min(52vh, 400px);
  overflow: auto;
  padding: 12px 14px 14px;
  border: 1px solid rgba(105, 227, 111, 0.4);
  border-radius: 8px;
  background: rgba(4, 25, 48, 0.94);
  color: #d7e6f5;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.35);
}
.e03-map-summary__head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
  p { margin: 0 0 4px; font-size: 12px; color: #8ba6c3; }
  h3 { margin: 0; font-size: 16px; color: #f3f8ff; }
}
.e03-map-summary__close {
  width: 28px;
  height: 28px;
  border: 1px solid rgba(105, 227, 111, 0.35);
  background: rgba(8, 40, 69, 0.72);
  color: #f3f8ff;
  border-radius: 6px;
  cursor: pointer;
}
.e03-map-summary__state {
  padding: 12px 0;
  text-align: center;
  color: #8ba6c3;
  font-size: 12px;
  &.is-error { color: #ff9f2f; }
}
.e03-map-summary__metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  div {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 8px;
    border-radius: 6px;
    background: rgba(8, 40, 69, 0.55);
    &.full { grid-column: 1 / -1; }
    span { font-size: 11px; color: #8ba6c3; }
    strong { font-size: 13px; color: #e8f3ff; font-weight: 600; }
  }
}
</style>
