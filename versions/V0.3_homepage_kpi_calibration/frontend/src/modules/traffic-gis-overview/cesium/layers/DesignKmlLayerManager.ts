import * as Cesium from "cesium";
import type {
  DesignKmlLayerDefinition,
  DesignLayerGroup,
  DesignLayerManifest,
} from "../../types/design-layers";
import type { TrafficMapFeature } from "../../types";
import { SpxPrimitiveLayer } from "./SpxPrimitiveLayer";

type LayerEntry = {
  definition: DesignKmlLayerDefinition;
  group: DesignLayerGroup;
  dataSource: Cesium.KmlDataSource;
};

type EntityColorSnapshot = {
  billboard?: Cesium.Color;
  point?: Cesium.Color;
  pointOutline?: Cesium.Color;
  labelFill?: Cesium.Color;
  labelOutline?: Cesium.Color;
  labelBackground?: Cesium.Color;
  polyline?: Cesium.Color;
  polygon?: Cesium.Color;
  polygonOutline?: Cesium.Color;
  corridor?: Cesium.Color;
};

type CompactLayerNode = {
  id: string;
  name: string;
  type: "kml" | "group" | "external-placeholder";
  url?: string;
  defaultVisible?: boolean;
  featureCount?: number;
  dataNote?: string;
  dataStatus?: string;
  children?: CompactLayerNode[];
};

type CompactLayerManifest = {
  version: string;
  name: string;
  stylePolicy: string;
  loadingPolicy: string;
  groups: Array<{
    id: string;
    name: string;
    children: CompactLayerNode[];
  }>;
};

export class DesignKmlLayerManager {
  private readonly entries = new Map<string, LayerEntry>();
  private readonly pendingLoads = new Map<
    string,
    Promise<Cesium.KmlDataSource>
  >();
  private readonly loadTokens = new Map<string, number>();
  private readonly originalColors = new WeakMap<Cesium.Entity, EntityColorSnapshot>();
  private spxLayer?: SpxPrimitiveLayer;
  private manifest?: DesignLayerManifest;

  constructor(
    private readonly viewer: Cesium.Viewer,
    private readonly manifestUrl: string,
    private readonly releaseOnHide = true,
  ) {}

  async init(): Promise<DesignLayerManifest> {
    const response = await fetch(this.manifestUrl);
    if (!response.ok) {
      throw new Error(`设计图层配置加载失败（HTTP ${response.status}）`);
    }
    const raw = (await response.json()) as
      | DesignLayerManifest
      | CompactLayerManifest;
    this.manifest = this.normalizeManifest(raw);
    return this.manifest;
  }

  getManifest() {
    if (!this.manifest) throw new Error("设计图层配置尚未初始化");
    return this.manifest;
  }

  private groupOf(layerId: string) {
    return this.getManifest().groups.find((group) =>
      group.layers.some((layer) => layer.id === layerId),
    );
  }

  private definitionOf(layerId: string) {
    const group = this.groupOf(layerId);
    const definition = group?.layers.find((layer) => layer.id === layerId);
    if (!group || !definition) throw new Error(`未知设计图层：${layerId}`);
    if (definition.available === false || !definition.file) {
      throw new Error(`${definition.name}暂无可加载数据`);
    }
    return { group, definition };
  }

  private normalizeManifest(
    raw: DesignLayerManifest | CompactLayerManifest,
  ): DesignLayerManifest {
    const firstGroup = raw.groups[0];
    if (firstGroup && "layers" in firstGroup) {
      return raw as DesignLayerManifest;
    }

    const compact = raw as CompactLayerManifest;
    const groups: DesignLayerGroup[] = [];
    let order = 1;
    for (const root of compact.groups) {
      for (const node of root.children) {
        const nodes = node.type === "group" ? node.children || [] : [node];
        groups.push({
          id: node.type === "kml" ? `${node.id}_group` : node.id,
          name:
            node.type === "kml" && node.id === "road"
              ? "路线总体"
              : node.name,
          order: order++,
          layers: nodes.map((layer) =>
            this.normalizeCompactLayer(layer, compact.stylePolicy),
          ),
        });
      }
    }

    return {
      project: compact.name,
      sourceFile: "S1-6_ESG首页关键要素精简版.kml",
      coordinateSystemLabel: "CGCS2000 / KML 经纬度",
      recommendedLoader: "Cesium.KmlDataSource",
      stylePolicy: compact.stylePolicy,
      selectionPolicy: compact.loadingPolicy,
      groups,
    };
  }

  private normalizeCompactLayer(
    layer: CompactLayerNode,
    stylePolicy: string,
  ): DesignKmlLayerDefinition {
    const available = layer.type === "kml" && Boolean(layer.url);
    return {
      id: layer.id,
      name: layer.name,
      file: layer.url || "",
      format: "kml",
      defaultVisible: available && layer.defaultVisible === true,
      loadMode: "onDemand",
      clampToGround: true,
      featureCount: layer.featureCount || 0,
      coordinateCount: 0,
      sourceLayers: [],
      stylePolicy,
      note:
        layer.dataNote ||
        (available ? undefined : "当前设计资料未包含该专题数据"),
      available,
      dataStatus: layer.dataStatus,
    };
  }

  private nextToken(layerId: string) {
    const token = (this.loadTokens.get(layerId) || 0) + 1;
    this.loadTokens.set(layerId, token);
    return token;
  }

  async setVisible(layerId: string, visible: boolean, opacity = 1) {
    if (layerId === "slope_spx") {
      const { definition } = this.definitionOf(layerId);
      if (!this.spxLayer) {
        const baseUrl = new URL(
          ".",
          new URL(this.manifestUrl, window.location.href),
        );
        this.spxLayer = new SpxPrimitiveLayer(
          this.viewer,
          new URL(definition.file, baseUrl).href,
        );
      }
      await this.spxLayer.setVisible(visible, opacity);
      return;
    }
    const current = this.entries.get(layerId);
    if (!visible) {
      this.nextToken(layerId);
      if (!current) return;
      if (this.releaseOnHide) {
        this.viewer.dataSources.remove(current.dataSource, true);
        this.entries.delete(layerId);
      } else {
        current.dataSource.show = false;
      }
      this.viewer.scene.requestRender();
      return;
    }

    if (current) {
      current.dataSource.show = true;
      this.applyOpacity(current.dataSource, opacity);
      this.viewer.scene.requestRender();
      return;
    }

    const { group, definition } = this.definitionOf(layerId);
    const token = this.nextToken(layerId);
    const baseUrl = new URL(".", new URL(this.manifestUrl, window.location.href));
    let pending = this.pendingLoads.get(layerId);
    if (!pending) {
      pending = Cesium.KmlDataSource.load(
        new URL(definition.file, baseUrl).href,
        {
          camera: this.viewer.scene.camera,
          canvas: this.viewer.scene.canvas,
          clampToGround: definition.clampToGround !== false,
        },
      );
      this.pendingLoads.set(layerId, pending);
    }

    let dataSource: Cesium.KmlDataSource;
    try {
      dataSource = await pending;
    } finally {
      if (this.pendingLoads.get(layerId) === pending) {
        this.pendingLoads.delete(layerId);
      }
    }

    if (this.loadTokens.get(layerId) !== token) return;

    dataSource.name = definition.name;
    this.decorateEntities(dataSource, group, definition);
    this.applyDistanceLimit(dataSource, definition.maxCameraHeight);
    this.captureOriginalColors(dataSource);
    this.applyOpacity(dataSource, opacity);
    await this.viewer.dataSources.add(dataSource);
    this.entries.set(layerId, { definition, group, dataSource });
    this.viewer.scene.requestRender();
  }

  async locate(layerId: string) {
    if (layerId === "slope_spx") {
      await this.spxLayer?.locate();
      return;
    }
    const entry = this.entries.get(layerId);
    if (!entry) throw new Error("请先勾选并加载该图层");
    await this.viewer.flyTo(entry.dataSource, {
      duration: 0.8,
      maximumHeight: entry.definition.maxCameraHeight,
    });
  }

  hasLoadedLayers() {
    return this.entries.size > 0;
  }

  /**
   * 首页和“回到项目全景”优先以路线中心线确定 S1-6 的完整范围。
   * 中心线未启用时，退化为当前全部可见设计图层的联合范围。
   */
  async locateOverview(preferredLayerId = "route_center") {
    const preferred =
      this.entries.get(preferredLayerId) ||
      this.entries.get("road_ecology_base") ||
      this.entries.get("road");
    if (preferred) {
      const bounds = preferred.definition.overviewRectangle;
      if (bounds) {
        const rectangle = Cesium.Rectangle.fromDegrees(...bounds);
        const sphere = Cesium.BoundingSphere.fromRectangle3D(
          rectangle,
          Cesium.Ellipsoid.WGS84,
          0,
        );
        await this.viewer.camera.flyToBoundingSphere(sphere, {
          duration: 0.8,
          offset: new Cesium.HeadingPitchRange(
            0,
            Cesium.Math.toRadians(-55),
            sphere.radius * 2.6,
          ),
        });
        return;
      }
      const centerlineEntities = preferred.dataSource.entities.values.filter(
        (entity) => this.isCenterlineEntity(entity),
      );
      await this.viewer.flyTo(
        centerlineEntities.length ? centerlineEntities : preferred.dataSource,
        { duration: 0.8 },
      );
      return;
    }
    const entities = [...this.entries.values()].flatMap(
      (entry) => entry.dataSource.entities.values,
    );
    if (!entities.length) throw new Error("当前没有可定位的设计图层");
    await this.viewer.flyTo(entities, { duration: 0.8 });
  }

  setOpacity(layerId: string, opacity: number) {
    if (layerId === "slope_spx") {
      this.spxLayer?.setOpacity(opacity);
      return;
    }
    const entry = this.entries.get(layerId);
    if (!entry) return;
    this.applyOpacity(entry.dataSource, opacity);
    this.viewer.scene.requestRender();
  }

  async setTerrain(enabled: boolean, terrainUrl: string) {
    if (!enabled) {
      this.viewer.terrainProvider = new Cesium.EllipsoidTerrainProvider();
      this.viewer.scene.globe.depthTestAgainstTerrain = false;
      this.viewer.scene.requestRender();
      return;
    }
    const provider = await Cesium.CesiumTerrainProvider.fromUrl(terrainUrl, {
      requestVertexNormals: true,
      requestWaterMask: true,
    });
    this.viewer.terrainProvider = provider;
    this.viewer.scene.globe.depthTestAgainstTerrain = true;
    this.viewer.scene.requestRender();
  }

  destroy() {
    this.loadTokens.forEach((_, id) => this.nextToken(id));
    for (const entry of this.entries.values()) {
      this.viewer.dataSources.remove(entry.dataSource, true);
    }
    this.entries.clear();
    this.spxLayer?.destroy();
    this.spxLayer = undefined;
  }

  private applyDistanceLimit(
    dataSource: Cesium.KmlDataSource,
    maxDistance?: number,
  ) {
    if (!maxDistance) return;
    const limit = new Cesium.DistanceDisplayCondition(0, maxDistance);
    for (const entity of dataSource.entities.values) {
      if (entity.label)
        entity.label.distanceDisplayCondition = new Cesium.ConstantProperty(limit);
      if (entity.billboard)
        entity.billboard.distanceDisplayCondition = new Cesium.ConstantProperty(limit);
      if (entity.point)
        entity.point.distanceDisplayCondition = new Cesium.ConstantProperty(limit);
    }
  }

  private decorateEntities(
    dataSource: Cesium.KmlDataSource,
    group: DesignLayerGroup,
    layer: DesignKmlLayerDefinition,
  ) {
    const pileAreaLabels = new Map<Cesium.Entity, string>();
    if (layer.id === "road_ecology_base") {
      const pileAreas = dataSource.entities.values
        .filter((entity) => /^堆渣线_\d+$/.test(entity.name?.trim() ?? ""))
        .sort((left, right) => {
          const leftId = Number(left.name?.split("_").at(-1) ?? 0);
          const rightId = Number(right.name?.split("_").at(-1) ?? 0);
          return leftId - rightId;
        });
      pileAreas.forEach((entity, index) => {
        pileAreaLabels.set(entity, `堆渣区${index + 1}`);
      });
    }

    dataSource.entities.values.forEach((entity, index) => {
      const pileAreaLabel = pileAreaLabels.get(entity);
      const sourceName = entity.name?.trim();
      if (pileAreaLabel) {
        if (!entity.properties) entity.properties = new Cesium.PropertyBag();
        if (!entity.properties.hasProperty("sourceFeatureName")) {
          entity.properties.addProperty("sourceFeatureName");
        }
        entity.properties.sourceFeatureName = new Cesium.ConstantProperty(
          sourceName,
        );
        entity.name = pileAreaLabel;
      }
      const feature = this.toTrafficFeature(entity, group, layer, index);
      if (!entity.properties) entity.properties = new Cesium.PropertyBag();
      if (!entity.properties.hasProperty("trafficFeature")) {
        entity.properties.addProperty("trafficFeature");
      }
      entity.properties.trafficFeature = new Cesium.ConstantProperty(feature);
      entity.name ||= `${layer.name} ${index + 1}`;
    });
    if (layer.id === "road_ecology_base") {
      this.hideSpoilSiteFeatures(dataSource);
      this.addPileAreaLabels(dataSource, pileAreaLabels);
      this.addKeyFeatureLabels(dataSource);
    }
  }

  private entityContextNames(entity: Cesium.Entity) {
    const names: string[] = [];
    let current: Cesium.Entity | undefined = entity;
    while (current) {
      if (current.name) names.push(current.name.trim());
      current = current.parent;
    }
    return names;
  }

  private isCenterlineEntity(entity: Cesium.Entity) {
    return this.entityContextNames(entity).some(
      (name) => name === "中心线" || name.startsWith("中心线_"),
    );
  }

  private isKeyLabelEntity(entity: Cesium.Entity) {
    return this.entityContextNames(entity).some(
      (name) =>
        name.includes("基本农田") ||
        name.includes("保护区") ||
        name.includes("生态保护"),
    );
  }

  private keyLabelText(entity: Cesium.Entity) {
    const name = entity.name?.trim() || "生态保护要素";
    if (name.includes("基本农田")) return name.split("_")[0];
    if (name.includes("保护区") || name.includes("生态保护"))
      return name.split("_")[0];
    return name;
  }

  private hideSpoilSiteFeatures(dataSource: Cesium.KmlDataSource) {
    for (const entity of dataSource.entities.values) {
      const isSpoilSite = this.entityContextNames(entity).some(
        (name) =>
          name.includes("取弃土场") ||
          name.includes("弃渣场") ||
          name === "0土场编号" ||
          /^q\d+$/i.test(name),
      );
      if (isSpoilSite) entity.show = false;
    }
  }

  private labelPosition(
    entity: Cesium.Entity,
    allEntities: Cesium.Entity[] = [entity],
  ) {
    const time = Cesium.JulianDate.now();
    const points: Cesium.Cartesian3[] = [];
    const visited = new Set<Cesium.Entity>();
    const pending = [entity];
    while (pending.length) {
      const current = pending.pop();
      if (!current || visited.has(current)) continue;
      visited.add(current);
      const point = current.position?.getValue(time);
      if (point) points.push(point);
      const positions = current.polyline?.positions?.getValue(time);
      if (positions?.length) points.push(...positions);
      const hierarchy = current.polygon?.hierarchy?.getValue(time);
      if (hierarchy?.positions?.length) points.push(...hierarchy.positions);
      allEntities.forEach((candidate) => {
        if (candidate.parent === current) pending.push(candidate);
      });
    }
    if (points.length) {
      return Cesium.BoundingSphere.fromPoints(points).center;
    }
    return undefined;
  }

  private addPileAreaLabels(
    dataSource: Cesium.KmlDataSource,
    labels: Map<Cesium.Entity, string>,
  ) {
    for (const [entity, text] of labels) {
      const position = this.labelPosition(entity, dataSource.entities.values);
      if (!position) continue;
      entity.position = new Cesium.ConstantPositionProperty(position);
      entity.label = new Cesium.LabelGraphics({
        text,
        font: "600 15px Microsoft YaHei",
        fillColor: Cesium.Color.fromCssColorString("#fff3b0"),
        outlineColor: Cesium.Color.fromCssColorString("#3a2600"),
        outlineWidth: 3,
        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
        showBackground: true,
        backgroundColor: Cesium.Color.fromCssColorString("#3a2b05").withAlpha(
          0.76,
        ),
        backgroundPadding: new Cesium.Cartesian2(9, 5),
        pixelOffset: new Cesium.Cartesian2(0, -14),
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
        distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 100000),
      });
    }
  }

  private addKeyFeatureLabels(dataSource: Cesium.KmlDataSource) {
    for (const entity of dataSource.entities.values) {
      if (!this.isKeyLabelEntity(entity)) continue;
      const position = this.labelPosition(entity);
      if (!position) continue;
      if (!entity.position) {
        entity.position = new Cesium.ConstantPositionProperty(position);
      }
      if (entity.label) continue;
      entity.label = new Cesium.LabelGraphics({
        text: this.keyLabelText(entity),
        font: "600 14px Microsoft YaHei",
        fillColor: Cesium.Color.fromCssColorString("#e7fff2"),
        outlineColor: Cesium.Color.fromCssColorString("#052c28"),
        outlineWidth: 3,
        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
        showBackground: true,
        backgroundColor: Cesium.Color.fromCssColorString("#04362f").withAlpha(
          0.78,
        ),
        backgroundPadding: new Cesium.Cartesian2(8, 5),
        pixelOffset: new Cesium.Cartesian2(0, -12),
        disableDepthTestDistance: Number.POSITIVE_INFINITY,
        distanceDisplayCondition: new Cesium.DistanceDisplayCondition(0, 50000),
      });
    }
  }

  private toTrafficFeature(
    entity: Cesium.Entity,
    group: DesignLayerGroup,
    layer: DesignKmlLayerDefinition,
    index: number,
  ): TrafficMapFeature {
    const name = entity.name?.trim() || `${layer.name} ${index + 1}`;
    const objectType = this.objectTypeOf(layer.id);
    return {
      id: `design:${layer.id}:${entity.id}`,
      layerId: `design:${layer.id}`,
      objectType,
      name,
      geometry: {
        type: "Point",
        coordinates: this.entityLngLat(entity),
      },
      properties: {
        一级分类: group.name,
        所属图层: layer.name,
        原CAD图层: layer.sourceLayers.join("、"),
        图层说明: layer.note || "—",
        坐标系: this.getManifest().coordinateSystemLabel,
      },
      status: "normal",
      statusLabel: "设计对象",
      businessSummary: {
        title: "工程对象综合信息",
        dashboardRows: [
          { label: "工程类型", value: layer.name },
          { label: "所属分类", value: group.name },
          { label: "施工进度", value: "待业务数据关联" },
          { label: "碳排放", value: "待业务数据关联" },
          { label: "安全风险", value: "待业务数据关联" },
          { label: "环保监测", value: "待业务数据关联" },
          { label: "闭环整改", value: "待业务数据关联" },
        ],
        dashboardNote:
          "该对象来自 S1-6 公路设计图。后续可通过对象编码、标段和桩号关联工程进度、碳排放、安全、环保及闭环数据。",
        targetModule: "project-map",
      },
      relationSummary: {
        total: 0,
        pendingCount: 0,
        highRiskCount: 0,
        byType: [],
      },
    };
  }

  private objectTypeOf(layerId: string) {
    if (layerId === "road") return "road-section";
    if (layerId === "bridge") return "bridge";
    if (layerId === "tunnel") return "tunnel";
    if (layerId.includes("culvert")) return "culvert";
    if (layerId.includes("slope")) return "slope";
    if (layerId.startsWith("spoil_")) return "spoil-site";
    if (layerId.includes("drain") || layerId.includes("ditch"))
      return "drainage";
    if (layerId === "farmland") return "farmland";
    if (layerId === "sound_barrier") return "sound-barrier";
    if (layerId.startsWith("route_")) return "road-section";
    return "design-object";
  }

  private entityLngLat(entity: Cesium.Entity): number[] {
    const time = Cesium.JulianDate.now();
    let cartesian = entity.position?.getValue(time);
    if (!cartesian) {
      cartesian = entity.polyline?.positions?.getValue(time)?.[0];
    }
    if (!cartesian) {
      const hierarchy = entity.polygon?.hierarchy?.getValue(time);
      cartesian = hierarchy?.positions?.[0];
    }
    if (!cartesian) return [0, 0];
    const point = Cesium.Cartographic.fromCartesian(cartesian);
    return [
      Cesium.Math.toDegrees(point.longitude),
      Cesium.Math.toDegrees(point.latitude),
      point.height,
    ];
  }

  private captureOriginalColors(dataSource: Cesium.KmlDataSource) {
    const time = Cesium.JulianDate.now();
    for (const entity of dataSource.entities.values) {
      const snapshot: EntityColorSnapshot = {
        billboard: entity.billboard?.color?.getValue(time)?.clone(),
        point: entity.point?.color?.getValue(time)?.clone(),
        pointOutline: entity.point?.outlineColor?.getValue(time)?.clone(),
        labelFill: entity.label?.fillColor?.getValue(time)?.clone(),
        labelOutline: entity.label?.outlineColor?.getValue(time)?.clone(),
        labelBackground: entity.label?.backgroundColor?.getValue(time)?.clone(),
        polyline: this.materialColor(entity.polyline?.material, time),
        polygon: this.materialColor(entity.polygon?.material, time),
        polygonOutline: entity.polygon?.outlineColor?.getValue(time)?.clone(),
        corridor: this.materialColor(entity.corridor?.material, time),
      };
      this.originalColors.set(entity, snapshot);
    }
  }

  private materialColor(
    material: Cesium.MaterialProperty | undefined,
    time: Cesium.JulianDate,
  ) {
    if (material instanceof Cesium.ColorMaterialProperty) {
      return material.color?.getValue(time)?.clone();
    }
    return undefined;
  }

  private alpha(color: Cesium.Color | undefined, opacity: number) {
    if (!color) return undefined;
    return color.withAlpha(color.alpha * Math.max(0, Math.min(1, opacity)));
  }

  private applyOpacity(dataSource: Cesium.KmlDataSource, opacity: number) {
    for (const entity of dataSource.entities.values) {
      const original = this.originalColors.get(entity);
      if (!original) continue;
      const billboard = this.alpha(original.billboard, opacity);
      const point = this.alpha(original.point, opacity);
      const pointOutline = this.alpha(original.pointOutline, opacity);
      const labelFill = this.alpha(original.labelFill, opacity);
      const labelOutline = this.alpha(original.labelOutline, opacity);
      const labelBackground = this.alpha(original.labelBackground, opacity);
      const polyline = this.alpha(original.polyline, opacity);
      const polygon = this.alpha(original.polygon, opacity);
      const polygonOutline = this.alpha(original.polygonOutline, opacity);
      const corridor = this.alpha(original.corridor, opacity);
      if (billboard && entity.billboard)
        entity.billboard.color = new Cesium.ConstantProperty(billboard);
      if (point && entity.point)
        entity.point.color = new Cesium.ConstantProperty(point);
      if (pointOutline && entity.point)
        entity.point.outlineColor = new Cesium.ConstantProperty(pointOutline);
      if (labelFill && entity.label)
        entity.label.fillColor = new Cesium.ConstantProperty(labelFill);
      if (labelOutline && entity.label)
        entity.label.outlineColor = new Cesium.ConstantProperty(labelOutline);
      if (labelBackground && entity.label)
        entity.label.backgroundColor = new Cesium.ConstantProperty(labelBackground);
      if (polyline && entity.polyline)
        entity.polyline.material = new Cesium.ColorMaterialProperty(polyline);
      if (polygon && entity.polygon)
        entity.polygon.material = new Cesium.ColorMaterialProperty(polygon);
      if (polygonOutline && entity.polygon)
        entity.polygon.outlineColor = new Cesium.ConstantProperty(polygonOutline);
      if (corridor && entity.corridor)
        entity.corridor.material = new Cesium.ColorMaterialProperty(corridor);
    }
  }
}
