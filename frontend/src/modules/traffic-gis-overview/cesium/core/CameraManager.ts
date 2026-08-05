import * as Cesium from "cesium";
import type { InitialView } from "../../types";
import { trafficGisConfig } from "../../config/traffic-gis.config";
import { CoordinateAdapter } from "./CoordinateAdapter";

type CorridorLockOptions = {
  rectangle: [number, number, number, number];
  minHeight: number;
  maxHeight: number;
};

export class CameraManager {
  private removeMoveEnd: (() => void) | null = null;
  private clamping = false;
  private lock: CorridorLockOptions | null = null;
  private prevMinZoom = 1;
  private prevMaxZoom = Number.POSITIVE_INFINITY;

  constructor(private readonly viewer: Cesium.Viewer) {}

  /** 仅在拖拽/缩放结束后软纠正视口中心，避免缩放过程中抖动回弹 */
  private softClampFocus() {
    if (!this.lock || this.clamping) return;
    const cam = this.viewer.camera;
    const carto = Cesium.Cartographic.fromCartesian(cam.positionWC);
    if (!carto) return;

    const [west, south, east, north] = this.lock.rectangle;
    const canvas = this.viewer.scene.canvas;
    const center = new Cesium.Cartesian2(canvas.clientWidth / 2, canvas.clientHeight / 2);
    const picked = cam.pickEllipsoid(center, this.viewer.scene.globe.ellipsoid);
    if (!picked) return;

    const focus = Cesium.Cartographic.fromCartesian(picked);
    const focusLon = Cesium.Math.toDegrees(focus.longitude);
    const focusLat = Cesium.Math.toDegrees(focus.latitude);
    const clampedFocusLon = Math.min(Math.max(focusLon, west), east);
    const clampedFocusLat = Math.min(Math.max(focusLat, south), north);

    const dLon = clampedFocusLon - focusLon;
    const dLat = clampedFocusLat - focusLat;
    if (Math.abs(dLon) < 1e-5 && Math.abs(dLat) < 1e-5) return;

    const height = Math.min(
      Math.max(carto.height, this.lock.minHeight),
      this.lock.maxHeight,
    );
    const camLon = Cesium.Math.toDegrees(carto.longitude) + dLon;
    const camLat = Cesium.Math.toDegrees(carto.latitude) + dLat;

    this.clamping = true;
    try {
      cam.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(camLon, camLat, height),
        orientation: {
          heading: cam.heading,
          pitch: cam.pitch,
          roll: cam.roll,
        },
        duration: 0.35,
      });
    } finally {
      // flyTo 异步；短延时后允许再次纠正
      window.setTimeout(() => {
        this.clamping = false;
      }, 400);
    }
  }

  /** 锁定在 1–3 标段走廊：原生限制缩放距离，结束拖拽后再轻推回边界 */
  enableCorridorLock(options?: {
    rectangle: [number, number, number, number];
    minHeight: number;
    maxHeight: number;
  }) {
    this.disableCorridorLock();
    const base = trafficGisConfig.corridorLock;
    this.lock = {
      rectangle: [...(options?.rectangle || base.rectangle)] as [
        number,
        number,
        number,
        number,
      ],
      minHeight: options?.minHeight ?? base.minHeight,
      maxHeight: options?.maxHeight ?? base.maxHeight,
    };

    const controller = this.viewer.scene.screenSpaceCameraController;
    this.prevMinZoom = controller.minimumZoomDistance;
    this.prevMaxZoom = controller.maximumZoomDistance;
    controller.minimumZoomDistance = this.lock.minHeight;
    controller.maximumZoomDistance = this.lock.maxHeight;

    this.removeMoveEnd = this.viewer.camera.moveEnd.addEventListener(() =>
      this.softClampFocus(),
    );
  }

  disableCorridorLock() {
    if (this.removeMoveEnd) {
      this.removeMoveEnd();
      this.removeMoveEnd = null;
    }
    if (this.lock) {
      const controller = this.viewer.scene.screenSpaceCameraController;
      controller.minimumZoomDistance = this.prevMinZoom;
      controller.maximumZoomDistance = this.prevMaxZoom;
    }
    this.lock = null;
    this.clamping = false;
  }

  private clampFlyRange(range: number) {
    if (!this.lock) return Math.max(range, 6000);
    const minRange = Math.max(this.lock.minHeight * 0.95, 2800);
    const maxRange = Math.min(this.lock.maxHeight * 0.85, 42000);
    return Math.min(Math.max(range, minRange), maxRange);
  }

  private clampRectangleDegrees(
    west: number,
    south: number,
    east: number,
    north: number,
  ): [number, number, number, number] {
    if (!this.lock) return [west, south, east, north];
    const [lw, ls, le, ln] = this.lock.rectangle;
    return [
      Math.max(west, lw),
      Math.max(south, ls),
      Math.min(east, le),
      Math.min(north, ln),
    ];
  }

  reset(view: InitialView = trafficGisConfig.initialView) {
    const [longitude, latitude] = CoordinateAdapter.displayLngLat(
      view.longitude,
      view.latitude,
    );
    let height = view.height;
    if (this.lock) {
      height = Math.min(Math.max(height, this.lock.minHeight), this.lock.maxHeight);
    }
    this.viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(
        longitude,
        latitude,
        height,
      ),
      orientation: {
        heading: Cesium.Math.toRadians(view.heading || 0),
        pitch: Cesium.Math.toRadians(view.pitch ?? -55),
        roll: Cesium.Math.toRadians(view.roll || 0),
      },
      duration: 0.8,
    });
  }

  async flyTo(entities: Cesium.Entity[]) {
    if (entities.length) await this.viewer.flyTo(entities, { duration: 0.8 });
  }

  flyToRectangle(rectangle: [number, number, number, number]) {
    const clamped = this.clampRectangleDegrees(...rectangle);
    this.viewer.camera.flyTo({
      destination: CoordinateAdapter.rectangle(clamped),
      duration: 0.8,
    });
  }

  /**
   * 以目标经纬度为画面中心飞入（保留标段上下文尺度）。
   * 注意：勿把相机位置直接放到 lon/lat 再配斜俯仰，否则地面点会落到视口底部。
   */
  flyToLonLat(longitude: number, latitude: number, range = 12000) {
    const [lon, lat] = CoordinateAdapter.displayLngLat(longitude, latitude);
    const target = Cesium.Cartesian3.fromDegrees(lon, lat, 0);
    const sphere = new Cesium.BoundingSphere(target, 120);
    this.viewer.camera.cancelFlight();
    this.viewer.camera.flyToBoundingSphere(sphere, {
      duration: 0.85,
      offset: new Cesium.HeadingPitchRange(
        0,
        Cesium.Math.toRadians(-62),
        this.clampFlyRange(Math.max(range, 6000)),
      ),
    });
  }

  /** 按点位集合计算包围盒并飞入；无有效坐标时不跳转默认位置 */
  flyToPoints(
    points: Array<{ longitude?: number | null; latitude?: number | null }>,
    options?: { singleRange?: number },
  ) {
    const raw = points
      .map((p) => {
        if (p.longitude == null || p.latitude == null) return null;
        const lon = Number(p.longitude);
        const lat = Number(p.latitude);
        if (!Number.isFinite(lon) || !Number.isFinite(lat)) return null;
        return { lon, lat };
      })
      .filter((item): item is { lon: number; lat: number } => item != null);

    if (!raw.length) return;

    if (raw.length === 1) {
      this.flyToLonLat(raw[0].lon, raw[0].lat, options?.singleRange ?? 10000);
      return;
    }

    const valid = raw.map((p) => CoordinateAdapter.displayLngLat(p.lon, p.lat));
    let west = valid[0][0];
    let east = valid[0][0];
    let south = valid[0][1];
    let north = valid[0][1];
    for (const [lon, lat] of valid) {
      west = Math.min(west, lon);
      east = Math.max(east, lon);
      south = Math.min(south, lat);
      north = Math.max(north, lat);
    }

    const spanLon = Math.max(east - west, 0.01);
    const spanLat = Math.max(north - south, 0.01);
    const padLon = Math.max(spanLon * 0.35, 0.02);
    const padLat = Math.max(spanLat * 0.35, 0.02);

    const rect = this.clampRectangleDegrees(
      west - padLon,
      south - padLat,
      east + padLon,
      north + padLat,
    );

    this.viewer.camera.cancelFlight();
    this.viewer.camera.flyTo({
      destination: Cesium.Rectangle.fromDegrees(...rect),
      duration: 0.9,
    });
  }

  captureView() {
    const cam = this.viewer.camera;
    const carto = Cesium.Cartographic.fromCartesian(cam.positionWC);
    return {
      longitude: Cesium.Math.toDegrees(carto.longitude),
      latitude: Cesium.Math.toDegrees(carto.latitude),
      height: carto.height,
      heading: Cesium.Math.toDegrees(cam.heading),
      pitch: Cesium.Math.toDegrees(cam.pitch),
      roll: Cesium.Math.toDegrees(cam.roll),
    };
  }

  restoreView(view: {
    longitude: number;
    latitude: number;
    height: number;
    heading?: number;
    pitch?: number;
    roll?: number;
  }) {
    let { longitude, latitude, height } = view;
    if (this.lock) {
      const [west, south, east, north] = this.lock.rectangle;
      longitude = Math.min(Math.max(longitude, west), east);
      latitude = Math.min(Math.max(latitude, south), north);
      height = Math.min(Math.max(height, this.lock.minHeight), this.lock.maxHeight);
    }
    this.viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(
        longitude,
        latitude,
        height,
      ),
      orientation: {
        heading: Cesium.Math.toRadians(view.heading || 0),
        pitch: Cesium.Math.toRadians(view.pitch ?? -55),
        roll: Cesium.Math.toRadians(view.roll || 0),
      },
      duration: 0.8,
    });
  }
}
