# UAir-raid-analytics

### Table of Contents

- [About project](#about-project)
- [AI-First Development](#ai-first-development)
- [Technology Stack](#technology-stack)
- [How the Data Works](#how-the-data-works)
- [Quick Start](#quick-start)
- [Raion Worker](#raion-worker)
- [Useful Commands](#useful-commands)
- [Documentation](#documentation)

### The finished product is available at: **https://uair-raid-analytics.potuzhnist.xyz/**

## About project

UAir-raid-analytics is a web application for exploring historical air raid alert statistics in Ukraine. It visualizes data on an interactive map, lets users switch between oblast-level and raion-level views, and compares regions by alert count, total alert duration, or a combined intensity index. The main goal is to make air raid alert data easier to inspect visually: users can quickly see where alerts happened more often, where they lasted longer, how the situation changes across a selected period, and which regions have the highest load for the chosen metric.

The project provides two map levels:

- **Oblasts** - the main mode, based on a broader historical open dataset.
- **Raions** - a more detailed map that uses locally cached alerts.in.ua data for the latest month.

## AI-First Development

This project was created from the beginning with AI assistance only: **ChatGPT Plus + Codex**. The architecture, backend, frontend, map rendering, synchronization worker, documentation, and iterative bug fixes were all implemented through AI conversations.

The `ai_conversations/` directory contains the full AI conversations used to build the application. It is part of the project history: it shows not only the final code, but also the decision-making process, debugging steps, and gradual refinement of the product.

## Technology Stack

- **Python 3.12+**
- **FastAPI** - backend and API
- **SQLAlchemy** - database access layer
- **SQLite** - local storage for normalized alert events
- **Jinja2** - HTML templates
- **Vanilla JavaScript** - frontend logic without a frontend framework
- **D3 Geo** - rendering GeoJSON as inline SVG
- **HTML/CSS SVG map UI** - no Leaflet, OpenStreetMap, or external tile providers
- **httpx** - alerts.in.ua API client for the background worker
- **pandas** - CSV dataset processing

## How the Data Works

### Oblast statistics

The main historical data source is the **Vadimkin Ukrainian Air Raid Sirens Dataset**. The `scripts/update_dataset.py` script downloads CSV data from configured URLs, normalizes alert events, and writes them into a local SQLite database.

When a user opens the map or changes filters, the backend does not rely on a precomputed table for every possible mode. Instead, it reads local events from the database and calculates the requested metrics at request time:

- alert period count;
- total alert duration;
- average alert duration;
- combined intensity index.

For oblast mode, the rule is: if an alert is active in at least one raion inside an oblast, the whole oblast is treated as being under alert. When there is no active alert anywhere inside the oblast, that continuous alert period is considered finished.

### Raion statistics and the alerts.in.ua worker

Raion-level data comes from the official **alerts.in.ua** API, but the frontend never calls that API directly. Instead, the project has a separate background worker:

```bash
python scripts/sync_alertsua_raions.py --loop
```

The worker uses a local reference file:

```text
data/reference/alertsua_raions.csv
```

This file contains known raions, their UIDs, oblast mapping, and an `enabled` flag. A key technical detail is that the alerts.in.ua history endpoint does not work directly with raion UIDs. The worker therefore requests history by **oblast UID**, then extracts only records where `location_type == "raion"` and `alert_type == "air_raid"`.

Fetched raion events are cached in the local database. User-facing raion API endpoints read only the local database:

- `/api/raions/summary`
- `/api/raions/{location_uid}/daily`
- `/api/raions/sync-status`

This design exists to:

- keep `ALERTS_IN_UA_TOKEN` out of the browser;
- avoid external API calls during user requests;
- respect alerts.in.ua rate limits;
- provide fast responses from the local cache.

Worker autostart is disabled by default. Raion synchronization must be started explicitly.

## Quick Start

### 1. Clone the repository

```bash
git clone <repository-url>
cd uair_raid_analytics
```

### 2. Create a virtual environment and install dependencies

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

### 3. Configure `.env`

Copy the example file:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Base `.env`:

```env
UAIR_APP_NAME=UAir-raid-analytics
UAIR_DEBUG=false
UAIR_DATABASE_URL=sqlite:///./data/processed/uair_raid_analytics.sqlite3
UAIR_PRIMARY_DATASET_URL=https://raw.githubusercontent.com/Vadimkin/ukrainian-air-raid-sirens-dataset/main/datasets/official_data_uk.csv
UAIR_SECONDARY_DATASET_URL=https://raw.githubusercontent.com/Vadimkin/ukrainian-air-raid-sirens-dataset/main/datasets/volunteer_data_uk.csv

ALERTS_IN_UA_TOKEN=
ALERTS_IN_UA_HISTORY_MIN_INTERVAL_SECONDS=35
ALERTS_IN_UA_HISTORY_DAILY_LIMIT=500
ALERTS_IN_UA_WORKER_ENABLED=false
```

The alerts.in.ua token is not required for oblast mode. To synchronize raion data, obtain an alerts.in.ua token and set:

```env
ALERTS_IN_UA_TOKEN=your_token_here
```

Do not lower `ALERTS_IN_UA_HISTORY_MIN_INTERVAL_SECONDS` below 30 seconds. The default value of 35 seconds is chosen because the alerts.in.ua history endpoint is limited to 2 requests per minute.

### 4. Download and process the main dataset

```bash
python scripts/update_dataset.py
```

### 5. Run the application

```bash
uvicorn server.main:app --reload
```

The local app will be available at:

```text
http://127.0.0.1:8000
```

The project description page:

```text
http://127.0.0.1:8000/about
```

## Raion Worker

Preview which oblasts will be synchronized:

```bash
python scripts/sync_alertsua_raions.py --dry-run --limit 3
```

Synchronize one oblast:

```bash
python scripts/sync_alertsua_raions.py --once
```

Run continuous synchronization:

```bash
python scripts/sync_alertsua_raions.py --loop
```

The worker does not request history by raion UID. It requests unique oblast UIDs from `data/reference/alertsua_raions.csv`, then extracts raion records from each oblast response. One full cycle takes roughly 15-16 minutes because the worker keeps a safe delay between requests.

## Useful Commands

Regenerate normalized GeoJSON files:

```bash
python scripts/normalize_geojson.py
```

Check Python files for syntax errors:

```bash
python -m compileall -q server scripts
```

Run the dataset update entrypoint:

```bash
uair-update-dataset
```

## Documentation

More technical context is stored in `docs/`, including:

- architecture;
- data pipeline;
- API endpoints;
- frontend logic;
- problem and solution notes.

Ukrainian version: [README.uk.md](README.uk.md)
