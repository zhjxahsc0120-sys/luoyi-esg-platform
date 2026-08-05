<script setup lang="ts">
/**
 * G03 参建单位履约评价 — 台账未接入时空态，不编造排名。
 * 布局沿用 G 组弹窗尺寸/风格，不新增一级区域。
 */
const emit = defineEmits<{ (e: 'close'): void }>()
</script>

<template>
  <div class="g03-eval-modal" role="dialog" aria-label="参建单位履约评价">
    <header class="modal-head">
      <div class="title-row">
        <span class="title-key">G03</span>
        <span class="title-name">参建单位履约评价</span>
      </div>
      <button type="button" class="close-btn" @click="emit('close')">关闭</button>
    </header>
    <section class="summary" aria-label="G03摘要">
      <div class="metric"><span class="label">纳入评价单位</span><strong>0</strong><span class="unit">家</span></div>
      <div class="metric"><span class="label">本周期已评价</span><strong>0</strong><span class="unit">家</span></div>
      <div class="metric"><span class="label">待评价</span><strong>0</strong><span class="unit">家</span></div>
      <div class="metric"><span class="label">台账状态</span><strong class="pending">未接入</strong></div>
    </section>
    <section class="body">
      <h3>说明</h3>
      <p>
        暂无有效数据。参建单位履约评价（单位排名、履约评价、考核结果）台账尚未接入本系统，
        首页指标按 <strong>0</strong> 展示，不编造排名或得分。台账接入后可在此扩展二级明细。
      </p>
      <dl class="meta">
        <div><dt>数据来源</dt><dd>履约评价台账（待建）</dd></div>
        <div><dt>责任单位</dt><dd>合约部 / 项目经理部</dd></div>
        <div><dt>状态</dt><dd>待建台账</dd></div>
      </dl>
    </section>
    <footer class="footer-info" title="正式接口：/api/dashboard/kpi/G03">
      接口：/api/dashboard/kpi/G03 · 口径：不编造
    </footer>
  </div>
</template>

<style scoped lang="scss">
.g03-eval-modal {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 420px;
  padding: 16px 18px 12px;
  color: var(--text-primary, #e8f1ff);
}
.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.title-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.title-key {
  color: #b794f6;
  font-size: 18px;
  font-weight: 700;
}
.title-name {
  font-size: 18px;
  font-weight: 650;
}
.close-btn {
  border: 1px solid rgba(143, 176, 224, 0.35);
  background: transparent;
  color: var(--text-secondary, #9eb6d4);
  border-radius: 4px;
  padding: 4px 12px;
  cursor: pointer;
}
.summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}
.metric {
  padding: 10px 12px;
  border: 1px solid rgba(143, 176, 224, 0.25);
  border-radius: 6px;
  background: rgba(12, 28, 52, 0.55);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.metric .label {
  font-size: 12px;
  color: var(--text-tertiary, #7f99b8);
}
.metric strong {
  font-size: 22px;
  font-weight: 700;
}
.metric .unit {
  font-size: 12px;
  color: var(--text-secondary, #9eb6d4);
}
.metric .pending {
  color: #ffb347;
  font-size: 16px;
}
.body h3 {
  margin: 0 0 8px;
  font-size: 15px;
}
.body p {
  margin: 0 0 12px;
  line-height: 1.6;
  color: var(--text-secondary, #9eb6d4);
  font-size: 13px;
}
.meta {
  display: grid;
  gap: 6px;
  margin: 0;
}
.meta > div {
  display: grid;
  grid-template-columns: 88px 1fr;
  gap: 8px;
  font-size: 12px;
}
.meta dt {
  color: var(--text-tertiary, #7f99b8);
}
.meta dd {
  margin: 0;
  color: var(--text-secondary, #9eb6d4);
}
.footer-info {
  margin-top: auto;
  font-size: 11px;
  color: var(--text-tertiary, #7f99b8);
}
</style>
