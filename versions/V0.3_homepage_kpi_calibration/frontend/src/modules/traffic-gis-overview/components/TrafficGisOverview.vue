<script setup lang="ts">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from "vue";
import * as Cesium from "cesium";
import { History, Maximize2, Minimize2 } from "lucide-vue-next";
import FeatureCard from "./FeatureCard.vue";
import BusinessLinksPanel from "./BusinessLinksPanel.vue";
import LayerControl from "./LayerControl.vue";
import MapChrome from "./MapChrome.vue";
import { ViewerManager } from "../cesium/core/ViewerManager";
import { CameraManager } from "../cesium/core/CameraManager";
import { LayerRegistry } from "../cesium/layers/LayerRegistry";
import { BasemapManager } from "../cesium/layers/BasemapManager";
import { SpatialAssetManager } from "../cesium/layers/SpatialAssetManager";
import { HistoricalCompareManager } from "../cesium/layers/HistoricalCompareManager";
import { DesignKmlLayerManager } from "../cesium/layers/DesignKmlLayerManager";
import { defaultBasemapId, type BasemapId } from "../config/basemaps.config";
import { designMapConfig } from "../config/design-map.config";
import { historicalImagerySnapshots } from "../config/historical-imagery.config";
import {
  VectorLayerStore,
  parseGeoJson,
  type VectorLayerRecord,
} from "../vector/VectorLayerStore";
import {
  SpatialAssetStore,
  type SpatialAssetRecord,
  type SpatialAssetType,
} from "../assets/SpatialAssetStore";
import { PointRenderer } from "../cesium/renderers/PointRenderer";
import { PolylineRenderer } from "../cesium/renderers/PolylineRenderer";
import { PolygonRenderer } from "../cesium/renderers/PolygonRenderer";
import { PickManager } from "../cesium/interaction/PickManager";
import { HighlightManager } from "../cesium/interaction/HighlightManager";
import {
  MockTrafficAdapter,
  HttpTrafficAdapter,
  ShpTrafficAdapter,
} from "../adapters";
import type {
  BusinessLinksResponse,
  FeatureRelation,
  GisBusinessLinkOpenPayload,
  PresentationMode,
  TrafficGisOverviewProps,
  TrafficLayerDefinition,
  TrafficLayerStyle,
  TrafficMapContext,
  TrafficMapFeature,
  E01MapMarker,
} from "../types";
import { trafficGisConfig } from "../config/traffic-gis.config";
import {
  LABEL_ATLAS_SCALE,
  crispLabelFont,
  sectionColors,
  tokens,
  wholePx,
} from "../config/style-tokens";
import { CoordinateAdapter } from "../cesium/core/CoordinateAdapter";
import { featureColor } from "../cesium/renderers/render-utils";
import type { DesignLayerStateMap } from "../types/design-layers";

const props = withDefaults(defineProps<TrafficGisOverviewProps>(), {
  showLegend: true,
  showModeSwitch: true,
  showConfigButton: true,
  interactionEnabled: true,
  dataMode: "mock",
  presentationMode: "preview" as PresentationMode,
  designOnly: false,
  e01Active: false,
  e01Markers: () => [],
  e01SelectedEventId: null,
  e01SelectedPointId: null,
  e01ShowInfoCard: false,
  e02Active: false,
  e02SelectedFeatureId: null,
  e03Active: false,
  e03SelectedFeatureId: null,
  s02Active: false,
  s02SelectedFeatureId: null,
});

const emit = defineEmits<{
  ready: [{ viewerReady: true }];
  featureClick: [TrafficMapFeature];
  featureHover: [TrafficMapFeature | null];
  statsChange: [
    { visibleFeatureCount: number; warningCount: number; offlineCount: number },
  ];
  error: [{ layerId?: string; message: string; recoverable: boolean }];
  openKpiSource: [payload: GisBusinessLinkOpenPayload];
  e01EventSelect: [eventId: number];
  e01PointSelect: [pointId: number];
  e02FeatureSelect: [featureId: string];
  e02MapBlankClick: [];
  e03FeatureSelect: [featureId: string];
  e03MapBlankClick: [];
  s02FeatureSelect: [featureId: string];
  s02MapBlankClick: [];
  cameraMove: [];
}>();

const root = ref<HTMLElement>();
const canvas = ref<HTMLElement>();
const secondaryCanvas = ref<HTMLElement>();
const loading = ref(true);
const selected = ref<TrafficMapFeature | null>(null);
const relationsData = ref<FeatureRelation[]>([]);
const relationsLoading = ref(false);
const businessLinksData = ref<BusinessLinksResponse | null>(null);
const businessLinksLoading = ref(false);
const businessLinksOpen = ref(false);
const compassHeading = ref(0);
const mode = ref<"all" | "risk" | "construction" | "environment">("all");
const panelOpen = ref(false);
const activeBasemap = ref<BasemapId>(defaultBasemapId);
const availableLayers = ref<TrafficLayerDefinition[]>([]);
const visibleIds = ref<string[]>([]);
const vectorLayers = ref<VectorLayerRecord[]>([]);
const assets = ref<SpatialAssetRecord[]>([]);
const compareOpen = ref(false);
const compareMode = ref<"swipe" | "dual">("swipe");
const leftSnapshotId = ref("baseline");
const rightSnapshotId = ref("latest");
const splitPosition = ref(50);
const isMapFullscreen = ref(false);
const designLayerStates = ref<DesignLayerStateMap>({});

const vectorStore = new VectorLayerStore();
const assetStore = new SpatialAssetStore();
const manager = new ViewerManager();
const secondaryManager = new ViewerManager();
const registry = new LayerRegistry();
const highlighter = new HighlightManager();

let basemaps: BasemapManager | undefined;
let spatialAssets: SpatialAssetManager | undefined;
let historicalCompare: HistoricalCompareManager | undefined;
let designLayers: DesignKmlLayerManager | undefined;
let camera: CameraManager | undefined;
let picker: PickManager | undefined;
let resizeObserver: ResizeObserver | undefined;
let removeCameraChanged: (() => void) | undefined;
let removePrimaryCompareSync: (() => void) | undefined;
let removeSecondaryCompareSync: (() => void) | undefined;
let secondaryBasemaps: BasemapManager | undefined;
let syncingCompareCamera = false;
let loadVersion = 0;
let e01DataSource: Cesium.CustomDataSource | undefined;
let savedCameraView: ReturnType<CameraManager["captureView"]> | null = null;
const e02VisualBackup = new Map<string, {
  width?: number;
  material?: Cesium.MaterialProperty | Cesium.Color;
  billboardScale?: number;
  polygonMaterial?: Cesium.MaterialProperty | Cesium.Color;
}>();

const pointRenderer = new PointRenderer();
const lineRenderer = new PolylineRenderer();
const polygonRenderer = new PolygonRenderer();
const shpAdapter = new ShpTrafficAdapter();

const adapter = computed(() =>
  props.dataMode === "api"
    ? new HttpTrafficAdapter()
    : props.dataMode === "shp"
      ? shpAdapter
      : new MockTrafficAdapter(),
);

const STYLE_STORAGE_KEY = "traffic-esg-business-layer-styles-v1";

function savedStyles() {
  try {
    return JSON.parse(
      localStorage.getItem(STYLE_STORAGE_KEY) || "{}",
    ) as Record<string, Partial<TrafficLayerStyle>>;
  } catch {
    return {};
  }
}

const context = (): TrafficMapContext => ({
  projectId: props.projectId,
  sectionId: props.sectionId,
  currentTime: props.currentTime,
  visibleLayerIds: visibleIds.value,
});

function modeAllows(layer: TrafficLayerDefinition) {
  if (mode.value === "all") return true;

  const type = layer.objectType || "";

  if (mode.value === "construction") {
    return ["road-section", "spoil-site", "chainage"].includes(type);
  }

  if (mode.value === "environment") {
    return ["water-source", "ecological-zone", "spoil-site", "environment-monitor"].includes(type);
  }

  if (mode.value === "risk") {
    return ["slope-monitor", "risk-point"].includes(type);
  }

  return true;
}

async function renderLayer(
  layer: TrafficLayerDefinition,
  features: TrafficMapFeature[],
) {
  const viewer = manager.get();
  if (layer.geometryType === "point")
    return pointRenderer.render(viewer, layer, features, props.presentationMode);
  if (layer.geometryType === "line")
    return lineRenderer.render(viewer, layer, features, props.presentationMode);
  if (layer.geometryType === "polygon")
    return polygonRenderer.render(viewer, layer, features, props.presentationMode);
  return [];
}

async function loadDefinitions() {
  if (props.designOnly) {
    availableLayers.value = [];
    visibleIds.value = [];
    return;
  }
  const receivedLayers = await adapter.value.getLayers({
    ...context(),
    visibleLayerIds: undefined,
  });
  const layers =
    props.presentationMode === "dashboard"
      ? receivedLayers.filter(
          (layer) => layer.source.type === "api" && !layer.source.url,
        )
      : receivedLayers;
  const overrides = savedStyles();
  availableLayers.value = layers.map((layer) => ({
    ...layer,
    style: { ...layer.style, ...overrides[layer.id] },
  }));
  if (!visibleIds.value.length)
    visibleIds.value = props.visibleLayerIds?.length
      ? [...props.visibleLayerIds]
      : layers.filter((l) => l.enabled).map((l) => l.id);
}

async function load() {
  const version = ++loadVersion;
  loading.value = true;
  const viewer = manager.get();
  registry.clear(viewer);
  try {
    if (!availableLayers.value.length) await loadDefinitions();
    if (!props.designOnly) {
      for (const vector of vectorLayers.value.filter((item) => item.visible))
        registry.set(
          vector.id,
          await renderLayer(vector.definition, vector.features),
        );
    }
    let layers = availableLayers.value.filter((l) =>
      visibleIds.value.includes(l.id),
    );
    layers = layers.filter(modeAllows);
    let count = 0,
      warning = 0,
      offline = 0;
    for (const layer of layers) {
      try {
        const features = await adapter.value.getFeatures(layer, context());
        if (version !== loadVersion) return;
        registry.set(layer.id, await renderLayer(layer, features));
        count += features.length;
        warning += features.filter((f) =>
          ["warning", "critical", "超标", "异常"].includes(String(f.status || "")),
        ).length;
        offline += features.filter((f) => f.status === "offline").length;
      } catch (e) {
        emit("error", {
          layerId: layer.id,
          message: e instanceof Error ? e.message : "图层加载失败",
          recoverable: true,
        });
      }
    }
    emit("statsChange", {
      visibleFeatureCount: count,
      warningCount: warning,
      offlineCount: offline,
    });
  } catch (e) {
    emit("error", {
      message: e instanceof Error ? e.message : "地图数据加载失败",
      recoverable: true,
    });
  } finally {
    if (version === loadVersion) loading.value = false;
  }
}

async function syncAssets() {
  if (props.designOnly) return;
  try {
    await spatialAssets?.sync(assets.value);
  } catch (e) {
    emit("error", {
      message:
        e instanceof Error
          ? e.message
          : "空间资源加载失败，请检查 URL 和跨域设置",
      recoverable: true,
    });
  }
}

async function switchBasemap(id: BasemapId) {
  try {
    basemaps?.switchTo(id);
    activeBasemap.value = id;
    await syncAssets();
    selected.value = null;
    relationsData.value = [];
    businessLinksData.value = null;
    businessLinksOpen.value = false;
    await load();
  } catch (e) {
    emit("error", {
      message: e instanceof Error ? e.message : "底图切换失败",
      recoverable: true,
    });
  }
}

function toggleLayer(id: string, show: boolean) {
  visibleIds.value = show
    ? [...new Set([...visibleIds.value, id])]
    : visibleIds.value.filter((item) => item !== id);
  load();
}

async function styleLayer(id: string, style: Partial<TrafficLayerStyle>) {
  availableLayers.value = availableLayers.value.map((layer) =>
    layer.id === id ? { ...layer, style: { ...layer.style, ...style } } : layer,
  );
  const overrides = savedStyles();
  localStorage.setItem(
    STYLE_STORAGE_KEY,
    JSON.stringify({ ...overrides, [id]: { ...overrides[id], ...style } }),
  );
  await load();
}

async function addVector(file: File) {
  try {
    const record = parseGeoJson(
      await file.text(),
      file.name.replace(/\.(geojson|json)$/i, ""),
    );
    vectorLayers.value = await vectorStore.add(vectorLayers.value, record);
    await load();
    await locateVector(record.id);
  } catch (e) {
    emit("error", {
      message: e instanceof Error ? e.message : "矢量文件读取失败",
      recoverable: true,
    });
  }
}

async function toggleVector(id: string, visible: boolean) {
  vectorLayers.value = vectorLayers.value.map((item) =>
    item.id === id ? { ...item, visible } : item,
  );
  await vectorStore.save(vectorLayers.value);
  await load();
}

async function styleVector(id: string, style: Partial<TrafficLayerStyle>) {
  vectorLayers.value = vectorLayers.value.map((item) =>
    item.id === id
      ? {
          ...item,
          color: String(style.color || item.color),
          definition: {
            ...item.definition,
            style: { ...item.definition.style, ...style },
          },
        }
      : item,
  );
  await vectorStore.save(vectorLayers.value);
  await load();
}

async function removeVector(id: string) {
  registry.remove(id, manager.get());
  vectorLayers.value = await vectorStore.remove(vectorLayers.value, id);
}

async function locateVector(id: string) {
  const entities = registry.get(id);
  if (entities.length) await camera?.flyTo(entities);
}

async function addAsset(input: {
  name: string;
  type: SpatialAssetType;
  url: string;
}) {
  assets.value = await assetStore.add(assets.value, {
    ...input,
    visible: true,
    opacity: 1,
  });
  await syncAssets();
}

async function toggleAsset(id: string, visible: boolean) {
  assets.value = assets.value.map((item) =>
    item.id === id ? { ...item, visible } : item,
  );
  await assetStore.save(assets.value);
  await syncAssets();
}

async function removeAsset(id: string) {
  assets.value = await assetStore.remove(assets.value, id);
  await syncAssets();
}

async function locateAsset(id: string) {
  await spatialAssets?.locate(id);
}

async function refreshData() {
  availableLayers.value = [];
  await loadDefinitions();
  await load();
}

function featureOf(e: Cesium.Entity) {
  return e.properties?.trafficFeature?.getValue(Cesium.JulianDate.now()) as
    TrafficMapFeature | undefined;
}

function findEntity(id: string) {
  return registry.all().find((e) => featureOf(e)?.id === id);
}

async function flyToFeature(id: string, options?: { range?: number }) {
  try {
    const entity = findEntity(id);
    if (entity) {
      const now = Cesium.JulianDate.now();
      let cartesian: Cesium.Cartesian3 | undefined;
      if (entity.position) {
        cartesian = entity.position.getValue(now) as Cesium.Cartesian3 | undefined;
      }
      if (!cartesian && entity.polyline) {
        const positions = entity.polyline.positions?.getValue(now) as
          | Cesium.Cartesian3[]
          | undefined;
        if (positions?.length) {
          cartesian = positions[Math.floor(positions.length / 2)];
        }
      }
      if (cartesian) {
        const carto = Cesium.Cartographic.fromCartesian(cartesian);
        const feature = featureOf(entity);
        const defaultRange =
          feature?.objectType === "road-section"
            ? 8500
            : feature?.objectType === "slope-monitor"
              ? 4200
              : 4800;
        camera?.flyToLonLat(
          Cesium.Math.toDegrees(carto.longitude),
          Cesium.Math.toDegrees(carto.latitude),
          options?.range ?? defaultRange,
        );
        return;
      }
      await camera?.flyTo([entity]);
    }
  } catch {
    // Entity may not be ready.
  }
}

async function flyToSection(sectionId: string) {
  const entities = registry
    .all()
    .filter((e) => featureOf(e)?.properties.sectionId === sectionId);
  if (entities.length) await camera?.flyTo(entities);
}

async function refreshLayer() {
  await refreshData();
}

async function loadRelations() {
  if (!selected.value) return;
  const currentAdapter = adapter.value;
  if (!("getRelations" in currentAdapter)) return;
  relationsLoading.value = true;
  try {
    const res = await currentAdapter.getRelations(selected.value, context());
    relationsData.value = res.items || [];
    if (res.summary && selected.value) {
      selected.value = { ...selected.value, relationSummary: res.summary };
    }
  } catch (e) {
    emit("error", {
      message: e instanceof Error ? e.message : "关联事项加载失败",
      recoverable: true,
    });
  } finally {
    relationsLoading.value = false;
  }
}

async function loadBusinessLinks() {
  if (!selected.value) return;
  const currentAdapter = adapter.value;
  if (!("getBusinessLinks" in currentAdapter)) return;
  businessLinksLoading.value = true;
  businessLinksOpen.value = true;
  businessLinksData.value = null;
  try {
    const res = await currentAdapter.getBusinessLinks(
      selected.value,
      context(),
    );
    businessLinksData.value = res;
  } catch (e) {
    emit("error", {
      message: e instanceof Error ? e.message : "关联业务加载失败",
      recoverable: true,
    });
  } finally {
    businessLinksLoading.value = false;
  }
}

async function resetView() {
  if (designLayers?.hasLoadedLayers()) {
    try {
      await designLayers.locateOverview();
      return;
    } catch {
      // 图层正处于释放/切换过程时，继续使用原有视角兜底。
    }
  }
  if (props.dataMode === "shp" || props.dataMode === "api") {
    camera?.flyToRectangle(trafficGisConfig.projectRectangle);
  } else {
    camera?.reset(props.initialView);
  }
}

function northUp() {
  const viewer = manager.get();
  viewer.camera.cancelFlight();
  viewer.camera.setView({
    orientation: {
      heading: 0,
      pitch: viewer.camera.pitch,
      roll: 0,
    },
  });
  compassHeading.value = 0;
}

function updateDesignState(
  id: string,
  patch: Partial<DesignLayerStateMap[string]>,
) {
  designLayerStates.value = {
    ...designLayerStates.value,
    [id]: {
      visible: false,
      loaded: false,
      loading: false,
      opacity: 1,
      ...designLayerStates.value[id],
      ...patch,
    },
  };
}

async function toggleDesignLayer(id: string, visible: boolean) {
  const state = designLayerStates.value[id];
  updateDesignState(id, {
    visible,
    loading: visible,
    error: undefined,
  });
  try {
    await designLayers?.setVisible(id, visible, state?.opacity ?? 1);
    updateDesignState(id, {
      visible,
      loaded: visible,
      loading: false,
    });
  } catch (error) {
    updateDesignState(id, {
      visible: false,
      loaded: false,
      loading: false,
      error: error instanceof Error ? error.message : "图层加载失败",
    });
    emit("error", {
      layerId: id,
      message: error instanceof Error ? error.message : "设计图层加载失败",
      recoverable: true,
    });
  }
}

async function initializeDesignLayers() {
  try {
    const manifest = await designLayers?.init();
    if (!manifest) return;
    const states: DesignLayerStateMap = {};
    for (const group of manifest.groups) {
      for (const layer of group.layers) {
        states[layer.id] = {
          visible: false,
          loaded: false,
          loading: false,
          opacity: 1,
        };
      }
    }
    designLayerStates.value = states;
    for (const layer of manifest.groups.flatMap((group) => group.layers)) {
      if (layer.available !== false && layer.defaultVisible) {
        await toggleDesignLayer(layer.id, true);
      }
    }
    await designLayers?.locateOverview();
  } catch (error) {
    emit("error", {
      message:
        error instanceof Error ? error.message : "设计图层配置读取失败",
      recoverable: true,
    });
  }
}

function snapshot(id: string) {
  return historicalImagerySnapshots.find((item) => item.id === id) ?? historicalImagerySnapshots[0];
}

async function applyHistoricalCompare() {
  if (!historicalCompare || !compareOpen.value) return;
  if (compareMode.value === "dual") {
    await enableDualCompare();
    return;
  }
  disableDualCompare();
  historicalCompare.show(snapshot(leftSnapshotId.value).basemapId, snapshot(rightSnapshotId.value).basemapId, splitPosition.value / 100);
}

function copyCamera(source: Cesium.Viewer, target: Cesium.Viewer) {
  if (syncingCompareCamera) return;
  syncingCompareCamera = true;
  target.camera.setView({
    destination: source.camera.positionWC.clone(),
    orientation: {
      heading: source.camera.heading,
      pitch: source.camera.pitch,
      roll: source.camera.roll,
    },
  });
  target.scene.requestRender();
  queueMicrotask(() => syncingCompareCamera = false);
}

async function enableDualCompare() {
  await nextTick();
  if (!secondaryCanvas.value) return;
  basemaps?.switchTo(snapshot(leftSnapshotId.value).basemapId);
  const primary = manager.get();
  let secondary: Cesium.Viewer;
  try {
    secondary = secondaryManager.get();
  } catch {
    secondary = secondaryManager.create(secondaryCanvas.value);
    secondaryBasemaps = new BasemapManager(secondary);
  }
  secondaryBasemaps?.switchTo(snapshot(rightSnapshotId.value).basemapId);
  copyCamera(primary, secondary);
  if (!removePrimaryCompareSync) {
    removePrimaryCompareSync = primary.camera.changed.addEventListener(() => copyCamera(primary, secondaryManager.get()));
    removeSecondaryCompareSync = secondary.camera.changed.addEventListener(() => copyCamera(secondary, manager.get()));
  }
  nextTick(() => {
    manager.resize();
    secondaryManager.resize();
  });
}

function disableDualCompare() {
  removePrimaryCompareSync?.();
  removeSecondaryCompareSync?.();
  removePrimaryCompareSync = undefined;
  removeSecondaryCompareSync = undefined;
  secondaryManager.destroy();
  secondaryBasemaps = undefined;
  nextTick(() => manager.resize());
}

function toggleCompare() {
  compareOpen.value = !compareOpen.value;
  selected.value = null;
  businessLinksOpen.value = false;
  if (compareOpen.value) void applyHistoricalCompare();
  else {
    disableDualCompare();
    basemaps?.switchTo(activeBasemap.value);
  }
}

function changeCompareMode(value: "swipe" | "dual") {
  compareMode.value = value;
  splitPosition.value = value === "dual" ? 50 : splitPosition.value;
  void applyHistoricalCompare();
}

function updateSplit(value: number) {
  if (compareMode.value === "dual") return;
  splitPosition.value = value;
  historicalCompare?.setPosition(value / 100);
}

function beginSplitDrag(event: PointerEvent) {
  if (compareMode.value !== "swipe") return;
  event.preventDefault();
  const move = (next: PointerEvent) => {
    const rect = root.value?.getBoundingClientRect();
    if (!rect) return;
    updateSplit(Math.max(5, Math.min(95, ((next.clientX - rect.left) / rect.width) * 100)));
  };
  const stop = () => {
    window.removeEventListener("pointermove", move);
    window.removeEventListener("pointerup", stop);
  };
  window.addEventListener("pointermove", move);
  window.addEventListener("pointerup", stop, { once: true });
}

async function toggleMapFullscreen() {
  if (!root.value) return;
  if (document.fullscreenElement === root.value) await document.exitFullscreen();
  else await root.value.requestFullscreen();
}

function handleFullscreenChange() {
  isMapFullscreen.value = document.fullscreenElement === root.value;
  nextTick(() => {
    manager.resize();
    if (compareMode.value === "dual") secondaryManager.resize();
  });
}


function getFeatureScreenPoint(id: string): { x: number; y: number } | null {
  try {
    const viewer = manager.get();
    const entity = findEntity(id);
    if (!entity) return null;
    const now = Cesium.JulianDate.now();
    let cartesian: Cesium.Cartesian3 | undefined;
    if (entity.position) {
      cartesian = entity.position.getValue(now) as Cesium.Cartesian3 | undefined;
    }
    if (!cartesian && entity.polyline) {
      const positions = entity.polyline.positions?.getValue(now) as
        | Cesium.Cartesian3[]
        | undefined;
      if (positions?.length) {
        cartesian = positions[Math.floor(positions.length / 2)];
      }
    }
    if (!cartesian) return null;
    const windowPos = Cesium.SceneTransforms.worldToWindowCoordinates(
      viewer.scene,
      cartesian,
    );
    if (!windowPos) return null;
    const canvasEl = viewer.scene.canvas;
    const canvasRect = canvasEl.getBoundingClientRect();
    const rootRect = root.value?.getBoundingClientRect();
    if (!rootRect) return { x: windowPos.x, y: windowPos.y };
    const scaleX = canvasRect.width / canvasEl.clientWidth;
    const scaleY = canvasRect.height / canvasEl.clientHeight;
    return {
      x: canvasRect.left - rootRect.left + windowPos.x * scaleX,
      y: canvasRect.top - rootRect.top + windowPos.y * scaleY,
    };
  } catch {
    return null;
  }
}

function restoreE02SelectionVisual() {
  for (const entity of registry.all()) {
    const key = String(entity.id);
    const backup = e02VisualBackup.get(key);
    if (!backup) continue;
    if (backup.width != null && entity.polyline) {
      entity.polyline.width = new Cesium.ConstantProperty(backup.width);
    }
    if (backup.material != null && entity.polyline) {
      entity.polyline.material = backup.material as Cesium.MaterialProperty;
    }
    if (backup.billboardScale != null && entity.billboard) {
      entity.billboard.scale = new Cesium.ConstantProperty(backup.billboardScale);
    }
    if (backup.polygonMaterial != null && entity.polygon) {
      entity.polygon.material = backup.polygonMaterial as Cesium.MaterialProperty;
    }
  }
  e02VisualBackup.clear();
}

function applyE02SelectionVisual(
  selectedId: string | null,
  relatedIds: string[] = [],
) {
  restoreE02SelectionVisual();
  if (!selectedId && !relatedIds.length) return;
  const related = new Set(relatedIds.length ? relatedIds : selectedId ? [selectedId] : []);
  for (const entity of registry.all()) {
    const feature = featureOf(entity);
    if (!feature) continue;
    if (String(entity.id).endsWith("-glow")) continue;
    const key = String(entity.id);
    const backup: {
      width?: number;
      material?: Cesium.MaterialProperty | Cesium.Color;
      billboardScale?: number;
      polygonMaterial?: Cesium.MaterialProperty | Cesium.Color;
    } = {};
    if (entity.polyline) {
      const widthProp = entity.polyline.width;
      backup.width =
        typeof widthProp?.getValue === "function"
          ? Number(widthProp.getValue(Cesium.JulianDate.now()))
          : Number(widthProp) || 4;
      backup.material = entity.polyline.material as Cesium.MaterialProperty;
    }
    if (entity.billboard) {
      const scaleProp = entity.billboard.scale;
      backup.billboardScale =
        typeof scaleProp?.getValue === "function"
          ? Number(scaleProp.getValue(Cesium.JulianDate.now()) ?? 1)
          : Number(scaleProp) || 1;
    }
    if (entity.polygon) {
      backup.polygonMaterial = entity.polygon.material as Cesium.MaterialProperty;
    }
    e02VisualBackup.set(key, backup);
    const isSelected = feature.id === selectedId;
    const isRelated = related.has(feature.id);
    const sectionKey = feature.id.replace(/-\d+$/, "") as keyof typeof sectionColors;
    const fallback =
      sectionColors[sectionKey]
      || sectionColors[feature.id as keyof typeof sectionColors]
      || tokens.cyan;
    const base = featureColor(feature, fallback);
    if (isSelected) {
      if (entity.polyline) {
        const bump = feature.objectType === "road-section" ? 1.5 : 2.5;
        entity.polyline.width = new Cesium.ConstantProperty(
          Math.max((backup.width || 3) + bump, 5),
        );
        entity.polyline.material = new Cesium.ColorMaterialProperty(base.withAlpha(1));
      }
      if (entity.billboard) {
        entity.billboard.scale = new Cesium.ConstantProperty(1.35);
      }
      if (entity.polygon) {
        entity.polygon.material = new Cesium.ColorMaterialProperty(base.withAlpha(0.55));
      }
    } else if (isRelated) {
      if (entity.polyline) {
        entity.polyline.width = new Cesium.ConstantProperty(backup.width || 3);
        entity.polyline.material = new Cesium.ColorMaterialProperty(base.withAlpha(0.55));
      }
      if (entity.billboard) {
        entity.billboard.scale = new Cesium.ConstantProperty(1);
      }
    } else {
      if (entity.polyline) {
        entity.polyline.width = new Cesium.ConstantProperty(
          Math.max((backup.width || 3) - 0.5, 2),
        );
        entity.polyline.material = new Cesium.ColorMaterialProperty(base.withAlpha(0.2));
      }
      if (entity.billboard) {
        entity.billboard.scale = new Cesium.ConstantProperty(0.85);
      }
      if (entity.polygon) {
        entity.polygon.material = new Cesium.ColorMaterialProperty(base.withAlpha(0.12));
      }
    }
  }
}

async function flyToLonLat(longitude: number, latitude: number, range = 12000) {
  camera?.flyToLonLat(longitude, latitude, range);
}

async function flyToPoints(
  points: Array<{ longitude?: number | null; latitude?: number | null }>,
  options?: { singleRange?: number },
) {
  camera?.flyToPoints(points, options);
}

function captureMapState() {
  savedCameraView = camera?.captureView() ?? null;
  return { camera: savedCameraView };
}

function restoreMapState() {
  if (savedCameraView) camera?.restoreView(savedCameraView);
  else void resetView();
  clearE01Markers();
}

function clearE01Markers() {
  if (e01DataSource) e01DataSource.entities.removeAll();
}

function syncE01Markers(markers: E01MapMarker[], selectedPointId: number | null | undefined) {
  try {
    const viewer = manager.get();
    if (!e01DataSource) {
      e01DataSource = new Cesium.CustomDataSource("e01-exceed-markers");
      viewer.dataSources.add(e01DataSource);
    }
    e01DataSource.entities.removeAll();
    const accent = Cesium.Color.fromCssColorString(tokens.e01Exceed);
    const selectedAccent = Cesium.Color.fromCssColorString(tokens.e01Selected);
    for (const marker of markers) {
      if (marker.longitude == null || marker.latitude == null) continue;
      const [lon, lat] = CoordinateAdapter.displayLngLat(marker.longitude, marker.latitude);
      const selected =
        selectedPointId != null
          ? marker.pointId === selectedPointId
          : Boolean(marker.highlighted);
      const dimmed =
        marker.dimmed === true ||
        (selectedPointId != null && marker.pointId !== selectedPointId);
      const shortLabel = marker.shortLabel || "点";
      const feature: TrafficMapFeature = {
        id: `e01-point-${marker.pointId}`,
        layerId: "e01-exceed",
        objectType: "e01-exceed-point",
        name: marker.label,
        geometry: { type: "Point", coordinates: [marker.longitude, marker.latitude] },
        properties: {
          e01EventId: marker.eventId,
          pointId: marker.pointId,
          status: marker.status,
          gisFeatureId: marker.gisFeatureId,
        },
        status: "warning",
        statusLabel: marker.status,
      };
      e01DataSource.entities.add({
        id: `e01-point-${marker.pointId}`,
        position: Cesium.Cartesian3.fromDegrees(lon, lat, 40),
        point: {
          pixelSize: selected ? 18 : dimmed ? 8 : 12,
          color: dimmed ? accent.withAlpha(0.28) : selected ? selectedAccent : accent,
          outlineColor: selected
            ? Cesium.Color.WHITE
            : Cesium.Color.WHITE.withAlpha(dimmed ? 0.25 : 0.9),
          outlineWidth: selected ? 4 : 2,
          heightReference: Cesium.HeightReference.RELATIVE_TO_GROUND,
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
        },
        label: {
          text: selected ? `${shortLabel} · ${marker.label}` : shortLabel,
          font: crispLabelFont(selected ? 12 : 11),
          scale: LABEL_ATLAS_SCALE,
          fillColor: Cesium.Color.WHITE,
          outlineColor: Cesium.Color.BLACK,
          outlineWidth: 4,
          style: Cesium.LabelStyle.FILL_AND_OUTLINE,
          verticalOrigin: Cesium.VerticalOrigin.TOP,
          pixelOffset: new Cesium.Cartesian2(0, wholePx(selected ? 16 : 12)),
          showBackground: true,
          backgroundColor: Cesium.Color.fromCssColorString("#1a1208").withAlpha(
            selected ? 0.78 : 0.62,
          ),
          backgroundPadding: new Cesium.Cartesian2(6, 3),
          disableDepthTestDistance: Number.POSITIVE_INFINITY,
          scaleByDistance: new Cesium.NearFarScalar(2000, 1.0, 52000, 0.75),
          show: !dimmed || selected,
        },
        properties: { trafficFeature: feature },
      });
    }
  } catch {
    // Viewer may not be ready yet.
  }
}

defineExpose({
  flyToFeature,
  flyToSection,
  flyToLonLat,
  flyToPoints,
  refreshLayer,
  resetView,
  captureMapState,
  restoreMapState,
  syncE01Markers,
  clearE01Markers,
  getFeatureScreenPoint,
  applyE02SelectionVisual,
  restoreE02SelectionVisual,
});

onMounted(async () => {
  await nextTick();
  const viewer = manager.create(canvas.value!);
  basemaps = new BasemapManager(viewer);
  spatialAssets = new SpatialAssetManager(viewer);
  historicalCompare = new HistoricalCompareManager(viewer);
  designLayers = new DesignKmlLayerManager(
    viewer,
    designMapConfig.manifestUrl,
    designMapConfig.releaseOnHide,
  );
  basemaps.switchTo(activeBasemap.value);
  if (!props.designOnly) {
    vectorLayers.value = await vectorStore.load();
    assets.value = await assetStore.load();
  }
  camera = new CameraManager(viewer);
  if (trafficGisConfig.corridorLock?.enabled) {
    camera.enableCorridorLock({
      rectangle: trafficGisConfig.corridorLock.rectangle,
      minHeight: trafficGisConfig.corridorLock.minHeight,
      maxHeight: trafficGisConfig.corridorLock.maxHeight,
    });
  }
  const updateHeading = () => {
    compassHeading.value = -Cesium.Math.toDegrees(viewer.camera.heading);
    emit("cameraMove");
  };
  updateHeading();
  removeCameraChanged = viewer.camera.changed.addEventListener(updateHeading);
  camera.reset(props.initialView);
  if (props.interactionEnabled) {
    picker = new PickManager(viewer);
    picker.bind(
      (f, e) => {
        highlighter.select(e);
        selected.value = f;
        relationsData.value = [];
        businessLinksData.value = null;
        businessLinksOpen.value = false;
        emit("featureClick", f);
        if (f.objectType === "e01-exceed-point") {
          const eventId = Number(f.properties?.e01EventId);
          const pointId = Number(f.properties?.pointId);
          if (Number.isFinite(pointId)) emit("e01PointSelect", pointId);
          if (Number.isFinite(eventId)) emit("e01EventSelect", eventId);
          return;
        }
        if (props.e03Active) {
          emit("e03FeatureSelect", f.id);
          void flyToFeature(f.id);
          return;
        }
        if (props.s02Active) {
          emit("s02FeatureSelect", f.id);
          void flyToFeature(f.id);
          return;
        }
        if (props.e02Active) {
          emit("e02FeatureSelect", f.id);
          void flyToFeature(f.id);
          return;
        }
        if (f.objectType === "road-section") void flyToFeature(f.id);
      },
      (f) => emit("featureHover", f || null),
      () => {
        if (props.e03Active) {
          highlighter.restore();
          selected.value = null;
          emit("e03MapBlankClick");
          return;
        }
        if (props.s02Active) {
          highlighter.restore();
          selected.value = null;
          emit("s02MapBlankClick");
          return;
        }
        if (props.e02Active) {
          highlighter.restore();
          selected.value = null;
          emit("e02MapBlankClick");
        }
      },
    );
  }
  resizeObserver = new ResizeObserver(() => manager.resize());
  resizeObserver.observe(root.value!);
  document.addEventListener("fullscreenchange", handleFullscreenChange);
  await initializeDesignLayers();
  if (!props.designOnly) await syncAssets();
  await loadDefinitions();
  await load();
  if (props.selectedFeatureId) await flyToFeature(props.selectedFeatureId);
  if (
    (props.dataMode === "shp" || props.dataMode === "api") &&
    !props.sectionId && !props.selectedFeatureId
  ) {
    if (designLayers?.hasLoadedLayers()) {
      await designLayers.locateOverview();
    } else {
      camera.flyToRectangle(trafficGisConfig.projectRectangle);
    }
  }
  emit("ready", { viewerReady: true });
});

onBeforeUnmount(() => {
  loadVersion++;
  resizeObserver?.disconnect();
  document.removeEventListener("fullscreenchange", handleFullscreenChange);
  removeCameraChanged?.();
  camera?.disableCorridorLock();
  disableDualCompare();
  picker?.destroy();
  highlighter.restore();
  restoreE02SelectionVisual();
  clearE01Markers();
  spatialAssets?.destroy();
  designLayers?.destroy();
  registry.clear(manager.get());
  manager.destroy();
});

watch(
  () => props.sectionId,
  async (sectionId) => {
    availableLayers.value = [];
    await refreshData();
    if (sectionId) await flyToSection(sectionId);
    else resetView();
  },
);

watch(
  () => [props.currentTime, props.dataMode],
  async () => {
    availableLayers.value = [];
    await refreshData();
  },
  { deep: true },
);

watch(
  () => props.visibleLayerIds,
  (ids) => {
    if (ids) {
      visibleIds.value = [...ids];
      load();
    }
  },
  { deep: true },
);

watch(
  () => props.selectedFeatureId,
  (id) => {
    if (id) flyToFeature(id);
  },
);

watch(
  () => [props.e01Active, props.e01Markers, props.e01SelectedPointId] as const,
  ([active, markers, selectedId]) => {
    if (!active) {
      clearE01Markers();
      return;
    }
    syncE01Markers(markers || [], selectedId ?? null);
  },
  { deep: true },
);

watch(mode, load);
watch([leftSnapshotId, rightSnapshotId], () => void applyHistoricalCompare());

function handleOpenKpiSource(payload: GisBusinessLinkOpenPayload) {
  emit('openKpiSource', {
    ...payload,
    gisFeatureId: payload.gisFeatureId || selected.value?.id,
  });
}
</script>

<template>
  <div ref="root" class="traffic-gis-overview" :class="{ 'is-dual-compare': compareOpen && compareMode === 'dual' }">
    <div ref="canvas" class="traffic-gis-overview__canvas traffic-gis-overview__canvas--primary"></div>
    <div v-if="compareOpen && compareMode === 'dual'" ref="secondaryCanvas" class="traffic-gis-overview__canvas traffic-gis-overview__canvas--secondary"></div>
    <section v-if="compareOpen" class="traffic-gis-overview__compare-toolbar">
      <div class="compare-mode-tabs">
        <button :class="{ active: compareMode === 'swipe' }" @click="changeCompareMode('swipe')">卷帘对比</button>
        <button :class="{ active: compareMode === 'dual' }" @click="changeCompareMode('dual')">双屏联动</button>
      </div>
      <label>左侧
        <select v-model="leftSnapshotId">
          <option v-for="item in historicalImagerySnapshots" :key="item.id" :value="item.id">{{ item.label }} · {{ item.date }}</option>
        </select>
      </label>
      <label>右侧
        <select v-model="rightSnapshotId">
          <option v-for="item in historicalImagerySnapshots" :key="item.id" :value="item.id">{{ item.label }} · {{ item.date }}</option>
        </select>
      </label>
      <small v-if="snapshot(leftSnapshotId).placeholder || snapshot(rightSnapshotId).placeholder">历史影像未上传，当前节点使用配置底图占位</small>
      <button class="compare-close" @click="toggleCompare">退出对比</button>
    </section>
    <div v-if="compareOpen" class="traffic-gis-overview__side-label left-label">{{ snapshot(leftSnapshotId).label }} · {{ snapshot(leftSnapshotId).date }}</div>
    <div v-if="compareOpen" class="traffic-gis-overview__side-label right-label">{{ snapshot(rightSnapshotId).label }} · {{ snapshot(rightSnapshotId).date }}</div>
    <div v-if="compareOpen" class="traffic-gis-overview__split" :class="compareMode" :style="{ left: compareMode === 'dual' ? '50%' : splitPosition + '%' }" @pointerdown="beginSplitDrag">
      <i>{{ compareMode === 'swipe' ? '↔' : '联动' }}</i>
    </div>
    <MapChrome
      :mode="mode"
      :config-open="panelOpen"
      :heading="compassHeading"
      :show-config-button="showConfigButton"
      :show-mode-switch="showModeSwitch"
      :presentation-mode="presentationMode"
      @mode-change="mode = $event"
      @reset="resetView"
      @north="northUp"
      @config="panelOpen = !panelOpen"
    />
    <LayerControl
      v-if="!designOnly"
      :open="panelOpen"
      :active-basemap="activeBasemap"
      :layers="availableLayers"
      :visible-ids="visibleIds"
      :vector-layers="vectorLayers"
      :assets="assets"
      :loading="loading"
      @close="panelOpen = false"
      @basemap-change="switchBasemap"
      @layer-toggle="toggleLayer"
      @layer-style="styleLayer"
      @vector-upload="addVector"
      @vector-toggle="toggleVector"
      @vector-style="styleVector"
      @vector-remove="removeVector"
      @vector-locate="locateVector"
      @asset-add="addAsset"
      @asset-toggle="toggleAsset"
      @asset-remove="removeAsset"
      @asset-locate="locateAsset"
      @refresh="refreshData"
    />
    <FeatureCard
      v-if="selected"
      class="traffic-gis-overview__detail"
      :feature="selected"
      :presentation-mode="presentationMode"
      :relations="relationsData"
      :relations-loading="relationsLoading"
      @close="selected = null"
      @load-relations="loadRelations"
      @load-business-links="loadBusinessLinks"
    />
    <BusinessLinksPanel
      v-if="selected && businessLinksOpen"
      class="traffic-gis-overview__business-links"
      :data="businessLinksData"
      :loading="businessLinksLoading"
      :feature-name="selected.name"
      :presentation-mode="presentationMode"
      @close="businessLinksOpen = false"
      @open-kpi-source="handleOpenKpiSource"
    />
    <div v-if="loading" class="traffic-gis-overview__loading">
      业务图层加载中…
    </div>
    <div class="traffic-gis-overview__mock">
      {{
        designOnly
          ? "S1-6 设计图层"
          : dataMode === "mock"
          ? "演示数据库数据"
          : dataMode === "shp"
            ? "SHP 实测空间数据"
            : "实时数据库数据"
      }}
    </div>
    <div class="traffic-gis-overview__quick-actions">
      <button class="quick-action quick-action--history" :class="{ active: compareOpen }" @click="toggleCompare">
        <History :size="15" />{{ compareOpen ? '关闭历史对比' : '历史对比' }}
      </button>
      <button class="quick-action quick-action--fullscreen" @click="toggleMapFullscreen">
        <component :is="isMapFullscreen ? Minimize2 : Maximize2" :size="15" />{{ isMapFullscreen ? '退出全屏' : '地图全屏' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.traffic-gis-overview {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 280px;
  overflow: hidden;
  background: #eef3f7;
  color: #d9f1ff;
}
.traffic-gis-overview__canvas {
  position: absolute;
  inset: 0;
}
.traffic-gis-overview.is-dual-compare .traffic-gis-overview__canvas--primary {
  right: auto;
  width: calc(50% - 4px);
}
.traffic-gis-overview__canvas--secondary {
  left: calc(50% + 4px);
  width: calc(50% - 4px);
}
.traffic-gis-overview:fullscreen {
  width: 100vw;
  height: 100vh;
  min-height: 100vh;
  background: #020b18;
}
.traffic-gis-overview__compare-toolbar {
  position: absolute;
  z-index: 18;
  top: 12px;
  left: 50%;
  display: flex;
  max-width: calc(100% - 150px);
  align-items: center;
  gap: 7px;
  padding: 7px;
  transform: translateX(-50%);
  border: 1px solid rgba(34, 215, 255, .55);
  border-radius: 5px;
  background: rgba(2, 14, 29, .94);
  box-shadow: 0 8px 28px #0008;
  white-space: nowrap;
}
.traffic-gis-overview__compare-toolbar label { color: #8eb6cb; font-size: 11px; }
.traffic-gis-overview__compare-toolbar select {
  margin-left: 4px;
  padding: 5px 7px;
  color: #d9f1ff;
  border: 1px solid #245a7b;
  background: #061c32;
}
.traffic-gis-overview__compare-toolbar small { color: #ffbd55; font-size: 10px; }
.compare-mode-tabs { display: flex; }
.compare-mode-tabs button { padding: 6px 9px; }
.traffic-gis-overview__side-label {
  position: absolute;
  z-index: 14;
  top: 67px;
  padding: 5px 9px;
  color: #e4f8ff;
  border: 1px solid #277da8;
  background: rgba(3, 20, 38, .85);
  font-size: 11px;
  pointer-events: none;
}
.left-label { left: 12px; }
.right-label { right: 12px; }
.traffic-gis-overview__split {
  position: absolute;
  z-index: 16;
  top: 0;
  bottom: 0;
  width: 3px;
  transform: translateX(-50%);
  background: #fff;
  box-shadow: 0 0 8px #22d7ff;
}
.traffic-gis-overview__split.swipe { cursor: ew-resize; }
.traffic-gis-overview__split.dual { pointer-events: none; background: #020b18; width: 8px; box-shadow: 0 0 0 1px #2a749a; }
.traffic-gis-overview__split i {
  position: absolute;
  top: 50%;
  left: 50%;
  display: grid;
  min-width: 30px;
  height: 30px;
  place-items: center;
  padding: 0 5px;
  transform: translate(-50%, -50%);
  color: #03101f;
  border-radius: 50%;
  background: #eafaff;
  font-style: normal;
  font-size: 11px;
  user-select: none;
}
.traffic-gis-overview__quick-actions {
  position: absolute;
  z-index: 20;
  right: 12px;
  bottom: 10px;
  display: flex;
  gap: 6px;
}
.traffic-gis-overview__design-toggle {
  position: absolute;
  z-index: 15;
  top: 9px;
  left: 10px;
  display: inline-flex;
  min-height: 31px;
  align-items: center;
  gap: 6px;
  padding: 6px 10px !important;
  color: #e8fbff !important;
  border: 1px solid rgba(43, 217, 244, 0.54) !important;
  border-radius: 4px;
  background: rgba(3, 28, 48, 0.78) !important;
  box-shadow: 0 0 8px rgba(34, 215, 255, 0.16);
  font-size: 11px;
  font-weight: 700;
}
.traffic-gis-overview__design-toggle:hover {
  border-color: #fff !important;
  background: rgba(8, 82, 119, 0.88) !important;
}
.traffic-gis-overview .quick-action {
  display: inline-flex;
  min-height: 34px;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  color: #effcff;
  border: 1px solid rgba(56, 223, 255, .56);
  border-radius: 5px;
  background: rgba(3, 28, 48, .68);
  box-shadow: 0 0 6px rgba(34, 215, 255, .18);
  font-weight: 700;
  text-shadow: 0 0 4px rgba(34, 215, 255, .28);
  transition: .16s ease;
}
.traffic-gis-overview .quick-action--history {
  border-color: rgba(67, 225, 154, .58);
  background: rgba(5, 48, 42, .68);
  box-shadow: 0 0 6px rgba(67, 225, 154, .18);
}
.traffic-gis-overview .quick-action:hover,
.traffic-gis-overview .quick-action.active {
  color: #fff;
  border-color: #fff;
  background: rgba(8, 82, 119, .82);
  box-shadow: 0 0 10px rgba(34, 215, 255, .38);
  transform: translateY(-2px);
}
.traffic-gis-overview .quick-action--history:hover,
.traffic-gis-overview .quick-action--history.active {
  background: rgba(9, 92, 70, .82);
  box-shadow: 0 0 10px rgba(67, 225, 154, .36);
}
.traffic-gis-overview button {
  padding: 6px 12px;
  color: #8eb6cb;
  background: rgba(4, 24, 48, 0.9);
  border: 1px solid rgba(34, 135, 255, 0.34);
  cursor: pointer;
}
.traffic-gis-overview button.active {
  color: #d9f1ff;
  border-color: #22d7ff;
  background: rgba(20, 100, 145, 0.75);
}
.traffic-gis-overview .layer-button {
  margin-left: 5px;
}
.traffic-gis-overview__detail {
  position: absolute;
  right: 18px;
  /* 给右下角“历史对比 / 地图全屏”操作区预留安全距离。 */
  bottom: 58px;
  z-index: 10;
  max-width: calc(100% - 36px);
  max-height: calc(100% - 164px);
  overflow: hidden;
}
/* 关联业务侧浮层：限制在 GIS 面板内部右下角，不遮挡右侧专题和底部时间轴 */
.traffic-gis-overview__business-links {
  position: absolute;
  right: 18px;
  bottom: 58px;
  z-index: 11;
  max-width: calc(100% - 36px);
  max-height: calc(100% - 164px);
}
.traffic-gis-overview__loading {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  padding: 10px 16px;
  background: rgba(2, 11, 24, 0.78);
  font-size: 12px;
  pointer-events: none;
}
.traffic-gis-overview__mock {
  position: absolute;
  left: 14px;
  bottom: 10px;
  color: #6f93ac;
  font-size: 10px;
}
.traffic-gis-overview :deep(.cesium-viewer-bottom),
.traffic-gis-overview :deep(.cesium-viewer-toolbar) {
  display: none !important;
}
@media (max-width: 800px) {
  .traffic-gis-overview__detail {
    right: 14px;
  }
  .traffic-gis-overview__business-links {
    right: 14px;
  }
  .traffic-gis-overview nav {
    top: 58px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .traffic-gis-overview * {
    animation: none !important;
    transition: none !important;
  }
}
</style>
