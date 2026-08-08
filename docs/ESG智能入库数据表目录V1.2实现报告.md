# ESG 智能入库数据表目录 V1.2 — 实现报告

> 日期：2026-08-08  
> 范围：仅前端智能入库页（`WorkspaceSmartEntry`）  
> 未修改：后端、数据库、首页、E01 二级分析、地图

## 一、页面结构

```text
ESG 智能入库（标题）
标准数据表上传、校验与入库确认（副标题）
  ↓
数据表目录（搜索 + 筛选 + 分组表格）
  ↓
E01 V1.2 双模板下载（点位 / 结果）
  ↓
新建上传区（拖拽 / 行内上传 / 依赖提示）
  ↓
校验结果（统计 + 明细表 + 错误下载占位）
  ↓
入库影响预览 + 确认入库
  ↓
最近入库批次（会话内记录；无历史 API 时空态）
```

智能入库页进入时 **隐藏** `WorkspaceNav` 工作台内部导航，其他路由与组件保留。

## 二、修改文件清单

| 文件 | 说明 |
|---|---|
| `frontend/src/data/esg-data-catalog.ts` | **新增** 数据表目录配置（E01 可上传 + E02–G04/碳排/扩展登记） |
| `frontend/src/utils/esg-import-presenter.ts` | **新增** API→展示模型、识别/校验映射 |
| `frontend/src/components/workspace/WorkspaceSmartEntry.vue` | **重写** 目录 + 上传工作区 |
| `frontend/src/views/WorkspacePage.vue` | `smart-upload` 时隐藏 `WorkspaceNav` |

## 三、未修改文件清单（边界内）

- `backend/**`（含 `esg_excel_import.py`）
- `DashboardPage.vue`、E01 二级分析组件、Cesium 地图
- 其他工作台路由/组件（`WorkspaceTasks`、`WorkspaceReview` 等）
- 全局 `SCREEN_WIDTH/HEIGHT` 与 scale 逻辑

## 四、数据字段映射（页面展示）

| 数据库/API | 页面 |
|---|---|
| `template_code` | 不直接展示；映射为数据表名称 |
| `point_code` 等英文字段 | 校验明细中转为中文列名（如「点位编号」） |
| `PASS` / `FAIL` 等 | 不展示；使用「校验通过/失败」「正常/异常」 |
| `recognize.template_version` | 「V1.2」模板版本标签 |
| `validation.errors[].message` | 「修改建议」；含「请先导入点位表」→「请先建立对应点位」 |

## 五、API 调用

| 接口 | 用途 |
|---|---|
| `POST /api/esg/import/upload` | `uploadEsgExcelImport(file, expectedTemplate?)` |
| `POST /api/esg/import/confirm` | `confirmEsgExcelImport(batchCode)` 人工确认入库 |
| `GET /templates/esg/...` | E01 V1.2 模板下载（后端静态文件服务） |

未新增后端 API。最近批次列表当前为 **会话内** 记录；无列表历史 API 时底部显示空态。

## 六、E01 目录项

| 数据表 | 性质 | 模板 | 依赖 | 状态 |
|---|---|---|---|---|
| 环境监测点位表 | 基础主数据 | V1.2 点位模板 | 无 | 可上传 |
| 环境监测结果表 | 事实数据 | V1.2 结果模板 | 点位表 | 可上传 |

模板路径（任务书约定）：

- `/templates/esg/split_V1.2_业务录入/E01_环境监测点位表.xlsx`
- `/templates/esg/split_V1.2_业务录入/E01_环境监测结果表.xlsx`

> 注：当前后端静态服务按文件名取 `templates/esg/` 根目录；若子目录文件未部署，下载需将 xlsx 放到后端可访问路径或扩展静态路由（**不在本次前端范围**）。

## 七、已知未实现项（P2 / 后续）

1. 错误明细文件下载（按钮已保留「后续接入」，不伪造成功）
2. 最近批次 **历史 API** 拉取
3. 智能体 / API / 定时连接来源的真实批次展示
4. E02–G04、碳排正式 V1.2 模板上传（目录已登记为「建设中」/「仅自动接入」，无可用下载）
5. 数据质量趋势、失败重传、自动接入监控

## 八、E02/E03/S/G 扩展方式

1. 在 `esg-data-catalog.ts` 增加目录项：`templateUrl`、`templateCode`、`status: '可上传'`
2. 在 `esg-import-presenter.ts` 补充 `sheetHint` / 字段中文映射
3. 无需改首页或二级分析；`displayAssociations` 声明影响的 L1 指标即可
4. 后端模板注册就绪后，将 `status` 从「建设中」改为「可上传」

## 十、校核结论 V1.0 响应（2026-08-08）

依据《ESG智能入库数据表目录V1.2页面与实现报告校核结论_V1.0》已完成 P0/P1 前端调整：

### 已落实

1. **两层结构**：默认「当前可上传数据表」工作台 + 「查看全部数据表」完整目录二级视图
2. **待处理聚焦**：「最近上传 / 待处理」区展示识别中、校验失败、待确认入库
3. **建设中降噪**：首屏仅展示可上传表；建设中/自动接入以汇总行提示，完整列表在二级目录
4. **筛选下沉**：「首页/专题关联」移至完整目录高级筛选
5. **统一卡片**：所有可上传表使用相同模板下载 + 上传组件，移除 E01 专属模板条
6. **模板下载 URL**：`resolveTemplateDownloadUrl` 按后端规则取 basename（`/templates/esg/{文件名}`）

### 模板下载实测

需在 API `:8765` 运行且 `templates/esg/` 下存在对应 xlsx 后逐一点击验证。若文件仅在 `split_V1.2_业务录入/` 子目录，需运维复制到 `templates/esg/` 根目录（后端静态路由限制，不在本次前端范围）。

### 仍待 P2

- 历史批次 API、错误明细下载、收藏/常用排序

