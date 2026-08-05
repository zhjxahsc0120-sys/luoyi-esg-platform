import type { KpiGroup, KpiItem, KpiKey } from '@/types/dashboard'
import type { EsgHomeStatus, EsgIndicatorHomeStatus } from '@/types/esg-home'
import { KPI_HOME_CATALOG, type KpiHomeCode } from '@/data/kpi-catalog'

/** Overlay frozen homepage labels so API/mock old semantics never surface to leaders. */
export function applyKpiHomeCatalogLabels(groups: KpiGroup[]): KpiGroup[] {
  return groups.map((group) => ({
    ...group,
    items: group.items.map((item) => {
      const code = item.key as KpiHomeCode
      const cat = KPI_HOME_CATALOG[code]
      if (!cat) return item
      return {
        ...item,
        label: cat.label,
        fullName: cat.fullName,
        unit: cat.unit ? cat.unit : item.unit,
      }
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
