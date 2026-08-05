<script setup lang="ts">
import type { MasterKpiGroup } from '@/data/master.mock'
import MasterKpiSubCard from './MasterKpiSubCard.vue'

defineProps<{
  group: MasterKpiGroup
}>()
</script>

<template>
  <div class="master-kpi-group" :class="`theme-${group.theme}`">
    <div class="group-header">
      <svg class="group-icon" :class="`theme-${group.theme}`" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <!-- E: leaf -->
        <template v-if="group.key === 'E'">
          <path d="M11 20A7 7 0 0 1 4 13C4 8 8 4 14 4h6v6c0 5-4 10-9 10z" />
          <path d="M4 20l7-7" />
        </template>
        <!-- S: people -->
        <template v-else-if="group.key === 'S'">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </template>
        <!-- G: shield-check -->
        <template v-else>
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          <path d="M9 12l2 2 4-4" />
        </template>
      </svg>
      <span class="group-letter" :class="`theme-${group.theme}`">{{ group.letter }}</span>
      <span class="group-title">{{ group.title }}</span>
    </div>
    <div class="group-items">
      <MasterKpiSubCard
        v-for="item in group.items"
        :key="item.key"
        :item="item"
        :theme="group.theme"
      />
    </div>
  </div>
</template>
