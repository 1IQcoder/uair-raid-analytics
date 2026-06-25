from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from server.models import AlertEvent, DatasetRefreshLog
from server.regions import REGION_BY_ID, UKRAINE_REGIONS


VALID_MODES = {"count", "duration", "combined"}
WAR_START = datetime(2022, 2, 24)
PERMANENT_ALERT_REGION_IDS = {"16", "29"}


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


def _clamped_interval(
    started_at: datetime,
    finished_at: datetime,
    start: datetime,
    end: datetime,
) -> tuple[datetime, datetime] | None:
    clamped_start = max(started_at, start)
    clamped_end = min(finished_at, end)
    if clamped_end <= clamped_start:
        return None
    return clamped_start, clamped_end


def _permanent_alert_interval(
    region_id: str,
    start: datetime,
    end: datetime,
) -> tuple[datetime, datetime] | None:
    if region_id not in PERMANENT_ALERT_REGION_IDS or end <= WAR_START:
        return None
    clamped_start = max(start, WAR_START)
    if end <= clamped_start:
        return None
    return clamped_start, end


def _merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    ordered = sorted((start, end) for start, end in intervals if end > start)
    if not ordered:
        return []

    merged = [ordered[0]]
    for start, end in ordered[1:]:
        current_start, current_end = merged[-1]
        if start <= current_end:
            merged[-1] = (current_start, max(current_end, end))
        else:
            merged.append((start, end))
    return merged


def _interval_minutes(intervals: list[tuple[datetime, datetime]]) -> float:
    return sum((end - start).total_seconds() / 60 for start, end in intervals)


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

    intervals_by_region: dict[str, list[tuple[datetime, datetime]]] = defaultdict(list)
    for event in _events_in_window(session, start, end):
        if not event.region_id:
            continue
        interval = _clamped_interval(event.started_at, event.finished_at, start, end)
        if interval:
            intervals_by_region[event.region_id].append(interval)

    for region_id in PERMANENT_ALERT_REGION_IDS:
        interval = _permanent_alert_interval(region_id, start, end)
        if interval:
            intervals_by_region[region_id].append(interval)

    for region_id, intervals in intervals_by_region.items():
        merged_intervals = _merge_intervals(intervals)
        bucket = buckets.setdefault(
            region_id,
            {
                "region_id": region_id,
                "region_name": REGION_BY_ID.get(region_id, {}).get("region_name", region_id),
                "alert_count": 0,
                "total_duration_minutes": 0.0,
                "average_duration_minutes": None,
                "metric_value": 0.0,
            },
        )
        bucket["alert_count"] = len(merged_intervals)
        bucket["total_duration_minutes"] = _interval_minutes(merged_intervals)

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
    stats = []
    for offset in range(days):
        day = start.date() + timedelta(days=offset)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        bucket_start = max(day_start, start)
        bucket_end = min(day_end, end)
        intervals = []

        for event in events:
            interval = _clamped_interval(event.started_at, event.finished_at, bucket_start, bucket_end)
            if interval:
                intervals.append(interval)

        permanent_interval = _permanent_alert_interval(region_id, bucket_start, bucket_end)
        if permanent_interval:
            intervals.append(permanent_interval)

        merged_intervals = _merge_intervals(intervals)
        stats.append(
            {
                "date": day.isoformat(),
                "alert_count": len(merged_intervals),
                "total_duration_minutes": _interval_minutes(merged_intervals),
            }
        )
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
