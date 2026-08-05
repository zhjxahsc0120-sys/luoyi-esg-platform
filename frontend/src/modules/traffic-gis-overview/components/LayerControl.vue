<script setup lang="ts">
import { computed, ref } from 'vue'
import { basemapDefinitions, type BasemapId } from '../config/basemaps.config'
import type { TrafficLayerDefinition, TrafficLayerStyle } from '../types'
import type { VectorLayerRecord } from '../vector/VectorLayerStore'
import type { SpatialAssetRecord, SpatialAssetType } from '../assets/SpatialAssetStore'

const props = defineProps<{ open: boolean; activeBasemap: BasemapId; layers: TrafficLayerDefinition[]; visibleIds: string[]; vectorLayers: VectorLayerRecord[]; assets: SpatialAssetRecord[]; loading: boolean }>()
const emit = defineEmits<{ close: []; basemapChange: [BasemapId]; layerToggle: [string, boolean]; layerStyle: [string, Partial<TrafficLayerStyle>]; vectorUpload: [File]; vectorToggle: [string, boolean]; vectorRemove: [string]; vectorLocate: [string]; vectorStyle: [string, Partial<TrafficLayerStyle>]; assetAdd: [{ name: string; type: SpatialAssetType; url: string }]; assetToggle: [string, boolean]; assetRemove: [string]; assetLocate: [string]; refresh: [] }>()

type Tab = 'basemap' | 'base' | 'assets' | 'business'
const tab = ref<Tab>('business')
const assetName = ref('')
const assetUrl = ref('')
const assetType = ref<SpatialAssetType>('imagery')
const configuredBaseLayers = computed(() => props.layers.filter(layer => Boolean(layer.source.url)))
const businessLayers = computed(() => props.layers.filter(layer => layer.source.type === 'api' && !layer.source.url))
const businessFeatureCount = computed(() => businessLayers.value.reduce((sum, layer) => sum + (layer.featureCount || 0), 0))
const titles: Record<Tab, [string, string]> = {
  basemap: ['基础地图', '选择卫星、街道等默认背景地图'],
  base: ['基础空间数据', '配置路线、断面、标段范围和重要面文件，这类数据不参与日常业务导入'],
  assets: ['三维与影像资源', '配置影像、地形、倾斜摄影与点云服务'],
  business: ['ESG业务数据', '自动读取数据库中的异常、超标、逾期、风险和整改数据；此处只控制显示效果'],
}

function upload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) emit('vectorUpload', file)
  input.value = ''
}
function addAsset() {
  if (!assetName.value.trim() || !assetUrl.value.trim()) return
  emit('assetAdd', { name: assetName.value.trim(), type: assetType.value, url: assetUrl.value.trim() })
  assetName.value = ''
  assetUrl.value = ''
}
</script>

<template>
  <aside v-if="open" class="admin">
    <header><div><b>地图数据与资源设置</b><small>基础空间数据与ESG业务数据分开管理</small></div><button @click="$emit('close')">← 返回地图</button></header>
    <div class="workspace">
      <nav>
        <button v-for="item in ([['basemap','01','基础地图','背景底图'],['base','02','基础空间数据','断面、路线、重要面'],['assets','03','三维与影像','影像、地形、三维'],['business','04','ESG业务数据','数据库自动读取']] as const)" :key="item[0]" :class="{active:tab===item[0]}" @click="tab=item[0]"><i>{{item[1]}}</i><span>{{item[2]}}<small>{{item[3]}}</small></span></button>
      </nav>
      <main>
        <div class="page-title"><div><h2>{{titles[tab][0]}}</h2><p>{{titles[tab][1]}}</p></div><label v-if="tab==='base'" class="primary">上传 GeoJSON<input type="file" accept=".geojson,.json" @change="upload"></label><button v-if="tab==='business'" class="primary" :disabled="loading" @click="$emit('refresh')">刷新数据库数据</button></div>

        <section v-if="tab==='basemap'" class="basemap-grid">
          <label v-for="item in basemapDefinitions" :key="item.id" class="basemap-card" :class="{selected:activeBasemap===item.id}"><input type="radio" name="basemap" :checked="activeBasemap===item.id" @change="$emit('basemapChange',item.id)"><div class="preview" :class="`preview--${item.id}`"><span>{{activeBasemap===item.id?'当前使用':'选择底图'}}</span></div><div class="card-body"><b>{{item.name}}</b><small>{{item.description}}</small></div></label>
        </section>

        <section v-else-if="tab==='base'">
          <div class="notice"><b>基础数据入口</b><span>适合项目路线、断面图、标段边界、施工区和其他重要面。上传后可控制显隐、定位和样式。</span></div>
          <h3>系统基础图层（{{configuredBaseLayers.length}}）</h3>
          <article v-for="layer in configuredBaseLayers" :key="layer.id" class="config-card"><div class="card-head"><label class="switch-row"><input type="checkbox" :checked="visibleIds.includes(layer.id)" @change="$emit('layerToggle',layer.id,($event.target as HTMLInputElement).checked)"><i :style="{background:layer.style.color}"></i><span><b>{{layer.name}}</b><small>{{layer.featureCount||0}}个要素 · {{layer.geometryType}}</small></span></label></div><LayerStyle :layer="layer" @style="value=>$emit('layerStyle',layer.id,value)" /></article>
          <h3>本地上传文件（{{vectorLayers.length}}）</h3>
          <div v-if="!vectorLayers.length" class="empty">尚未上传基础空间文件</div>
          <article v-for="item in vectorLayers" :key="item.id" class="config-card"><div class="card-head"><label class="switch-row"><input type="checkbox" :checked="item.visible" @change="$emit('vectorToggle',item.id,($event.target as HTMLInputElement).checked)"><i :style="{background:item.definition.style.color}"></i><span><b>{{item.name}}</b><small>{{item.features.length}}个要素 · {{item.definition.geometryType}}</small></span></label><div><button @click="$emit('vectorLocate',item.id)">定位</button><button class="danger" @click="$emit('vectorRemove',item.id)">删除</button></div></div></article>
        </section>

        <section v-else-if="tab==='assets'">
          <article class="form-card"><h3>新增空间资源</h3><div class="asset-form"><label>资源名称<input v-model="assetName" placeholder="例如：项目倾斜摄影"></label><label>资源类型<select v-model="assetType"><option value="imagery">影像切片 XYZ</option><option value="terrain">Cesium 地形</option><option value="tileset">倾斜摄影 / 3D Tiles</option><option value="pointcloud">点云 3D Tiles</option></select></label><label class="wide">资源地址<input v-model="assetUrl" placeholder="http://.../tileset.json"></label><button class="primary wide" @click="addAsset">添加资源</button></div></article>
          <article v-for="asset in assets" :key="asset.id" class="config-card"><div class="card-head"><label class="switch-row"><input type="checkbox" :checked="asset.visible" @change="$emit('assetToggle',asset.id,($event.target as HTMLInputElement).checked)"><i></i><span><b>{{asset.name}}</b><small>{{asset.type}} · {{asset.url}}</small></span></label><div><button @click="$emit('assetLocate',asset.id)">定位</button><button class="danger" @click="$emit('assetRemove',asset.id)">删除</button></div></div></article>
        </section>

        <section v-else>
          <div class="notice business-note"><b>数据库只读联动</b><span>业务内容由“数据智能上传”确认入库后自动出现。地图按类型和状态渲染，点击点位可查看完整业务详情。</span><div class="legend"><i class="normal"></i>正常 <i class="attention"></i>关注 <i class="warning"></i>预警/待复测 <i class="critical"></i>超标/逾期</div></div>
          <div class="summary"><span><b>{{businessLayers.length}}</b>类业务图层</span><span><b>{{businessFeatureCount}}</b>条空间数据</span><span><b>{{businessLayers.filter(l=>visibleIds.includes(l.id)).length}}</b>类正在显示</span></div>
          <div v-if="!businessLayers.length" class="empty">数据库暂无可显示的业务点位，请先在“数据智能上传”中确认入库</div>
          <article v-for="layer in businessLayers" :key="layer.id" class="config-card"><div class="card-head"><label class="switch-row"><input type="checkbox" :checked="visibleIds.includes(layer.id)" @change="$emit('layerToggle',layer.id,($event.target as HTMLInputElement).checked)"><i :style="{background:layer.style.color}"></i><span><b>{{layer.name}}</b><small>{{layer.featureCount||0}}条 · {{layer.geometryType}} · 点击地图要素查看详情</small></span></label></div><LayerStyle :layer="layer" @style="value=>$emit('layerStyle',layer.id,value)" /></article>
        </section>
      </main>
    </div>
    <footer><span></span>{{loading?'正在读取数据库…':'设置已保存；业务数据由数据库实时提供'}}</footer>
  </aside>
</template>

<script lang="ts">
import { defineComponent, h, type PropType } from 'vue'
const LayerStyle = defineComponent({
  props: { layer: { type: Object as PropType<TrafficLayerDefinition>, required: true } },
  emits: ['style'],
  setup(props, { emit }) { return () => h('div', { class: 'form-grid' }, [
    h('label', ['主色', h('input', { type: 'color', value: props.layer.style.color, onInput: (e: Event) => emit('style', { color: (e.target as HTMLInputElement).value }) })]),
    h('label', [props.layer.geometryType === 'point' ? '点位大小' : '线宽', h('input', { type: 'number', min: 1, max: 30, value: props.layer.style.width || 4, onChange: (e: Event) => emit('style', { width: Number((e.target as HTMLInputElement).value) }) })]),
    h('label', { class: 'checkbox' }, [h('input', { type: 'checkbox', checked: props.layer.style.showLabel !== false, onChange: (e: Event) => emit('style', { showLabel: (e.target as HTMLInputElement).checked }) }), '显示标签']),
  ]) }
})
</script>

<style scoped>
.admin{position:absolute;inset:0;z-index:30;display:grid;grid-template-rows:68px 1fr 38px;background:#f3f6f8;color:#263d4c;font-family:"Microsoft YaHei",sans-serif}.admin>header{display:flex;align-items:center;justify-content:space-between;padding:0 28px;background:#fff;border-bottom:1px solid #dce5eb}.admin>header b,.admin>header small,.card-body b,.card-body small,.switch-row b,.switch-row small{display:block}.admin>header small,.card-body small,.switch-row small{margin-top:4px;color:#8294a1;font-size:11px}.admin button,.primary{cursor:pointer;border:1px solid #c8d6df;background:#fff;color:#42647a;padding:7px 13px}.workspace{min-height:0;display:grid;grid-template-columns:220px 1fr}.workspace>nav{padding:18px 12px;background:#102a3a}.workspace>nav button{width:100%;display:flex;align-items:center;gap:10px;margin-bottom:7px;padding:12px;border:0;background:transparent;color:#bad0dc;text-align:left}.workspace>nav button.active{background:#1c4558;color:#fff;border-left:3px solid #23c7e8}.workspace>nav i{font-style:normal;font-size:10px;color:#42cde9}.workspace>nav span{flex:1}.workspace>nav small{display:block;margin-top:3px;color:#789bad;font-size:9px}.workspace>main{min-width:0;overflow:auto;padding:24px 30px}.page-title,.card-head{display:flex;align-items:center;justify-content:space-between}.page-title{margin-bottom:20px}.page-title h2{margin:0;font-size:19px}.page-title p{margin:5px 0 0;color:#7d909c;font-size:11px}.primary{background:#0b9fbe!important;border-color:#0b9fbe!important;color:#fff!important}.primary input{display:none}.basemap-grid{display:grid;grid-template-columns:repeat(3,minmax(180px,1fr));gap:16px}.basemap-card,.config-card,.form-card,.notice,.summary{display:block;margin-bottom:12px;padding:16px 18px;background:#fff;border:1px solid #dce5ea}.basemap-card{padding:0;cursor:pointer}.basemap-card.selected{border-color:#12b4d4;box-shadow:0 0 0 2px rgba(18,180,212,.12)}.basemap-card>input{display:none}.preview{height:130px;display:flex;align-items:flex-end;padding:10px;background:linear-gradient(135deg,#a7c5d5,#eef4f7)}.preview--satellite{background:linear-gradient(135deg,#2d543e,#9c8e65)}.preview--dark{background:linear-gradient(135deg,#102b3b,#305264)}.preview span{font-size:10px;color:#fff;background:rgba(0,0,0,.45);padding:4px 7px}.card-body{padding:14px}.switch-row{display:flex;align-items:center;gap:10px}.switch-row>input{display:none}.switch-row>i{width:10px;height:10px;background:#18b8d4;box-shadow:0 0 0 4px #e3f7fa}.switch-row:has(input:not(:checked)){opacity:.55}.form-grid,.asset-form{display:grid;grid-template-columns:repeat(3,minmax(120px,1fr));gap:12px;margin-top:14px;padding-top:14px;border-top:1px solid #edf1f3}.form-grid label,.asset-form label{font-size:11px;color:#607887}.form-grid input:not([type=checkbox]),.asset-form input,.asset-form select{box-sizing:border-box;width:100%;height:32px;margin-top:6px;border:1px solid #cbd8df}.checkbox{display:flex;align-items:center;gap:8px}.asset-form .wide{grid-column:1/-1}.notice{display:flex;align-items:center;gap:12px;border-left:4px solid #17abc8}.notice span{font-size:11px;color:#667e8d}.business-note{flex-wrap:wrap}.legend{margin-left:auto;font-size:11px}.legend i{display:inline-block;width:9px;height:9px;border-radius:50%;margin:0 4px 0 12px}.normal{background:#35dc91}.attention{background:#42a5f5}.warning{background:#ffb338}.critical{background:#ff4d5e}.summary{display:flex;gap:40px}.summary b{font-size:20px;color:#0a9dbd;margin-right:5px}.empty{padding:50px;text-align:center;background:#fff;border:1px dashed #c9d9e1;color:#7e929e}.danger{color:#d65b5b!important}h3{font-size:13px}.admin>footer{padding:11px 28px;background:#fff;border-top:1px solid #dce5eb;color:#788d99;font-size:10px}.admin>footer span{display:inline-block;width:7px;height:7px;margin-right:7px;border-radius:50%;background:#28c885}@media(max-width:900px){.workspace{grid-template-columns:170px 1fr}.basemap-grid,.form-grid{grid-template-columns:1fr}.workspace>main{padding:18px}}
</style>
