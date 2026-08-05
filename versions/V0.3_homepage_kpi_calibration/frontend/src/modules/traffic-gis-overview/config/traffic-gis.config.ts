export const trafficGisConfig = {
  initialView: {
    /** 罗宜高速正式 KML 道路中心线概览中心 */
    longitude: 108.76533935,
    latitude: 24.562372985,
    height: 42000,
    heading: 0,
    pitch: -55,
  },
  /** 复位 / 总览飞入框（与 public/gis/s1-6/layer-config.json overviewRectangle 对齐） */
  projectRectangle: [108.71055634, 24.46985643, 108.82012236, 24.65488954] as [
    number,
    number,
    number,
    number,
  ],
  /**
   * 相机硬边界：在正式道路范围外扩约 10%，
   * 限制拖出 / 过度缩小，锁定在高速走廊。
   */
  corridorLock: {
    enabled: true,
    rectangle: [108.6995, 24.4514, 108.8312, 24.6733] as [
      number,
      number,
      number,
      number,
    ],
    minHeight: 3200,
    maxHeight: 58000,
  },
  basemap: {
    url:
      import.meta.env.VITE_TRAFFIC_BASEMAP_URL ||
      "https://webst01.is.autonavi.com/appmaptile?style=6&x={x}&y={y}&z={z}",
    brightness: 0.9,
    contrast: 1.08,
    saturation: 0.9,
  },
  lod: { labelMaxHeight: 55000, pointMaxHeight: 120000 },
};
