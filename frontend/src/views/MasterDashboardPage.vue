<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { initMotionMode, motionOff } from '@/composables/useMotionMode'
import MasterTopBar from '@/components/master/MasterTopBar.vue'
import MasterKpiSection from '@/components/master/MasterKpiSection.vue'
import MasterGisSection from '@/components/master/MasterGisSection.vue'
import MasterRightPanels from '@/components/master/MasterRightPanels.vue'
import MasterTimeline from '@/components/master/MasterTimeline.vue'

// 初始化动画模式（解析 ?motion=off / prefers-reduced-motion）
initMotionMode()

const SCREEN_WIDTH = 1920
const SCREEN_HEIGHT = 1080

const windowWidth = ref(SCREEN_WIDTH)
const windowHeight = ref(SCREEN_HEIGHT)

const scale = computed(() => {
  const sx = windowWidth.value / SCREEN_WIDTH
  const sy = windowHeight.value / SCREEN_HEIGHT
  return Math.min(sx, sy)
})
const translateX = computed(() => (windowWidth.value - SCREEN_WIDTH * scale.value) / 2)
const translateY = computed(() => (windowHeight.value - SCREEN_HEIGHT * scale.value) / 2)

function handleResize() {
  windowWidth.value = window.innerWidth
  windowHeight.value = window.innerHeight
}

onMounted(() => window.addEventListener('resize', handleResize))
onUnmounted(() => window.removeEventListener('resize', handleResize))
</script>

<template>
  <div class="master-screen" :class="{ 'motion-off': motionOff }">
    <div
      class="master-canvas"
      :style="{
        transform: `translate(${translateX}px, ${translateY}px) scale(${scale})`,
      }"
    >
      <div class="master-page">
        <!-- 顶部标题 + 导航（全宽） -->
        <div class="master-header">
          <MasterTopBar />
        </div>
        <!-- 主体：统一两列 66% / 34%，列间距 10px -->
        <div class="master-content">
          <!-- 左列 66%：KPI(E+S) + GIS + 时间轴 -->
          <div class="master-col-left">
            <div class="master-kpi-row">
              <MasterKpiSection :group-keys="['E', 'S']" />
            </div>
            <div class="master-gis">
              <MasterGisSection />
            </div>
            <div class="master-timeline">
              <MasterTimeline />
            </div>
          </div>
          <!-- 右列 34%：KPI(G) + 三个专题面板 -->
          <div class="master-col-right">
            <div class="master-kpi-row">
              <MasterKpiSection :group-keys="['G']" />
            </div>
            <div class="master-panels">
              <MasterRightPanels />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.master-screen {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at 18% 12%, rgba(0, 174, 255, 0.05) 0%, transparent 30%),
    radial-gradient(circle at 85% 88%, rgba(166, 108, 255, 0.04) 0%, transparent 30%),
    #020b18;
}
</style>
