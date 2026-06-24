from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from uair_raid_analytics.models import AlertEvent, DatasetRefreshLog
from uair_raid_analytics.regions import REGION_BY_ID, UKRAINE_REGIONS


VALID_MODES = {"count", "duration", "combined"}


def latest_event_timestamp(session: Session) -> datetime | None:
    return session.scalar(select(func.max(AlertEvent.finished_at))) or session.scalar(
        select(func.max(AlertEvent.started_at))
    )


def analysis_window(session: Session, days: int) -> tuple[datetime | None, datetime | None]:
    end = latest_event_timestamp(session)
    if not end:
        return None, None
    if end.tzinfo is not None:
        end = end.astimezone().replace(tzinfo=None)
    return end - timedelta(days=days), end


def _overlap_minutes(started_at: datetime, finished_at: datetime, start: datetime, end: datetime) -> float:
    clamped_start = max(started_at, start)
    clamped_end = min(finished_at, end)
    return max((clamped_end - clamped_start).total_seconds() / 60, 0)


def _events_in_window(session: Session, start: datetime, end: datetime) -> list[AlertEvent]:
    stmt = (
        select(AlertEvent)
        .where(AlertEvent.finished_at.is_not(None))
        .where(AlertEvent.started_at < end)
        .where(AlertEvent.finished_at > start)
    )
    return list(session.scalars(stmt))


def region_summary(session: Session, days: int = 7, mode: str = "combined") -> list[dict]:
    if mode not in VALID_MODES:
        raise ValueError(f"Unsupported mode: {mode}")

    start, end = analysis_window(session, days)
    if start is None or end is None:
        return _empty_region_summary()

    buckets: dict[str, dict] = {
        region["region_id"]: {
            "region_id": region["region_id"],
            "region_name": region["region_name"],
            "alert_count": 0,
            "total_duration_minutes": 0.0,
            "average_duration_minutes": None,
            "metric_value": 0.0,
        }
        for region in UKRAINE_REGIONS
    }

    for event in _events_in_window(session, start, end):
        if not event.region_id:
            continue
        bucket = buckets.setdefault(
            event.region_id,
            {
                "region_id": event.region_id,
                "region_name": event.region_name,
                "alert_count": 0,
                "total_duration_minutes": 0.0,
                "average_duration_minutes": None,
                "metric_value": 0.0,
            },
        )
        bucket["alert_count"] += 1
        bucket["total_duration_minutes"] += _overlap_minutes(
            event.started_at,
            event.finished_at,
            start,
            end,
        )

    max_count = max((item["alert_count"] for item in buckets.values()), default=0)
    max_duration = max((item["total_duration_minutes"] for item in buckets.values()), default=0)

    for item in buckets.values():
        if item["alert_count"]:
            item["average_duration_minutes"] = item["total_duration_minutes"] / item["alert_count"]
        if mode == "count":
            item["metric_value"] = float(item["alert_count"])
        elif mode == "duration":
            item["metric_value"] = item["total_duration_minutes"]
        else:
            normalized_count = item["alert_count"] / max_count if max_count else 0
            normalized_duration = item["total_duration_minutes"] / max_duration if max_duration else 0
            item["metric_value"] = normalized_count * 0.5 + normalized_duration * 0.5

    return sorted(buckets.values(), key=lambda item: item["region_name"])


def daily_region_stats(session: Session, region_id: str, days: int = 7) -> dict:
    start, end = analysis_window(session, days)
    region_name = REGION_BY_ID.get(region_id, {}).get("region_name", region_id)
    if start is None or end is None:
        return {"region_id": region_id, "region_name": region_name, "days": days, "stats": []}

    stmt = (
        select(AlertEvent)
        .where(AlertEvent.region_id == region_id)
        .where(AlertEvent.finished_at.is_not(None))
        .where(AlertEvent.started_at < end)
        .where(AlertEvent.finished_at > start)
    )
    events = list(session.scalars(stmt))
    buckets = defaultdict(lambda: {"alert_count": 0, "total_duration_minutes": 0.0})

    for event in events:
        bucket_key = event.started_at.date().isoformat()
        buckets[bucket_key]["alert_count"] += 1
        buckets[bucket_key]["total_duration_minutes"] += _overlap_minutes(
            event.started_at,
            event.finished_at,
            start,
            end,
        )

    stats = [
        {
            "date": (start.date() + timedelta(days=offset)).isoformat(),
            "alert_count": buckets[(start.date() + timedelta(days=offset)).isoformat()][
                "alert_count"
            ],
            "total_duration_minutes": buckets[(start.date() + timedelta(days=offset)).isoformat()][
                "total_duration_minutes"
            ],
        }
        for offset in range(days)
    ]
    return {"region_id": region_id, "region_name": region_name, "days": days, "stats": stats}


def dataset_meta(session: Session) -> dict:
    latest_refresh = session.scalar(select(func.max(DatasetRefreshLog.refreshed_at)))
    total_events = session.scalar(select(func.count(AlertEvent.id))) or 0
    return {
        "latest_event_at": latest_event_timestamp(session),
        "total_events": total_events,
        "regions": UKRAINE_REGIONS,
        "last_refresh_at": latest_refresh,
    }


def _empty_region_summary() -> list[dict]:
    return [
        {
            "region_id": region["region_id"],
            "region_name": region["region_name"],
            "alert_count": 0,
            "total_duration_minutes": 0.0,
            "average_duration_minutes": None,
            "metric_value": 0.0,
        }
        for region in UKRAINE_REGIONS
    ]
