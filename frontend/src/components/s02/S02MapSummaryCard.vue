<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { getS02RiskDetail } from '@/services/api'
import type { S02RiskDetail, S02RiskItem } from '@/types/s02'
import { extractSectionLabel, typeWithSection } from '@/utils/section-label'

const props = defineProps<{
  risk: S02RiskItem | null
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
  openSpecialPlan: []
}>()

const loading = ref(false)
const error = ref('')
const detail = ref<S02RiskDetail | null>(null)
let loadSeq = 0

const title = computed(() => detail.value?.title || props.risk?.title || '风险源')
const typeLine = computed(() => {
  const r = detail.value || props.risk
  if (!r) return ''
  const section = r.sectionCode || extractSectionLabel(r.title, r.locationText) || ''
  return typeWithSection(r.businessCategoryLabel || r.riskType || '风险源', section)
})
const level = computed(() => detail.value?.riskLevel || props.risk?.riskLevel || '')
const location = computed(() => detail.value?.locationText || props.risk?.locationText || '—')
const description = computed(() => detail.value?.description || props.risk?.description || '—')
const measure = computed(() => detail.value?.controlMeasure || props.risk?.controlMeasure || '—')
const specialPlan = computed(
  () => detail.value?.specialPlanName || props.risk?.specialPlanName || '—',
)
const specialPlanStatus = computed(
  () => detail.value?.specialPlanStatus || props.risk?.specialPlanStatus || '',
)
const approval = computed(
  () => detail.value?.approvalStatus || props.risk?.approvalStatus || '—',
)
const responsible = computed(
  () => detail.value?.responsibleOrgName || props.risk?.responsibleOrgName || '—',
)
const hasSpecialPlanLink = computed(() => {
  const name = detail.value?.specialPlanName || props.risk?.specialPlanName
  return Boolean(name)
})

function levelClass(lv: string) {
  if (lv === '重大') return 'major'
  if (lv === '较大') return 'larger'
  return 'general'
}

async function loadDetail(id: number) {
  const seq = ++loadSeq
  loading.value = true
  error.value = ''
  try {
    const res = await getS02RiskDetail(id)
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
  () => [props.visible, props.risk?.id] as const,
  ([visible, riskId]) => {
    if (!visible || riskId == null) {
      detail.value = null
      error.value = ''
      return
    }
    void loadDetail(riskId)
  },
  { immediate: true },
)
</script>

<template>
  <aside v-if="visible && risk" class="s02-map-summary" aria-label="风险源摘要">
    <header class="s02-map-summary__head">
      <div>
        <p>{{ typeLine }}</p>
        <h3>{{ title }}</h3>
      </div>
      <button type="button" class="s02-map-summary__close" aria-label="关闭摘要" @click="emit('close')">×</button>
    </header>

    <div class="s02-map-summary__meta">
      <span class="level" :class="levelClass(level)">{{ level || '—' }}</span>
      <span>{{ risk.businessCode }}</span>
    </div>

    <div v-if="loading && !detail" class="s02-map-summary__state">加载详情…</div>
    <div v-else-if="error && !detail" class="s02-map-summary__state is-error">{{ error }}</div>
    <template v-else>
      <div class="s02-map-summary__metrics">
        <div class="full">
          <span>位置</span>
          <strong>{{ location }}</strong>
        </div>
        <div class="full">
          <span>描述</span>
          <strong class="measure">{{ description }}</strong>
        </div>
        <div class="full">
          <span>管控措施</span>
          <strong class="measure">{{ measure }}</strong>
        </div>
        <div class="full">
          <span>专项方案</span>
          <strong>
            {{ specialPlan }}
            <em v-if="specialPlanStatus">（{{ specialPlanStatus }}）</em>
          </strong>
        </div>
        <div>
          <span>审批状态</span>
          <strong>{{ approval }}</strong>
        </div>
        <div>
          <span>责任单位</span>
          <strong>{{ responsible }}</strong>
        </div>
      </div>
      <button
        v-if="hasSpecialPlanLink"
        type="button"
        class="s02-map-summary__detail"
        @click="emit('openSpecialPlan')"
      >
        查看重大风险专项方案
      </button>
    </template>
  </aside>
</template>

<style scoped lang="scss">
.s02-map-summary {
  position: absolute;
  right: 18px;
  bottom: 18px;
  z-index: 20;
  width: 380px;
  max-height: min(56vh, 460px);
  overflow: auto;
  padding: 12px 14px 14px;
  border: 1px solid rgba(47, 156, 255, 0.45);
  border-radius: 8px;
  background: rgba(4, 25, 48, 0.94);
  color: #d7e6f5;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.35);
}
.s02-map-summary__head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
  p { margin: 0 0 4px; font-size: 12px; color: #8ba6c3; }
  h3 { margin: 0; font-size: 16px; color: #f3f8ff; line-height: 1.35; }
}
.s02-map-summary__close {
  width: 28px;
  height: 28px;
  border: 1px solid rgba(47, 156, 255, 0.4);
  background: rgba(8, 40, 69, 0.72);
  color: #f3f8ff;
  border-radius: 6px;
  cursor: pointer;
}
.s02-map-summary__meta {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 10px;
  font-size: 12px;
  color: #8ba6c3;
  .level {
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 700;
    &.major { color: #ff4f5e; background: rgba(255, 79, 94, 0.12); }
    &.larger { color: #ffb347; background: rgba(255, 179, 71, 0.12); }
    &.general { color: #2f9cff; background: rgba(47, 156, 255, 0.12); }
  }
}
.s02-map-summary__state {
  padding: 12px 0;
  text-align: center;
  color: #8ba6c3;
  font-size: 12px;
  &.is-error { color: #ff9f2f; }
}
.s02-map-summary__metrics {
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
    .measure { font-weight: 500; line-height: 1.4; }
    em { font-style: normal; color: #8ba6c3; font-weight: 500; }
  }
}
.s02-map-summary__detail {
  width: 100%;
  margin-top: 10px;
  height: 34px;
  border: 1px solid rgba(166, 108, 255, 0.45);
  background: rgba(166, 108, 255, 0.16);
  color: #e6d9ff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}
</style>
