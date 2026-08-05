import * as Cesium from "cesium";
import type { TrafficMapFeature } from "../../types";
type PickResult = { feature: TrafficMapFeature; entity: Cesium.Entity };
export class PickManager {
  private handler?: Cesium.ScreenSpaceEventHandler;
  constructor(private readonly viewer: Cesium.Viewer) {}
  bind(
    onClick: (f: TrafficMapFeature, e: Cesium.Entity) => void,
    onHover: (f: TrafficMapFeature | null) => void,
  ) {
    this.handler = new Cesium.ScreenSpaceEventHandler(this.viewer.scene.canvas);
    this.handler.setInputAction(
      (e: Cesium.ScreenSpaceEventHandler.PositionedEvent) => {
        const result = this.pick(e.position);
        if (result) onClick(result.feature, result.entity);
      },
      Cesium.ScreenSpaceEventType.LEFT_CLICK,
    );
    this.handler.setInputAction(
      (e: Cesium.ScreenSpaceEventHandler.MotionEvent) =>
        onHover(this.pick(e.endPosition)?.feature ?? null),
      Cesium.ScreenSpaceEventType.MOUSE_MOVE,
    );
  }
  private normalizePickPosition(position: Cesium.Cartesian2): Cesium.Cartesian2 {
    const canvas = this.viewer.scene.canvas;
    const rect = canvas.getBoundingClientRect();

    if (!rect.width || !rect.height) return position;

    const scaleX = canvas.clientWidth / rect.width;
    const scaleY = canvas.clientHeight / rect.height;

    if (
      !Number.isFinite(scaleX) ||
      !Number.isFinite(scaleY) ||
      scaleX <= 0 ||
      scaleY <= 0
    ) {
      return position;
    }

    if (Math.abs(scaleX - 1) < 1e-4 && Math.abs(scaleY - 1) < 1e-4) {
      return position;
    }

    return new Cesium.Cartesian2(position.x * scaleX, position.y * scaleY);
  }
  private pick(position: Cesium.Cartesian2): PickResult | undefined {
    const normalized = this.normalizePickPosition(position);
    const picked = this.viewer.scene.pick(normalized);
    const entity = picked?.id as Cesium.Entity | undefined;
    const feature = entity?.properties?.trafficFeature?.getValue(
      Cesium.JulianDate.now(),
    ) as TrafficMapFeature | undefined;
    return entity && feature ? { feature, entity } : undefined;
  }
  destroy() {
    this.handler?.destroy();
    this.handler = undefined;
  }
}
