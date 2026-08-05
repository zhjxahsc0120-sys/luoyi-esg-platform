<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboard.store'
import { getDashboardPanels } from '@/services/api'
import type { CarbonSource } from '@/types/dashboard'

const store = useDashboardStore()

// ── 核算边界表（静态：方法学口径定义，非 API 数据） ──
interface BoundaryRow {
  source: string
  included: boolean
  note: string
}

const boundaryRows: BoundaryRow[] = [
  { source: '施工用油', included: true, note: '柴油消耗，主要来源' },
  { source: '施工用电', included: true, note: '外购电力，隧道掘进为主要消耗' },
  { source: '主要材料', included: true, note: '钢材、水泥等主要建材隐含碳' },
  { source: '施工运输', included: false, note: '待后续完善运输台账后纳入' },
]

// ── 核算口径说明（7.14 口径） ──
interface MethodologyNote {
  label: string
  value: string
}

const methodologyNotes: MethodologyNote[] = [
  { label: '核算口径', value: '施工用油 + 施工用电 + 主要材料' },
  { label: '运输排放', value: '暂不纳入核算边界' },
  { label: '统计起点', value: '2026-05-08（开工令日期）' },
  { label: '核算批次', value: '甲方7.14确认口径' },
]

// ── 来源构成颜色回退（与首页 CarbonBenefitPanel 保持一致） ──
const sourceColors: Record<string, string> = {
  施工用油: '#2f9cff',
  施工用电: '#69e36f',
  主要材料: '#a66cff',
  其他: '#ffb347',
}

function resolveColor(name: string, color?: string): string {
  return color || sourceColors[name] || '#8fa9c8'
}

// ── 来源构成：合计与占比动态计算 ──
const totalEmission = computed<number>(() =>
  store.carbonSrc.reduce((sum, item) => sum + Number(item.value || 0), 0),
)

interface SourceRow {
  name: string
  value: number
  percent: number
  color: string
}

const sourceRows = computed<SourceRow[]>(() =>
  store.carbonSrc.map((item: CarbonSource) => {
    const value = Number(item.value || 0)
    const percent = totalEmission.value > 0 ? (value / totalEmission.value) * 100 : 0
    return {
      name: item.name,
      value,
      percent: Number(percent.toFixed(1)),
      color: resolveColor(item.name, item.color),
    }
  }),
)

const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    await getDashboardPanels()
  } finally {
    loading.value = false
  }
})

function formatNumber(value: number): string {
  return value.toLocaleString('en-US')
}
</script>

<template>
  <div :class="['ws-page', 'carbon-boundary-page', { 'is-loading': loading }]">
    <!-- 核算边界表 -->
    <section class="ws-panel boundary-panel">
      <header class="ws-panel-header">
        <h3 class="ws-panel-title">核算边界</h3>
        <span class="ws-panel-count">甲方7.14确认口径</span>
      </header>
      <div class="ws-table-container boundary-table-container">
        <div class="ws-table-scroll no-scroll">
          <table class="ws-table boundary-table">
            <thead>
              <tr>
                <th style="width: 26%">排放源</th>
                <th style="width: 18%">是否纳入</th>
                <th style="width: 56%">说明</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in boundaryRows" :key="row.source">
                <td class="col-source">{{ row.source }}</td>
                <td class="col-included">
                  <span :class="['ws-tag', row.included ? 'ws-tag-green' : 'ws-tag-yellow']">
                    {{ row.included ? '纳入' : '暂不纳入' }}
                  </span>
                </td>
                <td class="col-note">{{ row.note }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- 来源构成 -->
    <section class="ws-panel source-panel">
      <header class="ws-panel-header">
        <h3 class="ws-panel-title">来源构成</h3>
        <span class="ws-panel-count">合计 {{ formatNumber(totalEmission) }} tCO₂e</span>
      </header>
      <div class="ws-table-container source-table-container">
        <div class="ws-table-scroll no-scroll">
          <table class="ws-table source-table">
            <thead>
              <tr>
                <th style="width: 26%">排放源</th>
                <th style="width: 24%">排放量 (tCO₂e)</th>
                <th style="width: 50%">占比</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in sourceRows" :key="row.name">
                <td class="col-source">
                  <span class="source-swatch" :style="{ background: row.color }" />
                  <span class="source-name">{{ row.name }}</span>
                </td>
                <td class="col-value">{{ formatNumber(row.value) }}</td>
                <td class="col-percent">
                  <div class="percent-bar">
                    <span
                      class="percent-fill"
                      :style="{ width: row.percent + '%', background: row.color }"
                    />
                  </div>
                  <span class="percent-text">{{ row.percent.toFixed(1) }}%</span>
                </td>
              </tr>
              <tr v-if="sourceRows.length === 0">
                <td colspan="3" class="empty-cell">暂无来源数据</td>
              </tr>
            </tbody>
            <tfoot v-if="sourceRows.length > 0">
              <tr>
                <td class="col-source">合计</td>
                <td class="col-value">{{ formatNumber(totalEmission) }}</td>
                <td class="col-percent">
                  <span class="percent-text">100.0%</span>
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </section>

    <!-- 核算口径说明 -->
    <section class="ws-panel methodology-panel">
      <header class="ws-panel-header">
        <h3 class="ws-panel-title">核算口径说明</h3>
        <span class="ws-panel-count">7.14 口径</span>
      </header>
      <ul class="methodology-list">
        <li
          v-for="note in methodologyNotes"
          :key="note.label"
          class="methodology-item"
        >
          <span class="methodology-label">{{ note.label }}</span>
          <span class="methodology-value">{{ note.value }}</span>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.carbon-boundary-page {
  overflow-y: auto;
  overflow-x: hidden;
}

.boundary-panel,
.source-panel,
.methodology-panel {
  flex-shrink: 0;
}

.boundary-table-container,
.source-table-container {
  flex: 0 1 auto;
}

/* ── 边界表 ── */
.boundary-table tbody tr,
.source-table tbody tr {
  cursor: default;
}

.boundary-table td.col-source,
.source-table td.col-source {
  font-weight: 600;
  color: var(--ws-text-primary);
}

.boundary-table td.col-note {
  color: var(--ws-text-secondary);
  white-space: normal;
  line-height: 1.5;
}

/* ── 来源构成表 ── */
.source-swatch {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 2px;
  margin-right: 8px;
  vertical-align: middle;
  flex-shrink: 0;
}

.source-name {
  vertical-align: middle;
}

.source-table td.col-value {
  font-variant-numeric: tabular-nums;
  color: var(--ws-text-primary);
}

.col-percent {
  display: flex;
  align-items: center;
  gap: 10px;
}

.percent-bar {
  flex: 1 1 auto;
  height: 8px;
  background: rgba(47, 156, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
  min-width: 60px;
}

.percent-fill {
  display: block;
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.percent-text {
  flex: 0 0 auto;
  font-size: 12px;
  color: var(--ws-text-secondary);
  font-variant-numeric: tabular-nums;
  min-width: 48px;
  text-align: right;
}

.empty-cell {
  text-align: center;
  color: var(--ws-text-muted);
  padding: 24px 12px;
}

.source-table tfoot td {
  font-size: 13px;
  font-weight: 600;
  color: var(--ws-text-primary);
  border-top: 1px solid var(--ws-border);
  border-bottom: none;
  background: rgba(0, 0, 0, 0.22);
  height: var(--ws-table-row-h, 44px);
}

.source-table tfoot td.col-value {
  font-variant-numeric: tabular-nums;
}

/* ── 核算口径说明 ── */
.methodology-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.methodology-item {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--ws-border-soft);
  border-radius: 6px;
}

.methodology-label {
  flex: 0 0 88px;
  font-size: 12px;
  color: var(--ws-text-secondary);
  font-weight: 500;
}

.methodology-value {
  flex: 1 1 auto;
  font-size: 13px;
  color: var(--ws-text-primary);
  line-height: 1.5;
}
</style>
