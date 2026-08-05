import * as Cesium from "cesium";
import {
  basemapDefinitions,
  defaultBasemapId,
  type BasemapDefinition,
  type BasemapId,
} from "../../config/basemaps.config";
import { CoordinateAdapter } from "../core/CoordinateAdapter";

export class BasemapManager {
  private currentId: BasemapId = defaultBasemapId;

  constructor(private readonly viewer: Cesium.Viewer) {}

  getCurrent() {
    return this.currentId;
  }

  switchTo(id: BasemapId) {
    const config = basemapDefinitions.find((item) => item.id === id);
    if (!config) throw new Error(`未知底图：${id}`);

    const layers = this.viewer.imageryLayers;
    layers.removeAll(true);

    const provider = this.createProvider(config);
    const layer = layers.addImageryProvider(provider);
    layer.brightness = config.brightness;
    layer.contrast = config.contrast;
    layer.saturation = config.saturation;
    layer.alpha = config.alpha ?? 1;

    this.viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString(
      config.globeBaseColor,
    );
    CoordinateAdapter.setDisplayCoordinateSystem(config.coordinateSystem);
    this.currentId = id;
    return layer;
  }

  private createProvider(config: BasemapDefinition): Cesium.ImageryProvider {
    return config.type === "osm"
      ? new Cesium.OpenStreetMapImageryProvider({ url: config.url })
      : new Cesium.UrlTemplateImageryProvider({
          url: config.url,
          credit: config.credit,
        });
  }
}
