<script setup lang="ts">
import { computed } from 'vue'
import type { KpiGroup } from '@/types/dashboard'
import KpiCard from './KpiCard.vue'
import { Leaf, Users, ShieldCheck } from 'lucide-vue-next'

const props = defineProps<{
  group: KpiGroup
}>()

const emit = defineEmits<{
  (e: 'select', key: string): void
}>()

const icons: Record<string, object> = {
  E: Leaf,
  S: Users,
  G: ShieldCheck,
}

const themeColor = computed(() => {
  const map: Record<string, string> = {
    green: '#69e36f',
    blue: '#2f9cff',
    purple: '#a66cff',
  }
  return map[props.group.theme]
})

function handleSelect(key: string) {
  emit('select', key)
}
</script>

<template>
  <div class="kpi-group-panel" :class="`theme-${group.theme}`">
    <div class="kpi-group-header">
      <div class="kpi-group-title" :style="{ color: themeColor }">
        <component :is="icons[group.key]" class="kpi-group-icon" />
        <span>{{ group.key }}</span>
        <span>{{ group.title }}</span>
      </div>
      <div class="kpi-group-status">{{ group.status }}</div>
    </div>
    <div
      class="kpi-items"
      :style="{ '--kpi-item-cols': String(Math.max(group.items.length, 1)) }"
    >
      <KpiCard v-for="item in group.items" :key="item.key" :item="item" :theme="group.theme" @select="handleSelect" />
    </div>
  </div>
</template>
