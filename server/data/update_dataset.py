from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import delete
from sqlalchemy.orm import Session

from server.config import PROJECT_ROOT, settings
from server.database import SessionLocal, init_db
from server.models import AlertEvent, DatasetRefreshLog
from server.regions import normalize_region_name, resolve_region_id


COLUMN_ALIASES = {
    "source_event_id": ["id", "alert_id", "source_event_id"],
    "region_name": [
        "region",
        "region_name",
        "oblast",
        "location_title",
        "location_oblast",
        "Область",
        "Регіон",
    ],
    "region_id": ["region_id", "location_uid", "location_oblast_uid", "uid"],
    "started_at": ["started_at", "start", "start_time", "started", "Початок"],
    "finished_at": ["finished_at", "end", "end_time", "finished", "Кінець"],
    "duration_minutes": ["duration_minutes", "duration", "minutes", "Тривалість"],
    "alert_type": ["alert_type", "type"],
    "raw_location_type": ["location_type"],
}


def _find_column(df: pd.DataFrame, aliases: list[str]) -> str | None:
    normalized = {str(column).strip().casefold(): column for column in df.columns}
    for alias in aliases:
        match = normalized.get(alias.casefold())
        if match is not None:
            return str(match)
    return None


def _read_csv(source: str) -> pd.DataFrame:
    # Pandas can read both remote URLs and local files, which keeps the update path flexible.
    return pd.read_csv(source)


def _parse_timestamp(value: Any) -> datetime | None:
    if pd.isna(value) or value == "":
        return None
    parsed = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(parsed):
        return None
    # Store timestamps as naive UTC because SQLite does not preserve timezone info reliably.
    return parsed.tz_convert(None).to_pydatetime()


def normalize_events(df: pd.DataFrame, source_name: str) -> list[dict[str, Any]]:
    columns = {key: _find_column(df, aliases) for key, aliases in COLUMN_ALIASES.items()}
    if not columns["region_name"] or not columns["started_at"]:
        raise ValueError(
            "Dataset must contain at least region_name and started_at compatible columns."
        )

    events: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        region_name = normalize_region_name(row[columns["region_name"]])
        started_at = _parse_timestamp(row[columns["started_at"]])
        finished_at = (
            _parse_timestamp(row[columns["finished_at"]])
            if columns["finished_at"]
            else None
        )
        if not region_name or started_at is None:
            continue

        alert_type = str(row[columns["alert_type"]]) if columns["alert_type"] else "air_raid"
        if alert_type and alert_type != "air_raid":
            continue

        duration_minutes = None
        if columns["duration_minutes"] and not pd.isna(row[columns["duration_minutes"]]):
            duration_minutes = float(row[columns["duration_minutes"]])
        elif finished_at:
            duration_minutes = max((finished_at - started_at).total_seconds() / 60, 0)

        region_id = None
        if columns["region_id"] and not pd.isna(row[columns["region_id"]]):
            region_id = str(row[columns["region_id"]]).strip()
        region_id = region_id or resolve_region_id(region_name)

        events.append(
            {
                "source": source_name,
                "source_event_id": str(row[columns["source_event_id"]])
                if columns["source_event_id"] and not pd.isna(row[columns["source_event_id"]])
                else None,
                "region_id": region_id,
                "region_name": region_name,
                "started_at": started_at,
                "finished_at": finished_at,
                "duration_minutes": duration_minutes,
                "alert_type": alert_type or "air_raid",
                "raw_location_type": str(row[columns["raw_location_type"]])
                if columns["raw_location_type"] and not pd.isna(row[columns["raw_location_type"]])
                else None,
            }
        )
    return events


def refresh_from_sources(sources: dict[str, str], session: Session) -> int:
    total_loaded = 0
    session.execute(delete(AlertEvent))

    for source_name, source_url in sources.items():
        if not source_url:
            continue
        try:
            df = _read_csv(source_url)
            events = normalize_events(df, source_name)
            session.bulk_insert_mappings(AlertEvent, events)
            session.add(
                DatasetRefreshLog(
                    source=source_name,
                    source_url=source_url,
                    status="success",
                    rows_loaded=len(events),
                    message=None,
                    refreshed_at=datetime.utcnow(),
                )
            )
            total_loaded += len(events)
        except Exception as exc:  # noqa: BLE001 - refresh logs should preserve failures.
            session.add(
                DatasetRefreshLog(
                    source=source_name,
                    source_url=source_url,
                    status="failed",
                    rows_loaded=0,
                    message=str(exc),
                    refreshed_at=datetime.utcnow(),
                )
            )
    session.commit()
    return total_loaded


def build_default_sources(primary_only: bool) -> dict[str, str]:
    sources = {"vadimkin_official": settings.primary_dataset_url}
    if not primary_only and settings.secondary_dataset_url:
        sources["vadimkin_volunteer"] = settings.secondary_dataset_url
    return sources


def run_refresh(primary_only: bool = True) -> int:
    init_db()
    with SessionLocal() as session:
        return refresh_from_sources(build_default_sources(primary_only), session)


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh UAir-raid-analytics dataset.")
    parser.add_argument(
        "--include-secondary",
        action="store_true",
        help="Also load the configured secondary/volunteer dataset.",
    )
    parser.add_argument(
        "--database-url",
        help="Override database URL for this run.",
    )
    args = parser.parse_args()

    if args.database_url:
        raise SystemExit("Use UAIR_DATABASE_URL in .env for database overrides.")

    (PROJECT_ROOT / "data" / "processed").mkdir(parents=True, exist_ok=True)
    loaded = run_refresh(primary_only=not args.include_secondary)
    print(f"Loaded {loaded} alert events.")


if __name__ == "__main__":
    main()
