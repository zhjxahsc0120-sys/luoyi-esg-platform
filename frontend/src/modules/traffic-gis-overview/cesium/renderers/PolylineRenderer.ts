import * as Cesium from "cesium";
import type {
  PresentationMode,
  TrafficLayerDefinition,
  TrafficMapFeature,
} from "../../types";
import { CoordinateAdapter } from "../core/CoordinateAdapter";
import { entityMeta } from "./render-utils";

export class PolylineRenderer {
  render(
    viewer: Cesium.Viewer,
    layer: TrafficLayerDefinition,
    features: TrafficMapFeature[],
    presentationMode: PresentationMode = "preview",
  ) {
    const isDashboard = presentationMode === "dashboard";
    const baseWidth = layer.style.width || 5;
    const lineWidth = baseWidth;

    return features.flatMap((f) => {
      if (f.geometry.type !== "LineString")
        throw new Error("PolylineRenderer收到非线要素");
      const positions = CoordinateAdapter.degreesArray(f.geometry.coordinates);
      // 标段线路使用图层配置色，不能被要素的 normal 状态统一覆盖成绿色。
      const color = Cesium.Color.fromCssColorString(layer.style.color);
      const midpoint =
        f.geometry.coordinates[Math.floor(f.geometry.coordinates.length / 2)];
      const label =
        layer.style.showLabel === false
          ? undefined
          : {
              text: f.name,
              font: `600 ${layer.style.labelSize || (isDashboard ? 13 : 14)}px Microsoft YaHei`,
              fillColor: Cesium.Color.fromCssColorString(
                layer.style.labelColor || "#ffffff",
              ),
              outlineColor: Cesium.Color.fromCssColorString("#173247"),
              outlineWidth: 4,
              style: Cesium.LabelStyle.FILL_AND_OUTLINE,
              showBackground: true,
              backgroundColor: Cesium.Color.fromCssColorString("#173247").withAlpha(
                isDashboard ? 0.78 : 0.84,
              ),
              backgroundPadding: new Cesium.Cartesian2(7, 4),
              pixelOffset: new Cesium.Cartesian2(0, -18),
              disableDepthTestDistance: Number.POSITIVE_INFINITY,
            };
      return [
        viewer.entities.add({
          ...entityMeta(f),
          id: `${f.id}-glow`,
          polyline: {
            positions,
            width: lineWidth + 8,
            material: new Cesium.PolylineGlowMaterialProperty({
              color: color.withAlpha(0.42),
              glowPower: 0.28,
            }),
            clampToGround: false,
          },
        }),
        viewer.entities.add({
          ...entityMeta(f),
          position: CoordinateAdapter.wgs84(midpoint),
          label,
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
