import * as Cesium from "cesium";
import { trafficGisConfig } from "../../config/traffic-gis.config";
import {
  LABEL_ATLAS_SCALE,
  crispLabelFont,
  labelSizes,
  wholePx,
} from "../../config/style-tokens";
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
    const nearScale = isDashboard ? 1.0 : 1.0;
    const farScale = isDashboard ? 0.5 : 0.75;
    const labelBgAlpha = isDashboard ? 0.62 : 0.74;
    const defaultPointLabel = isDashboard
      ? labelSizes.pointDashboard
      : labelSizes.pointPreview;
    const defaultSlopeLabel = isDashboard
      ? labelSizes.slopeDashboard
      : labelSizes.slopePreview;
    const labelSize = layer.style.labelSize || defaultPointLabel;

    return features.map((f) => {
      if (f.geometry.type !== "Point")
        throw new Error("PointRenderer收到非点要素");
      const color = featureColor(f, layer.style.color);
      const isSlope = f.objectType === "slope-monitor";
      const isRisk = f.objectType === "risk-point";

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
            font: crispLabelFont(
              isDashboard
                ? labelSizes.chainageDashboard
                : labelSizes.chainagePreview,
            ),
            scale: LABEL_ATLAS_SCALE,
            fillColor: Cesium.Color.fromCssColorString("#eafaff"),
            outlineColor: Cesium.Color.fromCssColorString("#031522"),
            outlineWidth: 4,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            showBackground: true,
            backgroundColor: Cesium.Color.fromCssColorString("#061827").withAlpha(
              isDashboard ? 0.62 : 0.74,
            ),
            backgroundPadding: new Cesium.Cartesian2(6, 4),
            pixelOffset: new Cesium.Cartesian2(0, wholePx(-17)),
            distanceDisplayCondition: new Cesium.DistanceDisplayCondition(
              0,
              isDashboard ? 36000 : 42000,
            ),
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
            scaleByDistance: new Cesium.NearFarScalar(2000, 1.0, 40000, 0.75),
          },
        });

      const displayName = isSlope
        ? f.name.replace(/^边坡监测点/, "边坡")
        : f.name;

      const pointLabelPx = isSlope
        ? Math.max(layer.style.labelSize || defaultSlopeLabel, 11)
        : labelSize;

      const label =
        layer.style.showLabel === false
          ? undefined
          : {
              text: displayName,
              font: crispLabelFont(pointLabelPx),
              scale: LABEL_ATLAS_SCALE,
              fillColor: Cesium.Color.fromCssColorString(
                layer.style.labelColor || "#ffffff",
              ),
              outlineColor: Cesium.Color.fromCssColorString("#041225"),
              outlineWidth: 4,
              style: Cesium.LabelStyle.FILL_AND_OUTLINE,
              showBackground: true,
              backgroundPadding: new Cesium.Cartesian2(7, 4),
              backgroundColor: Cesium.Color.fromCssColorString(
                isSlope ? "#2a1210" : isRisk ? "#2a1608" : "#06182a",
              ).withAlpha(labelBgAlpha),
              // 边坡/风险标签偏一侧，减少压住走廊
              pixelOffset: new Cesium.Cartesian2(
                wholePx(isSlope || isRisk ? 16 : 0),
                wholePx(isSlope || isRisk ? 10 : -46),
              ),
              verticalOrigin:
                isSlope || isRisk
                  ? Cesium.VerticalOrigin.TOP
                  : Cesium.VerticalOrigin.BOTTOM,
              distanceDisplayCondition: new Cesium.DistanceDisplayCondition(
                0,
                isSlope
                  ? 36000
                  : trafficGisConfig.lod.labelMaxHeight,
              ),
              disableDepthTestDistance: Number.POSITIVE_INFINITY,
              scaleByDistance: new Cesium.NearFarScalar(2000, 1.0, 52000, 0.75),
            };

      const iconW = Math.round((isSlope ? 32 : 36) * iconScale);
      const iconH = Math.round((isSlope ? 38 : 44) * iconScale);

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
