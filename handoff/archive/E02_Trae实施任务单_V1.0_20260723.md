# E02 Trae 实施任务单（V1.0 冻结稿配套）

**日期：** 2026-07-23  
**权威设计：** `_handoff/E02_工作台设计说明_B方案_20260723.md`（**V1.0 设计冻结稿**）  
**实施方：** Trae  
**二轮修正 / 对照验收：** Cursor（本会话代理）  
**Codex：** 验收评审（实现完成后）

---

## 0. 角色与协作

| 角色 | 职责 |
|------|------|
| Trae | 按本任务单完成 P1→P3（演示版可交付），提交可运行代码与自测说明 |
| Cursor | 对照冻结稿做二次修正（口径偏差、空态、主源过滤、壳一致性） |
| Codex | 验收是否满足冻结稿 |

**禁止：** 改 B 路线、加 L3、加「发起督办」、双表 KPI 相加、改正式 GIS 要素几何、把 demo 混进正式计数。

---

## 1. 目标（演示版可验收）

首页点击 **E02** → 进入与 E01 **同壳**的右侧一级总览 + 地图联动 → 点事项打开 **二级地图锚定闭环分析弹窗**。

- 正式部署 / `scope=formal`：未闭环正式数 **0**（甲方无真实事项）  
- 演示部署（服务端允许 demo）：卡片与工作台显示演示未闭环数，**全程「演示数据」角标**  
- 旧 `KpiDetailModal` E02：可暂留兼容，但 **KPI 默认进工作台**（对标 E01）

**本轮不做：** 真实督办流、完整附件预览引擎（无预览能力就不要放「预览」按钮）、切 KPI 主源到案卷表（仍处**切换前**）、E03/其他 KPI 改造。

---

## 2. 必读现状（动手前）

| 位置 | 说明 |
|------|------|
| `src/views/DashboardPage.vue` | E01 工作台接入样板；E02 仍走 `KpiDetailModal` |
| `src/components/e01/E01WorkspacePanel.vue` | 一级面板壳、分页、统计筛选 |
| `src/components/e01/E01MapSummaryCard.vue` | **现状**仍是右下角卡；冻结稿要求 E01/E02 二级均为**地图锚定弹窗**。本任务：**E02 必须做锚定弹窗**；E01 二级壳对齐可作为 **P3.5 可选**（若时间紧，先保证 E02 正确，并在 PR 注明 E01 母版对齐待 Cursor 二轮） |
| `src/components/gis/GisOverviewCesiumPanel.vue` | E01 markers / 选中联动 |
| `src/modules/traffic-gis-overview/...` | Cesium 高亮、相机、要素渲染 |
| `server/mysql_api.py` | `E02` KPI 当前：`COUNT(*) FROM env_issue_record WHERE issue_status<>'已闭环'`（**未过滤 demo**） |
| `get_e02_env_issue_detail` | 旧弹窗；硬编码 GIS map |
| `server/e_group/enums.py` | `E02_ENV`、EvidenceRole、CaseStatus |
| `server/migrations/e_group_e01_v1_1/V1_1_020__closure_case_tables.sql` | 案卷/证据/轨迹/关系表 |
| 既有种子 | `env_issue_record` id `420001–420005` 等可能抬高正式 KPI → **P1 必须处理**（标 demo 或迁出正式计数） |

---

## 3. 阶段划分与交付物

### P1 — 演示测数与双写（先做，可独立验收）

#### P1.1 Schema 闸

1. 检查 `env_issue_record` 是否有 `is_demo`、`data_nature`（及是否需要 `business_code`）。  
2. **若缺失**：新增迁移（建议路径  
   `server/migrations/e_group_e01_v1_1/V1_1_043__e02_env_issue_demo_fields.sql`  
   或独立 `e_group_e02` 目录，与现有 migrator 约定一致即可）。  
3. Check 约束建议对齐案卷：`(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)`。  
4. **存量处理（必须）：**  
   - 现有未闭环行若为演示/验收种子 → 一律标 `demo`/`is_demo=1`  
   - 保证：`COUNT formal 未闭环 = 0`  
   - 水保类型勿再作为 E02 演示主路径（E03 边界）

#### P1.2 双写种子（每条演示事项）

对设计稿 §11 的 **E02-D01～D07**：

| 步骤 | 表 | 要求 |
|------|-----|------|
| A | `env_issue_record` | `is_demo=1`,`data_nature='demo'`；中文 `issue_status`；`overdue`；`deadline`；`issue_type` 非水保；`business_code`/`issue` 编号与 D0x 对齐 |
| B | `e_closure_case` | `case_domain='E02_ENV'`；`source_table='env_issue_record'`；`source_record_id`=A.id；`source_business_key`=D0x；状态英文字段；`effective_status='EFFECTIVE'`（MERGED/CLOSED 按设计）；`is_demo=1` |
| C | `e_case_party` | 发现/整改/复查（销项）角色 |
| D | `e_case_status_history` | ≥2 条；**D07 含复查退回**轨迹与原因 comment |
| E | `e_case_evidence` | 按状态/轮次挂角色；无真实文件可用元数据占位，`evidence_role` 正确；**不得**用普通 status_history 冒充 `CLOSURE_DOCUMENT` |
| F | GIS 关系 | `gis_feature_business_relation`（`environment_problem`）关联**已有** featureId；案卷 `gis_feature_id` 可填主关联；**禁止 UPDATE 正式要素坐标/几何** |
| G | 可选 | `document_record` 占位文档行 |

**D05 销项：** 优先附件型证据；若用等价确认，必须满足设计 §8.4（确认人、时间、意见、依据 + 权限模拟字段），写入 evidence，**不是**仅一条 CLOSED history。

**D06 MERGED：** 台账状态计入「已合并」或不在未闭环集合；案卷 `MERGED`；**不进**演示未闭环 KPI。

建议 id 段：台账 `421001+`（避开 420001 旧段并迁移旧段为 demo），案卷 id 自增或约定段，**幂等**：迁移可重复执行（先删 demo 业务键再插，或 `INSERT ... ON DUPLICATE` / 存在则 skip）。

#### P1.3 P1 自验 SQL（写入 PR/报告）

```sql
-- 正式未闭环必须为 0
SELECT COUNT(*) FROM env_issue_record
 WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
   AND is_demo=0 AND data_nature='formal';

-- 演示未闭环（期望约 4：D01–D04；D07 若仍整改中也计入；D05/D06 不计）
SELECT COUNT(*) FROM env_issue_record
 WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
   AND is_demo=1 AND data_nature='demo';

-- 一对一
SELECT c.case_code, c.source_record_id, i.id
  FROM e_closure_case c
  JOIN env_issue_record i ON i.id=c.source_record_id
 WHERE c.case_domain='E02_ENV' AND c.is_demo=1;
```

**P1 完成定义：** 上库可查；正式 0；演示未闭环 >0；每条有案卷+轨迹+证据角色；GIS 仅关系、未改要素。

---

### P2 — 读数 API（切换前主源）

#### P2.1 服务端 demo 闸

- 配置项（择一落地，写清默认值）：如环境变量 `E02_ALLOW_DEMO=1` 或现有 app config。  
- **演示部署默认允许**；正式部署默认拒绝 `scope=demo`。  
- 拒绝时：HTTP 403 或返回空 formal 集 + 明确 `code`；打日志。  
- **禁止**仅靠前端 query 在正式环境读出 demo。

#### P2.2 KPI

改造 `get_dashboard_kpis`（或等价）中 E02：

```text
formal: COUNT env_issue_record 未闭环 AND is_demo=0 AND data_nature='formal'
demo:   仅当 allow_demo 时 COUNT ... is_demo=1 AND data_nature='demo'
```

响应增加：`dataNature` / `isDemo` / `scope`，供卡片角标。  
**不得**把两表 count 相加；**不得**再用「全部未闭环不加 demo 过滤」。

#### P2.3 列表与详情 API

建议：

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/environment/e02/issues` | overview 统计 + issues + spatialLinks |
| GET | `/api/environment/e02/issues/{id}` | 二级详情 |

查询参数：`scope=formal|demo`（受闸门约束）。

**列表项建议字段：**  
`id, businessCode, title, issueType, locationText, status, statusGroup(整改中|待复查|待销项|暂缓), overdue, deadline, responsibleOrgName, canLocate, spatialLinks[]`

**overview：**  
`total, rectifying, pendingReview, pendingClosure, suspended?(可选), overdueAmong`  
状态归组严格按冻结映射（DISCOVERED/PENDING_RECTIFICATION/RECTIFYING→整改中 等）。台账中文状态需映射到同一 group。

**spatialLinks：**  
`{ featureId, geometryType, role, isPrimary }`  
从关系表 + 案卷主关联组装；**不要**只返回虚构 lon/lat 点数组当唯一空间表达。

**详情：**  
进度、当前进展文案、party、statusHistory、evidence（按角色）、`materialCompleteness`（见下）、deadline/overdue、spatialLinks。

#### P2.4 材料完整度（服务端算，前端只展示）

实现设计 §8：

- 输入：当前状态、历史最高阶段、整改轮次、已挂 `evidence_role`、是否退回  
- 输出示例：

```json
{
  "requiredRoles": ["FORMAL_NOTICE", "RECTIFICATION_MATERIAL", "REVIEW_OPINION"],
  "coveredRoles": ["FORMAL_NOTICE", "RECTIFICATION_MATERIAL", "REVIEW_OPINION"],
  "pendingRoles": ["RECTIFICATION_MATERIAL"],
  "ratio": "3/4",
  "notes": ["本轮整改材料待补"]
}
```

- D07 类：退回后**不得**变成仅通知单 1/1  
- `CLOSURE_DOCUMENT` 覆盖：附件 **或** §8.4 等价确认；普通 CLOSED 轨迹不算  

#### P2.5 旧接口

- `get_e02_env_issue_detail`：加 demo 过滤，避免正式弹窗混 demo；或标记 deprecated。  
- 硬编码 `e02_gis_feature_map`：P2/P3 改为读关系表。

#### P2.6 注册路由

`server/app.py` 注册新路由；`src/services/api.ts` + `src/types/e02.ts` 类型。

**验证：** `python -m compileall -q server`

---

### P3 — 前端工作台 UI

#### P3.1 Dashboard 接入

在 `DashboardPage.vue`：

- `kpiKey==='E02'` → `openE02Workspace()`（对标 E01），**不要**默认开 `KpiDetailModal`  
- 与 E01 互斥：开 E02 关 E01，反之亦然  
- 右侧槽复用 `.dashboard-right` / E01 工作台 class 模式（可 `is-e02-workspace`）  
- 地图业务链 `openKpiFromBusinessLink` target E02 → 进入工作台并选中对应事项（若多事项见下）

#### P3.2 `E02WorkspacePanel.vue`（一级）

对标 `E01WorkspacePanel`：

- 标题「未闭环环保问题」+ 演示角标（`scope/demo`）  
- 统计：全部｜整改中｜待复查｜待销项；**其中逾期**叠加（文案勿让用户以为五格相加）  
- 列表字段见设计；默认分页 **3**（常量，同分辨率不跳变）；分页栏始终可见  
- 空态 / 加载 / 错误+重试  
- 关闭：退出工作台、清选中与高亮  

宽度：**复用 E01 容器**，勿另写死 66/34；可在注释或 README 回填实际 class。

#### P3.3 `E02ClosureAnalysisPopover.vue`（二级）

- **地图锚定**弹窗（非右下角固定迷你卡）  
- 内容：进度条、当前进展、责任、页签（闭环进展｜证据材料）、期限  
- 材料按钮：仅 预览（已实现）/ 下载 / 暂无材料；**禁止**无响应预览、禁止督办  
- 状态：加载中、失败+重试、无轨迹、无证据、GIS 不可用  

#### P3.4 关闭与空白点击（行为唯一）

关闭二级或点地图空白：

1. 保留一级筛选与页码  
2. 保留当前地图视角  
3. 取消事项选中与强高亮  
4. 恢复筛选结果的普通高亮  

#### P3.5 地图联动

- 打开 E02：按筛选高亮关联 **点/线/面**（HighlightManager / 现有 renderer）  
- flyTo / fit：**扣除右侧面板 + 顶栏 + 底时间轴** 后的有效可视区  
- 弹窗屏幕坐标随 camera 变化重算；右侧不足翻左侧  
- 无 GIS：列表「无法定位」；弹窗安全默认位  
- **一要素多事项：** 先出示选择列表，禁止随机开一条  
- 演示全程角标，避免「该点真发生过问题」的误解  

#### P3.6 E01 母版对齐（可选本轮）

若余力：将 `E01MapSummaryCard` 改为同壳锚定弹窗（内容仍为趋势）。  
若无余力：PR 明确「E02 已按冻结壳；E01 壳对齐交 Cursor 二轮」。

#### P3.7 前端验证

```bash
npm ci
npm run check
npm run build
```

（若环境限制，在交付说明写明原因与替代验证。）

---

## 4. 文件清单（预期新增/修改）

**新增（建议）**

- `server/migrations/.../V1_1_043__e02_*.sql`（字段 + seed，或拆 043 字段 / 044 seed）  
- `src/types/e02.ts`  
- `src/components/e02/E02WorkspacePanel.vue`  
- `src/components/e02/E02ClosureAnalysisPopover.vue`  
- （可选）`src/components/e02/E02FeatureIssuePicker.vue` 多事项选择  

**修改**

- `server/mysql_api.py`（KPI + e02 issues/detail + 完整度）  
- `server/app.py`  
- `src/services/api.ts`  
- `src/views/DashboardPage.vue`  
- `src/components/gis/GisOverviewCesiumPanel.vue`  
- `src/modules/traffic-gis-overview/components/TrafficGisOverview.vue`（及高亮/相机相关）  
- `src/styles/layout.scss`（e02 workspace class，复用 e01 槽）  
- 必要时 `server/e_group/enums.py`（白名单 source_table 含 `env_issue_record`）

**不要改：** 无关 KPI、正式 GIS 坐标 seed、E01 业务口径（除非做壳对齐）。

---

## 5. 验收清单（Trae 自测 + Codex/Cursor）

| # | 项 | 期望 |
|---|-----|------|
| 1 | 正式 KPI | 0 |
| 2 | 演示 KPI | = 演示未闭环台账数；有角标 |
| 3 | 双写 | 每条 demo 台账↔案卷 1:1 |
| 4 | 双表相加 | 不存在 |
| 5 | D07 材料 | 退回后完整度不退化成 1/1 |
| 6 | D05 销项 | 附件或 §8.4 确认；非裸 history |
| 7 | 一级 | 统计映射正确；逾期叠加；分页 |
| 8 | 二级 | 锚定+避让；内容为闭环分析 |
| 9 | 关闭/空白 | 保筛选页码视角；取消强选中 |
| 10 | GIS | 真实几何高亮；未改正式要素 |
| 11 | 多事项 | 选择列表 |
| 12 | demo 闸 | 正式部署无法只靠 URL 拉 demo |
| 13 | 无伪入口 | 无督办；无哑预览按钮 |
| 14 | 编译 | `compileall` + 前端 check/build |

---

## 6. 交付给 Cursor 二轮修正时请附

1. 变更文件列表与迁移编号  
2. 正式/演示 COUNT 截图或 SQL 结果  
3. 已知未做项（如 E01 壳、附件预览）  
4. 本地启动方式（端口、是否 `E02_ALLOW_DEMO=1`）  
5. 与冻结稿偏差说明（若有，须极短）

---

## 7. 给 Trae 的一句话

> 严格按 V1.0 冻结稿做 E02：**P1 双写测数 → P2 台账单源 API + demo 闸 → P3 一级面板 + 地图锚定二级弹窗**；正式 KPI 保持 0；不要改路线、不要做其它首页 KPI。

---

**任务单版本：** V1.0  
**对应设计：** E02 工作台设计说明 B 方案 V1.0 冻结稿  
