import * as Cesium from "cesium";
import {
  LABEL_FONT_STACK,
  LABEL_SUPERSAMPLE,
  statusColors,
} from "../../config/style-tokens";
import type { TrafficMapFeature } from "../../types";

export const featureColor = (f: TrafficMapFeature, fallback: string) => {
  // 标段走廊线用图层配色，不因业务 status=normal 统一染成绿
  if (f.objectType === "road-section") {
    return Cesium.Color.fromCssColorString(fallback);
  }
  // 面状保护区也优先图层色，避免状态色覆盖语义色
  if (
    f.objectType === "spoil-site"
    || f.objectType === "water-source"
    || f.objectType === "ecological-zone"
  ) {
    return Cesium.Color.fromCssColorString(fallback);
  }
  return Cesium.Color.fromCssColorString(
    f.status ? statusColors[f.status] : fallback,
  );
};

export const entityMeta = (f: TrafficMapFeature) => ({
  id: f.id,
  name: f.name,
  properties: { trafficFeature: f },
});

const xml = (value: string) =>
  value.replace(
    /[&<>"']/g,
    (char) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&apos;" }[
        char
      ] || char),
  );

/** 边坡监测：菱形针点，区别于超标圆点 */
export function slopeMonitorIcon(color: string) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="40" height="48" viewBox="0 0 40 48">
  <defs><filter id="g"><feGaussianBlur stdDeviation="1.4"/></filter></defs>
  <path d="M20 46 L8 28 L20 6 L32 28 Z" fill="${color}" opacity=".35" filter="url(#g)"/>
  <path d="M20 42 L10 28 L20 10 L30 28 Z" fill="#06182a" stroke="${color}" stroke-width="2"/>
  <circle cx="20" cy="26" r="5" fill="${color}"/>
  <text x="20" y="29" text-anchor="middle" font-family="Microsoft YaHei" font-size="9" font-weight="700" fill="#06182a">坡</text>
</svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

const iconGlyph: Record<string, string> = {
  "slope-monitor": "坡",
  "spoil-site": "弃",
  "water-source": "水",
  "ecological-zone": "叶",
  risk: "!",
  monitor: "测",
};

export function featureIcon(f: TrafficMapFeature, color: string) {
  if (f.objectType === "slope-monitor") return slopeMonitorIcon(color);
  const glyph = iconGlyph[f.objectType] || "●";
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="44" height="54" viewBox="0 0 44 54"><filter id="g"><feGaussianBlur stdDeviation="2"/></filter><path d="M22 51S4 33 4 21a18 18 0 1 1 36 0c0 12-18 30-18 30z" fill="${color}" opacity=".45" filter="url(#g)"/><path d="M22 48S7 32 7 21a15 15 0 1 1 30 0c0 11-15 27-15 27z" fill="#06182a" stroke="${color}" stroke-width="2"/><circle cx="22" cy="21" r="10" fill="${color}" opacity=".22"/><text x="22" y="26" text-anchor="middle" font-family="Microsoft YaHei" font-size="13" font-weight="700" fill="white">${glyph}</text></svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

/**
 * 标段等气泡标签：按 2× 栅格绘制 SVG，billboard 用 1× 宽高（超采样更清晰）。
 */
export function featureLabel(
  text: string,
  accent: string,
  textColor = "#ffffff",
  fontSize = 13,
  options?: { fixedWidth?: number },
) {
  const ss = LABEL_SUPERSAMPLE;
  const visualFont = Math.round(fontSize);
  const fontSs = visualFont * ss;
  const widthSs = options?.fixedWidth
    ? Math.round(options.fixedWidth) * ss
    : Math.max(78 * ss, Math.round(Array.from(text).length * (fontSs * 0.95) + 28 * ss));
  const heightSs = (visualFont >= 15 ? 42 : 38) * ss;
  const textY = (visualFont >= 15 ? 21 : 19) * ss;
  const barH = (visualFont >= 15 ? 30 : 26) * ss;
  const safe = xml(text);
  const strokeW = Math.max(2, Math.round(ss));
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${widthSs}" height="${heightSs}" viewBox="0 0 ${widthSs} ${heightSs}"><linearGradient id="b" x2="1"><stop stop-color="#041224" stop-opacity=".9"/><stop offset="1" stop-color="#0a2438" stop-opacity=".86"/></linearGradient><path d="M${3 * ss} ${1 * ss}H${widthSs - 3 * ss}V${barH + ss}H${widthSs / 2 + 5 * ss}L${widthSs / 2} ${heightSs - 4 * ss}L${widthSs / 2 - 5 * ss} ${barH + ss}H${3 * ss}Z" fill="url(#b)" stroke="${accent}" stroke-width="${1.2 * ss}"/><text x="${widthSs / 2}" y="${textY}" text-anchor="middle" font-family="${LABEL_FONT_STACK}" font-size="${fontSs}" font-weight="700" fill="${textColor}" stroke="#041225" stroke-width="${strokeW}" paint-order="stroke fill">${safe}</text></svg>`;
  return {
    image: `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`,
    width: Math.round(widthSs / ss),
    height: Math.round(heightSs / ss),
  };
}

/** 地图标签统一：1标段→标段一，与导航/E01 列表口径一致 */
export function normalizeMapLabel(name: string): string {
  const text = (name || "").trim();
  const digit = text.match(/^([123])\s*标段$/);
  if (digit) {
    return ({ "1": "标段一", "2": "标段二", "3": "标段三" } as const)[
      digit[1] as "1" | "2" | "3"
    ];
  }
  const cn = text.match(/^标段\s*([一二三])$/);
  if (cn) return `标段${cn[1]}`;
  return text;
}

/**
 * 面状图层中心小徽章：2× 超采样绘制 + 轻描边，billboard 1× 显示。
 */
export function zoneLabel(
  text: string,
  accent: string,
  kind: "spoil-site" | "water-source" | "ecological-zone" | "default",
  fontSize = 14,
) {
  const ss = LABEL_SUPERSAMPLE;
  const visualFont = Math.round(fontSize);
  const fontSs = visualFont * ss;
  const padX = Math.round(visualFont * 0.85) * ss;
  const widthSs = Math.max(
    58 * ss,
    Array.from(text).length * Math.round(fontSs * 0.95) + padX * 2,
  );
  const heightSs = Math.max(26 * ss, Math.round(visualFont + 14) * ss);
  const safe = xml(text);
  const fillOpacity =
    kind === "water-source" ? ".72" : kind === "spoil-site" ? ".78" : ".74";
  const rx =
    (kind === "water-source"
      ? Math.round(heightSs / 2 / ss)
      : kind === "spoil-site"
        ? 3
        : 4) * ss;
  const badge = `<rect x="${ss}" y="${ss}" width="${widthSs - 2 * ss}" height="${heightSs - 2 * ss}" rx="${rx}" fill="${
    kind === "spoil-site" ? "#1a1208" : kind === "ecological-zone" ? "#071a12" : "#041824"
  }" fill-opacity="${fillOpacity}" stroke="${accent}" stroke-width="${1.35 * ss}" stroke-opacity=".9"/>`;
  const textY = Math.round(heightSs / 2 + fontSs * 0.32);
  const strokeW = Math.max(2, Math.round(ss));
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${widthSs}" height="${heightSs}" viewBox="0 0 ${widthSs} ${heightSs}">${badge}<text x="${widthSs / 2}" y="${textY}" text-anchor="middle" font-family="${LABEL_FONT_STACK}" font-size="${fontSs}" font-weight="700" fill="#ffffff" fill-opacity=".96" stroke="#041225" stroke-width="${strokeW}" paint-order="stroke fill">${safe}</text></svg>`;
  return {
    image: `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`,
    width: Math.round(widthSs / ss),
    height: Math.round(heightSs / ss),
  };
}
