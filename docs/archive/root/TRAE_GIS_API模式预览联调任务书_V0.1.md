# TRAE_GIS_API模式预览联调任务书_V0.1

## 一、背景

地图模块第一阶段隔离预览页已经接入，当前 `/gis-preview` 使用：

```vue
data-mode="shp"
```

Codex 已完成 GIS 后端接口和 MySQL 测试数据入库。下一步请只在隔离预览页验证 API 模式，不要替换领导层首页原 GIS 区域，不要改 DashboardPage.vue。

## 二、访问地址

前端：

```text
http://localhost:5174/#/gis-preview
```

后端：

```text
http://127.0.0.1:8765
```

## 三、已完成的后端接口

### 1. 查询 GIS 图层清单

```http
GET /api/esg/gis/layers
```

支持查询条件：

| 查询条件 | 含义 | 示例 |
|---|---|---|
| `projectId` | 项目编号 | `LUOYI-ESG` |
| `sectionId` | 施工标段名称 | `1标段`、`2标段`、`3标段` |
| `currentTime` | 当前展示时间 | `2026-07-16 10:30` |
| `visibleLayerIds` | 指定显示图层，多个用英文逗号分隔 | `section-1,water-1,slope-2` |

返回格式：

```json
{
  "code": 0,
  "data": [
    {
      "id": "section-1",
      "name": "1标段",
      "geometryType": "line",
      "enabled": true,
      "objectType": "road-section",
      "featureCount": 1,
      "source": { "type": "api", "url": "/data/shp/1标段.geojson" },
      "style": {}
    }
  ]
}
```

### 2. 查询 GIS 要素

```http
GET /api/esg/gis/features
```

支持查询条件：

| 查询条件 | 含义 | 示例 |
|---|---|---|
| `projectId` | 项目编号 | `LUOYI-ESG` |
| `layerId` | 图层编号 | `section-1`、`water-1`、`slope-2` |
| `sectionId` | 施工标段名称 | `1标段`、`2标段`、`3标段` |
| `currentTime` | 当前展示时间 | `2026-07-16 10:30` |

返回格式：

```json
{
  "code": 0,
  "data": [
    {
      "id": "section-1-1",
      "layerId": "section-1",
      "objectType": "road-section",
      "name": "1标段",
      "geometry": {
        "type": "LineString",
        "coordinates": []
      },
      "properties": {
        "sectionId": "1标段",
        "sourceLayer": "1标段"
      },
      "status": "normal",
      "riskLevel": null,
      "updatedAt": "2026-07-16 14:56:00"
    }
  ]
}
```

## 四、当前测试数据

MySQL 已入库：

| 类型 | 数量 |
|---|---:|
| GIS 图层 | 10 |
| GIS 要素 | 10 |

包含：

- 1标段、2标段、3标段；
- 弃渣点1、弃渣点2；
- 水源保护区1、水源保护区2；
- 生态保护区1；
- 边坡监测点1、边坡监测点2。

注意：当前数据来自 `public/data/shp` 的 WGS84 GeoJSON 测试数据；不是正式业务生产数据。

## 五、Trae 本轮任务

### 任务 1：隔离预览页切换 API 模式

仅修改：

```text
src/views/GisPreviewPage.vue
```

将：

```vue
data-mode="shp"
```

临时改为：

```vue
data-mode="api"
```

建议同时显式传入：

```vue
project-id="LUOYI-ESG"
```

不要改首页，不要替换 `GisOverviewPanel`，不要删除原 SVG 地图。

### 任务 2：浏览器点测

访问：

```text
http://localhost:5174/#/gis-preview
```

检查：

- 页面能正常打开；
- 控制台无接口报错；
- 能显示线路、弃渣点、水源保护区、生态保护区、边坡监测点；
- 点击图层要素有交互反馈；
- `sectionId="1标段"` / `2标段` / `3标段` 过滤时，要素按施工标段变化；
- 若图层控制面板可见，图层开关有效；
- 如果 API 失败，页面应能暴露错误提示，不能静默空白。

### 任务 3：保留回退方式

如 API 模式显示异常，请先回退到：

```vue
data-mode="shp"
```

并记录：

- 浏览器控制台错误；
- 请求 URL；
- 返回内容；
- 页面截图。

本轮不要直接修地图模块内部大量代码，先定位问题。

## 六、验收命令

前端命令：

```powershell
npm.cmd run check
npm.cmd run build
```

后端命令由 Codex 已验证：

```powershell
python server\gis_api_test.py
python server\smoke_test.py
python server\dashboard_acceptance_test.py
```

## 七、本轮禁止事项

- 不要修改 `DashboardPage.vue`；
- 不要替换领导层首页 GIS 区域；
- 不要启用 `data/18` 重大危化品工厂 3D Tiles；
- 不要把 3D Tiles 描述为罗宜高速真实设施；
- 不要删除原 `GisOverviewPanel` / `RouteMapSvg`；
- 不要重写 `TrafficGisOverview.vue`；
- 不要更改已有 KPI、专题弹窗和数据上传工作台逻辑。
