/**
 * OFFLINE / DEV ONLY — not used by workspace primary path (Phase B.1).
 * E02 workspace reads Demo API `/api/environment/e02/objects` exclusively.
 * Kept for local offline experiments; do not re-wire as silent fallback.
 */
import type {
  E02ObjectDetail,
  E02ObjectItem,
  E02ObjectsPayload,
} from '@/types/e02'

const objects: E02ObjectDetail[] = [
  {
    id: 620001,
    objectCode: 'WS-Spoil-01',
    objectName: '一标弃土场 A',
    objectType: 'SPOIL',
    objectTypeLabel: '弃土场',
    locationText: 'K18+200 右侧弃土场',
    sectionCode: 'TJ-1',
    riskLevel: '黄',
    riskStatus: '防护加固中',
    restoreStatus: '恢复中',
    measureStatus: '拦挡与排水已落实 80%',
    completionRate: 80,
    responsibleUnit: '第一合同段项目部',
    canLocate: false,
    spatialLinks: [],
    updateTime: '2026-07-30 11:00:00',
    measureRequirement: '完善截排水沟，完成表层覆土与临时绿化',
    rectificationStatus: '整改中',
    spaceDesc: '占地约 2.1 ha，临近冲沟上游',
  },
  {
    id: 620002,
    objectCode: 'WS-Temp-02',
    objectName: '二标临时堆场',
    objectType: 'TEMP_LAND',
    objectTypeLabel: '临时用地',
    locationText: 'K52+050 便道临时堆场',
    sectionCode: 'TJ-2',
    riskLevel: '蓝',
    riskStatus: '管控正常',
    restoreStatus: '待恢复',
    measureStatus: '围挡完整，防渗垫层已铺设',
    completionRate: 65,
    responsibleUnit: '第二合同段项目部',
    canLocate: false,
    spatialLinks: [],
    updateTime: '2026-07-28 16:20:00',
    measureRequirement: '用毕及时清运，复垦前保留表土堆',
    rectificationStatus: '持续管控',
    spaceDesc: '临时占用农用地转用手续齐全',
  },
  {
    id: 620003,
    objectCode: 'WS-Topsoil-03',
    objectName: '三标表土剥离堆',
    objectType: 'TOPSOIL',
    objectTypeLabel: '表土剥离',
    locationText: 'K88+400 表土集中堆放点',
    sectionCode: 'TJ-3',
    riskLevel: '蓝',
    riskStatus: '正常',
    restoreStatus: '已剥离待回覆',
    measureStatus: '覆盖防尘网，四周排水通畅',
    completionRate: 90,
    responsibleUnit: '第三合同段项目部',
    canLocate: false,
    spatialLinks: [],
    updateTime: '2026-07-26 09:40:00',
    measureRequirement: '分标段回覆利用，禁止与弃渣混堆',
    rectificationStatus: '措施落实',
    spaceDesc: '剥离厚度约 30cm，方量约 1.2 万 m³',
  },
  {
    id: 620004,
    objectCode: 'WS-Slope-04',
    objectName: '隧道洞口边坡复绿段',
    objectType: 'SLOPE',
    objectTypeLabel: '边坡复绿',
    locationText: 'K101+120 隧道进口仰坡',
    sectionCode: 'TJ-3',
    riskLevel: '黄',
    riskStatus: '复绿推进中',
    restoreStatus: '植被恢复中',
    measureStatus: '客土喷播完成，成活率复核中',
    completionRate: 72,
    responsibleUnit: '安全环保部',
    canLocate: false,
    spatialLinks: [],
    updateTime: '2026-07-29 13:15:00',
    measureRequirement: '补植与养护至成活率达标后销项',
    rectificationStatus: '待复查',
    spaceDesc: '仰坡分级平台，喷播面积约 0.6 ha',
  },
]

function toItem(o: E02ObjectDetail): E02ObjectItem {
  const {
    id,
    objectCode,
    objectName,
    objectType,
    objectTypeLabel,
    locationText,
    sectionCode,
    riskLevel,
    riskStatus,
    restoreStatus,
    measureStatus,
    completionRate,
    responsibleUnit,
    canLocate,
    spatialLinks,
    updateTime,
  } = o
  return {
    id,
    objectCode,
    objectName,
    objectType,
    objectTypeLabel,
    locationText,
    sectionCode,
    riskLevel,
    riskStatus,
    restoreStatus,
    measureStatus,
    completionRate,
    responsibleUnit,
    canLocate,
    spatialLinks,
    updateTime,
  }
}

export function getE02ObjectsMock(): E02ObjectsPayload {
  const list = objects.map(toItem)
  const riskCount = list.filter((o) => o.riskLevel === '红' || o.riskLevel === '黄').length
  const avg =
    list.length === 0
      ? 100
      : Math.round(list.reduce((s, o) => s + (o.completionRate || 0), 0) / list.length)
  const byType = {
    SPOIL: list.filter((o) => o.objectType === 'SPOIL').length,
    TEMP_LAND: list.filter((o) => o.objectType === 'TEMP_LAND').length,
    TOPSOIL: list.filter((o) => o.objectType === 'TOPSOIL').length,
    SLOPE: list.filter((o) => o.objectType === 'SLOPE').length,
  }
  return {
    overview: {
      objectCount: list.length,
      riskCount,
      completionRate: avg,
      restoreNormalCount: list.filter((o) => o.riskStatus === '正常' || o.riskStatus === '管控正常')
        .length,
      byType,
    },
    objects: list,
    scope: 'demo',
    isDemo: true,
  }
}

export function getE02ObjectDetailMock(objectId: number): E02ObjectDetail | null {
  return objects.find((o) => o.id === objectId) || null
}
