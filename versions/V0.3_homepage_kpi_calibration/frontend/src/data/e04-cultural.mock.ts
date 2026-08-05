/**
 * Phase B — E04 文物保护管控 mock.
 * Shape mirrors GET /api/environment/e04/cultural-objects(+/{id}).
 * Leadership zero-object demo: survey done / 0 objects / risk normal.
 */
import type {
  E04CulturalObjectDetail,
  E04CulturalObjectsPayload,
} from '@/types/e04-cultural'

/** Zero-object leadership demo (preferred empty state). */
export const e04CulturalZeroPayload: E04CulturalObjectsPayload = {
  overview: {
    surveyStatus: '文物调查已完成',
    objectCount: 0,
    measureRate: 100,
    riskCount: 0,
    riskStatus: '正常',
    status: '正常',
  },
  objects: [],
  isDemo: true,
}

/** Seeded objects when demo needs non-empty list (API swap still preferred). */
export const e04CulturalDemoObjects: E04CulturalObjectDetail[] = [
  {
    id: 540001,
    projectId: 'LUOYI-ESG',
    sectionId: 1,
    relicCode: 'CR-K45-600',
    relicName: 'K45+600文物调查点',
    relicType: '历史遗迹',
    protectionLevel: '一般保护',
    locationDesc: 'K45+600 右侧坡脚',
    riskStatus: '正常',
    responsibleUnit: '安全环保部',
    updateTime: '2026-07-20 10:00:00',
    longitude: 114.12,
    latitude: 30.45,
    protectionScope: '施工影响范围外 50m',
    constructionImpact: '线路绕避，无直接扰动',
    protectionMeasure: '围挡标识 + 定期巡查',
    materialStatus: '调查报告已归档',
  },
  {
    id: 540002,
    projectId: 'LUOYI-ESG',
    sectionId: 2,
    relicCode: 'CR-K78-200',
    relicName: 'K78+200文物调查点',
    relicType: '古墓葬线索',
    protectionLevel: '重点关注',
    locationDesc: 'K78+200 左侧便道旁',
    riskStatus: '正常',
    responsibleUnit: '第二合同段项目部',
    updateTime: '2026-07-18 15:30:00',
    longitude: 114.35,
    latitude: 30.52,
    protectionScope: '临时用地外侧缓冲带',
    constructionImpact: '便道施工已避让',
    protectionMeasure: '专人看护 + 影像留存',
    materialStatus: '现场确认单齐全',
  },
  {
    id: 540003,
    projectId: 'LUOYI-ESG',
    sectionId: 3,
    relicCode: 'CR-K102-500',
    relicName: 'K102+500文物调查点',
    relicType: '近现代建筑遗存',
    protectionLevel: '一般保护',
    locationDesc: 'K102+500 改线段外侧',
    riskStatus: '正常',
    responsibleUnit: '第三合同段项目部',
    updateTime: '2026-07-15 09:20:00',
    longitude: 114.58,
    latitude: 30.61,
    protectionScope: '构筑物本体及 20m 缓冲',
    constructionImpact: '无占压',
    protectionMeasure: '警示牌 + 月度复核',
    materialStatus: '保护方案已备案',
  },
]

export function getE04CulturalObjectsMock(opts?: { zero?: boolean }): E04CulturalObjectsPayload {
  if (opts?.zero !== false && opts?.zero !== true) {
    // Default for leadership demo empty-state path when API absent: show completed survey
    // Prefer non-empty if DEMO_E04_OBJECTS=1, else zero-friendly.
    const preferObjects = String(import.meta.env.VITE_E04_MOCK_OBJECTS || '') === '1'
    if (!preferObjects) return { ...e04CulturalZeroPayload }
  }
  if (opts?.zero) return { ...e04CulturalZeroPayload }

  const objects = e04CulturalDemoObjects.map(
    ({
      id,
      relicCode,
      relicName,
      relicType,
      protectionLevel,
      locationDesc,
      riskStatus,
      responsibleUnit,
      updateTime,
    }) => ({
      id,
      relicCode,
      relicName,
      relicType,
      protectionLevel,
      locationDesc,
      riskStatus,
      responsibleUnit,
      updateTime,
    }),
  )
  return {
    overview: {
      surveyStatus: '文物调查已完成',
      objectCount: objects.length,
      measureRate: 100,
      riskCount: 0,
      riskStatus: '正常',
      status: '正常',
    },
    objects,
    isDemo: true,
  }
}

export function getE04CulturalObjectDetailMock(
  objectId: number,
): E04CulturalObjectDetail | null {
  return e04CulturalDemoObjects.find((o) => o.id === objectId) || null
}
