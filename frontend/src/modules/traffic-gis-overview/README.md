# 交通 ESG 项目一张图

该模块嵌入 ESG 综合看板，使用 Cesium 加载本批红线、道路与边坡矢量数据。

## 数据入口与生命周期

- 当前图层配置：`public/gis/s1-6/current-layer-config.json`
- 默认图层：SPX 边坡 XYZ 瓦片、项目红线、道路中间线、道路边线、弃渣场
- 边坡线保留在设置面板中手动开启；当前源数据与道路边线空间重复。
- 首页与预览页启用 `designOnly`，不再叠加旧生态、SPX、数据库业务点、本地缓存矢量和空间资源
- 高度碎片化的 KML 通过 `scripts/prepare-current-map-lines.mjs` 归并为 GeoJSON 后加载
- 加载失败写入单图层错误状态，可再次点击重试

`DesignKmlLayerManager` 负责配置读取、请求去重、图层缓存、显隐、定位和样式。
源目录变更后重新运行转换脚本，并同步更新 `current-layer-config.json`。

## 样式规则

- 红线：红色边界和透明填充。
- 道路中间线：普通细线，不使用高亮光晕。
- 道路边线：青蓝外发光和亮色核心线。
- 边坡线：橙色虚线。
- 弃渣场：橙色半透明填充、黄色高亮边界和近距离标签。
- SPX 边坡：本地透明 XYZ 瓦片，显示级别 10–18。

红线最后加载，面和边界使用本批矢量中的最高 `zIndex`，始终压在道路、
弃渣场等地面矢量之上。

当前提供的 `边坡线.kml` 除文档时间戳外与 `道路边线.kml` 完全相同，两层会
100% 空间重合；代码按原文件分别接入，待收到正确边坡数据后重新转换替换。

## 主要文件

- `components/TrafficGisOverview.vue`：Cesium 生命周期和运行状态
- `components/DesignLayerTree.vue`：图层开关、加载状态、定位和透明度
- `cesium/layers/DesignKmlLayerManager.ts`：按需加载、去重和缓存
- `scripts/prepare-current-map-lines.mjs`：本批线数据转换
- `config/design-map.config.ts`：配置入口、缓存策略和地形地址
- `cesium/interaction/PickManager.ts`：点击要素拾取
- `components/FeatureCard.vue`：工程对象及后续 ESG 业务详情

## 验证

```bash
npm.cmd run check
npm.cmd run build
```

浏览器验收入口：`http://127.0.0.1:5174/#/gis-preview`。确认出现红线、
道路中间线、道路边线、弃渣场和 SPX 边坡瓦片；边坡矢量线默认关闭，不再出现
旧生态、业务点及本地缓存图层。
