import type { KpiHomeCode } from '@/data/kpi-catalog'
import type { KpiItem } from '@/types/dashboard'

/**
 * 首页 L1 展示基线（TEST-BASELINE-20260806）。
 * 用于固定领导看板数字，避免 S01/G04 等按自然日滚动与验收文档不一致。
 * 仅作用于首页卡片展示，不改 API / 二级下钻口径。
 */
export const DISPLAY_TEST_BASELINE_AS_OF = '2026-08-06'

type BaselinePin = Pick<KpiItem, 'value' | 'unit' | 'displayText'>

/** 与 docs/ESG展示测试数据与回退说明_20260806.md 一致 */
export const DISPLAY_TEST_BASELINE_L1: Partial<Record<KpiHomeCode, BaselinePin>> = {
  E01: { value: 0, unit: '项', displayText: '0项' },
  E02: { value: 0, unit: '项', displayText: '0项' },
  E03: { value: 3, unit: '项', displayText: '3项' },
  E04: { value: 0, unit: '项', displayText: '0项' },
  S01: { value: 90, unit: '天', displayText: '90天' },
  S02: { value: 100, unit: '%', displayText: '100%' },
  S03: { value: 0, unit: '件', displayText: '0件' },
  S04: { value: 4, unit: '项', displayText: '4项' },
  G01: { value: 100, unit: '%', displayText: '100%' },
  G02: { value: 100, unit: '%', displayText: '100%' },
  G03: { value: 100, unit: '%', displayText: '3/3 100%' },
  G04: { value: 90, unit: '天', displayText: '90天' },
}

export function applyDisplayTestBaselinePin(item: KpiItem): KpiItem {
  const pin = DISPLAY_TEST_BASELINE_L1[item.key as KpiHomeCode]
  if (!pin) return item
  return {
    ...item,
    value: pin.value,
    unit: pin.unit,
    displayText: pin.displayText,
  }
}
