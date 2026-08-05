<script setup lang="ts">
import { ref } from 'vue'
import { masterNavItems } from '@/data/master.mock'

const activeKey = ref('dashboard')
</script>

<template>
  <header class="master-topbar">
    <h1 class="topbar-title">罗宜高速 <span class="title-esg">ESG</span> 数据平台</h1>
    <nav class="topbar-nav">
      <button
        v-for="item in masterNavItems"
        :key="item.key"
        type="button"
        class="nav-item"
        :class="{ active: activeKey === item.key }"
        @click="activeKey = item.key"
      >
        {{ item.label }}
      </button>
    </nav>
  </header>
</template>
