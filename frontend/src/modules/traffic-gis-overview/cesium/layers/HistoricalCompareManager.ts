import * as Cesium from "cesium";
import { basemapDefinitions, type BasemapId } from "../../config/basemaps.config";

export class HistoricalCompareManager {
  constructor(private readonly viewer: Cesium.Viewer) {}

  show(leftId: BasemapId, rightId: BasemapId, position = 0.5) {
    const layers = this.viewer.imageryLayers;
    layers.removeAll(true);
    const left = this.add(leftId);
    const right = this.add(rightId);
    left.splitDirection = Cesium.SplitDirection.LEFT;
    right.splitDirection = Cesium.SplitDirection.RIGHT;
    this.setPosition(position);
  }

  setPosition(position: number) {
    this.viewer.scene.splitPosition = Cesium.Math.clamp(position, 0.05, 0.95);
    this.viewer.scene.requestRender();
  }

  private add(id: BasemapId) {
    const config = basemapDefinitions.find((item) => item.id === id) ?? basemapDefinitions[0];
    const provider = config.type === "osm"
      ? new Cesium.OpenStreetMapImageryProvider({ url: config.url })
      : new Cesium.UrlTemplateImageryProvider({ url: config.url, credit: config.credit });
    const layer = this.viewer.imageryLayers.addImageryProvider(provider);
    layer.brightness = config.brightness;
    layer.contrast = config.contrast;
    layer.saturation = config.saturation;
    layer.alpha = config.alpha ?? 1;
    return layer;
  }
}
