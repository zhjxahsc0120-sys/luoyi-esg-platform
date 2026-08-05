<script setup lang="ts">

import type { ChatMessage, AssistantDataBasis } from '@/types/assistant'

import { statusLevelClass } from '@/utils/assistant-business-answer'



const props = defineProps<{

  message: ChatMessage

}>()



const emit = defineEmits<{

  (e: 'view-data-basis', data: AssistantDataBasis): void

  (e: 'follow-up', question: string): void

  (e: 'next-action', action: { label: string; question?: string }): void

}>()



function getKpiColorClass(color?: string): string {

  const map: Record<string, string> = {

    green: 'kpi-green',

    blue: 'kpi-blue',

    purple: 'kpi-purple',

    orange: 'kpi-orange',

    red: 'kpi-red',

    cyan: 'kpi-cyan',

  }

  return map[color || 'blue'] || 'kpi-blue'

}



function getStatusClass(status: string): string {

  if (['整改中', '办理中', '进行中', '管控中', '推进中'].includes(status)) return 'st-blue'

  if (['待复查', '待处理', '临期', '待复核', '有缺口', '需跟进'].includes(status)) return 'st-orange'

  if (['待销项', '逾期', '异常', '重点'].includes(status) || status.includes('待补齐')) return 'st-red'

  if (['正常', '已完成', '已闭环', '已齐', '较好', '受控中'].includes(status)) return 'st-green'

  return 'st-gray'

}



function getColAlign(align?: string): string {

  return align || 'left'

}



function packageMetaChips(card: NonNullable<ChatMessage['packageCard']>): string[] {

  const stats = card.stats

  if (stats && (stats.categoryCount || stats.requiredFileCount)) {

    const chips: string[] = []

    if (stats.categoryCount != null) chips.push(`类别 ${stats.categoryCount}`)

    if (stats.requiredFileCount != null) chips.push(`文件 ${stats.requiredFileCount}`)

    if (stats.collectedCount != null) chips.push(`已归集 ${stats.collectedCount}`)

    if (stats.pendingCount != null) chips.push(`待补齐 ${stats.pendingCount}`)

    if (stats.openIssueCount != null) chips.push(`未闭环 ${stats.openIssueCount}`)

    if (stats.closureRate) chips.push(`闭环率 ${stats.closureRate}`)

    return chips

  }

  return [`应备 ${card.requiredCount} 项`]

}



function onNextAction(action: { label: string; question?: string }) {

  if (action.question) {

    emit('follow-up', action.question)

    return

  }

  // 下载动作：若有资料包则滚动/聚焦由外层处理；无 question 时尝试打开 download

  if (props.message.packageCard?.downloadUrl && action.label.includes('下载')) {

    window.open(props.message.packageCard.downloadUrl, '_blank')

    return

  }

  emit('next-action', action)

}



const showBusinessCard = () =>

  props.message.role === 'assistant' &&

  !props.message.loading &&

  Boolean(

    props.message.statusConclusion ||

      props.message.kpiCards?.length ||

      props.message.riskItems?.length ||

      props.message.packageCard ||

      props.message.dataBasis,

  )

</script>



<template>

  <div class="message-row" :class="{ 'is-user': message.role === 'user' }">

    <div v-if="message.role === 'user'" class="user-message">

      <div class="user-bubble">

        <div class="bubble-text">{{ message.content }}</div>

        <div class="bubble-time">{{ message.time }}</div>

      </div>

    </div>



    <div v-else class="assistant-message">

      <div v-if="message.loading" class="loading-bubble">

        <div class="loading-dots">

          <span /><span /><span />

        </div>

        <span class="loading-text">正在汇总业务数据……</span>

      </div>



      <template v-else>

        <div class="assistant-avatar">助</div>

        <div class="assistant-content">

          <!-- 业务回答卡片：状态 → KPI → 风险 → 依据 → 下一步（检查类含资料包） -->

          <div v-if="showBusinessCard()" class="business-card">

            <div class="card-section section-status">

              <div class="section-head">

                <span class="section-label">状态判断</span>

                <span

                  v-if="message.statusLevel"

                  class="status-level"

                  :class="statusLevelClass(message.statusLevel)"

                >{{ message.statusLevel }}</span>

              </div>

              <div class="status-conclusion">{{ message.statusConclusion || message.content }}</div>

            </div>



            <div

              v-if="message.kpiCards && message.kpiCards.length"

              class="card-section section-kpi"

            >

              <div class="section-head">

                <span class="section-label">核心指标</span>

              </div>

              <div

                class="kpi-cards"

                :class="{ 'kpi-cards--wide': message.kpiCards.length > 4 }"

              >

                <div

                  v-for="(card, idx) in message.kpiCards"

                  :key="idx"

                  class="kpi-card"

                  :class="getKpiColorClass(card.color)"

                >

                  <div class="kpi-top">

                    <div class="kpi-label">{{ card.label }}</div>

                    <span v-if="card.statusText" class="kpi-status" :class="getStatusClass(card.statusText)">

                      {{ card.statusText }}

                    </span>

                  </div>

                  <div class="kpi-value">

                    <span class="value-num">{{ card.value }}</span>

                    <span v-if="card.unit" class="value-unit">{{ card.unit }}</span>

                  </div>

                  <div v-if="card.meaning" class="kpi-meaning">{{ card.meaning }}</div>

                </div>

              </div>

            </div>



            <div

              v-if="message.riskItems && message.riskItems.length"

              class="card-section section-risk"

            >

              <div class="section-head">

                <span class="section-label">{{ message.riskSectionTitle || '重点关注' }}</span>

              </div>

              <ol class="risk-list">

                <li v-for="(item, idx) in message.riskItems" :key="idx" class="risk-item">

                  <div class="risk-index">{{ idx + 1 }}</div>

                  <div class="risk-body">

                    <div class="risk-title">{{ item.title }}</div>

                    <div class="risk-meta">

                      <span v-if="item.section" class="risk-section">所属：{{ item.section }}</span>

                      <span class="status-tag" :class="getStatusClass(item.status)">

                        {{ item.status }}

                      </span>

                    </div>

                  </div>

                </li>

              </ol>

            </div>



            <div

              v-if="message.tableData && message.answerType === 'inspection'"

              class="card-section section-table"

            >

              <div class="section-head">

                <span class="section-label">{{ message.tableData.title }}</span>

              </div>

              <div class="table-wrap">

                <table>

                  <thead>

                    <tr>

                      <th

                        v-for="col in message.tableData.columns"

                        :key="col.key"

                        :class="'align-' + getColAlign(col.align)"

                      >

                        {{ col.label }}

                      </th>

                    </tr>

                  </thead>

                  <tbody>

                    <tr v-for="(row, ri) in message.tableData.rows" :key="ri">

                      <td

                        v-for="col in message.tableData.columns"

                        :key="col.key"

                        :class="'align-' + getColAlign(col.align)"

                      >

                        {{ row[col.key] }}

                      </td>

                    </tr>

                  </tbody>

                </table>

              </div>

            </div>



            <div

              v-else-if="message.tableData && message.answerType !== 'inspection'"

              class="card-section section-table"

            >

              <div class="section-head">

                <span class="section-label">{{ message.tableData.title }}</span>

              </div>

              <div class="table-wrap">

                <table>

                  <thead>

                    <tr>

                      <th

                        v-for="col in message.tableData.columns"

                        :key="col.key"

                        :class="'align-' + getColAlign(col.align)"

                      >

                        {{ col.label }}

                      </th>

                    </tr>

                  </thead>

                  <tbody>

                    <tr v-for="(row, ri) in message.tableData.rows" :key="ri">

                      <td

                        v-for="col in message.tableData.columns"

                        :key="col.key"

                        :class="'align-' + getColAlign(col.align)"

                      >

                        <template v-if="col.key === 'handleStatus' || col.key === 'timeStatus' || col.key === 'status'">

                          <span class="status-tag" :class="getStatusClass(String(row[col.key]))">

                            {{ row[col.key] }}

                          </span>

                        </template>

                        <template v-else>

                          {{ row[col.key] }}

                        </template>

                      </td>

                    </tr>

                  </tbody>

                </table>

              </div>

            </div>



            <!-- 上级检查：必须保留资料包下载 + 11 类统计 chips -->

            <div v-if="message.packageCard" class="card-section section-package">

              <div class="section-head">

                <span class="section-label">合规资料包</span>

              </div>

              <div class="package-card">

                <div class="package-head">

                  <div class="package-title">{{ message.packageCard.title }}</div>

                  <div class="package-meta">

                    <span

                      v-for="(chip, ci) in packageMetaChips(message.packageCard)"

                      :key="ci"

                      class="package-chip"

                    >{{ chip }}</span>

                  </div>

                </div>

                <div class="package-actions">

                  <a

                    class="package-download"

                    :href="message.packageCard.downloadUrl"

                    download

                    target="_blank"

                    rel="noopener"

                  >

                    下载资料包

                  </a>

                </div>

              </div>

            </div>



            <div v-if="message.dataBasis" class="card-section section-basis">

              <div class="section-head">

                <span class="section-label">数据依据</span>

              </div>

              <div class="basis-grid">

                <div class="basis-row">

                  <span class="basis-k">来源</span>

                  <span class="basis-v">{{ message.dataBasis.sources?.[0]?.name || message.dataBasis.itemName }}</span>

                </div>

                <div class="basis-row">

                  <span class="basis-k">统计时间</span>

                  <span class="basis-v">{{ message.dataBasis.dataPeriod || message.dataBasis.updateTime }}</span>

                </div>

                <div class="basis-row">

                  <span class="basis-k">口径</span>

                  <span class="basis-v">{{ message.dataBasis.caliber || '与首页指标保持一致' }}</span>

                </div>

                <div class="basis-row">

                  <span class="basis-k">核验</span>

                  <span class="basis-v basis-verified">{{ message.dataBasis.verifyStatus || '已核验' }}</span>

                </div>

              </div>

              <button class="basis-btn" @click="emit('view-data-basis', message.dataBasis!)">

                查看数据依据

              </button>

            </div>



            <div

              v-if="message.nextActions && message.nextActions.length"

              class="card-section section-next"

            >

              <div class="section-head">

                <span class="section-label">建议操作</span>

              </div>

              <div class="next-list">

                <button

                  v-for="(action, idx) in message.nextActions"

                  :key="idx"

                  class="next-item"

                  @click="onNextAction(action)"

                >

                  <span class="next-idx">{{ idx + 1 }}</span>

                  <span class="next-label">{{ action.label }}</span>

                </button>

              </div>

            </div>

          </div>



          <!-- 非结构化兜底（连接失败等） -->

          <div v-else class="answer-summary">{{ message.content }}</div>



          <div

            v-if="message.followUps && message.followUps.length && !(message.nextActions && message.nextActions.length)"

            class="follow-ups"

          >

            <div class="follow-title">继续查询</div>

            <div class="follow-list">

              <button

                v-for="(item, idx) in message.followUps"

                :key="idx"

                class="follow-item"

                @click="emit('follow-up', item)"

              >

                <span class="follow-icon">→</span>

                <span class="follow-text">{{ item }}</span>

              </button>

            </div>

          </div>

        </div>

      </template>

    </div>

  </div>

</template>



<style scoped lang="scss">

@use '@/styles/tokens.scss' as *;



.message-row {

  display: flex;

  width: 100%;



  &.is-user {

    justify-content: flex-end;

  }

}



.user-message {

  max-width: 70%;

  display: flex;

  flex-direction: column;

  align-items: flex-end;

}



.user-bubble {

  background: linear-gradient(135deg, rgba(22, 135, 255, 0.9) 0%, rgba(37, 185, 255, 0.9) 100%);

  border-radius: 12px 12px 4px 12px;

  padding: 12px 18px;

  color: #fff;

  box-shadow: 0 4px 12px rgba(22, 135, 255, 0.25);

}



.bubble-text {

  font-size: 15px;

  line-height: 1.6;

  white-space: pre-wrap;

}



.bubble-time {

  font-size: 11px;

  opacity: 0.75;

  margin-top: 6px;

  text-align: right;

}



.assistant-message {

  display: flex;

  gap: 14px;

  max-width: 100%;

}



.assistant-avatar {

  width: 40px;

  height: 40px;

  border-radius: 10px;

  background: linear-gradient(135deg, rgba(37, 185, 255, 0.95), rgba(22, 135, 255, 0.9));

  display: flex;

  align-items: center;

  justify-content: center;

  font-size: 14px;

  font-weight: 700;

  color: #fff;

  flex-shrink: 0;

}



.assistant-content {

  flex: 1;

  min-width: 0;

  display: flex;

  flex-direction: column;

  gap: 14px;

}



.business-card {

  background: rgba(8, 40, 69, 0.72);

  border: 1px solid rgba(74, 147, 207, 0.28);

  border-radius: 12px;

  overflow: hidden;

  display: flex;

  flex-direction: column;

}



.card-section {

  padding: 16px 18px;

  border-bottom: 1px solid rgba(74, 147, 207, 0.14);



  &:last-child {

    border-bottom: none;

  }

}



.section-status {

  background: linear-gradient(90deg, rgba(37, 185, 255, 0.1), transparent 70%);

}



.section-head {

  display: flex;

  align-items: center;

  justify-content: space-between;

  gap: 12px;

  margin-bottom: 10px;

}



.section-label {

  font-size: 12px;

  font-weight: 700;

  letter-spacing: 0.06em;

  color: var(--text-tertiary);

  text-transform: none;

}



.status-level {

  display: inline-flex;

  align-items: center;

  padding: 2px 10px;

  border-radius: 4px;

  font-size: 12px;

  font-weight: 700;

  border: 1px solid transparent;

}



.level-green {

  color: var(--green);

  border-color: rgba(67, 211, 107, 0.45);

  background: rgba(67, 211, 107, 0.12);

}



.level-blue {

  color: var(--cyan);

  border-color: rgba(37, 185, 255, 0.45);

  background: rgba(37, 185, 255, 0.12);

}



.level-orange {

  color: var(--orange);

  border-color: rgba(255, 159, 47, 0.45);

  background: rgba(255, 159, 47, 0.12);

}



.level-red {

  color: var(--red);

  border-color: rgba(255, 75, 85, 0.45);

  background: rgba(255, 75, 85, 0.12);

}



.status-conclusion {

  font-size: 15px;

  line-height: 1.75;

  color: var(--text-primary);

  white-space: pre-wrap;

  font-weight: 500;

}



.kpi-cards {

  display: grid;

  grid-template-columns: repeat(3, 1fr);

  gap: 10px;



  &.kpi-cards--wide {

    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));

  }

}



.kpi-card {

  padding: 12px 14px;

  background: rgba(4, 25, 48, 0.55);

  border: 1px solid rgba(74, 147, 207, 0.18);

  border-radius: var(--radius-sm);

  position: relative;

  overflow: hidden;



  &::before {

    content: '';

    position: absolute;

    top: 0;

    left: 0;

    width: 3px;

    height: 100%;

  }



  &.kpi-green::before { background: var(--green); }

  &.kpi-blue::before { background: var(--blue); }

  &.kpi-purple::before { background: var(--purple); }

  &.kpi-orange::before { background: var(--orange); }

  &.kpi-red::before { background: var(--red); }

  &.kpi-cyan::before { background: var(--cyan); }

}



.kpi-top {

  display: flex;

  align-items: flex-start;

  justify-content: space-between;

  gap: 8px;

  margin-bottom: 6px;

}



.kpi-label {

  font-size: 12px;

  color: var(--text-tertiary);

}



.kpi-status {

  flex-shrink: 0;

  font-size: 11px;

  padding: 1px 6px;

  border-radius: 3px;

  border: 1px solid transparent;

}



.kpi-value {

  display: flex;

  align-items: baseline;

  gap: 4px;

}



.value-num {

  font-size: 24px;

  font-weight: 700;

  color: var(--text-primary);

  font-family: var(--font-num);

}



.kpi-green .value-num { color: var(--green); }

.kpi-blue .value-num { color: var(--cyan); }

.kpi-purple .value-num { color: var(--purple); }

.kpi-orange .value-num { color: var(--orange); }

.kpi-red .value-num { color: var(--red); }

.kpi-cyan .value-num { color: var(--cyan); }



.value-unit {

  font-size: 12px;

  color: var(--text-tertiary);

}



.kpi-meaning {

  margin-top: 8px;

  font-size: 12px;

  line-height: 1.45;

  color: var(--text-secondary);

}



.risk-list {

  list-style: none;

  margin: 0;

  padding: 0;

  display: flex;

  flex-direction: column;

  gap: 10px;

}



.risk-item {

  display: flex;

  gap: 12px;

  padding: 12px 14px;

  background: rgba(4, 25, 48, 0.45);

  border: 1px solid rgba(74, 147, 207, 0.16);

  border-radius: var(--radius-sm);

}



.risk-index {

  width: 24px;

  height: 24px;

  border-radius: 50%;

  display: flex;

  align-items: center;

  justify-content: center;

  font-size: 12px;

  font-weight: 700;

  color: var(--cyan);

  background: rgba(37, 185, 255, 0.12);

  border: 1px solid rgba(37, 185, 255, 0.35);

  flex-shrink: 0;

}



.risk-body {

  flex: 1;

  min-width: 0;

}



.risk-title {

  font-size: 14px;

  font-weight: 600;

  color: var(--text-primary);

  margin-bottom: 6px;

}



.risk-meta {

  display: flex;

  flex-wrap: wrap;

  align-items: center;

  gap: 10px;

  font-size: 12px;

  color: var(--text-tertiary);

}



.table-wrap {

  overflow-x: auto;

  border: 1px solid rgba(74, 147, 207, 0.16);

  border-radius: var(--radius-sm);

}



table {

  width: 100%;

  border-collapse: collapse;

}



thead th {

  padding: 8px 10px;

  font-size: 12px;

  font-weight: 600;

  color: var(--text-secondary);

  background: rgba(4, 25, 48, 0.6);

  text-align: left;

  border-bottom: 1px solid var(--border-soft);

  white-space: nowrap;

}



tbody td {

  padding: 8px 10px;

  font-size: 12px;

  color: var(--text-primary);

  border-bottom: 1px solid var(--border-faint);

  line-height: 1.4;

}



tbody tr:last-child td {

  border-bottom: none;

}



.align-left { text-align: left; }

.align-center { text-align: center; }

.align-right { text-align: right; }



.status-tag {

  display: inline-block;

  padding: 2px 8px;

  font-size: 12px;

  border-radius: 3px;

  border: 1px solid transparent;

  white-space: nowrap;

}



.st-green {

  color: var(--green);

  border-color: rgba(67, 211, 107, 0.4);

  background: rgba(67, 211, 107, 0.1);

}



.st-blue {

  color: var(--cyan);

  border-color: rgba(37, 185, 255, 0.4);

  background: rgba(37, 185, 255, 0.1);

}



.st-orange {

  color: var(--orange);

  border-color: rgba(255, 159, 47, 0.4);

  background: rgba(255, 159, 47, 0.1);

}



.st-red {

  color: var(--red);

  border-color: rgba(255, 75, 85, 0.4);

  background: rgba(255, 75, 85, 0.1);

}



.st-gray {

  color: var(--text-tertiary);

  border-color: rgba(74, 147, 207, 0.18);

  background: rgba(8, 40, 69, 0.55);

}



.package-card {

  background: rgba(4, 25, 48, 0.5);

  border: 1px solid rgba(37, 185, 255, 0.28);

  border-radius: var(--radius-sm);

  padding: 14px 16px;

}



.package-title {

  font-size: 15px;

  font-weight: 600;

  color: var(--text-primary);

}



.package-meta {

  margin-top: 8px;

  display: flex;

  flex-wrap: wrap;

  gap: 6px;

}



.package-chip {

  display: inline-flex;

  padding: 2px 8px;

  border-radius: 4px;

  background: rgba(37, 185, 255, 0.1);

  border: 1px solid rgba(74, 147, 207, 0.28);

  color: var(--text-secondary);

  font-size: 12px;

}



.package-actions {

  margin-top: 12px;

  display: flex;

  justify-content: flex-end;

}



.package-download {

  display: inline-flex;

  align-items: center;

  justify-content: center;

  min-width: 128px;

  height: 36px;

  padding: 0 18px;

  border-radius: 4px;

  font-size: 14px;

  font-weight: 600;

  color: #041322;

  text-decoration: none;

  background: linear-gradient(135deg, #25b9ff 0%, #1687ff 100%);

  box-shadow: 0 4px 12px rgba(22, 135, 255, 0.28);



  &:hover {

    filter: brightness(1.06);

  }

}



.basis-grid {

  display: grid;

  grid-template-columns: 1fr 1fr;

  gap: 8px 16px;

  margin-bottom: 12px;

}



.basis-row {

  display: flex;

  gap: 10px;

  font-size: 13px;

  line-height: 1.5;

}



.basis-k {

  flex-shrink: 0;

  width: 64px;

  color: var(--text-muted);

}



.basis-v {

  color: var(--text-primary);

  min-width: 0;

}



.basis-verified {

  color: var(--green);

}



.basis-btn {

  padding: 6px 14px;

  font-size: 13px;

  color: var(--cyan);

  background: rgba(37, 185, 255, 0.1);

  border: 1px solid rgba(37, 185, 255, 0.3);

  border-radius: 4px;

  cursor: pointer;



  &:hover {

    background: rgba(37, 185, 255, 0.2);

  }

}



.next-list {

  display: flex;

  flex-direction: column;

  gap: 8px;

}



.next-item {

  display: flex;

  align-items: center;

  gap: 12px;

  padding: 12px 14px;

  text-align: left;

  font-size: 14px;

  color: var(--text-primary);

  background: rgba(4, 25, 48, 0.45);

  border: 1px solid rgba(74, 147, 207, 0.2);

  border-radius: var(--radius-sm);

  cursor: pointer;

  transition: border-color 0.15s ease, background 0.15s ease;



  &:hover {

    border-color: rgba(37, 185, 255, 0.45);

    background: rgba(12, 50, 84, 0.75);

  }

}



.next-idx {

  width: 22px;

  height: 22px;

  border-radius: 4px;

  display: flex;

  align-items: center;

  justify-content: center;

  font-size: 12px;

  font-weight: 700;

  color: #041322;

  background: var(--cyan);

  flex-shrink: 0;

}



.next-label {

  flex: 1;

  line-height: 1.4;

}



.answer-summary {

  font-size: 15px;

  line-height: 1.7;

  color: var(--text-primary);

  padding: 14px 18px;

  background: rgba(8, 40, 69, 0.65);

  border: 1px solid rgba(74, 147, 207, 0.18);

  border-radius: 4px 12px 12px 12px;

  white-space: pre-wrap;

}



.loading-bubble {

  display: flex;

  align-items: center;

  gap: 12px;

  padding: 16px 20px;

  background: rgba(8, 40, 69, 0.65);

  border: 1px solid rgba(74, 147, 207, 0.18);

  border-radius: 4px 12px 12px 12px;

}



.loading-dots {

  display: flex;

  gap: 4px;



  span {

    width: 8px;

    height: 8px;

    border-radius: 50%;

    background: var(--cyan);

    animation: bounce 1.4s infinite ease-in-out both;



    &:nth-child(1) { animation-delay: -0.32s; }

    &:nth-child(2) { animation-delay: -0.16s; }

  }

}



@keyframes bounce {

  0%, 80%, 100% { transform: scale(0); opacity: 0.3; }

  40% { transform: scale(1); opacity: 1; }

}



.loading-text {

  font-size: 14px;

  color: var(--text-secondary);

}



.follow-ups {

  display: flex;

  flex-direction: column;

  gap: 10px;

}



.follow-title {

  font-size: 13px;

  font-weight: 600;

  color: var(--text-secondary);

}



.follow-list {

  display: grid;

  grid-template-columns: repeat(2, 1fr);

  gap: 8px;

}



.follow-item {

  display: flex;

  align-items: center;

  gap: 10px;

  padding: 12px 16px;

  font-size: 13px;

  color: var(--text-primary);

  background: rgba(8, 40, 69, 0.65);

  border: 1px solid rgba(74, 147, 207, 0.18);

  border-radius: var(--radius-sm);

  cursor: pointer;

  text-align: left;



  &:hover {

    background: rgba(12, 50, 84, 0.82);

    border-color: rgba(74, 147, 207, 0.32);

  }

}



.follow-icon {

  color: var(--text-tertiary);

  flex-shrink: 0;

}



.follow-text {

  flex: 1;

  line-height: 1.4;

}



@media (max-width: 1600px) {

  .kpi-cards {

    grid-template-columns: repeat(2, 1fr);

  }



  .basis-grid {

    grid-template-columns: 1fr;

  }



  .user-message {

    max-width: 80%;

  }

}

</style>


