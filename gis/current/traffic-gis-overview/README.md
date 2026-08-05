# 交通 ESG 项目一张图

该模块嵌入 ESG 综合看板，使用 Cesium 加载 S1-6 高速公路正式 KML。

## 数据入口与生命周期

- 唯一图层配置：`public/gis/s1-6/layer-config.json`
- 默认基础层：道路、生态和关键保护要素，页面初始化时加载
- SPX 层：首页默认异步加载，不生成海量 Entity
- SPX 在 Web Worker 中解析，并按 4 种原始样式批量生成 Cesium Primitive
- SPX 成功加载后缓存 Primitive；关闭只设置 `show = false`
- 设计 KML 不在前台图层面板中开关；地图设置面板用于数据库业务异常图层
- 加载失败写入单图层错误状态，可再次点击重试

`DesignKmlLayerManager` 负责配置读取、请求去重、图层缓存、显隐、定位和
透明度；`SpxPrimitiveLayer` 负责高密度边坡的轻量批量渲染。KML 路径不得写入页面组件，新增或替换文件统一修改
`layer-config.json`。

## 样式规则

基础 KML 使用 `Cesium.KmlDataSource` 原样加载。SPX 保留全部原始坐标和折线
连接关系，按原始颜色、透明度和线宽批量绘制，不生成九万多个 Entity。透明度
调整以源 KML 颜色的 alpha 为基准，不统一改色。

## 主要文件

- `components/TrafficGisOverview.vue`：Cesium 生命周期和运行状态
- `components/DesignLayerTree.vue`：图层开关、加载状态、定位和透明度
- `cesium/layers/DesignKmlLayerManager.ts`：按需加载、去重和缓存
- `cesium/layers/SpxPrimitiveLayer.ts`：SPX 批量 Primitive 渲染
- `cesium/layers/spx-kml.worker.ts`：SPX 后台解析
- `config/design-map.config.ts`：配置入口、缓存策略和地形地址
- `cesium/interaction/PickManager.ts`：点击要素拾取
- `components/FeatureCard.vue`：工程对象及后续 ESG 业务详情

## 验证

```bash
npm run check
npm run build
```

浏览器验收要点：首次进入请求基础 KML 和 SPX KML；视角按新中心线范围定位；
不出现旧标段演示线和取弃土场；地图设置默认进入业务异常图层；全屏和业务点击正常。
