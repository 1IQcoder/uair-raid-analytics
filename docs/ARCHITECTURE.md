# Architecture

## Stack

- Backend: FastAPI.
- Data processing: Pandas.
- Storage: SQLite.
- ORM: SQLAlchemy.
- Web shell: Jinja2, d3-geo, inline SVG, vanilla JavaScript.

## Structure

```text
server/
  api/          HTTP API routes
  analytics/    runtime aggregation and metrics
  data/         dataset refresh and normalization
  web/          HTML templates and static frontend assets
  config.py     environment-based settings
  database.py   SQLAlchemy engine/session setup
  models.py     database tables
  regions.py    Ukraine region reference
```

## Data Flow

```mermaid
flowchart TD
  A["Vadimkin CSV"] --> B["update_dataset.py"]
  B --> C["Normalize events"]
  C --> D["SQLite alert_events"]
  D --> E["Runtime analytics"]
  E --> F["FastAPI endpoints"]
  F --> G["SVG map and HTML charts"]
```

## Precompute Strategy

MVP does not precompute aggregates.

This keeps the implementation small and allows the combined index formula to change easily. If runtime queries become slow later, add a summary table behind the same API response shape.
