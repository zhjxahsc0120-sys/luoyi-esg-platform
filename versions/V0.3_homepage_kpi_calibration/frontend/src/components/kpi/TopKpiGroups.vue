<script setup lang="ts">
import { computed } from 'vue'
import { useDashboardStore } from '@/stores/dashboard.store'
import KpiGroupPanel from './KpiGroupPanel.vue'

const props = defineProps<{
  /** 仅渲染指定组；默认全部 */
  groupKeys?: string[]
}>()

const store = useDashboardStore()

const emit = defineEmits<{
  (e: 'select', key: string): void
}>()

const groups = computed(() => {
  const all = store.kpis
  if (!props.groupKeys?.length) return all
  return all.filter((group) => props.groupKeys!.includes(group.key))
})

function handleSelect(key: string) {
  emit('select', key)
}
</script>

<template>
  <div class="kpi-groups" :class="{ 'kpi-groups--compact': groupKeys?.length === 2 }">
    <KpiGroupPanel
      v-for="group in groups"
      :key="group.key"
      :group="group"
      @select="handleSelect"
    />
  </div>
</template>
