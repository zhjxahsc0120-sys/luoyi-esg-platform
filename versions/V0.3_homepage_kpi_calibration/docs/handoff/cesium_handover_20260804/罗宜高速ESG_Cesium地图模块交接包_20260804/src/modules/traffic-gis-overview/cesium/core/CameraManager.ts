import * as Cesium from "cesium";
import type { InitialView } from "../../types";
import { trafficGisConfig } from "../../config/traffic-gis.config";
import { CoordinateAdapter } from "./CoordinateAdapter";
export class CameraManager {
  constructor(private readonly viewer: Cesium.Viewer) {}
  reset(view: InitialView = trafficGisConfig.initialView) {
    const [longitude, latitude] = CoordinateAdapter.displayLngLat(
      view.longitude,
      view.latitude,
    );
    this.viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(
        longitude,
        latitude,
        view.height,
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
    this.viewer.camera.flyTo({
      destination: CoordinateAdapter.rectangle(rectangle),
      duration: 0.8,
    });
  }
}
