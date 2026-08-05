# Codex：合并门禁 102（E02 工作台）简报

**日期：** 2026-07-23  
**目的：** 将本地已验收的 E02（门禁 102）相关改动合并进可共享主干，以便 Trae 开 103 分支。  
**前提：** 用户已确认 **102 = PASS**（见 `_handoff/E组工作台门禁台账_101_102_103.md`）。

---

## 1. 合并意图

把「E01 工作台 + E02 工作台 + GIS 联动/本体挂接」落库到 Git，避免 Trae 在脏工作区上做 103。

当前工作区大致在分支：`codex/3-full-stack-mysql-update`（以实际 `git status` 为准）。

---

## 2. 建议纳入提交的范围（业务）

### 后端 / 迁移

- `server/e_group/**`
- `server/migrations/e_group_e01_v1_1/**`（含 `V1_1_043`～`045`、E02 seed、migrate 脚本）
- `server/app.py` / `server/mysql_api.py` / `server/mysql_db.py` 中与 E01/E02 KPI、issues、detail 相关的改动

### 前端

- `src/components/e01/**`
- `src/components/e02/**`
- `src/types/e01.ts` / `src/types/e02.ts`
- `src/views/DashboardPage.vue`（工作台接入）
- `src/services/api.ts`
- `src/components/gis/GisOverviewCesiumPanel.vue`
- `src/modules/traffic-gis-overview/**`（高亮、相机、标段线宽、图例高亮等）
- `public/data/shp/manifest.json`（标段线宽统一）
- 相关 `layout.scss` / `dashboard.scss` 工作台样式

### 交接文档（建议一并进库）

- `_handoff/E02_工作台设计说明_B方案_20260723.md`
- `_handoff/E02_Trae实施任务单_V1.0_20260723.md`
- `_handoff/E02_Trae实施校核报告_20260723.md`
- `_handoff/E组工作台门禁台账_101_102_103.md`
- `_handoff/E01_二级同壳对齐_Trae实施任务单_103_20260723.md`
- `_handoff/CODEX_MERGE_102_BRIEF.md`（本文）
- `_handoff/NEXT_FOR_TRAE.md`（指向 103，且注明等合并）

---

## 3. 不要纳入（或单独丢弃）

- `_tmp_*.py` / `_tmp_*_out.txt` / `check-output*.txt` / `vue-tsc-errors.txt`
- `dashboard_*.png`、随意截图（除非明确要进 `_handoff/e01_screenshots`）
- `交付_E组V1.1*/**`、`交付_E02*/**` 大包（若需归档另开 docs 提交）
- 含密钥的 `.env`、真实上传目录

---

## 4. 建议提交信息

```text
feat: E02 workbench (gate 102) with body GIS links

Ship E01/E02 demo workbenches, E02 closure popover, and map
selection without leader lines. Record gate 102 PASS; 103 task
book ready after merge.
```

---

## 5. 合并后动作

1. 推远程并开/更新 PR → 目标 `main`（或团队约定集成分支）  
2. CI：`npm run check` / `npm run build`；`python -m compileall -q server`  
3. CI 绿且无阻塞审查后合并  
4. **门禁 103（与 E02 同流程）：** 请 Codex **校核设计**（不是直接建实现 Issue）：  
   `_handoff/E03_工作台设计说明_B方案_20260723.md`  
   意见退回 Cursor；冻结 V1.0 后再让 Trae 按 `_handoff/E03_Trae实施任务单_*.md` 开工  
5. 102 合并与 103 设计校核可并行，但 Trae 实现 103 必须等设计冻结  

---

## 6. 合并验收速查

| 项 | 期望 |
|----|------|
| E02 KPI formal | 0 |
| E02 demo 列表 | 未闭环 > 0，有演示角标 |
| E02 二级 | 地图内弹窗；空白可关 |
| GIS | D01→弃渣、D02/D07→水源、D03→弃渣2、D04→边坡、D05→生态 |
| 引导线 | 无 |
