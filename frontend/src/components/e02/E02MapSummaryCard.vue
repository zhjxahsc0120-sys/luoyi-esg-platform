<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { getE02IssueDetail } from '@/services/api'
import type { E02IssueDetail, E02IssueItem } from '@/types/e02'

const props = defineProps<{
  issue: E02IssueItem | null
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const loading = ref(false)
const error = ref('')
const detail = ref<E02IssueDetail | null>(null)
let loadSeq = 0

const title = computed(() => detail.value?.title || props.issue?.title || '环保问题')
const location = computed(() => detail.value?.locationText || props.issue?.locationText || '—')
const description = computed(() => detail.value?.description || props.issue?.description || '—')
const foundDate = computed(() => {
  const raw = detail.value?.foundDate || props.issue?.foundDate
  return raw ? String(raw).slice(0, 10) : '—'
})
const responsible = computed(
  () => detail.value?.responsibleOrgName || props.issue?.responsibleOrgName || '—',
)
const status = computed(() => detail.value?.status || props.issue?.status || '—')
const deadline = computed(() => {
  const raw = detail.value?.deadline || props.issue?.deadline
  return raw ? String(raw).slice(0, 10) : '—'
})
/** 仅展示接口/客户端回报的完成时间，不推算 */
const closedDate = computed(() => {
  const raw = detail.value?.closedDate ?? props.issue?.closedDate
  if (raw == null || raw === '') return '—'
  return String(raw).slice(0, 10)
})

async function loadDetail(id: number) {
  const seq = ++loadSeq
  loading.value = true
  error.value = ''
  try {
    const res = await getE02IssueDetail(id)
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
  () => [props.visible, props.issue?.id] as const,
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
  <aside v-if="visible && issue" class="e02-map-summary" aria-label="环保问题摘要">
    <header class="e02-map-summary__head">
      <div>
        <p>{{ issue.businessCode }} · {{ issue.businessCategoryLabel || issue.issueType }}</p>
        <h3>{{ title }}</h3>
      </div>
      <button type="button" class="e02-map-summary__close" aria-label="关闭" @click="emit('close')">×</button>
    </header>

    <div v-if="loading && !detail" class="e02-map-summary__state">加载详情…</div>
    <div v-else-if="error && !detail" class="e02-map-summary__state is-error">{{ error }}</div>
    <div v-else class="e02-map-summary__metrics">
      <div class="full">
        <span>位置</span>
        <strong>{{ location }}</strong>
      </div>
      <div class="full">
        <span>描述</span>
        <strong class="desc">{{ description }}</strong>
      </div>
      <div>
        <span>发现时间</span>
        <strong>{{ foundDate }}</strong>
      </div>
      <div>
        <span>整改状态</span>
        <strong>{{ status }}</strong>
      </div>
      <div>
        <span>整改期限</span>
        <strong>{{ deadline }}</strong>
      </div>
      <div>
        <span>整改完成时间</span>
        <strong>{{ closedDate }}</strong>
      </div>
      <div class="full">
        <span>责任单位</span>
        <strong>{{ responsible }}</strong>
      </div>
    </div>
  </aside>
</template>

<style scoped lang="scss">
.e02-map-summary {
  position: absolute;
  right: 18px;
  bottom: 18px;
  z-index: 20;
  width: 360px;
  max-height: min(52vh, 420px);
  overflow: auto;
  padding: 12px 14px 14px;
  border: 1px solid rgba(105, 227, 111, 0.4);
  border-radius: 8px;
  background: rgba(4, 25, 48, 0.94);
  color: #d7e6f5;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.35);
}
.e02-map-summary__head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
  p { margin: 0 0 4px; font-size: 12px; color: #8ba6c3; }
  h3 { margin: 0; font-size: 16px; color: #f3f8ff; line-height: 1.35; }
}
.e02-map-summary__close {
  width: 28px;
  height: 28px;
  border: 1px solid rgba(105, 227, 111, 0.35);
  background: rgba(8, 40, 69, 0.72);
  color: #f3f8ff;
  border-radius: 6px;
  cursor: pointer;
}
.e02-map-summary__state {
  padding: 12px 0;
  text-align: center;
  color: #8ba6c3;
  font-size: 12px;
  &.is-error { color: #ff9f2f; }
}
.e02-map-summary__metrics {
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
    .desc { font-weight: 500; line-height: 1.4; }
  }
}
</style>
