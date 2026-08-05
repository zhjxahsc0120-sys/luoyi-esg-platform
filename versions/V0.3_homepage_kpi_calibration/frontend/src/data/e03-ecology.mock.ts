/**
 * OFFLINE / DEV ONLY — not used by workspace primary path (Phase B.1).
 * E03 workspace reads Demo API `/api/environment/e03/eco-objects` exclusively.
 * Kept for local offline experiments; do not re-wire as silent fallback.
 */
import type {
  E03EcoObjectDetail,
  E03EcoObjectItem,
  E03EcoObjectsPayload,
} from '@/types/e03'

const objects: E03EcoObjectDetail[] = [
  {
    id: 730001,
    objectCode: 'ECO-SENS-01',
    objectName: '沿线饮用水源二级保护区缓冲带',
    objectKind: 'SENSITIVE',
    objectKindLabel: '生态敏感区域',
    locationText: 'K22+500～K24+100 水源保护区边缘',
    sectionCode: 'TJ-1',
    riskLevel: '黄',
    riskStatus: '施工避让管控中',
    protectionRequirement: '禁止废水排放与物料堆放；设立警示标识',
    responsibleUnit: '安全环保部',
    relatedMatter: '环评批复水源保护专章',
    canLocate: false,
    spatialLinks: [],
    updateTime: '2026-07-27 10:00:00',
  },
  {
    id: 730002,
    objectCode: 'ECO-SENS-02',
    objectName: '河谷湿地敏感段',
    objectKind: 'SENSITIVE',
    objectKindLabel: '生态敏感区域',
    locationText: 'K67+300 跨河桥址下游',
    sectionCode: 'TJ-2',
    riskLevel: '蓝',
    riskStatus: '正常',
    protectionRequirement: '桥址施工期浊度监测，落实泥浆循环',
    responsibleUnit: '第二合同段项目部',
    relatedMatter: '水保方案跨河专项',
    canLocate: false,
    spatialLinks: [],
    updateTime: '2026-07-25 15:40:00',
  },
  {
    id: 730003,
    objectCode: 'ECO-OBJ-03',
    objectName: '古树名木保护单株（银杏）',
    objectKind: 'PROTECTED',
    objectKindLabel: '生态保护对象',
    locationText: 'K91+050 改线外侧 80m',
    sectionCode: 'TJ-3',
    riskLevel: '蓝',
    riskStatus: '正常',
    protectionRequirement: '设置保护围栏，禁止根系扰动',
    responsibleUnit: '第三合同段项目部',
    relatedMatter: '林地征占用补充调查',
    canLocate: false,
    spatialLinks: [],
    updateTime: '2026-07-22 09:10:00',
  },
  {
    id: 730004,
    objectCode: 'ECO-OBJ-04',
    objectName: '野生动物通道预留段',
    objectKind: 'PROTECTED',
    objectKindLabel: '生态保护对象',
    locationText: 'K110+600 涵洞通道',
    sectionCode: 'TJ-3',
    riskLevel: '黄',
    riskStatus: '通道畅通核验中',
    protectionRequirement: '保持通道净空与两侧诱导设施完好',
    responsibleUnit: '工程管理部',
    relatedMatter: '生态监测季报',
    canLocate: false,
    spatialLinks: [],
    updateTime: '2026-07-29 14:00:00',
  },
]

function toItem(o: E03EcoObjectDetail): E03EcoObjectItem {
  const {
    id,
    objectCode,
    objectName,
    objectKind,
    objectKindLabel,
    locationText,
    sectionCode,
    riskLevel,
    riskStatus,
    protectionRequirement,
    responsibleUnit,
    relatedMatter,
    canLocate,
    spatialLinks,
    updateTime,
  } = o
  return {
    id,
    objectCode,
    objectName,
    objectKind,
    objectKindLabel,
    locationText,
    sectionCode,
    riskLevel,
    riskStatus,
    protectionRequirement,
    responsibleUnit,
    relatedMatter,
    canLocate,
    spatialLinks,
    updateTime,
  }
}

export function getE03EcoObjectsMock(): E03EcoObjectsPayload {
  const list = objects.map(toItem)
  const sensitiveCount = list.filter((o) => o.objectKind === 'SENSITIVE').length
  const protectedCount = list.filter((o) => o.objectKind === 'PROTECTED').length
  const riskCount = list.filter((o) => o.riskLevel === '红' || o.riskLevel === '黄').length
  return {
    overview: {
      areaCount: sensitiveCount,
      protectedCount,
      riskCount,
      riskStatus: riskCount > 0 ? '关注' : '正常',
    },
    objects: list,
    scope: 'demo',
    isDemo: true,
  }
}

export function getE03EcoObjectDetailMock(objectId: number): E03EcoObjectDetail | null {
  return objects.find((o) => o.id === objectId) || null
}
