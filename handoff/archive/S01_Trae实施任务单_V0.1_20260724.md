# S01 Trae 实施任务单 · 草稿（配套设计 V0.1）

**版本：** V0.1 草稿  
**日期：** 2026-07-24  
**门禁建议：** 105  
**状态：** **冻结前禁止开工。** 不得创建实现 Issue、不得改库/改测数、不得开 Trae 分支。  
**配套设计：** `_handoff/S01_连续安全生产天数设计说明_B方案_V0.1_20260724.md`  

---

## 0. 使用说明

仅在设计 **V1.0 冻结** 且本任务单升为 P1/P2/P3 正式版后，Trae 方可按阶段实施。

建议拆分（冻结后）：

| 阶段 | 内容 |
|------|------|
| P1 | Schema + 测数重建（起算 2026-05-08） |
| P2 | API 状态机 + 验收基线从 368 迁移 |
| P3 | `S01SafetyProductionModal` + 首页重置信息 |

---

## 1. P1（预告）范围

- 为 `safety_production_record` / `safety_incident_record` 补 `is_demo`、`data_nature`、死亡/认定字段、确认状态等（以冻结稿为准）  
- 重建测数：`project_start_date=2026-05-08`；阶段日期对齐开工后；默认无生效重置  
- 写入幂等迁移（优先 `server/migrations/e_group_e01_v1_1/` 下一号，或独立 `s01` 迁移目录——冻结时裁定）  

**非目标：** UI 大改；上传解析联动（可后置）。

---

## 2. P2（预告）范围

- `get_s01_detail`：按冻结口径计算天数与 `pending`  
- `/api/dashboard/kpis` S01 同源  
- 更新 `s01_safety_production_business_test.py`、`dashboard_acceptance_test.py` 中 **368** 基线  

---

## 3. P3（预告）范围

- 模态字体/布局对齐 E 组演示态收敛  
- 摘要展示统计起点、期末、最近重置  
- 前端禁止用本地开工日覆盖后端 `continuousDays`  

---

## 4. 验证（冻结后填写具体命令）

前端：`npm ci` → `npm run check` → `npm run build`  
后端：`python -m compileall -q server` + S01 专用验收  

---

## 5. 当前禁止事项

- [ ] 不得把 2025-07-10 / 368 直接改掉却无冻结稿  
- [ ] 不得把隐患/未遂写成重置事故  
- [ ] 不得新开地图工作台壳  
