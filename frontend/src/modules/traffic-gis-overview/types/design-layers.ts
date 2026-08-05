export interface DesignKmlLayerDefinition {
  id: string;
  name: string;
  file: string;
  format: "kml" | "kmz" | "geojson" | "compact-json";
  defaultVisible: boolean;
  loadMode: "eager" | "onDemand" | "manual";
  clampToGround: boolean;
  minCameraHeight?: number;
  maxCameraHeight?: number;
  overviewRectangle?: [number, number, number, number];
  featureCount: number;
  coordinateCount: number;
  sourceLayers: string[];
  stylePolicy: "preserve-original-kml-inline-style" | string;
  note?: string;
  available?: boolean;
  dataStatus?: string;
}

export interface DesignLayerGroup {
  id: string;
  name: string;
  order: number;
  layers: DesignKmlLayerDefinition[];
}

export interface DesignLayerManifest {
  project: string;
  sourceFile: string;
  coordinateSystemLabel: string;
  recommendedLoader: string;
  stylePolicy: string;
  selectionPolicy: string;
  groups: DesignLayerGroup[];
}

export interface DesignLayerRuntimeState {
  visible: boolean;
  loaded: boolean;
  loading: boolean;
  opacity: number;
  error?: string;
}

export type DesignLayerStateMap = Record<string, DesignLayerRuntimeState>;
