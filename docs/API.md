# API

## `GET /api/regions/summary`

Returns region-level metrics for the map.

Query params:

- `days`: analysis window, default `7`.
- `mode`: `count`, `duration`, or `combined`.

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

Example:

```text
/api/regions/31/daily?days=7
```

## `GET /api/meta`

Returns dataset metadata:

- latest event timestamp;
- total event count;
- known regions;
- last refresh timestamp.
