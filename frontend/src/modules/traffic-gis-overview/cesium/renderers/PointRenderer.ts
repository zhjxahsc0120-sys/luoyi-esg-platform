import * as Cesium from "cesium";
import { trafficGisConfig } from "../../config/traffic-gis.config";
import type {
  PresentationMode,
  TrafficLayerDefinition,
  TrafficMapFeature,
} from "../../types";
import { CoordinateAdapter } from "../core/CoordinateAdapter";
import { entityMeta, featureColor, featureIcon } from "./render-utils";

export class PointRenderer {
  render(
    viewer: Cesium.Viewer,
    layer: TrafficLayerDefinition,
    features: TrafficMapFeature[],
    presentationMode: PresentationMode = "preview",
  ) {
    const isDashboard = presentationMode === "dashboard";
    const iconScale = isDashboard ? 0.82 : 1.0;
    const nearScale = isDashboard ? 0.95 : 1.15;
    const farScale = isDashboard ? 0.58 : 0.72;
    const labelBgAlpha = isDashboard ? 0.72 : 0.88;
    const labelSize = isDashboard
      ? (layer.style.labelSize || 11)
      : (layer.style.labelSize || 12);

    return features.map((f) => {
      if (f.geometry.type !== "Point")
        throw new Error("PointRenderer收到非点要素");
      const color = featureColor(f, layer.style.color);
      const risk = f.objectType === "risk";
      const isEnvironmentMonitor = f.objectType === "environment-monitor";
      const isAlert = ["超标", "异常", "warning", "critical"].includes(f.status || "");
      const alertText = f.statusLabel || (f.status === "critical" ? "超标" : "预警");

      if (f.objectType === "chainage")
        return viewer.entities.add({
          ...entityMeta(f),
          position: CoordinateAdapter.wgs84(f.geometry.coordinates),
          point: {
            pixelSize: isDashboard ? 5 : 6,
            color: Cesium.Color.fromCssColorString("#eafaff"),
            outlineColor: Cesium.Color.fromCssColorString("#168cc2"),
            outlineWidth: 2,
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
          label: {
            text: f.name,
            font: `600 ${isDashboard ? 9 : 10}px Microsoft YaHei`,
            fillColor: Cesium.Color.fromCssColorString("#eafaff"),
            outlineColor: Cesium.Color.fromCssColorString("#031522"),
            outlineWidth: 4,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            showBackground: true,
            backgroundColor: Cesium.Color.fromCssColorString("#061827").withAlpha(
              isDashboard ? 0.58 : 0.72,
            ),
            backgroundPadding: new Cesium.Cartesian2(5, 3),
            pixelOffset: new Cesium.Cartesian2(0, -15),
            distanceDisplayCondition: new Cesium.DistanceDisplayCondition(
              0,
              isDashboard ? 30000 : 38000,
            ),
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
          },
        });

      const label =
        layer.style.showLabel === false || (isEnvironmentMonitor && !isAlert)
          ? undefined
          : {
              text: isEnvironmentMonitor && isAlert ? `⚠ ${f.name} · ${alertText}` : f.name,
              font: `${isAlert ? 600 : 400} ${isAlert ? labelSize + 1 : labelSize}px Microsoft YaHei`,
              fillColor: Cesium.Color.fromCssColorString(
                layer.style.labelColor || "#ffffff",
              ),
              outlineColor: Cesium.Color.fromCssColorString("#041225"),
              outlineWidth: 4,
              style: Cesium.LabelStyle.FILL_AND_OUTLINE,
              showBackground: true,
              backgroundPadding: new Cesium.Cartesian2(8, 5),
              backgroundColor: Cesium.Color.fromCssColorString(
                isAlert ? "#9f1024" : "#06182a",
              ).withAlpha(isAlert ? 0.94 : labelBgAlpha),
              pixelOffset: new Cesium.Cartesian2(0, -45),
              distanceDisplayCondition: new Cesium.DistanceDisplayCondition(
                0,
                f.objectType === "slope-monitor"
                  ? 16000
                  : trafficGisConfig.lod.labelMaxHeight,
              ),
              disableDepthTestDistance: Number.POSITIVE_INFINITY,
            };

      const iconW = Math.round((isAlert ? 56 : 34) * iconScale);
      const iconH = Math.round((isAlert ? 68 : 40) * iconScale);

      return viewer.entities.add({
        ...entityMeta(f),
        position: CoordinateAdapter.wgs84(f.geometry.coordinates),
        billboard: {
          image: featureIcon(f, color.toCssColorString()),
          width: iconW,
          height: iconH,
          verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
          scaleByDistance: new Cesium.NearFarScalar(
            1000,
            nearScale,
            180000,
            farScale,
          ),
          distanceDisplayCondition: new Cesium.DistanceDisplayCondition(
            0,
            trafficGisConfig.lod.pointMaxHeight,
          ),
        },
        label,
      });
    });
  }
}
