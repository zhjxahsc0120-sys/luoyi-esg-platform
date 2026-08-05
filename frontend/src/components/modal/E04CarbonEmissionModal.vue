<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { ChevronDown, FileX, Info, Lock, RefreshCw, X } from 'lucide-vue-next'
import type { E04SourceDetail, KpiDetailConfig } from '@/types/dashboard'

const props = defineProps<{ detail: KpiDetailConfig }>()
const emit = defineEmits<{ (e: 'close'): void; (e: 'retry'): void }>()
const isAcceptanceMode = new URLSearchParams(window.location.search).get('acceptance') === '1'
const modalRef = ref<HTMLDivElement | null>(null)
const chartRef = ref<HTMLDivElement | null>(null)
const materialExpanded = ref(false)
let chart: echarts.ECharts | null = null

const NUM_FONT = 'Bahnschrift, "DIN Alternate", Arial, sans-serif'

const sourceRows = computed(() => (props.detail.detailData || []) as E04SourceDetail[])
const materialDetails = computed(
  () => sourceRows.value.find((row) => row.sourceCode === 'material')?.materialDetails ?? props.detail.materialDetails ?? [],
)
const totalEmission = computed(() => sourceRows.value.reduce((sum, row) => sum + Number(row.emission || 0), 0))

const hasData = computed(() => sourceRows.value.length > 0)
const hasMonthlyData = computed(() => (props.detail.monthlyData?.length ?? 0) > 0)
const isEmptyState = computed(() => !hasData.value && props.detail.completenessStatus === 'empty')
const loadError = computed(() => (props.detail as any).loadError === true)
const demoDenied = computed(() => (props.detail as any).demoDenied === true)

/** 演示态摘要：只保留业务主信息，去掉核验/证据类字段 */
const summaryItems = computed(() =>
  (props.detail.summary || []).filter((item) => !['核验状态', '数据性质', '边界版本'].includes(item.label)),
)

const factorCards = computed(() => {
  const cards: { title: string; line: string }[] = []
  for (const row of sourceRows.value) {
    if (row.sourceCode === 'material') {
      cards.push({ title: '主要材料', line: '水泥 / 钢材 / 沥青 · 分项因子核算' })
      continue
    }
    if (row.emissionFactor == null) continue
    cards.push({
      title: row.source,
      line: `${formatNumber(row.emissionFactor, row.sourceCode === 'diesel' ? 2 : 3)} ${row.factorUnit || ''}`,
    })
  }
  return cards
})

function formatNumber(value: number, digits = 2) {
  return Number(value || 0).toLocaleString('zh-CN', { minimumFractionDigits: digits, maximumFractionDigits: digits })
}
function formatActivity(row: E04SourceDetail) {
  return `${formatNumber(row.activityValue, 2)} ${row.activityUnit}`
}
function formatFactor(row: E04SourceDetail) {
  if (row.sourceCode === 'material' || row.emissionFactor === null) return '分项核算'
  const digits = row.sourceCode === 'diesel' ? 2 : 3
  return `${formatNumber(row.emissionFactor, digits)} ${row.factorUnit}`
}
function summaryColor(label: string) {
  if (label === '累计碳排放') return '#69e36f'
  if (label === '统计起点') return '#8ec8ff'
  return '#e8f3ff'
}

function initChart() {
  if (!chartRef.value || !hasMonthlyData.value) return
  chart?.dispose()
  chart = echarts.init(chartRef.value)
  const monthly = props.detail.monthlyData ?? []
  chart.setOption({
    animation: !isAcceptanceMode,
    animationDuration: 450,
    textStyle: { fontFamily: NUM_FONT },
    tooltip: {
      trigger: 'axis',
      textStyle: { fontSize: 13, fontFamily: NUM_FONT },
      formatter: (params: any[]) =>
        [params[0]?.axisValue ?? '', ...params.map((item) => `${item.marker}${item.seriesName}：${formatNumber(item.value)} tCO₂e`)].join('<br/>'),
    },
    legend: {
      top: 4,
      left: 'center',
      itemWidth: 12,
      itemHeight: 8,
      itemGap: 28,
      textStyle: { color: '#b8cce3', fontSize: 13, fontFamily: NUM_FONT },
      data: ['当月排放', '累计排放'],
    },
    grid: { left: 58, right: 64, top: 42, bottom: 32 },
    xAxis: {
      type: 'category',
      data: monthly.map((item) => item.period.replace(/^\d{4}-/, '') + '月'),
      axisLine: { lineStyle: { color: 'rgba(143,169,200,.28)' } },
      axisTick: { show: false },
      axisLabel: { color: '#b8cce3', fontSize: 13, margin: 10, fontFamily: NUM_FONT },
    },
    yAxis: [
      {
        type: 'value',
        name: '当月 tCO₂e',
        nameGap: 12,
        nameTextStyle: { color: '#8fa9c8', fontSize: 12, padding: [0, 0, 0, 0] },
        axisLabel: { color: '#8fa9c8', fontSize: 12, fontFamily: NUM_FONT },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,.09)' } },
      },
      {
        type: 'value',
        name: '累计 tCO₂e',
        nameGap: 12,
        nameTextStyle: { color: '#8fa9c8', fontSize: 12 },
        axisLabel: { color: '#8fa9c8', fontSize: 12, fontFamily: NUM_FONT },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '当月排放',
        type: 'bar',
        barWidth: 24,
        data: monthly.map((item) => item.monthlyEmission),
        itemStyle: { color: '#69e36f', borderRadius: [3, 3, 0, 0] },
      },
      {
        name: '累计排放',
        type: 'line',
        yAxisIndex: 1,
        symbol: 'circle',
        symbolSize: 7,
        lineStyle: { width: 2, color: '#e8f3ff' },
        itemStyle: { color: '#e8f3ff' },
        data: monthly.map((item) => item.cumulativeEmission),
      },
    ],
  })
}

function handleResize() {
  chart?.resize()
}
function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') emit('close')
}
function handleOverlayClick(event: MouseEvent) {
  if (event.target === event.currentTarget) emit('close')
}

watch(() => props.detail.monthlyData, () => nextTick(initChart), { deep: true })
onMounted(() => {
  nextTick(() => {
    initChart()
    modalRef.value?.focus()
  })
  window.addEventListener('resize', handleResize)
  window.addEventListener('keydown', handleKeydown)
})
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleKeydown)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <Teleport to="body">
    <div class="e04-overlay" :class="{ acceptance: isAcceptanceMode }" @click="handleOverlayClick">
      <div
        ref="modalRef"
        class="e04-modal"
        :class="{ acceptance: isAcceptanceMode }"
        role="dialog"
        aria-modal="true"
        aria-labelledby="e04-modal-title"
        tabindex="-1"
      >
        <header class="e04-header">
          <h2 id="e04-modal-title"><i /><span>E04</span>项目累计碳排放</h2>
          <button type="button" aria-label="关闭" @click="emit('close')"><X :size="20" /></button>
        </header>

        <section class="e04-summary" aria-label="E04摘要">
          <div v-for="item in summaryItems" :key="item.label" class="summary-card">
            <span>{{ item.label }}</span>
            <div>
              <strong :class="{ 'is-text': typeof item.value !== 'number' }" :style="{ color: summaryColor(item.label) }">
                {{ typeof item.value === 'number' ? formatNumber(item.value) : item.value }}
              </strong>
              <small v-if="item.unit">{{ item.unit }}</small>
            </div>
          </div>
        </section>

        <div v-if="loadError" class="exception-state api-error-state">
          <RefreshCw :size="40" />
          <p class="exception-title">数据加载失败</p>
          <p class="exception-sub">无法获取碳排放核算数据，请稍后重试。</p>
          <button type="button" class="retry-btn" @click="emit('retry')"><RefreshCw :size="14" />重新加载</button>
        </div>

        <div v-else-if="demoDenied" class="exception-state">
          <Lock :size="40" />
          <p class="exception-title">数据未开放</p>
          <p class="exception-sub">当前环境暂无可用核算批次。</p>
        </div>

        <div v-else-if="isEmptyState" class="exception-state">
          <FileX :size="40" />
          <p class="exception-title">暂无数据</p>
          <p class="exception-sub">未检测到核算批次。</p>
        </div>

        <main v-else class="e04-content">
          <div class="e04-main">
            <section class="panel chart-panel">
              <h3>{{ detail.chartTitle }}</h3>
              <div v-if="hasMonthlyData" ref="chartRef" class="e04-chart" />
              <div v-else class="chart-placeholder"><Info :size="18" /><span>暂无月度排放数据</span></div>
            </section>

            <section class="panel source-panel">
              <div class="panel-heading">
                <h3>{{ detail.detailTitle }}</h3>
                <span>单位：tCO₂e</span>
              </div>
              <div class="source-table-wrap">
                <table class="source-table">
                  <colgroup>
                    <col /><col /><col /><col /><col />
                  </colgroup>
                  <thead>
                    <tr>
                      <th>排放来源</th>
                      <th>活动数据</th>
                      <th>排放因子</th>
                      <th>排放量</th>
                      <th>占比</th>
                    </tr>
                  </thead>
                  <tbody>
                    <template v-for="row in sourceRows" :key="row.sourceCode">
                      <tr>
                        <td>
                          <button
                            v-if="row.sourceCode === 'material'"
                            type="button"
                            class="material-toggle"
                            :aria-expanded="materialExpanded"
                            @click="materialExpanded = !materialExpanded"
                          >
                            <ChevronDown :size="14" :class="{ expanded: materialExpanded }" />{{ row.source }}
                          </button>
                          <span v-else>{{ row.source }}</span>
                        </td>
                        <td>{{ formatActivity(row) }}</td>
                        <td>{{ formatFactor(row) }}</td>
                        <td>{{ formatNumber(row.emission) }}</td>
                        <td>{{ row.share.toFixed(1) }}%</td>
                      </tr>
                      <tr v-if="row.sourceCode === 'material' && materialExpanded" class="material-detail-row">
                        <td colspan="5">
                          <div class="material-grid">
                            <div v-for="item in materialDetails" :key="item.material" class="material-card">
                              <strong>{{ item.material }}</strong>
                              <span>{{ formatNumber(item.activityValue) }} {{ item.activityUnit }}</span>
                              <span>{{ formatNumber(item.emissionFactor, 2) }} {{ item.factorUnit }}</span>
                              <b>{{ formatNumber(item.emission) }} tCO₂e</b>
                            </div>
                          </div>
                        </td>
                      </tr>
                    </template>
                  </tbody>
                  <tfoot>
                    <tr>
                      <td>合计</td>
                      <td>—</td>
                      <td>—</td>
                      <td>{{ formatNumber(totalEmission) }}</td>
                      <td>100.0%</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </section>
          </div>

          <aside class="e04-side">
            <section class="panel composition-panel">
              <h3>排放来源构成</h3>
              <div class="composition-list">
                <div v-for="row in sourceRows" :key="row.sourceCode" class="composition-item">
                  <div class="composition-head">
                    <span>{{ row.source }}</span>
                    <strong>{{ formatNumber(row.emission) }} <small>tCO₂e</small></strong>
                  </div>
                  <div class="share-track"><i :style="{ width: `${row.share}%` }" /></div>
                  <small class="share-pct">{{ row.share.toFixed(1) }}%</small>
                </div>
              </div>
            </section>

            <section class="panel factor-panel">
              <h3>核算参数</h3>
              <ul class="factor-list">
                <li v-for="card in factorCards" :key="card.title">
                  <span>{{ card.title }}</span>
                  <strong>{{ card.line }}</strong>
                </li>
              </ul>
              <p class="factor-note">计入：用油 · 用电 · 材料；运输暂不纳入</p>
            </section>
          </aside>
        </main>

        <footer class="e04-footer">
          <button type="button" @click="emit('close')">关闭</button>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<style scoped lang="scss">
.e04-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  box-sizing: border-box;
  background: rgba(2, 11, 24, 0.72);
  &.acceptance {
    animation: none;
  }
}

.e04-modal {
  width: min(1436px, calc(100vw - 48px));
  height: min(880px, calc(100vh - 48px));
  max-width: 1436px;
  max-height: 880px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(105, 227, 111, 0.35);
  border-radius: 8px;
  outline: none;
  background: rgba(4, 25, 48, 0.98);
  color: #d7e6f5;
  font-family: 'Microsoft YaHei UI', 'PingFang SC', 'Noto Sans SC', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: geometricPrecision;
  &.acceptance,
  &.acceptance * {
    animation: none !important;
    transition: none !important;
  }
}

.e04-header {
  height: 48px;
  flex: 0 0 48px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 16px;
  border-bottom: 1px solid rgba(105, 227, 111, 0.16);

  h2 {
    margin: 0;
    flex: 1;
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 19px;
    font-weight: 700;
    color: #f3f8ff;
    line-height: 1.2;

    i {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #69e36f;
      box-shadow: 0 0 0 3px rgba(105, 227, 111, 0.18);
      flex-shrink: 0;
    }

    span {
      color: #69e36f;
      font-family: Bahnschrift, 'DIN Alternate', Arial, sans-serif;
      font-size: 18px;
      font-weight: 700;
      margin-right: 2px;
    }
  }

  button {
    width: 32px;
    height: 32px;
    display: grid;
    place-items: center;
    border: 0;
    border-radius: 4px;
    background: transparent;
    color: #8fa9c8;
    cursor: pointer;
    flex-shrink: 0;
  }

  button:hover,
  button:focus-visible {
    background: rgba(105, 227, 111, 0.08);
    color: #e8f3ff;
    outline: 1px solid rgba(105, 227, 111, 0.28);
  }
}

.e04-summary {
  flex: 0 0 auto;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  padding: 12px 16px 0;
}

.summary-card {
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
  padding: 10px 12px;
  border: 1px solid rgba(105, 227, 111, 0.15);
  border-radius: 6px;
  background: rgba(105, 227, 111, 0.035);

  > span {
    color: #9fb6ce;
    font-size: 13px;
    line-height: 18px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  > div {
    min-width: 0;
    display: flex;
    align-items: baseline;
    gap: 6px;
    white-space: nowrap;
  }

  strong {
    min-width: 0;
    font-family: Bahnschrift, 'DIN Alternate', Arial, sans-serif;
    font-size: 24px;
    line-height: 28px;
    font-weight: 700;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  strong.is-text {
    font-size: 18px;
    line-height: 24px;
    font-weight: 600;
  }

  small {
    color: #8fa9c8;
    font-size: 13px;
    flex-shrink: 0;
  }
}

.exception-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #6f879d;

  .exception-title {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: #b8cce3;
  }

  .exception-sub {
    margin: 0;
    font-size: 13px;
    max-width: 360px;
    text-align: center;
    line-height: 1.6;
  }
}

.retry-btn {
  margin-top: 8px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border: 1px solid rgba(105, 227, 111, 0.35);
  border-radius: 4px;
  background: rgba(105, 227, 111, 0.08);
  color: #e8f3ff;
  font-size: 14px;
  cursor: pointer;
}

.api-error-state {
  color: #ff8a8a;
  .exception-title {
    color: #ff8a8a;
  }
}

.e04-content {
  min-height: 0;
  flex: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 12px;
  padding: 12px 16px;
  box-sizing: border-box;
}

.e04-main,
.e04-side {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.panel {
  min-width: 0;
  min-height: 0;
  box-sizing: border-box;
  border: 1px solid rgba(105, 227, 111, 0.15);
  border-radius: 6px;
  background: rgba(4, 22, 40, 0.72);

  h3 {
    margin: 0;
    color: #e8f3ff;
    font-size: 15px;
    line-height: 22px;
    font-weight: 600;
  }
}

.chart-panel {
  flex: 0 0 236px;
  padding: 10px 12px;
}

.e04-chart {
  width: 100%;
  height: 190px;
}

.chart-placeholder {
  width: 100%;
  height: 190px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #6f879d;
  font-size: 13px;
}

.source-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-heading {
  height: 36px;
  flex: 0 0 36px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  border-bottom: 1px solid rgba(143, 169, 200, 0.1);

  span {
    color: #8fa9c8;
    font-size: 12px;
  }
}

.source-table-wrap {
  min-height: 0;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  scrollbar-color: rgba(143, 169, 200, 0.48) rgba(143, 169, 200, 0.08);
}

.source-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 13px;

  col {
    width: 20%;
  }

  th,
  td {
    width: 20%;
    height: 38px;
    padding: 0 8px;
    text-align: center;
    vertical-align: middle;
    border-bottom: 1px solid rgba(143, 169, 200, 0.12);
    border-right: 1px solid rgba(143, 169, 200, 0.14);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  th:last-child,
  td:last-child {
    border-right: 0;
  }

  th {
    height: 36px;
    background: #071b31;
    color: #b8cce3;
    font-size: 13px;
    font-weight: 600;
  }

  td {
    color: #d9e7f5;
    font-family: Bahnschrift, 'DIN Alternate', Arial, sans-serif;
    font-variant-numeric: tabular-nums;
  }

  td:first-child {
    font-family: 'Microsoft YaHei UI', 'PingFang SC', 'Noto Sans SC', sans-serif;
  }

  tbody tr:hover:not(.material-detail-row) {
    background: rgba(105, 227, 111, 0.035);
  }

  tfoot td {
    color: #e8f3ff;
    font-weight: 600;
    background: rgba(105, 227, 111, 0.035);
  }
}

.material-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 0;
  border: 0;
  background: transparent;
  color: #e8f3ff;
  font: inherit;
  cursor: pointer;

  svg {
    transition: transform 0.15s ease;
  }

  svg.expanded {
    transform: rotate(180deg);
  }
}

.material-detail-row td {
  height: auto;
  padding: 8px 10px 10px;
  background: rgba(47, 156, 255, 0.035);
  white-space: normal;
  text-align: left;
  border-right: 0;
}

.material-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.material-card {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 4px 10px;
  padding: 8px 10px;
  border: 1px solid rgba(47, 156, 255, 0.15);
  border-radius: 4px;
  color: #b8cce3;
  font-size: 12px;

  strong {
    color: #e8f3ff;
    font-size: 13px;
    grid-column: 1 / -1;
  }

  b {
    color: #69e36f;
    text-align: right;
    font-family: Bahnschrift, 'DIN Alternate', Arial, sans-serif;
  }
}

.e04-side .panel {
  padding: 10px 12px;
  overflow-y: auto;
  scrollbar-width: thin;
}

.composition-panel {
  flex: 1.35;
}

.composition-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.composition-item {
  position: relative;
  padding-right: 42px;
}

.composition-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  font-size: 13px;
  color: #d7e6f5;

  strong {
    font-family: Bahnschrift, 'DIN Alternate', Arial, sans-serif;
    font-size: 17px;
    font-variant-numeric: tabular-nums;

    small {
      color: #8fa9c8;
      font-size: 11px;
      font-weight: 400;
    }
  }
}

.share-pct {
  position: absolute;
  right: 0;
  bottom: -2px;
  color: #b8cce3;
  font-family: Bahnschrift, 'DIN Alternate', Arial, sans-serif;
  font-size: 12px;
}

.share-track {
  height: 6px;
  margin-top: 6px;
  overflow: hidden;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.06);

  i {
    display: block;
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, rgba(105, 227, 111, 0.48), #69e36f);
  }
}

.factor-panel {
  flex: 1;
}

.factor-list {
  list-style: none;
  margin: 10px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;

  li {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 8px 10px;
    border: 1px solid rgba(143, 169, 200, 0.12);
    border-radius: 4px;
    background: rgba(7, 27, 49, 0.55);

    span {
      color: #9fb6ce;
      font-size: 12px;
    }

    strong {
      color: #e8f3ff;
      font-size: 13px;
      font-weight: 600;
      font-family: Bahnschrift, 'DIN Alternate', Arial, sans-serif;
      line-height: 1.35;
    }
  }
}

.factor-note {
  margin: 10px 0 0;
  color: #8fa9c8;
  font-size: 12px;
  line-height: 1.5;
}

.e04-footer {
  height: 48px;
  flex: 0 0 48px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 16px;
  border-top: 1px solid rgba(105, 227, 111, 0.12);

  button {
    width: 110px;
    height: 32px;
    border: 1px solid rgba(105, 227, 111, 0.35);
    border-radius: 4px;
    background: rgba(105, 227, 111, 0.08);
    color: #e8f3ff;
    font-size: 14px;
    cursor: pointer;
  }

  button:hover,
  button:focus-visible {
    background: rgba(105, 227, 111, 0.15);
    outline: none;
  }
}
</style>
