<script setup lang="ts">
import { computed } from 'vue'
import { masterKpiGroups } from '@/data/master.mock'
import { KPI_HOME_HIDDEN_KEYS } from '@/data/kpi-catalog'
import MasterKpiGroupCard from './MasterKpiGroupCard.vue'

const props = defineProps<{
  groupKeys?: string[]
}>()

const groups = computed(() => {
  const base =
    !props.groupKeys || props.groupKeys.length === 0
      ? masterKpiGroups
      : masterKpiGroups.filter((g) => props.groupKeys!.includes(g.key))
  return base.map((g) => ({
    ...g,
    items: g.items.filter((item) => !KPI_HOME_HIDDEN_KEYS.has(item.key as never)),
  }))
})
</script>

<template>
  <div class="master-kpi-groups">
    <MasterKpiGroupCard
      v-for="group in groups"
      :key="group.key"
      :group="group"
    />
  </div>
</template>
