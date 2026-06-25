# Next Steps for Codex

Use this order for implementation continuation.

## 1. Verify Real Dataset Columns

Run:

```bash
python scripts/update_dataset.py
```

If the Vadimkin CSV column names differ from current aliases, update `COLUMN_ALIASES` in:

```text
server/data/update_dataset.py
```

Do not add sample data unless explicitly requested.

## 2. Regenerate Ukraine Regions GeoJSON

The frontend uses a stable normalized file:

```text
server/web/static/geo/ukraine_regions.geojson
```

Regenerate it from the bundled full-resolution `ukr_admin1.geojson` source:

```bash
python scripts/normalize_geojson.py
```

## 3. Improve Dataset Refresh

Current implementation uses full refresh.

Future option:

- keep full refresh for simplicity;
- or add incremental import by `source_event_id` and timestamps;
- or add daily automation through cron/GitHub Actions.

## 4. Add Optional alerts.in.ua Validation

Create a separate module for validation only:

```text
server/data/alerts_in_ua_validation.py
```

Token must come from `.env`.

## 5. Add Precompute Later Only If Needed

Current runtime aggregation is acceptable for MVP.

If performance becomes a problem:

- add `region_daily_aggregates` table;
- refresh it after dataset update;
- keep the existing API response format unchanged.
