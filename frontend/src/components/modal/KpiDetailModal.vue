<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { X, AlertTriangle, ShieldCheck, FileCheck, Clock, MapPin } from 'lucide-vue-next'
import type {
  KpiDetailConfig,
  KpiDetailBottomItem,
  TopicTab,
  KpiModalFocusContext,
  E02DetailRow,
  E02MainStatus,
  E03DetailRow,
} from '@/types/dashboard'
import { carbonTabData, monthlyTabData } from '@/data/dashboard.mock'
import ClassBMatterModal from './ClassBMatterModal.vue'
import S02SafetyRiskModal from './S02SafetyRiskModal.vue'
// Legacy dedicated modals retained on disk; Class B V1.0 uses ClassBMatterModal shell.
// G03ContractorEvalModal / G03RectificationModal: legacy — do not bind on homepage.
import CarbonBenefitModal from './CarbonBenefitModal.vue'
import MonthlyReportModal from './MonthlyReportModal.vue'
import { parseFocusObjectId } from '@/utils/esg-demo'

const props = defineProps<{
  detail: KpiDetailConfig
  focusContext?: KpiModalFocusContext | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'retry'): void
}>()

/** Risk drill: kpiKey + objectId → focus row inside G dedicated modals. */
const focusObjectId = computed(() => parseFocusObjectId(props.focusContext?.sourceId))

const isAcceptanceMode = new URLSearchParams(window.location.search).get('acceptance') === '1'

const modalRef = ref<HTMLDivElement | null>(null)
const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const showSuperviseToast = ref(false)
const superviseToastMessage = ref('督办功能为原型预留，尚未接入业务流程')
let superviseTimer: ReturnType<typeof setTimeout> | null = null

const focusRowRef = ref<HTMLTableRowElement | null>(null)
const focusScrollDone = ref(false)

const themeColor = computed(() => {
  const map: Record<string, string> = {
    green: '#69e36f',
    blue: '#2f9cff',
    purple: '#a66cff',
  }
  return map[props.detail.theme]
})

// E01 筛选
const e01Filter = ref('all')
type E01Category = '扬尘' | '噪声' | '废水' | '地表水'
type E01Status = '复测达标' | '待复测' | '复测中' | '复测仍超标'
type E01DetailRow = KpiDetailBottomItem & {
  id: string | number
  category: E01Category
  status: E01Status
  point: string
  factor: string
  time: string
}

const e01StatusFilter = ref<E01Status | null>(null)
const e01SelectedId = ref<string | number | null>(null)
const e01Categories = [
  { key: 'all', label: '全部' },
  { key: 'wastewater', label: '废水' },
  { key: 'noise', label: '噪声' },
  { key: 'dust', label: '扬尘' },
  { key: 'surface', label: '地表水' },
]

// E01 月度数据（与总数对齐：7月合计2）
const e01TrendData = {
  months: ['2月', '3月', '4月', '5月', '6月', '7月'],
  all: [1, 3, 1, 2, 3, 2],
  dust: [1, 2, 1, 1, 2, 1],
  noise: [0, 1, 0, 1, 1, 1],
  wastewater: [0, 0, 0, 0, 0, 0],
  surface: [0, 0, 0, 0, 0, 0],
}

// E01 分类颜色映射
const e01CatColors: Record<string, string> = {
  dust: '#69e36f',
  noise: '#2f9cff',
  wastewater: '#a66cff',
  surface: '#00e5ff',
}

// E01 动态可用分类（过滤无数据类别）
const e01AvailableCategories = computed(() => {
  const available: typeof e01Categories = [{ key: 'all', label: '全部' }]
  e01Categories.forEach(cat => {
    if (cat.key === 'all') return
    const data = e01TrendData[cat.key as keyof typeof e01TrendData] as number[]
    if (data.some(v => Number(v) > 0)) {
      available.push(cat)
    }
  })
  return available
})

// E01 类别构成数据（优先使用 API categoryData）
const e01CompositionData = computed(() => {
  const apiCategoryData = props.detail.categoryData as { name: string; value: number }[] | undefined
  if (apiCategoryData && apiCategoryData.length > 0) {
    const catColorMap: Record<string, string> = {
      '扬尘': '#69e36f',
      '噪声': '#2f9cff',
      '废水': '#a66cff',
      '地表水': '#00e5ff',
      'dust': '#69e36f',
      'noise': '#2f9cff',
      'wastewater': '#a66cff',
      'surface': '#00e5ff',
    }
    return apiCategoryData
      .filter(cat => cat.name !== '合计')
      .map(cat => ({
        name: cat.name,
        value: cat.value,
        color: catColorMap[cat.name] || '#8fa9c8',
      }))
      .filter(cat => cat.value > 0)
  }
  const total = e01TrendData.all[e01TrendData.all.length - 1] || 0
  const items: Array<{ name: string; value: number; color: string }> = []
  e01Categories.forEach(cat => {
    if (cat.key === 'all') return
    const data = e01TrendData[cat.key as keyof typeof e01TrendData] as number[]
    const value = data[data.length - 1] || 0
    if (value > 0) {
      items.push({
        name: cat.label,
        value,
        color: e01CatColors[cat.key] || '#8fa9c8',
      })
    }
  })
  return items
})

// E01 是否有有效数据
const e01HasData = computed(() => {
  return e01AvailableCategories.value.length > 1 || e01TrendData.all.some(v => v > 0)
})

const e01DetailRows = computed(() => {
  if (props.detail.key !== 'E01') return []
  return props.detail.detailData as E01DetailRow[]
})

const e01CategoryByFilter: Record<string, E01Category | null> = {
  all: null,
  dust: '扬尘',
  noise: '噪声',
  wastewater: '废水',
  surface: '地表水',
}

const e01FilterByCategory: Record<E01Category, string> = {
  '扬尘': 'dust',
  '噪声': 'noise',
  '废水': 'wastewater',
  '地表水': 'surface',
}

const filteredE01DetailData = computed(() => {
  const category = e01CategoryByFilter[e01Filter.value]
  return e01DetailRows.value.filter(row =>
    (!category || row.category === category) &&
    (!e01StatusFilter.value || row.status === e01StatusFilter.value),
  )
})

const e01DetailFilterSummary = computed(() => {
  const categoryLabel = e01Filter.value === 'all'
    ? '全部'
    : (e01Categories.find(item => item.key === e01Filter.value)?.label ?? '全部')
  const filterLabel = e01StatusFilter.value
    ? (categoryLabel === '全部' ? e01StatusFilter.value : `${categoryLabel} / ${e01StatusFilter.value}`)
    : categoryLabel
  return `${filterLabel} · 共${filteredE01DetailData.value.length}条`
})

function isE01Actionable(row: E01DetailRow) {
  return row.status === '待复测' || row.status === '复测仍超标'
}

const e01SelectedRow = computed(() =>
  e01DetailRows.value.find(row => row.id === e01SelectedId.value) ?? null,
)

const e01CanSupervise = computed(() => Boolean(
  e01SelectedRow.value && isE01Actionable(e01SelectedRow.value),
))

const e01SuperviseTitle = computed(() => {
  const row = e01SelectedRow.value
  if (!row) return '请先选择待复测或复测仍超标记录'
  if (!isE01Actionable(row)) return '该记录已复测达标，无需督办'
  return `对${row.point.replace(/\s+/g, '')}${row.factor.replace(/^扬尘\//, '')}记录发起督办`
})

function toggleE01Selection(row: E01DetailRow) {
  if (!isE01Actionable(row)) return
  e01SelectedId.value = e01SelectedId.value === row.id ? null : row.id
}

function toggleE01StatusFilter(status: E01Status, count: number) {
  if (count <= 0) return
  e01StatusFilter.value = e01StatusFilter.value === status ? null : status
}

function handleE01Reminder() {
  const row = e01PendingReminder.value as E01DetailRow | null
  if (!row || !isE01Actionable(row)) return
  e01StatusFilter.value = null
  e01Filter.value = e01FilterByCategory[row.category]
  e01SelectedId.value = row.id
  nextTick(() => {
    const selectedRow = modalRef.value?.querySelector(`[data-e01-id="${String(row.id)}"]`)
    selectedRow?.scrollIntoView({ block: 'nearest' })
  })
}

function handleE01ModalKeydown(event: KeyboardEvent) {
  if (props.detail.key === 'E01' && event.key === 'Escape') {
    event.stopPropagation()
    emit('close')
  }
}

const e01Scale = ref(1)
const e02Scale = ref(1)
const e03Scale = ref(1)

function updateE01Scale() {
  if (props.detail.key !== 'E01') return
  e01Scale.value = Math.min(1, window.innerWidth / 1920, window.innerHeight / 1080)
}

function updateE02Scale() {
  if (props.detail.key !== 'E02') return
  e02Scale.value = Math.min(1, window.innerWidth / 1920, window.innerHeight / 1080)
}

function updateE03Scale() {
  if (props.detail.key !== 'E03') return
  e03Scale.value = Math.min(1, window.innerWidth / 1920, window.innerHeight / 1080)
}

function e01SummaryValue(label: string) {
  const item = props.detail.summary.find(summaryItem => summaryItem.label === label)
  return Number(item?.value ?? 0)
}

const e01MonthlyTotal = computed(() => e01SummaryValue('本月超标项次'))
const e01CompletedCount = computed(() => e01SummaryValue('已完成复测'))
const e01PendingCount = computed(() => e01SummaryValue('待复测'))
const e01StillExceededCount = computed(() => e01SummaryValue('复测仍超标'))
const e01CompletionRate = computed(() => {
  if (e01MonthlyTotal.value <= 0) return 0
  return Math.round((e01CompletedCount.value / e01MonthlyTotal.value) * 100)
})

const e01PendingReminder = computed(() => {
  if (props.detail.key !== 'E01') return null
  return props.detail.detailData.find(item => item.status === '待复测') ?? null
})

function summaryValueColor(item: KpiDetailConfig['summary'][number]) {
  if (props.detail.key === 'E01') {
    if (item.label === '待复测') return '#ffb347'
    if (item.label === '复测仍超标') return Number(item.value) > 0 ? '#ff4f5e' : '#69e36f'
    if (item.label === '已完成复测') return '#69e36f'
  }
  if (props.detail.key === 'E02' && item.label === '已逾期' && Number(item.value) > 0) return '#ff4f5e'
  return themeColor.value
}

function e01StatusClass(status: unknown) {
  const statusText = String(status ?? '')
  if (statusText === '复测达标') return 'tag-green'
  if (statusText === '待复测') return 'tag-orange'
  if (statusText === '复测中') return 'tag-blue'
  if (statusText === '复测仍超标') return 'tag-red'
  return 'tag-green'
}

// 监听可用分类变化，确保选中类别始终有效
watch(e01AvailableCategories, (newCats) => {
  const validKeys = newCats.map(c => c.key)
  if (!validKeys.includes(e01Filter.value)) {
    e01Filter.value = 'all'
  }
}, { immediate: true })

const allE02Items = computed<E02DetailRow[]>(() =>
  props.detail.key === 'E02' ? props.detail.detailData as E02DetailRow[] : [],
)

const e02StatusColors: Record<E02MainStatus, string> = {
  '整改中': '#2f9cff',
  '待复查': '#ffb347',
  '待销项': '#69e36f',
}

// E02权威状态构成优先使用接口statusData，仅在回退数据缺失时从明细补齐。
const e02StatusData = computed(() => {
  const apiData = props.detail.key === 'E02' ? props.detail.statusData : undefined
  const statuses: E02MainStatus[] = ['整改中', '待复查', '待销项']
  return statuses.map(name => ({
    name,
    value: Number(apiData?.find(item => item.name === name)?.value ?? allE02Items.value.filter(row => row.mainStatus === name).length),
    color: e02StatusColors[name],
  }))
})

const e02OverdueCount = computed(() => allE02Items.value.filter(row => row.overdue === true).length)

function e02SummaryValue(label: string, fallback: number) {
  return Number(props.detail.summary.find(item => item.label === label)?.value ?? fallback)
}

const e02SummaryCards = computed(() => [
  { label: '当前未闭环', value: e02SummaryValue('当前未闭环', allE02Items.value.length), unit: '项', kind: 'all' as const },
  { label: '整改中', value: e02SummaryValue('整改中', e02StatusData.value[0]?.value ?? 0), unit: '项', kind: 'main' as const, filterValue: '整改中' as E02MainStatus },
  { label: '待复查', value: e02SummaryValue('待复查', e02StatusData.value[1]?.value ?? 0), unit: '项', kind: 'main' as const, filterValue: '待复查' as E02MainStatus },
  { label: '待销项', value: e02SummaryValue('待销项', e02StatusData.value[2]?.value ?? 0), unit: '项', kind: 'main' as const, filterValue: '待销项' as E02MainStatus },
  { label: '已逾期', value: e02SummaryValue('已逾期', e02OverdueCount.value), unit: '项', kind: 'overdue' as const },
])

const mainStatusFilter = ref<E02MainStatus | null>(null)
const categoryFilter = ref<string | null>(null)
const overdueOnly = ref(false)
const e02SelectedId = ref<string | null>(null)

const e02HasFilters = computed(() => Boolean(mainStatusFilter.value || categoryFilter.value || overdueOnly.value))

const filteredE02Items = computed(() => allE02Items.value.filter(row =>
  (!mainStatusFilter.value || row.mainStatus === mainStatusFilter.value) &&
  (!categoryFilter.value || row.category === categoryFilter.value) &&
  (!overdueOnly.value || row.overdue === true),
))

// 类型列表不预先应用categoryFilter，保留同一主状态/逾期范围内的类型切换能力。
const e02TypeScopeItems = computed(() => allE02Items.value.filter(row =>
  (!mainStatusFilter.value || row.mainStatus === mainStatusFilter.value) &&
  (!overdueOnly.value || row.overdue === true),
))

function aggregateE02Items(items: E02DetailRow[], field: 'category' | 'department') {
  const counts = new Map<string, number>()
  items.forEach(row => {
    const key = row[field]
    if (key) counts.set(key, (counts.get(key) ?? 0) + 1)
  })
  return Array.from(counts, ([name, value]) => ({ name, value }))
}

const e02TypeData = computed(() => aggregateE02Items(e02TypeScopeItems.value, 'category'))

const e02DepartmentData = computed(() =>
  aggregateE02Items(filteredE02Items.value, 'department')
    .sort((a, b) => b.value - a.value || a.name.localeCompare(b.name, 'zh-CN')),
)

const e02OverdueReminder = computed(() => filteredE02Items.value.find(row => row.overdue === true) ?? null)

const e02FilterLabels = computed(() =>
  [mainStatusFilter.value, categoryFilter.value, overdueOnly.value ? '已逾期' : null].filter((value): value is string => Boolean(value)),
)

const e02FilterSummary = computed(() => {
  return `${e02FilterLabels.value.length > 0 ? e02FilterLabels.value.join(' / ') : '全部'} · 共${filteredE02Items.value.length}条`
})

const e02ActiveFilterText = computed(() => e02FilterLabels.value.join(' / '))

const e02HighlightedStatuses = computed(() => {
  if (!e02HasFilters.value) return new Set<E02MainStatus>(['整改中', '待复查', '待销项'])
  return new Set(filteredE02Items.value.map(row => row.mainStatus))
})

const e02SelectedRow = computed(() => allE02Items.value.find(row => row.id === e02SelectedId.value) ?? null)
const e02CanSupervise = computed(() => props.detail.key !== 'E02' || Boolean(e02SelectedRow.value))
const e02ActionTitle = computed(() => e02SelectedRow.value ? `已选择“${e02SelectedRow.value.name}”` : '请先选择未闭环事项')

function clearE02Filters() {
  mainStatusFilter.value = null
  categoryFilter.value = null
  overdueOnly.value = false
  e02SelectedId.value = null
}

function activateE02Summary(item: (typeof e02SummaryCards.value)[number]) {
  if (item.kind === 'all') {
    clearE02Filters()
  } else if (item.kind === 'main') {
    mainStatusFilter.value = mainStatusFilter.value === item.filterValue ? null : item.filterValue
  } else {
    overdueOnly.value = !overdueOnly.value
  }
}

function e02ToggleMainStatus(status: E02MainStatus) {
  mainStatusFilter.value = mainStatusFilter.value === status ? null : status
}

function e02ToggleCategory(category: string) {
  categoryFilter.value = categoryFilter.value === category ? null : category
}

function e02ToggleSelection(row: E02DetailRow) {
  e02SelectedId.value = e02SelectedId.value === row.id ? null : row.id
}

function e02MainStatusClass(status: E02MainStatus) {
  if (status === '整改中') return 'tag-blue'
  if (status === '待复查') return 'tag-orange'
  return 'tag-green'
}

function handleE02OverdueReminder() {
  const row = e02OverdueReminder.value
  if (!row) return
  overdueOnly.value = true
  e02SelectedId.value = row.id
  nextTick(() => modalRef.value?.querySelector(`[data-e02-id="${row.id}"]`)?.scrollIntoView({ block: 'nearest' }))
}

function isE02SummaryActive(item: (typeof e02SummaryCards.value)[number]) {
  if (item.kind === 'all') return !mainStatusFilter.value && !categoryFilter.value && !overdueOnly.value
  if (item.kind === 'main') return mainStatusFilter.value === item.filterValue
  return overdueOnly.value
}

watch(filteredE02Items, rows => {
  if (e02SelectedId.value && !rows.some(row => row.id === e02SelectedId.value)) e02SelectedId.value = null
})

// E04 行选择与督办
const e04SelectedRow = ref<number | null>(null)

function e04HandleRowClick(index: number) {
  e04SelectedRow.value = e04SelectedRow.value === index ? null : index
}

const e04CanSupervise = computed(() => {
  if (props.detail.key !== 'E04') return true
  if (e04SelectedRow.value === null) return false
  const item = props.detail.detailData[e04SelectedRow.value]
  return item && (item as any).attention !== '正常'
})

// E03 真实明细筛选、聚合与选择
type E03DeadlineFilter = 'normal' | 'overdue' | null

const allE03Items = computed<E03DetailRow[]>(() =>
  props.detail.key === 'E03' ? props.detail.detailData as E03DetailRow[] : [],
)
const e03DeadlineFilter = ref<E03DeadlineFilter>(null)
const e03SegmentFilter = ref<string | null>(null)
const e03CategoryFilter = ref<string | null>(null)
const e03SelectedId = ref<number | null>(null)

const e03Segments = computed(() =>
  Array.from(new Set(allE03Items.value.map(row => row.segment).filter(Boolean))),
)
const e03Categories = computed(() =>
  Array.from(new Set(allE03Items.value.map(row => row.category).filter(Boolean)))
    .sort((a, b) => a.localeCompare(b, 'zh-CN')),
)
const e03HasFilters = computed(() => Boolean(e03DeadlineFilter.value || e03SegmentFilter.value || e03CategoryFilter.value))
const filteredE03Items = computed(() => allE03Items.value.filter(row =>
  (!e03DeadlineFilter.value || (e03DeadlineFilter.value === 'overdue' ? row.overdue : !row.overdue)) &&
  (!e03SegmentFilter.value || row.segment === e03SegmentFilter.value) &&
  (!e03CategoryFilter.value || row.category === e03CategoryFilter.value),
))

function aggregateE03Items(items: E03DetailRow[], field: 'category' | 'department') {
  const counts = new Map<string, number>()
  items.forEach(row => {
    const value = row[field]
    if (value) counts.set(value, (counts.get(value) ?? 0) + 1)
  })
  return Array.from(counts, ([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value || a.name.localeCompare(b.name, 'zh-CN'))
}

const e03SegmentData = computed(() => e03Segments.value.map(section => {
  const rows = allE03Items.value.filter(row => row.segment === section)
  const overdue = rows.filter(row => row.overdue).length
  return { section, normal: rows.length - overdue, overdue, total: rows.length }
}))
const e03TypeData = computed(() => aggregateE03Items(filteredE03Items.value, 'category'))
const e03DepartmentData = computed(() => aggregateE03Items(filteredE03Items.value, 'department'))
const e03OverdueRows = computed(() => filteredE03Items.value
  .filter(row => row.overdue)
  .sort((a, b) => a.deadline.localeCompare(b.deadline) || a.id - b.id))
const e03OverdueReminder = computed(() => e03OverdueRows.value[0] ?? null)
const e03OtherOverdueCount = computed(() => Math.max(0, e03OverdueRows.value.length - 1))
const e03SelectedRow = computed(() => allE03Items.value.find(row => row.id === e03SelectedId.value) ?? null)
const e03CanOperate = computed(() => Boolean(e03SelectedRow.value))
const e03FilterLabels = computed(() => [
  e03DeadlineFilter.value === 'overdue' ? '已逾期' : e03DeadlineFilter.value === 'normal' ? '正常' : null,
  e03SegmentFilter.value,
  e03CategoryFilter.value,
].filter((value): value is string => Boolean(value)))
const e03FilterSummary = computed(() =>
  `${e03FilterLabels.value.length ? e03FilterLabels.value.join(' / ') : '全部'} · 共${filteredE03Items.value.length}条`,
)
const e03HighlightedSegments = computed(() => {
  if (!e03HasFilters.value) return new Set(e03Segments.value)
  return new Set(filteredE03Items.value.map(row => row.segment))
})

function clearE03Filters() {
  e03DeadlineFilter.value = null
  e03SegmentFilter.value = null
  e03CategoryFilter.value = null
  e03SelectedId.value = null
}

function toggleE03DeadlineFilter(value: Exclude<E03DeadlineFilter, null> | 'all') {
  e03DeadlineFilter.value = value === 'all' ? null : e03DeadlineFilter.value === value ? null : value
}

function toggleE03SegmentFilter(value: string | null) {
  e03SegmentFilter.value = e03SegmentFilter.value === value ? null : value
}

function toggleE03CategoryFilter(value: string | null) {
  e03CategoryFilter.value = e03CategoryFilter.value === value ? null : value
}

function toggleE03Selection(row: E03DetailRow) {
  e03SelectedId.value = e03SelectedId.value === row.id ? null : row.id
}

function e03MainStatusClass(status: E03DetailRow['mainStatus']) {
  if (status === '整改中') return 'tag-blue'
  if (status === '待整改') return 'tag-orange'
  return 'tag-normal'
}

function handleE03OverdueReminder() {
  const row = e03OverdueReminder.value
  if (!row) return
  e03DeadlineFilter.value = 'overdue'
  e03SegmentFilter.value = row.segment
  e03CategoryFilter.value = null
  e03SelectedId.value = row.id
  nextTick(() => modalRef.value?.querySelector(`[data-e03-id="${row.id}"]`)?.scrollIntoView({ block: 'nearest' }))
}

watch(filteredE03Items, rows => {
  if (e03SelectedId.value !== null && !rows.some(row => row.id === e03SelectedId.value)) e03SelectedId.value = null
})

// E04 时间范围筛选
const e04TimeRange = ref('6m')
const e04TimeRanges = [
  { key: '6m', label: '近6月' },
  { key: '12m', label: '近12月' },
]

// E04 趋势数据（完整核算月，不包含未完成月份）
const e04TrendData = {
  months6: ['1月', '2月', '3月', '4月', '5月', '6月'],
  months12: ['7月', '8月', '9月', '10月', '11月', '12月', '1月', '2月', '3月', '4月', '5月', '6月'],
  data6: [0.156, 0.182, 0.168, 0.142, 0.132, 0.128],
  data12: [0.174, 0.171, 0.169, 0.165, 0.161, 0.159, 0.156, 0.182, 0.168, 0.142, 0.132, 0.128],
  target: 0.150,
}

// E04 标段排名
const e04SectionRanking = [
  { name: 'K36+500~K41+000 桥梁段', value: 0.112, normal: true },
  { name: 'K12+300~K16+800 路基段', value: 0.128, normal: true, highlight: true },
  { name: 'K48+150~K52+800 隧道段', value: 0.145, normal: true },
  { name: 'K24+000~K28+500 路基段', value: 0.186, normal: true },
  { name: 'K61+800~K65+200 互通段', value: 0.198, normal: false },
]

// S01 近12月状态
const s01MonthlyStatus = [
  { month: '2025-08', status: '正常' },
  { month: '2025-09', status: '正常' },
  { month: '2025-10', status: '正常' },
  { month: '2025-11', status: '正常' },
  { month: '2025-12', status: '正常' },
  { month: '2026-01', status: '正常' },
  { month: '2026-02', status: '正常' },
  { month: '2026-03', status: '正常' },
  { month: '2026-04', status: '正常' },
  { month: '2026-05', status: '正常' },
  { month: '2026-06', status: '正常' },
  { month: '2026-07', status: '正常' },
]

// S01 时间轴节点
const s01TimelineNodes = [
  { label: '起算节点', value: '2025-07-10', type: 'start' },
  { label: '30天月度复核', value: '2025-08-10', type: 'review' },
  { label: '60天月度复核', value: '2025-09-09', type: 'review' },
  { label: '特殊施工期', value: '2025-10~2025-12', type: 'special' },
  { label: '90天月度复核', value: '2025-10-09', type: 'review' },
  { label: '当前连续', value: '368天', type: 'current' },
]

// S01 计数规则摘要
const s01Rules = [
  '每日按自然日滚动累计，持续无责任事故则天数+1',
  '发生经认定的责任事故，天数从次日开始重新计算',
  '停工期是否计入连续天数，按项目确认口径执行',
]

// S03 纠纷类型分布
const s03TypeData = [
  { name: '工资支付', value: 2, color: '#2f9cff' },
  { name: '退场结算', value: 1, color: '#ffb347' },
  { name: '考勤争议', value: 1, color: '#a66cff' },
]

// S03 风险等级
const s03RiskData = [
  { name: '高风险', value: 1, color: '#ff4f5e' },
  { name: '中风险', value: 2, color: '#ffb347' },
  { name: '一般关注', value: 1, color: '#2f9cff' },
]

// 专题标签页
const activeTab = ref('cumulative')
const isTopicMode = computed(() => props.detail.isTopic === true)

// 碳足迹标签页数据
const topicData = computed(() => props.detail.topicData || {})
const carbonCumulativeData = computed(() => topicData.value.cumulative || carbonTabData.cumulative)
const carbonBenefitData = computed(() => topicData.value.benefit || carbonTabData.benefit)
const carbonSourceData = computed(() => topicData.value.source || carbonTabData.source)
const carbonCostData = computed(() => topicData.value.cost || carbonTabData.cost)
const carbonMeasuresData = computed(() => topicData.value.measures || carbonTabData.measures)

// 月报标签页数据
const monthlyProgressData = computed(() => topicData.value.progress || monthlyTabData.progress)
const monthlyChaptersData = computed(() => topicData.value.chapters || monthlyTabData.chapters)
const monthlyStatusChain = computed(() => topicData.value.statusChain || monthlyTabData.statusChain)
const monthlyGroupFilter = ref('all')

const currentChartType = computed(() => props.detail.key)

function findFocusedRowIndex(rows: KpiDetailBottomItem[]): number {
  const ctx = props.focusContext
  if (!ctx) return -1
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i] as any
    if (ctx.sourceId && row.sourceId === ctx.sourceId) return i
    if (ctx.sourceId && row.id === ctx.sourceId) return i
  }
  if (ctx.gisFeatureId) {
    for (let i = 0; i < rows.length; i++) {
      const row = rows[i] as any
      if (row.gisFeatureId === ctx.gisFeatureId) return i
    }
  }
  return -1
}

const hasFocusContext = computed(() => {
  const ctx = props.focusContext
  if (!ctx) return false
  if (props.detail.key !== 'E02') return false
  return !!(ctx.sourceId || ctx.gisFeatureId)
})

const e02FocusedIndex = computed(() => {
  if (!hasFocusContext.value || props.detail.key !== 'E02') return -1
  return findFocusedRowIndex(filteredE02Items.value)
})

const focusNotFound = computed(() => {
  if (!hasFocusContext.value) return false
  if (props.detail.key === 'E02') return e02FocusedIndex.value === -1
  return false
})

const focusSourceText = computed(() => {
  const ctx = props.focusContext
  if (!ctx) return ''
  const key = props.detail.key
  if (ctx.title) {
    if (key === 'E02') return `已从 GIS 地图定位到：${ctx.title}`
    return `已从 GIS 地图定位到：${ctx.title}`
  }
  if (ctx.sourceId) {
    if (key === 'E02') return `已从 GIS 地图定位到关联环保问题：${ctx.sourceId}`
  }
  return '已从 GIS 地图定位到关联记录'
})

const focusNotFoundText = computed(() => {
  return '已打开对应指标弹窗，但未在当前明细中找到该 GIS 关联记录。'
})

const isFromGis = computed(() => props.focusContext?.from === 'gis')
const isGisViewOnlyKpi = computed(() =>
  isFromGis.value && props.detail.key === 'E02',
)

const filteredMonthlyDetailData = computed(() => {
  if (!props.detail.detailData) return []
  if (props.detail.key !== 'MONTHLY') return props.detail.detailData
  const filter = monthlyGroupFilter.value
  if (filter === 'all') return props.detail.detailData
  return props.detail.detailData.filter((d: any) => d.group === filter)
})

function initChart() {
  if (!chartRef.value) return
  if (chart) {
    chart.dispose()
    chart = null
  }
  chart = echarts.init(chartRef.value)
  // E02 图表柱状条点击筛选
  chart.on('click', (params: { name?: string }) => {
    if (!params.name) return
    if (props.detail.key === 'E02') {
      const statusName = params.name
      if (['整改中', '待复查', '待关闭', '待销项'].includes(statusName)) {
        e02ToggleMainStatus(statusName === '待关闭' ? '待销项' : statusName as E02MainStatus)
      }
    } else if (props.detail.key === 'E03' && e03Segments.value.includes(params.name)) {
      toggleE03SegmentFilter(params.name)
    }
  })
  updateChart()
}

function updateChart() {
  if (!chart) return
  const key = props.detail.key

  // 专题模式图表
  if (key === 'CARBON') {
    if (activeTab.value === 'cumulative') {
      chart.setOption({
        grid: { top: 30, right: 20, bottom: 30, left: 50 },
        xAxis: {
          type: 'category',
          data: carbonCumulativeData.value.months,
          axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
          axisLabel: { color: '#8fa9c8', fontSize: 10, rotate: 30 },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'value',
          axisLine: { show: false },
          axisLabel: { color: '#8fa9c8', fontSize: 11 },
          splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
        },
        tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
        legend: { bottom: 0, textStyle: { color: '#8fa9c8', fontSize: 11 }, itemWidth: 14, itemHeight: 8 },
        series: [
          {
            type: 'bar',
            name: '月度排放',
            data: carbonCumulativeData.value.monthlyData,
            barWidth: 12,
            itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#69e36f' }, { offset: 1, color: 'rgba(105,227,111,0.2)' }]), borderRadius: [2, 2, 0, 0] },
          },
          {
            type: 'line',
            name: '累计排放',
            data: carbonCumulativeData.value.cumulativeData,
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            lineStyle: { color: '#2f9cff', width: 2 },
            itemStyle: { color: '#2f9cff', borderColor: '#02111f', borderWidth: 2 },
            yAxisIndex: 0,
          },
        ],
      })
    } else if (activeTab.value === 'benefit') {
      chart.setOption({
        grid: { top: 30, right: 20, bottom: 30, left: 50 },
        xAxis: {
          type: 'category',
          data: carbonBenefitData.value.months,
          axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
          axisLabel: { color: '#8fa9c8', fontSize: 10, rotate: 30 },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'value',
          axisLine: { show: false },
          axisLabel: { color: '#8fa9c8', fontSize: 11 },
          splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
        },
        tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
        legend: { bottom: 0, textStyle: { color: '#8fa9c8', fontSize: 11 }, itemWidth: 14, itemHeight: 8 },
        series: [
          {
            type: 'bar',
            name: '基准方案',
            data: carbonBenefitData.value.baselineData,
            barWidth: 10,
            itemStyle: { color: 'rgba(255,179,71,0.6)', borderRadius: [2, 2, 0, 0] },
          },
          {
            type: 'bar',
            name: '实际方案',
            data: carbonBenefitData.value.actualData,
            barWidth: 10,
            itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#69e36f' }, { offset: 1, color: 'rgba(105,227,111,0.2)' }]), borderRadius: [2, 2, 0, 0] },
          },
        ],
      })
    } else if (activeTab.value === 'source') {
      chart.setOption({
        grid: { top: 10, right: 20, bottom: 24, left: 60 },
        xAxis: {
          type: 'value',
          max: 60,
          axisLine: { show: false },
          axisLabel: { color: '#8fa9c8', fontSize: 11, formatter: '{value}%' },
          splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
        },
        yAxis: {
          type: 'category',
          data: carbonSourceData.value.items.map((d: any) => d.name),
          axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
          axisLabel: { color: '#8fa9c8', fontSize: 12 },
          axisTick: { show: false },
        },
        tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
        series: [
          {
            type: 'bar',
            data: carbonSourceData.value.items.map((d: any) => ({ value: d.value, itemStyle: { color: d.color, borderRadius: [0, 3, 3, 0] } })),
            barWidth: 16,
            label: { show: true, position: 'right', color: '#e8f3ff', fontSize: 11, formatter: '{c}%' },
          },
        ],
      })
    }
    return
  }

  if (key === 'MONTHLY') {
    chart.setOption({
      grid: { top: 10, right: 20, bottom: 24, left: 80 },
      xAxis: {
        type: 'value',
        max: 100,
        axisLine: { show: false },
        axisLabel: { color: '#8fa9c8', fontSize: 11, formatter: '{value}%' },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        data: monthlyProgressData.value.groups.map((d: any) => d.label),
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#8fa9c8', fontSize: 12 },
        axisTick: { show: false },
      },
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
      series: [
        {
          type: 'bar',
          data: monthlyProgressData.value.groups.map((d: any) => ({ value: d.value, itemStyle: { color: d.color, borderRadius: [0, 4, 4, 0] } })),
          barWidth: 16,
          label: { show: true, position: 'right', color: '#e8f3ff', fontSize: 11, formatter: '{c}%' },
        },
      ],
    })
    return
  }

  if (key === 'E01') {
    const cat = e01Filter.value as keyof typeof e01TrendData
    const series: any[] = []

    if (cat === 'all') {
      e01AvailableCategories.value.forEach(availableCat => {
        if (availableCat.key === 'all') return
        const catName = availableCat.label
        const catColor = e01CatColors[availableCat.key] || themeColor.value
        const data = e01TrendData[availableCat.key as keyof typeof e01TrendData] as number[]
        series.push({
          id: `bar-${availableCat.key}`,
          type: 'bar',
          name: catName,
          data,
          barWidth: 12,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: catColor },
              { offset: 1, color: `${catColor}40` },
            ]),
            borderRadius: [2, 2, 0, 0],
          },
        })
      })
      series.push({
        id: 'line-total',
        type: 'line',
        name: '合计',
        data: e01TrendData.all,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: '#f4edc4', width: 2 },
        itemStyle: { color: '#fff8d6', borderColor: '#f4edc4', borderWidth: 1 },
        z: 5,
      })
    } else {
      const catName = e01Categories.find(c => c.key === cat)?.label || ''
      const catColor = e01CatColors[cat] || themeColor.value
      series.push({
        id: `bar-${cat}`,
        type: 'bar',
        name: catName,
        data: e01TrendData[cat] as number[],
        barWidth: 16,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: catColor },
            { offset: 1, color: `${catColor}40` },
          ]),
          borderRadius: [2, 2, 0, 0],
        },
      })
    }

    chart.setOption({
      animation: !isAcceptanceMode,
      grid: { top: 20, right: 16, bottom: 22, left: 32 },
      xAxis: {
        type: 'category',
        data: e01TrendData.months,
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#8fa9c8', fontSize: 13, margin: 12 },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        minInterval: 1,
        axisLine: { show: false },
        axisLabel: { color: '#8fa9c8', fontSize: 13 },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(5,18,38,0.92)',
        borderColor: 'rgba(0,174,255,0.3)',
        textStyle: { color: '#e8f3ff', fontSize: 13 }
      },
      legend: {
        show: false,
      },
      series,
    }, { replaceMerge: ['series', 'legend'] })
  } else if (key === 'E02') {
    const statusData = e02StatusData.value
    const highlightedStatuses = e02HighlightedStatuses.value
    const maxValue = Math.max(...statusData.map(d => d.value), 1)
    const xAxisMax = Math.ceil(maxValue * 1.3)
    chart.setOption({
      animation: !isAcceptanceMode,
      grid: { top: 10, right: 20, bottom: 24, left: 70 },
      xAxis: {
        type: 'value',
        minInterval: 1,
        max: xAxisMax,
        axisLine: { show: false },
        axisLabel: { color: '#8fa9c8', fontSize: 13 },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        data: statusData.map(d => d.name),
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#8fa9c8', fontSize: 13 },
        axisTick: { show: false },
      },
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 13 } },
      series: [
        {
          type: 'bar',
          data: statusData.map(d => {
            const opacity = highlightedStatuses.has(d.name) ? 1 : 0.3
            return {
              value: d.value,
              itemStyle: { color: d.color, borderRadius: [0, 3, 3, 0], opacity },
              label: { opacity },
            }
          }),
          barWidth: 12,
          label: { show: true, position: 'right', color: '#e8f3ff', fontSize: 13 },
        },
      ],
    })
  } else if (key === 'E03') {
    const segments = e03SegmentData.value
    const opacityFor = (section: string) => e03HighlightedSegments.value.has(section) ? 1 : 0.28
    const overdueColor = e03DeadlineFilter.value === 'overdue' ? '#ff4f5e' : '#d85f69'
    chart.setOption({
      animation: !isAcceptanceMode,
      grid: { top: 18, right: 48, bottom: 28, left: 78 },
      xAxis: {
        type: 'value',
        interval: 1,
        minInterval: 1,
        max: Math.ceil(Math.max(...segments.map(item => item.total), 1)),
        axisLine: { show: false },
        axisLabel: { color: '#8fa9c8', fontSize: 13, formatter: (value: number) => String(Math.round(value)) },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        inverse: true,
        data: segments.map(item => item.section),
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#b8cce3', fontSize: 13 },
        axisTick: { show: false },
      },
      legend: {
        top: 0,
        right: 8,
        itemWidth: 12,
        itemHeight: 8,
        textStyle: { color: '#b8cce3', fontSize: 13 },
        data: ['正常时限', '已逾期'],
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: 'rgba(5,18,38,0.94)',
        borderColor: 'rgba(105,227,111,0.3)',
        textStyle: { color: '#e8f3ff', fontSize: 13 },
        formatter: (params: Array<{ axisValue?: string }>) => {
          const section = String(params[0]?.axisValue ?? '')
          const item = segments.find(entry => entry.section === section)
          if (!item) return section
          return `${section}<br/>正常时限：${item.normal}项<br/>已逾期：${item.overdue}项<br/><strong>合计：${item.total}项</strong>`
        },
      },
      series: [
        {
          name: '正常时限',
          type: 'bar',
          stack: 'total',
          barWidth: 18,
          itemStyle: { color: '#69e36f' },
          data: segments.map(item => ({
            value: item.normal,
            itemStyle: { color: '#69e36f', opacity: opacityFor(item.section), borderRadius: item.overdue ? [3, 0, 0, 3] : [3, 3, 3, 3] },
            label: {
              show: item.normal > 0,
              position: 'inside',
              color: '#062312',
              fontSize: 13,
              fontWeight: 700,
              opacity: opacityFor(item.section),
              formatter: item.normal > 0 ? String(item.normal) : '',
            },
          })),
        },
        {
          name: '已逾期',
          type: 'bar',
          stack: 'total',
          barWidth: 18,
          itemStyle: { color: overdueColor },
          data: segments.map(item => ({
            value: item.overdue,
            itemStyle: { color: overdueColor, opacity: opacityFor(item.section), borderRadius: [0, 3, 3, 0] },
            label: {
              show: item.overdue > 0,
              position: 'inside',
              color: '#ffffff',
              fontSize: 13,
              fontWeight: 700,
              opacity: opacityFor(item.section),
              formatter: item.overdue > 0 ? String(item.overdue) : '',
            },
          })),
        },
        {
          name: '合计',
          type: 'bar',
          barGap: '-100%',
          barWidth: 18,
          silent: true,
          tooltip: { show: false },
          data: segments.map(item => ({
            value: item.total,
            itemStyle: { color: 'transparent' },
            label: { show: true, position: 'right', color: '#e8f3ff', fontSize: 13, fontWeight: 600, formatter: `${item.total}` },
          })),
        },
      ],
    }, true)
  } else if (key === 'E04') {
    const range = e04TimeRange.value
    const months = range === '6m' ? e04TrendData.months6 : e04TrendData.months12
    const data = range === '6m' ? e04TrendData.data6 : e04TrendData.data12

    chart.setOption({
      grid: { top: 20, right: 20, bottom: 30, left: 45 },
      xAxis: {
        type: 'category',
        data: months,
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#8fa9c8', fontSize: 11 },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 0.25,
        axisLine: { show: false },
        axisLabel: { color: '#8fa9c8', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(5,18,38,0.92)',
        borderColor: 'rgba(0,174,255,0.3)',
        textStyle: { color: '#e8f3ff', fontSize: 12 },
        formatter: (params: any) => {
          const p = params[0]
          return `${p.name}<br/>碳排放强度: <strong>${p.value}</strong> tCO₂e/万元`
        }
      },
      series: [
        {
          type: 'line',
          name: '碳排放强度',
          data: data,
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: { color: '#69e36f', width: 2 },
          itemStyle: { color: '#69e36f', borderColor: '#02111f', borderWidth: 2 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(105,227,111,0.3)' },
              { offset: 1, color: 'rgba(105,227,111,0)' },
            ]),
          },
        },
        {
          type: 'line',
          name: '目标值',
          data: Array(months.length).fill(e04TrendData.target),
          smooth: false,
          symbol: 'none',
          lineStyle: { color: '#ffb347', width: 1, type: 'dashed' },
        },
      ],
    })
  } else if (key === 'S01') {
    chart.setOption({
      grid: { top: 10, right: 20, bottom: 24, left: 60 },
      xAxis: {
        type: 'value',
        minInterval: 1,
        max: 6,
        axisLine: { show: false },
        axisLabel: { show: false },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        data: s01TimelineNodes.map(d => d.label),
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#8fa9c8', fontSize: 11 },
        axisTick: { show: false },
      },
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
      series: [
        {
          type: 'bar',
          data: [1, 2, 2, 3, 2, 4].map((v, i) => ({
            value: v,
            itemStyle: {
              color: s01TimelineNodes[i].type === 'current' ? '#2f9cff' :
                     s01TimelineNodes[i].type === 'start' ? '#69e36f' :
                     s01TimelineNodes[i].type === 'special' ? '#ffb347' : '#2f9cff',
              borderRadius: [0, 3, 3, 0],
            },
          })),
          barWidth: 4,
        },
      ],
    })
  } else if (key === 'S03') {
    chart.setOption({
      grid: { top: 10, right: 20, bottom: 24, left: 70 },
      xAxis: {
        type: 'value',
        minInterval: 1,
        max: 3,
        axisLine: { show: false },
        axisLabel: { color: '#8fa9c8', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(143,169,200,0.08)', type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        data: s03TypeData.map(d => d.name),
        axisLine: { lineStyle: { color: 'rgba(143,169,200,0.2)' } },
        axisLabel: { color: '#8fa9c8', fontSize: 12 },
        axisTick: { show: false },
      },
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(5,18,38,0.92)', borderColor: 'rgba(0,174,255,0.3)', textStyle: { color: '#e8f3ff', fontSize: 12 } },
      series: [
        {
          type: 'bar',
          data: s03TypeData.map(d => ({ value: d.value, itemStyle: { color: d.color, borderRadius: [0, 3, 3, 0] } })),
          barWidth: 12,
          label: { show: true, position: 'right', color: '#e8f3ff', fontSize: 11 },
        },
      ],
    })
  }
}

function handleResize() {
  updateE01Scale()
  updateE02Scale()
  updateE03Scale()
  chart?.resize()
}

function handleOverlayClick(e: MouseEvent) {
  if (e.target === e.currentTarget) {
    emit('close')
  }
}

function handleDetailReserved() {
  if (props.detail.key === 'E02' && e02SelectedRow.value) {
    superviseToastMessage.value = `已选择“${e02SelectedRow.value.name}”，详情功能尚未接入。`
  } else if (props.detail.key === 'E03' && e03SelectedRow.value) {
    superviseToastMessage.value = `已选择“${e03SelectedRow.value.name}”，事项详情流程尚未接入。`
  } else {
    return
  }
  showTemporaryToast()
}

function handleSupervise() {
  if (props.detail.key === 'E01') {
    const row = e01SelectedRow.value
    if (!row || !isE01Actionable(row)) return
    superviseToastMessage.value = `已选择“${row.point.replace(/\s+/g, '')}—${row.factor}”。督办流程尚未接入。`
  } else if (props.detail.key === 'E02') {
    if (!e02SelectedRow.value) return
    superviseToastMessage.value = `已选择“${e02SelectedRow.value.name}”。\n督办流程尚未接入。`
  } else if (props.detail.key === 'E03') {
    if (!e03SelectedRow.value) return
    superviseToastMessage.value = `已选择“${e03SelectedRow.value.name}”，督办流程尚未接入。`
  } else {
    superviseToastMessage.value = '督办功能为原型预留，尚未接入业务流程'
  }
  showTemporaryToast()
}

function showTemporaryToast() {
  showSuperviseToast.value = true
  if (superviseTimer) {
    clearTimeout(superviseTimer)
  }
  superviseTimer = setTimeout(() => {
    showSuperviseToast.value = false
    superviseTimer = null
  }, 3000)
}

watch(e01Filter, () => {
  if (props.detail.key === 'E01') {
    updateChart()
  }
})

watch(filteredE01DetailData, (rows) => {
  if (e01SelectedId.value !== null && !rows.some(row => row.id === e01SelectedId.value)) {
    e01SelectedId.value = null
  }
})

watch([mainStatusFilter, categoryFilter, overdueOnly], () => {
  if (props.detail.key === 'E02') updateChart()
})

watch([e03DeadlineFilter, e03SegmentFilter, e03CategoryFilter], () => {
  if (props.detail.key === 'E03') updateChart()
})

watch(e04TimeRange, () => {
  if (props.detail.key === 'E04') {
    updateChart()
  }
})

watch(() => props.detail.key, (newKey) => {
  if (newKey === 'CARBON') {
    activeTab.value = 'cumulative'
  } else if (newKey === 'MONTHLY') {
    activeTab.value = 'progress'
  }
})

watch(activeTab, () => {
  if (isTopicMode.value) {
    nextTick(() => {
      if (chartRef.value) {
        if (chart) {
          chart.dispose()
          chart = null
        }
        chart = echarts.init(chartRef.value)
        updateChart()
      }
    })
  }
})

watch(() => props.detail.key, () => {
  focusScrollDone.value = false
  updateE01Scale()
  updateE02Scale()
  updateE03Scale()
  nextTick(() => {
    initChart()
    modalRef.value?.focus()
  })
})

watch([hasFocusContext, e02FocusedIndex, () => props.detail.key], () => {
  if (!hasFocusContext.value) return
  const key = props.detail.key
  if (key === 'E02') {
    if (e02FocusedIndex.value === -1 && (mainStatusFilter.value || categoryFilter.value || overdueOnly.value)) {
      mainStatusFilter.value = null
      categoryFilter.value = null
      overdueOnly.value = false
    }
  }
}, { immediate: true })

watch([e02FocusedIndex], () => {
  if (!hasFocusContext.value || focusScrollDone.value) return
  const idx = e02FocusedIndex.value
  if (idx >= 0) {
    nextTick(() => {
      focusRowRef.value?.scrollIntoView({ block: 'center', behavior: 'smooth' })
      focusScrollDone.value = true
    })
  }
}, { immediate: true })

onMounted(() => {
  updateE01Scale()
  updateE02Scale()
  updateE03Scale()
  nextTick(() => {
    initChart()
    window.addEventListener('resize', handleResize)
    modalRef.value?.focus()
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
  if (superviseTimer) {
    clearTimeout(superviseTimer)
    superviseTimer = null
  }
})
</script>

<template>
  <ClassBMatterModal
    v-if="['S01', 'S03', 'S04', 'G01', 'G02', 'G03', 'G04'].includes(detail.key)"
    :module-key="detail.key"
    @close="emit('close')"
  />
  <S02SafetyRiskModal v-else-if="detail.key === 'S02'" @close="emit('close')" />
  <!-- 首页 E04 已切换为文物保护工作台；不再打开碳排放弹窗。若仍请求 E04 detail 则走下方通用壳。 -->
  <CarbonBenefitModal v-else-if="detail.key === 'CARBON'" :detail="detail" @close="emit('close')" />
  <MonthlyReportModal v-else-if="detail.key === 'MONTHLY'" :detail="detail" @close="emit('close')" />
  <div v-else class="kpi-modal-overlay" :class="{ 'e01-acceptance-overlay': detail.key === 'E01' && isAcceptanceMode, 'e02-acceptance-overlay': detail.key === 'E02' && isAcceptanceMode, 'e03-acceptance-overlay': detail.key === 'E03' && isAcceptanceMode }" @click="handleOverlayClick">
    <div
      ref="modalRef"
      class="kpi-modal"
      :class="[`theme-${detail.theme}`, { 'is-e01': detail.key === 'E01', 'is-e02': detail.key === 'E02', 'is-e03': detail.key === 'E03', 'is-acceptance': (detail.key === 'E01' || detail.key === 'E02' || detail.key === 'E03') && isAcceptanceMode }]"
      :style="detail.key === 'E01' ? { '--e01-scale': e01Scale } : detail.key === 'E02' ? { '--e02-scale': e02Scale } : detail.key === 'E03' ? { '--e03-scale': e03Scale } : undefined"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="`modal-title-${detail.key}`"
      tabindex="-1"
      @keydown="handleE01ModalKeydown"
    >
      <!-- 标题栏 -->
      <div class="modal-header">
        <h2 :id="`modal-title-${detail.key}`" class="modal-title">
          <span class="title-key">{{ detail.key }}</span>
          <span class="title-name">{{ detail.fullName }}</span>
        </h2>
        <button class="modal-close" aria-label="关闭" @click="emit('close')">
          <X :size="20" />
        </button>
      </div>

      <!-- 专题标签页导航 -->
      <div v-if="isTopicMode" class="modal-tabs">
        <button
          v-for="tab in detail.tabs"
          :key="tab.key"
          class="tab-btn"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- 顶部摘要指标 -->
      <div class="modal-summary">
        <template v-if="detail.key === 'E02'">
          <button
            v-for="item in e02SummaryCards"
            :key="item.label"
            type="button"
            class="summary-card e02-summary-card"
            :class="{ active: isE02SummaryActive(item) }"
            @click="activateE02Summary(item)"
          >
            <div class="summary-label">{{ item.label }}</div>
            <div class="summary-value-row">
              <span class="summary-value" :style="{ color: summaryValueColor(item) }">{{ item.value }}</span>
              <span class="summary-unit">{{ item.unit }}</span>
            </div>
          </button>
        </template>
        <template v-else>
          <div v-for="(item, idx) in detail.summary" :key="idx" class="summary-card">
            <div class="summary-label">{{ item.label }}</div>
            <div class="summary-value-row">
              <span class="summary-value" :style="{ color: summaryValueColor(item) }">
                {{ item.value }}
              </span>
              <span v-if="item.unit" class="summary-unit">{{ item.unit }}</span>
            </div>
          </div>
        </template>
      </div>

      <!-- E04 指标计算说明 -->
      <div v-if="detail.key === 'E04'" class="calc-explanation">
        <div class="calc-title">指标计算说明</div>
        <div class="calc-formula">
          <span class="calc-term">单位完成产值碳排放强度（tCO₂e/万元）</span>
          <span class="calc-operator">＝</span>
          <span class="calc-term">核算期施工活动碳排放量（tCO₂e）</span>
          <span class="calc-operator">÷</span>
          <span class="calc-term">同期完成产值（万元）</span>
        </div>
        <div class="calc-formula">
          <span class="calc-term">核算期施工活动碳排放量</span>
          <span class="calc-operator">＝</span>
          <span class="calc-term">Σ（施工活动数据 × 对应排放因子）</span>
        </div>
        <div class="calc-note">施工活动数据包括纳入当前核算边界的燃油消耗量、用电量及其他能源活动数据。</div>
      </div>

      <!-- 主内容区：左图右摘 -->
      <div class="modal-content">
        <div class="content-main">
          <div class="chart-section">
            <div class="chart-header">
              <span class="chart-title">{{
                detail.key === 'E04' ? (e04TimeRange === '6m' ? '近6个完整核算月碳排放强度趋势' : '近12个完整核算月碳排放强度趋势') :
                detail.key === 'CARBON' && activeTab === 'cumulative' ? '月度累计碳足迹趋势' :
                detail.key === 'CARBON' && activeTab === 'benefit' ? '基准方案与实际方案对比' :
                detail.key === 'CARBON' && activeTab === 'source' ? '排放来源构成' :
                detail.key === 'CARBON' && activeTab === 'cost' ? '成本影响分析' :
                detail.key === 'CARBON' && activeTab === 'measures' ? '主要低碳措施' :
                detail.key === 'MONTHLY' && activeTab === 'progress' ? 'E/S/G 各组准备进度' :
                detail.key === 'MONTHLY' && activeTab === 'chapters' ? '章节与成果清单' :
                detail.key === 'MONTHLY' && activeTab === 'gaps' ? '缺项与校核清单' :
                detail.chartTitle
              }}</span>
              <!-- E01 筛选 -->
              <div v-if="detail.key === 'E01'" class="chart-filters">
                <button
                  v-for="cat in e01AvailableCategories"
                  :key="cat.key"
                  class="filter-btn"
                  :class="{ active: e01Filter === cat.key }"
                  @click="e01Filter = cat.key"
                >
                  {{ cat.label }}
                </button>
              </div>
              <!-- E04 时间范围 -->
              <div v-if="detail.key === 'E04'" class="chart-filters">
                <button
                  v-for="range in e04TimeRanges"
                  :key="range.key"
                  class="filter-btn"
                  :class="{ active: e04TimeRange === range.key }"
                  @click="e04TimeRange = range.key"
                >
                  {{ range.label }}
                </button>
              </div>
              <div v-if="detail.key === 'E02' && e02HasFilters" class="e02-active-filter">
                <span>当前筛选：<strong>{{ e02ActiveFilterText }}</strong></span>
                <span>共{{ filteredE02Items.length }}条</span>
                <button type="button" @click="clearE02Filters">清除</button>
              </div>
              <div v-if="detail.key === 'E03' && e03HasFilters" class="e03-active-filter">
                <span>当前筛选：<strong>{{ e03FilterLabels.join(' / ') }}</strong></span>
                <span>共{{ filteredE03Items.length }}条</span>
                <button type="button" @click="clearE03Filters">清除筛选</button>
              </div>
              <!-- E01 图例 -->
              <div v-if="detail.key === 'E01' && e01Filter === 'all' && e01CompositionData.length > 1" class="chart-legend">
                <span class="legend-item"><i class="legend-dot dust"></i>扬尘</span>
                <span class="legend-item"><i class="legend-dot noise"></i>噪声</span>
                <span class="legend-item"><i class="legend-dot line"></i>合计</span>
              </div>
            </div>
            <div v-if="detail.key === 'E02' && e02HasFilters && filteredE02Items.length === 0" class="e02-chart-empty">
              当前筛选条件下无匹配事项
            </div>

            <div v-if="detail.key === 'E03'" class="e03-filter-panel" aria-label="E03筛选条件">
              <div class="e03-filter-group">
                <span>时限状态</span>
                <button type="button" :class="{ active: e03DeadlineFilter === null }" @click="e03DeadlineFilter = null">全部</button>
                <button type="button" :class="{ active: e03DeadlineFilter === 'normal' }" @click="toggleE03DeadlineFilter('normal')">正常</button>
                <button type="button" :class="{ active: e03DeadlineFilter === 'overdue' }" @click="toggleE03DeadlineFilter('overdue')">已逾期</button>
              </div>
              <div class="e03-filter-group">
                <span>所属标段</span>
                <button type="button" :class="{ active: e03SegmentFilter === null }" @click="e03SegmentFilter = null">全部</button>
                <button v-for="segment in e03Segments" :key="segment" type="button" :class="{ active: e03SegmentFilter === segment }" @click="toggleE03SegmentFilter(segment)">{{ segment }}</button>
              </div>
              <div class="e03-filter-group e03-category-filters">
                <span>问题类型</span>
                <button type="button" :class="{ active: e03CategoryFilter === null }" @click="e03CategoryFilter = null">全部</button>
                <button v-for="category in e03Categories" :key="category" type="button" :class="{ active: e03CategoryFilter === category }" @click="toggleE03CategoryFilter(category)">{{ category }}</button>
              </div>
            </div>
            <div v-if="detail.key === 'E03' && filteredE03Items.length === 0" class="e03-chart-empty">当前筛选条件下暂无记录</div>

            <!-- S01 时间轴和月度状态 -->
            <div v-else-if="detail.key === 'S01'" class="s01-content">
              <div class="s01-timeline">
                <svg viewBox="0 0 100 60" preserveAspectRatio="none" class="timeline-svg">
                  <defs>
                    <linearGradient id="timelineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stop-color="#69e36f" />
                      <stop offset="60%" stop-color="#2f9cff" />
                      <stop offset="100%" stop-color="#2f9cff" />
                    </linearGradient>
                  </defs>
                  <!-- 时间轴线 -->
                  <path
                    d="M 8 30 L 92 30"
                    fill="none"
                    stroke="rgba(143,169,200,0.2)"
                    stroke-width="2"
                    stroke-dasharray="4 2"
                  />
                  <!-- 进度线 -->
                  <path
                    d="M 8 30 L 82 30"
                    fill="none"
                    stroke="url(#timelineGradient)"
                    stroke-width="3"
                    stroke-linecap="round"
                  />
                  <!-- 节点 -->
                  <g transform="translate(8, 30)">
                    <circle r="4" fill="#69e36f" />
                    <text y="-8" text-anchor="middle" fill="#69e36f" font-size="5" font-weight="700">起算</text>
                    <text y="12" text-anchor="middle" fill="#8fa9c8" font-size="4">2025-07-10</text>
                  </g>
                  <g transform="translate(23, 30)">
                    <circle r="3" fill="none" stroke="#2f9cff" stroke-width="1.5" />
                    <text y="-6" text-anchor="middle" fill="#8fa9c8" font-size="4">30天</text>
                  </g>
                  <g transform="translate(38, 30)">
                    <circle r="3" fill="none" stroke="#2f9cff" stroke-width="1.5" />
                    <text y="-6" text-anchor="middle" fill="#8fa9c8" font-size="4">60天</text>
                  </g>
                  <g transform="translate(53, 30)">
                    <rect x="-4" y="-4" width="8" height="8" fill="none" stroke="#ffb347" stroke-width="1.5" rx="1" />
                    <text y="-6" text-anchor="middle" fill="#ffb347" font-size="4">特殊期</text>
                  </g>
                  <g transform="translate(68, 30)">
                    <circle r="3" fill="none" stroke="#2f9cff" stroke-width="1.5" />
                    <text y="-6" text-anchor="middle" fill="#8fa9c8" font-size="4">90天</text>
                  </g>
                  <g transform="translate(82, 30)">
                    <circle r="5" fill="#2f9cff" />
                    <circle r="3" fill="#02111f" />
                    <text y="-10" text-anchor="middle" fill="#2f9cff" font-size="5" font-weight="700">368天</text>
                    <text y="12" text-anchor="middle" fill="#8fa9c8" font-size="4">当前</text>
                  </g>
                </svg>
              </div>
              <div class="s01-monthly">
                <div class="monthly-title">近12个月安全生产状态</div>
                <div class="monthly-grid">
                  <div v-for="m in s01MonthlyStatus" :key="m.month" class="month-item">
                    <div class="month-dot status-normal" />
                    <div class="month-label">{{ m.month }}</div>
                    <div class="month-status">{{ m.status }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- E01 空状态 -->
            <div v-else-if="detail.key === 'E01' && !e01HasData" class="chart-empty-state">
              <div class="empty-icon">
                <ShieldCheck :size="48" />
              </div>
              <div class="empty-text">当前统计周期暂无环境监测超标数据</div>
            </div>

            <!-- ECharts 图表 -->
            <div v-else-if="!isTopicMode || (detail.key === 'CARBON' && ['cumulative', 'benefit', 'source'].includes(activeTab)) || (detail.key === 'MONTHLY' && activeTab === 'progress')" ref="chartRef" class="chart-container" />

            <!-- 碳足迹-成本影响 -->
            <div v-if="detail.key === 'CARBON' && activeTab === 'cost'" class="topic-text-content">
              <div class="topic-metric-grid">
                <div class="topic-metric-card">
                  <div class="topic-metric-label">低碳措施投入</div>
                  <div class="topic-metric-value" style="color: #ffb347">{{ carbonCostData.investment }}<span class="unit">万元</span></div>
                </div>
                <div class="topic-metric-card">
                  <div class="topic-metric-label">节约成本</div>
                  <div class="topic-metric-value" style="color: #69e36f">{{ carbonCostData.savings }}<span class="unit">万元</span></div>
                </div>
                <div class="topic-metric-card">
                  <div class="topic-metric-label">避免成本</div>
                  <div class="topic-metric-value" style="color: #2f9cff">{{ carbonCostData.avoidedCost }}<span class="unit">万元</span></div>
                </div>
              </div>
              <div class="topic-note">
                <div class="topic-note-title">测算口径</div>
                <div class="topic-note-text">{{ carbonCostData.caliber }}</div>
              </div>
              <div class="topic-note warning">
                <div class="topic-note-text">{{ carbonCostData.note }}</div>
              </div>
            </div>

            <!-- 碳足迹-主要措施 -->
            <div v-if="detail.key === 'CARBON' && activeTab === 'measures'" class="topic-measures-content">
              <table class="detail-table">
                <thead>
                  <tr>
                    <th v-for="col in carbonMeasuresData.columns" :key="col.key" :style="{ width: col.width || 'auto' }">{{ col.label }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, ri) in carbonMeasuresData.list" :key="ri">
                    <td v-for="col in carbonMeasuresData.columns" :key="col.key">
                      <span v-if="col.key === 'status'" class="status-tag" :class="`tag-${detail.theme}`">{{ (row as any)[col.key] }}</span>
                      <span v-else>{{ (row as any)[col.key] }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 碳足迹-核算边界说明 -->
            <div v-if="detail.key === 'CARBON' && activeTab === 'cumulative'" class="topic-note" style="margin-top: 6px;">
              <div class="topic-note-title">核算边界</div>
              <div class="topic-note-text">{{ carbonCumulativeData.boundary }}</div>
            </div>

            <!-- 月报-章节清单（完整表格） -->
            <div v-if="detail.key === 'MONTHLY' && activeTab === 'chapters'" class="topic-text-content full-height-table">
              <table class="detail-table">
                <thead>
                  <tr>
                    <th v-for="col in monthlyChaptersData.columns" :key="col.key" :style="{ width: col.width || 'auto' }">{{ col.label }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in monthlyChaptersData.list" :key="row.index">
                    <td>{{ row.index }}</td>
                    <td>{{ row.group }}</td>
                    <td>{{ row.name }}</td>
                    <td>{{ row.type }}</td>
                    <td :class="{ 'text-success': row.status === '已完成', 'text-warning': row.status === '编制中' || row.status === '待确认', 'text-danger': row.status === '待补充' }">{{ row.status }}</td>
                    <td>{{ row.owner }}</td>
                    <td>{{ row.person }}</td>
                    <td>{{ row.deadline }}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 月报-缺项清单（完整表格） -->
            <div v-if="detail.key === 'MONTHLY' && activeTab === 'gaps'" class="topic-text-content full-height-table">
              <table class="detail-table">
                <thead>
                  <tr>
                    <th v-for="col in detail.detailColumns" :key="col.key" :style="{ width: col.width || 'auto' }">{{ col.label }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, ri) in filteredMonthlyDetailData" :key="ri">
                    <td v-for="col in detail.detailColumns" :key="col.key" :class="{ 'text-warning': row[col.key] === '待补齐' || row[col.key] === '待确认' || row[col.key] === '异常', 'text-danger': row[col.key] === '已逾期' }">
                      {{ row[col.key] }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 碳足迹-低碳增益公式 -->
            <div v-if="detail.key === 'CARBON' && activeTab === 'benefit'" class="topic-note" style="margin-top: 6px;">
              <div class="topic-note-title">核心公式</div>
              <div class="topic-note-text">{{ carbonBenefitData.formula }}</div>
              <div class="topic-note-text" style="margin-top: 4px; color: #ffb347;">{{ carbonBenefitData.note }}</div>
            </div>

            <!-- 月报-状态链（仅进度页显示） -->
            <div v-if="detail.key === 'MONTHLY' && activeTab === 'progress'" class="monthly-status-chain">
              <div
                v-for="node in monthlyStatusChain"
                :key="node.key"
                class="chain-node"
                :class="node.status"
              >
                <div class="chain-dot" />
                <div class="chain-label">{{ node.label }}</div>
              </div>
            </div>
          </div>

          <!-- 明细表格 -->
          <div class="detail-section" v-if="!(detail.key === 'CARBON' && ['cost', 'measures'].includes(activeTab)) && !(detail.key === 'MONTHLY' && ['chapters', 'gaps'].includes(activeTab))">
            <div v-if="hasFocusContext && !focusNotFound" class="focus-banner">
              <MapPin :size="14" />
              <span>{{ focusSourceText }}</span>
              <span v-if="isGisViewOnlyKpi" class="focus-banner__hint">GIS 来源仅用于查看</span>
            </div>
            <div v-else-if="hasFocusContext && focusNotFound" class="focus-banner focus-banner--warn">
              <AlertTriangle :size="14" />
              <span>{{ focusNotFoundText }}</span>
            </div>
            <div class="detail-title">
              <span>{{ detail.detailTitle }}</span>
              <span v-if="detail.key === 'E01'" class="e01-detail-filter-summary">{{ e01DetailFilterSummary }}</span>
              <span v-else-if="detail.key === 'E02'" class="e02-detail-filter-summary">{{ e02FilterSummary }}</span>
              <span v-else-if="detail.key === 'E03'" class="e03-detail-filter-summary">{{ e03FilterSummary }}</span>
            </div>
            <div class="detail-table-wrapper">
              <table class="detail-table" :class="{ 'detail-table--e01': detail.key === 'E01', 'detail-table--e02': detail.key === 'E02', 'detail-table--e03': detail.key === 'E03' }">
                <thead>
                  <tr>
                    <th
                      v-for="col in detail.detailColumns"
                      :key="col.key"
                      :style="{ width: col.width || 'auto' }"
                    >
                      {{ col.label }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <template v-if="(detail.key === 'E01' ? filteredE01DetailData : detail.key === 'E02' ? filteredE02Items : detail.key === 'E03' ? filteredE03Items : detail.key === 'MONTHLY' ? filteredMonthlyDetailData : detail.detailData).length > 0">
                    <tr
                      v-for="(row, ri) in (detail.key === 'E01' ? filteredE01DetailData : detail.key === 'E02' ? filteredE02Items : detail.key === 'E03' ? filteredE03Items : detail.key === 'MONTHLY' ? filteredMonthlyDetailData : detail.detailData)"
                      :key="detail.key === 'E01' || detail.key === 'E02' || detail.key === 'E03' ? String(row.id) : ri"
                      :data-e01-id="detail.key === 'E01' ? String(row.id) : undefined"
                      :data-e02-id="detail.key === 'E02' ? String(row.id) : undefined"
                      :data-e03-id="detail.key === 'E03' ? String(row.id) : undefined"
                      :tabindex="detail.key === 'E02' || detail.key === 'E03' || (detail.key === 'E01' && isE01Actionable(row as E01DetailRow)) ? 0 : undefined"
                      :aria-selected="detail.key === 'E01' ? e01SelectedId === row.id : detail.key === 'E02' ? e02SelectedId === row.id : detail.key === 'E03' ? e03SelectedId === row.id : undefined"
                      :ref="el => {
                        if (
                          (detail.key === 'E02' && e02FocusedIndex === ri)
                        ) {
                          focusRowRef = el as HTMLTableRowElement | null
                        }
                      }"
                      :class="{
                        'row-selected': (detail.key === 'E02' && e02SelectedId === row.id) || (detail.key === 'E03' && e03SelectedId === row.id) || (detail.key === 'E04' && e04SelectedRow === ri),
                        'e02-selectable': detail.key === 'E02',
                        'e03-selectable': detail.key === 'E03',
                        'e03-row-selected': detail.key === 'E03' && e03SelectedId === row.id,
                        'e03-row-overdue': detail.key === 'E03' && row.overdue === true,
                        'e01-selectable': detail.key === 'E01' && isE01Actionable(row as E01DetailRow),
                        'e01-row-selected': detail.key === 'E01' && e01SelectedId === row.id,
                        'row-focused':
                          (detail.key === 'E02' && hasFocusContext && e02FocusedIndex === ri),
                      }"
                      @click="detail.key === 'E01' && toggleE01Selection(row as E01DetailRow); detail.key === 'E02' && e02ToggleSelection(row as E02DetailRow); detail.key === 'E03' && toggleE03Selection(row as E03DetailRow); detail.key === 'E04' && e04HandleRowClick(ri)"
                      @keydown.enter.prevent="detail.key === 'E01' && toggleE01Selection(row as E01DetailRow); detail.key === 'E02' && e02ToggleSelection(row as E02DetailRow); detail.key === 'E03' && toggleE03Selection(row as E03DetailRow)"
                      @keydown.space.prevent="detail.key === 'E01' && toggleE01Selection(row as E01DetailRow); detail.key === 'E02' && e02ToggleSelection(row as E02DetailRow); detail.key === 'E03' && toggleE03Selection(row as E03DetailRow)"
                    >
                      <td
                        v-for="col in detail.detailColumns"
                      :key="col.key"
                      :title="detail.key === 'E01' || detail.key === 'E02' || detail.key === 'E03' ? String(row[col.key] ?? '') : undefined"
                      :class="{
                          'text-danger': typeof row[col.key] === 'string' && (row[col.key] as string).includes('逾期'),
                          'text-warning': (col.key === 'attention' && (row[col.key] as string) === '需关注') ||
                               (typeof row[col.key] === 'string' && ((row[col.key] as string).includes('剩余') || (row[col.key] as string).includes('临期') || (row[col.key] as string).includes('今日'))),
                          'text-success': (col.key === 'attention' && (row[col.key] as string) === '正常') ||
                               (typeof row[col.key] === 'string' && (row[col.key] as string) === '正常'),
                        }"
                      >
                        <span v-if="detail.key === 'E02' && col.key === 'mainStatus'" class="status-tag" :class="e02MainStatusClass(row.mainStatus as E02MainStatus)">
                          {{ row.mainStatus }}
                        </span>
                        <span v-else-if="detail.key === 'E02' && col.key === 'deadlineStatus'" class="status-tag" :class="row.overdue ? 'tag-red' : 'tag-normal'">
                          {{ row.deadlineStatus }}
                        </span>
                        <span v-else-if="detail.key === 'E03' && col.key === 'mainStatus'" class="status-tag" :class="e03MainStatusClass(row.mainStatus as E03DetailRow['mainStatus'])">
                          {{ row.mainStatus }}
                        </span>
                        <span v-else-if="detail.key === 'E03' && col.key === 'deadlineStatus'" class="status-tag" :class="row.overdue ? 'tag-red' : 'tag-normal'">
                          {{ row.deadlineStatus }}
                        </span>
                        <span
                          v-else-if="col.key === 'status' || col.key === 'level' || col.key === 'retest'"
                          class="status-tag"
                          :class="detail.key === 'E01' ? e01StatusClass(row[col.key]) : ((typeof row[col.key] === 'string' && (row[col.key] as string).includes('逾期')) ? 'tag-red' : `tag-${detail.theme}`)"
                        >
                          {{ row[col.key] }}
                        </span>
                        <span v-else-if="col.key === 'no'" class="mono-no">{{ row[col.key] }}</span>
                        <span v-else>{{ row[col.key] }}</span>
                      </td>
                    </tr>
                  </template>
                  <tr v-else>
                    <td :colspan="detail.detailColumns.length" class="no-data">
                      {{ detail.key === 'E01' || detail.key === 'E02' || detail.key === 'E03' ? '当前筛选条件下暂无记录' : '暂无符合条件的数据' }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 右侧摘要 -->
        <div class="content-side">
          <!-- E01 复测处置、类别构成与待处理提醒 -->
          <template v-if="detail.key === 'E01'">
            <div class="side-section e01-disposal-section">
              <div class="side-title">复测处置</div>
              <div class="e01-rate-row">
                <span>复测完成率</span>
                <strong>{{ e01CompletionRate }}%</strong>
              </div>
              <div class="e01-progress-track" aria-label="复测完成率">
                <div class="e01-progress-fill" :style="{ width: `${e01CompletionRate}%` }" />
              </div>
              <div class="e01-disposal-list">
                <button type="button" class="e01-disposal-item" :class="{ active: e01StatusFilter === '复测达标' }" @click="toggleE01StatusFilter('复测达标', e01CompletedCount)"><span>已完成复测</span><strong class="green"><span class="e01-disposal-count">{{ e01CompletedCount }}</span><span class="e01-disposal-unit">项</span></strong></button>
                <button type="button" class="e01-disposal-item" :class="{ active: e01StatusFilter === '待复测' }" @click="toggleE01StatusFilter('待复测', e01PendingCount)"><span>待复测</span><strong class="orange"><span class="e01-disposal-count">{{ e01PendingCount }}</span><span class="e01-disposal-unit">项</span></strong></button>
                <button type="button" class="e01-disposal-item" :class="{ active: e01StatusFilter === '复测仍超标' }" :disabled="e01StillExceededCount === 0" @click="toggleE01StatusFilter('复测仍超标', e01StillExceededCount)"><span>复测仍超标</span><strong :class="e01StillExceededCount > 0 ? 'red' : 'green'"><span class="e01-disposal-count">{{ e01StillExceededCount }}</span><span class="e01-disposal-unit">项</span></strong></button>
              </div>
            </div>
            <div class="side-section e01-composition-section">
              <div class="side-title">类别构成</div>
              <div class="ring-wrap">
                <svg v-if="e01CompositionData.length > 0" viewBox="0 0 100 100" class="mini-ring">
                  <circle cx="50" cy="50" r="38" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="12" />
                  <circle
                    v-for="(item, idx) in e01CompositionData"
                    :key="item.name"
                    cx="50"
                    cy="50"
                    r="38"
                    fill="none"
                    :stroke="item.color"
                    stroke-width="12"
                    :stroke-dasharray="`${(item.value / e01CompositionData.reduce((sum, i) => sum + i.value, 0)) * 238.7} 238.7`"
                    stroke-linecap="round"
                    :transform="`rotate(${-90 + (e01CompositionData.slice(0, idx).reduce((sum, i) => sum + i.value, 0) / e01CompositionData.reduce((sum, i) => sum + i.value, 0)) * 360} 50 50)`"
                  />
                  <text x="50" y="43" text-anchor="middle" fill="#e8f3ff" font-size="10.5" font-weight="600">合计</text>
                  <text x="50" y="64" text-anchor="middle" fill="#e8f3ff" font-size="14" font-weight="700">{{ e01CompositionData.reduce((sum, i) => sum + i.value, 0) }}项次</text>
                </svg>
                <div v-if="e01CompositionData.length > 0" class="ring-legend">
                  <div v-for="item in e01CompositionData" :key="item.name" class="ring-legend-item">
                    <i class="dot" :style="{ background: item.color }"></i>{{ item.name }} <span class="num">{{ item.value }}（{{ Math.round((item.value / e01CompositionData.reduce((sum, i) => sum + i.value, 0)) * 100) }}%）</span>
                  </div>
                </div>
                <div v-else class="empty-hint">暂无有效数据</div>
              </div>
            </div>
            <div class="side-section e01-reminder-section">
              <div class="side-title">待处理提醒</div>
              <button v-if="e01PendingReminder" type="button" class="e01-reminder" aria-label="查看并选择待处理的PM10复测记录" @click="handleE01Reminder">
                <div class="e01-reminder-point">{{ e01PendingReminder.point }}</div>
                <div class="e01-reminder-message">PM10超标记录待复测</div>
                <div class="e01-reminder-time">监测时间：{{ e01PendingReminder.time }}</div>
              </button>
              <div v-else class="empty-hint">当前无待处理复测记录</div>
            </div>
          </template>

          <!-- E02 问题类型 -->
          <template v-else-if="detail.key === 'E02'">
            <div class="side-section e02-type-section">
              <div class="side-title">
                <span>问题类型分布</span>
                <small>{{ e02TypeScopeItems.length }}条</small>
              </div>
              <div class="e02-distribution-list">
                <button
                  v-for="t in e02TypeData"
                  :key="t.name"
                  type="button"
                  class="e02-distribution-row"
                  :class="{ active: categoryFilter === t.name }"
                  @click="e02ToggleCategory(t.name)"
                >
                  <span>{{ t.name }}</span>
                  <strong>{{ t.value }}<small>项</small></strong>
                </button>
                <div v-if="e02TypeData.length === 0" class="e02-empty-state">当前筛选下暂无问题类型数据</div>
              </div>
            </div>
            <div class="side-section e02-department-section">
              <div class="side-title">
                <span>责任部门分布</span>
                <small>{{ filteredE02Items.length }}条</small>
              </div>
              <div class="e02-distribution-list">
                <div v-for="item in e02DepartmentData" :key="item.name" class="e02-distribution-row is-static">
                  <span>{{ item.name }}</span>
                  <strong>{{ item.value }}<small>项</small></strong>
                </div>
                <div v-if="e02DepartmentData.length === 0" class="e02-empty-state">当前筛选下暂无责任部门数据</div>
              </div>
            </div>
            <div class="side-section e02-overdue-section">
              <div class="side-title">逾期提醒</div>
              <button
                v-if="e02OverdueReminder"
                type="button"
                class="e02-overdue-reminder"
                aria-label="查看并选中逾期环保问题"
                @click="handleE02OverdueReminder"
              >
                <strong>{{ e02OverdueReminder.name }}</strong>
                <span>责任部门：{{ e02OverdueReminder.department }}</span>
                <span>整改截止：{{ e02OverdueReminder.deadline }}</span>
                <em>已超过整改期限</em>
              </button>
              <div v-else class="e02-overdue-empty" :class="{ 'is-empty-result': filteredE02Items.length === 0 }">
                {{ filteredE02Items.length === 0 ? '当前筛选条件下暂无事项' : '当前筛选下无逾期事项' }}
              </div>
            </div>
          </template>

          <!-- E03 真实问题分布与逾期提醒 -->
          <template v-else-if="detail.key === 'E03'">
            <div class="side-section e03-type-section">
              <div class="side-title"><span>问题类型分布</span><small>{{ filteredE03Items.length }}条</small></div>
              <div class="e03-distribution-list">
                <button v-for="item in e03TypeData" :key="item.name" type="button" class="e03-distribution-row" :class="{ active: e03CategoryFilter === item.name }" @click="toggleE03CategoryFilter(item.name)">
                  <span>{{ item.name }}</span><strong>{{ item.value }}<small>项</small></strong>
                </button>
                <div v-if="e03TypeData.length === 0" class="e03-empty-state">当前筛选下暂无问题类型数据</div>
              </div>
            </div>
            <div class="side-section e03-department-section">
              <div class="side-title"><span>责任部门分布</span><small>{{ filteredE03Items.length }}条</small></div>
              <div class="e03-distribution-list">
                <div v-for="item in e03DepartmentData" :key="item.name" class="e03-distribution-row is-static">
                  <span>{{ item.name }}</span><strong>{{ item.value }}<small>项</small></strong>
                </div>
                <div v-if="e03DepartmentData.length === 0" class="e03-empty-state">当前筛选下暂无责任部门数据</div>
              </div>
            </div>
            <div class="side-section e03-overdue-section">
              <div class="side-title">逾期提醒</div>
              <button v-if="e03OverdueReminder" type="button" class="e03-overdue-reminder" :aria-label="`查看并选中逾期水保问题：${e03OverdueReminder.name}`" @click="handleE03OverdueReminder">
                <strong>{{ e03OverdueReminder.name }}</strong>
                <span>{{ e03OverdueReminder.segment }}</span>
                <span>责任部门：{{ e03OverdueReminder.department }}</span>
                <span>整改截止：{{ e03OverdueReminder.deadline }}</span>
                <em>已超过整改期限<span v-if="e03OtherOverdueCount > 0">，另有{{ e03OtherOverdueCount }}项逾期</span></em>
              </button>
              <div v-else class="e03-overdue-empty" :class="{ 'is-empty-result': filteredE03Items.length === 0 }">
                {{ filteredE03Items.length === 0 ? '当前筛选条件下暂无记录' : '当前筛选下无逾期事项' }}
              </div>
            </div>
          </template>

          <!-- E04 标段对比 -->
          <template v-else-if="detail.key === 'E04'">
            <div class="side-section">
              <div class="side-title">2026年6月标段强度对比</div>
              <div class="type-bar-list">
                <div v-for="(s, idx) in e04SectionRanking" :key="s.name" class="type-bar-item">
                  <span class="type-label" :class="{ 'text-highlight': s.highlight }">{{ s.name }}</span>
                  <div class="type-bar-track">
                    <div class="type-bar-fill" :class="{ 'bar-warning': !s.normal }" :style="{ width: `${(s.value / 0.2) * 100}%` }" />
                  </div>
                  <span class="type-value" :class="{ 'text-warning': !s.normal }">{{ s.value }}</span>
                </div>
              </div>
            </div>
            <div class="alert-banner">
              <AlertTriangle :size="14" />
              <span>K61+800~K65+200 互通段强度较上月上升11.4%，建议重点关注</span>
            </div>
          </template>

          <!-- S01 计数规则 -->
          <template v-else-if="detail.key === 'S01'">
            <div class="side-section">
              <div class="side-title">计数规则摘要</div>
              <ul class="rule-list">
                <li v-for="(r, idx) in s01Rules" :key="idx">{{ r }}</li>
              </ul>
            </div>
          </template>

          <!-- S03 风险等级 -->
          <template v-else-if="detail.key === 'S03'">
            <div class="side-section">
              <div class="side-title">纠纷风险等级（项）</div>
              <div class="type-bar-list">
                <div v-for="t in s03RiskData" :key="t.name" class="type-bar-item">
                  <span class="type-label">{{ t.name }}</span>
                  <div class="type-bar-track">
                    <div class="type-bar-fill" :style="{ width: `${(t.value / 2) * 100}%`, background: t.color }" />
                  </div>
                  <span class="type-value">{{ t.value }}</span>
                </div>
              </div>
            </div>
            <div class="alert-banner">
              <AlertTriangle :size="14" />
              <span>1项群体性风险（工资支付涉及12人），1项逾期</span>
            </div>
          </template>

          <!-- 碳足迹 右侧摘要（仅累计/增益/来源页显示） -->
          <template v-else-if="detail.key === 'CARBON' && ['cumulative', 'benefit', 'source'].includes(activeTab)">
            <div class="side-section">
              <div class="side-title">累计减排量</div>
              <div class="conclusion-grid">
                <div class="conclusion-card">
                  <div class="conclusion-label">核算减排量</div>
                  <div class="conclusion-value" style="color: #69e36f">{{ carbonBenefitData.totalReduction }}<span class="unit">tCO₂e</span></div>
                </div>
                <div class="conclusion-card">
                  <div class="conclusion-label">减排率</div>
                  <div class="conclusion-value" style="color: #2f9cff">{{ carbonBenefitData.reductionRate }}<span class="unit">%</span></div>
                </div>
                <div class="conclusion-card">
                  <div class="conclusion-label">碳汇/抵消</div>
                  <div class="conclusion-value" style="color: #00e5ff">326<span class="unit">tCO₂e</span></div>
                </div>
                <div class="conclusion-card">
                  <div class="conclusion-label">净排放</div>
                  <div class="conclusion-value" style="color: #e8f3ff">12,530<span class="unit">tCO₂e</span></div>
                </div>
              </div>
            </div>
            <div class="alert-banner">
              <AlertTriangle :size="14" />
              <span>实际排放、低碳增益、碳汇/抵消量三者分开核算，不得合并</span>
            </div>
          </template>

          <!-- 月报 右侧摘要（仅进度/缺项页显示） -->
          <template v-else-if="detail.key === 'MONTHLY' && ['progress', 'gaps'].includes(activeTab)">
            <div class="side-section">
              <div class="side-title">待补与校核（按组别）</div>
              <div class="type-bar-list">
                <div v-for="g in monthlyProgressData.groups" :key="g.key" class="type-bar-item" style="cursor: pointer;" @click="monthlyGroupFilter = monthlyGroupFilter === g.key ? 'all' : g.key">
                  <span class="type-label">{{ g.label }}</span>
                  <div class="type-bar-track">
                    <div class="type-bar-fill" :style="{ width: `${g.value}%`, background: g.color }" />
                  </div>
                  <span class="type-value">{{ g.value }}%</span>
                </div>
              </div>
            </div>
            <div class="side-section">
              <div class="side-title">月报章节完成情况</div>
              <div class="warning-list">
                <div v-for="ch in monthlyChaptersData.list" :key="ch.name" class="warning-item">
                  <span class="warning-label">[{{ ch.group }}] {{ ch.name }}</span>
                  <span class="warning-value" :style="{ color: ch.status === '已完成' ? '#69e36f' : ch.status === '数据校核中' ? '#ffb347' : '#ff4f5e' }">{{ ch.status }}</span>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- 底栏 -->
      <div class="modal-footer-info">
        <div class="footer-item">
          <FileCheck :size="12" />
          <span>数据来源：{{ (detail.dataSource || '').split(' ')[0] }}</span>
        </div>
        <div v-if="detail.key === 'E02' && detail.statisticsAsOf" class="footer-item">
          <Clock :size="12" />
          <span>统计时点：{{ detail.statisticsAsOf }}</span>
        </div>
        <div class="footer-item">
          <Clock :size="12" />
          <span>更新时间：{{ detail.updateTime }}</span>
        </div>
        <div v-if="detail.completeness" class="footer-item" :class="detail.completenessStatus">
          <ShieldCheck :size="12" />
          <span>{{ detail.key === 'E01' ? `完整性：${detail.completeness}` : detail.completeness }}</span>
        </div>
        <div v-if="detail.isMock" class="footer-item mock-tag">
          原型示例数据
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="modal-actions">
        <button v-if="detail.key === 'E02' || detail.key === 'E03'" class="btn btn-ghost" :disabled="detail.key === 'E02' ? e02SelectedRow === null : e03SelectedRow === null" @click="handleDetailReserved" :title="detail.key === 'E02' ? (e02SelectedRow === null ? '请先选择事项' : e02ActionTitle) : (e03SelectedRow === null ? '请先选择水保问题' : `已选择“${e03SelectedRow.name}”`)">
          {{ detail.key === 'E03' ? '查看问题详情' : '查看事项详情' }}
        </button>
        <button
          v-if="!isGisViewOnlyKpi"
          class="btn btn-primary"
          :style="detail.key === 'E02' || detail.key === 'E04' ? { background: '#2f9cff', borderColor: '#2f9cff' } : { background: themeColor, borderColor: themeColor }"
          :disabled="(detail.key === 'E01' && !e01CanSupervise) || (detail.key === 'E02' && !e02CanSupervise) || (detail.key === 'E03' && !e03CanOperate) || (detail.key === 'E04' && !e04CanSupervise)"
          :title="detail.key === 'E01' ? e01SuperviseTitle : detail.key === 'E02' ? e02ActionTitle : detail.key === 'E03' ? (e03SelectedRow ? `对“${e03SelectedRow.name}”发起督办` : '请先选择水保问题') : undefined"
          @click="handleSupervise"
        >
          {{ detail.key === 'E01' || detail.key === 'E02' || detail.key === 'E03' ? '发起督办（原型）' : '发起督办' }}
        </button>
        <button class="btn btn-outline" @click="emit('close')">
          关闭
        </button>
      </div>

      <!-- 督办提示 -->
      <Transition name="toast">
        <div v-if="showSuperviseToast" class="supervise-toast">
          <AlertTriangle :size="14" />
          <span>{{ superviseToastMessage }}</span>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/tokens.scss' as *;

.kpi-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(2, 11, 24, 0.72);
  backdrop-filter: blur(4px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 0.2s ease;
}

.kpi-modal-overlay.e01-acceptance-overlay {
  animation: none;
}

.kpi-modal-overlay.e02-acceptance-overlay {
  animation: none;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.kpi-modal {
  width: 68vw;
  max-width: 1280px;
  height: 80vh;
  max-height: 80vh;
  background: linear-gradient(180deg, rgba(7, 22, 44, 0.96) 0%, rgba(5, 18, 38, 0.96) 100%);
  border: 1px solid transparent;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideUp 0.25s ease;
  box-shadow:
    0 0 0 1px rgba(0, 174, 255, 0.3),
    0 20px 60px rgba(0, 0, 0, 0.6);

  &.theme-green {
    border-color: rgba(105, 227, 111, 0.4);
    box-shadow:
      0 0 0 1px rgba(105, 227, 111, 0.35),
      0 20px 60px rgba(0, 0, 0, 0.6);
  }
  &.theme-blue {
    box-shadow:
      0 0 0 1px rgba(47, 156, 255, 0.35),
      0 20px 60px rgba(0, 0, 0, 0.6);
  }
  &.theme-purple {
    box-shadow:
      0 0 0 1px rgba(166, 108, 255, 0.35),
      0 20px 60px rgba(0, 0, 0, 0.6);
  }

  &.is-e01 {
    width: 1436px;
    max-width: none;
    height: 880px;
    max-height: none;
    flex-shrink: 0;
    border-color: rgba(105, 227, 111, 0.35);
    border-radius: 8px;
    outline: none;
    transform: scale(var(--e01-scale, 1));
    transform-origin: center;
    animation: e01Appear 0.2s ease;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);

    &:focus,
    &:focus-visible {
      outline: none;
    }

    .modal-header {
      height: 60px;
      box-sizing: border-box;
      padding: 0 16px;

      .modal-title {
        font-size: 22px;
      }
    }

    .modal-summary {
      gap: 12px;
      padding: 12px 16px;

    .summary-card {
        box-sizing: border-box;
        height: 65px;
        padding: 7px 12px;
        gap: 2px;

        .summary-label {
          overflow: hidden;
          font-size: 14px;
          line-height: 18px;
          white-space: nowrap;
          text-overflow: ellipsis;
        }

        .summary-value-row {
          height: 29px;
          align-items: baseline;
          gap: 5px;

          .summary-value {
            font-size: 28px;
            line-height: 28px;
          }

          .summary-unit {
            font-size: 13px;
            line-height: 16px;
          }
        }
      }
    }

    .modal-content {
      grid-template-columns: minmax(0, 1fr) 300px;
      gap: 12px;
      padding: 0 16px 12px;
    }

    .content-main,
    .content-side {
      gap: 12px;
    }

    .content-side {
      overflow: hidden;
    }

    .chart-section,
    .detail-section,
    .side-section {
      border-color: rgba(105, 227, 111, 0.18);
      border-radius: 6px;
    }

    .chart-section {
      padding: 10px 12px;

      .chart-title {
        font-size: 15px;
      }

      .chart-filters .filter-btn {
        padding: 3px 11px;
        font-size: 13px;
        line-height: 18px;
      }

      .chart-legend {
        gap: 14px;

        .legend-item {
          font-size: 13px;
          line-height: 18px;
        }
      }
    }

    .chart-container {
      height: 180px;
    }

    .modal-footer-info {
      padding-right: 16px;
      padding-left: 16px;
      font-size: 12px;

      .footer-item {
        white-space: nowrap;
      }
    }

    .modal-actions {
      padding: 10px 16px 14px;
    }

    .detail-title,
    .side-title {
      font-size: 15px;
      line-height: 20px;
    }

    .detail-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }

    .e01-detail-filter-summary {
      color: var(--text-muted);
      font-size: 13px;
      font-weight: 500;
      white-space: nowrap;
    }

    &.is-acceptance,
    &.is-acceptance * {
      animation: none !important;
      transition: none !important;
    }
  }

  &.is-e02,
  &.is-e03 {
    width: 1436px;
    max-width: none;
    height: 880px;
    max-height: none;
    flex-shrink: 0;
    border-color: rgba(105, 227, 111, 0.35);
    border-radius: 8px;
    outline: none;
    transform: scale(var(--e02-scale, var(--e03-scale, 1)));
    transform-origin: center;
    animation: e01Appear 0.2s ease;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);

    &:focus,
    &:focus-visible {
      outline: none;
    }

    .modal-header {
      height: 60px;
      box-sizing: border-box;
      padding: 0 16px;

      .modal-title { font-size: 22px; }
    }

    .modal-summary {
      gap: 12px;
      padding: 12px 16px;

      .summary-card {
        box-sizing: border-box;
        height: 65px;
        padding: 7px 12px;
        gap: 2px;

        .summary-label {
          overflow: hidden;
          font-size: 14px;
          line-height: 18px;
          white-space: nowrap;
          text-overflow: ellipsis;
        }

        .summary-value-row {
          height: 29px;
          align-items: baseline;
          gap: 5px;

          .summary-value { font-size: 28px; line-height: 28px; }
          .summary-unit { font-size: 13px; line-height: 16px; }
        }
      }
    }

    .modal-content {
      grid-template-columns: minmax(0, 1fr) 300px;
      gap: 12px;
      padding: 0 16px 12px;
    }

    .content-main,
    .content-side { gap: 12px; }

    .content-side { overflow: hidden; }

    .chart-section,
    .detail-section,
    .side-section {
      border-color: rgba(105, 227, 111, 0.18);
      border-radius: 6px;
    }

    .chart-section {
      padding: 10px 12px;
      .chart-title { font-size: 15px; }
    }

    .chart-container { height: 180px; }

    .detail-title,
    .side-title {
      font-size: 15px;
      line-height: 20px;
    }

    .detail-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }

    .e02-detail-filter-summary,
    .e03-detail-filter-summary {
      color: var(--text-muted);
      font-size: 13px;
      font-weight: 500;
      white-space: nowrap;
    }

    .modal-footer-info {
      padding-right: 16px;
      padding-left: 16px;
      font-size: 12px;
      .footer-item { white-space: nowrap; }
    }

    .modal-actions { padding: 10px 16px 14px; }

    &.is-acceptance,
    &.is-acceptance * {
      animation: none !important;
      transition: none !important;
    }
  }
}

@keyframes e01Appear {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

// Header
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(143, 169, 200, 0.12);
  flex-shrink: 0;
  position: relative;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,229,255,0.4), transparent);
  }

  .modal-title {
    margin: 0;
    font-size: 20px;
    font-weight: 700;
    color: var(--text-main);
    display: flex;
    align-items: center;
    gap: 10px;

    .title-key {
      font-family: var(--font-num);
      font-size: 26px;
      font-weight: 700;
      color: var(--text-main);
      opacity: 0.95;
    }
    .theme-green & .title-key { color: #69e36f; text-shadow: 0 0 8px rgba(105,227,111,0.4); }
    .theme-blue & .title-key { color: #2f9cff; text-shadow: 0 0 8px rgba(47,156,255,0.4); }
    .theme-purple & .title-key { color: #a66cff; text-shadow: 0 0 8px rgba(166,108,255,0.4); }
  }

  .modal-close {
    width: 32px;
    height: 32px;
    border-radius: 4px;
    border: 1px solid var(--border-faint);
    background: rgba(255, 255, 255, 0.03);
    color: var(--text-muted);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s;

    &:hover {
      color: var(--text-main);
      border-color: var(--border-blue-dim);
      background: rgba(255, 79, 94, 0.1);
    }
  }
}

// Summary
.modal-summary {
  display: flex;
  gap: 10px;
  padding: 12px 18px;
  flex-shrink: 0;

  .summary-card {
    flex: 1;
    padding: 10px 14px;
    border: 1px solid var(--border-faint);
    border-radius: 4px;
    background: rgba(255, 255, 255, 0.02);
    display: flex;
    flex-direction: column;
    gap: 4px;
      transition: border-color 0.2s ease, background 0.2s ease;

      &.e02-summary-card {
        width: auto;
        margin: 0;
        color: inherit;
        font: inherit;
        text-align: left;
        cursor: pointer;

        &:hover,
        &:focus-visible {
          background: rgba(47, 156, 255, 0.06);
          border-color: rgba(47, 156, 255, 0.35);
          outline: none;
        }
      }

    .summary-label {
      font-size: 12px;
      color: var(--text-muted);
    }
    .summary-value-row {
      display: flex;
      align-items: baseline;
      gap: 4px;

      .summary-value {
        font-family: var(--font-num);
        font-size: 26px;
        font-weight: 700;
        text-shadow: 0 0 6px currentColor;
        line-height: 1;
      }
      .summary-unit {
        font-size: 11px;
        color: var(--text-muted);
      }
    }

    // E02 可点击指标卡
    &.clickable {
      cursor: pointer;

      &:hover {
        background: rgba(47, 156, 255, 0.06);
        border-color: rgba(47, 156, 255, 0.35);
      }
    }

    &.active {
      background: rgba(47, 156, 255, 0.1);
      border-color: rgba(47, 156, 255, 0.6);
      box-shadow: 0 0 8px rgba(47, 156, 255, 0.25);
    }
  }
}

// E04 指标计算说明
.calc-explanation {
  padding: 8px 18px;
  background: rgba(105, 227, 111, 0.04);
  border-top: 1px solid rgba(105, 227, 111, 0.15);
  border-bottom: 1px solid rgba(105, 227, 111, 0.15);

  .calc-title {
    font-size: 12px;
    color: #69e36f;
    font-weight: 500;
    margin-bottom: 6px;
  }

  .calc-formula {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: var(--text-main);
    margin-bottom: 4px;
    flex-wrap: wrap;

    .calc-term {
      color: var(--text-main);
      font-weight: 500;
    }

    .calc-operator {
      color: #69e36f;
      font-weight: 600;
    }
  }

  .calc-note {
    font-size: 10px;
    color: var(--text-muted);
    margin-top: 4px;
    padding-top: 4px;
    border-top: 1px dashed rgba(143, 169, 200, 0.15);
  }
}

// Content
.modal-content {
  display: grid;
  grid-template-columns: 1fr 260px;
  gap: 12px;
  padding: 0 18px 12px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.content-main {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.content-side {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;

  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-track { background: transparent; }
  &::-webkit-scrollbar-thumb { background: rgba(143,169,200,0.2); border-radius: 2px; }
}

.chart-section {
  border: 1px solid var(--border-faint);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.015);
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
  min-height: 0;
  max-height: 55%;

  .chart-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
  }

  .chart-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-main);
  }

  .chart-filters {
    display: flex;
    gap: 4px;

    .filter-btn {
      padding: 3px 10px;
      font-size: 11px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border-faint);
      border-radius: 3px;
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.15s;

      &:hover {
        color: var(--text-main);
        border-color: var(--border-blue-dim);
      }
      &.active {
        color: var(--text-main);
        border-color: var(--border-blue);
        background: rgba(0, 174, 255, 0.1);
      }
    }
  }

  .chart-legend {
    display: flex;
    gap: 10px;

    .legend-item {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 11px;
      color: var(--text-muted);

      .legend-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;

        &.dust { background: #69e36f; }
        &.noise { background: #2f9cff; }
        &.line { width: 12px; height: 2px; background: #ffffff; border-radius: 0; }
      }
    }
  }
}

.chart-container {
  height: 160px;
  width: 100%;
  flex-shrink: 0;
  min-height: 0;
}

// S02 路线图
.route-map-area {
  position: relative;
  height: 200px;
  border-radius: 3px;
  overflow: hidden;
  background: #031020;

  .route-svg {
    width: 100%;
    height: 100%;
    display: block;
  }

  .route-legend {
    position: absolute;
    bottom: 8px;
    right: 10px;
    display: flex;
    gap: 12px;
    background: rgba(5, 18, 38, 0.8);
    padding: 4px 10px;
    border-radius: 3px;
    border: 1px solid var(--border-faint);

    .legend-item {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 10px;
      color: var(--text-muted);

      .legend-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;

        &.major { background: #ff4f5e; }
        &.bigger { background: #ffb347; }
      }
    }
  }
}

.chart-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  gap: 12px;
  color: var(--text-muted);

  .empty-icon {
    opacity: 0.5;
  }

  .empty-text {
    font-size: 14px;
    font-weight: 600;
  }
}

.e03-route-area {
  position: relative;
  height: 200px;
  border-radius: 3px;
  overflow: hidden;
  background: #031020;

  .route-svg {
    width: 100%;
    height: 100%;
    display: block;
  }

  .route-legend {
    position: absolute;
    bottom: 8px;
    right: 10px;
    display: flex;
    gap: 12px;
    background: rgba(5, 18, 38, 0.8);
    padding: 4px 10px;
    border-radius: 3px;
    border: 1px solid var(--border-faint);

    .legend-item {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 10px;
      color: var(--text-muted);

      .legend-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;

        &.passage { background: #2f9cff; }
        &.noise-dot { background: #ffb347; }
        &.land { background: #a66cff; }
      }
    }
  }
}

// Detail table
.detail-section {
  flex: 1;
  min-height: 0;
  border: 1px solid var(--border-faint);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.015);
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: hidden;

  .focus-banner {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    font-size: 11px;
    color: #2f9cff;
    background: rgba(47, 156, 255, 0.08);
    border: 1px solid rgba(47, 156, 255, 0.25);
    border-radius: 3px;
    flex-shrink: 0;

    &--warn {
      color: #ffb347;
      background: rgba(255, 179, 71, 0.08);
      border-color: rgba(255, 179, 71, 0.25);
    }

    &__hint {
      margin-left: auto;
      font-size: 10px;
      opacity: 0.7;
    }
  }

  .detail-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-main);
    flex-shrink: 0;
  }

  .detail-table-wrapper {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    min-height: 0;

    &::-webkit-scrollbar { width: 4px; }
    &::-webkit-scrollbar-track { background: transparent; }
    &::-webkit-scrollbar-thumb { background: rgba(143,169,200,0.2); border-radius: 2px; }
  }

  .detail-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;

    th {
      position: sticky;
      top: 0;
      background: rgba(5, 18, 38, 0.95);
      color: var(--text-muted);
      font-weight: 500;
      text-align: left;
      padding: 6px 8px;
      border-bottom: 1px solid var(--border-faint);
      white-space: nowrap;
    }

    td {
      padding: 6px 8px;
      color: var(--text-main);
      border-bottom: 1px solid rgba(143, 169, 200, 0.06);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      transition: background 0.15s ease;
    }

    tr:hover td {
      background: rgba(0, 174, 255, 0.04);
    }

    // E02 行选中
    tr.row-selected td {
      background: rgba(47, 156, 255, 0.12) !important;
      box-shadow: inset 2px 0 0 #2f9cff;
    }

    // GIS 关联定位高亮
    tr.row-focused td {
      background: rgba(47, 156, 255, 0.18) !important;
      box-shadow: inset 3px 0 0 #2f9cff, 0 0 12px rgba(47, 156, 255, 0.25);
      animation: focusRowGlow 1.6s ease-out;
    }

    @keyframes focusRowGlow {
      0% { background: rgba(47, 156, 255, 0.35) !important; }
      100% { background: rgba(47, 156, 255, 0.18) !important; }
    }

    .status-tag {
      display: inline-block;
      padding: 1px 6px;
      border-radius: 2px;
      font-size: 10px;
      font-weight: 500;

      &.tag-green {
        color: #69e36f;
        background: rgba(105, 227, 111, 0.12);
        border: 1px solid rgba(105, 227, 111, 0.3);
      }
      &.tag-blue {
        color: #2f9cff;
        background: rgba(47, 156, 255, 0.12);
        border: 1px solid rgba(47, 156, 255, 0.3);
      }
      &.tag-purple {
        color: #a66cff;
        background: rgba(166, 108, 255, 0.12);
        border: 1px solid rgba(166, 108, 255, 0.3);
      }
      &.tag-red {
        color: #ff4f5e;
        background: rgba(255, 79, 94, 0.12);
        border: 1px solid rgba(255, 79, 94, 0.3);
      }
      &.tag-orange {
        color: #ffb347;
        background: rgba(255, 179, 71, 0.12);
        border: 1px solid rgba(255, 179, 71, 0.3);
      }
      &.tag-normal {
        color: #9cc9a3;
        background: rgba(105, 227, 111, 0.07);
        border: 1px solid rgba(105, 227, 111, 0.18);
      }
    }

    &.detail-table--e01 {
      table-layout: fixed;
      font-size: 14px;

      th {
        height: 36px;
        box-sizing: border-box;
        padding: 0 4px;
        font-size: 14px;
        line-height: 36px;
      }

      td {
        height: 38px;
        box-sizing: border-box;
        padding: 0 4px;
        font-size: 14px;
        line-height: 38px;
      }

      .status-tag {
        padding: 2px 7px;
        font-size: 12px;
        line-height: 19px;
      }

      tr.e01-selectable {
        cursor: pointer;

        &:hover td {
          background: rgba(255, 179, 71, 0.045);
        }

        &:focus-visible {
          outline: 1px solid rgba(255, 179, 71, 0.55);
          outline-offset: -1px;
        }
      }

      tr:not(.e01-selectable):hover td {
        background: transparent;
      }

      tr.e01-row-selected td {
        background: rgba(255, 179, 71, 0.08);

        &:first-child {
          box-shadow: inset 2px 0 0 #ffb347;
        }
      }
    }

    &.detail-table--e02 {
      table-layout: fixed;
      font-size: 14px;

      th {
        height: 36px;
        box-sizing: border-box;
        padding: 0 4px;
        font-size: 14px;
        line-height: 36px;
      }

      td {
        height: 38px;
        box-sizing: border-box;
        padding: 0 4px;
        font-size: 14px;
        line-height: 38px;
      }

      .status-tag {
        padding: 2px 7px;
        font-size: 12px;
        line-height: 19px;
      }

      tr.e02-selectable {
        cursor: pointer;

        &:focus-visible {
          outline: 1px solid rgba(47, 156, 255, 0.55);
          outline-offset: -1px;
        }
      }

      tr.row-selected td {
        box-shadow: none;

        &:first-child { box-shadow: inset 2px 0 0 #2f9cff; }
      }
    }

    &.detail-table--e03 {
      table-layout: fixed;
      font-size: 14px;

      th {
        height: 36px;
        box-sizing: border-box;
        padding: 0 4px;
        font-size: 14px;
        line-height: 36px;
      }

      td {
        height: 38px;
        box-sizing: border-box;
        padding: 0 4px;
        font-size: 14px;
        line-height: 38px;
      }

      .status-tag {
        padding: 2px 7px;
        font-size: 12px;
        line-height: 19px;
      }

      tr.e03-selectable {
        cursor: pointer;

        &:focus-visible {
          outline: 1px solid rgba(105, 227, 111, 0.55);
          outline-offset: -1px;
        }
      }

      tr.e03-row-selected td {
        background: rgba(105, 227, 111, 0.08) !important;
        box-shadow: none;
        &:first-child { box-shadow: inset 2px 0 0 #69e36f; }
      }

      tr.e03-row-selected.e03-row-overdue td {
        background: rgba(255, 79, 94, 0.08) !important;
        &:first-child { box-shadow: inset 2px 0 0 #ff4f5e; }
      }
    }

    .mono-no {
      font-family: var(--font-num);
      font-size: 11px;
    }

    .text-danger { color: #ff4f5e; }
    .text-warning { color: #ffb347; }
    .text-success { color: #69e36f; }
    .no-data { text-align: center; color: var(--text-faint); padding: 20px; }
  }
}

// Side
.side-section {
  border: 1px solid var(--border-faint);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.015);
  padding: 10px 12px;

  .side-title {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-main);
    margin-bottom: 8px;
  }
}

.is-e02 {
  .e02-type-section { flex: 0 0 214px; }
  .e02-department-section { flex: 0 0 146px; }
  .e02-overdue-section { flex: 1; min-height: 0; }

  .chart-section { position: relative; }

  .e02-active-filter {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 3px 8px;
    border: 1px solid rgba(47, 156, 255, 0.22);
    border-radius: 3px;
    background: rgba(47, 156, 255, 0.06);
    color: var(--text-muted);
    font-size: 13px;
    line-height: 18px;
    white-space: nowrap;

    strong { color: #69e36f; font-weight: 600; }

    button {
      margin: 0;
      padding: 0;
      border: 0;
      background: transparent;
      color: #2f9cff;
      font: inherit;
      cursor: pointer;

      &:hover,
      &:focus-visible { color: #8ecaff; outline: none; }
    }
  }

  .e02-chart-empty {
    position: absolute;
    top: 44px;
    right: 18px;
    z-index: 2;
    padding: 4px 9px;
    border-radius: 3px;
    background: rgba(143, 169, 200, 0.07);
    color: var(--text-muted);
    font-size: 12px;
    line-height: 18px;
    pointer-events: none;
  }

  .side-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;

    > small {
      color: var(--text-muted);
      font-size: 12px;
      font-weight: 500;
    }
  }

  .e02-distribution-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .e02-distribution-row {
    width: 100%;
    min-height: 28px;
    box-sizing: border-box;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin: 0;
    padding: 3px 8px;
    border: 1px solid transparent;
    border-radius: 3px;
    background: rgba(255, 255, 255, 0.018);
    color: var(--text-main);
    font-size: 13px;
    line-height: 20px;
    text-align: left;
    cursor: pointer;

    &:hover,
    &:focus-visible,
    &.active {
      border-color: rgba(105, 227, 111, 0.32);
      background: rgba(105, 227, 111, 0.07);
      outline: none;
    }

    &.is-static {
      cursor: default;
      &:hover { border-color: transparent; background: rgba(255, 255, 255, 0.018); }
    }

    strong {
      min-width: 38px;
      color: #e8f3ff;
      font-family: var(--font-num);
      font-size: 18px;
      line-height: 20px;
      text-align: right;
    }

    small {
      margin-left: 2px;
      color: var(--text-muted);
      font-family: inherit;
      font-size: 12px;
      font-weight: 400;
    }
  }

  .e02-overdue-reminder {
    width: 100%;
    min-height: 120px;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
    box-sizing: border-box;
    padding: 10px 12px;
    border: 1px solid rgba(255, 79, 94, 0.32);
    border-radius: 4px;
    background: rgba(255, 79, 94, 0.07);
    color: var(--text-main);
    font: inherit;
    text-align: left;
    cursor: pointer;

    &:hover,
    &:focus-visible {
      border-color: rgba(255, 79, 94, 0.58);
      background: rgba(255, 79, 94, 0.11);
      outline: none;
    }

    strong { font-size: 14px; line-height: 20px; }
    span { color: #b8cce3; font-size: 13px; line-height: 18px; }
    em { color: #ff6b78; font-size: 13px; font-style: normal; font-weight: 600; line-height: 18px; }
  }

  .e02-empty-state,
  .e02-overdue-empty {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 54px;
    padding: 8px;
    box-sizing: border-box;
    border: 1px dashed rgba(143, 169, 200, 0.14);
    border-radius: 3px;
    color: var(--text-muted);
    font-size: 13px;
    line-height: 20px;
    text-align: center;
  }

  .e02-overdue-empty {
    min-height: 96px;
    color: #9cc9a3;

    &.is-empty-result { color: var(--text-muted); }
  }

  .supervise-toast span { white-space: pre-line; }
}

.is-e03 {
  .chart-section { position: relative; max-height: none; }
  &.kpi-modal .chart-container { height: 194px; }
  .e03-type-section { flex: 1 1 auto; min-height: 0; }
  .e03-department-section { flex: 0 0 96px; }
  .e03-overdue-section { flex: 0 0 162px; }

  .detail-table-wrapper {
    scrollbar-width: thin;
    scrollbar-color: rgba(143, 169, 200, 0.52) rgba(143, 169, 200, 0.08);

    &::-webkit-scrollbar { width: 8px; }
    &::-webkit-scrollbar-track {
      background: rgba(143, 169, 200, 0.08);
      border-radius: 4px;
    }
    &::-webkit-scrollbar-thumb {
      min-height: 28px;
      border: 2px solid transparent;
      border-radius: 4px;
      background: rgba(143, 169, 200, 0.52);
      background-clip: padding-box;
    }
    &::-webkit-scrollbar-thumb:hover { background: rgba(143, 169, 200, 0.72); background-clip: padding-box; }
  }

  .e03-active-filter {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 3px 8px;
    border: 1px solid rgba(105, 227, 111, 0.22);
    border-radius: 3px;
    background: rgba(105, 227, 111, 0.06);
    color: var(--text-muted);
    font-size: 13px;
    line-height: 18px;
    white-space: nowrap;

    strong { color: #69e36f; font-weight: 600; }

    button {
      margin: 0;
      padding: 0;
      border: 0;
      background: transparent;
      color: #69e36f;
      font: inherit;
      cursor: pointer;
      &:hover,
      &:focus-visible { color: #b6f4ba; outline: none; }
    }
  }

  .e03-filter-panel {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 4px 8px;
    border: 1px solid rgba(105, 227, 111, 0.14);
    border-radius: 4px;
    background: rgba(105, 227, 111, 0.025);
  }

  .e03-filter-group {
    display: flex;
    align-items: center;
    gap: 4px;
    min-width: 0;

    > span {
      width: 62px;
      flex: 0 0 62px;
      color: #b8cce3;
      font-size: 12px;
      font-weight: 600;
    }

    button {
      min-width: 44px;
      height: 22px;
      padding: 0 8px;
      border: 1px solid rgba(143, 169, 200, 0.18);
      border-radius: 3px;
      background: rgba(255, 255, 255, 0.025);
      color: var(--text-muted);
      font-size: 12px;
      line-height: 20px;
      cursor: pointer;

      &:hover,
      &:focus-visible,
      &.active {
        border-color: rgba(105, 227, 111, 0.42);
        background: rgba(105, 227, 111, 0.09);
        color: #e8f3ff;
        outline: none;
      }
    }
  }

  .e03-chart-empty {
    position: absolute;
    top: 118px;
    right: 18px;
    z-index: 2;
    padding: 4px 9px;
    border-radius: 3px;
    background: rgba(143, 169, 200, 0.08);
    color: var(--text-muted);
    font-size: 12px;
    line-height: 18px;
    pointer-events: none;
  }

  .side-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    > small { color: var(--text-muted); font-size: 12px; font-weight: 500; }
  }

  .e03-distribution-list {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .e03-distribution-row {
    width: 100%;
    min-height: 25px;
    box-sizing: border-box;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin: 0;
    padding: 2px 8px;
    border: 1px solid transparent;
    border-radius: 3px;
    background: rgba(255, 255, 255, 0.018);
    color: var(--text-main);
    font-size: 13px;
    line-height: 19px;
    text-align: left;
    cursor: pointer;

    &:hover,
    &:focus-visible,
    &.active {
      border-color: rgba(105, 227, 111, 0.32);
      background: rgba(105, 227, 111, 0.07);
      outline: none;
    }

    &.is-static {
      cursor: default;
      &:hover { border-color: transparent; background: rgba(255, 255, 255, 0.018); }
    }

    strong {
      min-width: 38px;
      color: #e8f3ff;
      font-family: var(--font-num);
      font-size: 18px;
      line-height: 20px;
      text-align: right;
    }

    small {
      margin-left: 2px;
      color: var(--text-muted);
      font-family: inherit;
      font-size: 12px;
      font-weight: 400;
    }
  }

  .e03-overdue-reminder {
    width: 100%;
    min-height: 126px;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
    box-sizing: border-box;
    padding: 9px 11px;
    border: 1px solid rgba(255, 79, 94, 0.32);
    border-radius: 4px;
    background: rgba(255, 79, 94, 0.07);
    color: var(--text-main);
    font: inherit;
    text-align: left;
    cursor: pointer;

    &:hover,
    &:focus-visible {
      border-color: rgba(255, 79, 94, 0.58);
      background: rgba(255, 79, 94, 0.11);
      outline: none;
    }

    strong { font-size: 14px; line-height: 20px; }
    span { color: #b8cce3; font-size: 13px; line-height: 17px; }
    em { color: #ff6b78; font-size: 13px; font-style: normal; font-weight: 600; line-height: 18px; }
  }

  .e03-empty-state,
  .e03-overdue-empty {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 52px;
    padding: 8px;
    box-sizing: border-box;
    border: 1px dashed rgba(143, 169, 200, 0.14);
    border-radius: 3px;
    color: var(--text-muted);
    font-size: 13px;
    line-height: 20px;
    text-align: center;
  }

  .e03-overdue-empty {
    min-height: 116px;
    color: #9cc9a3;
    &.is-empty-result { color: var(--text-muted); }
  }
}

.conclusion-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;

  .conclusion-card {
    padding: 8px;
    border: 1px solid var(--border-faint);
    border-radius: 3px;
    background: rgba(255, 255, 255, 0.02);
    text-align: center;

    .conclusion-label {
      font-size: 10px;
      color: var(--text-muted);
      margin-bottom: 2px;
    }
    .conclusion-value {
      font-family: var(--font-num);
      font-size: 18px;
      font-weight: 700;
      text-shadow: 0 0 4px currentColor;

      .unit {
        font-size: 10px;
        font-weight: 400;
        text-shadow: none;
        margin-left: 2px;
        color: var(--text-muted);
      }
    }
  }
}

.ring-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;

  .mini-ring {
    width: 100px;
    height: 100px;
  }

  .ring-legend {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 3px;

    .ring-legend-item {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 10px;
      color: var(--text-muted);

      .dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        display: inline-block;

        &.green { background: #69e36f; }
        &.blue { background: #2f9cff; }
        &.purple { background: #a66cff; }
        &.cyan { background: #00e5ff; }
      }

      .num {
        margin-left: auto;
        color: var(--text-main);
        font-family: var(--font-num);
      }
    }
  }
}

.e01-disposal-section {
  .e01-rate-row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    color: var(--text-muted);
    font-size: 13px;
    line-height: 22px;

    strong {
      color: #69e36f;
      font-family: var(--font-num);
      font-size: 26px;
      line-height: 1;
    }
  }

  .e01-progress-track {
    height: 7px;
    margin: 9px 0 10px;
    overflow: hidden;
    border-radius: 4px;
    background: rgba(255, 255, 255, 0.07);
  }

  .e01-progress-fill {
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, rgba(105, 227, 111, 0.65), #69e36f);
  }

  .e01-disposal-list {
    display: flex;
    flex-direction: column;
    gap: 0;

    .e01-disposal-item {
      display: flex;
      width: 100%;
      padding: 0 4px;
      align-items: center;
      justify-content: space-between;
      border: 0;
      border-radius: 3px;
      outline: none;
      background: transparent;
      color: var(--text-muted);
      font-size: 13px;
      line-height: 23px;
      text-align: left;
      cursor: pointer;

      &:hover:not(:disabled),
      &:focus-visible {
        background: rgba(47, 156, 255, 0.08);
      }

      &.active {
        background: rgba(47, 156, 255, 0.12);
        box-shadow: inset 2px 0 0 #2f9cff;
      }

      &:disabled {
        cursor: default;
        opacity: 0.75;
      }
    }

    strong {
      display: inline-flex;
      width: 52px;
      align-items: baseline;
      justify-content: flex-end;
      font-family: var(--font-num);
      font-weight: 600;
      text-align: right;
    }

    .e01-disposal-count {
      font-size: 18px;
      line-height: 20px;
    }

    .e01-disposal-unit {
      margin-left: 3px;
      font-family: inherit;
      font-size: 12px;
      font-weight: 500;
      line-height: 16px;
    }
    .green { color: #69e36f; }
    .orange { color: #ffb347; }
    .red { color: #ff4f5e; }
  }
}

.e01-composition-section {
  flex: 1;
  min-height: 0;

  .ring-wrap {
    flex-direction: row;
    justify-content: center;
    gap: 18px;
    height: calc(100% - 22px);
  }

  .ring-wrap .mini-ring {
    width: 116px;
    height: 116px;
    flex: 0 0 116px;
  }

  .ring-wrap .ring-legend {
    width: 120px;
    gap: 8px;

    .ring-legend-item {
      gap: 7px;
      font-size: 13px;
      line-height: 20px;
    }
  }
}

.e01-reminder-section {
  .e01-reminder {
    display: block;
    width: 100%;
    padding: 10px 12px;
    border: 0;
    border-left: 2px solid #ffb347;
    border-radius: 3px;
    outline: none;
    background: rgba(255, 179, 71, 0.06);
    text-align: left;
    cursor: pointer;
    transition: background 0.15s ease, border-color 0.15s ease;

    &:hover,
    &:focus-visible {
      border-left-color: #ffd08a;
      background: rgba(255, 179, 71, 0.12);
    }
  }

  .e01-reminder-point {
    color: var(--text-main);
    font-size: 14px;
    line-height: 19px;
    font-weight: 600;
  }

  .e01-reminder-message {
    margin-top: 6px;
    color: #ffb347;
    font-size: 13px;
    line-height: 18px;
  }

  .e01-reminder-time {
    margin-top: 5px;
    color: var(--text-muted);
    font-size: 12px;
    line-height: 17px;
  }
}

.type-bar-list {
  display: flex;
  flex-direction: column;
  gap: 6px;

  .type-bar-item {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 2px 4px;
    border-radius: 3px;
    transition: background 0.2s ease;

    .type-label {
      font-size: 11px;
      color: var(--text-muted);
      width: 60px;
      flex-shrink: 0;
    }
    .type-bar-track {
      flex: 1;
      height: 5px;
      background: rgba(255, 255, 255, 0.06);
      border-radius: 3px;
      overflow: hidden;

      .type-bar-fill {
        height: 100%;
        background: #2f9cff;
        border-radius: 3px;
        transition: width 0.3s ease;
      }
    }
    .type-value {
      font-size: 11px;
      color: var(--text-main);
      width: 16px;
      text-align: right;
      font-family: var(--font-num);
    }

    // E02 类型筛选激活
    &.active {
      background: rgba(47, 156, 255, 0.12);
      box-shadow: inset 0 0 0 1px rgba(47, 156, 255, 0.5);

      .type-label {
        color: #2f9cff;
      }
    }
  }
}

.alert-banner {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  background: rgba(255, 79, 94, 0.08);
  border: 1px solid rgba(255, 79, 94, 0.25);
  border-radius: 3px;
  font-size: 11px;
  color: #ff8a94;

  &.purple {
    background: rgba(166, 108, 255, 0.08);
    border-color: rgba(166, 108, 255, 0.25);
    color: #c79eff;
  }

  // E02 无逾期时的正常状态
  &.green {
    background: rgba(105, 227, 111, 0.08);
    border-color: rgba(105, 227, 111, 0.25);
    color: #69e36f;
  }
}

.warning-list {
  display: flex;
  flex-direction: column;
  gap: 6px;

  .warning-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 5px 8px;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 3px;
    font-size: 11px;

    .warning-label { color: var(--text-muted); }
    .warning-value {
      color: var(--text-main);
      font-family: var(--font-num);
      font-weight: 600;
    }
  }
}

// S01 时间轴和月度状态
.s01-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;

  .s01-timeline {
    flex-shrink: 0;
    height: 100px;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 3px;
    border: 1px solid var(--border-faint);

    .timeline-svg {
      width: 100%;
      height: 100%;
      display: block;
    }
  }

  .s01-monthly {
    flex: 1;
    min-height: 0;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 3px;
    border: 1px solid var(--border-faint);
    padding: 8px 10px;

    .monthly-title {
      font-size: 11px;
      font-weight: 600;
      color: var(--text-main);
      margin-bottom: 6px;
    }

    .monthly-grid {
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 6px;
      height: calc(100% - 24px);
      overflow-y: auto;
      overflow-x: hidden;

      &::-webkit-scrollbar { width: 4px; }
      &::-webkit-scrollbar-track { background: transparent; }
      &::-webkit-scrollbar-thumb { background: rgba(143,169,200,0.2); border-radius: 2px; }
    }

    .month-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2px;
      padding: 4px;
      background: rgba(255, 255, 255, 0.02);
      border-radius: 2px;

      .month-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;

        &.status-normal { background: #69e36f; box-shadow: 0 0 4px rgba(105,227,111,0.4); }
        &.status-warning { background: #ffb347; box-shadow: 0 0 4px rgba(255,179,71,0.4); }
        &.status-danger { background: #ff4f5e; box-shadow: 0 0 4px rgba(255,79,94,0.4); }
      }

      .month-label {
        font-size: 9px;
        color: var(--text-muted);
        white-space: nowrap;
      }

      .month-status {
        font-size: 9px;
        color: #69e36f;
      }
    }
  }
}

// E04 高亮样式
.text-highlight {
  color: #69e36f !important;
  font-weight: 600;
}

.bar-warning {
  background: #ff4f5e !important;
}

// S01 规则列表
.rule-list {
  margin: 0;
  padding-left: 16px;
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.6;

  li {
    margin-bottom: 4px;

    &:last-child { margin-bottom: 0; }
  }
}

// Footer info
.modal-footer-info {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 8px 18px;
  border-top: 1px solid rgba(143, 169, 200, 0.1);
  background: rgba(255, 255, 255, 0.01);
  flex-shrink: 0;
  font-size: 11px;
  color: var(--text-faint);

  .footer-item {
    display: flex;
    align-items: center;
    gap: 4px;

    &.complete { color: #69e36f; }
    &.incomplete { color: #ffb347; }
    &.pending { color: var(--text-faint); }
  }

  .mock-tag {
    margin-left: auto;
    padding: 2px 8px;
    background: rgba(255, 179, 71, 0.1);
    border: 1px solid rgba(255, 179, 71, 0.25);
    border-radius: 2px;
    color: #ffb347;
    font-size: 10px;
  }
}

// Actions
.modal-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 12px 18px 16px;
  flex-shrink: 0;

  .btn {
    padding: 8px 24px;
    font-size: 14px;
    font-weight: 500;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
    min-width: 140px;
    height: 36px;

    &:active:not(:disabled) {
      transform: scale(0.97);
      transition-duration: 0.08s;
    }

    &:disabled {
      opacity: 0.45;
      cursor: not-allowed;
    }
  }
  .btn-ghost {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border-faint);
    color: var(--text-muted);

    &:hover:not(:disabled) {
      border-color: var(--border-blue-dim);
      color: var(--text-main);
    }
  }
  .btn-primary {
    border: 1px solid;
    color: #02111f;
    font-weight: 600;

    &:hover:not(:disabled) { opacity: 0.9; }
  }
  .btn-outline {
    background: transparent;
    border: 1px solid var(--border-blue-dim);
    color: var(--text-main);

    &:hover {
      border-color: var(--border-blue);
      background: rgba(0, 174, 255, 0.06);
    }
  }
}

// 专题标签页
.modal-tabs {
  display: flex;
  gap: 4px;
  padding: 0 18px 10px;
  border-bottom: 1px solid rgba(143, 169, 200, 0.08);
  flex-shrink: 0;

  .tab-btn {
    padding: 4px 14px;
    font-size: 12px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border-faint);
    border-radius: 3px;
    color: var(--text-muted);
    cursor: pointer;
    transition: all 0.15s;

    &:hover {
      color: var(--text-main);
      border-color: var(--border-blue-dim);
    }

    &.active {
      color: var(--text-main);
      border-color: var(--border-blue);
      background: rgba(0, 174, 255, 0.1);
    }
  }
}

// 专题文本内容
.topic-text-content {
  padding: 10px 12px;
  border: 1px solid var(--border-faint);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.015);

  // 月报章节清单和缺项清单完整表格
  &.full-height-table {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    display: flex;
    flex-direction: column;

    &::-webkit-scrollbar { width: 4px; }
    &::-webkit-scrollbar-track { background: transparent; }
    &::-webkit-scrollbar-thumb { background: rgba(143,169,200,0.2); border-radius: 2px; }

    .detail-table {
      flex: 1;
      th { position: sticky; top: 0; }
    }
  }

  .topic-metric-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-bottom: 10px;

    .topic-metric-card {
      padding: 10px;
      border: 1px solid var(--border-faint);
      border-radius: 3px;
      background: rgba(255, 255, 255, 0.02);
      text-align: center;

      .topic-metric-label {
        font-size: 11px;
        color: var(--text-muted);
        margin-bottom: 4px;
      }

      .topic-metric-value {
        font-family: var(--font-num);
        font-size: 20px;
        font-weight: 700;
        text-shadow: 0 0 4px currentColor;

        .unit {
          font-size: 10px;
          font-weight: 400;
          text-shadow: none;
          margin-left: 2px;
          color: var(--text-muted);
        }
      }
    }
  }

  .topic-note {
    padding: 8px 10px;
    background: rgba(255, 255, 255, 0.02);
    border-radius: 3px;
    border: 1px solid var(--border-faint);
    margin-bottom: 6px;

    &.warning {
      border-color: rgba(255, 179, 71, 0.25);
      color: #ffb347;
    }

    .topic-note-title {
      font-size: 11px;
      font-weight: 600;
      color: var(--text-main);
      margin-bottom: 4px;
    }

    .topic-note-text {
      font-size: 11px;
      color: var(--text-muted);
      line-height: 1.5;
    }
  }
}

// 专题措施内容
.topic-measures-content {
  border: 1px solid var(--border-faint);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.015);
  padding: 10px 12px;
  overflow-y: auto;

  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-track { background: transparent; }
  &::-webkit-scrollbar-thumb { background: rgba(143,169,200,0.2); border-radius: 2px; }
}

// 月报状态链
.monthly-status-chain {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 10px 12px;
  border: 1px solid var(--border-faint);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.015);
  flex-shrink: 0;

  .chain-node {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    position: relative;

    &:not(:last-child)::after {
      content: '';
      position: absolute;
      top: 6px;
      right: -50%;
      width: 100%;
      height: 2px;
      background: rgba(143, 169, 200, 0.15);
    }

    &.done::after {
      background: #69e36f;
    }

    &.current::after {
      background: linear-gradient(90deg, #2f9cff, rgba(143, 169, 200, 0.15));
    }

    .chain-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: rgba(143, 169, 200, 0.2);
      margin-bottom: 6px;
      position: relative;
      z-index: 1;
    }

    &.done .chain-dot {
      background: #69e36f;
      box-shadow: 0 0 4px rgba(105, 227, 111, 0.4);
    }

    &.current .chain-dot {
      background: #2f9cff;
      box-shadow: 0 0 4px rgba(47, 156, 255, 0.4);
    }

    &.pending .chain-dot {
      background: rgba(143, 169, 200, 0.2);
    }

    .chain-label {
      font-size: 10px;
      color: var(--text-muted);
      white-space: nowrap;
    }

    &.done .chain-label { color: #69e36f; }
    &.current .chain-label { color: #2f9cff; font-weight: 600; }
  }
}

// ── Toast 过渡动画 ──
.toast-enter-active {
  transition: opacity 0.25s ease, transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.toast-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
