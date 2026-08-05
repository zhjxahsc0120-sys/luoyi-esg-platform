<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { X } from 'lucide-vue-next'
import { getClassBMatterDemo } from '@/data/class-b-matters.mock'
import type { MatterDetail, MatterListRow, MatterModuleDemo } from '@/types/matter'

const props = defineProps<{
  moduleKey: string
  /** Optional API/home overlay for top stats (e.g. S01 continuous days) */
  statsOverride?: Array<{ label: string; value: string | number; unit?: string }>
}>()

const emit = defineEmits<{
  close: []
}>()

const demo = ref<MatterModuleDemo | null>(null)
const selectedId = ref<string | null>(null)
const modalRef = ref<HTMLDivElement | null>(null)

const rows = computed(() => demo.value?.rows || [])
const selected = computed<MatterListRow | null>(() => {
  if (!selectedId.value) return rows.value[0] || null
  return rows.value.find((r) => r.id === selectedId.value) || rows.value[0] || null
})
const detail = computed<MatterDetail | null>(() => selected.value?.detail || null)
const stats = computed(() => props.statsOverride?.length ? props.statsOverride : (demo.value?.stats || []))
const themeClass = computed(() => `theme-${demo.value?.theme || 'blue'}`)

function selectRow(row: MatterListRow) {
  selectedId.value = row.id
}

function handleOverlayClick(e: MouseEvent) {
  if (e.target === e.currentTarget) emit('close')
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

watch(
  () => props.moduleKey,
  (key) => {
    demo.value = getClassBMatterDemo(key)
    selectedId.value = demo.value?.rows[0]?.id || null
  },
  { immediate: true },
)

onMounted(() => {
  window.addEventListener('keydown', onKey)
  modalRef.value?.focus()
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKey)
})
</script>

<template>
  <div class="matter-overlay" @click="handleOverlayClick">
    <div
      ref="modalRef"
      class="matter-modal"
      :class="themeClass"
      role="dialog"
      aria-modal="true"
      tabindex="-1"
    >
      <header class="matter-head">
        <div>
          <h2>{{ demo?.title || moduleKey }}</h2>
          <p v-if="demo?.hint" class="matter-hint">{{ demo.hint }}</p>
        </div>
        <button type="button" class="matter-close" aria-label="关闭" @click="emit('close')">
          <X :size="18" />
        </button>
      </header>

      <section v-if="stats.length" class="matter-stats" aria-label="业务统计">
        <div v-for="s in stats" :key="s.label" class="matter-stats__cell">
          <span>{{ s.label }}</span>
          <strong>{{ s.value }}<em v-if="s.unit">{{ s.unit }}</em></strong>
        </div>
      </section>

      <div class="matter-body">
        <section class="matter-list-pane" aria-label="业务事项列表">
          <h3>业务事项列表</h3>
          <div class="matter-table-wrap">
            <table>
              <thead>
                <tr>
                  <th
                    v-for="col in demo?.columns || []"
                    :key="col.key"
                    :style="col.width ? { width: col.width } : undefined"
                  >
                    {{ col.label }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in rows"
                  :key="row.id"
                  :class="{ active: selected?.id === row.id }"
                  @click="selectRow(row)"
                >
                  <td v-for="col in demo?.columns || []" :key="col.key">
                    {{ row.cells[col.key] || '—' }}
                  </td>
                </tr>
              </tbody>
            </table>
            <p v-if="!rows.length" class="matter-empty">暂无事项 Demo 数据</p>
          </div>
        </section>

        <section v-if="detail" class="matter-detail-pane" aria-label="事项详情">
          <h3>{{ detail.title }}</h3>

          <div class="matter-section">
            <h4>基础信息</h4>
            <dl>
              <div v-for="f in detail.basic" :key="f.label">
                <dt>{{ f.label }}</dt>
                <dd>{{ f.value }}</dd>
              </div>
            </dl>
          </div>

          <div class="matter-section">
            <h4>业务状态</h4>
            <dl>
              <div v-for="f in detail.businessStatus" :key="f.label">
                <dt>{{ f.label }}</dt>
                <dd>{{ f.value }}</dd>
              </div>
            </dl>
          </div>

          <div class="matter-section">
            <h4>关键指标</h4>
            <dl>
              <div v-for="f in detail.keyMetrics" :key="f.label">
                <dt>{{ f.label }}</dt>
                <dd>{{ f.value }}</dd>
              </div>
            </dl>
          </div>

          <div class="matter-section">
            <h4>关联资料</h4>
            <ul v-if="detail.relatedDocs.length">
              <li v-for="(d, i) in detail.relatedDocs" :key="i">
                <b>{{ d.name }}</b>
                <span>{{ d.kind }}</span>
                <em>{{ d.status }}</em>
              </li>
            </ul>
            <p v-else class="matter-empty">暂无关联资料</p>
          </div>

          <div class="matter-section">
            <h4>操作记录</h4>
            <ul v-if="detail.operationLogs.length" class="matter-logs">
              <li v-for="(log, i) in detail.operationLogs" :key="i">
                <time>{{ log.at }}</time>
                <b>{{ log.action }}</b>
                <span>{{ log.operator }}</span>
                <em>{{ log.remark }}</em>
              </li>
            </ul>
            <p v-else class="matter-empty">暂无操作记录</p>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.matter-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(2, 12, 24, 0.72);
  padding: 24px;
}
.matter-modal {
  width: min(1280px, 96vw);
  height: min(860px, 92vh);
  display: flex;
  flex-direction: column;
  border-radius: 10px;
  border: 1px solid rgba(47, 156, 255, 0.35);
  background: linear-gradient(180deg, rgba(8, 32, 56, 0.98), rgba(4, 20, 38, 0.98));
  color: #d7e6f5;
  overflow: hidden;
  &.theme-purple {
    border-color: rgba(166, 108, 255, 0.4);
  }
}
.matter-head {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 20px 10px;
  h2 { margin: 0; font-size: 22px; color: #f3f8ff; }
}
.matter-hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: #8ba6c3;
}
.matter-close {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(8, 40, 69, 0.7);
  color: #f3f8ff;
  border-radius: 6px;
  cursor: pointer;
}
.matter-stats {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  padding: 0 20px 12px;
}
.matter-stats__cell {
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(8, 40, 69, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.08);
  span { display: block; font-size: 12px; color: #8ba6c3; margin-bottom: 4px; }
  strong {
    font-size: 22px;
    color: #2f9cff;
    em { font-style: normal; font-size: 12px; margin-left: 4px; color: #8ba6c3; }
  }
}
.theme-purple .matter-stats__cell strong { color: #c4a3ff; }
.matter-body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 12px;
  padding: 0 20px 18px;
}
.matter-list-pane,
.matter-detail-pane {
  min-height: 0;
  overflow: auto;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  background: rgba(6, 28, 48, 0.55);
  padding: 12px 14px;
  h3 {
    margin: 0 0 10px;
    font-size: 15px;
    color: #f3f8ff;
  }
}
.matter-table-wrap {
  overflow: auto;
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 13px;
  }
  th, td {
    padding: 8px 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    text-align: left;
  }
  th { color: #8ba6c3; font-weight: 600; }
  tr {
    cursor: pointer;
    &:hover td { background: rgba(47, 156, 255, 0.08); }
    &.active td { background: rgba(47, 156, 255, 0.16); }
  }
}
.theme-purple .matter-table-wrap tr {
  &:hover td { background: rgba(166, 108, 255, 0.1); }
  &.active td { background: rgba(166, 108, 255, 0.18); }
}
.matter-section {
  margin-bottom: 14px;
  h4 {
    margin: 0 0 8px;
    font-size: 13px;
    color: #9ec5ef;
    border-left: 3px solid #2f9cff;
    padding-left: 8px;
  }
  dl {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px 10px;
    margin: 0;
  }
  dt { font-size: 11px; color: #8ba6c3; }
  dd { margin: 0; font-size: 13px; color: #e8f3ff; }
  ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  li {
    display: grid;
    grid-template-columns: 1.2fr 0.6fr 0.6fr;
    gap: 8px;
    padding: 8px 10px;
    border-radius: 6px;
    background: rgba(8, 40, 69, 0.5);
    font-size: 12px;
    b { color: #f3f8ff; }
    span, em { color: #8ba6c3; font-style: normal; }
  }
}
.theme-purple .matter-section h4 { border-left-color: #a66cff; color: #d7c4ff; }
.matter-logs li {
  grid-template-columns: 0.9fr 0.8fr 0.7fr 1.2fr !important;
}
.matter-empty {
  margin: 12px 0;
  color: #8ba6c3;
  font-size: 13px;
}
</style>
