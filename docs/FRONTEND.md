# Frontend Notes

## Current Approach

The MVP frontend is intentionally lightweight:

- server-rendered HTML through Jinja2;
- Leaflet for the Ukraine map;
- Chart.js for daily bar charts;
- vanilla JavaScript for data loading and interactions.

This keeps the first implementation easy to inspect and avoids adding a frontend build system too early.

## Required Map Asset

Add Ukraine regions GeoJSON here:

```text
uair_raid_analytics/web/static/geo/ukraine_regions.geojson
```

The JavaScript tries to match GeoJSON features by one of these properties:

- `region_id`
- `id`
- `uid`
- `name`
- `NAME_1`
- `shapeName`

Best future improvement: normalize the GeoJSON during setup so each feature has `region_id` matching `uair_raid_analytics/regions.py`.

## User Flow

1. Open `/`.
2. App requests `/api/regions/summary`.
3. Map regions are colored by selected metric mode.
4. User switches period or mode.
5. User clicks a region.
6. App requests `/api/regions/{region_id}/daily`.
7. Side panel updates metrics and chart.
