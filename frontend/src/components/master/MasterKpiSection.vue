<script setup lang="ts">
import { computed } from 'vue'
import { masterKpiGroups } from '@/data/master.mock'
import MasterKpiGroupCard from './MasterKpiGroupCard.vue'

const props = defineProps<{
  groupKeys?: string[]
}>()

const groups = computed(() => {
  if (!props.groupKeys || props.groupKeys.length === 0) return masterKpiGroups
  return masterKpiGroups.filter(g => props.groupKeys!.includes(g.key))
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
