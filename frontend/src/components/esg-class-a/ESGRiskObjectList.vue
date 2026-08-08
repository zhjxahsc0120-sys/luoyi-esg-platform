<script setup lang="ts">
import type { EsgObjectFilter, EsgRiskObjectCard } from '@/types/esg-class-a'

defineProps<{
  items: EsgRiskObjectCard[]
  filter: EsgObjectFilter
  selectedId: number | null
  loading?: boolean
  emptyLabel?: string
}>()

const emit = defineEmits<{
  'update:filter': [filter: EsgObjectFilter]
  select: [item: EsgRiskObjectCard]
}>()

const filters: { key: EsgObjectFilter; label: string }[] = [
  { key: 'risk', label: '异常' },
  { key: 'all', label: '全部' },
  { key: 'normal', label: '正常' },
]

const dotClass: Record<string, string> = {
  danger: 'dot-danger',
  warning: 'dot-warning',
  normal: 'dot-normal',
  info: 'dot-info',
}
</script>

<template>
  <section class="risk-object-list">
    <div class="filter-row" role="tablist" aria-label="风险筛选">
      <button
        v-for="tab in filters"
        :key="tab.key"
        type="button"
        role="tab"
        class="filter-btn"
        :class="{ active: filter === tab.key }"
        :aria-selected="filter === tab.key"
        @click="emit('update:filter', tab.key)"
      >
        {{ tab.label }}
      </button>
    </div>

    <div v-if="loading" class="empty">加载中…</div>
    <div v-else-if="!items.length" class="empty">
      <strong>{{ emptyLabel || '当前筛选暂无监测点' }}</strong>
      <span v-if="filter === 'risk'">当前监测范围内没有需要优先处置的对象</span>
    </div>
    <ul v-else class="list">
      <li
        v-for="item in items"
        :key="item.id"
        class="card"
        :class="{ active: selectedId === item.id }"
        role="button"
        tabindex="0"
        @click="emit('select', item)"
        @keydown.enter="emit('select', item)"
      >
        <div class="card-head">
          <span class="dot" :class="dotClass[item.statusLevel]" />
          <span class="code">{{ item.code }}</span>
          <span class="status" :class="dotClass[item.statusLevel]">{{ item.statusLabel }}</span>
        </div>
        <div class="name">{{ item.name }}</div>
        <div class="meta location">{{ item.locationText }}</div>
        <div class="card-foot">
          <span>{{ item.latestResult || '暂无结果' }}{{ item.latestUnit ? ` ${item.latestUnit}` : '' }}</span>
          <span class="trend">↗ {{ item.trendLabel || '趋势' }}</span>
        </div>
      </li>
    </ul>
  </section>
</template>

<style scoped lang="scss">
.risk-object-list {
  display: flex;
  flex-direction: column;
  min-height: 0;
  flex: 1;
}

.filter-row {
  flex-shrink: 0;
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.filter-btn {
  flex: 1;
  height: 34px;
  border-radius: 6px;
  border: 1px solid rgba(105, 227, 111, 0.28);
  background: rgba(8, 40, 69, 0.5);
  color: #c5d8ef;
  font-size: 16px;
  cursor: pointer;

  &.active {
    color: #f3f8ff;
    border-color: rgba(105, 227, 111, 0.65);
    background: rgba(105, 227, 111, 0.16);
  }
}

.list {
  flex: 1;
  min-height: 0;
  margin: 0;
  padding: 0;
  list-style: none;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid rgba(105, 227, 111, 0.2);
  background: rgba(8, 40, 69, 0.45);
  cursor: pointer;

  &:hover,
  &.active {
    border-color: rgba(105, 227, 111, 0.6);
    background: rgba(105, 227, 111, 0.1);
  }
}

.card-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.dot-normal { background: #69e36f; }
.dot-warning { background: #ffc857; }
.dot-danger { background: #ff5a7a; }
.dot-info { background: #2f9cff; }

.code {
  font-size: 16px;
  font-weight: 700;
  color: #e8f3ff;
}

.status {
  margin-left: auto;
  font-size: 14px;
  font-weight: 600;

  &.dot-normal { color: #69e36f; }
  &.dot-warning { color: #ffc857; }
  &.dot-danger { color: #ff7a96; }
}

.name {
  margin-top: 6px;
  font-size: 18px;
  font-weight: 600;
  color: #f3f8ff;
  line-height: 1.3;
}

.meta {
  margin-top: 4px;
  font-size: 14px;
  color: #8ba6c3;
}

.location {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-foot {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-top: 8px;
  color: #d7e6f5;
  font-size: 14px;

  .trend { color: #67b8ff; }
}

.empty {
  padding: 20px 8px;
  text-align: center;
  color: #8ba6c3;
  font-size: 16px;

  strong,
  span { display: block; }
  strong { color: #e8f3ff; font-size: 18px; }
  span { margin-top: 6px; font-size: 14px; }
}
</style>
