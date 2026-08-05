import * as Cesium from "cesium";
import type { SpatialAssetRecord } from "../../assets/SpatialAssetStore";
import type { TrafficMapFeature } from "../../types";
export class SpatialAssetManager {
  private imagery = new Map<string, Cesium.ImageryLayer>();
  private models = new Map<string, Cesium.Cesium3DTileset>();
  private labels = new Map<string, Cesium.Entity>();
  constructor(private readonly viewer: Cesium.Viewer) {}
  async sync(items: SpatialAssetRecord[]) {
    this.clearOverlays();
    this.viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
    this.viewer.scene.globe.enableLighting = false;
    let terrainError: unknown;
    for (const item of items.filter((i) => i.visible)) {
      if (item.type === "imagery") {
        const layer = this.viewer.imageryLayers.addImageryProvider(
          new Cesium.UrlTemplateImageryProvider({ url: item.url }),
        );
        layer.alpha = item.opacity;
        this.imagery.set(item.id, layer);
      } else if (item.type === "terrain") {
        try {
          this.viewer.terrainProvider = item.terrainProvider === "arcgis"
            ? await Cesium.ArcGISTiledElevationTerrainProvider.fromUrl(item.url)
            : await Cesium.CesiumTerrainProvider.fromUrl(item.url, {
                requestVertexNormals: true,
              });
          this.viewer.scene.globe.enableLighting = true;
        } catch (error) {
          this.viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
          terrainError = error;
        }
      } else {
        const tileset = await Cesium.Cesium3DTileset.fromUrl(item.url);
        this.viewer.scene.primitives.add(tileset);
        if (item.placement) {
          const source = Cesium.Cartographic.fromCartesian(
            tileset.boundingSphere.center,
          );
          const sourceOrigin = Cesium.Cartesian3.fromRadians(
            source.longitude,
            source.latitude,
            source.height,
          );
          const targetOrigin = Cesium.Cartesian3.fromDegrees(
            item.placement.longitude,
            item.placement.latitude,
            item.placement.height + source.height,
          );
          const sourceFrame = Cesium.Transforms.eastNorthUpToFixedFrame(
            sourceOrigin,
          );
          const targetFrame = Cesium.Transforms.eastNorthUpToFixedFrame(
            targetOrigin,
          );
          tileset.modelMatrix = Cesium.Matrix4.multiply(
            targetFrame,
            Cesium.Matrix4.inverse(sourceFrame, new Cesium.Matrix4()),
            new Cesium.Matrix4(),
          );
          if (item.label) {
            const feature: TrafficMapFeature = {
              id: `${item.id}-label`,
              layerId: item.id,
              objectType: "hazardous-chemical-factory",
              name: item.label,
              geometry: {
                type: "Point",
                coordinates: [
                  item.placement.longitude,
                  item.placement.latitude,
                  item.placement.height,
                ],
              },
              properties: item.properties || {},
              status: "critical",
              riskLevel: 4,
            };
            const label = this.viewer.entities.add({
              position: Cesium.Cartesian3.fromDegrees(
                item.placement.longitude,
                item.placement.latitude,
                item.placement.height + (item.placement.labelHeight || 100),
              ),
              point: {
                pixelSize: 13,
                color: Cesium.Color.fromCssColorString("#ff4d5a"),
                outlineColor: Cesium.Color.WHITE,
                outlineWidth: 2,
                disableDepthTestDistance: Number.POSITIVE_INFINITY,
              },
              label: {
                text: `⚠ ${item.label}`,
                font: "bold 14px sans-serif",
                fillColor: Cesium.Color.WHITE,
                outlineColor: Cesium.Color.fromCssColorString("#68151c"),
                outlineWidth: 4,
                style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                showBackground: true,
                backgroundColor: Cesium.Color.fromCssColorString("#310a13").withAlpha(0.9),
                backgroundPadding: new Cesium.Cartesian2(10, 7),
                pixelOffset: new Cesium.Cartesian2(0, -28),
                disableDepthTestDistance: Number.POSITIVE_INFINITY,
                distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 30000),
              },
              properties: { trafficFeature: feature },
            });
            this.labels.set(item.id, label);
          }
        }
        this.models.set(item.id, tileset);
      }
    }
    if (terrainError) throw terrainError;
  }
  async locate(id: string) {
    const model = this.models.get(id);
    if (model) await this.viewer.zoomTo(model);
  }
  clearOverlays() {
    this.imagery.forEach((layer) =>
      this.viewer.imageryLayers.remove(layer, true),
    );
    this.models.forEach((model) => this.viewer.scene.primitives.remove(model));
    this.labels.forEach((label) => this.viewer.entities.remove(label));
    this.imagery.clear();
    this.models.clear();
    this.labels.clear();
  }
  destroy() {
    this.clearOverlays();
  }
}
