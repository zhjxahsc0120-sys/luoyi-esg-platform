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
} as const;
export const statusColors = {
  normal: tokens.green,
  attention: tokens.yellow,
  warning: tokens.orange,
  critical: tokens.red,
  offline: "#718092",
} as const;
