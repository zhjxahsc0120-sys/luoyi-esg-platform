<script setup lang="ts">
import { computed } from 'vue';
import type { FeatureRelation, PresentationMode, TrafficMapFeature } from '../types';

const props = withDefaults(defineProps<{
  feature: TrafficMapFeature;
  presentationMode?: PresentationMode;
  relations?: FeatureRelation[];
  relationsLoading?: boolean;
}>(), {
  presentationMode: 'preview',
  relationsLoading: false,
});

defineEmits<{ close: []; loadRelations: []; loadBusinessLinks: [] }>();

const STATUS_LABELS: Record<string, string> = {
  normal: '正常',
  attention: '关注',
  warning: '预警',
  critical: '预警',
  offline: '离线',
};

const isDashboard = computed(() => props.presentationMode === 'dashboard');
const isCritical = computed(() =>
  props.feature.status === 'critical' || ['超标', '逾期', '严重'].includes(displayStatus.value),
);

function isAlertRow(label: string, value: string) {
  if (!isCritical.value) return false;
  return ['检测结果', '判定结果', '当前状态', '预警状态', '逾期天数', '风险等级'].some(key =>
    label.includes(key),
  ) || ['超标', '逾期', '异常', '严重'].some(key => value.includes(key));
}

const displayStatus = computed(() => {
  const f = props.feature;
  if (f.statusLabel) return f.statusLabel;
  if (f.businessSummary?.statusLabel) return f.businessSummary.statusLabel;
  if (f.status) return STATUS_LABELS[f.status] || f.status;
  return '正常';
});

const headerTitle = computed(() => {
  if (isDashboard.value && props.feature.businessSummary?.title) {
    return props.feature.businessSummary.title;
  }
  const type = props.feature.objectType;
  if (type === 'road-section') return '施工标段概览';
  if (['water-source', 'ecological-zone', 'spoil-site'].includes(type)) return '环保区域概览';
  if (['slope-monitor', 'risk-point'].includes(type)) return '风险监测概览';
  if (type === 'environment-monitor') return '环境监测详情';
  return '空间要素详情';
});

const dashboardRows = computed(() => {
  if (props.feature.businessSummary?.dashboardRows?.length) {
    return props.feature.businessSummary.dashboardRows;
  }
  const p = props.feature.properties;
  const type = props.feature.objectType;
  if (type === 'road-section') {
    return [
      { label: '建设进度', value: String(p['建设进度'] || '—') },
      { label: '环保问题', value: String(p['环保问题'] || '—') },
      { label: '风险点', value: String(p['风险点'] || '—') },
      { label: '计划完工', value: String(p['计划完工'] || '—') },
    ];
  }
  if (['water-source', 'ecological-zone', 'spoil-site'].includes(type)) {
    return [
      { label: '当前状态', value: String(p['当前状态'] || p['status'] || '正常管控') },
      { label: '最近巡查', value: String(p['最近巡查'] || '—') },
      { label: '责任单位', value: String(p['责任单位'] || '—') },
    ];
  }
  if (['slope-monitor', 'risk-point'].includes(type)) {
    return [
      { label: '设备状态', value: String(p['设备状态'] || '在线') },
      { label: '预警状态', value: String(p['预警状态'] || '正常') },
      { label: '数据更新', value: String(p['数据更新时间'] || p['updatedAt'] || '—') },
    ];
  }
  if (type === 'environment-monitor') {
    return [
      { label: '监测因子', value: String(p['监测因子'] || '—') },
      { label: '检测结果', value: `${String(p['检测值'] ?? '—')} ${String(p['单位'] || '')}`.trim() },
      { label: '标准限值', value: `${String(p['标准限值'] ?? '—')} ${String(p['单位'] || '')}`.trim() },
      { label: '判定结果', value: String(p['判定结果'] || displayStatus.value) },
      { label: '标段 / 桩号', value: `${String(p['标段'] || '—')} / ${String(p['桩号'] || '—')}` },
      { label: '采样日期', value: String(p['采样日期'] || '—') },
      { label: '经纬度', value: `${String(p['经度'] || '—')}, ${String(p['纬度'] || '—')}` },
      { label: '报告编号', value: String(p['报告编号'] || '—') },
      { label: '未闭环问题', value: String(p['未闭环问题'] || '无') },
      { label: '闭环状态', value: String(p['闭环状态'] || '—') },
    ];
  }
  return [];
});

const dashboardNote = computed(() => {
  if (props.feature.businessSummary?.dashboardNote) {
    return props.feature.businessSummary.dashboardNote;
  }
  const type = props.feature.objectType;
  if (type === 'road-section') {
    return '当前标段处于主体施工阶段，环保问题和风险点均纳入台账跟踪。';
  }
  if (['water-source', 'ecological-zone', 'spoil-site'].includes(type)) {
    return '该区域已纳入环保敏感点管控，后续与巡查记录、问题闭环数据联动。';
  }
  if (['slope-monitor', 'risk-point'].includes(type)) {
    return '当前监测点持续纳入风险预警范围，异常变化将同步进入风险督办链路。';
  }
  if (type === 'environment-monitor') {
    return displayStatus.value === '超标'
      ? '该点位检测结果超过标准限值，已纳入 E01 环境异常跟踪。'
      : '该点位当前检测结果达标。';
  }
  return '';
});

const relationSummary = computed(() => props.feature.relationSummary);

const previewRows = computed(() => {
  const rows: Array<{ label: string; value: string }> = [];
  if (props.feature.businessSummary?.previewRows?.length) {
    rows.push(...props.feature.businessSummary.previewRows);
  }
  const propEntries = Object.entries(props.feature.properties).filter(
    ([key]) =>
      !['trafficFeature', '__layerName', 'sourceLayer', 'sectionId', 'NAME'].includes(key),
  );
  const existingLabels = new Set(rows.map(r => r.label));
  for (const [key, value] of propEntries) {
    if (!existingLabels.has(key)) {
      rows.push({ label: key, value: String(value) });
    }
  }
  return rows;
});

const previewProgress = computed(() =>
  String(props.feature.properties['建设进度'] || '0%'),
);

const isSection = computed(() => props.feature.objectType === 'road-section');
const recentHistory = computed(() => {
  const value = props.feature.properties['recentHistory'];
  return Array.isArray(value) ? value.slice(0, 5) as Array<Record<string, unknown>> : [];
});

const displayRelations = computed(() => {
  if (props.relations?.length) return props.relations;
  return props.feature.relations || [];
});

const RISK_LABELS: Record<number, string> = {
  1: '一般',
  2: '较大',
  3: '重大',
  4: '特大',
};

function riskLabel(level?: number) {
  if (!level) return '';
  return RISK_LABELS[level] || '';
}
</script>

<template>
  <article :class="{ 'feature-card--dashboard': isDashboard }">
    <button class="close" aria-label="关闭详情" @click="$emit('close')">×</button>

    <!-- Dashboard 模式：领导层摘要口径 + 关联事项摘要 -->
    <template v-if="isDashboard">
      <header>
        <div>
          <small>{{ headerTitle }}</small>
          <b>{{ feature.name }}</b>
        </div>
        <span :class="{ critical: isCritical }">{{ displayStatus }}</span>
      </header>
      <div v-if="dashboardRows.length" class="summary">
        <div v-for="row in dashboardRows" :key="row.label" class="summary-item" :class="{ 'summary-item--alert': isAlertRow(row.label, row.value) }">
          <span>{{ row.label }}</span>
          <b>{{ row.value }}</b>
        </div>
      </div>
      <p v-if="dashboardNote" class="note">{{ dashboardNote }}</p>
      <a v-if="feature.properties['closureIssueId']" class="closure-link" href="#/closure">进入问题闭环管理 →</a>
      <div v-if="recentHistory.length" class="history-block">
        <div class="history-title"><span>最近检测记录</span><b>{{ feature.properties['历史记录数'] || recentHistory.length }} 条</b></div>
        <div v-for="(item,index) in recentHistory" :key="index" class="history-row" :class="{ alert: ['超标','逾期','异常'].includes(String(item.status || '')) }">
          <span>{{ item.date }} · {{ item.factor }}</span>
          <b>{{ item.value }} {{ item.unit }}</b>
          <em>{{ item.status }}</em>
        </div>
      </div>

      <!-- 关联事项摘要 -->
      <div v-if="relationSummary && relationSummary.total > 0" class="relations-summary">
        <div class="relations-header">
          <span>关联事项</span>
          <b>{{ relationSummary.total }} 项</b>
        </div>
        <div class="relations-meta">
          <span v-if="relationSummary.pendingCount > 0">待处理 {{ relationSummary.pendingCount }} 项</span>
          <span v-if="relationSummary.highRiskCount > 0" class="high-risk">高风险 {{ relationSummary.highRiskCount }} 项</span>
        </div>
        <div class="chips">
          <span
            v-for="item in relationSummary.byType"
            :key="item.type"
            class="chip"
          >
            {{ item.typeLabel }} {{ item.count }}
          </span>
        </div>
      </div>

      <!-- 查看关联业务按钮：仅查看，不办理 -->
      <button
        v-if="relationSummary && relationSummary.total > 0"
        class="business-links-btn"
        @click="$emit('loadBusinessLinks')"
      >
        查看关联业务
      </button>
    </template>

    <!-- Preview 模式：完整调试字段 + 关联事项列表 -->
    <template v-else>
      <header>
        <div>
          <small>{{ headerTitle }}</small>
          <b>{{ feature.name }}</b>
        </div>
        <span :class="{ critical: isCritical }">{{ displayStatus }}</span>
      </header>
      <template v-if="isSection && !feature.businessSummary">
        <div class="progress">
          <div>
            <span>建设进度</span>
            <b>{{ previewProgress }}</b>
          </div>
          <i><em :style="{ width: previewProgress }"></em></i>
        </div>
        <div class="metrics">
          <span><b>{{ feature.properties['线路长度'] || '--' }}</b><small>线路长度</small></span>
          <span><b>{{ feature.properties['环保问题'] || '--' }}</b><small>环保问题</small></span>
          <span><b>{{ feature.properties['风险点'] || '--' }}</b><small>风险点</small></span>
        </div>
      </template>
      <dl v-if="previewRows.length">
        <template v-for="row in previewRows" :key="row.label">
          <dt>{{ row.label }}</dt>
          <dd :class="{ 'alert-value': isAlertRow(row.label, row.value) }">{{ row.value }}</dd>
        </template>
      </dl>

      <!-- 关联事项完整列表 -->
      <div class="relations-section">
        <div class="relations-title">
          <span>关联事项</span>
          <b v-if="relationSummary">{{ relationSummary.total }} 项</b>
        </div>
        <div v-if="relationsLoading" class="relations-loading">加载中…</div>
        <div v-else-if="displayRelations.length" class="relations-list">
          <div
            v-for="(rel, idx) in displayRelations"
            :key="idx"
            class="relation-item"
          >
            <div class="relation-head">
              <span class="relation-type">{{ rel.typeLabel || rel.type }}</span>
              <span v-if="rel.code" class="relation-code">{{ rel.code }}</span>
              <span v-if="rel.riskLevel" class="relation-risk">风险: {{ riskLabel(rel.riskLevel) }}</span>
            </div>
            <div class="relation-name">{{ rel.name }}</div>
            <div v-if="rel.status" class="relation-status">状态: {{ rel.status }}</div>
            <div v-if="rel.summary" class="relation-summary-text">{{ rel.summary }}</div>
            <div v-if="rel.updatedAt" class="relation-time">{{ rel.updatedAt }}</div>
          </div>
        </div>
        <div v-else class="relations-empty">暂无关联事项</div>
        <button class="relation-link-btn" @click="$emit('loadRelations')">
          {{ displayRelations.length ? '刷新关联事项' : '加载关联事项' }}
        </button>
        <button
          v-if="relationSummary && relationSummary.total > 0"
          class="business-links-btn business-links-btn--preview"
          @click="$emit('loadBusinessLinks')"
        >
          查看关联业务
        </button>
      </div>

      <footer v-if="isSection">演示补充资料 · 可在接入正式项目数据后替换</footer>
    </template>
  </article>
</template>

<style scoped>
article {
  position: relative;
  width: 300px;
  max-height: calc(100% - 24px);
  overflow-y: auto;
  padding: 14px;
  background: linear-gradient(145deg, rgba(4, 28, 48, 0.97), rgba(3, 15, 29, 0.96));
  border: 1px solid rgba(28, 194, 230, 0.55);
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.42);
  color: #d9f1ff;
}
.close {
  position: absolute;
  right: 8px;
  top: 7px;
  width: 25px;
  height: 25px;
  padding: 0 !important;
  border: 0 !important;
  background: transparent !important;
  color: #7ba8ba !important;
  font-size: 20px;
  line-height: 24px;
}
.close:hover { color: #fff !important; }

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px 10px 0;
  border-bottom: 1px solid rgba(45, 172, 207, 0.24);
}
header small, header b { display: block; }
header small { margin-bottom: 4px; color: #5ba4bd; font-size: 9px; }
header b { font-size: 16px; }
header > span {
  padding: 3px 8px;
  color: #52e3a4;
  background: rgba(27, 176, 114, 0.12);
  border: 1px solid rgba(46, 213, 145, 0.3);
  font-size: 10px;
}
header > span.critical {
  color: #fff;
  background: rgba(255, 38, 61, 0.88);
  border-color: #ff6475;
  box-shadow: 0 0 12px rgba(255, 38, 61, 0.45);
  font-weight: 700;
}

.progress { padding: 12px 0; }
.progress > div { display: flex; justify-content: space-between; font-size: 11px; }
.progress > div span { color: #7fa2b3; }
.progress > div b { color: #2bd9f4; }
.progress > i { display: block; height: 5px; margin-top: 6px; background: #0c3146; }
.progress em { display: block; height: 100%; background: linear-gradient(90deg, #126ed1, #23ddf3); }

.metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }
.metrics span { padding: 8px 4px; text-align: center; background: rgba(10, 58, 82, 0.48); border: 1px solid rgba(45, 151, 191, 0.2); }
.metrics b, .metrics small { display: block; }
.metrics b { font-size: 12px; }
.metrics small { margin-top: 4px; color: #6f94a6; font-size: 9px; }

dl { display: grid; grid-template-columns: 82px 1fr; margin: 10px 0 0; font-size: 10px; }
dt, dd { padding: 4px 2px; border-bottom: 1px solid rgba(67, 117, 139, 0.12); }
dt { color: #6f93ac; }
dd { margin: 0; color: #bdd2dc; }
dd.alert-value { color: #ff596b; font-weight: 700; text-shadow: 0 0 8px rgba(255, 38, 61, 0.42); }

footer { margin-top: 9px; color: #52788b; font-size: 9px; }

/* Dashboard 模式 */
.feature-card--dashboard {
  width: 260px;
  max-height: calc(100% - 24px);
  padding: 12px;
}
.feature-card--dashboard header b { font-size: 14px; }
.feature-card--dashboard header small { font-size: 8px; }
.feature-card--dashboard header > span { font-size: 9px; padding: 2px 6px; }

.summary { margin-top: 10px; }
.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  border-bottom: 1px solid rgba(67, 117, 139, 0.15);
}
.summary-item span { color: #7fa2b3; font-size: 11px; }
.summary-item b { color: #d9f1ff; font-size: 12px; }
.summary-item--alert b { color: #ff596b; font-size: 13px; text-shadow: 0 0 8px rgba(255, 38, 61, 0.45); }
.summary-item--alert span { color: #ff9aa5; }

.note {
  margin: 8px 0 0;
  padding: 6px 8px;
  color: #8aabbf;
  font-size: 10px;
  line-height: 1.5;
  background: rgba(10, 38, 58, 0.4);
  border-left: 2px solid rgba(34, 194, 230, 0.3);
}
.closure-link{display:block;margin-top:8px;padding:7px 9px;color:#fff;text-align:center;text-decoration:none;background:rgba(255,38,61,.72);border:1px solid #ff6475;font-size:10px;font-weight:700}
.history-block { margin-top:9px; padding-top:8px; border-top:1px solid rgba(45,172,207,.2); }
.history-title { display:flex; justify-content:space-between; margin-bottom:5px; color:#7fa2b3; font-size:10px; }
.history-title b { color:#2bd9f4; }
.history-row { display:grid; grid-template-columns:1fr auto auto; gap:7px; align-items:center; padding:4px 0; border-bottom:1px solid rgba(67,117,139,.12); font-size:9px; }
.history-row span { color:#7fa2b3; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.history-row b { color:#d9f1ff; }
.history-row em { min-width:32px; color:#52e3a4; font-style:normal; text-align:right; }
.history-row.alert b,.history-row.alert em { color:#ff596b; font-weight:700; }

/* 关联事项摘要（dashboard） */
.relations-summary {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(45, 172, 207, 0.2);
}
.relations-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
}
.relations-header span { color: #7fa2b3; }
.relations-header b { color: #2bd9f4; font-size: 12px; }
.relations-meta {
  display: flex;
  gap: 10px;
  margin-top: 4px;
  font-size: 10px;
  color: #8aabbf;
}
.relations-meta .high-risk { color: #ff8888; }
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 5px;
}
.chip {
  padding: 2px 7px;
  font-size: 10px;
  color: #a8d4e8;
  background: rgba(20, 60, 88, 0.5);
  border: 1px solid rgba(45, 151, 191, 0.25);
  border-radius: 2px;
}

/* 关联事项完整列表（preview） */
.relations-section {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid rgba(45, 172, 207, 0.2);
}
.relations-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  margin-bottom: 6px;
}
.relations-title span { color: #7fa2b3; }
.relations-title b { color: #2bd9f4; }

.relations-loading, .relations-empty {
  font-size: 10px;
  color: #6f94a6;
  padding: 6px 0;
}

.relations-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.relation-item {
  padding: 6px 7px;
  background: rgba(10, 38, 58, 0.35);
  border: 1px solid rgba(45, 151, 191, 0.15);
  border-radius: 3px;
}
.relation-head {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 9px;
}
.relation-type {
  padding: 1px 5px;
  color: #2bd9f4;
  background: rgba(20, 60, 88, 0.6);
  border-radius: 2px;
}
.relation-code { color: #8aabbf; }
.relation-risk { color: #ff8888; }
.relation-name {
  font-size: 11px;
  color: #d9f1ff;
  margin-top: 3px;
}
.relation-status {
  font-size: 9px;
  color: #7fa2b3;
  margin-top: 2px;
}
.relation-summary-text {
  font-size: 9px;
  color: #8aabbf;
  margin-top: 2px;
  line-height: 1.4;
}
.relation-time {
  font-size: 8px;
  color: #52788b;
  margin-top: 2px;
}

.relation-link-btn {
  width: 100%;
  margin-top: 6px;
  padding: 5px;
  font-size: 10px;
  color: #7fa2b3;
  background: transparent;
  border: 1px solid rgba(45, 151, 191, 0.2);
  cursor: pointer;
}
.relation-link-btn:hover {
  color: #d9f1ff;
  border-color: rgba(34, 194, 230, 0.4);
}

/* 查看关联业务按钮：保持 dashboard 卡片紧凑 */
.business-links-btn {
  width: 100%;
  margin-top: 6px;
  padding: 5px 8px;
  font-size: 11px;
  color: #2bd9f4;
  background: rgba(20, 60, 88, 0.4);
  border: 1px solid rgba(34, 194, 230, 0.35);
  border-radius: 2px;
  cursor: pointer;
}
.business-links-btn:hover {
  color: #fff;
  background: rgba(34, 194, 230, 0.18);
  border-color: rgba(34, 194, 230, 0.6);
}
.business-links-btn--preview {
  margin-top: 4px;
  font-size: 10px;
}
</style>
