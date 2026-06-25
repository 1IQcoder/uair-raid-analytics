# UAir-raid-analytics

Python-first MVP for historical air raid alert analytics in Ukraine.

The project uses a prepared historical dataset as the main data source, stores normalized alert events in a local SQLite database, and exposes map/chart analytics through a FastAPI application.

## MVP Scope

- Historical data only.
- No real-time active alert display.
- Primary source: Vadimkin Ukrainian Air Raid Sirens Dataset.
- Optional validation/fallback source: alerts.in.ua API.
- Default analytics period: latest 7 days available in the local dataset.
- Runtime calculation of map metrics, including the combined intensity index.

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
- The app reads normalized Ukraine regions GeoJSON from:

```text
server/web/static/geo/ukraine_regions.geojson
```

- Regenerate it from the bundled full-resolution geoBoundaries file with:

```bash
python scripts/normalize_geojson.py
```

## Documentation

Project implementation context is stored in `docs/`.
