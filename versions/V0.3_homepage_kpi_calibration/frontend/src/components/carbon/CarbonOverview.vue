<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboard.store'
import { getDashboardPanels } from '@/services/api'
import type { CarbonSource, ReductionMeasure } from '@/types/dashboard'

const store = useDashboardStore()

const loading = ref(false)

/** 三项碳排核心指标（来自 store.carbon） */
const carbonMetrics = computed(() => store.carbon)
/** 碳排放来源构成（来自 store.carbonSrc） */
const carbonSources = computed(() => store.carbonSrc)
/** 减排措施（来自 store.reductions） */
const reductionMeasures = computed(() => store.reductions)

/** 来源合计值，用于计算各来源占比 */
const sourceTotal = computed(() =>
  carbonSources.value.reduce((sum, s) => sum + (Number(s?.value) || 0), 0),
)

function sourcePercent(value: number | undefined | null): number {
  const total = sourceTotal.value
  if (!total) return 0
  return ((Number(value) || 0) / total) * 100
}

/** 数值格式化；空值统一回退为 '--' */
function formatValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === '') return '--'
  const num = Number(value)
  if (Number.isNaN(num)) return String(value)
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  })
}

/** 指标卡强调色：碳足迹-绿 / 减排量-蓝 / 节约成本-紫 */
const metricColors = ['#69e36f', '#2f9cff', '#a66cff']
function metricColor(index: number): string {
  return metricColors[index] ?? '#2f9cff'
}

/** 来源默认配色（store 数据可能不带 color 字段） */
const sourceColorMap: Record<string, string> = {
  施工用油: '#69e36f',
  施工用电: '#2f9cff',
  主要材料: '#a66cff',
}
function sourceColor(name: string | undefined | null, color?: string): string {
  if (color) return color
  if (name && sourceColorMap[name]) return sourceColorMap[name]
  return '#2f9cff'
}

/** 措施等级颜色：高-绿 / 较高-蓝 / 中-紫 / 低-黄 */
const levelColorMap: Record<string, string> = {
  高: '#69e36f',
  较高: '#2f9cff',
  中: '#a66cff',
  低: '#ffb347',
}
function levelColor(level: string | undefined | null): string {
  return (level && levelColorMap[level]) || '#8fa9c8'
}

function levelStyle(level: string | undefined | null): Record<string, string> {
  const c = levelColor(level)
  return {
    color: c,
    borderColor: c,
    background: `${c}1f`,
  }
}

onMounted(async () => {
  loading.value = true
  try {
    // 从接口刷新面板数据；接口不可用时回退到 store 内置 mock 数据
    const data = await getDashboardPanels()
    if (data?.carbon) {
      if (data.carbon.metrics) {
        store.carbon = data.carbon.metrics as {
          label: string
          value: number
          unit: string
          sub: string
        }[]
      }
      if (data.carbon.sources) {
        store.carbonSrc = data.carbon.sources as CarbonSource[]
      }
      if (data.carbon.reductions) {
        store.reductions = data.carbon.reductions as ReductionMeasure[]
      }
    }
  } catch {
    // 静默回退到 store mock 数据
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="ws-page carbon-overview" :class="{ 'is-loading': loading }">
    <!-- 顶部三项核心指标卡 -->
    <section class="metric-row">
      <div
        v-for="(m, i) in carbonMetrics"
        :key="i"
        class="metric-card"
        :style="{ '--accent': metricColor(i) }"
      >
        <div class="metric-label">{{ m?.label || '--' }}</div>
        <div class="metric-value-row">
          <span class="metric-value">{{ formatValue(m?.value) }}</span>
          <span class="metric-unit">{{ m?.unit || '' }}</span>
        </div>
        <div class="metric-sub">{{ m?.sub || '' }}</div>
      </div>
      <div v-if="!carbonMetrics.length" class="metric-card metric-empty">
        暂无碳排指标数据
      </div>
    </section>

    <!-- 来源构成 + 减排措施 -->
    <section class="dual-row">
      <!-- 来源构成 -->
      <div class="ws-panel source-panel">
        <div class="ws-panel-header">
          <span class="ws-panel-title">碳排放来源构成</span>
          <span class="ws-panel-count">合计 {{ formatValue(sourceTotal) }} tCO₂e</span>
        </div>
        <div class="source-list">
          <div v-for="(s, i) in carbonSources" :key="i" class="source-item">
            <div class="source-head">
              <span class="source-name">{{ s?.name || '--' }}</span>
              <span class="source-val">
                <span class="source-val-num">{{ formatValue(s?.value) }}</span>
                <span class="source-val-unit">tCO₂e</span>
                <span class="source-val-pct">{{ sourcePercent(s?.value).toFixed(1) }}%</span>
              </span>
            </div>
            <div class="source-bar">
              <div
                class="source-bar-fill"
                :style="{
                  width: sourcePercent(s?.value) + '%',
                  background: sourceColor(s?.name, s?.color),
                }"
              ></div>
            </div>
          </div>
          <p v-if="!carbonSources.length" class="empty-tip">暂无来源构成数据</p>
        </div>
      </div>

      <!-- 减排措施 -->
      <div class="ws-panel measure-panel">
        <div class="ws-panel-header">
          <span class="ws-panel-title">减排措施</span>
        </div>
        <div class="measure-list">
          <div v-for="(r, i) in reductionMeasures" :key="i" class="measure-item">
            <span class="measure-name">{{ r?.name || '--' }}</span>
            <span class="measure-level" :style="levelStyle(r?.level)">
              {{ r?.level || '--' }}
            </span>
          </div>
          <p v-if="!reductionMeasures.length" class="empty-tip">暂无减排措施数据</p>
        </div>
      </div>
    </section>

    <!-- 核算口径说明 -->
    <section class="ws-panel method-panel">
      <div class="ws-panel-header">
        <span class="ws-panel-title">核算口径（7.14）</span>
      </div>
      <ul class="method-list">
        <li>核算口径：施工用油 + 施工用电 + 主要材料</li>
        <li>运输排放暂不纳入核算边界</li>
        <li>统计起点：2026-05-08（开工令日期）</li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.carbon-overview {
  /* 基于 .ws-page 的 flex 列布局，此处仅做局部补充 */
}

.carbon-overview.is-loading {
  opacity: 0.7;
  pointer-events: none;
}

/* ── 顶部指标卡行 ── */
.metric-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--ws-card-gap);
  flex-shrink: 0;
}

.metric-card {
  background: var(--ws-bg-panel);
  border: 1px solid var(--ws-border);
  border-radius: var(--ws-panel-radius);
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  position: relative;
  overflow: hidden;
  box-sizing: border-box;
  min-height: 92px;
}

.metric-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--accent, var(--ws-cyan));
}

.metric-empty {
  grid-column: 1 / -1;
  align-items: center;
  justify-content: center;
  color: var(--ws-text-muted);
  font-size: 13px;
}

.metric-label {
  font-size: 14px;
  color: var(--ws-text-secondary);
  line-height: 20px;
}

.metric-value-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.metric-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--accent, var(--ws-cyan));
  line-height: 38px;
  font-variant-numeric: tabular-nums;
}

.metric-unit {
  font-size: 13px;
  color: var(--ws-text-secondary);
}

.metric-sub {
  font-size: 12px;
  color: var(--ws-text-muted);
  line-height: 16px;
}

/* ── 两栏区：来源构成 / 减排措施 ── */
.dual-row {
  flex: 1 1 auto;
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: var(--ws-section-gap);
  min-height: 0;
}

.source-panel,
.measure-panel {
  min-height: 0;
}

/* 来源构成 */
.source-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-top: 4px;
}

.source-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.source-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.source-name {
  font-size: 13px;
  color: var(--ws-text-primary);
}

.source-val {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.source-val-num {
  font-size: 16px;
  font-weight: 600;
  color: var(--ws-text-primary);
  font-variant-numeric: tabular-nums;
}

.source-val-unit {
  font-size: 11px;
  color: var(--ws-text-secondary);
}

.source-val-pct {
  font-size: 12px;
  color: var(--ws-text-secondary);
  font-variant-numeric: tabular-nums;
  margin-left: 4px;
}

.source-bar {
  height: 8px;
  background: rgba(47, 156, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.source-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;
}

/* 减排措施 */
.measure-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 4px;
}

.measure-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--ws-border-soft);
  border-radius: 6px;
}

.measure-name {
  font-size: 13px;
  color: var(--ws-text-primary);
}

.measure-level {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 12px;
  border-radius: 999px;
  border: 1px solid;
  white-space: nowrap;
}

/* ── 核算口径 ── */
.method-panel {
  flex-shrink: 0;
}

.method-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.method-list li {
  font-size: 13px;
  color: var(--ws-text-secondary);
  line-height: 20px;
  padding-left: 14px;
  position: relative;
}

.method-list li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 7px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--ws-cyan);
}

/* ── 空状态 ── */
.empty-tip {
  margin: 0;
  padding: 20px 0;
  text-align: center;
  font-size: 13px;
  color: var(--ws-text-muted);
}
</style>
