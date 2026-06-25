# Project Context

## Name

- Public name: `UAir-raid-analytics`
- Python package name: `server`

## Product Goal

Build a simple web application where regular users can explore historical air raid alert statistics across Ukrainian regions.

The first screen should be a map of Ukraine. Region color intensity should help users compare regions quickly. Clicking a region opens detailed daily statistics.

## MVP Decisions

- Use Python as the main language.
- Use historical data only.
- Do not show current active alerts in the MVP.
- Use Vadimkin dataset as the primary source.
- Use alerts.in.ua only through an explicit cached raion sync worker.
- Use SQLite for local MVP storage.
- Calculate aggregates and combined index on request.
- Do not add tests or sample dataset at this stage.
- Do not abstract for other countries. The product is Ukraine-specific.
- Do not call alerts.in.ua from frontend or during user API requests.

## Metric Modes

The map supports three modes:

- `count`: number of alerts.
- `duration`: total alert duration.
- `combined`: normalized count and duration with equal weights.

Current formula:

```text
combined = normalized_alert_count * 0.5 + normalized_total_duration * 0.5
```

The formula is intentionally isolated in the analytics layer.

## Map Levels

- `regions`: ADM1 oblast map, default mode.
- `districts`: ADM2 raion map, loaded only after the user switches map level.

District geometry keeps parent `region_id`, so clicking a district opens the same oblast detail popup. When cached raion summaries exist, district fill and tooltip use raion metrics; otherwise they fall back to parent-oblast metrics.
