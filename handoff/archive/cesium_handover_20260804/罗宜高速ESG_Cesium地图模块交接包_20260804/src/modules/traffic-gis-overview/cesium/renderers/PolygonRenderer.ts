import * as Cesium from "cesium";
import type {
  PresentationMode,
  TrafficLayerDefinition,
  TrafficMapFeature,
} from "../../types";
import { CoordinateAdapter } from "../core/CoordinateAdapter";
import { entityMeta, featureColor, featureLabel } from "./render-utils";

export class PolygonRenderer {
  render(
    viewer: Cesium.Viewer,
    layer: TrafficLayerDefinition,
    features: TrafficMapFeature[],
    presentationMode: PresentationMode = "preview",
  ) {
    const isDashboard = presentationMode === "dashboard";
    const fillAlpha = isDashboard ? 0.14 : 0.22;
    const labelSize = isDashboard
      ? (layer.style.labelSize || 11)
      : (layer.style.labelSize || 12);

    return features.map((f) => {
      if (f.geometry.type !== "Polygon")
        throw new Error("PolygonRenderer收到非面要素");
      const color = featureColor(f, layer.style.color);
      const ring = f.geometry.coordinates[0];
      const center = ring
        .reduce(
          (sum, coordinate) => [sum[0] + coordinate[0], sum[1] + coordinate[1]],
          [0, 0],
        )
        .map((value) => value / ring.length);
      const tag = featureLabel(
        f.name,
        color.toCssColorString(),
        layer.style.labelColor || "#ffffff",
        labelSize,
      );
      return viewer.entities.add({
        ...entityMeta(f),
        position: CoordinateAdapter.wgs84(center),
        billboard:
          layer.style.showLabel === false
            ? undefined
            : {
                image: tag.image,
                width: tag.width,
                height: tag.height,
                verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
                pixelOffset: new Cesium.Cartesian2(0, -4),
                disableDepthTestDistance: Number.POSITIVE_INFINITY,
                distanceDisplayCondition: new Cesium.DistanceDisplayCondition(
                  0,
                  16000,
                ),
              },
        polygon: {
          hierarchy: CoordinateAdapter.degreesArray(ring),
          material: new Cesium.StripeMaterialProperty({
            evenColor: color.withAlpha(layer.style.opacity ?? fillAlpha),
            oddColor: Cesium.Color.TRANSPARENT,
            repeat: 18,
            offset: 0,
            orientation: Cesium.StripeOrientation.VERTICAL,
          }),
          outline: false,
          height: 40,
        },
        polyline: {
          positions: CoordinateAdapter.degreesArray(ring),
          width: layer.style.width || 3,
          material: new Cesium.PolylineDashMaterialProperty({
            color,
            dashLength: 14,
          }),
          clampToGround: false,
        },
      });
    });
  }
}
