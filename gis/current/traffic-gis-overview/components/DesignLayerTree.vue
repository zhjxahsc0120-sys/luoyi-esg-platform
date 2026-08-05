<script setup lang="ts">
import { computed, ref } from "vue";
import {
  ChevronDown,
  ChevronRight,
  Crosshair,
  Layers3,
  Map,
  Mountain,
  RotateCcw,
  X,
} from "lucide-vue-next";
import { basemapDefinitions, type BasemapId } from "../config/basemaps.config";
import type {
  DesignKmlLayerDefinition,
  DesignLayerManifest,
  DesignLayerStateMap,
} from "../types/design-layers";

const props = defineProps<{
  open: boolean;
  manifest: DesignLayerManifest | null;
  states: DesignLayerStateMap;
  activeBasemap: BasemapId;
  terrainEnabled: boolean;
}>();

const emit = defineEmits<{
  close: [];
  layerToggle: [layerId: string, visible: boolean];
  groupToggle: [layerIds: string[], visible: boolean];
  selectAll: [];
  clearAll: [];
  locate: [layerId: string];
  opacity: [layerId: string, opacity: number];
  basemapChange: [id: BasemapId];
  terrainChange: [enabled: boolean];
  reset: [];
}>();

const expanded = ref(
  new Set<string>([
    "route",
    "structures",
    "labels",
    "road_group",
    "slope",
    "spoil",
    "eco_constraints",
    "filtered_design_map",
    "homepage_map_layers",
  ]),
);

const visibleCount = computed(
  () => Object.values(props.states).filter((state) => state.visible).length,
);
const totalCount = computed(
  () =>
    props.manifest?.groups.reduce(
      (sum, group) =>
        sum + group.layers.filter((layer) => layer.available !== false).length,
      0,
    ) || 0,
);

function stateOf(id: string) {
  return (
    props.states[id] || {
      visible: false,
      loaded: false,
      loading: false,
      opacity: 1,
    }
  );
}

function toggleGroupOpen(id: string) {
  const next = new Set(expanded.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  expanded.value = next;
}

function groupChecked(layers: DesignKmlLayerDefinition[]) {
  const available = layers.filter((layer) => layer.available !== false);
  return (
    available.length > 0 &&
    available.every((layer) => stateOf(layer.id).visible)
  );
}

function groupPartial(layers: DesignKmlLayerDefinition[]) {
  const available = layers.filter((layer) => layer.available !== false);
  const count = available.filter((layer) => stateOf(layer.id).visible).length;
  return count > 0 && count < available.length;
}

function onGroupToggle(layers: DesignKmlLayerDefinition[], event: Event) {
  emit(
    "groupToggle",
    layers
      .filter((layer) => layer.available !== false)
      .map((layer) => layer.id),
    (event.target as HTMLInputElement).checked,
  );
}

function opacityLabel(value: number) {
  return `${Math.round(value * 100)}%`;
}
</script>

<template>
  <aside v-if="open" class="design-layer-tree">
    <header>
      <div>
        <Layers3 :size="16" />
        <span><b>项目一张图</b><small>S1-6 设计图层</small></span>
      </div>
      <button title="关闭图层树" @click="$emit('close')"><X :size="15" /></button>
    </header>

    <div class="design-layer-tree__actions">
      <button @click="$emit('selectAll')">全选</button>
      <button @click="$emit('clearAll')">清空</button>
      <span>{{ visibleCount }}/{{ totalCount }} 已显示</span>
    </div>

    <div v-if="!manifest" class="design-layer-tree__empty">正在读取图层配置…</div>
    <div v-else class="design-layer-tree__groups">
      <section v-for="group in manifest.groups" :key="group.id">
        <div class="design-layer-tree__group">
          <button class="expand" @click="toggleGroupOpen(group.id)">
            <component :is="expanded.has(group.id) ? ChevronDown : ChevronRight" :size="14" />
          </button>
          <input
            type="checkbox"
            :checked="groupChecked(group.layers)"
            :indeterminate="groupPartial(group.layers)"
            @change="onGroupToggle(group.layers, $event)"
          />
          <button class="group-name" @click="toggleGroupOpen(group.id)">
            {{ group.name }}<small>{{ group.layers.length }}</small>
          </button>
        </div>

        <div v-if="expanded.has(group.id)" class="design-layer-tree__children">
          <article
            v-for="layer in group.layers"
            :key="layer.id"
            :class="{
              active: stateOf(layer.id).visible,
              error: stateOf(layer.id).error,
              unavailable: layer.available === false,
            }"
          >
            <div class="layer-main">
              <input
                type="checkbox"
                :checked="stateOf(layer.id).visible"
                :disabled="layer.available === false || stateOf(layer.id).loading"
                @change="$emit('layerToggle', layer.id, ($event.target as HTMLInputElement).checked)"
              />
              <button
                class="layer-name"
                :title="`${layer.note || ''}\n要素 ${layer.featureCount.toLocaleString()} 个`"
                :disabled="layer.available === false"
                @click="
                  layer.available !== false &&
                  $emit('layerToggle', layer.id, !stateOf(layer.id).visible)
                "
              >
                <span>{{ layer.name }}</span>
                <small v-if="layer.available === false">暂无数据</small>
                <small v-else-if="stateOf(layer.id).loading">加载中…</small>
                <small v-else-if="stateOf(layer.id).error">{{ stateOf(layer.id).error }}</small>
                <small v-else>{{ layer.featureCount.toLocaleString() }} 个要素</small>
              </button>
              <button
                class="locate"
                :disabled="layer.available === false || !stateOf(layer.id).loaded"
                title="定位到图层"
                @click="$emit('locate', layer.id)"
              >
                <Crosshair :size="13" />
              </button>
            </div>
            <label v-if="stateOf(layer.id).visible" class="opacity">
              <span>透明度</span>
              <input
                type="range"
                min="0.1"
                max="1"
                step="0.05"
                :value="stateOf(layer.id).opacity"
                @input="$emit('opacity', layer.id, Number(($event.target as HTMLInputElement).value))"
              />
              <em>{{ opacityLabel(stateOf(layer.id).opacity) }}</em>
            </label>
          </article>
        </div>
      </section>
    </div>

    <footer>
      <label>
        <Map :size="13" /><span>底图</span>
        <select
          :value="activeBasemap"
          @change="$emit('basemapChange', ($event.target as HTMLSelectElement).value as BasemapId)"
        >
          <option v-for="item in basemapDefinitions" :key="item.id" :value="item.id">
            {{ item.name }}
          </option>
        </select>
      </label>
      <label class="terrain-switch">
        <Mountain :size="13" /><span>在线地形</span>
        <input
          type="checkbox"
          :checked="terrainEnabled"
          @change="$emit('terrainChange', ($event.target as HTMLInputElement).checked)"
        />
      </label>
      <button class="reset" @click="$emit('reset')"><RotateCcw :size="13" />回到项目全景</button>
    </footer>
  </aside>
</template>

<style scoped>
.design-layer-tree {
  position: absolute;
  z-index: 15;
  top: 48px;
  bottom: 52px;
  left: 10px;
  display: grid;
  width: 282px;
  min-height: 0;
  grid-template-rows: auto auto 1fr auto;
  color: #d9f1ff;
  border: 1px solid rgba(44, 184, 224, 0.48);
  border-radius: 6px;
  background: linear-gradient(155deg, rgba(3, 23, 42, 0.94), rgba(2, 13, 27, 0.9));
  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.38);
  backdrop-filter: blur(8px);
}
.design-layer-tree button,
.design-layer-tree select {
  color: inherit;
  border: 0;
  background: transparent;
}
.design-layer-tree > header {
  display: flex;
  min-height: 48px;
  align-items: center;
  justify-content: space-between;
  padding: 0 11px 0 13px;
  border-bottom: 1px solid rgba(65, 167, 202, 0.24);
}
.design-layer-tree > header > div {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #2bd9f4;
}
.design-layer-tree > header span,
.design-layer-tree > header b,
.design-layer-tree > header small {
  display: block;
}
.design-layer-tree > header b { color: #e4f8ff; font-size: 14px; }
.design-layer-tree > header small { margin-top: 2px; color: #6f93ac; font-size: 9px; }
.design-layer-tree > header button { display: grid; width: 28px; height: 28px; place-items: center; cursor: pointer; }
.design-layer-tree__actions {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border-bottom: 1px solid rgba(65, 167, 202, 0.17);
}
.design-layer-tree__actions button {
  padding: 4px 10px;
  border: 1px solid rgba(52, 174, 214, 0.34);
  border-radius: 3px;
  background: rgba(14, 74, 103, 0.38);
  font-size: 10px;
  cursor: pointer;
}
.design-layer-tree__actions span { margin-left: auto; color: #6f93ac; font-size: 9px; }
.design-layer-tree__groups {
  min-height: 0;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: #1c7799 #071a2c;
}
.design-layer-tree__group {
  display: grid;
  min-height: 37px;
  grid-template-columns: 24px 18px 1fr;
  align-items: center;
  padding: 0 7px;
  border-bottom: 1px solid rgba(65, 167, 202, 0.13);
  background: rgba(7, 44, 68, 0.48);
}
.expand { display: grid; place-items: center; cursor: pointer; }
.group-name { display: flex; align-items: center; justify-content: space-between; padding: 0 4px; text-align: left; font-size: 12px; cursor: pointer; }
.group-name small {
  min-width: 21px;
  padding: 2px 5px;
  color: #7aa3b6;
  border-radius: 10px;
  background: rgba(27, 89, 117, 0.5);
  text-align: center;
}
.design-layer-tree__children article {
  padding: 7px 8px 7px 34px;
  border-bottom: 1px solid rgba(68, 129, 151, 0.1);
  transition: background 0.15s ease;
}
.design-layer-tree__children article.active {
  background: linear-gradient(90deg, rgba(18, 120, 151, 0.24), transparent);
}
.design-layer-tree__children article.error { background: rgba(127, 26, 41, 0.22); }
.design-layer-tree__children article.unavailable {
  opacity: 0.55;
  background: rgba(75, 91, 105, 0.12);
}
.design-layer-tree__children article.unavailable .layer-name {
  cursor: not-allowed;
}
.layer-main {
  display: grid;
  grid-template-columns: 18px 1fr 26px;
  align-items: center;
  gap: 4px;
}
.layer-name { min-width: 0; padding: 0; text-align: left; cursor: pointer; }
.layer-name span,
.layer-name small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.layer-name span { color: #c9e5ef; font-size: 11px; }
.layer-name small { margin-top: 3px; color: #557f93; font-size: 8px; }
article.error .layer-name small { color: #ff7d8c; }
.locate { display: grid; width: 26px; height: 25px; place-items: center; color: #60cfe9 !important; cursor: pointer; }
.locate:disabled { opacity: 0.25; cursor: default; }
.opacity {
  display: grid;
  grid-template-columns: 36px 1fr 30px;
  align-items: center;
  gap: 5px;
  margin-top: 6px;
  color: #6f93ac;
  font-size: 8px;
}
.opacity input { width: 100%; height: 3px; accent-color: #25c9e6; }
.opacity em { color: #87b7c9; font-style: normal; text-align: right; }
.design-layer-tree__empty { display: grid; place-items: center; color: #6f93ac; font-size: 11px; }
.design-layer-tree > footer {
  display: grid;
  gap: 7px;
  padding: 9px 10px;
  border-top: 1px solid rgba(65, 167, 202, 0.22);
  background: rgba(2, 17, 31, 0.75);
}
.design-layer-tree > footer label {
  display: grid;
  grid-template-columns: 18px 62px 1fr;
  align-items: center;
  color: #87a9b9;
  font-size: 10px;
}
.design-layer-tree > footer select {
  height: 26px;
  padding: 0 6px;
  border: 1px solid rgba(50, 151, 190, 0.36);
  background: #08243b;
  font-size: 10px;
}
.terrain-switch input { justify-self: end; accent-color: #27d2ec; }
.design-layer-tree > footer .reset {
  display: flex;
  height: 29px;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: #caedf7;
  border: 1px solid rgba(52, 174, 214, 0.34);
  border-radius: 3px;
  background: rgba(14, 74, 103, 0.38);
  font-size: 10px;
  cursor: pointer;
}
@media (max-width: 900px) {
  .design-layer-tree { width: 242px; }
}
</style>
