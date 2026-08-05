import * as Cesium from "cesium";
import {
  basemapDefinitions,
  defaultBasemapId,
  type BasemapDefinition,
} from "../../config/basemaps.config";
import { CoordinateAdapter } from "./CoordinateAdapter";

function createImageryProvider(basemap: BasemapDefinition) {
  return basemap.type === "osm"
    ? new Cesium.OpenStreetMapImageryProvider({ url: basemap.url })
    : new Cesium.UrlTemplateImageryProvider({
        url: basemap.url,
        credit: basemap.credit,
      });
}

export class ViewerManager {
  private viewer?: Cesium.Viewer;

  create(container: HTMLElement) {
    if (this.viewer) return this.viewer;

    const basemap =
      basemapDefinitions.find((item) => item.id === defaultBasemapId) ??
      basemapDefinitions[0];

    this.viewer = new Cesium.Viewer(container, {
      baseLayer: new Cesium.ImageryLayer(createImageryProvider(basemap)),
      terrainProvider: new Cesium.EllipsoidTerrainProvider(),
      animation: false,
      timeline: false,
      baseLayerPicker: false,
      geocoder: false,
      homeButton: false,
      sceneModePicker: false,
      navigationHelpButton: false,
      fullscreenButton: false,
      infoBox: false,
      selectionIndicator: false,
      requestRenderMode: true,
      maximumRenderTimeChange: Number.POSITIVE_INFINITY,
      scene3DOnly: true,
    });

    const layer = this.viewer.imageryLayers.get(0);
    layer.brightness = basemap.brightness;
    layer.contrast = basemap.contrast;
    layer.saturation = basemap.saturation;
    layer.alpha = basemap.alpha ?? 1;

    this.viewer.scene.backgroundColor =
      Cesium.Color.fromCssColorString("#eef3f7");
    this.viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString(
      basemap.globeBaseColor,
    );
    CoordinateAdapter.setDisplayCoordinateSystem(basemap.coordinateSystem);
    this.viewer.scene.screenSpaceCameraController.inertiaSpin = 0;
    return this.viewer;
  }

  get() {
    if (!this.viewer) throw new Error("Viewer 尚未创建");
    return this.viewer;
  }

  resize() {
    this.viewer?.resize();
  }

  destroy() {
    if (this.viewer && !this.viewer.isDestroyed()) this.viewer.destroy();
    this.viewer = undefined;
  }
}
