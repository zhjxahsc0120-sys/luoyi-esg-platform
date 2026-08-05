<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import HeaderNav from '@/components/layout/HeaderNav.vue'
import WorkspaceNav from '@/components/workspace/WorkspaceNav.vue'
import WorkspaceHome from '@/components/workspace/WorkspaceHome.vue'
import WorkspaceTasks from '@/components/workspace/WorkspaceTasks.vue'
import WorkspaceSmartEntry from '@/components/workspace/WorkspaceSmartEntry.vue'
import WorkspaceReview from '@/components/workspace/WorkspaceReview.vue'
import WorkspaceDocuments from '@/components/workspace/WorkspaceDocuments.vue'
import TaskModal from '@/components/workspace/TaskModal.vue'
import { uploadTasks } from '@/data/workspace.mock'
import type { UploadTask } from '@/types/workspace'
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

const activeNav = ref('smart-upload')
const selectedStatus = ref('')
const selectedTaskId = ref<string | null>(null)
const forceTab = ref<string>('')

// 从 URL query ?t= 同步初始 Tab
function syncTabFromQuery() {
  const t = route.query.t as string | undefined
  if (t && ['workspace', 'tasks', 'smart-upload', 'review', 'documents'].includes(t)) {
    activeNav.value = t
  }
}

syncTabFromQuery()

const currentTask = computed(() => {
  if (!selectedTaskId.value) return null
  return uploadTasks.find(t => t.id === selectedTaskId.value) || {
    id: selectedTaskId.value,
    name: '任务办理',
    module: 'E',
    moduleName: '环境环保',
    deadline: '',
    deadlineDisplay: '',
    progressCurrent: 0,
    progressTotal: 1,
    status: '待上传',
    nextStep: '开始办理',
  } as UploadTask
})

function handleNavigate(key: string, status?: string) {
  activeNav.value = key
  if (status) {
    selectedStatus.value = status
  } else {
    selectedStatus.value = ''
  }
  // 同步 ?t= 深链
  router.replace({ query: { t: key } })
}

function handleOpenTask(taskId: string, tab?: string) {
  selectedTaskId.value = taskId
  forceTab.value = tab || ''
}

function handleCloseModal() {
  selectedTaskId.value = null
  forceTab.value = ''
}

function handlePlatformNav(key: string) {
  if (key === 'dashboard') {
    router.push('/')
  } else if (key === 'assistant') {
    router.push('/assistant')
  } else if (key === 'workspace') {
    // already here
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
      <div class="workspace-page">
        <!-- 与 Dashboard/Assistant 同壳：1920×1080 + scale，HeaderNav 像素级一致 -->
        <div class="workspace-header-nav">
          <HeaderNav active-key="workspace" @navigate="handlePlatformNav" />
        </div>

        <!-- 二级导航：本轮隐藏，不保留高度和空白占位 -->
        <WorkspaceNav v-if="activeNav !== 'smart-upload'" :active-nav="activeNav" @navigate="handleNavigate" />

        <main class="workspace-main">
          <WorkspaceHome
            v-if="activeNav === 'workspace'"
            @navigate="handleNavigate"
            @open-task="handleOpenTask"
          />
          <WorkspaceTasks
            v-else-if="activeNav === 'tasks'"
            :initial-status="selectedStatus"
            @open-task="handleOpenTask"
          />
          <WorkspaceSmartEntry
            v-else-if="activeNav === 'smart-upload'"
          />
          <WorkspaceReview
            v-else-if="activeNav === 'review'"
            @open-task="handleOpenTask"
          />
          <WorkspaceDocuments
            v-else-if="activeNav === 'documents'"
          />
        </main>

        <TaskModal
          v-if="currentTask"
          :task="currentTask"
          :force-tab="forceTab"
          @close="handleCloseModal"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.screen-wrapper {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  /* 避免聚焦底部操作按钮时浏览器程序性滚动画布，保持标题与流程条稳定 */
  overflow: clip;
  background: #020b18;
}

.screen-canvas {
  width: 1920px;
  height: 1080px;
  transform-origin: top left;
  will-change: transform;
}

.workspace-page {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  /* 与 .dashboard-page / .assistant-page 同壳：顶栏外 padding + 与下方内容间距 */
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
