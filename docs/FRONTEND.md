# Frontend Notes

## Current Approach

The MVP frontend is intentionally lightweight:

- server-rendered HTML through Jinja2;
- d3-geo for the static inline SVG Ukraine map;
- responsive HTML markup for daily bar charts;
- vanilla JavaScript for data loading and interactions.

This keeps the first implementation easy to inspect and avoids adding a frontend build system too early.

## Required Map Asset

The app reads normalized Ukraine regions GeoJSON here:

```text
server/web/static/geo/ukraine_regions.geojson
```

Generate this stable file from the full-resolution `ukr_admin1.geojson` source:

```text
python scripts/normalize_geojson.py
```

The JavaScript matches GeoJSON features to API summaries by `region_id`.

## User Flow

1. Open `/`.
2. App requests `/api/regions/summary`.
3. Map regions are colored by selected metric mode.
4. User switches period or mode.
5. User clicks a region.
6. App requests `/api/regions/{region_id}/daily`.
7. Detail popup updates metrics and the HTML chart.
