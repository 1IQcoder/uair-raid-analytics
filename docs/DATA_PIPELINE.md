# Data Pipeline

## Primary Source

Primary source is the Vadimkin Ukrainian Air Raid Sirens Dataset.

Configured URLs live in `.env`:

```text
UAIR_PRIMARY_DATASET_URL=
UAIR_SECONDARY_DATASET_URL=
```

By default, the refresh script loads only the primary source. Use `--include-secondary` only if the project intentionally wants to merge official and volunteer data.

## Update Command

```bash
python scripts/update_dataset.py
```

The command:

1. Initializes the SQLite database.
2. Downloads configured CSV source.
3. Normalizes rows into internal alert events.
4. Replaces current `alert_events` table content.
5. Writes a refresh log entry.

For MVP, full refresh is preferred over incremental sync. It is simpler and safer while the dataset size is still manageable.

## Internal Event Fields

```text
source
source_event_id
region_id
region_name
started_at
finished_at
duration_minutes
alert_type
raw_location_type
```

## Region Scope

The application is Ukraine-specific.

The current reference list is stored in `server/regions.py` and follows Ukrainian regions plus Kyiv, Sevastopol, and Crimea. Future support for districts or communities should extend this reference instead of generalizing the product to other countries.

## alerts.in.ua Raion Cache

Oblast history still comes from the Vadimkin dataset. Raion-level history is cached from the official alerts.in.ua API by an explicit worker CLI.

Frontend and user-facing API requests must never call alerts.in.ua. They read local SQLite tables only.

Important endpoint behavior:

- alerts.in.ua history endpoint works with oblast UIDs.
- Raion UIDs are not valid request targets for `month_ago` history and may return HTTP 404.
- The worker requests `/v1/regions/{oblast_uid}/alerts/month_ago.json`.
- It extracts only response records where `location_type == "raion"` and `alert_type == "air_raid"`.
- Hromada/city records are ignored for raion analytics.

Required `.env` values:

```text
ALERTS_IN_UA_TOKEN=
ALERTS_IN_UA_HISTORY_MIN_INTERVAL_SECONDS=35
ALERTS_IN_UA_HISTORY_DAILY_LIMIT=500
ALERTS_IN_UA_WORKER_ENABLED=false
```

Default worker autostart is disabled. Do not lower `ALERTS_IN_UA_HISTORY_MIN_INTERVAL_SECONDS` below 30 seconds. The project default is 35 seconds because the alerts.in.ua history endpoint is limited to 2 requests per minute.

Reference raions are stored in:

```text
data/reference/alertsua_raions.csv
```

Required columns:

```text
location_uid,location_title,oblast_uid,oblast_name,enabled
```

Only rows with `enabled == true` are used. The reference file is used to:

- validate known raion UIDs;
- map raion UID to oblast metadata;
- build the unique enabled oblast UID list that the worker requests.

Manual commands:

```bash
python scripts/sync_alertsua_raions.py --dry-run --limit 3
python scripts/sync_alertsua_raions.py --once
python scripts/sync_alertsua_raions.py --loop
```

`--limit N` limits oblast requests, not raion rows.

Recommended usage:

1. Validate the reference file and request order:

```bash
python scripts/sync_alertsua_raions.py --dry-run --limit 3
```

2. Sync one oblast history response:

```bash
python scripts/sync_alertsua_raions.py --once
```

3. Continue a full cycle manually:

```bash
python scripts/sync_alertsua_raions.py --loop
```

The first request after a fresh state is the first pending oblast from the enabled reference grouping. In the current reference order this is `13` (`Івано-Франківська область`). The endpoint is `month_ago`, so the returned history is the API's last-month window for that oblast. A full cycle currently has 24 unique enabled oblast requests.

Worker behavior:

1. Load enabled raions from the reference CSV.
2. Group enabled raions by `oblast_uid`.
3. Create/update oblast-based local sync state rows.
4. Pick pending oblasts first, then the oldest `last_synced_at`.
5. Request oblast `month_ago` history with at least 35 seconds between requests.
6. Filter response alerts to raion air-raid records.
7. Upsert events into `alertsua_raion_events`.
8. Update `alertsua_sync_state`.
9. Pause at least 10 minutes on HTTP 429.
10. Stop immediately on HTTP 401/403.

Because the worker syncs oblasts instead of raions, a full cycle is roughly 25-27 requests. At 35 seconds per request this takes about 15-16 minutes.

Keep the alerts.in.ua token in `.env` only. Never log or expose it.
