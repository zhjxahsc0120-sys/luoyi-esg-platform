/**
 * E03 水保与复绿 — 前端展示 Demo。
 * 可尝试复用 Phase B E02 objects API 并映射；不可用时回退本 Demo。
 */
import type {
  E03ObjectType,
  E03WaterObjectDetail,
  E03WaterObjectItem,
  E03WaterObjectsPayload,
} from '@/types/e03'
import type { E02ObjectItem, E02ObjectsPayload } from '@/types/e02'

const objects: E03WaterObjectDetail[] = [
  {
    id: 630001,
    objectCode: 'WS-Spoil-01',
    objectName: '一标弃土场 A',
    objectType: 'SPOIL',
    objectTypeLabel: '弃土场',
    locationText: 'K18+200 右侧弃土场',
    sectionCode: 'TJ-1',
    areaHa: 2.1,
    status: '防护加固中',
    isKey: true,
    approvalStatus: '已批复',
    regreenStatus: '恢复中',
    imageryNote: '2026-07 无人机正射已入库',
    responsibleUnit: '第一合同段项目部',
    canLocate: true,
    spatialLinks: [
      { featureId: 'LY-SEC-TJ1', geometryType: 'LineString', role: 'section', isPrimary: true },
    ],
    updateTime: '2026-07-30 11:00:00',
    spaceDesc: '占地约 2.1 ha，临近冲沟上游',
    measureRequirement: '完善截排水沟，完成表层覆土与临时绿化',
  },
  {
    id: 630002,
    objectCode: 'WS-Temp-02',
    objectName: '二标临时堆场',
    objectType: 'TEMP_LAND',
    objectTypeLabel: '临时占地',
    locationText: 'K52+050 便道临时堆场',
    sectionCode: 'TJ-2',
    areaHa: 0.8,
    status: '管控中',
    isKey: true,
    approvalStatus: '临时用地手续齐全',
    regreenStatus: '待复垦',
    imageryNote: '现场照片 6 张',
    responsibleUnit: '第二合同段项目部',
    canLocate: true,
    spatialLinks: [
      { featureId: 'LY-SEC-TJ2', geometryType: 'LineString', role: 'section', isPrimary: true },
    ],
    updateTime: '2026-07-28 16:20:00',
    spaceDesc: '临时占用农用地转用手续齐全',
    measureRequirement: '用毕及时清运，复垦前保留表土堆',
  },
  {
    id: 630003,
    objectCode: 'WS-Topsoil-03',
    objectName: '三标表土剥离堆',
    objectType: 'TOPSOIL',
    objectTypeLabel: '表土剥离',
    locationText: 'K88+400 表土集中堆放点',
    sectionCode: 'TJ-3',
    areaHa: 0.35,
    status: '正常堆存',
    isKey: false,
    approvalStatus: '方案备案',
    regreenStatus: '已剥离待回覆',
    imageryNote: '暂无最新影像',
    responsibleUnit: '第三合同段项目部',
    canLocate: true,
    spatialLinks: [
      { featureId: 'LY-SEC-TJ3', geometryType: 'LineString', role: 'section', isPrimary: true },
    ],
    updateTime: '2026-07-26 09:40:00',
    spaceDesc: '剥离厚度约 30cm，方量约 1.2 万 m³',
    measureRequirement: '分标段回覆利用，禁止与弃渣混堆',
  },
  {
    id: 630004,
    objectCode: 'WS-Regreen-04',
    objectName: '隧道洞口边坡复绿段',
    objectType: 'REGREEN',
    objectTypeLabel: '复绿区域',
    locationText: 'K101+120 隧道进口仰坡',
    sectionCode: 'TJ-3',
    areaHa: 0.6,
    status: '复绿推进中',
    isKey: true,
    approvalStatus: '专项方案已审',
    regreenStatus: '客土喷播完成，成活率复核中',
    imageryNote: '2026-07-29 航拍对比图已关联',
    responsibleUnit: '安全环保部',
    canLocate: true,
    spatialLinks: [
      { featureId: 'LY-SEC-TJ3', geometryType: 'LineString', role: 'section', isPrimary: true },
    ],
    updateTime: '2026-07-29 13:15:00',
    spaceDesc: '仰坡分级平台，喷播面积约 0.6 ha',
    measureRequirement: '补植与养护至成活率达标后销项',
  },
]

function toItem(o: E03WaterObjectDetail): E03WaterObjectItem {
  const {
    id,
    objectCode,
    objectName,
    objectType,
    objectTypeLabel,
    locationText,
    sectionCode,
    areaHa,
    status,
    isKey,
    approvalStatus,
    regreenStatus,
    imageryNote,
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
    areaHa,
    status,
    isKey,
    approvalStatus,
    regreenStatus,
    imageryNote,
    responsibleUnit,
    canLocate,
    spatialLinks,
    updateTime,
  }
}

function mapLegacyType(type: string): { objectType: E03ObjectType; label: string } {
  if (type === 'SPOIL') return { objectType: 'SPOIL', label: '弃土场' }
  if (type === 'TEMP_LAND') return { objectType: 'TEMP_LAND', label: '临时占地' }
  if (type === 'TOPSOIL') return { objectType: 'TOPSOIL', label: '表土剥离' }
  return { objectType: 'REGREEN', label: '复绿区域' }
}

/** 将 Phase B E02 水保对象载荷映射为 V1.0 E03 展示结构 */
export function mapE02ObjectsToE03Water(payload: E02ObjectsPayload): E03WaterObjectsPayload {
  const objectsMapped: E03WaterObjectItem[] = (payload.objects || []).map((o: E02ObjectItem, idx) => {
    const mapped = mapLegacyType(o.objectType === 'SLOPE' ? 'REGREEN' : o.objectType)
    const isKey = o.riskLevel === '红' || o.riskLevel === '黄' || o.riskStatus?.includes('中')
    return {
      id: o.id,
      objectCode: o.objectCode,
      objectName: o.objectName,
      objectType: mapped.objectType,
      objectTypeLabel: mapped.label,
      locationText: o.locationText,
      sectionCode: o.sectionCode,
      areaHa: Number((1.2 + (idx % 4) * 0.3).toFixed(2)),
      status: o.riskStatus || o.restoreStatus || '管控中',
      isKey: Boolean(isKey),
      approvalStatus: '审批状态待接口补充',
      regreenStatus: o.restoreStatus || o.measureStatus || '—',
      imageryNote: '影像资料待关联',
      responsibleUnit: o.responsibleUnit,
      canLocate: o.canLocate || (o.spatialLinks?.length > 0),
      spatialLinks: o.spatialLinks || [],
      updateTime: o.updateTime,
    }
  })
  return buildPayload(objectsMapped, payload.scope || 'demo', Boolean(payload.isDemo))
}

function buildPayload(
  list: E03WaterObjectItem[],
  scope: string,
  isDemo: boolean,
): E03WaterObjectsPayload {
  const byType: Record<E03ObjectType, number> = {
    SPOIL: 0,
    TEMP_LAND: 0,
    TOPSOIL: 0,
    REGREEN: 0,
  }
  for (const o of list) byType[o.objectType] += 1
  return {
    overview: {
      objectCount: list.length,
      keyCount: list.filter((o) => o.isKey).length,
      areaTotalHa: Number(list.reduce((s, o) => s + (o.areaHa || 0), 0).toFixed(2)),
      pendingApproval: list.filter((o) => !String(o.approvalStatus).includes('已')).length,
      byType,
    },
    objects: list,
    scope,
    isDemo,
  }
}

export function getE03WaterObjectsMock(): E03WaterObjectsPayload {
  return buildPayload(objects.map(toItem), 'demo', true)
}

export function getE03WaterObjectDetailMock(objectId: number): E03WaterObjectDetail | null {
  return objects.find((o) => o.id === objectId) || null
}

export function isE03KeyObject(o: Pick<E03WaterObjectItem, 'isKey'>): boolean {
  return Boolean(o.isKey)
}
