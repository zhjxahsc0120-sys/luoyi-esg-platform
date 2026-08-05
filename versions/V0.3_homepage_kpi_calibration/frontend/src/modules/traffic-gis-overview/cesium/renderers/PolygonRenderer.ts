import * as Cesium from "cesium";
import type {
  PresentationMode,
  TrafficLayerDefinition,
  TrafficMapFeature,
} from "../../types";
import { CoordinateAdapter } from "../core/CoordinateAdapter";
import { labelSizes, wholePx } from "../../config/style-tokens";
import { entityMeta, featureColor, zoneLabel } from "./render-utils";

type ZoneKind = "spoil-site" | "water-source" | "ecological-zone" | "default";

function zoneKind(objectType?: string): ZoneKind {
  if (objectType === "spoil-site") return "spoil-site";
  if (objectType === "water-source") return "water-source";
  if (objectType === "ecological-zone") return "ecological-zone";
  return "default";
}

function shortZoneName(name: string, kind: ZoneKind) {
  if (kind === "spoil-site") return name.replace(/^弃渣点/, "弃渣");
  if (kind === "water-source") return name.replace(/^水源保护区/, "水源");
  if (kind === "ecological-zone") return name.replace(/^生态保护区/, "生态");
  return name;
}

export class PolygonRenderer {
  render(
    viewer: Cesium.Viewer,
    layer: TrafficLayerDefinition,
    features: TrafficMapFeature[],
    presentationMode: PresentationMode = "preview",
  ) {
    const isDashboard = presentationMode === "dashboard";
    const kind = zoneKind(layer.objectType);
    const defaultLabel =
      kind === "water-source"
        ? isDashboard
          ? labelSizes.zoneDashboard
          : labelSizes.zonePreview
        : isDashboard
          ? labelSizes.zoneDashboard - 1
          : labelSizes.zonePreview - 1;
    const labelSize = layer.style.labelSize || defaultLabel;

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

      const fillAlpha =
        layer.style.opacity ??
        (kind === "water-source"
          ? isDashboard ? 0.2 : 0.28
          : kind === "spoil-site"
            ? isDashboard ? 0.24 : 0.32
            : kind === "ecological-zone"
              ? isDashboard ? 0.16 : 0.22
              : isDashboard ? 0.14 : 0.22);

      const material =
        kind === "water-source"
          ? color.withAlpha(fillAlpha)
          : kind === "spoil-site"
            ? new Cesium.StripeMaterialProperty({
                evenColor: color.withAlpha(fillAlpha),
                oddColor: color.withAlpha(fillAlpha * 0.25),
                repeat: 22,
                offset: 0.15,
                orientation: Cesium.StripeOrientation.HORIZONTAL,
              })
            : kind === "ecological-zone"
              ? new Cesium.StripeMaterialProperty({
                  evenColor: color.withAlpha(fillAlpha),
                  oddColor: Cesium.Color.TRANSPARENT,
                  repeat: 14,
                  offset: 0,
                  orientation: Cesium.StripeOrientation.VERTICAL,
                })
              : new Cesium.StripeMaterialProperty({
                  evenColor: color.withAlpha(fillAlpha),
                  oddColor: Cesium.Color.TRANSPARENT,
                  repeat: 18,
                  offset: 0,
                  orientation: Cesium.StripeOrientation.VERTICAL,
                });

      const outlineMaterial =
        kind === "water-source"
          ? new Cesium.PolylineDashMaterialProperty({
              color: color.withAlpha(0.95),
              dashLength: 18,
            })
          : kind === "spoil-site"
            ? color.withAlpha(0.95)
            : new Cesium.PolylineDashMaterialProperty({
                color: color.withAlpha(0.9),
                dashLength: kind === "ecological-zone" ? 10 : 14,
              });

      const tag = zoneLabel(
        shortZoneName(f.name, kind),
        color.toCssColorString(),
        kind,
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
                verticalOrigin: Cesium.VerticalOrigin.CENTER,
                // 水源略上移，减少压住走廊线
                pixelOffset: new Cesium.Cartesian2(
                  0,
                  wholePx(
                    kind === "water-source" ? -10 : kind === "spoil-site" ? 8 : -6,
                  ),
                ),
                disableDepthTestDistance: Number.POSITIVE_INFINITY,
                distanceDisplayCondition: new Cesium.DistanceDisplayCondition(
                  0,
                  isDashboard ? 52000 : 62000,
                ),
                scaleByDistance: new Cesium.NearFarScalar(
                  2500,
                  1.0,
                  52000,
                  0.75,
                ),
              },
        polygon: {
          hierarchy: CoordinateAdapter.degreesArray(ring),
          material,
          outline: false,
          height: kind === "water-source" ? 22 : 36,
        },
        polyline: {
          positions: CoordinateAdapter.degreesArray(ring),
          width: kind === "spoil-site" ? Math.max(layer.style.width || 3, 3) : (layer.style.width || 2.5),
          material: outlineMaterial,
          clampToGround: false,
        },
      });
    });
  }
}
