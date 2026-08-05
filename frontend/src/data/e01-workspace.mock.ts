/**
 * OFFLINE / DEV ONLY — not used by workspace primary path (Phase B.1).
 * E01 workspace reads Demo API `/api/environment/e01/events` exclusively.
 * Kept for local offline experiments; do not re-wire as silent fallback.
 */
import type {
  E01EventDetail,
  E01EventsPayload,
  E01OpenPoint,
  E01PointTrendPayload,
} from '@/types/e01'

const openPoints: E01OpenPoint[] = [
  {
    pointId: 11001,
    pointCode: 'WP-TJ1-01',
    pointName: '一标废水排放口',
    sectionCode: 'TJ-1',
    sectionName: '第一合同段',
    locationText: 'K12+300 施工营地排水口',
    monitorCategory: 'WATER',
    monitorCategoryLabel: '水质',
    status: '整改中',
    caseStatus: 'RECTIFYING',
    discoveredAt: '2026-07-28T09:20:00+08:00',
    longitude: 114.08,
    latitude: 30.41,
    canLocate: true,
    primaryEventId: 21001,
    eventIds: [21001],
    factors: [
      {
        factorCode: 'SS',
        factorName: '悬浮物',
        detectedValue: 86,
        limitValue: 70,
        unit: 'mg/L',
        exceedMultiple: 1.23,
        resultId: 31001,
        eventId: 21001,
      },
    ],
  },
  {
    pointId: 11002,
    pointCode: 'AP-TJ2-03',
    pointName: '二标扬尘监测点',
    sectionCode: 'TJ-2',
    sectionName: '第二合同段',
    locationText: 'K48+150 路基作业面',
    monitorCategory: 'AIR',
    monitorCategoryLabel: '环境空气',
    status: '待复查',
    caseStatus: 'PENDING_REVIEW',
    discoveredAt: '2026-07-30T14:10:00+08:00',
    longitude: 114.22,
    latitude: 30.48,
    canLocate: true,
    primaryEventId: 21002,
    eventIds: [21002],
    factors: [
      {
        factorCode: 'PM10',
        factorName: 'PM10日均浓度',
        detectedValue: 168,
        limitValue: 150,
        unit: 'μg/m³',
        exceedMultiple: 1.12,
        resultId: 31002,
        eventId: 21002,
      },
    ],
  },
  {
    pointId: 11003,
    pointCode: 'NP-TJ3-02',
    pointName: '三标噪声敏感点',
    sectionCode: 'TJ-3',
    sectionName: '第三合同段',
    locationText: 'K96+800 居民点旁',
    monitorCategory: 'NOISE',
    monitorCategoryLabel: '噪声',
    status: '待销项',
    caseStatus: 'PENDING_CLOSURE',
    discoveredAt: '2026-07-25T21:40:00+08:00',
    longitude: 114.51,
    latitude: 30.58,
    canLocate: true,
    primaryEventId: 21003,
    eventIds: [21003],
    factors: [
      {
        factorCode: 'LAeqN',
        factorName: '夜间等效声级',
        detectedValue: 58,
        limitValue: 55,
        unit: 'dB(A)',
        exceedMultiple: 1.05,
        resultId: 31003,
        eventId: 21003,
      },
    ],
  },
]

export function getE01EventsMock(): E01EventsPayload {
  const waterCount = openPoints.filter((p) => p.monitorCategory === 'WATER').length
  const airCount = openPoints.filter((p) => p.monitorCategory === 'AIR').length
  const noiseCount = openPoints.filter((p) => p.monitorCategory === 'NOISE').length
  return {
    kpi: {
      exceedItemCount: openPoints.length,
      eventCount: openPoints.length,
      pointCount: openPoints.length + 9,
      openEventCount: openPoints.length,
    },
    overview: {
      totalOpenPoints: openPoints.length,
      waterCount,
      airCount,
      noiseCount,
      monitorPointCount: openPoints.length + 9,
      anomalyCount: openPoints.length,
      openCount: openPoints.length,
      riskLevel: '黄',
    },
    byCategory: [
      { name: '水质', value: waterCount },
      { name: '环境空气', value: airCount },
      { name: '噪声', value: noiseCount },
    ],
    byStatus: [
      { name: '整改中', value: 1 },
      { name: '待复查', value: 1 },
      { name: '待销项', value: 1 },
    ],
    events: [],
    openPoints,
    mapPoints: openPoints.map((p) => ({
      pointId: p.pointId,
      pointCode: p.pointCode,
      pointName: p.pointName,
      longitude: p.longitude,
      latitude: p.latitude,
      openCount: 1,
      eventCount: 1,
      eventIds: p.eventIds,
      primaryStatus: p.status,
      monitorCategory: p.monitorCategory,
    })),
    isDemo: true,
  }
}

export function getE01EventDetailMock(eventId: number): E01EventDetail | null {
  const point = openPoints.find((p) => p.eventIds.includes(eventId) || p.primaryEventId === eventId)
  if (!point) return null
  const factor = point.factors[0]
  return {
    summary: {
      eventId,
      eventCode: `E01-${eventId}`,
      title: `${point.pointName}超标`,
      pointId: point.pointId,
      pointCode: point.pointCode,
      pointName: point.pointName,
      sectionCode: point.sectionCode,
      sectionName: point.sectionName,
      locationText: point.locationText,
      monitorCategory: point.monitorCategory,
      monitorCategoryLabel: point.monitorCategoryLabel,
      factorCode: factor?.factorCode || '',
      factorName: factor?.factorName || '',
      detectedValue: factor?.detectedValue,
      limitValue: factor?.limitValue,
      unit: factor?.unit,
      exceedMultiple: factor?.exceedMultiple,
      status: point.status,
      caseStatus: point.caseStatus,
      isOpen: true,
      discoveredAt: point.discoveredAt,
      longitude: point.longitude,
      latitude: point.latitude,
      resultId: factor?.resultId || 0,
      resultCode: `R-${factor?.resultId || 0}`,
      sampleId: 1,
    },
    initialFactors: factor
      ? [
          {
            resultId: factor.resultId,
            resultCode: `R-${factor.resultId}`,
            testStage: '初检',
            factorCode: factor.factorCode,
            factorName: factor.factorName,
            judgement: '超标',
            detectedValue: factor.detectedValue,
            limitValue: factor.limitValue,
            unit: factor.unit,
            exceedMultiple: factor.exceedMultiple,
          },
        ]
      : [],
    allSampleFactors: [],
    rectificationRounds: [
      {
        id: 1,
        roundNo: 1,
        startedAt: point.discoveredAt,
        summary: '已下达整改通知，现场落实抑尘/隔音/沉淀措施',
        reviewStatus: '进行中',
      },
    ],
    retestRounds: [],
    statusHistory: [
      {
        sequenceNo: 1,
        toStatus: point.caseStatus || point.status,
        toStatusLabel: point.status,
        actionAt: point.discoveredAt,
        operatorName: '系统',
        comment: '监测超标立案',
      },
    ],
    evidence: [],
    closure: {
      status: point.caseStatus,
      statusLabel: point.status,
      openedAt: point.discoveredAt,
    },
  }
}

export function getE01PointTrendMock(
  pointId: number,
  factorCode?: string | null,
): E01PointTrendPayload | null {
  const point = openPoints.find((p) => p.pointId === pointId)
  if (!point) return null
  const factor =
    point.factors.find((f) => !factorCode || f.factorCode === factorCode) || point.factors[0]
  if (!factor) return null
  const base = Number(factor.detectedValue) || 50
  const limit = Number(factor.limitValue) || 40
  const series = [0, 1, 2, 3, 4].map((i) => {
    const valueNum = Math.round((base - i * 2 + (i % 2)) * 10) / 10
    return {
      at: `2026-07-${String(26 + i).padStart(2, '0')}T10:00:00+08:00`,
      value: valueNum,
      valueNum,
      limitValue: limit,
      judgement: valueNum > limit ? '超标' : '达标',
      exceeded: valueNum > limit,
      exceedMultiple: valueNum > limit ? Math.round((valueNum / limit) * 100) / 100 : null,
      resultId: factor.resultId + i,
      sampleId: i + 1,
      testStage: i === 4 ? '复测' : '日常',
    }
  })
  return {
    point: {
      pointId: point.pointId,
      pointCode: point.pointCode,
      pointName: point.pointName,
      monitorCategory: point.monitorCategory,
      monitorCategoryLabel: point.monitorCategoryLabel,
      sectionCode: point.sectionCode,
      sectionName: point.sectionName,
      locationText: point.locationText,
      status: point.status,
      discoveredAt: point.discoveredAt,
      longitude: point.longitude,
      latitude: point.latitude,
      primaryEventId: point.primaryEventId,
      factors: point.factors,
    },
    factor: {
      factorCode: factor.factorCode,
      factorName: factor.factorName,
      unit: factor.unit,
      limitValue: factor.limitValue,
      limitValueNum: limit,
    },
    series,
    stats: {
      sampleCount: series.length,
      exceedCount: series.filter((s) => s.exceeded).length,
      latestValue: series[series.length - 1]?.value,
      latestAt: series[series.length - 1]?.at,
      latestExceeded: Boolean(series[series.length - 1]?.exceeded),
    },
    factorOptions: point.factors.map((f) => ({
      factorCode: f.factorCode,
      factorName: f.factorName,
      unit: f.unit,
      sampleCount: series.length,
      exceedCount: 1,
    })),
  }
}
