# Cursor 校核 · ESG智能入库一页式 V0.2

| 项 | 内容 |
|---|---|
| 日期 | 2026-07-26 |
| 分支 | `trae/carbon-page`（工作区未提交改动） |
| 对照 | `ESG智能数据填报_一页式工作台设计与联调任务书_V0.2_20260726.md` |
| 结论 | **PARTIAL**（前端一页式壳层基本到位；演示资料链 / DB 回查 / 真原文定位未达标） |

## 1. 声称交付 vs 实查

| 声称 | 实查 |
|------|------|
| `WorkspaceSmartUpload.vue` 重写 idle/uploading/parsing/ready 双栏 | **属实**。状态机含 idle→uploading→parsing→ready→done/failed；ready 左原文约 55% + 右三 Tab + 底栏 |
| `WorkspacePage.vue` 默认 smart-upload；smart-upload 隐藏 `WorkspaceNav` | **属实**。`activeNav` 默认 `smart-upload`；`v-if="activeNav !== 'smart-upload'"` |
| `dashboard.mock.ts` 顶栏「ESG智能数据填报」 | **属实**。`navItems` 三项：工作台首页｜ESG智能助手｜ESG智能数据填报 |
| 交付包 `交付_ESG智能入库一页式/` | **存在**（交付说明 + 三文件镜像） |
| `npm ci` / `check` / `build` | **check 本机复跑 EXIT:0**；build 依交付说明声明通过（本轮未重跑完整 build） |

## 2. UX / 红线抽检

| 项 | 结果 |
|---|---|
| 顶栏三入口命名 | PASS |
| 二级导航仅在 smart-upload 隐藏；其它 `?t=` Tab 仍可显 | PASS（符合「隐藏入口不删能力」） |
| Dashboard / GIS / router 碳月报路径 | **未改**（本轮 diff 仅上述 3 个前端文件） |
| 碳核算独立页 / 月报独立页 | **未合入路由**（见 §4） |

## 3. 相对 V0.2 缺口（门禁相关）

交付说明自承：**未改后端与数据库** → 本轮为 **前端联调壳 + 复用既有 parse API**，不是任务书要求的完整演示数据链。

| V0.2 要求 | 状态 | 说明 |
|-----------|------|------|
| DEMO 资料包 A–D（§7） | **缺** | 无 fixtures/`DEMO_*` 包；仅有 `public/samples/` 既有 CSV |
| 演示业务底数 + 幂等 init/cleanup（§8–9） | **缺** | 未见 DEMO-INGEST / cleanup 脚本 |
| 真 PDF/Excel 原文预览与 bbox/单元格定位（§3.2） | **弱** | 「原文」为字段块列表；`handleViewSource` 仅翻页高亮，非真实阅读器 |
| 疑似重复决策流（取消 / 新版本）（§7.3 / 状态机） | **弱** | 仅 toast 提示 DUPLICATE，无 AwaitDecision |
| 多文件「作为一个资料包」 | **弱** | 可多选上传，但解析只对 **最后一个** `fileId` 调 `startParseFile` |
| 确认入库 DB 可回查证据（§11 / 门禁 11） | **未交付** | UI 调 `confirmParseJob`；无本轮 DB 回查证据 / demo 隔离证明 |
| 设计图 PNG | **缺** | 任务书引用图入库时仍缺失 |
| 暂存待确认 | **弱** | toast 占位，无持久 draft |

**因此相对 V0.2 验收门禁：PARTIAL，不得标 PASS。**

## 4. 碳核算页（并行 · 暂停清单）

未跟踪文件已落地，**未接线**：

| 路径 | 状态 |
|------|------|
| `src/views/CarbonPage.vue` | 页壳 + 三 Tab 切换写好 |
| `src/components/carbon/CarbonNav.vue` | 概览 / 构成与边界 / 明细 |
| `src/components/carbon/CarbonOverview.vue` | 概览（panels） |
| `src/components/carbon/CarbonBoundary.vue` | 构成与边界 |
| `src/components/carbon/CarbonDetail.vue` | 明细 |
| `src/router/index.ts` | **无** `/carbon` |
| `dashboard.mock.ts` `navItems` | **无**「碳核算」「月报」 |
| `Monthly*Page` | **不存在** |

### Resume checklist（碳）

1. `navItems` 增加「碳核算」（及允许的「月报」占位）  
2. `router` 注册 `/#/carbon` → `CarbonPage`  
3. Dashboard / Workspace / Assistant `handleNav*` 互通  
4. 点验三 Tab + `?t=`；确认无硬编码 6175 主值  
5. `npm run check` / `build`；交付包 `交付_碳核算独立页/`  
6. **勿**在本恢复轮实现月报页主体（姊妹单）

## 5. 建议下一步

- **主路径（V0.2）：** 补 DEMO 包 A–D + 确定性适配器/底数 + 真原文定位或明确降级例外；跑通 §11 并附 DB 回查；再标 PASS。  
- **碳页：** 按上表 resume；与 V0.2 顶栏三入口冲突时，需产品确认顶栏是否扩为五入口（碳任务单要求扩栏）。
