import * as Cesium from "cesium";
import type {
  PresentationMode,
  TrafficLayerDefinition,
  TrafficMapFeature,
} from "../../types";
import { CoordinateAdapter } from "../core/CoordinateAdapter";
import { labelSizes, wholePx } from "../../config/style-tokens";
import { entityMeta, featureColor, featureLabel, normalizeMapLabel } from "./render-utils";

export class PolylineRenderer {
  render(
    viewer: Cesium.Viewer,
    layer: TrafficLayerDefinition,
    features: TrafficMapFeature[],
    presentationMode: PresentationMode = "preview",
  ) {
    const isDashboard = presentationMode === "dashboard";
    // 大屏：三色标段统一细线+弱光晕，避免蓝标视觉上更“胖”
    const glowAlpha = isDashboard ? 0.18 : 0.72;
    const glowPower = isDashboard ? 0.14 : 0.38;
    const glowExtra = isDashboard ? 2 : 12;
    const baseWidth = layer.style.width || 5;
    const lineWidth = isDashboard ? 3 : baseWidth;

    return features.flatMap((f) => {
      if (f.geometry.type !== "LineString")
        throw new Error("PolylineRenderer收到非线要素");
      const positions = CoordinateAdapter.degreesArray(f.geometry.coordinates);
      const color = featureColor(f, layer.style.color);
      const midpoint =
        f.geometry.coordinates[Math.floor(f.geometry.coordinates.length / 2)];
      const labelText = normalizeMapLabel(f.name);
      const sectionLabelSize = isDashboard
        ? labelSizes.sectionDashboard
        : (layer.style.labelSize || labelSizes.sectionPreview);
      const tag = featureLabel(
        labelText,
        color.toCssColorString(),
        layer.style.labelColor || "#ffffff",
        sectionLabelSize,
        // 标段一/二/三固定同宽，避免气泡感官宽度不一致
        f.objectType === "road-section" ? { fixedWidth: 88 } : undefined,
      );
      const billboard =
        layer.style.showLabel === false
          ? undefined
          : {
              image: tag.image,
              width: tag.width,
              height: tag.height,
              verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
              // 标段标签略偏上，给超标点下方标签让位
              pixelOffset: new Cesium.Cartesian2(
                0,
                wholePx(isDashboard ? -14 : -8),
              ),
              disableDepthTestDistance: Number.POSITIVE_INFINITY,
              distanceDisplayCondition: isDashboard
                ? new Cesium.DistanceDisplayCondition(8000, 90000)
                : undefined,
              scaleByDistance: new Cesium.NearFarScalar(2500, 1.0, 52000, 0.75),
            };
      return [
        viewer.entities.add({
          ...entityMeta(f),
          id: `${f.id}-glow`,
          polyline: {
            positions,
            width: lineWidth + glowExtra,
            material: new Cesium.PolylineGlowMaterialProperty({
              color: color.withAlpha(glowAlpha),
              glowPower,
            }),
            clampToGround: false,
          },
        }),
        viewer.entities.add({
          ...entityMeta(f),
          position: CoordinateAdapter.wgs84(midpoint),
          billboard,
          polyline: {
            positions,
            width: lineWidth,
            material: color.withAlpha(layer.style.opacity ?? 1),
            clampToGround: false,
          },
        }),
      ];
    });
  }
}
