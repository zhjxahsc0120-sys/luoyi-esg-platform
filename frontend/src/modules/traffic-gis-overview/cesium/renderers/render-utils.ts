import * as Cesium from "cesium";
import { statusColors } from "../../config/style-tokens";
import type { TrafficMapFeature } from "../../types";
const businessStatusColors: Record<string, string> = {
  ...statusColors,
  '正常': statusColors.normal,
  '达标': statusColors.normal,
  '已完成': statusColors.normal,
  '超标': statusColors.critical,
  '逾期': statusColors.critical,
  '异常': statusColors.warning,
  '待复测': statusColors.warning,
};
export const featureColor = (f: TrafficMapFeature, fallback: string) =>
  Cesium.Color.fromCssColorString(
    (f.status && businessStatusColors[f.status]) || fallback || '#22d7ff',
  );
export const entityMeta = (f: TrafficMapFeature) => ({
  id: f.id,
  name: f.name,
  properties: { trafficFeature: f },
});
const iconGlyph:Record<string,string>={"slope-monitor":"!","spoil-site":"弃","water-source":"水","ecological-zone":"叶",risk:"!",monitor:"测","environment-monitor":"测"};
export function featureIcon(f:TrafficMapFeature,color:string){const critical=f.status==='critical';const glyph=critical?'!':(iconGlyph[f.objectType]||'●');const fill=critical?'#ff263d':'#06182a';const ring=critical?'#ffffff':color;const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="44" height="54" viewBox="0 0 44 54"><filter id="g"><feGaussianBlur stdDeviation="${critical?3:2}"/></filter><path d="M22 52S3 34 3 21a19 19 0 1 1 38 0c0 13-19 31-19 31z" fill="${color}" opacity="${critical?.8:.45}" filter="url(#g)"/><path d="M22 48S7 32 7 21a15 15 0 1 1 30 0c0 11-15 27-15 27z" fill="${fill}" stroke="${ring}" stroke-width="${critical?3:2}"/><circle cx="22" cy="21" r="10" fill="${critical?'#d90024':color}" opacity="${critical?1:.22}"/><text x="22" y="27" text-anchor="middle" font-family="Microsoft YaHei" font-size="${critical?18:13}" font-weight="800" fill="white">${glyph}</text></svg>`;return`data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`}
const xml=(value:string)=>value.replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[char]||char));
export function featureLabel(text:string,accent:string,textColor='#ffffff',fontSize=13){const width=Math.max(74,Array.from(text).length*fontSize+28);const height=42;const safe=xml(text);const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><defs><filter id="s"><feGaussianBlur stdDeviation="2"/></filter><linearGradient id="b" x2="1"><stop stop-color="#071b2d" stop-opacity=".96"/><stop offset="1" stop-color="#0b2c43" stop-opacity=".92"/></linearGradient></defs><rect x="3" y="3" width="${width-6}" height="28" rx="3" fill="${accent}" opacity=".35" filter="url(#s)"/><path d="M4 2H${width-4}V30H${width/2+6}L${width/2} 38L${width/2-6} 30H4Z" fill="url(#b)" stroke="${accent}" stroke-width="1.4"/><path d="M4 2H24" stroke="#fff" stroke-opacity=".75" stroke-width="2"/><text x="${width/2}" y="21" text-anchor="middle" font-family="Microsoft YaHei" font-size="${fontSize}" font-weight="600" fill="${textColor}">${safe}</text></svg>`;return{image:`data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`,width,height}}
