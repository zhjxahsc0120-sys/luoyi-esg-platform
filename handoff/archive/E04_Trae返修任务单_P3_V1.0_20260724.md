# E04 Trae 返修任务单 · P3（门禁 104 · 不签收）

**日期：** 2026-07-24  
**状态：** Cursor **不签收**；须修阻断后再交二轮  
**依据：** `交付_E04_P3_UI实施包/` + `_handoff/E04_Trae实施任务单_P3_V1.0_20260724.md`  
**审查：** [E04 P3 review](3557c2a5-9e65-490c-8e09-26813faaab2a)

---

## 结论摘要

P3.1 / P3.2 主体（B′-1 六项摘要、差异条、候选非 KPI、C03 折叠、主值 12856）**原则通过**。  
DoD「异常态可用」**不通过**：七类异常中 **勾稽失败**、**API 失败+重试** 当前不可达。

**在阻断修复并二轮签收前，不要开工 E05。**

---

## 阻断项（必须修）

### B1. 勾稽失败逻辑恒真（永不告警）

文件：`src/components/modal/E04CarbonEmissionModal.vue`

现状：`totalEmission` 与 `sourceSumMatchesTotal` **都对 `detailData` 行求和再互比**，永远相等。

要求：来源合计应与 **累计主值**（摘要「累计碳排放」/ API 批次主值，锚定 **12856**）比较，容差 `< 0.01`。  
不等时展示现有红色告警条。

自测：人为把某一来源 emission 改偏 → 必须出现「来源合计与累计主值不一致」。

### B2. API 失败 + 重试 UI 不可达

文件建议：

- `src/views/DashboardPage.vue`（`handleKpiSelect` / `handleRetryKpi`）
- 必要时 `src/types/dashboard.ts`、`E04CarbonEmissionModal.vue`

现状：模态认 `detail.loadError === true`，但 `getDashboardKpiDetail` 失败时 `apiGet` 返回 `null`，页面不写入 `loadError`，仍可能保留 mock/旧态；重试链路 emit 已通，但错误壳进不去。

要求：

1. E04（至少）详情请求失败 → 打开模态时 `detail` 带 `loadError: true`（可保留最小壳字段）  
2. 成功响应清除 `loadError`  
3. 点「重试」重新请求；仍失败则保持错误态；成功则正常渲染  

自测：断后端或强改 API 失败 → 错误态 + 重试可用。

---

## 非阻断（可同包顺修）

| # | 说明 |
|---|------|
| N1 | API 摘要「数据性质」现为「测试数据」，E04 冻结稿场景 UI 用「演示数据」——**E04 按冻结保留「演示」**；与 E01–E03「去演示」分轨，勿混改 |
| N2 | `c01EqualsE04` 后端若硬编码 `True`，建议改为与 E04 主值实比（或文档声明本期仅 UI 壳） |
| N3 | mock 可补 `loadError` / `demoDenied` / `monthlyGaps` 夹具便于自测 |
| N4 | 冻结 §4.4 其余异常（材料≠来源、因子失效、边界退役）若不在七类承诺内，二轮注明「未做」即可 |

---

## 验证

```bash
python -m compileall -q server
npm run check
npm run build
```

交付：更新 `交付_E04_P3_UI实施包/` + 简短返修说明（写清 B1/B2 自测证据）。

---

## DoD（二轮）

- [ ] B1 勾稽：主值 vs 来源合计，可触发告警  
- [ ] B2 API 失败壳 + 重试闭环  
- [ ] 主值仍 12856；候选非 KPI；C03 默认折叠  
- [ ] check/build 通过  
