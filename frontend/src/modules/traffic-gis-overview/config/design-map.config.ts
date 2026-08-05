export const designMapConfig = {
  manifestUrl: "/gis/s1-6/current-layer-config.json?v=20260805-eager-details-1",
  spxTiles: {
    enabled: true,
    url: "/gis/s1-6/layers/current/spx-tiles/{z}/{x}/{y}.png",
    minimumLevel: 10,
    maximumLevel: 18,
    rectangle: [
      108.73409259,
      24.47120628,
      108.84577845,
      24.76033661,
    ] as [number, number, number, number],
    alpha: 1,
  },
  // KML 文件较大：关闭图层时仅隐藏，保留 Cesium DataSource 缓存。
  releaseOnHide: false,
  terrainUrl:
    import.meta.env.VITE_TRAFFIC_TERRAIN_URL ||
    "https://data.mars3d.cn/terrain",
};
