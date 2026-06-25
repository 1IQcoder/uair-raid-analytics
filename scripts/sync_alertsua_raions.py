from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

VENV_PYTHON = PROJECT_ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin") / (
    "python.exe" if os.name == "nt" else "python"
)
if VENV_PYTHON.exists() and Path(sys.executable).resolve() != VENV_PYTHON.resolve():
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), *sys.argv])

from server.config import settings
from server.data.alertsua_reference import enabled_oblasts_from_raions, load_enabled_raions


def dry_run(limit: int | None) -> None:
    raions = load_enabled_raions()
    oblasts = enabled_oblasts_from_raions(raions)
    selected = oblasts[:limit] if limit else oblasts
    print(f"Loaded {len(raions)} enabled alerts.in.ua raions from reference CSV.")
    print(f"Will request {len(oblasts)} unique oblast history endpoints.")
    for oblast in selected:
        print(f"{oblast.oblast_uid}: {oblast.oblast_name}")
    if not settings.alerts_in_ua_token:
        print("ALERTS_IN_UA_TOKEN is not configured; sync requests will be skipped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync alerts.in.ua raion history cache.")
    parser.add_argument("--dry-run", action="store_true", help="Validate reference CSV without network calls.")
    parser.add_argument("--once", action="store_true", help="Sync the next one oblast and exit.")
    parser.add_argument("--loop", action="store_true", help="Continuously sync oblast history.")
    parser.add_argument("--limit", type=int, help="Maximum oblast requests to inspect/sync.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if args.dry_run:
        dry_run(args.limit)
        return

    if not args.once and not args.loop:
        parser.error("Choose one of --dry-run, --once, or --loop.")

    if not settings.alerts_in_ua_token:
        print("ALERTS_IN_UA_TOKEN is not configured; skipping alerts.in.ua sync.")
        return

    from server.database import SessionLocal, init_db
    from server.workers.alertsua_history_worker import AlertsUaHistoryWorker

    init_db()
    limit = args.limit
    if args.once and limit is None:
        limit = 1

    with SessionLocal() as session:
        worker = AlertsUaHistoryWorker(session=session)
        results = worker.run(limit=limit, loop=args.loop)
        for result in results:
            message = f": {result.message}" if result.message else ""
            print(
                f"{result.oblast_uid or '-'} {result.status} "
                f"loaded={result.loaded}{message}"
            )


if __name__ == "__main__":
    main()
