<script setup lang="ts">
import { computed } from 'vue'
import type { EsgRiskObjectDetail } from '@/types/esg-class-a'

const props = defineProps<{
  detail: EsgRiskObjectDetail | null
  loading?: boolean
}>()

const showAbnormal = computed(
  () => props.detail?.statusLevel !== 'normal' && Boolean(props.detail?.abnormalFactor),
)
</script>

<template>
  <section class="risk-detail">
    <div v-if="loading" class="empty">详情加载中…</div>
    <div v-else-if="!detail" class="empty">请选择监测点查看详情</div>
    <template v-else>
      <h3 class="detail-title">{{ detail.pointName }}</h3>
      <div class="detail-status-row">
        <span class="detail-status" :class="`tone-${detail.statusLevel}`">{{ detail.statusLabel }}</span>
        <span v-if="detail.lifecycleStage">当前节点：{{ detail.lifecycleStage }}</span>
      </div>

      <div class="block">
        <h4>基础信息</h4>
        <dl class="info">
          <div><dt>监测点编号</dt><dd>{{ detail.pointCode }}</dd></div>
          <div><dt>监测类型</dt><dd>{{ detail.monitorType }}</dd></div>
          <div><dt>所在位置</dt><dd>{{ detail.location }}</dd></div>
          <div><dt>当前状态</dt><dd :class="`tone-${detail.statusLevel}`">{{ detail.statusLabel }}</dd></div>
          <div v-if="detail.responsibleUnit"><dt>责任单位</dt><dd>{{ detail.responsibleUnit }}</dd></div>
          <div v-if="detail.deadline"><dt>整改期限</dt><dd>{{ detail.deadline }}</dd></div>
          <div v-if="detail.nextNode"><dt>下一节点</dt><dd>{{ detail.nextNode }}</dd></div>
        </dl>
      </div>

      <div v-if="showAbnormal" class="block abnormal">
        <h4>异常指标</h4>
        <dl class="info">
          <div v-if="detail.abnormalFactor"><dt>异常指标</dt><dd>{{ detail.abnormalFactor }}</dd></div>
          <div v-if="detail.abnormalValue"><dt>检测值</dt><dd>{{ detail.abnormalValue }}</dd></div>
          <div v-if="detail.abnormalLimit"><dt>标准限值</dt><dd>{{ detail.abnormalLimit }}</dd></div>
          <div v-if="detail.exceedMultiple"><dt>超标倍数</dt><dd class="tone-danger">{{ detail.exceedMultiple }}</dd></div>
          <div v-if="detail.disposalStatus"><dt>处置状态</dt><dd>{{ detail.disposalStatus }}</dd></div>
          <div v-if="detail.rectificationMeasure"><dt>整改措施</dt><dd>{{ detail.rectificationMeasure }}</dd></div>
        </dl>
      </div>

      <div class="block">
        <h4>最新监测结果</h4>
        <table>
          <thead>
            <tr>
              <th>指标</th>
              <th>检测值</th>
              <th>单位</th>
              <th>标准限值</th>
              <th>结果</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in detail.factors" :key="row.name">
              <td>{{ row.name }}</td>
              <td>{{ row.detectedValue }}</td>
              <td>{{ row.unit }}</td>
              <td>{{ row.limitValue }}</td>
              <td :class="row.isAbnormal ? 'tone-danger' : 'tone-normal'">{{ row.resultLabel }}</td>
            </tr>
          </tbody>
        </table>
        <p class="footnote">监测时间：{{ detail.latestTime }} · 数据来源：{{ detail.dataSource }}</p>
        <p v-if="detail.evidenceCount" class="footnote">关联证据：{{ detail.evidenceCount }} 项</p>
      </div>
    </template>
  </section>
</template>

<style scoped lang="scss">
.risk-detail {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding-top: 8px;
}

.detail-title {
  margin: 0 0 10px;
  font-size: 20px;
  font-weight: 700;
  color: #f3f8ff;
}

.detail-status-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: -4px 0 8px;
  color: #8ba6c3;
  font-size: 14px;
}

.detail-status {
  padding: 3px 9px;
  border-radius: 999px;
  border: 1px solid currentColor;
  font-weight: 700;
}

.block {
  margin-bottom: 10px;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid rgba(105, 227, 111, 0.18);
  background: rgba(8, 40, 69, 0.4);

  h4 {
    margin: 0 0 8px;
    font-size: 16px;
    font-weight: 700;
    color: #69e36f;
  }

  &.abnormal {
    border-color: rgba(255, 122, 150, 0.3);
    background: rgba(255, 90, 122, 0.08);
  }
}

.info {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;

  div {
    display: grid;
    grid-template-columns: 80px 1fr;
    gap: 8px;
    font-size: 15px;
  }

  dt { color: #8ba6c3; margin: 0; }
  dd { margin: 0; color: #e8f3ff; word-break: break-word; }
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;

  th, td {
    padding: 6px 4px;
    text-align: left;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  }

  th { color: #8ba6c3; font-weight: 600; }
  td { color: #e8f3ff; }
}

.footnote {
  margin: 8px 0 0;
  font-size: 13px;
  color: #8ba6c3;
}

.tone-normal { color: #69e36f; }
.tone-warning { color: #ffc857; }
.tone-danger { color: #ff7a96; }

.empty {
  padding: 16px 8px;
  text-align: center;
  color: #8ba6c3;
  font-size: 15px;
}
</style>
