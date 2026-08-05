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
  openDetail: []
}>()

const loading = ref(false)
const error = ref('')
const detail = ref<S02RiskDetail | null>(null)
let loadSeq = 0

const title = computed(
  () => detail.value?.title || props.risk?.title || '安全风险点',
)

const typeLine = computed(() => {
  const r = detail.value || props.risk
  if (!r) return ''
  const section = extractSectionLabel(r.title, r.locationText) || ''
  return typeWithSection(r.riskType || '安全风险', section)
})

const level = computed(() => detail.value?.riskLevel || props.risk?.riskLevel || '')
const status = computed(() => detail.value?.status || props.risk?.status || '—')
const location = computed(() => detail.value?.locationText || props.risk?.locationText || '—')
const measure = computed(() => detail.value?.controlMeasure || props.risk?.controlMeasure || '—')
const startDate = computed(() => {
  const raw = detail.value?.controlStartDate || props.risk?.controlStartDate
  return raw ? String(raw).slice(0, 10) : '—'
})
const businessCode = computed(() => detail.value?.businessCode || props.risk?.businessCode || '—')

function levelClass(lv: string) {
  return lv === '重大' ? 'major' : 'larger'
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
  <aside v-if="visible && risk" class="s02-map-summary" aria-label="风险点摘要">
    <header class="s02-map-summary__head">
      <div>
        <p>{{ typeLine }}</p>
        <h3>{{ title }}</h3>
      </div>
      <button type="button" class="s02-map-summary__close" aria-label="关闭摘要" @click="emit('close')">×</button>
    </header>

    <div class="s02-map-summary__meta">
      <span class="level" :class="levelClass(level)">{{ level || '—' }}</span>
      <span>{{ businessCode }}</span>
    </div>

    <div v-if="loading && !detail" class="s02-map-summary__state">加载详情…</div>
    <div v-else-if="error && !detail" class="s02-map-summary__state is-error">{{ error }}</div>
    <template v-else>
      <div class="s02-map-summary__metrics">
        <div>
          <span>管控状态</span>
          <strong>{{ status }}</strong>
        </div>
        <div>
          <span>起控日期</span>
          <strong>{{ startDate }}</strong>
        </div>
        <div class="full">
          <span>位置</span>
          <strong>{{ location }}</strong>
        </div>
        <div class="full">
          <span>管控措施</span>
          <strong class="measure">{{ measure }}</strong>
        </div>
      </div>
      <button type="button" class="s02-map-summary__detail" @click="emit('openDetail')">
        查看管控详情
      </button>
    </template>
  </aside>
</template>

<style scoped lang="scss">
.s02-map-summary {
  position: absolute;
  right: 12px;
  bottom: 12px;
  z-index: 20;
  width: min(328px, calc(100% - 24px));
  padding: 10px 12px 12px;
  border-radius: 8px;
  border: 1px solid rgba(47, 156, 255, 0.45);
  background: rgba(4, 22, 40, 0.92);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
  color: #d7e6f5;
  backdrop-filter: blur(6px);
  animation: s02-summary-in 0.22s ease-out;
}

@keyframes s02-summary-in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.s02-map-summary__head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: flex-start;

  p {
    margin: 0;
    font-size: 12px;
    color: #8ba6c3;
  }

  h3 {
    margin: 3px 0 0;
    font-size: 15px;
    line-height: 1.35;
    color: #f3f8ff;
    font-weight: 700;
  }
}

.s02-map-summary__close {
  width: 26px;
  height: 26px;
  border: 1px solid rgba(47, 156, 255, 0.4);
  border-radius: 5px;
  background: rgba(8, 40, 69, 0.65);
  color: #f3f8ff;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  flex-shrink: 0;
}

.s02-map-summary__meta {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #8ba6c3;

  .level {
    border-radius: 3px;
    padding: 1px 6px;
    &.major {
      color: #ff4f5e;
      border: 1px solid rgba(255, 79, 94, 0.45);
    }
    &.larger {
      color: #ffb347;
      border: 1px solid rgba(255, 179, 71, 0.45);
    }
  }
}

.s02-map-summary__metrics {
  margin-top: 8px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 10px;

  .full { grid-column: 1 / -1; }

  span {
    display: block;
    font-size: 11px;
    color: #7f95ad;
  }

  strong {
    display: block;
    margin-top: 1px;
    font-size: 13px;
    color: #e8f3ff;
    font-weight: 600;
    line-height: 1.35;

    &.measure {
      font-weight: 500;
      color: #c3d4e8;
    }
  }
}

.s02-map-summary__state {
  margin-top: 12px;
  min-height: 48px;
  display: grid;
  place-items: center;
  font-size: 12px;
  color: #8ba6c3;
  &.is-error { color: #ff9f2f; }
}

.s02-map-summary__detail {
  margin-top: 10px;
  width: 100%;
  padding: 6px 0;
  font-size: 12px;
  border: 1px solid rgba(47, 156, 255, 0.45);
  border-radius: 5px;
  background: rgba(47, 156, 255, 0.12);
  color: #2f9cff;
  cursor: pointer;
}
</style>
