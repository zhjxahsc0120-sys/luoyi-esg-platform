<script setup lang="ts">
import PanelCard from '@/components/layout/PanelCard.vue'
import BarMetricChart from '@/components/charts/BarMetricChart.vue'
import { useDashboardStore } from '@/stores/dashboard.store'
import {
  ShieldCheck,
  AlertTriangle,
  AlertCircle,
  Info,
  ListChecks,
} from 'lucide-vue-next'
import type { ComplianceMetric, WarningListItem } from '@/types/dashboard'

const store = useDashboardStore()

const emit = defineEmits<{
  selectWarning: [payload: { kpiKey: string; objectId: number | null }]
}>()

const TONE_MEANING: Record<string, string> = {
  red: '立即督办',
  yellow: '重点关注',
  blue: '持续跟踪',
  neutral: '事项汇总',
}

const TONE_ICON = {
  red: AlertTriangle,
  yellow: AlertCircle,
  blue: Info,
  neutral: ListChecks,
} as const

function toneOf(item: ComplianceMetric) {
  return item.tone || 'neutral'
}

function meaningOf(item: ComplianceMetric) {
  return TONE_MEANING[toneOf(item)] || ''
}

function iconOf(item: ComplianceMetric) {
  return TONE_ICON[toneOf(item)] || ListChecks
}

function splitSafeguard(item: string) {
  const separatorIndex = item.indexOf('，')

  if (separatorIndex === -1) {
    return { title: item, detail: '' }
  }

  return {
    title: item.slice(0, separatorIndex),
    detail: item.slice(separatorIndex + 1),
  }
}

function levelClass(level: string) {
  if (level === '红') return 'lvl-red'
  if (level === '黄') return 'lvl-yellow'
  return 'lvl-blue'
}

function canNavigate(row: WarningListItem) {
  return Boolean(row.kpiKey)
}

function handleRowClick(row: WarningListItem) {
  // Contract rule: navigate with kpiKey + objectId only — never guess from objectName
  if (!row.kpiKey) return
  emit('selectWarning', {
    kpiKey: row.kpiKey,
    objectId: row.objectId ?? null,
  })
}
</script>

<template>
  <PanelCard title="综合风险态势与预警" :icon="ShieldCheck">
    <div class="compliance-grid">
      <div
        v-for="item in store.compliance"
        :key="item.label"
        class="metric-card"
        :class="`tone-${toneOf(item)}`"
      >
        <div class="metric-head">
          <component :is="iconOf(item)" :size="13" class="metric-icon" />
          <div class="metric-label">{{ item.label }}</div>
        </div>
        <div class="metric-value">{{ item.value }}<span class="metric-unit">{{ item.unit }}</span></div>
        <div v-if="meaningOf(item)" class="metric-meaning">{{ meaningOf(item) }}</div>
      </div>
      <div class="compliance-subpanel effectiveness-card">
        <div class="compliance-subtitle">
          预警构成
        </div>
        <BarMetricChart :data="store.effectiveness" />
      </div>
      <div class="compliance-subpanel safeguard-card">
        <div class="compliance-subtitle">重点风险事项</div>
        <div class="safeguard-list">
          <div v-for="(item, index) in store.safeguards" :key="index" class="safeguard-item">
            <span class="safeguard-dot" />
            <span class="safeguard-content">
              <span class="safeguard-title">{{ splitSafeguard(item).title }}</span>
              <span v-if="splitSafeguard(item).detail" class="safeguard-detail">
                {{ splitSafeguard(item).detail }}
              </span>
            </span>
          </div>
        </div>
        <div class="warning-list-block">
          <div class="warning-list-title">红黄蓝预警清单</div>
          <div class="warning-table-wrap">
            <table class="warning-table">
              <thead>
                <tr>
                  <th>等级</th>
                  <th>事项</th>
                  <th>来源</th>
                  <th>状态</th>
                  <th>时间</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(row, idx) in store.warningItems"
                  :key="`${row.kpiKey || 'x'}-${row.objectId ?? idx}`"
                  :class="{ clickable: canNavigate(row) }"
                  @click="handleRowClick(row)"
                >
                  <td><span class="lvl-badge" :class="levelClass(row.level)">{{ row.level }}</span></td>
                  <td class="col-title" :title="row.title">{{ row.title }}</td>
                  <td>{{ row.kpiKey || row.source }}</td>
                  <td>{{ row.status }}</td>
                  <td>{{ row.updatedAt }}</td>
                </tr>
                <tr v-if="!store.warningItems.length">
                  <td colspan="5" class="empty-row">暂无预警事项</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </PanelCard>
</template>

<style scoped lang="scss">
.compliance-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  grid-template-rows: auto minmax(0, 1fr);
  gap: 8px;
  min-width: 0;
  min-height: 0;
}

.compliance-grid > .metric-card {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: 8px 6px;
  border-radius: 6px;
  border: 1px solid var(--border-faint);
  background: var(--bg-card);
  text-align: center;
}

.metric-head {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 100%;
}

.metric-icon {
  flex-shrink: 0;
}

.metric-label {
  color: var(--text-muted);
  font-size: 11px;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.metric-value {
  font-family: var(--font-num);
  font-size: 22px;
  font-weight: 700;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}

.metric-unit {
  margin-left: 2px;
  font-size: 11px;
  font-weight: 500;
  opacity: 0.85;
}

.metric-meaning {
  color: var(--text-tertiary, #7f99b8);
  font-size: 10px;
  line-height: 1.2;
}

.tone-red {
  border-color: rgba(239, 68, 68, 0.55);
  background: rgba(239, 68, 68, 0.1);

  .metric-icon,
  .metric-value {
    color: #ef4444;
  }
}

.tone-yellow {
  border-color: rgba(234, 179, 8, 0.55);
  background: rgba(234, 179, 8, 0.1);

  .metric-icon,
  .metric-value {
    color: #eab308;
  }
}

.tone-blue {
  border-color: rgba(59, 130, 246, 0.55);
  background: rgba(59, 130, 246, 0.1);

  .metric-icon,
  .metric-value {
    color: #3b82f6;
  }
}

.tone-neutral {
  border-color: rgba(148, 163, 184, 0.4);
  background: rgba(148, 163, 184, 0.08);

  .metric-icon,
  .metric-value {
    color: #cbd5e1;
  }
}

.compliance-subpanel {
  min-width: 0;
  min-height: 0;
  height: 100%;
  padding: 8px 10px;
  background: var(--bg-card);
  border: 1px solid var(--border-blue-dim);
  border-radius: 6px;
  overflow: hidden;
}

.effectiveness-card,
.safeguard-card {
  display: flex;
  flex-direction: column;
}

.effectiveness-card {
  grid-column: 1 / span 2;
  min-height: 132px;
}

.safeguard-card {
  grid-column: 3 / span 2;
}

.compliance-subtitle {
  height: 22px;
  margin: 0 0 6px;
  color: #fff;
  font-size: 15px;
  font-weight: 650;
  line-height: 22px;
  flex-shrink: 0;
}

.effectiveness-card :deep(.chart-container) {
  flex: 1;
  width: 100%;
  min-width: 0;
  min-height: 96px;
}

.safeguard-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
  flex-shrink: 0;
  max-height: 52px;
  overflow: hidden;
  margin-bottom: 6px;
}

.safeguard-item {
  display: grid;
  grid-template-columns: 5px minmax(0, 1fr);
  align-items: start;
  column-gap: 6px;
  min-width: 0;
}

.safeguard-dot {
  width: 4px;
  height: 4px;
  margin-top: 5px;
  border-radius: 50%;
  background: var(--cyan);
}

.safeguard-content {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.safeguard-title,
.safeguard-detail {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.safeguard-title {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 500;
  line-height: 17px;
}

.safeguard-detail {
  color: var(--text-tertiary);
  font-size: 11px;
  font-weight: 400;
  line-height: 15px;
}

.warning-list-block {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  border-top: 1px solid rgba(80, 120, 160, 0.25);
  padding-top: 4px;
}

.warning-list-title {
  color: #d7e7f5;
  font-size: 12px;
  font-weight: 600;
  line-height: 18px;
  margin-bottom: 3px;
  flex-shrink: 0;
}

.warning-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.warning-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 11px;

  th,
  td {
    padding: 2px 4px;
    text-align: left;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    border-bottom: 1px solid rgba(80, 120, 160, 0.18);
  }

  th {
    color: #8fabc4;
    font-weight: 500;
  }

  td {
    color: var(--text-secondary);
  }

  .col-title {
    width: 42%;
  }

  .empty-row {
    text-align: center;
    color: var(--text-tertiary);
    padding: 8px 4px;
  }

  tr.clickable {
    cursor: pointer;
  }

  tr.clickable:hover td {
    background: rgba(47, 156, 255, 0.08);
  }
}

.lvl-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
}

.lvl-red {
  color: #fecaca;
  background: rgba(239, 68, 68, 0.28);
}

.lvl-yellow {
  color: #fef08a;
  background: rgba(234, 179, 8, 0.28);
}

.lvl-blue {
  color: #bfdbfe;
  background: rgba(59, 130, 246, 0.28);
}
</style>
