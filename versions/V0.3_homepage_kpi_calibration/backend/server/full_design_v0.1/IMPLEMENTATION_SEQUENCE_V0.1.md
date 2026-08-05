# 罗宜高速 ESG 后续实施顺序建议 V0.1

## 1. 当前状态

已经完成：

- 领导首页 KPI API 接入；
- S01 连续安全生产天数 API 接入；
- 上传工作台 P01/P02/P04/P05 基础 API 接入；
- S01 任务办理弹窗详情 API 基线；
- 智能入库扩展数据库设计 V0.1；
- 当前联调库冒烟测试。

## 2. 不建议马上做的事

暂不建议：

- 继续接入剩余 11 个 KPI 弹窗；
- 大规模改领导首页专题模块；
- 直接上 MySQL 实例执行草案；
- 为所有页面先造展示型接口。

原因：

```text
页面展示接口如果早于业务数据结构定稿，
后面会反复返工字段、状态和统计口径。
```

## 3. 推荐实施顺序

### 第一阶段：设计固化

输出：

```text
MySQL 正式建库包 V0.1
智能入库接口契约 V0.1
工作台主链路接口契约 V0.1
KPI 来源与计算口径 V0.1
```

### 第二阶段：MySQL 原型库

工作：

```text
建 MySQL 实例
执行 schema
导入字典和字段映射
导入样例数据
执行校验 SQL
```

### 第三阶段：后端服务正式化

工作：

```text
从 SQLite 原型服务迁移到 MySQL
补智能入库接口
补资料详情/版本接口
补审核流转接口
保留 mock fallback 策略
```

### 第四阶段：Trae 前端接入

优先接：

```text
P03 ESG 智能入库
S01 任务办理弹窗
P05 资料中心详情
P04 审核轨迹
```

后接：

```text
11 个 KPI 详情弹窗
碳足迹专题
月报专题
GIS 地图
```

## 4. 下一步建议

下一步建议由 Codex 继续输出：

```text
罗宜高速 ESG MySQL 建库包 V0.1
```

包含：

```text
01_schema_mysql.sql
02_seed_dictionary.sql
03_seed_field_mapping.sql
04_seed_demo_data.sql
05_views.sql
06_validation_queries.sql
README_建库说明.md
```

等该建库包成型后，再建 MySQL 实例给 Codex 执行，会比现在直接建库更稳。
