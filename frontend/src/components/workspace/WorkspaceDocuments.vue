<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  Search,
  FileText,
  Link2,
  Tag,
  Clock,
  User,
  Folder,
  History,
  RefreshCw,
  Shield,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Hash,
  FileCheck2,
  FileType,
  RotateCcw,
  Filter,
} from 'lucide-vue-next'
import {
  documents as mockDocuments,
} from '@/data/workspace.mock'
import type { StatusCard, Document as DocumentType, DocumentVersion, DocumentRelatedTask } from '@/types/workspace'

const activeLeftTab = ref<'esg' | 'type'>('esg')
const selectedCategory = ref('全部资料')
const selectedType = ref('')
const typeSearchKeyword = ref('')
const searchKeyword = ref('')
const selectedCycle = ref('')
const selectedModule = ref('')
const selectedSource = ref('')
const selectedStatus = ref('')
const selectedRelation = ref('')
const documentList = ref<DocumentType[]>([...mockDocuments])
const selectedDoc = ref<DocumentType>({ ...mockDocuments[0] })
const pageMessage = ref('')
const pageMessageType = ref<'info' | 'success' | 'error'>('info')
const activeDetailTab = ref<'detail' | 'version' | 'relation'>('detail')
const currentPage = ref(1)
const pageSize = ref(10)

const statusCards = computed<StatusCard[]>(() => {
  const total = documentList.value.length
  const monthNew = documentList.value.filter(d => d.uploadTime?.startsWith('2026-08')).length
  const pendingArchive = documentList.value.filter(d => d.source === '审核归档' && d.status !== '已失效').length
  const expiringSoon = documentList.value.filter(d => d.status === '即将失效').length
  return [
    { label: '资料总数', value: total, unit: '份', color: '#69e36f' },
    { label: '本月新增', value: monthNew, unit: '份', color: '#2f9cff' },
    { label: '待归档', value: pendingArchive, unit: '份', color: '#ffb347' },
    { label: '即将失效', value: expiringSoon, unit: '份', color: '#ff4f5e' },
  ]
})

const sourceOptions = ['智能入库', '任务上传', '审核归档', '系统生成', '历史迁移']
const cycleOptions = ['2026-07', '2026-08', '2026-Q2', '2026年度', '2025年度']
const moduleOptions = [
  { label: '全部', value: '' },
  { label: 'E 环境环保', value: 'E' },
  { label: 'S 社会责任', value: 'S' },
  { label: 'G 治理合规', value: 'G' },
]
const statusOptions = ['有效', '即将失效', '已失效']
const relationOptions = ['关联KPI指标', '关联月报', '关联业务事项', '关联上传任务']

const esgCategories = [
  { label: '全部资料', value: 'all', color: '#69e36f' },
  { label: '环境环保', value: 'E', color: '#69e36f' },
  { label: '社会责任', value: 'S', color: '#2f9cff' },
  { label: '治理合规', value: 'G', color: '#a66cff' },
  { label: '综合/月报资料', value: 'comprehensive', color: '#ffb347' },
]

const computedEsgCategories = computed(() => {
  const total = documentList.value.length
  const counts: Record<string, number> = { E: 0, S: 0, G: 0 }
  let comprehensive = 0
  for (const doc of documentList.value) {
    if (doc.module === 'E' || doc.module === 'S' || doc.module === 'G') {
      counts[doc.module]++
    } else {
      comprehensive++
    }
  }
  return [
    { label: '全部资料', value: 'all', color: '#69e36f', count: total },
    { label: '环境环保', value: 'E', color: '#69e36f', count: counts.E },
    { label: '社会责任', value: 'S', color: '#2f9cff', count: counts.S },
    { label: '治理合规', value: 'G', color: '#a66cff', count: counts.G },
    { label: '综合/月报资料', value: 'comprehensive', color: '#ffb347', count: comprehensive },
  ]
})

const computedTypes = computed(() => {
  const map = new Map<string, number>()
  for (const doc of documentList.value) {
    map.set(doc.type, (map.get(doc.type) || 0) + 1)
  }
  const types = Array.from(map.entries()).map(([label, value]) => ({ label, value }))
  if (typeSearchKeyword.value) {
    return types.filter(t => t.label.includes(typeSearchKeyword.value))
  }
  return types
})

const filteredDocuments = computed(() => {
  return documentList.value.filter(doc => {
    if (selectedCategory.value !== '全部资料') {
      if (selectedCategory.value === '综合/月报资料') {
        if (doc.module === 'E' || doc.module === 'S' || doc.module === 'G') return false
      } else {
        const cat = esgCategories.find(c => c.label === selectedCategory.value)
        if (cat && cat.value !== 'all' && doc.module !== cat.value) return false
      }
    }
    if (selectedType.value && doc.type !== selectedType.value) return false
    if (searchKeyword.value && !doc.name.includes(searchKeyword.value)) return false
    if (selectedCycle.value && doc.cycle !== selectedCycle.value) return false
    if (selectedModule.value && doc.module !== selectedModule.value) return false
    if (selectedSource.value && doc.source !== selectedSource.value) return false
    if (selectedStatus.value && doc.status !== selectedStatus.value) return false
    return true
  })
})

const totalRecords = computed(() => filteredDocuments.value.length)
const totalPages = computed(() => Math.max(1, Math.ceil(totalRecords.value / pageSize.value)))

const paginatedDocuments = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredDocuments.value.slice(start, start + pageSize.value)
})

function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

function changePageSize(size: number) {
  pageSize.value = size
  currentPage.value = 1
}

function getPageNumbers(): number[] {
  const pages: number[] = []
  const maxPages = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxPages / 2))
  let end = Math.min(totalPages.value, start + maxPages - 1)
  if (end - start + 1 < maxPages) {
    start = Math.max(1, end - maxPages + 1)
  }
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
}

watch([selectedCategory, selectedType, searchKeyword, selectedCycle, selectedModule, selectedSource, selectedStatus, selectedRelation], () => {
  currentPage.value = 1
})

function getModuleColor(module?: string) {
  switch (module) {
    case 'E':
      return '#69e36f'
    case 'S':
      return '#2f9cff'
    case 'G':
      return '#a66cff'
    default:
      return '#8fa9c8'
  }
}

function getModuleName(module?: string) {
  switch (module) {
    case 'E':
      return '环境环保'
    case 'S':
      return '社会责任'
    case 'G':
      return '治理合规'
    default:
      return '综合'
  }
}

function getStatusColor(status: string) {
  switch (status) {
    case '有效':
      return '#69e36f'
    case '即将失效':
      return '#ffb347'
    case '已失效':
      return '#ff4f5e'
    default:
      return '#8fa9c8'
  }
}

function getSourceColor(source: string) {
  switch (source) {
    case '智能入库':
      return '#69e36f'
    case '任务上传':
      return '#2f9cff'
    case '审核归档':
      return '#a66cff'
    case '系统生成':
      return '#ffb347'
    case '历史迁移':
      return '#8fa9c8'
    default:
      return '#8fa9c8'
  }
}

function handleCardClick(cardLabel: string) {
  switch (cardLabel) {
    case '资料总数':
      selectedStatus.value = ''
      selectedCategory.value = '全部资料'
      break
    case '本月新增':
      selectedStatus.value = ''
      break
    case '待归档':
      selectedSource.value = '审核归档'
      break
    case '即将失效':
      selectedStatus.value = '即将失效'
      break
  }
}

function handleCategoryClick(label: string) {
  selectedCategory.value = label
}

function handleTypeClick(label: string) {
  selectedType.value = selectedType.value === label ? '' : label
}

function handleReset() {
  searchKeyword.value = ''
  selectedCycle.value = ''
  selectedModule.value = ''
  selectedSource.value = ''
  selectedStatus.value = ''
  selectedRelation.value = ''
  selectedCategory.value = '全部资料'
  selectedType.value = ''
}

function handleSelectDocument(doc: DocumentType) {
  selectedDoc.value = { ...doc }
  activeDetailTab.value = 'detail'
}

function handlePreview() {
  showMessage('文件预览功能为原型预留，暂未接入真实文件预览服务。', 'info')
}

function showMessage(message: string, type: 'info' | 'success' | 'error' = 'info') {
  pageMessage.value = message
  pageMessageType.value = type
  setTimeout(() => {
    pageMessage.value = ''
  }, 3000)
}

const groupedRelations = computed(() => {
  const tasks = selectedDoc.value?.relatedTasks || []
  const groups: Record<string, DocumentRelatedTask[]> = {
    'KPI指标': [],
    '月报': [],
    '业务事项': [],
    '上传任务': [],
  }
  for (const task of tasks) {
    if (groups[task.type]) {
      groups[task.type].push(task)
    }
  }
  const totalRefs = tasks.reduce((sum, t) => sum + t.referenceCount, 0)
  return { groups, totalRefs }
})

const currentVersion = computed(() => {
  return selectedDoc.value?.versions?.find(v => v.isCurrent)
})

const historyVersions = computed(() => {
  return selectedDoc.value?.versions?.filter(v => !v.isCurrent) || []
})
</script>

<template>
  <div class="workspace-documents ws-page">
    <div v-if="pageMessage" :class="['ws-page-message', pageMessageType]">
      {{ pageMessage }}
    </div>

    <div class="ws-status-cards cols-4">
      <div
        v-for="card in statusCards"
        :key="card.label"
        class="ws-status-card with-icon"
        :style="{ '--accent-color': card.color }"
        @click="handleCardClick(card.label)"
      >
        <div class="ws-card-icon">
          <Folder v-if="card.label === '资料总数'" :size="18" />
          <RefreshCw v-else-if="card.label === '本月新增'" :size="18" />
          <Clock v-else-if="card.label === '待归档'" :size="18" />
          <AlertTriangle v-else-if="card.label === '即将失效'" :size="18" />
        </div>
        <div class="ws-card-body">
          <div class="ws-card-label">{{ card.label }}</div>
          <div class="ws-card-value-row">
            <span class="ws-card-value">{{ card.value }}</span>
            <span class="ws-card-unit">{{ card.unit }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="main-content">
      <div class="left-sidebar">
        <div class="sidebar-tabs">
          <button
            :class="{ active: activeLeftTab === 'esg' }"
            @click="activeLeftTab = 'esg'"
          >
            按ESG分类
          </button>
          <button
            :class="{ active: activeLeftTab === 'type' }"
            @click="activeLeftTab = 'type'"
          >
            按资料类型
          </button>
        </div>

        <div v-show="activeLeftTab === 'esg'" class="sidebar-content">
          <div class="category-list">
            <button
              v-for="cat in computedEsgCategories"
              :key="cat.label"
              :class="{ active: selectedCategory === cat.label }"
              @click="handleCategoryClick(cat.label)"
            >
              <span class="category-dot" :style="{ background: cat.color }"></span>
              <span class="category-name">{{ cat.label }}</span>
              <span class="category-count">{{ cat.count }}</span>
            </button>
          </div>
        </div>

        <div v-show="activeLeftTab === 'type'" class="sidebar-content">
          <div class="type-search-box">
            <Search :size="14" />
            <input v-model="typeSearchKeyword" type="text" placeholder="搜索类型..." />
          </div>
          <div class="type-list-wrapper">
            <div class="type-list">
              <button
                v-for="type in computedTypes"
                :key="type.label"
                :class="{ active: selectedType === type.label }"
                @click="handleTypeClick(type.label)"
              >
                <FileType :size="14" class="type-icon" />
                <span class="type-name">{{ type.label }}</span>
                <span class="type-count">{{ type.value }}</span>
              </button>
            </div>
          </div>
          <div class="type-footer">
            共 {{ computedTypes.length }} 种类型
          </div>
        </div>
      </div>

      <div class="middle-section">
        <div class="ws-filter-bar filter-bar">
          <div class="ws-filter-row filter-row">
            <div class="ws-search-box search-box">
              <Search :size="16" />
              <input v-model="searchKeyword" type="text" placeholder="请输入资料名称" />
            </div>
            <div class="filter-group">
              <span class="filter-label">资料周期</span>
              <select v-model="selectedCycle">
                <option value="">全部</option>
                <option v-for="c in cycleOptions" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
            <div class="filter-group">
              <span class="filter-label">ESG模块</span>
              <select v-model="selectedModule">
                <option v-for="m in moduleOptions" :key="m.value" :value="m.value">{{ m.label }}</option>
              </select>
            </div>
          </div>
          <div class="ws-filter-row filter-row">
            <div class="filter-group">
              <span class="filter-label">来源</span>
              <select v-model="selectedSource">
                <option value="">全部</option>
                <option v-for="s in sourceOptions" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
            <div class="filter-group">
              <span class="filter-label">有效状态</span>
              <select v-model="selectedStatus">
                <option value="">全部</option>
                <option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
            <div class="filter-group">
              <span class="filter-label">关联指标/任务</span>
              <select v-model="selectedRelation">
                <option value="">全部</option>
                <option v-for="r in relationOptions" :key="r" :value="r">{{ r }}</option>
              </select>
            </div>
            <div class="filter-actions">
              <button class="ws-btn ws-btn-secondary" @click="handleReset">
                <RotateCcw :size="14" />
                重置
              </button>
              <button class="ws-btn ws-btn-primary">
                <Filter :size="14" />
                筛选
              </button>
            </div>
          </div>
        </div>

        <div class="ws-table-container">
          <div class="ws-table-scroll" :class="{ 'no-scroll': pageSize <= 10 }">
            <table class="ws-table">
              <colgroup>
                <col class="col-name" />
                <col class="col-type" />
                <col class="col-module" />
                <col class="col-cycle" />
                <col class="col-version" />
                <col class="col-source" />
                <col class="col-related" />
                <col class="col-status" />
                <col class="col-action" />
              </colgroup>
              <thead>
                <tr>
                  <th class="col-name">资料名称</th>
                  <th class="col-type">资料类型</th>
                  <th class="col-module">ESG模块</th>
                  <th class="col-cycle">资料周期</th>
                  <th class="col-version">当前版本</th>
                  <th class="col-source">来源</th>
                  <th class="col-related">关联数量</th>
                  <th class="col-status">有效状态</th>
                  <th class="col-action">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="doc in paginatedDocuments"
                  :key="doc.id"
                  :class="{ selected: selectedDoc?.id === doc.id }"
                  @click="handleSelectDocument(doc)"
                >
                  <td class="col-name">
                    <FileText :size="16" class="doc-icon" />
                    <span class="doc-name-text">{{ doc.name }}</span>
                  </td>
                  <td class="col-type">{{ doc.type }}</td>
                  <td class="col-module">
                    <span
                      class="module-tag"
                      :style="{ background: `${getModuleColor(doc.module)}20`, color: getModuleColor(doc.module) }"
                    >
                      {{ getModuleName(doc.module) }}
                    </span>
                  </td>
                  <td class="col-cycle">{{ doc.cycle }}</td>
                  <td class="col-version">
                    <span class="version-tag">{{ doc.version }}</span>
                  </td>
                  <td class="col-source">
                    <span
                      class="source-tag"
                      :style="{ background: `${getSourceColor(doc.source)}20`, color: getSourceColor(doc.source) }"
                    >
                      {{ doc.source }}
                    </span>
                  </td>
                  <td class="col-related">
                    <span class="related-count">
                      <Link2 :size="12" />
                      {{ doc.relatedTaskCount }}
                    </span>
                  </td>
                  <td class="col-status">
                    <span class="status-tag" :style="{ color: getStatusColor(doc.status) }">
                      <span class="status-dot" :style="{ background: getStatusColor(doc.status) }"></span>
                      {{ doc.status }}
                    </span>
                  </td>
                  <td class="col-action">
                    <div class="action-cell">
                      <button class="action-btn preview-btn" @click.stop="handlePreview">
                        预览
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="ws-pagination-bar">
          <div class="ws-pagination-info">
            共 <span class="highlight">{{ totalRecords }}</span> 条记录，第 {{ currentPage }}/{{ totalPages }} 页
          </div>
          <div class="ws-pagination-controls">
            <button class="ws-page-btn" :disabled="currentPage === 1" @click="goToPage(currentPage - 1)">上一页</button>
            <button
              v-for="p in getPageNumbers()"
              :key="p"
              class="ws-page-btn"
              :class="{ active: currentPage === p }"
              @click="goToPage(p)"
            >
              {{ p }}
            </button>
            <button class="ws-page-btn" :disabled="currentPage === totalPages" @click="goToPage(currentPage + 1)">下一页</button>
            <select v-model.number="pageSize" class="ws-page-size-select" @change="changePageSize(pageSize)">
              <option :value="10">10条/页</option>
              <option :value="20">20条/页</option>
              <option :value="30">30条/页</option>
            </select>
          </div>
        </div>
      </div>

      <div class="right-sidebar">
        <div class="ws-detail-panel">
          <div class="card-header">
            <div class="card-tabs">
              <button
                :class="{ active: activeDetailTab === 'detail' }"
                @click="activeDetailTab = 'detail'"
              >
                资料详情
              </button>
              <button
                :class="{ active: activeDetailTab === 'version' }"
                @click="activeDetailTab = 'version'"
              >
                版本管理
              </button>
              <button
                :class="{ active: activeDetailTab === 'relation' }"
                @click="activeDetailTab = 'relation'"
              >
                关联关系
              </button>
            </div>
          </div>

          <div v-show="activeDetailTab === 'detail'" class="ws-detail-content">
            <div class="current-file">
              <div class="file-icon-wrapper">
                <FileText :size="28" class="file-icon" />
              </div>
              <div class="file-info">
                <span class="file-name">{{ selectedDoc?.name }}</span>
                <div class="file-meta">
                  <span class="meta-item">
                    <Hash :size="12" />
                    {{ selectedDoc?.size }}
                  </span>
                  <span class="meta-item">
                    <FileCheck2 :size="12" />
                    {{ selectedDoc?.format }}
                  </span>
                </div>
              </div>
            </div>

            <div class="ws-detail-section">
              <div class="ws-section-title">基本信息</div>
              <div class="detail-grid">
                <div class="detail-item">
                  <span class="item-label">资料类型</span>
                  <span class="item-value">{{ selectedDoc?.type }}</span>
                </div>
                <div class="detail-item">
                  <span class="item-label">ESG模块</span>
                  <span
                    class="item-value module-badge"
                    :style="{ background: `${getModuleColor(selectedDoc?.module)}20`, color: getModuleColor(selectedDoc?.module) }"
                  >
                    {{ getModuleName(selectedDoc?.module) }}
                  </span>
                </div>
                <div class="detail-item">
                  <span class="item-label">资料周期</span>
                  <span class="item-value">{{ selectedDoc?.cycle }}</span>
                </div>
                <div class="detail-item">
                  <span class="item-label">文件大小</span>
                  <span class="item-value">{{ selectedDoc?.size }}</span>
                </div>
                <div class="detail-item">
                  <span class="item-label">文件格式</span>
                  <span class="item-value">{{ selectedDoc?.format }}</span>
                </div>
                <div class="detail-item">
                  <span class="item-label">当前版本</span>
                  <span class="item-value version-highlight">{{ selectedDoc?.version }}</span>
                </div>
                <div class="detail-item">
                  <span class="item-label">上传人</span>
                  <span class="item-value">{{ selectedDoc?.creator }}</span>
                </div>
                <div class="detail-item">
                  <span class="item-label">上传时间</span>
                  <span class="item-value">{{ selectedDoc?.uploadTime }}</span>
                </div>
                <div class="detail-item">
                  <span class="item-label">来源</span>
                  <span
                    class="item-value source-badge"
                    :style="{ background: `${getSourceColor(selectedDoc?.source || '')}20`, color: getSourceColor(selectedDoc?.source || '') }"
                  >
                    {{ selectedDoc?.source }}
                  </span>
                </div>
                <div class="detail-item">
                  <span class="item-label">有效期</span>
                  <span class="item-value" :style="{ color: getStatusColor(selectedDoc?.status || '') }">
                    {{ selectedDoc?.validPeriod }}
                  </span>
                </div>
              </div>
            </div>

            <div class="ws-detail-section">
              <div class="ws-section-title">
                <Tag :size="14" />
                AI识别标签
              </div>
              <div class="tags-list">
                <span v-for="tag in selectedDoc?.tags" :key="tag" class="tag-item">{{ tag }}</span>
              </div>
            </div>

            <div class="ws-detail-section">
              <div class="ws-section-title">
                <Shield :size="14" />
                哈希查重状态
              </div>
              <div class="hash-status" :class="{ unique: selectedDoc?.isUnique }">
                <div class="hash-icon">
                  <CheckCircle v-if="selectedDoc?.isUnique" :size="20" />
                  <XCircle v-else :size="20" />
                </div>
                <div class="hash-info">
                  <div class="hash-title">
                    {{ selectedDoc?.isUnique ? '唯一文件，未发现重复' : '检测到重复文件' }}
                  </div>
                  <div class="hash-value">{{ selectedDoc?.fileHash }}</div>
                </div>
              </div>
            </div>
          </div>

          <div v-show="activeDetailTab === 'version'" class="ws-detail-content">
            <div v-if="currentVersion" class="current-version-card">
              <div class="version-header">
                <span class="version-label">当前有效版本</span>
                <span class="version-badge current">{{ currentVersion.version }}</span>
              </div>
              <div class="version-info">
                <div class="version-row">
                  <span class="row-label">上传人</span>
                  <span class="row-value">{{ currentVersion.uploader }}</span>
                </div>
                <div class="version-row">
                  <span class="row-label">上传时间</span>
                  <span class="row-value">{{ currentVersion.uploadTime }}</span>
                </div>
                <div class="version-row">
                  <span class="row-label">变更说明</span>
                  <span class="row-value">{{ currentVersion.changeDesc }}</span>
                </div>
                <div class="version-row">
                  <span class="row-label">审核状态</span>
                  <span class="row-value status-text">
                    <span class="status-dot success"></span>
                    {{ currentVersion.reviewStatus }}
                  </span>
                </div>
              </div>
            </div>

            <div class="history-versions-section">
              <div class="ws-section-title">
                <History :size="14" />
                历史版本
              </div>
              <div class="history-list">
                <div
                  v-for="(ver, index) in historyVersions"
                  :key="ver.version"
                  class="history-item"
                >
                  <div class="history-timeline">
                    <div class="timeline-dot"></div>
                    <div v-if="index < historyVersions.length - 1" class="timeline-line"></div>
                  </div>
                  <div class="history-content">
                    <div class="history-header">
                      <span class="history-version">{{ ver.version }}</span>
                      <span class="history-status">{{ ver.reviewStatus }}</span>
                    </div>
                    <div class="history-meta">
                      <span class="meta-item">
                        <User :size="12" />
                        {{ ver.uploader }}
                      </span>
                      <span class="meta-item">
                        <Clock :size="12" />
                        {{ ver.uploadTime }}
                      </span>
                    </div>
                    <div class="history-desc">{{ ver.changeDesc }}</div>
                  </div>
                </div>
                <div v-if="!historyVersions.length" class="empty-history">
                  暂无历史版本
                </div>
              </div>
            </div>
          </div>

          <div v-show="activeDetailTab === 'relation'" class="ws-detail-content">
            <div class="relation-summary">
              <div class="summary-item">
                <span class="summary-value">{{ selectedDoc?.relatedTasks?.length || 0 }}</span>
                <span class="summary-label">关联总数</span>
              </div>
              <div class="summary-divider"></div>
              <div class="summary-item">
                <span class="summary-value highlight">{{ groupedRelations.totalRefs }}</span>
                <span class="summary-label">被引用次数</span>
              </div>
            </div>

            <div class="relation-groups">
              <div class="relation-group">
                <div class="group-header">
                  <span class="group-icon kpi-icon">📊</span>
                  <span class="group-title">关联KPI指标</span>
                  <span class="group-count">{{ groupedRelations.groups['KPI指标']?.length || 0 }}</span>
                </div>
                <div class="group-list">
                  <div
                    v-for="item in groupedRelations.groups['KPI指标']"
                    :key="item.name"
                    class="group-item"
                  >
                    <span
                      class="module-badge"
                      :style="{ background: `${getModuleColor(item.module)}20`, color: getModuleColor(item.module) }"
                    >
                      {{ item.module }}
                    </span>
                    <span class="item-name">{{ item.name }}</span>
                    <span class="item-refs">引用 {{ item.referenceCount }} 次</span>
                  </div>
                  <div v-if="!groupedRelations.groups['KPI指标']?.length" class="empty-group">
                    暂无关联
                  </div>
                </div>
              </div>

              <div class="relation-group">
                <div class="group-header">
                  <span class="group-icon report-icon">📑</span>
                  <span class="group-title">关联月报</span>
                  <span class="group-count">{{ groupedRelations.groups['月报']?.length || 0 }}</span>
                </div>
                <div class="group-list">
                  <div
                    v-for="item in groupedRelations.groups['月报']"
                    :key="item.name"
                    class="group-item"
                  >
                    <span
                      class="module-badge"
                      :style="{ background: `${getModuleColor(item.module)}20`, color: getModuleColor(item.module) }"
                    >
                      {{ item.module }}
                    </span>
                    <span class="item-name">{{ item.name }}</span>
                    <span class="item-refs">引用 {{ item.referenceCount }} 次</span>
                  </div>
                  <div v-if="!groupedRelations.groups['月报']?.length" class="empty-group">
                    暂无关联
                  </div>
                </div>
              </div>

              <div class="relation-group">
                <div class="group-header">
                  <span class="group-icon biz-icon">📋</span>
                  <span class="group-title">关联业务事项</span>
                  <span class="group-count">{{ groupedRelations.groups['业务事项']?.length || 0 }}</span>
                </div>
                <div class="group-list">
                  <div
                    v-for="item in groupedRelations.groups['业务事项']"
                    :key="item.name"
                    class="group-item"
                  >
                    <span
                      class="module-badge"
                      :style="{ background: `${getModuleColor(item.module)}20`, color: getModuleColor(item.module) }"
                    >
                      {{ item.module }}
                    </span>
                    <span class="item-name">{{ item.name }}</span>
                    <span class="item-refs">引用 {{ item.referenceCount }} 次</span>
                  </div>
                  <div v-if="!groupedRelations.groups['业务事项']?.length" class="empty-group">
                    暂无关联
                  </div>
                </div>
              </div>

              <div class="relation-group">
                <div class="group-header">
                  <span class="group-icon task-icon">📤</span>
                  <span class="group-title">关联上传任务</span>
                  <span class="group-count">{{ groupedRelations.groups['上传任务']?.length || 0 }}</span>
                </div>
                <div class="group-list">
                  <div
                    v-for="item in groupedRelations.groups['上传任务']"
                    :key="item.name"
                    class="group-item"
                  >
                    <span
                      class="module-badge"
                      :style="{ background: `${getModuleColor(item.module)}20`, color: getModuleColor(item.module) }"
                    >
                      {{ item.module }}
                    </span>
                    <span class="item-name">{{ item.name }}</span>
                    <span class="item-refs">引用 {{ item.referenceCount }} 次</span>
                  </div>
                  <div v-if="!groupedRelations.groups['上传任务']?.length" class="empty-group">
                    暂无关联
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workspace-documents {
  min-height: 0;
}

.main-content {
  display: flex;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.left-sidebar {
  width: 200px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: rgba(5, 26, 50, 0.8);
  border: 1px solid rgba(105, 227, 111, 0.1);
  border-radius: 10px;
  overflow: hidden;
}

.sidebar-tabs {
  display: flex;
  border-bottom: 1px solid rgba(105, 227, 111, 0.1);
  flex-shrink: 0;
}

.sidebar-tabs button {
  flex: 1;
  padding: 10px 8px;
  background: transparent;
  border: none;
  color: #8fa9c8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
}

.sidebar-tabs button.active {
  color: #69e36f;
  border-bottom-color: #69e36f;
  background: rgba(105, 227, 111, 0.08);
}

.sidebar-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.category-list {
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-list button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #e8f3ff;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.category-list button:hover {
  background: rgba(105, 227, 111, 0.08);
}

.category-list button.active {
  background: rgba(105, 227, 111, 0.15);
}

.category-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.category-name {
  flex: 1;
}

.category-count {
  font-size: 11px;
  color: #8fa9c8;
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
}

.type-search-box {
  padding: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid rgba(105, 227, 111, 0.08);
  color: #8fa9c8;
  flex-shrink: 0;
}

.type-search-box input {
  flex: 1;
  background: transparent;
  border: none;
  color: #e8f3ff;
  font-size: 12px;
  outline: none;
}

.type-list-wrapper {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.type-list {
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.type-list button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #e8f3ff;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.type-list button:hover {
  background: rgba(105, 227, 111, 0.08);
}

.type-list button.active {
  background: rgba(105, 227, 111, 0.15);
  color: #69e36f;
}

.type-icon {
  color: #8fa9c8;
  flex-shrink: 0;
}

.type-list button.active .type-icon {
  color: #69e36f;
}

.type-name {
  flex: 1;
}

.type-count {
  font-size: 11px;
  color: #8fa9c8;
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
}

.type-footer {
  padding: 8px 10px;
  text-align: center;
  font-size: 11px;
  color: #5a7a9a;
  border-top: 1px solid rgba(105, 227, 111, 0.08);
  flex-shrink: 0;
}

.middle-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.middle-section > .ws-table-container {
  flex: 1 1 auto;
  min-height: 0;
}

.middle-section > .ws-table-container + .ws-pagination-bar {
  flex: 0 0 auto;
  margin-top: 0;
}

.filter-bar {
  /* chrome from .ws-filter-bar */
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.search-box {
  /* size only; chrome from .ws-search-box */
  min-width: 220px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 12px;
  color: #8fa9c8;
  white-space: nowrap;
}

.filter-group select {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(105, 227, 111, 0.2);
  border-radius: 4px;
  padding: 6px 10px;
  color: #e8f3ff;
  font-size: 12px;
  outline: none;
  min-width: 110px;
  cursor: pointer;
}

.filter-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.reset-btn,
.filter-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-btn {
  background: rgba(105, 227, 111, 0.08);
  border: 1px solid rgba(105, 227, 111, 0.2);
  color: #8fa9c8;
}

.reset-btn:hover {
  border-color: rgba(105, 227, 111, 0.4);
  color: #69e36f;
}

.filter-btn {
  background: linear-gradient(135deg, #69e36f 0%, #2f9cff 100%);
  border: none;
  color: #031020;
  font-weight: 600;
}

.filter-btn:hover {
  opacity: 0.9;
}

.col-name {
  width: auto;
}

.col-type {
  width: 100px;
}

.col-module {
  width: 120px;
}

.col-cycle {
  width: 110px;
}

.col-version {
  width: 88px;
}

.col-source {
  width: 90px;
}

.col-related {
  width: 88px;
}

.col-status {
  width: 96px;
}

.col-action {
  width: 88px;
  min-width: 88px;
  position: relative;
}

.doc-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.doc-icon {
  color: #8fa9c8;
  flex-shrink: 0;
}

.doc-name-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.module-tag,
.source-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.version-tag {
  display: inline-block;
  padding: 2px 6px;
  background: rgba(166, 108, 255, 0.15);
  color: #a66cff;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.related-count {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #2f9cff;
  font-size: 12px;
}

.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.action-cell {
  display: inline-flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 2px;
  white-space: nowrap;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 4px 6px;
  background: transparent;
  border: none;
  color: #8fa9c8;
  font-size: 12px;
  line-height: 1.2;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
  white-space: nowrap;
  flex-shrink: 0;
}

.action-btn:hover {
  color: #69e36f;
  background: rgba(105, 227, 111, 0.1);
}

.preview-btn {
  color: #2f9cff;
}

.preview-btn:hover {
  color: #5fb4ff;
  background: rgba(47, 156, 255, 0.1);
}

.right-sidebar {
  width: 30%;
  min-width: 320px;
  max-width: 420px;
  flex-shrink: 0;
}

.card-header {
  padding: 0;
  border-bottom: 1px solid rgba(105, 227, 111, 0.1);
  flex-shrink: 0;
}

.card-tabs {
  display: flex;
}

.card-tabs button {
  flex: 1;
  padding: 12px 8px;
  background: transparent;
  border: none;
  color: #8fa9c8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
}

.card-tabs button.active {
  color: #69e36f;
  border-bottom-color: #69e36f;
  background: rgba(105, 227, 111, 0.08);
}

.current-file {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  margin-bottom: 12px;
}

.file-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: rgba(105, 227, 111, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #69e36f;
  flex-shrink: 0;
}

.file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.file-name {
  font-size: 13px;
  color: #e8f3ff;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  display: flex;
  gap: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #8fa9c8;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.item-label {
  font-size: 11px;
  color: #5a7a9a;
}

.item-value {
  font-size: 12px;
  color: #e8f3ff;
}

.item-value.module-badge,
.item-value.source-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
  width: fit-content;
}

.version-highlight {
  color: #a66cff;
  font-weight: 600;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-item {
  padding: 4px 10px;
  background: rgba(47, 156, 255, 0.15);
  border: 1px solid rgba(47, 156, 255, 0.3);
  border-radius: 4px;
  font-size: 11px;
  color: #2f9cff;
}

.hash-status {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 79, 94, 0.1);
  border: 1px solid rgba(255, 79, 94, 0.2);
  border-radius: 6px;
}

.hash-status.unique {
  background: rgba(105, 227, 111, 0.1);
  border-color: rgba(105, 227, 111, 0.2);
}

.hash-icon {
  flex-shrink: 0;
  color: #ff4f5e;
}

.hash-status.unique .hash-icon {
  color: #69e36f;
}

.hash-info {
  flex: 1;
  min-width: 0;
}

.hash-title {
  font-size: 12px;
  color: #e8f3ff;
  font-weight: 500;
  margin-bottom: 4px;
}

.hash-value {
  font-size: 11px;
  color: #8fa9c8;
  font-family: monospace;
}

.current-version-card {
  background: linear-gradient(135deg, rgba(105, 227, 111, 0.15) 0%, rgba(47, 156, 255, 0.1) 100%);
  border: 1px solid rgba(105, 227, 111, 0.3);
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 16px;
}

.version-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(105, 227, 111, 0.15);
}

.version-label {
  font-size: 12px;
  color: #8fa9c8;
}

.version-badge {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 700;
  background: rgba(105, 227, 111, 0.2);
  color: #69e36f;
}

.version-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.version-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.row-label {
  font-size: 12px;
  color: #8fa9c8;
}

.row-value {
  font-size: 12px;
  color: #e8f3ff;
}

.status-text {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot.success {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #69e36f;
}

.history-list {
  display: flex;
  flex-direction: column;
}

.history-item {
  display: flex;
  gap: 12px;
}

.history-timeline {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 16px;
  flex-shrink: 0;
}

.timeline-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #8fa9c8;
  border: 2px solid rgba(5, 26, 50, 0.8);
  margin-top: 4px;
}

.timeline-line {
  width: 1px;
  flex: 1;
  background: rgba(105, 227, 111, 0.15);
  min-height: 30px;
}

.history-content {
  flex: 1;
  padding-bottom: 16px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.history-version {
  font-size: 13px;
  font-weight: 600;
  color: #e8f3ff;
}

.history-status {
  font-size: 11px;
  padding: 2px 8px;
  background: rgba(255, 179, 71, 0.15);
  color: #ffb347;
  border-radius: 4px;
}

.history-meta {
  display: flex;
  gap: 12px;
  margin-bottom: 6px;
}

.history-meta .meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #8fa9c8;
}

.history-desc {
  font-size: 12px;
  color: #a8c0d8;
  line-height: 1.5;
}

.empty-history {
  padding: 30px;
  text-align: center;
  color: #5a7a9a;
  font-size: 12px;
}

.relation-summary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  margin-bottom: 16px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.summary-value {
  font-size: 24px;
  font-weight: 700;
  color: #e8f3ff;
  line-height: 1;
}

.summary-value.highlight {
  color: #69e36f;
}

.summary-label {
  font-size: 12px;
  color: #8fa9c8;
}

.summary-divider {
  width: 1px;
  height: 36px;
  background: rgba(105, 227, 111, 0.15);
}

.relation-groups {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.relation-group {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(105, 227, 111, 0.08);
}

.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(105, 227, 111, 0.06);
  border-bottom: 1px solid rgba(105, 227, 111, 0.08);
}

.group-icon {
  font-size: 14px;
}

.group-title {
  flex: 1;
  font-size: 12px;
  color: #e8f3ff;
  font-weight: 500;
}

.group-count {
  font-size: 11px;
  color: #8fa9c8;
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 8px;
  border-radius: 10px;
}

.group-list {
  padding: 8px;
}

.group-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  transition: background 0.2s;
}

.group-item:hover {
  background: rgba(105, 227, 111, 0.06);
}

.group-item .module-badge {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  flex-shrink: 0;
}

.item-name {
  flex: 1;
  font-size: 12px;
  color: #e8f3ff;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-refs {
  font-size: 11px;
  color: #2f9cff;
  flex-shrink: 0;
}

.empty-group {
  padding: 16px;
  text-align: center;
  color: #5a7a9a;
  font-size: 12px;
}
</style>
