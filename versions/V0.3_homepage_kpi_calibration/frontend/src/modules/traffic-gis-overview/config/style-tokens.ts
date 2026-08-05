export const tokens = {
  bg: "#041225",
  panel: "rgba(4,24,48,.78)",
  border: "rgba(34,135,255,.4)",
  text: "#d9f1ff",
  muted: "#6f93ac",
  cyan: "#22d7ff",
  blue: "#247bff",
  green: "#39e27d",
  yellow: "#f5c542",
  orange: "#ff8a34",
  red: "#ff4d5a",
  purple: "#9a6cff",
  /** 1–3 标段走廊主色 */
  section1: "#4DA3FF",
  section2: "#2EC8A6",
  section3: "#F0B429",
  /** E01 超标点 */
  e01Exceed: "#ff9f2f",
  e01Selected: "#ffb347",
} as const;

/**
 * 点/面标签「视觉」字号（总览高度约 3–5 万米可读）。
 * Cesium Label 请用 crispLabelFont(size) + LABEL_ATLAS_SCALE(0.5)：
 * 以 2× 字号写入字形图集再 scale 0.5，减轻中文糊边。
 * SVG 徽章同理：按 2× 栅格绘制，billboard 用 1× 宽高。
 */
export const labelSizes = {
  zoneDashboard: 14,
  zonePreview: 15,
  pointDashboard: 13,
  pointPreview: 14,
  slopeDashboard: 12,
  slopePreview: 13,
  chainageDashboard: 11,
  chainagePreview: 12,
  sectionDashboard: 14,
  sectionPreview: 13,
} as const;

/** Cesium Label scale：与 crispLabelFont 的 2× 字号配对 */
export const LABEL_ATLAS_SCALE = 0.5 as const;

export const LABEL_FONT_STACK =
  "Microsoft YaHei, PingFang SC, sans-serif" as const;

/** SVG / 纹理标签超采样倍率 */
export const LABEL_SUPERSAMPLE = 2 as const;

/** visual 14 → `bold 28px Microsoft YaHei, PingFang SC, sans-serif` */
export function crispLabelFont(
  visualPx: number,
  weight: "bold" | "600" = "bold",
): string {
  const atlasPx = Math.max(2, Math.round(visualPx) * 2);
  return `${weight} ${atlasPx}px ${LABEL_FONT_STACK}`;
}

/** 整像素偏移，避免亚像素采样发糊 */
export function wholePx(n: number): number {
  return Math.round(n);
}

export const statusColors = {
  normal: tokens.green,
  attention: tokens.yellow,
  warning: tokens.orange,
  critical: tokens.red,
  offline: "#718092",
} as const;

export const sectionColors = {
  "section-1": tokens.section1,
  "section-2": tokens.section2,
  "section-3": tokens.section3,
} as const;
