# 罗宜高速 ESG Demo API 字段契约 V0.1

> 用途：演示联调。字段语义沿用《ESG数据库实施方案 V1.0》，数据源使用 Demo 适配层；不作为生产 API 契约。

## 1. 首页指标

`GET /api/dashboard/kpis?projectId=1001&periodEnd=2026-08-04`

### 返回

```json
{
  "projectId": 1001,
  "periodEnd": "2026-08-04",
  "items": [
    {
      "key": "E04",
      "name": "文物保护",
      "value": 1,
      "unit": "处",
      "hint": "调查已完成，识别 1 处文物对象，保护措施落实率 100%。",
      "riskLevel": "NORMAL"
    }
  ]
}
```

### 固定字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `key` | string | E01-E04、S01-S04、G01-G04 |
| `name` | string | 指标名称 |
| `value` | number/string | 指标值；Demo 允许数值或展示文本 |
| `unit` | string | 次、%、天、件、项、处等 |
| `hint` | string | 面向首页的解释性提示 |
| `riskLevel` | string | NORMAL/LOW/MEDIUM/HIGH/CRITICAL |

数据源：`v_esg_demo_dashboard_kpis`。生产版本映射到 `fact_indicator_result`、`cfg_indicator` 和风险聚合层。

## 2. 指标详情

`GET /api/dashboard/kpi/{key}?projectId=1001&periodEnd=2026-08-04`

### 通用返回

```json
{
  "key": "G03",
  "name": "设计变更管理",
  "value": 4,
  "unit": "项",
  "hint": "4 项设计变更中 1 项待审批且附件缺失。",
  "riskLevel": "MEDIUM",
  "trend": [{"periodEnd": "2026-08-04", "value": 4}],
  "summary": {"total": 4, "pending": 1, "abnormal": 1},
  "objects": [
    {
      "objectType": "biz_design_change",
      "objectId": 26002,
      "objectName": "K18 段边坡防护方案调整",
      "status": "待审批",
      "riskLevel": "MEDIUM"
    }
  ]
}
```

### E04 专属字段

E04 详情必须补充：

```json
{
  "objectCount": 1,
  "surveyStatus": "COMPLETED",
  "measureRate": 100,
  "riskStatus": "NORMAL"
}
```

- `objectCount`：文物对象数，由 `biz_cultural_relic_object` 聚合。
- `surveyStatus`：调查状态。
- `measureRate`：保护措施落实率；Demo 口径为文物对象措施落实率平均值。
- `riskStatus`：文物对象风险聚合结果。

### G02/G03 强制隔离

| key | 详情来源 | 对象类型 | 禁止绑定 |
|---|---|---|---|
| `G02` | `biz_permit` + `biz_night_construction_record` | 许可证/夜间施工记录 | 不读取设计变更或整改事项 |
| `G03` | `biz_design_change` | 设计变更 | 不读取 `biz_rectification` 作为指标本体 |
| `G04` | `biz_internal_control_issue` | 内控廉洁问题 | 不读取合规资料缺失作为指标本体 |

## 3. 对象详情

`GET /api/dashboard/kpi/{key}/objects/{objectId}?projectId=1001`

### 返回字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `kpiKey` | string | 指标编码 |
| `objectId` | number | 业务对象 ID |
| `objectType` | string | 业务表/对象类型 |
| `objectName` | string | 对象名称 |
| `responsibleUnit` | string | 责任单位 |
| `status` | string | 对象当前状态 |
| `riskLevel` | string | 对象风险等级 |
| `fields` | object | 指标专属字段 |
| `evidence` | array | 来源资料/文档引用 |
| `riskWarnings` | array | 关联风险预警和处置 |

E04 `fields` 示例：`{ "objectCount": 1, "surveyStatus": "COMPLETED", "measureRate": 100, "riskStatus": "NORMAL" }`。

## 4. 综合风险预警

`GET /api/dashboard/risk-warnings?projectId=1001&status=OPEN&page=1&pageSize=20`

### 返回字段

```json
{
  "items": [
    {
      "level": "HIGH",
      "domain": "G",
      "kpiKey": "G02",
      "objectId": 25002,
      "objectName": "2026-08-03 夜间施工记录",
      "responsibleUnit": "二工区施工单位",
      "status": "OPEN",
      "reason": "夜间施工许可临期且续期审批未完成。",
      "triggerTime": "2026-08-04 09:10:00"
    }
  ],
  "total": 1
}
```

固定字段：`level`、`domain`、`kpiKey`、`objectId`、`objectName`、`responsibleUnit`、`status`。点击规则：前端使用 `kpiKey + objectId` 跳转，不通过 `objectName` 反查。

数据源：`v_esg_demo_risk_list`；明细处置来自 `biz_risk_disposal`。

## 5. Demo 数据源索引

| 模块 | Demo 事实表 | 结果/风险 |
|---|---|---|
| E01 | 复用 `biz_env_monitor_*` | `esg_demo_indicator_result` |
| E02 | `biz_soil_disposal_site`、`biz_temporary_land_use`、`biz_topsoil_stripping`、`biz_construction_slope` | 结果 + `biz_risk_warning` |
| E03 | `biz_ecological_sensitive_area`、`biz_ecological_protection_object` | 结果 + `biz_risk_warning` |
| E04 | `biz_cultural_relic_object` | 结果 + `biz_risk_warning` |
| S01/S02 | 复用 `biz_safety_event`、`biz_safety_daily_status`、`biz_safety_risk_point` | 结果 + 风险 |
| S03 | `biz_worker_payment_summary`，补充 `biz_labor_dispute` | 结果 + 风险 |
| S04 | 复用 `biz_public_appeal` | 结果 |
| G01 | 复用 `biz_project_approval`、`biz_approval_catalog` | 结果 |
| G02 | 复用 `biz_permit` + `biz_night_construction_record` | 结果 + 风险 |
| G03 | `biz_design_change` | 结果 + 风险 |
| G04 | `biz_internal_control_issue` | 结果 + 风险 |

