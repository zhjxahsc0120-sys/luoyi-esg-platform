# BASELINE · Workspace UI polish · 2026-07-26

| 项 | 内容 |
| --- | --- |
| **日期** | 2026-07-26 |
| **分支** | `trae/workspace-nav-s02s03` |
| **Tag** | `baseline/workspace-ui-20260726` |
| **Commit** | `38385dc47e4ea612fbdeb02694534748140657b0` |
| **用途** | Workspace UI 打磨快照；后续「右侧碳与月报」Trae 工作的**开工基线**与回退点 |

## 与旧基线共存

| Tag | 保护范围 | 用途 |
| --- | --- | --- |
| `baseline/l1-l2-gis-20260726` | 首页 Dashboard L1/L2、GIS、e01/e02/e03/s02 等 | **首页受保护**；勿覆盖/删除本 tag |
| `baseline/workspace-ui-20260726` | Workspace 壳层 UI 打磨 + 填报入口相关产品态 | **碳/月报右侧栏**从此 tag 开工；出问题回退本 tag |

两个 tag **同时保留**。回退 Workspace 打磨时用本文件；回退首页 GIS/L1L2 时用 `_handoff/版本回退_baseline_l1-l2-gis_20260726.md`（或等价基线说明）。

## 恢复命令（只读检视 / 回退对照）

```bash
git fetch origin --tags
git switch --detach baseline/workspace-ui-20260726
```

恢复到可继续开发的分支 tip（在确认需要丢弃后续提交时，由负责人执行；本说明不要求 force 操作）：

```bash
git switch trae/workspace-nav-s02s03
# 若需把工作区对齐到本 tag（危险：会丢弃未备份改动，须先确认）
# git reset --hard baseline/workspace-ui-20260726
```

## 本快照包含（产品相关）

- `src/views/WorkspacePage.vue`
- `src/components/workspace/**`（Home / Nav / Tasks / SmartUpload / Review / Documents 等）
- `src/styles/workspace.scss`
- `_handoff` 中与 Workspace 碳/月报设计、实施任务单、本基线说明相关的文档指针

## 明确未纳入本提交的垃圾/临时物

`_tmp_*`、`__pycache__`、日志、巨型 `交付_*` 包、截图杂物、未跟踪的 `server/storage` 等——除非此前已跟踪。

## Trae 下一单入口

- 任务单：`_handoff/碳核算与月报独立页/作废/Trae实施任务单_Workspace右侧碳与月报_V1.0_20260726.md`
- 设计：`_handoff/碳核算与月报独立页/作废/Workspace右侧_碳与月报模块设计_V0.1_20260726.md`
- **必须从** `baseline/workspace-ui-20260726` 对应提交起做碳/月报右栏；破损时恢复本 tag。
