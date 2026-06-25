# UAir-raid-analytics

Python-first MVP for historical air raid alert analytics in Ukraine.

The project uses a prepared historical dataset as the main data source, stores normalized alert events in a local SQLite database, and exposes map/chart analytics through a FastAPI application.

## MVP Scope

- Historical data only.
- No real-time active alert display.
- Primary source: Vadimkin Ukrainian Air Raid Sirens Dataset.
- Cached raion-level source: alerts.in.ua API, synchronized only by an explicit background CLI.
- Default analytics period: latest 7 days available in the local dataset.
- Runtime calculation of map metrics, including the combined intensity index.
- Region and district map modes. District mode uses cached raion data when available.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
python scripts/update_dataset.py
uvicorn server.main:app --reload
```

Open the app at `http://127.0.0.1:8000`.

## Important Notes

- The repository does not include a sample dataset.
- The update script downloads CSV data from configured URLs and writes normalized events to SQLite.
- The app reads normalized Ukraine GeoJSON from:

```text
server/web/static/geo/ukraine_regions.geojson
server/web/static/geo/ukraine_districts.geojson
```

- Regenerate them from the bundled full-resolution `ukr_admin1.geojson` and `ukr_admin2.geojson` files with:

```bash
python scripts/normalize_geojson.py
```

- Raion-level alerts.in.ua sync is explicit and disabled by default:

```bash
python scripts/sync_alertsua_raions.py --dry-run --limit 3
python scripts/sync_alertsua_raions.py --once
```

- User-facing API requests always read local SQLite data. They never call alerts.in.ua directly.
- The alerts.in.ua worker requests history by oblast UID and extracts raion records from the response; it does not request history by raion UID.

## Documentation

Project implementation context is stored in `docs/`.
