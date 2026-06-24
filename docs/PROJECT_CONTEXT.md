# Project Context

## Name

- Public name: `UAir-raid-analytics`
- Python package name: `uair_raid_analytics`

## Product Goal

Build a simple web application where regular users can explore historical air raid alert statistics across Ukrainian regions.

The first screen should be a map of Ukraine. Region color intensity should help users compare regions quickly. Clicking a region opens detailed daily statistics.

## MVP Decisions

- Use Python as the main language.
- Use historical data only.
- Do not show current active alerts in the MVP.
- Use Vadimkin dataset as the primary source.
- Keep alerts.in.ua API as optional validation/fallback.
- Use SQLite for local MVP storage.
- Calculate aggregates and combined index on request.
- Do not add tests or sample dataset at this stage.
- Do not abstract for other countries. The product is Ukraine-specific.

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
