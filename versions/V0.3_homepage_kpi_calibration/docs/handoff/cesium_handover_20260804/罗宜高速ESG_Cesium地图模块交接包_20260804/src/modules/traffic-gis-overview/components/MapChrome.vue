<script setup lang="ts">
import { RotateCcw, Settings } from 'lucide-vue-next';
import type { PresentationMode } from '../types';

withDefaults(defineProps<{
  mode: 'all' | 'construction' | 'environment' | 'risk';
  configOpen: boolean;
  heading: number;
  showConfigButton?: boolean;
  showModeSwitch?: boolean;
  presentationMode?: PresentationMode;
}>(), {
  showConfigButton: true,
  showModeSwitch: true,
  presentationMode: 'preview',
});

defineEmits<{
  modeChange: ['all' | 'construction' | 'environment' | 'risk'];
  reset: [];
  north: [];
  config: [];
}>();
</script>

<template>
  <div class="chrome" :class="{ 'chrome--dashboard': presentationMode === 'dashboard' }">
    <div class="frame">
      <i></i><i></i><i></i><i></i>
    </div>
    <div v-if="presentationMode !== 'dashboard'" class="title">
      <b>GIS 地图主视览</b>
      <span>空间态势 + 时序影像</span>
    </div>
    <div class="tools" role="toolbar" aria-label="地图专题视图">
      <span v-if="showModeSwitch" class="tools__label">专题视图</span>
      <div v-if="showModeSwitch" class="tools__modes" role="group" aria-label="业务专题">
        <button :class="{ active: mode === 'all' }" title="显示全部已启用的地图对象" @click="$emit('modeChange', 'all')">综合</button>
        <button :class="{ active: mode === 'construction' }" title="查看路线、标段、桩号和施工区域" @click="$emit('modeChange', 'construction')">工程标段</button>
        <button :class="{ active: mode === 'environment' }" title="查看环境监测点和生态保护区域" @click="$emit('modeChange', 'environment')">环境监测</button>
        <button :class="{ active: mode === 'risk' }" title="查看风险点和预警事项" @click="$emit('modeChange', 'risk')">风险预警</button>
      </div>
      <button class="tools__reset" title="恢复项目全线默认视角" aria-label="复位视角" @click="$emit('reset')">
        <RotateCcw /><span>复位视角</span>
      </button>
    </div>
    <button
      v-if="showConfigButton"
      class="settings-button"
      :class="{ active: configOpen }"
      title="地图设置"
      aria-label="打开地图设置"
      @click="$emit('config')"
    >
      <Settings /><span>设置</span>
    </button>
    <button class="compass" title="点击回正北" @click="$emit('north')">
      <span class="rose" :style="{ transform: `rotate(${heading}deg)` }">
        <b>N</b><i>▲</i><i>◆</i><small>S</small>
      </span>
    </button>
  </div>
</template>

<style scoped>
.chrome,
.frame {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.chrome {
  z-index: 8;
}
.frame {
  border: 1px solid rgba(19, 201, 240, 0.5);
  box-shadow: inset 0 0 38px rgba(0, 126, 180, 0.12);
}
.frame i {
  position: absolute;
  width: 38px;
  height: 18px;
  border-color: #21d4f4;
}
.frame i:nth-child(1) { left: 0; top: 0; border-left: 3px solid; border-top: 3px solid; }
.frame i:nth-child(2) { right: 0; top: 0; border-right: 3px solid; border-top: 3px solid; }
.frame i:nth-child(3) { left: 0; bottom: 0; border-left: 3px solid; border-bottom: 3px solid; }
.frame i:nth-child(4) { right: 0; bottom: 0; border-right: 3px solid; border-bottom: 3px solid; }

.title {
  position: absolute;
  left: 16px;
  top: 13px;
  padding: 8px 16px;
  background: linear-gradient(90deg, rgba(3, 25, 43, 0.95), rgba(3, 25, 43, 0.35));
  border-left: 3px solid #20d4f2;
  pointer-events: auto;
}
.title b, .title span { display: block; }
.title b { color: #29d9f5; font-size: 16px; }
.title span { margin-top: 3px; color: #6ba5ba; font-size: 10px; }

.tools {
  position: absolute;
  left: 50%;
  top: 14px;
  display: flex;
  align-items: center;
  gap: 7px;
  transform: translateX(-50%);
  padding: 5px 6px;
  border: 1px solid rgba(113, 185, 218, 0.22);
  border-radius: 6px;
  background: rgba(4, 22, 37, 0.46);
  box-shadow: 0 3px 14px rgba(0, 8, 18, 0.14);
  backdrop-filter: blur(5px);
  pointer-events: auto;
}
.tools__label {
  padding: 0 5px;
  color: rgba(203, 231, 242, 0.68);
  font-size: 12px;
  white-space: nowrap;
}
.tools__modes {
  display: flex;
  gap: 3px;
  padding: 2px;
  border-radius: 4px;
  background: rgba(2, 15, 27, 0.22);
}
.tools button {
  min-height: 30px;
  padding: 5px 11px;
  border: 1px solid transparent;
  border-radius: 3px;
  background: rgba(15, 54, 76, 0.26);
  color: rgba(220, 241, 248, 0.82);
  font-size: 12px;
  white-space: nowrap;
  cursor: pointer;
  transition: color .15s ease, border-color .15s ease, background .15s ease;
}
.tools button:hover {
  border-color: rgba(112, 213, 235, 0.32);
  color: #f2fbff;
  background: rgba(44, 126, 158, 0.26);
}
.tools button.active {
  border-color: rgba(100, 218, 238, 0.42);
  color: #effcff;
  background: rgba(28, 132, 164, 0.38);
  box-shadow: inset 0 -2px rgba(89, 222, 238, 0.58);
}
.tools .tools__reset {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-left: 2px;
  padding-inline: 9px;
  border-left-color: rgba(143, 195, 215, 0.2);
  color: rgba(190, 218, 229, 0.72);
  background: transparent;
}
.tools__reset svg {
  width: 13px;
  height: 13px;
}

.settings-button {
  position: absolute;
  right: 14px;
  top: 12px;
  display: grid;
  place-items: center;
  width: 66px;
  height: 34px;
  grid-template-columns: auto auto;
  gap: 5px;
  padding: 0 9px;
  border: 1px solid rgba(55, 220, 255, .58);
  border-radius: 5px;
  background: rgba(3, 28, 48, 0.68);
  color: #c9eaf5;
  box-shadow: 0 0 6px rgba(34, 215, 255, .18);
  pointer-events: auto;
  cursor: pointer;
}
.settings-button:hover,
.settings-button.active {
  border-color: #fff;
  color: #fff;
  background: rgba(8, 82, 119, 0.82);
  box-shadow: 0 0 10px rgba(34, 215, 255, .38);
  transform: translateY(-1px);
}
.settings-button svg {
  width: 15px;
  height: 15px;
}
.settings-button span { font-size: 11px; font-weight: 700; }

.compass {
  position: absolute;
  right: 19px;
  top: 67px;
  width: 62px;
  height: 62px;
  padding: 0;
  border: 1px solid rgba(34, 193, 224, 0.35);
  border-radius: 50%;
  background: radial-gradient(circle, rgba(8, 48, 68, 0.9), rgba(2, 14, 27, 0.72));
  box-shadow: 0 0 18px rgba(19, 197, 235, 0.2);
  pointer-events: auto;
  cursor: pointer;
}
.rose {
  position: absolute;
  inset: 5px;
  display: block;
  border: 1px solid rgba(133, 221, 239, 0.3);
  border-radius: 50%;
  transition: transform 0.12s linear;
}
.rose b, .rose small, .rose i {
  position: absolute;
  color: #dff9ff;
  font-style: normal;
  text-shadow: 0 0 7px #18c7eb;
}
.rose b { left: 50%; top: 1px; transform: translateX(-50%); font-size: 10px; color: #ff6e6e; }
.rose small { left: 50%; bottom: 1px; transform: translateX(-50%); font-size: 8px; }
.rose i:nth-of-type(1) { left: 50%; top: 12px; transform: translateX(-50%); font-size: 19px; color: #ff7474; }
.rose i:nth-of-type(2) { left: 50%; top: 23px; transform: translateX(-50%) rotate(45deg); font-size: 14px; color: #a8efff; }

/* Dashboard 模式：更紧凑的工具条 */
.chrome--dashboard .tools {
  top: 6px;
  gap: 5px;
  padding: 3px 4px;
  background: rgba(3, 20, 38, 0.4);
}
.chrome--dashboard .tools__label {
  padding: 0 4px;
  font-size: 11px;
}
.chrome--dashboard .tools button {
  min-height: 26px;
  padding: 3px 8px;
  font-size: 11px;
}
.chrome--dashboard .frame i {
  display: none;
}
.chrome--dashboard .settings-button {
  top: 8px;
  right: 10px;
  width: 60px;
  height: 30px;
}
.chrome--dashboard .compass {
  width: 50px;
  height: 50px;
  top: 56px;
  right: 14px;
}
.chrome--dashboard .title b {
  font-size: 14px;
}
.chrome--dashboard .title span {
  font-size: 9px;
}

@media (max-width: 1050px) {
  .tools { left: 16px; top: 70px; transform: none; }
  .compass { display: none; }
}
</style>
