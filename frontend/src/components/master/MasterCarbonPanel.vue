<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { Leaf } from 'lucide-vue-next'
import { motionOff } from '@/composables/useMotionMode'
import {
  carbonMetrics,
  carbonSources,
  carbonMeasures,
} from '@/data/master.mock'

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const levelColor: Record<string, string> = {
  '高': 'var(--green)',
  '较高': 'var(--cyan)',
  '中': 'var(--orange)',
  '低': 'var(--text-muted)',
}

function initChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  updateOption()
}

function updateOption() {
  if (!chart) return
  chart.setOption({
    animation: !motionOff.value,
    tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
    legend: {
      orient: 'vertical',
      right: 2,
      top: 'center',
      textStyle: { color: '#8ba6c3', fontSize: 11 },
      itemWidth: 9,
      itemHeight: 9,
      itemGap: 6,
    },
    series: [
      {
        type: 'pie',
        radius: ['48%', '72%'],
        center: ['28%', '50%'],
        avoidLabelOverlap: false,
        label: { show: false },
        labelLine: { show: false },
        data: carbonSources.map((s) => ({
          name: s.name,
          value: s.value,
          itemStyle: { color: s.color },
        })),
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

watch(() => carbonSources, updateOption, { deep: true })
</script>

<template>
  <div class="master-panel carbon-panel">
    <div class="panel-header">
      <Leaf :size="16" style="color: var(--green)" />
      <span class="panel-title">碳足迹与低碳增益</span>
    </div>
    <div class="panel-body">
      <!-- 顶部 3 张度量卡 -->
      <div class="metric-cards metric-cards-3">
        <div v-for="m in carbonMetrics" :key="m.key" class="metric-card">
          <div class="metric-value-row">
            <span class="metric-value">{{ m.value }}</span>
            <span class="metric-unit">{{ m.unit }}</span>
          </div>
          <span class="metric-label">{{ m.label }}</span>
          <span v-if="m.note" class="metric-note">{{ m.note }}</span>
        </div>
      </div>
      <!-- 下部左右两区 -->
      <div class="carbon-lower">
        <!-- 左：碳足迹来源构成 -->
        <div class="carbon-left">
          <div class="sub-title">碳足迹来源构成</div>
          <div ref="chartRef" class="carbon-chart" />
        </div>
        <!-- 右：主要减排措施 -->
        <div class="carbon-right">
          <div class="sub-title">主要减排措施</div>
          <div class="measure-list">
            <div v-for="(m, i) in carbonMeasures" :key="i" class="measure-row">
              <div class="measure-info">
                <span class="measure-name">{{ m.name }}</span>
                <span class="measure-level" :style="{ color: levelColor[m.level] }">{{ m.level }}</span>
              </div>
              <div class="measure-track">
                <div class="measure-fill" :style="{ width: m.ratio + '%' }" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
