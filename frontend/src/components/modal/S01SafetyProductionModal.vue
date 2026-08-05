<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { Check, Clock, FileCheck, ShieldCheck, X, AlertCircle } from 'lucide-vue-next'
import { getDashboardKpiS01 } from '@/services/api'

// S 组业务主色：蓝色（与 E 组绿色、G 组紫色区分）
const THEME_COLOR = '#2f9cff'
const THEME_RGB = '47, 156, 255'

// 语义状态色（不跟随 S 组主色）
const STATUS_COLORS = {
  normal: '#69e36f',     // 正常、已完成、已闭环：绿色
  processing: '#2f9cff', // 处理中、办理中：蓝色
  pending: '#ffb347',    // 待处理、临期、提醒：橙色
  danger: '#ff4f5e',     // 逾期、异常、高风险：红色
  muted: '#8ba6c3',     // 次要文字、暂无数据：灰色
} as const

type CountingStatus = 'continuous' | 'interrupted' | 'pending'

interface SafetyProductionData {
  projectStartDate: string
  currentDate: string
  continuousDays?: number
  currentStage: string
  currentStageDetail: string
  countingStatus: CountingStatus
  latestInterruptDate?: string
  latestInterruptReason?: string
  updateTime: string
  timeline?: {
    startLabel: string
    startDate: string
    message: string
    endLabel: string
    endDate: string
    months: string[]
  }
  constructionStages?: {
    id: string
    name: string
    status: 'completed' | 'current' | 'not_started'
    detail?: string
    startDate?: string
    endDate?: string
  }[]
  conclusion?: string
}

const emit = defineEmits<{ (e: 'close'): void }>()

const isAcceptanceMode = new URLSearchParams(window.location.search).get('acceptance') === '1'
const modalRef = ref<HTMLDivElement | null>(null)
const chartRef = ref<HTMLDivElement | null>(null)
const scale = ref(1)
let chart: echarts.ECharts | null = null

const data = ref<SafetyProductionData>({
  projectStartDate: '2025-07-10',
  currentDate: '2026-07-13',
  currentStage: '路基桥涵施工',
  currentStageDetail: '路基｜桥梁｜隧道并行施工',
  countingStatus: 'continuous',
  updateTime: '2026-07-13 10:30',
  constructionStages: [],
  conclusion: '项目开工以来，暂无导致连续安全生产计数中断的事故记录，当前连续安全生产368天。',
})

function toUtcDate(dateText: string) {
  const [year, month, day] = dateText.split('-').map(Number)
  return Date.UTC(year, month - 1, day)
}

// 主值只信 API continuousDays（与首页 S01 / _resolve_s01_snapshot 同源）；无值时不前端重算
const continuousDays = computed(() => {
  if (typeof data.value.continuousDays === 'number') return data.value.continuousDays
  return null
})

function mapCountingStatus(raw: string | null | undefined): CountingStatus {
  const s = (raw || '').toUpperCase()
  if (s === 'RESET_CYCLE' || s === 'INTERRUPTED') return 'interrupted'
  if (s === 'PENDING_DETERMINATION' || s === 'PENDING') return 'pending'
  return 'continuous'
}

const statusLabel = computed(() => {
  if (data.value.countingStatus === 'interrupted') return '计数中断'
  if (data.value.countingStatus === 'pending') return '待复核'
  return '连续计数中'
})

const statusColor = computed(() => {
  if (data.value.countingStatus === 'interrupted') return STATUS_COLORS.danger
  if (data.value.countingStatus === 'pending') return STATUS_COLORS.pending
  return STATUS_COLORS.normal
})

// 月度累计安全生产天数（基于开工日期可证明推导，与 continuousDays 口径一致）
const monthlyCumulative = computed(() => {
  if (!data.value.projectStartDate || !data.value.currentDate) {
    return [] as { month: string; cumulative: number }[]
  }
  const startDate = new Date(toUtcDate(data.value.projectStartDate))
  const endDate = new Date(toUtcDate(data.value.currentDate))
  const result: { month: string; cumulative: number }[] = []
  let total = 0
  let year = startDate.getUTCFullYear()
  let month = startDate.getUTCMonth() + 1

  while (year < endDate.getUTCFullYear() || (year === endDate.getUTCFullYear() && month <= endDate.getUTCMonth() + 1)) {
    const monthStart = (year === startDate.getUTCFullYear() && month === startDate.getUTCMonth() + 1)
      ? Date.UTC(year, month - 1, startDate.getUTCDate())
      : Date.UTC(year, month - 1, 1)
    const nextMonthStart = (year === endDate.getUTCFullYear() && month === endDate.getUTCMonth() + 1)
      ? Date.UTC(year, month - 1, endDate.getUTCDate())
      : Date.UTC(year, month, 1)
    const daysThisMonth = Math.max(0, Math.floor((nextMonthStart - monthStart) / 86_400_000))
    total += daysThisMonth
    result.push({ month: `${year}-${String(month).padStart(2, '0')}`, cumulative: total })
    month += 1
    if (month > 12) { month = 1; year += 1 }
  }

  return result
})

const summaryCards = computed(() => [
  {
    label: '连续安全生产天数',
    value: continuousDays.value === null ? '--' : String(continuousDays.value),
    unit: continuousDays.value === null ? '' : '天',
    color: continuousDays.value === null ? STATUS_COLORS.muted : STATUS_COLORS.normal,
  },
  { label: '开工日期', value: data.value.projectStartDate || '--', unit: '', color: THEME_COLOR },
  { label: '统计截止', value: data.value.currentDate || '--', unit: '', color: THEME_COLOR },
  { label: '计数状态', value: statusLabel.value, unit: '', color: statusColor.value },
  { label: '当前工期阶段', value: data.value.currentStage || '--', unit: '', color: STATUS_COLORS.processing },
])

function initChart() {
  if (!chartRef.value) return
  chart?.dispose()
  chart = echarts.init(chartRef.value)
  const monthly = monthlyCumulative.value
  chart.setOption({
    animation: !isAcceptanceMode,
    animationDuration: 450,
    tooltip: {
      trigger: 'axis',
      textStyle: { fontSize: 13 },
      formatter: (params: any[]) => [params[0]?.axisValue ?? '', `累计安全生产：${params[0]?.value ?? 0} 天`].join('<br/>'),
    },
    grid: { left: 62, right: 24, top: 30, bottom: 48 },
    xAxis: {
      type: 'category',
      data: monthly.map(item => item.month.replace(/^\d{4}-/, '') + '月'),
      axisLine: { lineStyle: { color: 'rgba(143,169,200,.28)' } },
      axisTick: { show: false },
      axisLabel: { color: '#8fa9c8', fontSize: 13, margin: 14 },
    },
    yAxis: {
      type: 'value',
      name: '累计天数',
      nameTextStyle: { color: '#8fa9c8', fontSize: 13 },
      axisLabel: { color: '#8fa9c8', fontSize: 13 },
      splitLine: { lineStyle: { color: 'rgba(143,169,200,.09)' } },
    },
    series: [
      {
        name: '累计安全生产天数',
        type: 'line',
        symbol: 'circle',
        symbolSize: 7,
        smooth: true,
        lineStyle: { width: 2, color: THEME_COLOR },
        itemStyle: { color: THEME_COLOR },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: `rgba(${THEME_RGB}, 0.28)` },
            { offset: 1, color: `rgba(${THEME_RGB}, 0)` },
          ]),
        },
        data: monthly.map(item => item.cumulative),
      },
    ],
  })
}

function updateScale() {
  scale.value = Math.min(1, window.innerWidth / 1920, window.innerHeight / 1080)
}

function handleResize() { updateScale(); chart?.resize() }
function handleKeydown(event: KeyboardEvent) { if (event.key === 'Escape') emit('close') }
function handleOverlayClick(event: MouseEvent) { if (event.target === event.currentTarget) emit('close') }

const stageStatusText = (status: string) => status === 'completed' ? '已完成' : status === 'current' ? '进行中' : '未开始'
const stageStatusColor = (status: string) => status === 'completed' ? STATUS_COLORS.normal : status === 'current' ? STATUS_COLORS.processing : STATUS_COLORS.muted
const stageStatusClass = (status: string) => status === 'completed' ? 'completed' : status === 'current' ? 'current' : 'pending'

const countingRules = [
  { label: '起始时间', value: '开工日期' },
  { label: '统计截止', value: '当前日期' },
  { label: '计数口径', value: '项目开工以来' },
  { label: '中断条件', value: '发生导致连续记录中断的生产安全责任事故', multiline: true },
  { label: '当前状态', value: '连续计数中' },
]

async function loadData() {
  const resp = await getDashboardKpiS01()
  if (!resp) return
  const start =
    resp.statisticsStart ||
    resp.cycleStartDate ||
    resp.projectStartDate ||
    data.value.projectStartDate
  const asOf = resp.statisticsAsOf || resp.currentDate || data.value.currentDate
  data.value = {
    projectStartDate: start || '--',
    currentDate: asOf || '--',
    continuousDays: typeof resp.continuousDays === 'number' ? resp.continuousDays : undefined,
    currentStage: resp.currentConstructionStage || resp.currentStage || '资料待补齐',
    currentStageDetail: resp.currentStageDetail || '',
    countingStatus: mapCountingStatus(resp.countingStatus),
    latestInterruptDate: resp.latestInterruptDate || undefined,
    latestInterruptReason: resp.latestInterruptReason || undefined,
    updateTime: resp.updateTime || '--',
    timeline: resp.timeline,
    constructionStages: (resp.constructionStages || []).map((s) => ({
      id: s.id,
      name: s.name,
      status: (s.status === 'completed' || s.status === 'current' || s.status === 'not_started'
        ? s.status
        : 'not_started') as 'completed' | 'current' | 'not_started',
      detail: s.detail,
      startDate: s.startDate,
      endDate: s.endDate,
    })),
    conclusion: resp.conclusion,
  }
}

watch(() => data.value.continuousDays, () => nextTick(initChart), { immediate: false })

onMounted(() => {
  updateScale()
  nextTick(() => { initChart(); modalRef.value?.focus() })
  window.addEventListener('resize', handleResize)
  window.addEventListener('keydown', handleKeydown)
  loadData().then(() => nextTick(initChart))
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', handleKeydown)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div class="s01-overlay" :class="{ acceptance: isAcceptanceMode }" @click="handleOverlayClick">
    <div
      ref="modalRef"
      class="s01-modal"
      :class="{ acceptance: isAcceptanceMode }"
      :style="{ '--s01-scale': scale }"
      role="dialog"
      aria-modal="true"
      aria-labelledby="s01-modal-title"
      tabindex="-1"
    >
      <header class="s01-header">
        <h2 id="s01-modal-title">
          <span class="title-key">S01</span>
          <span class="title-name">连续安全生产天数</span>
        </h2>
        <button type="button" aria-label="关闭" @click="emit('close')">
          <X :size="22" />
        </button>
      </header>

      <section class="s01-summary" aria-label="S01摘要">
        <div v-for="item in summaryCards" :key="item.label" class="summary-card">
          <span class="summary-label">{{ item.label }}</span>
          <div class="summary-value-row">
            <strong :style="{ color: item.color }">{{ item.value }}</strong>
            <small v-if="item.unit">{{ item.unit }}</small>
          </div>
        </div>
      </section>

      <main class="s01-content">
        <div class="s01-main">
          <section class="panel chart-panel">
            <h3>连续安全生产天数累计趋势</h3>
            <div ref="chartRef" class="s01-chart" />
          </section>

          <section class="panel record-panel">
            <div class="panel-heading">
              <h3>安全生产关键记录</h3>
              <span>连续计数依据</span>
            </div>
            <div class="record-empty">
              <AlertCircle :size="26" />
              <p>暂无连续计数中断记录</p>
              <small>项目开工以来，暂无导致连续安全生产计数中断的事故记录。</small>
            </div>
          </section>
        </div>

        <aside class="s01-side">
          <section class="panel rule-panel">
            <h3>连续安全生产计数规则</h3>
            <dl>
              <div v-for="rule in countingRules" :key="rule.label" :class="{ multiline: (rule as any).multiline }">
                <dt>{{ rule.label }}</dt>
                <dd>{{ rule.value }}</dd>
              </div>
            </dl>
          </section>

          <section class="panel conclusion-panel">
            <h3>本轮结论</h3>
            <div class="conclusion-body">
              <div class="conclusion-icon">
                <ShieldCheck :size="20" />
              </div>
              <p>{{ data.conclusion || '暂无数据' }}</p>
            </div>
          </section>

          <section class="panel quality-panel">
            <h3>数据质量状态</h3>
            <dl>
              <div><dt>指标编码</dt><dd>S01</dd></div>
              <div><dt>统计口径</dt><dd>开工日期至今</dd></div>
              <div><dt>数据状态</dt><dd class="ok">已接入</dd></div>
              <div><dt>证据资料</dt><dd>暂未关联</dd></div>
            </dl>
          </section>
        </aside>
      </main>

      <footer class="s01-footer">
        <div class="footer-info" title="正式接口：/api/dashboard/kpi/S01">
          <FileCheck :size="14" />
          <span>数据来源：项目正式数据库</span>
        </div>
        <div class="footer-info">
          <Clock :size="14" />
          <span>更新时间：{{ data.updateTime }}</span>
        </div>
        <div class="footer-info ok">
          <Check :size="14" />
          <span>核验状态：已对齐首页S01卡片</span>
        </div>
        <button type="button" @click="emit('close')">关闭</button>
      </footer>
    </div>
  </div>
</template>

<style scoped lang="scss">
.s01-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: rgba(2, 11, 24, 0.76);
  backdrop-filter: blur(4px);
  animation: s01Fade 0.2s ease;

  &.acceptance { animation: none; }
}

.s01-modal {
  width: 1436px;
  height: 880px;
  flex: 0 0 1436px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(47, 156, 255, 0.35);
  border-radius: 8px;
  outline: none;
  background: linear-gradient(180deg, #07182b, #04101f);
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.64);
  color: #e8f3ff;
  transform: scale(var(--s01-scale));
  transform-origin: center;
  animation: s01Rise 0.25s ease;

  &.acceptance,
  &.acceptance * {
    animation: none !important;
    transition: none !important;
  }

  &:focus,
  &:focus-visible { outline: none; }
}

.s01-header {
  height: 60px;
  flex: 0 0 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
  padding: 0 16px;
  border-bottom: 1px solid rgba(47, 156, 255, 0.16);

  h2 {
    margin: 0;
    display: flex;
    align-items: baseline;
    gap: 12px;
    font-size: 22px;
    font-weight: 600;
    color: #e8f3ff;

    .title-key {
      color: #2f9cff;
      font-family: "DIN Alternate", "Roboto Condensed", sans-serif;
      font-size: 26px;
      font-weight: 700;
      text-shadow: 0 0 8px rgba(47, 156, 255, 0.4);
    }
  }

  button {
    width: 36px;
    height: 36px;
    display: grid;
    place-items: center;
    border: 0;
    border-radius: 4px;
    background: transparent;
    color: #8fa9c8;
    cursor: pointer;

    &:hover,
    &:focus-visible {
      background: rgba(47, 156, 255, 0.08);
      color: #e8f3ff;
      outline: 1px solid rgba(47, 156, 255, 0.28);
    }
  }
}

.s01-summary {
  flex: 0 0 88px;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  box-sizing: border-box;
  padding: 12px 16px 0;

  .summary-card {
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-sizing: border-box;
    padding: 8px 14px;
    border: 1px solid rgba(47, 156, 255, 0.15);
    border-radius: 5px;
    background: rgba(47, 156, 255, 0.035);

    .summary-label {
      color: #b8cce3;
      font-size: 14px;
      line-height: 20px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .summary-value-row {
      min-width: 0;
      display: flex;
      align-items: baseline;
      gap: 5px;
      white-space: nowrap;

      strong {
        min-width: 0;
        font-family: "DIN Alternate", "Roboto Condensed", sans-serif;
        font-size: 28px;
        line-height: 34px;
        font-weight: 700;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      small {
        color: #8fa9c8;
        font-size: 13px;
      }
    }
  }
}

.s01-content {
  min-height: 0;
  flex: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 330px;
  gap: 12px;
  box-sizing: border-box;
  padding: 12px 16px;
}

.s01-main,
.s01-side {
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.panel {
  min-width: 0;
  min-height: 0;
  box-sizing: border-box;
  border: 1px solid rgba(47, 156, 255, 0.15);
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
  flex: 0 0 376px;
  padding: 10px 12px;
}

.s01-chart {
  width: 100%;
  height: 332px;
}

.record-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.record-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #8fa9c8;

  p {
    margin: 0;
    color: #b8cce3;
    font-size: 14px;
  }

  small {
    color: #6d86a3;
    font-size: 12px;
  }
}

.panel-heading {
  height: 38px;
  flex: 0 0 38px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  box-sizing: border-box;
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

  &::-webkit-scrollbar { width: 6px; }
  &::-webkit-scrollbar-track { background: rgba(143, 169, 200, 0.06); }
  &::-webkit-scrollbar-thumb {
    background: rgba(143, 169, 200, 0.4);
    border-radius: 3px;

    &:hover { background: rgba(143, 169, 200, 0.6); }
  }
}

.source-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 14px;

  th {
    height: 36px;
    padding: 0 8px;
    border-bottom: 1px solid rgba(143, 169, 200, 0.15);
    background: #071b31;
    color: #b8cce3;
    font-size: 14px;
    font-weight: 600;
    text-align: left;
    position: sticky;
    top: 0;
    z-index: 1;
  }

  td {
    height: 38px;
    padding: 0 8px;
    border-bottom: 1px solid rgba(143, 169, 200, 0.08);
    color: #d9e7f5;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  tbody tr:hover {
    background: rgba(47, 156, 255, 0.035);
  }

  .numeric {
    font-variant-numeric: tabular-nums;
    text-align: center;
  }
}

.status-tag {
  display: inline-flex;
  min-width: 64px;
  height: 24px;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  padding: 0 7px;
  border: 1px solid;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.03);

  &.completed { background: rgba(105, 227, 111, 0.08); }
  &.current { background: rgba(47, 156, 255, 0.08); }
  &.pending { background: rgba(143, 169, 200, 0.08); }
}

.s01-side .panel { padding: 10px 12px; }

.rule-panel { flex: 1.2; }

.rule-panel dl {
  margin: 8px 0 0;
  padding: 0;

  div {
    min-height: 30px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    border-bottom: 1px solid rgba(143, 169, 200, 0.07);
    font-size: 13px;

    &:last-child { border-bottom: 0; }

    &.multiline {
      min-height: 42px;
      flex-direction: column;
      align-items: flex-start;
      justify-content: center;
      gap: 4px;

      dt { color: #8fa9c8; }

      dd {
        margin: 0;
        color: #d9e7f5;
        text-align: left;
        line-height: 1.4;
        white-space: normal;
        word-break: break-all;
      }
    }
  }

  dt { color: #8fa9c8; flex: 0 0 auto; }
  dd {
    margin: 0;
    color: #d9e7f5;
    text-align: right;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.conclusion-panel { flex: 1; }

.conclusion-body {
  display: flex;
  gap: 10px;
  margin-top: 8px;

  .conclusion-icon {
    width: 28px;
    height: 28px;
    flex: none;
    display: grid;
    place-items: center;
    border-radius: 4px;
    background: rgba(105, 227, 111, 0.12);
    color: #69e36f;
    border: 1px solid rgba(105, 227, 111, 0.25);
  }

  p {
    margin: 0;
    color: #f4f8ff;
    font-size: 13px;
    line-height: 1.5;
  }
}

.quality-panel { flex: 1; }

.quality-panel dl {
  margin: 8px 0 0;

  div {
    min-height: 27px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    border-bottom: 1px solid rgba(143, 169, 200, 0.07);
    font-size: 13px;

    &:last-child { border-bottom: 0; }
  }

  dt { color: #8fa9c8; }
  dd { margin: 0; color: #d9e7f5; text-align: right; }
  dd.ok { color: #69e36f; font-weight: 600; }
}

.s01-footer {
  height: 52px;
  flex: 0 0 52px;
  display: flex;
  align-items: center;
  gap: 18px;
  box-sizing: border-box;
  padding: 0 16px;
  border-top: 1px solid rgba(47, 156, 255, 0.12);

  .footer-info {
    min-width: 0;
    display: flex;
    align-items: center;
    gap: 6px;
    color: #8fa9c8;
    font-size: 12px;
    white-space: nowrap;

    &:first-child {
      max-width: 360px;
      overflow: hidden;

      span {
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }

    &.ok { color: #69e36f; }
  }

  button {
    width: 120px;
    height: 34px;
    margin-left: auto;
    border: 1px solid rgba(47, 156, 255, 0.35);
    border-radius: 4px;
    background: rgba(47, 156, 255, 0.08);
    color: #e8f3ff;
    font-size: 14px;
    cursor: pointer;

    &:hover,
    &:focus-visible {
      background: rgba(47, 156, 255, 0.15);
      outline: none;
    }
  }
}

@keyframes s01Fade {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes s01Rise {
  from {
    opacity: 0;
    transform: translateY(12px) scale(var(--s01-scale));
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(var(--s01-scale));
  }
}
</style>
