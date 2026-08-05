<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { getS02RiskDetail } from '@/services/api'
import type { S02RiskDetail } from '@/types/s02'

const props = defineProps<{
  riskId: number | null
  /** 右侧工作台占用时，弹窗翻到地图左侧 */
  flipLeft?: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const loading = ref(false)
const error = ref('')
const detail = ref<S02RiskDetail | null>(null)
const activeTab = ref<'history' | 'evidence'>('history')

const hasHistory = computed(() => (detail.value?.history?.length || 0) > 0)
const hasEvidence = computed(() => (detail.value?.evidence?.length || 0) > 0)

/** 甲方口径：辨识登记 → 进入在管 → 持续管控 → 销号评估 */
const progressSteps = computed(() => {
  if (!detail.value) return []
  const status = detail.value.status
  const cancelled = status === '已销号'
  return [
    { key: 'identify', label: '辨识', done: true },
    { key: 'enter', label: '在管', done: true },
    {
      key: 'control',
      label: '管控',
      done: status === '持续管控' || cancelled,
    },
    { key: 'cancel', label: '销号', done: cancelled },
  ]
})

async function loadDetail(id: number) {
  loading.value = true
  error.value = ''
  try {
    const res = await getS02RiskDetail(id)
    if (!res || res.code !== 0 || !res.data) {
      error.value = '详情暂不可用'
      detail.value = null
      return
    }
    detail.value = res.data
  } catch {
    error.value = '详情加载失败'
    detail.value = null
  } finally {
    loading.value = false
  }
}

watch(() => props.riskId, (id) => {
  if (id != null) {
    activeTab.value = 'history'
    void loadDetail(id)
  } else {
    detail.value = null
  }
}, { immediate: true })

function dateOnly(value?: string | null) {
  if (!value) return '—'
  return value.slice(0, 10)
}

function dateTime(value?: string | null) {
  if (!value) return '—'
  return value.length > 16 ? value.slice(0, 16) : value
}

function historyLabel(fromStatus?: string | null, toStatus?: string | null) {
  if (!fromStatus) return toStatus || '—'
  return `${fromStatus} → ${toStatus || '—'}`
}

function levelClass(level?: string) {
  return level === '重大' ? 'major' : 'larger'
}
</script>

<template>
  <div
    v-if="props.riskId != null"
    class="s02-popover"
    :class="{ 'is-flip-left': flipLeft }"
  >
    <div class="s02-popover__inner">
      <header class="s02-popover__head">
        <div class="s02-popover__head-text">
          <p>{{ detail?.riskType || '安全风险' }} · {{ detail?.businessCode || '—' }}</p>
          <h3>{{ detail?.title || '加载中…' }}</h3>
        </div>
        <button type="button" class="s02-popover__close" @click="emit('close')">×</button>
      </header>

      <div v-if="loading" class="s02-popover__state">正在加载…</div>
      <div v-else-if="error" class="s02-popover__state is-error">
        {{ error }}
        <button v-if="props.riskId" class="s02-popover__retry" @click="loadDetail(props.riskId)">重试</button>
      </div>
      <template v-else-if="detail">
        <div class="s02-popover__progress">
          <div
            v-for="(step, idx) in progressSteps"
            :key="step.key"
            class="s02-popover__step"
            :class="{ done: step.done }"
          >
            <span class="s02-popover__dot" />
            <span class="s02-popover__label">{{ step.label }}</span>
            <span v-if="idx < progressSteps.length - 1" class="s02-popover__line" />
          </div>
        </div>
        <div class="s02-popover__progress-note">在管＝纳入在管清单；管控＝措施落实与监测</div>

        <div class="s02-popover__current">
          <span class="level" :class="levelClass(detail.riskLevel)">{{ detail.riskLevel }}</span>
          <strong>当前状态：</strong>
          <span>{{ detail.status }}</span>
          <span v-if="detail.confirmStatus" class="s02-popover__confirm">{{ detail.confirmStatus }}</span>
        </div>

        <div v-if="detail.parties?.length" class="s02-popover__parties">
          <div
            v-for="p in detail.parties"
            :key="`${p.role}-${p.userName}`"
            class="s02-popover__party"
          >
            <span class="s02-popover__party-role">{{ p.roleLabel }}</span>
            <span class="s02-popover__party-name">{{ p.orgName }} {{ p.userName }}</span>
          </div>
        </div>

        <div class="s02-popover__deadline">
          <span>起控日期：{{ dateOnly(detail.controlStartDate) }}</span>
          <span v-if="detail.cancelledDate">销号日期：{{ dateOnly(detail.cancelledDate) }}</span>
          <span v-else-if="detail.reviewCycle">复核节奏：{{ detail.reviewCycle }}</span>
        </div>

        <div class="s02-popover__measure">
          <span>管控措施</span>
          <strong>{{ detail.controlMeasure || '—' }}</strong>
        </div>

        <div class="s02-popover__tabs">
          <button
            type="button"
            :class="{ active: activeTab === 'history' }"
            @click="activeTab = 'history'"
          >
            管控进展
          </button>
          <button
            type="button"
            :class="{ active: activeTab === 'evidence' }"
            @click="activeTab = 'evidence'"
          >
            管控材料
          </button>
        </div>

        <div class="s02-popover__tab-body">
          <div v-if="activeTab === 'history'" class="s02-popover__history">
            <p v-if="!hasHistory" class="s02-popover__empty">暂无管控轨迹</p>
            <div
              v-for="(h, idx) in detail.history"
              :key="idx"
              class="s02-popover__history-item"
            >
              <div class="s02-popover__history-meta">
                <span class="s02-popover__history-status">
                  {{ historyLabel(h.fromStatus, h.toStatus) }}
                </span>
                <span class="s02-popover__history-time">{{ dateTime(h.actionAt) }}</span>
              </div>
              <div v-if="h.operatorName" class="s02-popover__history-operator">
                {{ h.operatorName }} {{ h.operatorOrgName ? `（${h.operatorOrgName}）` : '' }}
              </div>
              <div v-if="h.comment" class="s02-popover__history-comment">{{ h.comment }}</div>
            </div>
          </div>

          <div v-else class="s02-popover__evidence">
            <p v-if="!hasEvidence" class="s02-popover__empty">暂无管控材料登记</p>
            <div
              v-for="e in detail.evidence"
              :key="`${e.role}-${e.title}`"
              class="s02-popover__evidence-item"
            >
              <div class="s02-popover__evidence-role">{{ e.roleLabel }}</div>
              <div class="s02-popover__evidence-title">{{ e.title }}</div>
              <div v-if="e.description" class="s02-popover__evidence-desc">{{ e.description }}</div>
              <div class="s02-popover__evidence-meta">
                {{ dateOnly(e.createdAt) }} · 建设单位台账登记
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped lang="scss">
.s02-popover {
  position: absolute;
  z-index: 28;
  top: 52px;
  left: 16px;
  width: min(380px, calc(100% - 32px));
  max-height: calc(100% - 72px);
  background: rgba(4, 25, 48, 0.98);
  border: 1px solid rgba(47, 156, 255, 0.4);
  border-radius: 8px;
  color: #d7e6f5;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45);
}

.s02-popover.is-flip-left {
  left: 16px;
  right: auto;
}

@media (max-width: 1400px) {
  .s02-popover {
    width: min(340px, calc(100% - 24px));
  }
}

.s02-popover__inner {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  max-height: calc(100vh - 120px);
  padding: 14px;
}

.s02-popover__head {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 10px;
}

.s02-popover__head-text {
  min-width: 0;

  p {
    margin: 0;
    font-size: 12px;
    color: #8ba6c3;
  }

  h3 {
    margin: 3px 0 0;
    font-size: 16px;
    font-weight: 700;
    color: #f3f8ff;
    line-height: 1.35;
  }
}

.s02-popover__close {
  width: 26px;
  height: 26px;
  font-size: 16px;
  line-height: 1;
  border: 1px solid rgba(47, 156, 255, 0.4);
  background: rgba(8, 40, 69, 0.72);
  color: #f3f8ff;
  border-radius: 5px;
  cursor: pointer;
  flex-shrink: 0;
}

.s02-popover__state {
  padding: 20px 0;
  text-align: center;
  color: #8ba6c3;
  font-size: 13px;
  &.is-error { color: #ff9f2f; }
}

.s02-popover__retry {
  display: block;
  margin: 8px auto 0;
  padding: 3px 12px;
  font-size: 12px;
  border: 1px solid rgba(47, 156, 255, 0.4);
  background: rgba(8, 40, 69, 0.72);
  color: #2f9cff;
  border-radius: 4px;
  cursor: pointer;
}

.s02-popover__progress {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 12px;
  padding: 8px 0;
}

.s02-popover__step {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;

  &.done {
    .s02-popover__dot { background: #2f9cff; box-shadow: 0 0 0 3px rgba(47, 156, 255, 0.2); }
    .s02-popover__label { color: #2f9cff; }
  }
}

.s02-popover__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(139, 166, 195, 0.4);
  flex-shrink: 0;
}

.s02-popover__label {
  font-size: 11px;
  color: #8ba6c3;
  white-space: nowrap;
}

.s02-popover__line {
  flex: 1;
  height: 1px;
  background: rgba(139, 166, 195, 0.3);
  min-width: 8px;
}

.s02-popover__progress-note {
  flex-shrink: 0;
  font-size: 10px;
  color: #6d86a3;
  margin-top: -6px;
  margin-bottom: 8px;
  text-align: center;
  line-height: 1.4;
}

.s02-popover__current {
  flex-shrink: 0;
  font-size: 13px;
  margin-bottom: 10px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;

  .level {
    border-radius: 3px;
    padding: 1px 6px;
    font-size: 12px;
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

.s02-popover__confirm {
  margin-left: 2px;
  color: #2f9cff;
  font-size: 12px;
}

.s02-popover__parties {
  flex-shrink: 0;
  margin-bottom: 10px;
}

.s02-popover__party {
  display: flex;
  gap: 8px;
  font-size: 12px;
  margin-bottom: 4px;
}

.s02-popover__party-role {
  color: #8ba6c3;
  min-width: 56px;
}

.s02-popover__party-name {
  color: #d7e6f5;
}

.s02-popover__deadline {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: #8ba6c3;
  margin-bottom: 8px;
}

.s02-popover__measure {
  flex-shrink: 0;
  margin-bottom: 10px;
  padding: 8px;
  border-radius: 6px;
  background: rgba(47, 156, 255, 0.08);
  border: 1px solid rgba(47, 156, 255, 0.2);

  span {
    display: block;
    font-size: 11px;
    color: #8ba6c3;
  }

  strong {
    display: block;
    margin-top: 2px;
    font-size: 13px;
    font-weight: 500;
    color: #e8f3ff;
    line-height: 1.4;
  }
}

.s02-popover__tabs {
  flex-shrink: 0;
  display: flex;
  gap: 0;
  border-bottom: 1px solid rgba(47, 156, 255, 0.22);
  margin-bottom: 8px;

  button {
    flex: 1;
    padding: 6px 0;
    font-size: 13px;
    border: none;
    background: transparent;
    color: #8ba6c3;
    cursor: pointer;
    border-bottom: 2px solid transparent;

    &.active {
      color: #2f9cff;
      border-bottom-color: #2f9cff;
    }
  }
}

.s02-popover__tab-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.s02-popover__empty {
  text-align: center;
  color: #8ba6c3;
  font-size: 12px;
  padding: 16px 0;
}

.s02-popover__history-item {
  padding: 8px 0;
  border-bottom: 1px solid rgba(139, 166, 195, 0.12);
}

.s02-popover__history-meta {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
}

.s02-popover__history-status {
  color: #2f9cff;
  font-weight: 600;
}

.s02-popover__history-time {
  color: #8ba6c3;
  flex-shrink: 0;
}

.s02-popover__history-operator {
  font-size: 11px;
  color: #8ba6c3;
  margin-top: 2px;
}

.s02-popover__history-comment {
  font-size: 12px;
  color: #d7e6f5;
  margin-top: 4px;
}

.s02-popover__evidence-item {
  padding: 8px 0;
  border-bottom: 1px solid rgba(139, 166, 195, 0.12);
}

.s02-popover__evidence-role {
  font-size: 11px;
  color: #2f9cff;
}

.s02-popover__evidence-title {
  font-size: 13px;
  color: #f3f8ff;
  margin-top: 2px;
}

.s02-popover__evidence-desc {
  font-size: 12px;
  color: #8ba6c3;
  margin-top: 2px;
}

.s02-popover__evidence-meta {
  margin-top: 4px;
  font-size: 11px;
  color: #7f95ad;
}
</style>
