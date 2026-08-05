<script setup lang="ts">
import { Building2, CalendarClock, Clock3, ShieldCheck } from 'lucide-vue-next'
</script>

<template>
  <section class="project-status-bar" aria-label="项目状态">
    <div class="status-item">
      <Building2 class="status-icon" aria-hidden="true" />
      <span class="status-label">项目名称</span>
      <strong>罗宜高速</strong>
    </div>
    <div class="status-item">
      <CalendarClock class="status-icon" aria-hidden="true" />
      <span class="status-label">当前阶段</span>
      <strong>路基与桥涵主体施工</strong>
    </div>
    <div class="status-item">
      <ShieldCheck class="status-icon" aria-hidden="true" />
      <span class="status-label">综合状态</span>
      <strong class="status-ok">总体可控</strong>
    </div>
    <div class="status-item status-time">
      <Clock3 class="status-icon" aria-hidden="true" />
      <span class="status-label">数据更新时间</span>
      <strong>2026-07-13 10:30</strong>
    </div>
  </section>
</template>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.project-status-bar {
  height: 100%;
  display: grid;
  grid-template-columns: 1fr 1.35fr 1fr 1.25fr;
  align-items: center;
  min-width: 0;
  padding: 0 12px;
  border: 1px solid var(--line-base);
  border-radius: var(--radius-sm);
  background: rgba(5, 22, 40, 0.76);
  box-shadow: inset 0 0 var(--space-20) rgba(33, 214, 255, 0.035);
}

.status-item {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: var(--space-8);
  color: var(--text-secondary);
  font-size: var(--fs-status);
  white-space: nowrap;
}

.status-item + .status-item {
  border-left: 1px solid var(--line-soft);
  padding-left: 14px;
}

.status-icon {
  width: var(--icon-sm);
  height: var(--icon-sm);
  flex: none;
  color: var(--cyan);
}

.status-label::after { content: '：'; }

strong {
  overflow: hidden;
  color: var(--text-primary);
  font-weight: 600;
  text-overflow: ellipsis;
}

.status-ok {
  color: var(--green);
  text-shadow: none;
}

.status-time { justify-content: flex-end; }

@media (max-height: 900px), (max-width: 1680px) {
  .project-status-bar { padding-inline: 8px; }
  .status-item { gap: 5px; font-size: 13px; }
  .status-item + .status-item { padding-left: 8px; }
  .status-icon { width: 14px; height: 14px; }
}
</style>
