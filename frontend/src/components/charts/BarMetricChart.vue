<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  data: { label: string; value: number }[]
}>()

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

function initChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  updateOption()
  window.addEventListener('resize', onResize)
}

function updateOption() {
  if (!chart) return
  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { top: 8, right: 44, bottom: 8, left: 4, containLabel: true },
    xAxis: {
      type: 'value',
      show: false,
      max: Math.max(...props.data.map((d) => d.value), 1) * 1.15,
    },
    yAxis: {
      type: 'category',
      data: props.data.map((d) => d.label),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: '#8fa9c8',
        fontSize: 12,
        margin: 10,
        interval: 0,
        overflow: 'truncate',
        width: 108,
      },
    },
    series: [
      {
        type: 'bar',
        data: props.data.map((d) => d.value),
        barWidth: 14,
        barCategoryGap: '42%',
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: 'rgba(47, 156, 255, 0.3)' },
            { offset: 1, color: '#2f9cff' },
          ]),
          borderRadius: [0, 5, 5, 0],
        },
        label: {
          show: true,
          position: 'right',
          formatter: '{c} 项',
          color: '#e8f3ff',
          fontSize: 12,
          distance: 6,
        },
      },
    ],
  })
}

function onResize() {
  chart?.resize()
}

onMounted(initChart)
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
})

watch(() => props.data, updateOption, { deep: true })
</script>

<template>
  <div ref="chartRef" class="chart-container" />
</template>
