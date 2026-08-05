<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import * as echarts from 'echarts'
import { FileText } from 'lucide-vue-next'
import { motionOff } from '@/composables/useMotionMode'
import {
  monthlySummary,
  monthlyDocs,
} from '@/data/master.mock'

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const rate = computed(() => monthlySummary.completionRate)

function initChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  updateOption()
}

function updateOption() {
  if (!chart) return
  chart.setOption({
    animation: !motionOff.value,
    series: [
      {
        type: 'gauge',
        startAngle: 90,
        endAngle: -270,
        radius: '88%',
        pointer: { show: false },
        progress: {
          show: true,
          overlap: false,
          roundCap: true,
          clip: false,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
              { offset: 0, color: '#1687ff' },
              { offset: 1, color: '#25b9ff' },
            ]),
          },
        },
        axisLine: {
          lineStyle: {
            width: 8,
            color: [[1, 'rgba(73, 132, 178, 0.15)']],
          },
        },
        splitLine: { show: false },
        axisTick: { show: false },
        axisLabel: { show: false },
        data: [{ value: rate.value }],
        title: {
          show: true,
          offsetCenter: [0, '0%'],
          fontSize: 20,
          fontWeight: 700,
          color: '#f3f8ff',
          fontFamily: 'Bahnschrift, DIN Alternate, Arial Narrow, sans-serif',
          formatter: () => `${rate.value}%`,
        },
        detail: { show: false },
      },
    ],
  })
}

function onResize() {
  chart?.resize()
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', onResize)
})
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
})

watch(rate, updateOption)
</script>

<template>
  <div class="master-panel monthly-panel">
    <div class="panel-header">
      <FileText :size="16" style="color: var(--purple)" />
      <span class="panel-title">月报准备与输出</span>
    </div>
    <div class="panel-body">
      <div class="monthly-layout">
        <!-- 左侧 -->
        <div class="monthly-left">
          <div class="month-label">{{ monthlySummary.month }}</div>
          <div ref="chartRef" class="monthly-ring" />
          <div class="monthly-stats">
            <div class="stat-row">
              <span class="stat-label">待补资料</span>
              <span class="stat-val">{{ monthlySummary.pendingDocs }} 份</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">待确认</span>
              <span class="stat-val">{{ monthlySummary.pendingConfirm }} 项</span>
            </div>
          </div>
          <div class="monthly-footer">
            <div class="footer-row">
              <span class="footer-icon status-icon" />
              <span class="footer-label">状态</span>
              <span class="footer-val">{{ monthlySummary.status }}</span>
            </div>
            <div class="footer-row">
              <span class="footer-icon date-icon" />
              <span class="footer-label">预计完成</span>
              <span class="footer-val">{{ monthlySummary.expectedDate }}</span>
            </div>
          </div>
        </div>
        <!-- 右侧 -->
        <div class="monthly-right">
          <div class="sub-title">待补资料清单</div>
          <div class="doc-table">
            <div class="doc-thead">
              <span class="col-name">资料名称</span>
              <span class="col-dept">责任单位</span>
              <span class="col-deadline">截止</span>
            </div>
            <div
              v-for="(d, i) in monthlyDocs"
              :key="i"
              class="doc-row"
              :class="{ urgent: d.status === 'urgent' }"
            >
              <span class="col-name">{{ d.name }}</span>
              <span class="col-dept">{{ d.dept }}</span>
              <span class="col-deadline">{{ d.deadline }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
