import * as Cesium from "cesium";

export type DisplayCoordinateSystem = "wgs84" | "gcj02";

const A = 6378245.0;
const EE = 0.00669342162296594323;

function outOfChina(longitude: number, latitude: number) {
  return (
    longitude < 73.66 ||
    longitude > 135.05 ||
    latitude < 3.86 ||
    latitude > 53.55
  );
}

function transformLatitude(x: number, y: number) {
  let ret =
    -100.0 +
    2.0 * x +
    3.0 * y +
    0.2 * y * y +
    0.1 * x * y +
    0.2 * Math.sqrt(Math.abs(x));
  ret +=
    ((20.0 * Math.sin(6.0 * x * Math.PI) +
      20.0 * Math.sin(2.0 * x * Math.PI)) *
      2.0) /
    3.0;
  ret +=
    ((20.0 * Math.sin(y * Math.PI) +
      40.0 * Math.sin((y / 3.0) * Math.PI)) *
      2.0) /
    3.0;
  ret +=
    ((160.0 * Math.sin((y / 12.0) * Math.PI) +
      320 * Math.sin((y * Math.PI) / 30.0)) *
      2.0) /
    3.0;
  return ret;
}

function transformLongitude(x: number, y: number) {
  let ret =
    300.0 +
    x +
    2.0 * y +
    0.1 * x * x +
    0.1 * x * y +
    0.1 * Math.sqrt(Math.abs(x));
  ret +=
    ((20.0 * Math.sin(6.0 * x * Math.PI) +
      20.0 * Math.sin(2.0 * x * Math.PI)) *
      2.0) /
    3.0;
  ret +=
    ((20.0 * Math.sin(x * Math.PI) +
      40.0 * Math.sin((x / 3.0) * Math.PI)) *
      2.0) /
    3.0;
  ret +=
    ((150.0 * Math.sin((x / 12.0) * Math.PI) +
      300.0 * Math.sin((x / 30.0) * Math.PI)) *
      2.0) /
    3.0;
  return ret;
}

function wgs84ToGcj02(longitude: number, latitude: number) {
  if (outOfChina(longitude, latitude)) return [longitude, latitude] as const;

  let dLat = transformLatitude(longitude - 105.0, latitude - 35.0);
  let dLng = transformLongitude(longitude - 105.0, latitude - 35.0);
  const radLat = (latitude / 180.0) * Math.PI;
  let magic = Math.sin(radLat);
  magic = 1 - EE * magic * magic;
  const sqrtMagic = Math.sqrt(magic);
  dLat = (dLat * 180.0) / (((A * (1 - EE)) / (magic * sqrtMagic)) * Math.PI);
  dLng =
    (dLng * 180.0) /
    ((A / sqrtMagic) * Math.cos(radLat) * Math.PI);
  return [longitude + dLng, latitude + dLat] as const;
}

export class CoordinateAdapter {
  private static displayCoordinateSystem: DisplayCoordinateSystem = "wgs84";

  static setDisplayCoordinateSystem(system: DisplayCoordinateSystem) {
    CoordinateAdapter.displayCoordinateSystem = system;
  }

  static getDisplayCoordinateSystem() {
    return CoordinateAdapter.displayCoordinateSystem;
  }

  static displayLngLat(longitude: number, latitude: number) {
    return CoordinateAdapter.displayCoordinateSystem === "gcj02"
      ? wgs84ToGcj02(longitude, latitude)
      : ([longitude, latitude] as const);
  }

  static wgs84(coordinates: number[]) {
    const [longitude, latitude, height = 0] = coordinates;
    if (Math.abs(longitude) > 180 || Math.abs(latitude) > 90)
      throw new Error("坐标不是有效 WGS84 经纬度");
    const [displayLongitude, displayLatitude] = CoordinateAdapter.displayLngLat(
      longitude,
      latitude,
    );
    return Cesium.Cartesian3.fromDegrees(
      displayLongitude,
      displayLatitude,
      height,
    );
  }

  static degreesArray(coordinates: number[][]) {
    return Cesium.Cartesian3.fromDegreesArrayHeights(
      coordinates.flatMap((coordinate) => {
        const [displayLongitude, displayLatitude] =
          CoordinateAdapter.displayLngLat(coordinate[0], coordinate[1]);
        return [displayLongitude, displayLatitude, coordinate[2] || 0];
      }),
    );
  }

  static rectangle(rectangle: [number, number, number, number]) {
    const [west, south, east, north] = rectangle;
    const corners = [
      CoordinateAdapter.displayLngLat(west, south),
      CoordinateAdapter.displayLngLat(east, north),
    ];
    return Cesium.Rectangle.fromDegrees(
      Math.min(corners[0][0], corners[1][0]),
      Math.min(corners[0][1], corners[1][1]),
      Math.max(corners[0][0], corners[1][0]),
      Math.max(corners[0][1], corners[1][1]),
    );
  }
}
