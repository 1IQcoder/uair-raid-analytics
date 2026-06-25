from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from server.analytics.metrics import VALID_MODES, _clamped_interval, _interval_minutes, _merge_intervals
from server.data.alertsua_reference import load_enabled_raions
from server.models import AlertsUaRaionEvent, AlertsUaSyncState


def latest_raion_event_timestamp(session: Session) -> datetime | None:
    return session.scalar(select(func.max(AlertsUaRaionEvent.finished_at))) or session.scalar(
        select(func.max(AlertsUaRaionEvent.started_at))
    )


def raion_analysis_window(
    session: Session,
    days: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[datetime | None, datetime | None]:
    if start_date and end_date:
        if end_date < start_date:
            start_date, end_date = end_date, start_date
        return (
            datetime.combine(start_date, datetime.min.time()),
            datetime.combine(end_date + timedelta(days=1), datetime.min.time()),
        )

    end = latest_raion_event_timestamp(session)
    if not end:
        return None, None
    if end.tzinfo is not None:
        end = end.astimezone().replace(tzinfo=None)
    return end - timedelta(days=days), end


def _window_day_count(start: datetime, end: datetime) -> int:
    return max((end.date() - start.date()).days, 1)


def _raion_events_in_window(
    session: Session,
    start: datetime,
    end: datetime,
    location_uid: str | None = None,
) -> list[AlertsUaRaionEvent]:
    stmt = (
        select(AlertsUaRaionEvent)
        .where(AlertsUaRaionEvent.alert_type == "air_raid")
        .where(AlertsUaRaionEvent.started_at < end)
        .where(
            or_(
                AlertsUaRaionEvent.finished_at.is_(None),
                AlertsUaRaionEvent.finished_at > start,
            )
        )
    )
    if location_uid:
        stmt = stmt.where(AlertsUaRaionEvent.location_uid == location_uid)
    return list(session.scalars(stmt))


def _known_raion_buckets() -> dict[str, dict]:
    return {
        raion.location_uid: {
            "location_uid": raion.location_uid,
            "location_title": raion.location_title,
            "oblast_uid": raion.oblast_uid,
            "oblast_name": raion.oblast_name,
            "alert_count": 0,
            "total_duration_minutes": 0.0,
            "average_duration_minutes": None,
            "metric_value": 0.0,
        }
        for raion in load_enabled_raions()
    }


def raion_summary(
    session: Session,
    days: int = 7,
    mode: str = "combined",
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    if mode not in VALID_MODES:
        raise ValueError(f"Unsupported mode: {mode}")

    buckets = _known_raion_buckets()
    start, end = raion_analysis_window(session, days, start_date, end_date)
    if start is None or end is None:
        return sorted(buckets.values(), key=lambda item: item["location_title"])

    intervals_by_uid: dict[str, list[tuple[datetime, datetime]]] = defaultdict(list)
    for event in _raion_events_in_window(session, start, end):
        interval = _clamped_interval(event.started_at, event.finished_at or end, start, end)
        if interval:
            intervals_by_uid[event.location_uid].append(interval)
        buckets.setdefault(
            event.location_uid,
            {
                "location_uid": event.location_uid,
                "location_title": event.location_title,
                "oblast_uid": event.reference_oblast_uid or event.requested_oblast_uid,
                "oblast_name": event.location_oblast,
                "alert_count": 0,
                "total_duration_minutes": 0.0,
                "average_duration_minutes": None,
                "metric_value": 0.0,
            },
        )

    for location_uid, intervals in intervals_by_uid.items():
        merged = _merge_intervals(intervals)
        bucket = buckets[location_uid]
        bucket["alert_count"] = len(merged)
        bucket["total_duration_minutes"] = _interval_minutes(merged)

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

    return sorted(buckets.values(), key=lambda item: item["location_title"])


def daily_raion_stats(
    session: Session,
    location_uid: str,
    days: int = 7,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    start, end = raion_analysis_window(session, days, start_date, end_date)
    raions_by_uid = {raion.location_uid: raion for raion in load_enabled_raions()}
    location_title = raions_by_uid.get(location_uid).location_title if location_uid in raions_by_uid else location_uid
    if start is None or end is None:
        return {"location_uid": location_uid, "location_title": location_title, "days": days, "stats": []}

    events = _raion_events_in_window(session, start, end, location_uid)
    stats = []
    for offset in range(_window_day_count(start, end)):
        day = start.date() + timedelta(days=offset)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        bucket_start = max(day_start, start)
        bucket_end = min(day_end, end)
        intervals = []

        for event in events:
            interval = _clamped_interval(
                event.started_at,
                event.finished_at or bucket_end,
                bucket_start,
                bucket_end,
            )
            if interval:
                intervals.append(interval)

        merged = _merge_intervals(intervals)
        stats.append(
            {
                "date": day.isoformat(),
                "alert_count": len(merged),
                "total_duration_minutes": _interval_minutes(merged),
            }
        )
    return {
        "location_uid": location_uid,
        "location_title": location_title,
        "days": len(stats),
        "stats": stats,
    }


def raion_sync_status(session: Session) -> list[dict]:
    states = session.scalars(
        select(AlertsUaSyncState).order_by(AlertsUaSyncState.oblast_name, AlertsUaSyncState.oblast_uid)
    )
    return [
        {
            "oblast_uid": state.oblast_uid,
            "oblast_name": state.oblast_name,
            "status": state.status,
            "last_synced_at": state.last_synced_at,
            "last_error": state.last_error,
            "retry_after": state.retry_after,
            "total_events_loaded": state.total_events_loaded,
        }
        for state in states
    ]
