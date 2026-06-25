# API

## `GET /api/regions/summary`

Returns region-level metrics for the map.

Query params:

- `days`: analysis window, default `7`.
- `mode`: `count`, `duration`, or `combined`.
- `start_date`: optional inclusive `YYYY-MM-DD` start date.
- `end_date`: optional inclusive `YYYY-MM-DD` end date.

If both `start_date` and `end_date` are provided, they override the rolling `days` window.

Example:

```text
/api/regions/summary?days=7&mode=combined
```

Response item:

```json
{
  "region_id": "31",
  "region_name": "м. Київ",
  "alert_count": 4,
  "total_duration_minutes": 320.0,
  "average_duration_minutes": 80.0,
  "metric_value": 0.72
}
```

## `GET /api/regions/{region_id}/daily`

Returns daily statistics for a selected region.

Query params:

- `days`: analysis window, default `7`.
- `start_date`: optional inclusive `YYYY-MM-DD` start date.
- `end_date`: optional inclusive `YYYY-MM-DD` end date.

Example:

```text
/api/regions/31/daily?days=7
```

## `GET /api/raions/summary`

Returns raion-level metrics from the local alerts.in.ua cache only. This endpoint never calls alerts.in.ua directly.

Query params:

- `days`: analysis window, default `7`.
- `mode`: `count`, `duration`, or `combined`.
- `start_date`: optional inclusive `YYYY-MM-DD` start date.
- `end_date`: optional inclusive `YYYY-MM-DD` end date.

Response item:

```json
{
  "location_uid": "39",
  "location_title": "Луцький район",
  "oblast_uid": "8",
  "oblast_name": "Волинська область",
  "alert_count": 2,
  "total_duration_minutes": 180.0,
  "average_duration_minutes": 90.0,
  "metric_value": 0.42
}
```

## `GET /api/raions/{location_uid}/daily`

Returns daily local-cache statistics for one alerts.in.ua raion.

## `GET /api/raions/sync-status`

Returns local oblast-based sync state rows for alerts.in.ua history requests. The worker requests oblast history and extracts raion records from each response.

## `GET /api/update-log`

Returns a compact local update journal for the UI. It combines:

- the latest oblast dataset refresh;
- current raion worker sync state;
- latest synced/failed/pending oblast sync rows.

The endpoint reads local DB state only and never calls alerts.in.ua.

## `GET /api/meta`

Returns dataset metadata:

- latest event timestamp;
- total event count;
- known regions;
- last refresh timestamp.
