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

The current reference list is stored in `uair_raid_analytics/regions.py` and follows Ukrainian regions plus Kyiv, Sevastopol, and Crimea. Future support for districts or communities should extend this reference instead of generalizing the product to other countries.

## alerts.in.ua Role

alerts.in.ua is not the primary source in the MVP.

Use it later only for:

- spot validation;
- fallback checks;
- comparing latest data after a dataset refresh.

Keep the token in `.env` only.
