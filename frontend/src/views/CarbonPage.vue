<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import HeaderNav from '@/components/layout/HeaderNav.vue'
import CarbonNav from '@/components/carbon/CarbonNav.vue'
import CarbonOverview from '@/components/carbon/CarbonOverview.vue'
import CarbonBoundary from '@/components/carbon/CarbonBoundary.vue'
import CarbonDetail from '@/components/carbon/CarbonDetail.vue'
import '@/styles/workspace.scss'

const SCREEN_WIDTH = 1920
const SCREEN_HEIGHT = 1080

const route = useRoute()
const router = useRouter()

const windowWidth = ref(SCREEN_WIDTH)
const windowHeight = ref(SCREEN_HEIGHT)

const scale = computed(() => {
  const scaleX = windowWidth.value / SCREEN_WIDTH
  const scaleY = windowHeight.value / SCREEN_HEIGHT
  return Math.min(scaleX, scaleY)
})

const translateX = computed(() => {
  const scaledWidth = SCREEN_WIDTH * scale.value
  return (windowWidth.value - scaledWidth) / 2
})

const translateY = computed(() => {
  const scaledHeight = SCREEN_HEIGHT * scale.value
  return (windowHeight.value - scaledHeight) / 2
})

function handleResize() {
  windowWidth.value = window.innerWidth
  windowHeight.value = window.innerHeight
}

const activeTab = ref('overview')

function syncTabFromQuery() {
  const t = route.query.t as string | undefined
  if (t && ['overview', 'boundary', 'detail'].includes(t)) {
    activeTab.value = t
  }
}

syncTabFromQuery()

function handleTabChange(key: string) {
  activeTab.value = key
  router.replace({ query: { t: key } })
}

function handlePlatformNav(key: string) {
  if (key === 'dashboard') {
    router.push('/')
  } else if (key === 'assistant') {
    router.push('/assistant')
  } else if (key === 'workspace') {
    router.push('/workspace')
  } else if (key === 'monthly-report') {
    router.push('/monthly-report')
  }
}

watch(() => route.query.t, () => {
  syncTabFromQuery()
})

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div class="screen-wrapper">
    <div
      class="screen-canvas"
      :style="{
        transform: `translate(${translateX}px, ${translateY}px) scale(${scale})`,
      }"
    >
      <div class="carbon-page workspace-page">
        <div class="workspace-header-nav">
          <HeaderNav active-key="carbon" @navigate="handlePlatformNav" />
        </div>

        <CarbonNav :active-tab="activeTab" @navigate="handleTabChange" />

        <main class="workspace-main">
          <CarbonOverview
            v-if="activeTab === 'overview'"
          />
          <CarbonBoundary
            v-else-if="activeTab === 'boundary'"
          />
          <CarbonDetail
            v-else-if="activeTab === 'detail'"
          />
        </main>
      </div>
    </div>
  </div>
</template>

<style scoped>
.screen-wrapper {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: #020b18;
}

.screen-canvas {
  width: 1920px;
  height: 1080px;
  transform-origin: top left;
  will-change: transform;
}

.carbon-page {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: var(--main-gap);
  gap: var(--main-gap);
  background: linear-gradient(180deg, #020b18 0%, #051a32 100%);
  overflow: hidden;
}

.workspace-header-nav {
  height: var(--dashboard-header-h, 80px);
  flex-shrink: 0;
}

.workspace-main {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
</style>
