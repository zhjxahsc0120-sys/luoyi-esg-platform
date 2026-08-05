<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getDashboardTopic } from '@/services/api'
import type { KpiDetailConfig } from '@/types/dashboard'

const loading = ref(true)
const detail = ref<KpiDetailConfig | null>(null)

const hasError = computed(() => !detail.value || detail.value.loadError === true)
const hasSummary = computed(() => !!detail.value && detail.value.summary.length > 0)
const hasColumns = computed(() => !!detail.value && detail.value.detailColumns.length > 0)
const hasRows = computed(() => !!detail.value && detail.value.detailData.length > 0)

async function loadDetail() {
  loading.value = true
  detail.value = null
  try {
    detail.value = await getDashboardTopic('carbon')
  } catch {
    detail.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDetail()
})
</script>

<template>
  <div class="carbon-detail ws-page">
    <!-- 加载态 -->
    <div v-if="loading" class="state-block state-loading">
      <span class="state-spinner" aria-hidden="true" />
      <span class="state-text">数据加载中…</span>
    </div>

    <!-- 错误 / 空态 -->
    <div v-else-if="hasError" class="state-block state-error">
      <span class="state-text">数据加载失败，暂无碳核算明细数据</span>
      <button class="ws-btn ws-btn-secondary ws-btn-sm" @click="loadDetail">重新加载</button>
    </div>

    <!-- 内容态 -->
    <template v-else>
      <!-- 顶部汇总卡 -->
      <div v-if="hasSummary" class="ws-status-cards cols-4">
        <div
          v-for="(item, idx) in detail!.summary"
          :key="idx"
          class="ws-status-card carbon-summary-card"
          :style="{ '--accent-color': '#69e36f' }"
        >
          <div class="ws-card-label">{{ item.label }}</div>
          <div class="ws-card-value-row">
            <span class="ws-card-value">{{ item.value }}</span>
            <span v-if="item.unit" class="ws-card-unit">{{ item.unit }}</span>
          </div>
        </div>
      </div>

      <!-- 明细表格 -->
      <div class="detail-panel ws-panel">
        <div class="ws-panel-header">
          <div class="ws-panel-title">{{ detail!.detailTitle || '明细数据' }}</div>
        </div>
        <div class="ws-table-container">
          <div class="ws-table-scroll" :class="{ 'no-scroll': hasRows && detail!.detailData.length <= 10 }">
            <table class="ws-table">
              <colgroup>
                <col
                  v-for="col in detail!.detailColumns"
                  :key="col.key"
                  :style="{ width: col.width || 'auto' }"
                />
              </colgroup>
              <thead>
                <tr>
                  <th v-for="col in detail!.detailColumns" :key="col.key">{{ col.label }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, ri) in detail!.detailData" :key="ri">
                  <td v-for="col in detail!.detailColumns" :key="col.key">{{ row[col.key] }}</td>
                </tr>
                <tr v-if="!hasRows">
                  <td :colspan="hasColumns ? detail!.detailColumns.length : 1" class="table-empty">
                    暂无明细数据
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 数据来源信息 -->
      <div class="source-info">
        <div class="source-item">
          <span class="source-label">数据来源</span>
          <span class="source-value">{{ detail!.dataSource || '—' }}</span>
        </div>
        <div class="source-item">
          <span class="source-label">更新时间</span>
          <span class="source-value">{{ detail!.updateTime || '—' }}</span>
        </div>
        <div class="source-item">
          <span class="source-label">更新频率</span>
          <span class="source-value">{{ detail!.updateFrequency || '—' }}</span>
        </div>
        <div class="source-item">
          <span class="source-label">数据完整性</span>
          <span class="source-value">{{ detail!.completeness || '—' }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.carbon-detail {
  min-height: 0;
}

/* ── 状态块（加载 / 错误） ── */
.state-block {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(47, 156, 255, 0.14);
  border-radius: 8px;
  min-height: 0;
}

.state-loading .state-text {
  color: #8fa9c8;
  font-size: 13px;
}

.state-error .state-text {
  color: #ff4f5e;
  font-size: 13px;
}

.state-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid rgba(105, 227, 111, 0.2);
  border-top-color: #69e36f;
  border-radius: 50%;
  animation: carbon-detail-spin 0.8s linear infinite;
}

@keyframes carbon-detail-spin {
  to {
    transform: rotate(360deg);
  }
}

/* ── 汇总卡（绿色主题） ── */
.carbon-summary-card {
  cursor: default;
}

.carbon-summary-card:hover {
  border-color: rgba(105, 227, 111, 0.45);
}

/* ── 明表面板 ── */
.detail-panel {
  flex: 1;
  min-height: 0;
}

/* 明细表为只读展示，取消行指针与悬停高亮 */
.detail-panel :deep(.ws-table tbody tr) {
  cursor: default;
}

.detail-panel :deep(.ws-table tbody tr:hover) {
  background: rgba(105, 227, 111, 0.05);
}

.table-empty {
  text-align: center !important;
  color: #5a7a9a !important;
  font-size: 13px;
  padding: 24px 12px !important;
  white-space: normal !important;
}

/* ── 数据来源信息 ── */
.source-info {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 24px;
  padding: 10px 14px;
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(47, 156, 255, 0.14);
  border-radius: 8px;
}

.source-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.source-label {
  font-size: 12px;
  color: #8fa9c8;
  white-space: nowrap;
}

.source-label::before {
  content: '';
  display: inline-block;
  width: 3px;
  height: 12px;
  margin-right: 6px;
  background: #69e36f;
  border-radius: 2px;
  vertical-align: middle;
}

.source-value {
  font-size: 12px;
  color: #e8f3ff;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
