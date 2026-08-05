<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue';
import type { BusinessLinkItem, BusinessLinksResponse, GisBusinessLinkOpenPayload, PresentationMode } from '../types';

const props = withDefaults(
  defineProps<{
    data: BusinessLinksResponse | null;
    loading: boolean;
    featureName: string;
    presentationMode?: PresentationMode;
  }>(),
  {
    presentationMode: 'preview',
  },
);

const emit = defineEmits<{ close: []; 'open-kpi-source': [payload: GisBusinessLinkOpenPayload] }>();

const isDashboard = computed(() => props.presentationMode === 'dashboard');
const isPreview = computed(() => props.presentationMode === 'preview');

const tooltipMessage = ref('');
let tooltipTimer: ReturnType<typeof setTimeout> | undefined;

function showPlaceholderTip(item: BusinessLinkItem) {
  tooltipMessage.value =
    item.actionTip || '关联业务跳转为原型预留，尚未接入页面联动。';
  if (tooltipTimer) clearTimeout(tooltipTimer);
  tooltipTimer = setTimeout(() => {
    tooltipMessage.value = '';
  }, 2400);
}

function canOpenKpiSource(item: BusinessLinkItem) {
  return (
    permissions.value?.canView !== false &&
    (item.targetKpiCode === 'E02' || item.targetKpiCode === 'S02') &&
    !!item.sourceId
  );
}

function handleOpenSource(item: BusinessLinkItem) {
  if (!canOpenKpiSource(item)) {
    showPlaceholderTip(item);
    return;
  }
  emit('open-kpi-source', {
    targetType: item.targetKpiCode as 'E02' | 'S02',
    sourceId: item.sourceId!,
    sourceTable: item.sourceTable,
    title: item.title || item.code,
  });
}

onBeforeUnmount(() => {
  if (tooltipTimer) clearTimeout(tooltipTimer);
});

const RISK_LABELS: Record<number, string> = {
  1: '一般',
  2: '较大',
  3: '重大',
  4: '特大',
};

function riskLabel(level?: number) {
  if (!level) return '';
  return RISK_LABELS[level] || '';
}

const permissions = computed(() => props.data?.permissions);
const canViewOnly = computed(() => {
  const p = permissions.value;
  if (!p) return false;
  return p.canView && !p.canSupervise && !p.canHandle;
});

const permissionNotice = computed(() => {
  if (permissions.value?.notice) return permissions.value.notice;
  return '领导层仅查看关联业务线索，不在地图侧办理事项。';
});

const summary = computed(() => props.data?.summary);
const items = computed(() => props.data?.items || []);

function actionLabel(item: BusinessLinkItem) {
  if (canOpenKpiSource(item)) {
    if (item.targetKpiCode === 'E02') return '查看环保问题来源';
    if (item.targetKpiCode === 'S02') return '查看安全风险来源';
  }
  if (item.actionLabel) return item.actionLabel;
  if (item.typeLabel) return `查看${item.typeLabel}来源（预留）`;
  return '查看来源（预留）';
}
</script>

<template>
  <aside
    class="business-links-panel"
    :class="{ 'business-links-panel--dashboard': isDashboard }"
  >
    <button class="blp-close" aria-label="关闭关联业务" @click="$emit('close')">×</button>

    <header class="blp-header">
      <small>关联业务线索</small>
      <b>{{ featureName }}｜关联业务</b>
    </header>

    <div v-if="loading" class="blp-loading">加载关联业务中…</div>

    <template v-else-if="data">
      <!-- 顶部摘要 -->
      <div class="blp-summary">
        <div class="blp-summary-item">
          <span>关联事项</span>
          <b>{{ summary?.total ?? 0 }} 项</b>
        </div>
        <div class="blp-summary-item">
          <span>待处理</span>
          <b>{{ summary?.pendingCount ?? 0 }} 项</b>
        </div>
        <div class="blp-summary-item">
          <span>高风险</span>
          <b class="high-risk">{{ summary?.highRiskCount ?? 0 }} 项</b>
        </div>
      </div>

      <!-- 权限提示 -->
      <div v-if="canViewOnly" class="blp-notice">{{ permissionNotice }}</div>

      <!-- 业务列表 -->
      <div v-if="items.length" class="blp-list">
        <div v-for="item in items" :key="item.id" class="blp-item">
          <div class="blp-item-head">
            <span class="blp-item-type">{{ item.typeLabel || item.type }}</span>
            <span v-if="item.code" class="blp-item-code">{{ item.code }}</span>
            <span v-if="item.riskLevel" class="blp-item-risk">
              风险：{{ riskLabel(item.riskLevel) }}
            </span>
          </div>
          <div class="blp-item-title">{{ item.title }}</div>
          <div v-if="item.status" class="blp-item-status">状态：{{ item.status }}</div>
          <div v-if="item.summary" class="blp-item-summary">{{ item.summary }}</div>

          <!-- preview 模式展示更完整字段 -->
          <template v-if="isPreview">
            <div v-if="item.sourceTable" class="blp-item-meta">
              <span>来源表</span><code>{{ item.sourceTable }}</code>
            </div>
            <div v-if="item.sourceId" class="blp-item-meta">
              <span>来源ID</span><code>{{ item.sourceId }}</code>
            </div>
            <div v-if="item.updatedAt" class="blp-item-meta">
              <span>更新时间</span><code>{{ item.updatedAt }}</code>
            </div>
          </template>
          <div v-else-if="item.updatedAt" class="blp-item-time">{{ item.updatedAt }}</div>

          <button
            class="blp-item-action"
            :class="{ 'blp-item-action--active': canOpenKpiSource(item) }"
            @click="handleOpenSource(item)"
          >
            {{ actionLabel(item) }}
          </button>
        </div>
      </div>
      <div v-else class="blp-empty">暂无关联业务</div>
    </template>

    <!-- 预留提示 toast -->
    <Transition name="blp-toast">
      <div v-if="tooltipMessage" class="blp-toast">{{ tooltipMessage }}</div>
    </Transition>
  </aside>
</template>

<style scoped>
.business-links-panel {
  width: 340px;
  max-height: calc(100% - 120px);
  overflow-y: auto;
  padding: 14px;
  background: linear-gradient(145deg, rgba(4, 28, 48, 0.97), rgba(3, 15, 29, 0.96));
  border: 1px solid rgba(28, 194, 230, 0.55);
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.42);
  color: #d9f1ff;
}

.blp-close {
  position: absolute;
  right: 8px;
  top: 7px;
  width: 25px;
  height: 25px;
  padding: 0 !important;
  border: 0 !important;
  background: transparent !important;
  color: #7ba8ba !important;
  font-size: 20px;
  line-height: 24px;
  cursor: pointer;
}
.blp-close:hover { color: #fff !important; }

.blp-header {
  padding: 0 32px 10px 0;
  border-bottom: 1px solid rgba(45, 172, 207, 0.24);
}
.blp-header small,
.blp-header b { display: block; }
.blp-header small { margin-bottom: 4px; color: #5ba4bd; font-size: 9px; }
.blp-header b { font-size: 15px; }

.blp-loading,
.blp-empty {
  padding: 16px 4px;
  font-size: 11px;
  color: #6f94a6;
}

.blp-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  margin-top: 10px;
}
.blp-summary-item {
  padding: 7px 4px;
  text-align: center;
  background: rgba(10, 58, 82, 0.48);
  border: 1px solid rgba(45, 151, 191, 0.2);
}
.blp-summary-item span,
.blp-summary-item b { display: block; }
.blp-summary-item span { color: #6f94a6; font-size: 9px; }
.blp-summary-item b { margin-top: 4px; font-size: 13px; color: #d9f1ff; }
.blp-summary-item b.high-risk { color: #ff8888; }

.blp-notice {
  margin: 8px 0 0;
  padding: 6px 8px;
  color: #8aabbf;
  font-size: 10px;
  line-height: 1.5;
  background: rgba(10, 38, 58, 0.4);
  border-left: 2px solid rgba(255, 200, 80, 0.4);
}

.blp-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 10px;
}
.blp-item {
  padding: 8px;
  background: rgba(10, 38, 58, 0.35);
  border: 1px solid rgba(45, 151, 191, 0.15);
  border-radius: 3px;
}
.blp-item-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 9px;
}
.blp-item-type {
  padding: 1px 5px;
  color: #2bd9f4;
  background: rgba(20, 60, 88, 0.6);
  border-radius: 2px;
}
.blp-item-code { color: #8aabbf; }
.blp-item-risk { color: #ff8888; }

.blp-item-title {
  margin-top: 4px;
  font-size: 12px;
  color: #d9f1ff;
}
.blp-item-status {
  margin-top: 2px;
  font-size: 9px;
  color: #7fa2b3;
}
.blp-item-summary {
  margin-top: 3px;
  font-size: 9px;
  line-height: 1.4;
  color: #8aabbf;
}
.blp-item-meta {
  display: flex;
  gap: 4px;
  margin-top: 2px;
  font-size: 9px;
  color: #6f94a6;
}
.blp-item-meta code {
  color: #a8d4e8;
  font-family: 'Consolas', monospace;
}
.blp-item-time {
  margin-top: 2px;
  font-size: 8px;
  color: #52788b;
}

.blp-item-action {
  width: 100%;
  margin-top: 6px;
  padding: 5px;
  font-size: 10px;
  color: #7fa2b3;
  background: transparent;
  border: 1px solid rgba(45, 151, 191, 0.2);
  cursor: pointer;
}
.blp-item-action:hover {
  color: #d9f1ff;
  border-color: rgba(34, 194, 230, 0.4);
}
.blp-item-action--active {
  color: #b8ecff;
  border-color: rgba(47, 156, 255, 0.6);
  background: rgba(47, 156, 255, 0.08);
}
.blp-item-action--active:hover {
  color: #ffffff;
  border-color: rgba(47, 156, 255, 0.9);
  background: rgba(47, 156, 255, 0.15);
}

.blp-toast {
  position: absolute;
  left: 50%;
  bottom: 14px;
  transform: translateX(-50%);
  padding: 8px 14px;
  font-size: 11px;
  color: #ffe7a8;
  background: rgba(30, 30, 10, 0.92);
  border: 1px solid rgba(255, 200, 80, 0.4);
  border-radius: 3px;
  pointer-events: none;
  white-space: nowrap;
  z-index: 5;
}
.blp-toast-enter-active,
.blp-toast-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.blp-toast-enter-from,
.blp-toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(6px);
}

/* Dashboard 模式：更紧凑 */
.business-links-panel--dashboard {
  width: 320px;
  padding: 12px;
}
.business-links-panel--dashboard .blp-header b { font-size: 13px; }
.business-links-panel--dashboard .blp-header small { font-size: 8px; }
.business-links-panel--dashboard .blp-summary-item b { font-size: 12px; }
.business-links-panel--dashboard .blp-item-title { font-size: 11px; }
</style>
