import type {
  BusinessLinksResponse,
  RelationsResponse,
  TrafficDataAdapter,
  TrafficLayerDefinition,
  TrafficMapContext,
  TrafficMapFeature,
} from "../types";
export class HttpTrafficAdapter implements TrafficDataAdapter {
  constructor(
    private readonly baseUrl = import.meta.env.VITE_TRAFFIC_API_BASE ||
      "/api/esg/gis",
  ) {}
  async getLayers(context: TrafficMapContext) {
    return this.request<TrafficLayerDefinition[]>("/layers", { ...context });
  }
  async getFeatures(layer: TrafficLayerDefinition, context: TrafficMapContext) {
    const features = await this.request<TrafficMapFeature[]>("/features", {
      ...context,
      layerId: layer.id,
    });
    const statusMap: Record<string, TrafficMapFeature['status']> = {
      '正常': 'normal', '达标': 'normal', '关注': 'attention', '待复测': 'warning',
      '预警': 'warning', '异常': 'warning', '超标': 'critical', '逾期': 'critical', '离线': 'offline',
    };
    return features.map(feature => {
      const rawStatus = String(feature.status || '');
      return {
        ...feature,
        status: statusMap[rawStatus] || feature.status,
        statusLabel: feature.statusLabel || rawStatus || undefined,
      };
    });
  }
  async getRelations(feature: TrafficMapFeature, context: TrafficMapContext) {
    return this.request<RelationsResponse>(
      `/features/${feature.id}/relations`,
      { projectId: context.projectId },
    );
  }
  async getBusinessLinks(feature: TrafficMapFeature, context: TrafficMapContext) {
    return this.request<BusinessLinksResponse>(
      `/features/${feature.id}/business-links`,
      { projectId: context.projectId },
    );
  }
  private async request<T>(path: string, params: Record<string, unknown>) {
    const query = new URLSearchParams(
      Object.entries(params)
        .filter(([, v]) => v != null)
        .map(([k, v]) => [k, String(v)]),
    );
    const response = await fetch(this.baseUrl + path + "?" + query);
    if (!response.ok) throw new Error("GIS接口失败 " + response.status);
    const body = (await response.json()) as { code: number; data: T };
    if (body.code !== 0) throw new Error("GIS接口返回失败");
    return body.data;
  }
}
