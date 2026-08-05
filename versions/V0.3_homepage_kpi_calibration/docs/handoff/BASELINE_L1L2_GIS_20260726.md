# Baseline: L1/L2 GIS Dashboard — 2026-07-26

## Protected tag

- **Tag:** `baseline/l1-l2-gis-20260726`
- **Branch at pin:** `trae/workspace-nav-s02s03`
- **Purpose:** Freeze the product-complete Dashboard L1/L2 + GIS + related workspace/server state so later work does not overwrite finished pages without explicit scope.

## What this baseline protects

- Dashboard L1/L2 layout and KPI/master shell
- GIS overview (Cesium module, home GIS section, preview)
- e01 / e02 / e03 / s02 workspace panels and map summary cards
- Panels chart fixes (BarMetricChart, RingChart, carbon/compliance panels)
- HeaderNav「数据填报」entry and workspace shell (nav/home/page)
- Related server APIs/payloads (dashboard, monthly report, carbon benefit, mysql_api, e_group, intelligent_ingestion, migrations)
- Recovery/check handoff notes under `_handoff/` for this date

## Restoration

```bash
git fetch --tags
git switch --detach baseline/l1-l2-gis-20260726
# or create a recovery branch:
git switch -c restore/l1-l2-gis-20260726 baseline/l1-l2-gis-20260726
```

## Trae / agent rule

**Do not** overwrite Dashboard GIS L1/L2, home layout, or GIS module behavior unless the Issue explicitly scopes that change and references this baseline. Prefer additive work on new branches; restore from this tag if regressions appear.

See also: `_handoff/Cursor_L1L2_GIS完整态恢复说明_20260726.md`, `_handoff/Cursor_完整态校核_20260726.md`, `_handoff/NEXT_FOR_TRAE.md`.
