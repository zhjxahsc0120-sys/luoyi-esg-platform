export const designMapConfig = {
  manifestUrl: "/gis/s1-6/layer-config.json",
  // KML 文件较大：关闭图层时仅隐藏，保留 Cesium DataSource 缓存。
  releaseOnHide: false,
  terrainUrl:
    import.meta.env.VITE_TRAFFIC_TERRAIN_URL ||
    "https://data.mars3d.cn/terrain",
};
