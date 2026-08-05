<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { getE03IssueDetail } from '@/services/api'
import type { E03IssueDetail } from '@/types/e03'

const props = defineProps<{
  issueId: number | null
  /** 右侧工作台占用时，弹窗翻到地图左侧 */
  flipLeft?: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const loading = ref(false)
const error = ref('')
const detail = ref<E03IssueDetail | null>(null)
const activeTab = ref<'history' | 'evidence'>('history')

const CASE_STATUS_ZH: Record<string, string> = {
  DISCOVERED: '已发现',
  PENDING_RECTIFICATION: '待整改',
  RECTIFYING: '整改中',
  PENDING_REVIEW: '待复查',
  PENDING_CLOSURE: '待销项',
  CLOSED: '已闭环',
  CANCELLED: '已撤销',
  MERGED: '已合并',
  SUSPENDED: '暂缓',
}

const hasHistory = computed(() => (detail.value?.history?.length || 0) > 0)
const hasEvidence = computed(() => (detail.value?.evidence?.length || 0) > 0)

const progressSteps = computed(() => {
  if (!detail.value) return []
  const status = detail.value.status
  const steps = [
    { key: 'found', label: '发现', done: true },
    { key: 'rectify', label: '整改', done: status !== '已发现' && status !== '待整改' },
    {
      key: 'review',
      label: '复查',
      done: status === '待销项' || status === '已闭环',
    },
    { key: 'closure', label: '销项', done: status === '已闭环' },
  ]
  return steps
})

function statusZh(code?: string | null) {
  if (!code) return ''
  return CASE_STATUS_ZH[code] || code
}

function historyLabel(fromStatus?: string | null, toStatus?: string | null) {
  const to = statusZh(toStatus)
  if (!fromStatus) return to
  return `${statusZh(fromStatus)} → ${to}`
}

function rectificationHint(status?: string | null): string {
  if (!status) return '按水保方案落实整改'
  if (status === '已闭环') return '整改已完成并销项'
  if (status === '待销项') return '整改完成，待销项确认'
  if (status === '待复查') return '整改完成，待复查'
  return '按水土保持方案及监理意见落实整改措施'
}

async function loadDetail(id: number) {
  loading.value = true
  error.value = ''
  try {
    const res = await getE03IssueDetail(id)
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

watch(() => props.issueId, (id) => {
  if (id != null) {
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
</script>

<template>
  <div
    v-if="props.issueId != null"
    class="e03-popover"
    :class="{ 'is-flip-left': flipLeft }"
  >
    <div class="e03-popover__inner">
      <header class="e03-popover__head">
        <h3>{{ detail?.title || '加载中…' }}</h3>
        <button type="button" class="e03-popover__close" @click="emit('close')">×</button>
      </header>

      <div v-if="loading" class="e03-popover__state">正在加载…</div>
      <div v-else-if="error" class="e03-popover__state is-error">
        {{ error }}
        <button v-if="props.issueId" class="e03-popover__retry" @click="loadDetail(props.issueId)">重试</button>
      </div>
      <template v-else-if="detail">
          <!-- 问题概况（水保差异，不得只换标题抄 E02） -->
          <div class="e03-popover__overview">
            <div class="e03-popover__overview-title">问题概况</div>
            <div class="e03-popover__overview-grid">
              <div class="e03-popover__overview-item">
                <span class="e03-popover__overview-label">水保问题类型</span>
                <span class="e03-popover__overview-value">{{ detail.issueType || '—' }}</span>
              </div>
              <div class="e03-popover__overview-item">
                <span class="e03-popover__overview-label">关联对象</span>
                <span class="e03-popover__overview-value">{{ detail.title || '—' }}</span>
              </div>
              <div class="e03-popover__overview-item">
                <span class="e03-popover__overview-label">位置</span>
                <span class="e03-popover__overview-value">{{ detail.locationText || '—' }}</span>
              </div>
              <div class="e03-popover__overview-item">
                <span class="e03-popover__overview-label">发现依据</span>
                <span class="e03-popover__overview-value">{{ detail.discoveryBasis || '—' }}</span>
              </div>
              <div class="e03-popover__overview-item is-wide">
                <span class="e03-popover__overview-label">问题描述</span>
                <span class="e03-popover__overview-value">{{ detail.description || '—' }}</span>
              </div>
              <div class="e03-popover__overview-item is-wide">
                <span class="e03-popover__overview-label">整改要求</span>
                <span class="e03-popover__overview-value">{{ rectificationHint(detail.status) }}</span>
              </div>
            </div>
          </div>

          <div class="e03-popover__progress">
            <div
              v-for="(step, idx) in progressSteps"
              :key="step.key"
              class="e03-popover__step"
              :class="{ done: step.done }"
            >
              <span class="e03-popover__dot" />
              <span class="e03-popover__label">{{ step.label }}</span>
              <span v-if="idx < progressSteps.length - 1" class="e03-popover__line" />
            </div>
          </div>

          <div class="e03-popover__current">
            <strong>当前状态：</strong>
            <span>{{ detail.status }}</span>
            <span v-if="detail.overdue" class="e03-popover__overdue">已逾期</span>
          </div>

          <div v-if="detail.parties?.length" class="e03-popover__parties">
            <div
              v-for="p in detail.parties"
              :key="`${p.role}-${p.userName}`"
              class="e03-popover__party"
            >
              <span class="e03-popover__party-role">{{ p.roleLabel }}</span>
              <span class="e03-popover__party-name">{{ p.orgName }} {{ p.userName }}</span>
            </div>
          </div>

          <div class="e03-popover__deadline">
            <span>整改期限：{{ dateOnly(detail.deadline) }}</span>
            <span v-if="detail.foundDate">发现时间：{{ dateOnly(detail.foundDate) }}</span>
          </div>

          <div class="e03-popover__tabs">
            <button
              type="button"
              :class="{ active: activeTab === 'history' }"
              @click="activeTab = 'history'"
            >
              闭环进展
            </button>
            <button
              type="button"
              :class="{ active: activeTab === 'evidence' }"
              @click="activeTab = 'evidence'"
            >
              证据材料
            </button>
          </div>

          <div class="e03-popover__tab-body">
            <div v-if="activeTab === 'history'" class="e03-popover__history">
              <p v-if="!hasHistory" class="e03-popover__empty">暂无状态轨迹</p>
              <div
                v-for="(h, idx) in detail.history"
                :key="idx"
                class="e03-popover__history-item"
              >
                <div class="e03-popover__history-meta">
                  <span class="e03-popover__history-status">
                    {{ historyLabel(h.fromStatus, h.toStatus) }}
                  </span>
                  <span class="e03-popover__history-time">{{ dateTime(h.actionAt) }}</span>
                </div>
                <div v-if="h.operatorName" class="e03-popover__history-operator">
                  {{ h.operatorName }} {{ h.operatorOrgName ? `（${h.operatorOrgName}）` : '' }}
                </div>
                <div v-if="h.comment" class="e03-popover__history-comment">{{ h.comment }}</div>
                <div v-if="h.transitionResult === 'RETURNED'" class="e03-popover__history-returned">
                  退回原因：{{ h.comment || '无详细说明' }}
                </div>
              </div>
            </div>

            <div v-else class="e03-popover__evidence">
              <p v-if="!hasEvidence" class="e03-popover__empty">暂无证据材料</p>
              <div
                v-for="e in detail.evidence"
                :key="`${e.role}-${e.title}`"
                class="e03-popover__evidence-item"
              >
                <div class="e03-popover__evidence-role">{{ e.roleLabel }}</div>
                <div class="e03-popover__evidence-title">{{ e.title }}</div>
                <div v-if="e.description" class="e03-popover__evidence-desc">{{ e.description }}</div>
                <a
                  v-if="e.documentId || e.hasAttachment"
                  class="e03-popover__evidence-action is-link"
                  :href="`/api/workspace/documents/${e.documentId}`"
                  target="_blank"
                  rel="noopener noreferrer"
                >下载</a>
                <div v-else class="e03-popover__evidence-action is-muted">暂无材料</div>
              </div>

              <div v-if="detail.materialCompleteness" class="e03-popover__completeness">
                <div class="e03-popover__completeness-title">
                  材料完整度：{{ detail.materialCompleteness.ratio }}
                </div>
                <div
                  v-for="note in detail.materialCompleteness.notes"
                  :key="note"
                  class="e03-popover__completeness-note"
                >
                  {{ note }}
                </div>
              </div>
            </div>
          </div>

          <!-- GIS 关联位置说明（测试数据场景） -->
          <div v-if="detail.gisDisclaimer" class="e03-popover__gis-disclaimer">
            {{ detail.gisDisclaimer }}
          </div>
        </template>
      </div>
    </div>
</template>

<style scoped lang="scss">
.e03-popover {
  position: absolute;
  z-index: 28;
  top: 52px;
  left: 16px;
  width: min(380px, calc(100% - 32px));
  max-height: calc(100% - 72px);
  background: rgba(4, 25, 48, 0.98);
  border: 1px solid rgba(105, 227, 111, 0.35);
  border-radius: 8px;
  color: #d7e6f5;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45);
}

.e03-popover.is-flip-left {
  left: 16px;
  right: auto;
}

@media (max-width: 1400px) {
  .e03-popover {
    width: min(340px, calc(100% - 24px));
  }
}

.e03-popover__inner {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  padding: 14px;
}

.e03-popover__head {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;

  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 700;
    color: #f3f8ff;
  }
}

.e03-popover__close {
  width: 26px;
  height: 26px;
  font-size: 16px;
  line-height: 1;
  border: 1px solid rgba(105, 227, 111, 0.35);
  background: rgba(8, 40, 69, 0.72);
  color: #f3f8ff;
  border-radius: 5px;
  cursor: pointer;
}

.e03-popover__state {
  padding: 20px 0;
  text-align: center;
  color: #8ba6c3;
  font-size: 13px;
  &.is-error { color: #ff9f2f; }
}

.e03-popover__retry {
  display: block;
  margin: 8px auto 0;
  padding: 3px 12px;
  font-size: 12px;
  border: 1px solid rgba(105, 227, 111, 0.35);
  background: rgba(8, 40, 69, 0.72);
  color: #69e36f;
  border-radius: 4px;
  cursor: pointer;
}

/* 问题概况（水保差异） */
.e03-popover__overview {
  flex-shrink: 0;
  margin-bottom: 12px;
  padding: 10px;
  border-radius: 6px;
  background: rgba(8, 40, 69, 0.5);
  border: 1px solid rgba(105, 227, 111, 0.18);
}

.e03-popover__overview-title {
  font-size: 13px;
  font-weight: 600;
  color: #69e36f;
  margin-bottom: 8px;
}

.e03-popover__overview-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 10px;
}

.e03-popover__overview-item {
  display: flex;
  flex-direction: column;
  gap: 2px;

  &.is-wide {
    grid-column: 1 / -1;
  }
}

.e03-popover__overview-label {
  font-size: 11px;
  color: #8ba6c3;
}

.e03-popover__overview-value {
  font-size: 12px;
  color: #d7e6f5;
  line-height: 1.4;
}

.e03-popover__progress {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 12px;
  padding: 8px 0;
}

.e03-popover__step {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;

  &.done {
    .e03-popover__dot { background: #69e36f; box-shadow: 0 0 0 3px rgba(105, 227, 111, 0.2); }
    .e03-popover__label { color: #69e36f; }
  }
}

.e03-popover__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(139, 166, 195, 0.4);
  flex-shrink: 0;
}

.e03-popover__label {
  font-size: 11px;
  color: #8ba6c3;
  white-space: nowrap;
}

.e03-popover__line {
  flex: 1;
  height: 1px;
  background: rgba(139, 166, 195, 0.3);
  min-width: 8px;
}

.e03-popover__current {
  flex-shrink: 0;
  font-size: 13px;
  margin-bottom: 10px;
  .e03-popover__overdue {
    margin-left: 8px;
    color: #ff6b6b;
    font-size: 12px;
  }
}

.e03-popover__parties {
  flex-shrink: 0;
  margin-bottom: 10px;
}

.e03-popover__party {
  display: flex;
  gap: 8px;
  font-size: 12px;
  margin-bottom: 4px;
}

.e03-popover__party-role {
  color: #8ba6c3;
  min-width: 56px;
}

.e03-popover__party-name {
  color: #d7e6f5;
}

.e03-popover__deadline {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: #8ba6c3;
  margin-bottom: 10px;
}

.e03-popover__tabs {
  flex-shrink: 0;
  display: flex;
  gap: 0;
  border-bottom: 1px solid rgba(105, 227, 111, 0.2);
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
      color: #69e36f;
      border-bottom-color: #69e36f;
    }
  }
}

.e03-popover__tab-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.e03-popover__empty {
  text-align: center;
  color: #8ba6c3;
  font-size: 12px;
  padding: 16px 0;
}

.e03-popover__history-item {
  padding: 8px 0;
  border-bottom: 1px solid rgba(139, 166, 195, 0.12);
}

.e03-popover__history-meta {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
}

.e03-popover__history-status {
  color: #69e36f;
  font-weight: 600;
}

.e03-popover__history-time {
  color: #8ba6c3;
  flex-shrink: 0;
}

.e03-popover__history-operator {
  font-size: 11px;
  color: #8ba6c3;
  margin-top: 2px;
}

.e03-popover__history-comment {
  font-size: 12px;
  color: #d7e6f5;
  margin-top: 4px;
}

.e03-popover__history-returned {
  margin-top: 4px;
  font-size: 12px;
  color: #ff9f2f;
}

.e03-popover__evidence-item {
  padding: 8px 0;
  border-bottom: 1px solid rgba(139, 166, 195, 0.12);
}

.e03-popover__evidence-role {
  font-size: 11px;
  color: #69e36f;
}

.e03-popover__evidence-title {
  font-size: 13px;
  color: #f3f8ff;
  margin-top: 2px;
}

.e03-popover__evidence-desc {
  font-size: 12px;
  color: #8ba6c3;
  margin-top: 2px;
}

.e03-popover__evidence-action {
  margin-top: 4px;
  font-size: 11px;
  color: #8ba6c3;

  &.is-link {
    display: inline-block;
    color: #69e36f;
    text-decoration: underline;
    cursor: pointer;
  }

  &.is-muted {
    pointer-events: none;
    color: #6a8099;
  }
}

.e03-popover__completeness {
  margin-top: 10px;
  padding: 8px;
  border-radius: 6px;
  background: rgba(105, 227, 111, 0.08);
  border: 1px solid rgba(105, 227, 111, 0.2);
}

.e03-popover__completeness-title {
  font-size: 12px;
  color: #69e36f;
  font-weight: 600;
}

.e03-popover__completeness-note {
  font-size: 11px;
  color: #ff9f2f;
  margin-top: 4px;
}

.e03-popover__gis-disclaimer {
  flex-shrink: 0;
  margin-top: 8px;
  padding: 6px 8px;
  font-size: 11px;
  color: #8ba6c3;
  border-radius: 4px;
  background: rgba(255, 159, 47, 0.06);
  border: 1px solid rgba(255, 159, 47, 0.2);
}
</style>
