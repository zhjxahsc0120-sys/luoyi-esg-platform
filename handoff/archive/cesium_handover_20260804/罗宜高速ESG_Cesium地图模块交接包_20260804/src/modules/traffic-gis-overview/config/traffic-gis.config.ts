export const trafficGisConfig = {
  initialView: {
    longitude: 109.68,
    latitude: 24.45,
    height: 52000,
    heading: 0,
    pitch: -55,
  },
  projectRectangle: [109.52, 24.39, 109.83, 24.52] as [
    number,
    number,
    number,
    number,
  ],
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
