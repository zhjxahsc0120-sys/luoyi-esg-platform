<script setup lang="ts">
import { computed } from 'vue'
import PanelCard from '@/components/layout/PanelCard.vue'
import ProgressRing from '@/components/charts/ProgressRing.vue'
import { useDashboardStore } from '@/stores/dashboard.store'
import type { MonthlyReadinessStatus } from '@/types/monthly-report'
import { FileText } from 'lucide-vue-next'

const store = useDashboardStore()

const readiness = computed(() => store.monthlyReadiness)

const safeProgress = computed(() => {
  if (readiness.value.denominator === 0 || !Number.isFinite(readiness.value.progress)) return 0
  return Math.min(100, Math.max(0, readiness.value.progress))
})

const reportName = computed(() => {
  const value = readiness.value.reportPeriod
  const match = /^(\d{4})-(0[1-9]|1[0-2])$/.exec(value)
  return match ? `${match[1]}年${Number(match[2])}月月报` : value
})

const deadlineRange = computed(() => (
  `${formatDeadline(readiness.value.deadlineStart)}—${formatDeadline(readiness.value.deadlineEnd)}`
))

function formatDeadline(value: string) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
  if (!match) return value

  const year = Number(match[1])
  const month = Number(match[2])
  const day = Number(match[3])
  const date = new Date(year, month - 1, day)
  if (
    date.getFullYear() !== year
    || date.getMonth() !== month - 1
    || date.getDate() !== day
  ) return value

  return `${month}月${day}日`
}

function statusClass(status: MonthlyReadinessStatus) {
  return {
    待提交: 'status-pending',
    待确认: 'status-confirm',
    待补正: 'status-correction',
    校验通过: 'status-passed',
    '不适用（已确认）': 'status-na',
  }[status]
}
</script>

<template>
  <PanelCard title="月报准备与输出" :icon="FileText">
    <div class="monthly-report-panel monthly-readiness-grid">
      <section class="monthly-subpanel readiness-overview">
        <div class="report-name">{{ reportName }}</div>
        <div class="rate-label">资料归集率</div>
        <ProgressRing :progress="safeProgress" :size="80" :stroke-width="5" color="#8b5cf6" />
        <div class="gathered-count">
          已归集<strong>{{ readiness.numerator }} / {{ readiness.denominator }}</strong>项
        </div>
        <div class="status-summary">
          <span class="summary-status summary-pending">
            <i class="status-dot" />待提交 <strong>{{ readiness.statusCounts['待提交'] }}</strong>
          </span>
          <span class="summary-status summary-confirm">
            <i class="status-dot" />待确认 <strong>{{ readiness.statusCounts['待确认'] }}</strong>
          </span>
          <span class="summary-status summary-correction">
            <i class="status-dot" />待补正 <strong>{{ readiness.statusCounts['待补正'] }}</strong>
          </span>
        </div>
        <div class="deadline-range">各任务截止：{{ deadlineRange }}</div>
      </section>

      <section class="monthly-subpanel exception-panel">
        <div class="monthly-subtitle">待处理资料（{{ readiness.exceptionTasks.length }}）</div>
        <template v-if="readiness.exceptionTasks.length">
          <div class="task-columns" aria-hidden="true">
            <span>资料任务</span>
            <span>状态</span>
            <span>截止日</span>
          </div>
          <div class="exception-list">
            <article
              v-for="task in readiness.exceptionTasks"
              :key="task.taskCode"
              class="exception-item"
              :title="`${task.taskCode} ${task.taskName}`"
            >
              <div class="task-info">
                <span class="task-name">{{ task.taskName }}</span>
                <span class="responsible-unit">{{ task.responsibleUnit }}</span>
              </div>
              <span class="status-badge" :class="statusClass(task.monthlyStatus)">
                {{ task.monthlyStatus }}
              </span>
              <span class="task-deadline">{{ formatDeadline(task.deadline) }}</span>
            </article>
          </div>
        </template>
        <div v-else class="all-passed">本期资料已全部校验通过</div>
      </section>
    </div>
  </PanelCard>
</template>

<style scoped lang="scss">
.monthly-report-panel.monthly-readiness-grid {
  flex: 1;
  display: grid;
  grid-template-columns: minmax(0, 40fr) minmax(0, 60fr);
  gap: 8px;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
}

.monthly-subpanel {
  min-width: 0;
  min-height: 0;
  height: 100%;
  padding: 6px;
  overflow: hidden;
  background: var(--bg-card);
  border: 1px solid var(--border-blue-dim);
  border-radius: 6px;
}

.monthly-subtitle {
  height: 20px;
  margin-bottom: 2px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  line-height: 20px;
}

.readiness-overview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
}

.report-name {
  color: var(--text-main);
  font-size: 15px;
  font-weight: 600;
  line-height: 20px;
  text-align: center;
}

.rate-label {
  color: var(--text-tertiary);
  font-size: 11px;
  font-weight: 400;
  line-height: 15px;
  text-align: center;
}

.readiness-overview :deep(.progress-ring) {
  flex-shrink: 0;
}

.readiness-overview :deep(.progress-ring circle) {
  transition: none !important;
}

.readiness-overview :deep(.progress-text) {
  font-size: 20px;
}

.gathered-count {
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 17px;
}

.gathered-count strong {
  color: #fff;
  font-weight: 600;
}

.status-summary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 11px;
  line-height: 16px;
  white-space: nowrap;
}

.summary-status {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 0 4px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.035);
}

.summary-status strong {
  color: inherit;
  font-weight: 600;
}

.status-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

.summary-pending { color: var(--orange); }
.summary-confirm { color: var(--blue); }
.summary-correction { color: var(--red); }

.deadline-range {
  color: var(--text-tertiary);
  font-size: 11px;
  line-height: 16px;
  text-align: center;
  white-space: nowrap;
}

.exception-panel {
  display: flex;
  flex-direction: column;
}

.task-columns,
.exception-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 58px 48px;
  column-gap: 6px;
  min-width: 0;
}

.task-columns {
  height: 15px;
  color: var(--text-disabled);
  font-size: 11px;
  line-height: 15px;
}

.task-columns span:nth-child(2) {
  text-align: center;
}

.task-columns span:nth-child(3) {
  text-align: right;
}

.exception-list {
  flex: 1;
  display: grid;
  grid-template-rows: repeat(4, minmax(0, 1fr));
  gap: 4px;
  min-width: 0;
  min-height: 0;
}

.exception-item {
  align-items: center;
  min-width: 0;
  min-height: 0;
  padding: 2px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.exception-item:last-child {
  border-bottom: 0;
}

.task-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-width: 0;
}

.task-name {
  min-width: 0;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 500;
  line-height: 16px;
  white-space: normal;
  overflow-wrap: break-word;
}

.status-badge {
  box-sizing: border-box;
  min-width: 46px;
  justify-self: center;
  padding: 0 5px;
  border: 1px solid currentColor;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 600;
  line-height: 15px;
  text-align: center;
  white-space: nowrap;
}

.status-pending { color: var(--orange); }
.status-confirm { color: var(--blue); }
.status-correction { color: var(--red); }
.status-passed { color: var(--green); }
.status-na { color: var(--text-disabled); }

.task-deadline {
  color: var(--text-tertiary);
  font-size: 11px;
  line-height: 16px;
  text-align: right;
  white-space: nowrap;
}

.responsible-unit {
  min-width: 0;
  margin-top: 1px;
  color: var(--text-secondary);
  font-size: 11px;
  line-height: 15px;
  white-space: nowrap;
}

.all-passed {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--green);
  font-size: 13px;
  text-align: center;
}
</style>
