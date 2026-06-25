# Frontend Notes

## Current Approach

The MVP frontend is intentionally lightweight:

- server-rendered HTML through Jinja2;
- d3-geo for the static inline SVG Ukraine map;
- responsive HTML markup for daily bar charts;
- vanilla JavaScript for data loading and interactions.

This keeps the first implementation easy to inspect and avoids adding a frontend build system too early.

## Required Map Asset

The app reads normalized Ukraine GeoJSON here:

```text
server/web/static/geo/ukraine_regions.geojson
server/web/static/geo/ukraine_districts.geojson
```

Generate these stable files from the full-resolution `ukr_admin1.geojson` and `ukr_admin2.geojson` sources:

```text
python scripts/normalize_geojson.py
```

The JavaScript matches oblast GeoJSON features to API summaries by `region_id`.

District mode renders ADM2 geometry. Normalized district features keep:

- `district_id`: ADM2 pcode from the map source.
- `alertsua_location_uid`: alerts.in.ua raion UID matched from `data/reference/alertsua_raions.csv`.
- `region_id`: parent oblast UID for click/details fallback.

District fill and tooltip use `alertsua_location_uid` when cached raion data exists. If the selected period has no cached raion events, the district is gray and the tooltip says `Немає даних за цей період`.

## User Flow

1. Open `/`.
2. App requests `/api/regions/summary`.
3. Map regions are colored by selected metric mode.
4. User switches period or mode.
5. User can switch map level between regions and districts.
6. User can show/hide oblast labels.
7. User can use either a rolling `days` window or explicit `start_date` / `end_date`.
   In district mode, explicit dates are constrained to the last 31 days because the cached raion source is alerts.in.ua `month_ago`.
8. User clicks a region or district.
9. App requests `/api/regions/{region_id}/daily` for the parent oblast detail popup.
10. Detail popup updates metrics and the HTML chart.

## About And Update Journal

The `/about` route explains the product goal, map levels, metric modes, filters, and data sources.

The main map screen includes a compact update journal. It polls `/api/update-log` every 30 seconds so raion worker progress becomes visible while `scripts/sync_alertsua_raions.py --loop` is running.

The frontend supports Ukrainian and English through `server/web/static/js/i18n.js`. The selected language is stored in `localStorage` and shared by the map page and `/about`.
