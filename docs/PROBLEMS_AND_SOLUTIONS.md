# Problems And Solutions

## Package Rename

Problem: the project originally referenced the old internal package path.

Solution: the backend package is now `server`, and docs/config/scripts should use `server.main:app` and `server/...` paths.

## ADM1 GeoJSON Mismatch

Problem: the first map file used different property names than the API summary data.

Solution: `scripts/normalize_geojson.py` adds stable `region_id` and `region_name` properties to normalized GeoJSON.

## Poor Coastline Rendering

Problem: simplified GeoJSON made Crimea and the southern coastline look too coarse.

Solution: switched to full-resolution `ukr_admin1.geojson`, normalized it to `ukraine_regions.geojson`, and rewound rings for d3-geo rendering.

## D3 Rendered A Filled Rectangle

Problem: d3-geo interpreted standard GeoJSON ring orientation as the inverse polygon.

Solution: the normalizer rewinds exterior/interior rings for d3 rendering.

## Daily Duration Over 24 Hours

Problem: raw overlapping events were summed directly, and multi-day events were bucketed by start date.

Solution: analytics now clips intervals to the requested window/day and merges overlaps before calculating duration.

## Crimea And Luhansk Looked Empty

Problem: permanent-alert territories had no normal finished event history in the dataset window.

Solution: the analytics layer injects permanent active intervals for Crimea and Luhansk from `2022-02-24`.

## District Mode Before Raion Data

Problem: ADM2 geometry exists before reliable raion alert history is loaded.

Solution: district mode renders raion geometry immediately, keeps oblast click behavior, and falls back to parent-oblast metrics until cached raion summaries are available.

## alerts.in.ua Rate Limit Risk

Problem: the history endpoint is limited to 2 requests per minute.

Solution: the worker waits at least 35 seconds between requests, pauses at least 10 minutes after HTTP 429, and is disabled by default.

## alerts.in.ua Raion History 404

Problem: `/v1/regions/{raion_uid}/alerts/month_ago.json` can return HTTP 404 because the history endpoint expects oblast UIDs, not raion UIDs.

Solution: the worker groups enabled reference raions by `oblast_uid`, requests oblast history, filters returned alerts to `location_type == "raion"` and `alert_type == "air_raid"`, then stores those raion events locally.
