import type {
  TrafficDataAdapter,
  TrafficGeometry,
  TrafficLayerDefinition,
  TrafficMapContext,
  TrafficMapFeature,
} from "../types";
import{buildChainage,lineLength}from'../domain/chainage';

type GeoJsonFeature = {
  id?: string | number;
  properties?: Record<string, unknown>;
  geometry: TrafficGeometry;
};
type Manifest = { crs: string; layers: TrafficLayerDefinition[] };

const monitorProfiles: Record<string, Record<string, unknown>> = {
  边坡监测点1: {
    监测点编号: "BP-JC-001",
    所属标段: "1标段",
    设备状态: "在线",
    地表水平位移: "3.2 mm",
    垂直沉降: "1.6 mm",
    深部位移: "2.4 mm",
    裂缝宽度: "0.4 mm",
    "24小时降雨量": "12.6 mm",
    地下水位埋深: "4.8 m",
    数据更新时间: "2026-07-16 10:30",
    预警状态: "正常",
    资料说明: "演示监测数据，待传感器接口替换",
  },
  边坡监测点2: {
    监测点编号: "BP-JC-002",
    所属标段: "2标段",
    设备状态: "在线",
    地表水平位移: "5.8 mm",
    垂直沉降: "2.1 mm",
    深部位移: "3.6 mm",
    裂缝宽度: "0.7 mm",
    "24小时降雨量": "12.6 mm",
    地下水位埋深: "5.3 m",
    数据更新时间: "2026-07-16 10:32",
    预警状态: "关注",
    资料说明: "演示监测数据，待传感器接口替换",
  },
};

const environmentalProfiles: Record<string, Record<string, unknown>> = {
  水源保护区1: {
    保护区编号: "SY-BH-001",
    所属标段: "1标段",
    保护对象: "沿线村镇集中式饮用水水源",
    保护级别: "二级保护区",
    水体类型: "地表水",
    当前水质: "Ⅲ类",
    主要管控要求: "禁止施工废水直排，设置截排水沟及沉淀设施",
    最近巡查: "2026-07-15",
    巡查状态: "正常",
    责任单位: "施工一标项目部环保组",
    资料说明: "演示保护区资料，待正式环评及监测数据替换",
  },
  水源保护区2: {
    保护区编号: "SY-BH-002",
    所属标段: "2标段",
    保护对象: "河流型饮用水水源补给区",
    保护级别: "准保护区",
    水体类型: "河流",
    当前水质: "Ⅲ类",
    主要管控要求: "加强桥面径流收集，危险品运输路段设置应急设施",
    最近巡查: "2026-07-14",
    巡查状态: "正常",
    责任单位: "施工二标项目部环保组",
    资料说明: "演示保护区资料，待正式环评及监测数据替换",
  },
  生态保护区1: {
    保护区编号: "ST-BH-001",
    所属标段: "1标段",
    保护类型: "沿线林地与自然植被保护区",
    主要生态要素: "常绿阔叶林、灌草地及野生动物通道",
    敏感等级: "较高",
    当前扰动情况: "施工边界内局部扰动",
    主要管控要求: "严控施工红线，表土剥离保存，完工后及时复绿",
    植被恢复率: "86%",
    最近巡查: "2026-07-15",
    巡查状态: "正常",
    责任单位: "施工一标项目部环保组",
    资料说明: "演示生态资料，待正式生态调查数据替换",
  },
};

export class ShpTrafficAdapter implements TrafficDataAdapter {
  private manifest?: Promise<Manifest>;
  constructor(private readonly manifestUrl = "/data/shp/manifest.json") {}
  private loadManifest() {
    return (this.manifest ??= fetch(this.manifestUrl).then(async (response) => {
      if (!response.ok)
        throw new Error(`SHP 图层清单加载失败 ${response.status}`);
      const manifest = (await response.json()) as Manifest;
      if (manifest.crs !== "EPSG:4326")
        throw new Error(`不支持的 SHP 坐标系：${manifest.crs}`);
      return manifest;
    }));
  }
  async getLayers(context: TrafficMapContext) {
    const { layers } = await this.loadManifest();
    const all=[...layers,{id:'chainage-marks',name:'路线桩号',geometryType:'point',enabled:true,objectType:'chainage',featureCount:0,source:{type:'geojson'},style:{color:'#f8f4d8',width:6,showLabel:true,labelColor:'#eafaff',labelSize:11}}as TrafficLayerDefinition];return all.filter(
      (layer) =>
        !context.visibleLayerIds || context.visibleLayerIds.includes(layer.id),
    );
  }
  async getFeatures(layer: TrafficLayerDefinition, context: TrafficMapContext) {
    if(layer.id==='chainage-marks'){const{layers}=await this.loadManifest();const roads=layers.filter(item=>item.objectType==='road-section');const routeData=await Promise.all(['3标段','2标段','1标段'].map(async name=>{const road=roads.find(item=>item.name===name)!;const response=await fetch(road.source.url!);const collection=await response.json()as{features:GeoJsonFeature[]};let coordinates=(collection.features[0].geometry as{type:'LineString';coordinates:number[][]}).coordinates;if(name==='3标段'){const west=coordinates.reduce((best,current,index)=>current[0]<coordinates[best][0]?index:best,0);coordinates=coordinates.slice(0,west+1)}return{sectionId:name,coordinates,reverse:name==='3标段'}}));const marks=buildChainage(routeData,5000);return context.sectionId?marks.filter(mark=>mark.properties.sectionId===context.sectionId):marks}
    if (!layer.source.url) return [];
    const response = await fetch(layer.source.url);
    if (!response.ok)
      throw new Error(`${layer.name} GeoJSON 加载失败 ${response.status}`);
    const collection = (await response.json()) as {
      features: GeoJsonFeature[];
    };
    const labelField = layer.style.labelField;
    const suffix = layer.name.match(/([123])$/)?.[1];
    const sectionId =
      layer.objectType === "road-section"
        ? layer.name
        : suffix
          ? `${suffix}标段`
          : undefined;
    const profiles:Record<string,Record<string,unknown>>={'1标段':{施工单位:'广西路桥工程集团第一项目部',监理单位:'广西交通工程监理咨询公司',建设进度:'72%',环保问题:'1项',风险点:'1处',计划完工:'2027年06月'},'2标段':{施工单位:'广西路建工程集团第二项目部',监理单位:'北京华通公路桥梁监理公司',建设进度:'58%',环保问题:'3项',风险点:'1处',计划完工:'2027年10月'},'3标段':{施工单位:'中交第四公路工程局项目部',监理单位:'广西桂通工程管理集团',建设进度:'46%',环保问题:'2项',风险点:'2处',计划完工:'2028年03月'}};const features = collection.features.map(
      (item, index): TrafficMapFeature => ({
        id: String(item.id ?? `${layer.id}-${index + 1}`),
        layerId: layer.id,
        objectType: layer.objectType || "shp-layer",
        name: String(
          (labelField && item.properties?.[labelField]) || layer.name,
        ),
        geometry: item.geometry,
        properties: {
          ...(item.properties || {}),
          sourceLayer: layer.name,
          sectionId,
          ...(layer.objectType === "slope-monitor"
            ? monitorProfiles[layer.name] || {
                设备状态: "在线",
                预警状态: "正常",
                资料说明: "演示监测数据，待传感器接口替换",
              }
            : {}),
          ...(["water-source", "ecological-zone"].includes(
            layer.objectType || "",
          )
            ? environmentalProfiles[layer.name] || {
                巡查状态: "正常",
                资料说明: "演示保护区资料，待正式调查数据替换",
              }
            : {}),
          ...(layer.objectType==='road-section'?{...profiles[layer.name],线路长度:`${(lineLength((item.geometry as{type:'LineString';coordinates:number[][]}).coordinates)/1000).toFixed(2)} km`,资料说明:'演示补充，待正式资料替换'}:{}),
        },
        status:
          layer.objectType === "slope-monitor"
            ? layer.name.endsWith("2")
              ? "attention"
              : "normal"
            : undefined,
      }),
    );
    return context.sectionId
      ? features.filter(
          (feature) => feature.properties.sectionId === context.sectionId,
        )
      : features;
  }
}
