export type FeatureStatus =
  "normal" | "attention" | "warning" | "critical" | "offline";
export interface PointGeometry {
  type: "Point";
  coordinates: number[];
}
export interface LineGeometry {
  type: "LineString";
  coordinates: number[][];
}
export interface PolygonGeometry {
  type: "Polygon";
  coordinates: number[][][];
}
export type TrafficGeometry = PointGeometry | LineGeometry | PolygonGeometry;
export interface TrafficMapFeature {
  id: string;
  layerId: string;
  objectType: string;
  name: string;
  geometry: TrafficGeometry;
  properties: Record<string, unknown>;
  status?: FeatureStatus;
  statusLabel?: string;
  riskLevel?: 1 | 2 | 3 | 4;
  updatedAt?: string;
  businessSummary?: BusinessSummary;
  relationSummary?: RelationSummary;
  relations?: FeatureRelation[];
}

export interface BusinessSummary {
  statusCode?: string;
  statusLabel?: string;
  title?: string;
  dashboardRows?: Array<{ label: string; value: string }>;
  dashboardNote?: string;
  previewRows?: Array<{ label: string; value: string }>;
  targetModule?: string;
  targetRoute?: string;
}

export interface RelationSummary {
  total: number;
  pendingCount: number;
  highRiskCount: number;
  byType: Array<{
    type: string;
    typeLabel: string;
    count: number;
  }>;
}

export interface FeatureRelation {
  type: string;
  typeLabel?: string;
  code?: string;
  name: string;
  status?: string;
  riskLevel?: number;
  sourceTable?: string;
  sourceId?: string;
  summary?: string;
  updatedAt?: string;
}

export interface RelationsResponse {
  featureId: string;
  featureName: string;
  objectType: string;
  summary: RelationSummary;
  items: FeatureRelation[];
}

export interface BusinessLinkItem {
  id: string;
  type: string;
  typeLabel?: string;
  code?: string;
  title: string;
  status?: string;
  riskLevel?: number;
  summary?: string;
  sourceTable?: string;
  sourceId?: string;
  targetKpiCode?: string;
  targetModule?: string;
  targetModuleGroup?: string;
  actionLabel?: string;
  actionEnabled?: boolean;
  actionTip?: string;
  updatedAt?: string;
}

export interface BusinessLinksResponse {
  featureId: string;
  featureName: string;
  objectType: string;
  statusLabel?: string;
  title?: string;
  summary: RelationSummary;
  items: BusinessLinkItem[];
  permissions: {
    canView: boolean;
    canSupervise: boolean;
    canHandle: boolean;
    notice?: string;
  };
}

export interface GisBusinessLinkOpenPayload {
  targetType: "E02" | "S02";
  sourceId: string;
  sourceTable?: string;
  gisFeatureId?: string;
  title?: string;
}
export interface TrafficMapContext {
  projectId: string;
  sectionId?: string;
  currentTime?: string | Date;
  visibleLayerIds?: string[];
}
export interface TrafficLayerStyle {
  color: string;
  width?: number;
  opacity?: number;
  outlineColor?: string;
  icon?: string;
  showLabel?: boolean;
  labelColor?: string;
  labelSize?: number;
  labelField?: string;
}
export interface TrafficLayerDefinition {
  id: string;
  name: string;
  geometryType: "point" | "line" | "polygon" | "tileset";
  enabled: boolean;
  source: { type: "mock" | "api" | "geojson" | "tileset"; url?: string };
  style: TrafficLayerStyle;
  objectType?: string;
  featureCount?: number;
  fields?: string[];
  minCameraHeight?: number;
  maxCameraHeight?: number;
  zIndex?: number;
}
export interface TrafficDataAdapter {
  getLayers(context: TrafficMapContext): Promise<TrafficLayerDefinition[]>;
  getFeatures(
    layer: TrafficLayerDefinition,
    context: TrafficMapContext,
  ): Promise<TrafficMapFeature[]>;
  getFeatureDetail?(
    feature: TrafficMapFeature,
  ): Promise<Record<string, unknown>>;
  getRelations?(
    feature: TrafficMapFeature,
    context: TrafficMapContext,
  ): Promise<RelationsResponse>;
  getBusinessLinks?(
    feature: TrafficMapFeature,
    context: TrafficMapContext,
  ): Promise<BusinessLinksResponse>;
}
export interface InitialView {
  longitude: number;
  latitude: number;
  height: number;
  heading?: number;
  pitch?: number;
  roll?: number;
}
export type PresentationMode = "preview" | "dashboard";

export interface E01MapMarker {
  eventId: number;
  pointId: number;
  label: string;
  shortLabel?: string;
  monitorCategory?: string;
  longitude: number;
  latitude: number;
  status: string;
  isOpen: boolean;
  highlighted?: boolean;
  dimmed?: boolean;
  gisFeatureId?: string | null;
}

export interface TrafficGisOverviewProps {
  projectId: string;
  sectionId?: string;
  currentTime?: string | Date;
  visibleLayerIds?: string[];
  selectedFeatureId?: string;
  initialView?: InitialView;
  showLegend?: boolean;
  showModeSwitch?: boolean;
  showConfigButton?: boolean;
  interactionEnabled?: boolean;
  dataMode?: "mock" | "api" | "shp";
  presentationMode?: PresentationMode;
  /**
   * 仅显示项目设计图层，不加载旧业务/演示图层、用户矢量和空间资源。
   * 用于 S1-6“项目一张图”作为首页唯一空间底图的场景。
   */
  designOnly?: boolean;
  e01Active?: boolean;
  e01Markers?: E01MapMarker[];
  e01SelectedEventId?: number | null;
  e01SelectedPointId?: number | null;
  e01ShowInfoCard?: boolean;
  /** E02 工作台激活时：空白点击清除选中；要素点击上报 featureId */
  e02Active?: boolean;
  e02SelectedFeatureId?: string | null;
  /** E03 工作台激活时：空白点击清除选中；要素点击上报 featureId */
  e03Active?: boolean;
  e03SelectedFeatureId?: string | null;
  /** S02 安全风险点工作台 */
  s02Active?: boolean;
  s02SelectedFeatureId?: string | null;
}
