# ESG 智能助手 · 数据库驱动问答实现方案

| 项 | 内容 |
|----|------|
| **版本** | V0.1 |
| **日期** | 2026-07-26 |
| **状态** | **草案 · 待确认**（本主题代码冻结，勿开工实现） |
| **范围页** | `/#/assistant`（`AssistantPage`） |
| **原则** | 回答数字与清单来自 MySQL / 现有 API 聚合；禁止固定 FAQ 业务数 |

---

## 1. 现状问题

| 问题 | 说明 |
|------|------|
| **一问多用同一回答** | `AssistantPage.handleSendMessage` 无论用户点选/输入何问题，均调用 `createEnvIssuesAnswer()`，返回同一套「未闭环环保问题」固定文案与表格。 |
| **固定文案与首页口径脱节** | `src/data/assistant.mock.ts` 内写死「12 项未闭环」等数字；首页 KPI / E02 API 口径可能是其他值（如未闭环 5），演示易穿帮。 |
| **推荐问题无独立数据路径** | 欢迎区 5 问、侧栏快捷能力 5 项、最近会话标题、跟进追问等均未映射到真实查询。 |
| **语音仅为假录** | `AssistantInput.toggleRecording` 用 `setTimeout` 填入固定句子，未接 Web Speech，也未走统一问答链路。 |

**结论：** 当前助手是「UI 壳 + 单条 mock 回答」，不具备按问题查库、动态摘要的能力。

---

## 2. 目标

1. **页面上出现的每一个可点击/可发送问题**，发送后走统一问答链路，得到**该问题对应**的、基于库表/现有 API 的动态回答。
2. 回答结构专业、可验收：短结论 + KPI 数字卡 +（可选）清单表 + 口径/数据依据 + 可下钻链接；**业务数字禁止写死在前端 mock**。
3. **无数据 / 查询失败**：友好空态或错误态（如「当前暂无未闭环环保问题」「数据暂不可用，请稍后重试」），不回落成另一条问题的假数据。
4. **会话能力保留**：新建会话、历史消息列表行为不破坏；不改首页 KPI 展示结构与数据口径。
5. **外部 LLM 非必依赖**：离线/无 Key 环境必须可用；LLM 仅作可选润色增强。

---

## 3. 架构（建议）

```text
前端 AssistantPage
  └─ POST /api/assistant/ask  { question, sessionId? }
        │
        ▼
后端 assistant 模块
  ├─ 1) Intent 路由：问题文本 → intent_key（模板/关键字/归一化匹配）
  ├─ 2) Data 聚合：按 intent 调用现有 mysql_api / 已有 /api/... 逻辑（复用，不重算口径）
  ├─ 3) Answer 模板：把查询结果填入结构化 ChatMessage（content / kpiCards / tableData / dataBasis / followUps）
  └─ 4) 返回 JSON；前端替换 loading 气泡
```

| 层 | 职责 | 建议落点 |
|----|------|----------|
| **前端** | 发问、渲染富消息、空态；推荐问题/快捷能力/跟进均 `emit` 同一 `send` | `AssistantPage.vue`；`api.ts` 增加 `askAssistant` |
| **Intent 路由** | 将自然语言/固定文案映射到 `intent_key`；未知 intent → 引导话术 + 推荐已支持问题 | `server/assistant/intent_router.py`（新建，薄） |
| **数据聚合** | **优先复用**已有函数（如 `get_e02_issues`、`get_s02_risks`、`get_dashboard_kpis`、`get_monthly_report_overview` 等），保证与首页/工作台同口径 | `server/mysql_api.py` 已有逻辑；必要时薄封装 `server/assistant/data_fetchers.py` |
| **回答组装** | 模板字符串 + 插值；数字一律来自 fetcher 返回值 | `server/assistant/answer_templates.py` |
| **API 入口** | 单端点即可（P1） | `POST /api/assistant/ask`（`app.py` / `mysql_api`） |

**口径铁律：** Intent 对应指标的筛选条件、状态枚举、累计口径，必须与现有 KPI/工作台 API **同源同函数**，禁止助手侧另写一套 SQL「近似统计」。

---

## 4. 问题清单盘点方法

### 4.1 盘点来源（当前页面）

| 来源 | 文件/位置 | 当前条目（示例） |
|------|-----------|------------------|
| 欢迎推荐问题 | `welcomeQuestions`（`assistant.mock.ts`） | 未闭环环保问题；较大及以上安全风险点；累计碳排放；月报待处理；E/S/G 总体情况 |
| 快捷能力 | `quickCategories` → 点击发 `cat.name` | 环境 E / 社会 S / 治理 G / 碳专题 / 月报专题 |
| 最近会话标题 | `recentSessions[].title` | 与欢迎问题部分重叠 + 逾期整改、三标段安全风险等 |
| 跟进追问 | `createEnvIssuesAnswer().followUps` | 查看逾期事项；按责任部门统计；查看三标段问题；导出问题清单 |
| 自由输入 | 输入框 | P1 仅覆盖已注册模板；未命中给引导 |

**方法：** 从上述数组/文案做**去重全集** → 每条填「intent_key / 数据源（API 或表） / 回答模板 ID / 空态文案 / 下钻目标」→ 评审确认后再编码。

### 4.2 初版映射表（草案 · 待确认）

| # | 页面问题 / 触发文案 | 建议 intent | 优先数据源（现有） | 备注 |
|---|---------------------|-------------|-------------------|------|
| 1 | 当前有哪些未闭环环保问题？ | `e02.open_issues` | `GET /api/environment/e02/issues` → `get_e02_issues` | 与 E02 工作台同口径 |
| 2 | 当前较大及以上安全风险点有多少？ | `s02.active_major_risks` | `GET /api/social/s02/risks` / KPI S02 | 在管较大及以上 |
| 3 | 项目累计碳排放是多少？ | `e04.cumulative_carbon` | KPI E04 / carbon 相关 API | 与首页累计 tCO₂e 同源 |
| 4 | 本月还有哪些月报资料待处理？ / 本月月报资料待处理情况 | `monthly.pending` | `/api/monthly-report/readiness` 或 `get_monthly_report_overview` | 待办清单摘要 |
| 5 | 查看 E/S/G 三类指标总体情况 | `kpi.esg_overview` | `GET /api/dashboard/kpis` | 聚合三组 KPI 卡片，不改首页结构 |
| 6 | 当前有哪些逾期整改事项？ / 查看逾期事项 | `cross.overdue_rectify` | E02/E03/G 等逾期筛选聚合 | P1 可先 E02 逾期；P2 补全 |
| 7 | 三标段安全风险情况 | `s02.segment_3` | S02 risks + 标段过滤 | 缺字段则 P2 补查询 |
| 8 | 环境 E / 社会 S / 治理 G | `kpi.group_E` / `_S` / `_G` | `get_dashboard_kpis` 分组 | 快捷能力入口 |
| 9 | 碳专题 | `carbon.topic` | carbon benefit / E04 详情 | |
| 10 | 月报专题 | `monthly.topic` | monthly-report topic | |
| 11 | 按责任部门统计 | `e02.by_department` | E02 issues 聚合 | 跟进问 |
| 12 | 查看三标段问题 | `e02.segment_3` | E02 + 标段过滤 | 跟进问 |
| 13 | 导出问题清单 | `e02.export_hint` | 不真导出文件；返回「请至 E02 工作台导出」+ 链接 | P1 文案引导即可 |

盘点完成后输出一张「问题—意图—API—验收 SQL/接口」表，作为实施任务单附件。

---

## 5. 回答模板设计

### 5.1 统一结构（对齐现有 `ChatMessage`）

| 区块 | 字段 | 规则 |
|------|------|------|
| 结论一句 | `content` | 含**查询得到的数字**与截止日期；无数据时用空态句，不编造 |
| 关键数字 | `kpiCards[]` | value 来自 API；label/unit 可配置，value 不可写死 |
| 清单（可选） | `tableData` | rows 来自查询前 N 条；`total` 为真实总数 |
| 口径与依据 | `dataBasis` | scope / updateTime / sources / caliber；核验状态按真实字段，禁止「测试数据」「未确认」类 UI 铬条；可写「建设单位确认口径」中性表述 |
| 继续查询 | `followUps[]` | 仅挂**已实现 intent** 的追问文案 |

### 5.2 模板示例（数字均为占位符，实现时插值）

```text
结论：截至{as_of}，项目当前未闭环环保问题共 {open_count} 项，其中整改中 {rectifying}、待复查 {recheck}、待销项 {to_close}。
KPI：未闭环总数 / 各办理状态计数（来自 get_e02_issues 聚合）
表：前 5 条问题名称、标段、责任部门、截止日期、办理/时限状态
依据：统计范围=项目全线；口径说明=与 E02 工作台一致；来源表/接口名
下钻：工作台 E02 / 事项详情 deep-link（路由参数待确认）
```

### 5.3 空态 / 失败

| 场景 | 行为 |
|------|------|
| 查询成功且 count=0 | 结论说明「暂无…」；可省略表或给空表提示；仍给口径与相关入口 |
| API/DB 失败 | 简短错误结论 + 重试建议；不展示假 KPI |
| Intent 未识别 | 说明当前支持的问题清单（来自注册表），引导点击推荐问题 |

### 5.4 禁止事项

- 前端/后端模板中写死业务数量（如「12 项」「6175 tCO₂e」作为常量答案）。
- 助手专用 SQL 与 KPI 口径不一致。
- UI 出现「测试数据」「未确认」「演示数据」等铬条文案（内部 `data_nature` 可不暴露）。

---

## 6. 语音输入（二期 · 本方案仅预留）

| 项 | 说明 |
|----|------|
| **时机** | **P3**；P1/P2 不改 `AssistantInput` 录音逻辑亦可，或先去掉假录音以免误导 |
| **技术** | 浏览器 Web Speech API（`SpeechRecognition` / `webkitSpeechRecognition`），Chrome 优先 |
| **行为** | 点击麦克风 → 听取 → **仅将转写文本填入输入框** → 用户确认发送（或可选自动发送）→ **同一** `/api/assistant/ask` 链路 |
| **降级** | 不支持时 Toast/hint：「当前浏览器不支持语音输入，请使用文字」 |
| **不做** | 服务端 STT、录音上传（除非后续另开需求） |

---

## 7. 分期

| 阶段 | 内容 | 验收要点 |
|------|------|----------|
| **P1** | Intent 注册表覆盖页面全部展示问题；读**现有** API/函数组装回答；前端改 `handleSendMessage` 调新接口；去掉「凡问皆 E02 mock」 | 点选每一推荐问题/快捷能力 → 数字与对应工作台或首页 KPI **一致**；无数据空态正确 |
| **P2** | 补缺口查询（跨模块逾期聚合、标段过滤、部门统计等现有 API 不足处）；会话点击加载真实问答历史（若需要） | 跟进问与会话标题全覆盖；缺口有接口或明确降级文案 |
| **P3** | Web Speech 语音填入输入框 | Chrome 可转写；不支持浏览器有提示；仍走 P1 链路 |

**建议顺序：** 先完成 §4 映射表确认 → 再开 P1 任务单 → 禁止并行做固定 FAQ 文案方案。

---

## 8. 非范围

| 不做 | 说明 |
|------|------|
| 改首页 KPI 展示结构 / 卡片布局 / 指标口径 | 助手只**读**同源数据 |
| 外部 LLM Key 作为必依赖 | 可选增强润色 `content` 句式，失败须回落模板句 |
| 本轮实现语音 / 改助手业务代码 | **代码冻结至方案确认** |
| 真文件导出、权限改造、多租户 | 超出本主题 |
| 大改聊天 UI 视觉体系 | 沿用现有 `AssistantMessage` 富内容结构即可 |

---

## 9. 待确认项

1. **权威口径源：** 助手数字以「首页 KPI 快照」为准，还是以「各工作台 list API」为准？（建议：单指标跟工作台 list/detail，总览跟 `get_dashboard_kpis`，并在 dataBasis 写明。）
2. **时间锚点：** `as_of` 用服务器当前时间，还是业务「数据更新时间」字段？
3. **下钻链接：** 跳转首页 KPI 弹窗、E02/S02 Workspace，还是 GIS？路由参数约定？
4. **最近会话：** P1 是否仅「点击标题 = 重新提问」即可，还是要持久化会话历史表？
5. **「导出问题清单」：** P1 引导文案是否足够，是否需要后端生成文件？
6. **未命中 intent：** 是否允许极轻量关键字模糊匹配，还是严格白名单？
7. **验收环境：** 以当前 MySQL seed（如 S02 在管 8）为黄金数，还是另备助手验收脚本？
8. **LLM 可选增强：** 是否进 P2+  backlog，默认关闭？

---

## 10. 实施前检查清单（确认后交给 Trae）

- [ ] §4 映射表签字/确认
- [ ] 每个 intent 注明复用的函数名与验收对比接口
- [ ] 空态文案表确认
- [ ] 出 Trae 任务单（P1），明确勿动首页 KPI
- [ ] 本主题在确认前 **不改** `assistant.mock` 业务数、不接假 FAQ、不实现语音

---

## 11. 相关文件（只读参考 · 非本轮修改）

| 路径 | 用途 |
|------|------|
| `src/views/AssistantPage.vue` | 发问入口（现状：统一 mock 回答） |
| `src/data/assistant.mock.ts` | 推荐问题 / 现唯一富回答 |
| `src/components/assistant/*` | 欢迎区、侧栏、输入、消息渲染 |
| `src/types/assistant.ts` | `ChatMessage` 结构 |
| `src/services/api.ts` | 现有 KPI / E02 / S02 / monthly 客户端 |
| `server/mysql_api.py` | 同源数据函数 |

---

**文档状态：** V0.1 草案，待产品/甲方确认 §9 后升版并出 P1 任务单。在此之前：**助手问答与语音相关代码冻结。**
