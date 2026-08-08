import type { KpiGroup, KpiItem, KpiKey } from '@/types/dashboard'
import type { EsgHomeStatus, EsgIndicatorHomeStatus } from '@/types/esg-home'
import {
  computeG04HomeDemoDays,
  G04_HOME_DEMO_DISPLAY,
  KPI_HOME_CATALOG,
  KPI_HOME_HIDDEN_KEYS,
  type KpiHomeCode,
} from '@/data/kpi-catalog'
import { applyDisplayTestBaselinePin } from '@/data/display-test-baseline'

/** Homepage-only G04 display overlay: days + 天（does not call S01 / API). */
function applyG04HomeDemoDisplay(item: KpiItem): KpiItem {
  if (item.key !== 'G04') return item
  return {
    ...item,
    value: computeG04HomeDemoDays(),
    unit: '天',
    displayText: undefined,
    hint: G04_HOME_DEMO_DISPLAY.hint,
  }
}

function applyHomeValueOverlay(item: KpiItem): KpiItem {
  return applyDisplayTestBaselinePin(applyG04HomeDemoDisplay(item))
}

/** Overlay homepage display labels so API/mock old titles never surface on cards. */
export function applyKpiHomeCatalogLabels(groups: KpiGroup[]): KpiGroup[] {
  return groups.map((group) => ({
    ...group,
    items: group.items
      .filter((item) => !KPI_HOME_HIDDEN_KEYS.has(item.key as KpiHomeCode))
      .map((item) => {
        const code = item.key as KpiHomeCode
        const cat = KPI_HOME_CATALOG[code]
        if (!cat) return applyHomeValueOverlay(item)
        return applyHomeValueOverlay({
          ...item,
          label: cat.label,
          fullName: cat.fullName,
          unit: cat.unit ? cat.unit : item.unit,
        } as KpiItem)
      }),
  }))
}

function indicatorMap(status: EsgHomeStatus): Map<KpiKey, EsgIndicatorHomeStatus> {
  const map = new Map<KpiKey, EsgIndicatorHomeStatus>()
  for (const group of status.groups) {
    for (const ind of group.indicators) {
      map.set(ind.key, ind)
    }
  }
  return map
}

/** Merge ESG home summary into existing KPI groups (status + indicator cards). */
export function mergeEsgHomeIntoKpiGroups(
  groups: KpiGroup[],
  status: EsgHomeStatus,
): KpiGroup[] {
  const byKey = new Map(status.groups.map((g) => [g.key, g]))
  const inds = indicatorMap(status)

  return applyKpiHomeCatalogLabels(
    groups.map((group) => {
      const rollup = byKey.get(group.key)
      return {
        ...group,
        status: rollup?.status ?? group.status,
        items: group.items.map((item): KpiItem => {
          const ind = inds.get(item.key)
          if (!ind) return item
          return {
            ...item,
            label: ind.label || item.label,
            fullName: ind.fullName || item.fullName,
            value: ind.value,
            unit: ind.unit !== undefined ? ind.unit : item.unit,
            hint: ind.hint !== undefined ? ind.hint : item.hint,
            displayText: ind.displayText !== undefined ? ind.displayText : item.displayText,
            ledgerStatus: ind.ledgerStatus !== undefined ? ind.ledgerStatus : item.ledgerStatus,
          }
        }),
      }
    }),
  )
}
