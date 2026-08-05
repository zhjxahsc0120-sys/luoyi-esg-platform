const GIS_API_BASE = import.meta.env.VITE_TRAFFIC_API_BASE || "/api/esg/gis";

type ConfigurationResponse<T> = {
  code: number;
  data: { key: string; value: T | null; version: number };
};

export async function loadGisConfiguration<T>(
  key: string,
  projectId = "LUOYI-ESG",
): Promise<T | null> {
  const query = new URLSearchParams({ projectId, key });
  const response = await fetch(`${GIS_API_BASE}/configuration?${query}`);
  if (!response.ok) throw new Error(`GIS配置读取失败 ${response.status}`);
  const body = (await response.json()) as ConfigurationResponse<T>;
  if (body.code !== 0) throw new Error("GIS配置读取失败");
  return body.data.value;
}

export async function saveGisConfiguration<T>(
  key: string,
  value: T,
  projectId = "LUOYI-ESG",
): Promise<void> {
  const response = await fetch(`${GIS_API_BASE}/configuration`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ projectId, key, value, operatorName: "项目管理员" }),
  });
  if (!response.ok) throw new Error(`GIS配置保存失败 ${response.status}`);
  const body = (await response.json()) as ConfigurationResponse<T>;
  if (body.code !== 0) throw new Error("GIS配置保存失败");
}
