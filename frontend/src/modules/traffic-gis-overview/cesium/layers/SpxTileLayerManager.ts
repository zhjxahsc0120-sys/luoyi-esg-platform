import * as Cesium from "cesium";

export interface SpxTileLayerOptions {
  url: string;
  minimumLevel: number;
  maximumLevel: number;
  rectangle: [number, number, number, number];
  alpha?: number;
}

export class SpxTileLayerManager {
  private layer?: Cesium.ImageryLayer;
  private removeCameraMoveEnd?: () => void;

  constructor(
    private readonly viewer: Cesium.Viewer,
    private readonly options: SpxTileLayerOptions,
  ) {}

  show() {
    const layers = this.viewer.imageryLayers;
    if (this.layer && layers.indexOf(this.layer) >= 0) {
      this.layer.show = true;
      layers.raiseToTop(this.layer);
      this.updateAlpha();
      this.viewer.scene.requestRender();
      return;
    }

    const provider = new Cesium.UrlTemplateImageryProvider({
      url: this.options.url,
      minimumLevel: this.options.minimumLevel,
      maximumLevel: this.options.maximumLevel,
      tilingScheme: new Cesium.WebMercatorTilingScheme(),
      rectangle: Cesium.Rectangle.fromDegrees(...this.options.rectangle),
      hasAlphaChannel: true,
    });
    this.layer = layers.addImageryProvider(provider);
    this.layer.show = true;
    layers.raiseToTop(this.layer);
    this.updateAlpha();
    if (!this.removeCameraMoveEnd) {
      this.removeCameraMoveEnd = this.viewer.camera.moveEnd.addEventListener(
        () => this.updateAlpha(),
      );
    }
    this.viewer.scene.requestRender();
  }

  destroy() {
    this.removeCameraMoveEnd?.();
    this.removeCameraMoveEnd = undefined;
    if (
      this.layer &&
      this.viewer.imageryLayers.indexOf(this.layer) >= 0
    ) {
      this.viewer.imageryLayers.remove(this.layer, true);
    }
    this.layer = undefined;
  }

  private updateAlpha() {
    if (!this.layer) return;
    const height = this.viewer.camera.positionCartographic.height;
    const lodAlpha = height > 25000 ? 0.28 : height > 10000 ? 0.55 : 1;
    this.layer.alpha = (this.options.alpha ?? 1) * lodAlpha;
    this.viewer.scene.requestRender();
  }
}
