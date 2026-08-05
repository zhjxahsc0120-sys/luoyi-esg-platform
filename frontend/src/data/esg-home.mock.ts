/**
 * Phase A — ESG homepage summary mock.
 * Shape mirrors planned Demo API GET /api/dashboard/esg-home-status.
 * Swap: api.getEsgHomeStatus() prefers HTTP, falls back here.
 */
import type { EsgHomeStatus } from '@/types/esg-home'
import { KPI_HOME_CATALOG } from '@/data/kpi-catalog'
import {
  complianceMetrics,
  effectivenessItems,
  safeguardItems,
  warningListItems,
} from '@/data/dashboard.mock'

function cat(key: keyof typeof KPI_HOME_CATALOG) {
  return KPI_HOME_CATALOG[key]
}

export const esgHomeStatusMock: EsgHomeStatus = {
  source: 'mock',
  updatedAt: '2026-08-04T00:00:00+08:00',
  ryb: { red: 3, yellow: 5, blue: 8, total: 16 },
  complianceMetrics: [...complianceMetrics],
  effectiveness: [...effectivenessItems],
  safeguards: [...safeguardItems],
  warningItems: [...warningListItems],
  groups: [
    {
      key: 'E',
      title: '环境环保组',
      status: '风险 4 · 红2 黄1 蓝1',
      riskCount: 4,
      ryb: { red: 2, yellow: 1, blue: 1 },
      indicators: [
        {
          key: 'E01',
          label: cat('E01').label,
          fullName: cat('E01').fullName,
          value: 2,
          unit: cat('E01').unit,
          statusTone: 'attention',
        },
        {
          key: 'E02',
          label: cat('E02').label,
          fullName: cat('E02').fullName,
          value: 4,
          unit: cat('E02').unit,
          statusTone: 'attention',
        },
        {
          key: 'E03',
          label: cat('E03').label,
          fullName: cat('E03').fullName,
          value: 4,
          unit: cat('E03').unit,
          statusTone: 'attention',
        },
        {
          key: 'E04',
          label: cat('E04').label,
          fullName: cat('E04').fullName,
          value: 0,
          unit: cat('E04').unit,
          hint: '文物调查已完成 · 保护对象 0 · 风险正常',
          statusTone: 'normal',
        },
      ],
    },
    {
      key: 'S',
      title: '社会责任组',
      status: '风险 1 · 红0 黄0 蓝1',
      riskCount: 1,
      ryb: { red: 0, yellow: 0, blue: 1 },
      indicators: [
        {
          key: 'S01',
          label: cat('S01').label,
          fullName: cat('S01').fullName,
          value: 368,
          unit: cat('S01').unit,
          statusTone: 'normal',
        },
        {
          key: 'S02',
          label: cat('S02').label,
          fullName: cat('S02').fullName,
          value: 8,
          unit: cat('S02').unit,
          statusTone: 'attention',
        },
        {
          key: 'S03',
          label: cat('S03').label,
          fullName: cat('S03').fullName,
          value: 2,
          unit: cat('S03').unit,
          hint: '工资发放达标率：暂无评价数据',
          statusTone: 'attention',
        },
        {
          key: 'S04',
          label: cat('S04').label,
          fullName: cat('S04').fullName,
          value: 3,
          unit: cat('S04').unit,
          hint: '投诉 2 · 信访 1 · 化解率：暂无有效数据',
          statusTone: 'attention',
        },
      ],
    },
    {
      key: 'G',
      title: '治理合规组',
      status: '风险 3 · 红1 黄1 蓝1',
      riskCount: 3,
      ryb: { red: 1, yellow: 1, blue: 1 },
      indicators: [
        {
          key: 'G01',
          label: cat('G01').label,
          fullName: cat('G01').fullName,
          value: '2/12',
          unit: '17%',
          hint: '审批 2/7 · 许可 0/5',
          statusTone: 'risk',
        },
        {
          key: 'G02',
          label: cat('G02').label,
          fullName: cat('G02').fullName,
          value: '0/8',
          unit: '0%',
          hint: '编制 1/8 · 审批通过 0/8 · 有审批文件 0/8',
          statusTone: 'risk',
        },
        {
          key: 'G03',
          label: cat('G03').label,
          fullName: cat('G03').fullName,
          value: 0,
          unit: cat('G03').unit,
          displayText: '台账待接入',
          ledgerStatus: 'pending',
          hint: '变更/审批/实施：暂无有效数据',
          statusTone: 'pending',
        },
        {
          key: 'G04',
          label: cat('G04').label,
          fullName: cat('G04').fullName,
          value: 9,
          unit: cat('G04').unit,
          statusTone: 'attention',
        },
      ],
    },
  ],
}

export function getEsgHomeStatusMock(): EsgHomeStatus {
  return {
    ...esgHomeStatusMock,
    groups: esgHomeStatusMock.groups.map((g) => ({
      ...g,
      ryb: { ...g.ryb },
      indicators: g.indicators.map((i) => ({ ...i })),
    })),
    complianceMetrics: esgHomeStatusMock.complianceMetrics.map((m) => ({ ...m })),
    effectiveness: esgHomeStatusMock.effectiveness.map((e) => ({ ...e })),
    safeguards: [...esgHomeStatusMock.safeguards],
    warningItems: esgHomeStatusMock.warningItems.map((w) => ({ ...w })),
    ryb: { ...esgHomeStatusMock.ryb },
  }
}
