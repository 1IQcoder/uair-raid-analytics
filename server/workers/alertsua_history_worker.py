from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from server.config import settings
from server.data.alertsua_client import (
    AlertsUaAuthError,
    AlertsUaClient,
    AlertsUaClientError,
    AlertsUaRateLimitError,
)
from server.data.alertsua_reference import (
    AlertsUaOblast,
    AlertsUaRaion,
    enabled_oblasts_from_raions,
    load_enabled_raions,
)
from server.models import AlertsUaRaionEvent, AlertsUaSyncState


LOGGER = logging.getLogger(__name__)
SYNC_STATUSES = {"pending", "synced", "failed", "disabled"}


@dataclass
class SyncResult:
    oblast_uid: str | None
    status: str
    loaded: int = 0
    message: str | None = None


class SafeRateLimiter:
    def __init__(self, min_interval_seconds: int, daily_limit: int) -> None:
        self.min_interval_seconds = max(min_interval_seconds, 35)
        self.daily_limit = daily_limit
        self.requests_today = 0
        self.day = datetime.utcnow().date()
        self.next_request_at: datetime | None = None

    def wait(self) -> bool:
        now = datetime.utcnow()
        if now.date() != self.day:
            self.day = now.date()
            self.requests_today = 0

        if self.daily_limit and self.requests_today >= self.daily_limit:
            LOGGER.info("alerts.in.ua daily limit reached: %s", self.daily_limit)
            return False

        if self.next_request_at and now < self.next_request_at:
            pause = (self.next_request_at - now).total_seconds()
            LOGGER.info("alerts.in.ua rate-limit pause: %.1f seconds", pause)
            time.sleep(pause)
        return True

    def mark_request(self) -> None:
        self.requests_today += 1
        self.next_request_at = datetime.utcnow() + timedelta(seconds=self.min_interval_seconds)

    def pause_after_429(self) -> None:
        self.next_request_at = datetime.utcnow() + timedelta(minutes=10)
        LOGGER.warning("alerts.in.ua returned 429; pausing at least 10 minutes")


def _utc_now() -> datetime:
    return datetime.utcnow()


def _parse_timestamp(value: Any) -> datetime | None:
    if value in {None, ""}:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        raw = str(value).replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return None
    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def _first_value(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload and payload[key] not in {None, ""}:
            return payload[key]
    return None


def _parse_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().casefold()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    return None


def is_raion_air_raid(alert: dict[str, Any]) -> bool:
    return (
        str(_first_value(alert, "location_type") or "").casefold() == "raion"
        and str(_first_value(alert, "alert_type", "type") or "").casefold() == "air_raid"
    )


def normalize_alert(
    alert: dict[str, Any],
    requested_oblast: AlertsUaOblast,
    raions_by_uid: dict[str, AlertsUaRaion],
) -> dict[str, Any] | None:
    started_at = _parse_timestamp(
        _first_value(alert, "started_at", "start_at", "startedAt", "start")
    )
    if started_at is None:
        return None

    source_event_id = _first_value(alert, "id", "alert_id", "source_event_id")
    location_uid = str(_first_value(alert, "location_uid") or "").strip()
    if not location_uid:
        return None
    reference_raion = raions_by_uid.get(location_uid)
    if reference_raion is None:
        LOGGER.warning(
            "alerts.in.ua returned unmatched raion uid=%s from requested oblast uid=%s",
            location_uid,
            requested_oblast.oblast_uid,
        )
    alert_type = str(_first_value(alert, "alert_type", "type") or "air_raid")
    refreshed_at = _utc_now()
    return {
        "source_event_id": str(source_event_id) if source_event_id is not None else None,
        "location_uid": location_uid,
        "location_title": str(
            _first_value(alert, "location_title")
            or (reference_raion.location_title if reference_raion else location_uid)
        ),
        "location_type": str(_first_value(alert, "location_type") or "raion"),
        "location_oblast": str(_first_value(alert, "location_oblast") or requested_oblast.oblast_name),
        "location_oblast_uid": str(_first_value(alert, "location_oblast_uid") or ""),
        "requested_oblast_uid": requested_oblast.oblast_uid,
        "reference_oblast_uid": reference_raion.oblast_uid if reference_raion else None,
        "location_raion": str(
            _first_value(alert, "location_raion")
            or _first_value(alert, "location_title")
            or (reference_raion.location_title if reference_raion else location_uid)
        ),
        "started_at": started_at,
        "finished_at": _parse_timestamp(
            _first_value(alert, "finished_at", "end_at", "finishedAt", "end")
        ),
        "updated_at": _parse_timestamp(_first_value(alert, "updated_at", "updatedAt")),
        "alert_type": alert_type,
        "notes": _first_value(alert, "notes"),
        "calculated": _parse_bool(_first_value(alert, "calculated")),
        "raw_json": json.dumps(alert, ensure_ascii=False, separators=(",", ":")),
        "refreshed_at": refreshed_at,
    }


def ensure_sync_states(session: Session, oblasts: list[AlertsUaOblast]) -> None:
    existing = {
        state.oblast_uid: state
        for state in session.scalars(select(AlertsUaSyncState)).all()
    }
    enabled = {oblast.oblast_uid for oblast in oblasts}

    for oblast in oblasts:
        state = existing.get(oblast.oblast_uid)
        if state is None:
            session.add(
                AlertsUaSyncState(
                    oblast_uid=oblast.oblast_uid,
                    oblast_name=oblast.oblast_name,
                    status="pending",
                    total_events_loaded=0,
                )
            )
            continue
        state.oblast_name = oblast.oblast_name
        if state.status == "disabled":
            state.status = "pending"

    for oblast_uid, state in existing.items():
        if oblast_uid not in enabled:
            state.status = "disabled"
    session.commit()


def pick_next_state(session: Session) -> AlertsUaSyncState | None:
    now = _utc_now()
    stmt = (
        select(AlertsUaSyncState)
        .where(AlertsUaSyncState.status != "disabled")
        .where(or_(AlertsUaSyncState.retry_after.is_(None), AlertsUaSyncState.retry_after <= now))
        .order_by(
            case((AlertsUaSyncState.status == "pending", 0), else_=1),
            AlertsUaSyncState.last_synced_at.is_(None).desc(),
            AlertsUaSyncState.last_synced_at.asc(),
            AlertsUaSyncState.id.asc(),
        )
    )
    return session.scalars(stmt).first()


def upsert_alert(session: Session, values: dict[str, Any]) -> bool:
    source_event_id = values.get("source_event_id")
    existing = None
    if source_event_id:
        existing = session.scalar(
            select(AlertsUaRaionEvent).where(
                AlertsUaRaionEvent.source_event_id == source_event_id
            )
        )
    if existing is None:
        existing = session.scalar(
            select(AlertsUaRaionEvent).where(
                AlertsUaRaionEvent.location_uid == values["location_uid"],
                AlertsUaRaionEvent.started_at == values["started_at"],
                AlertsUaRaionEvent.alert_type == values["alert_type"],
            )
        )

    if existing is None:
        values["created_at"] = _utc_now()
        session.add(AlertsUaRaionEvent(**values))
        return True

    for key, value in values.items():
        setattr(existing, key, value)
    return False


class AlertsUaHistoryWorker:
    def __init__(
        self,
        session: Session,
        client: AlertsUaClient | None = None,
        min_interval_seconds: int | None = None,
        daily_limit: int | None = None,
    ) -> None:
        self.session = session
        self.client = client or AlertsUaClient()
        self.rate_limiter = SafeRateLimiter(
            min_interval_seconds or settings.alerts_in_ua_history_min_interval_seconds,
            daily_limit if daily_limit is not None else settings.alerts_in_ua_history_daily_limit,
        )
        self.stop_requested = False

    def stop(self) -> None:
        self.stop_requested = True

    def prepare(self) -> tuple[dict[str, AlertsUaRaion], dict[str, AlertsUaOblast]]:
        raions = load_enabled_raions()
        oblasts = enabled_oblasts_from_raions(raions)
        ensure_sync_states(self.session, oblasts)
        return (
            {raion.location_uid: raion for raion in raions},
            {oblast.oblast_uid: oblast for oblast in oblasts},
        )

    def sync_one(self) -> SyncResult:
        raions_by_uid, oblasts_by_uid = self.prepare()
        state = pick_next_state(self.session)
        if state is None:
            return SyncResult(None, "idle", message="No enabled oblasts are available.")
        oblast = oblasts_by_uid.get(state.oblast_uid)
        if oblast is None:
            state.status = "disabled"
            self.session.commit()
            return SyncResult(state.oblast_uid, "disabled")

        if not self.rate_limiter.wait():
            return SyncResult(state.oblast_uid, "daily_limit")

        try:
            alerts = self.client.history_month_ago(oblast.oblast_uid)
            self.rate_limiter.mark_request()
        except AlertsUaRateLimitError as exc:
            self.rate_limiter.pause_after_429()
            state.status = "failed"
            state.last_error = str(exc)
            state.retry_after = _utc_now() + timedelta(minutes=10)
            self.session.commit()
            return SyncResult(oblast.oblast_uid, "rate_limited", message=str(exc))
        except AlertsUaAuthError as exc:
            state.status = "failed"
            state.last_error = str(exc)
            self.session.commit()
            self.stop()
            return SyncResult(oblast.oblast_uid, "auth_failed", message=str(exc))
        except AlertsUaClientError as exc:
            state.status = "failed"
            state.last_error = str(exc)
            state.retry_after = _utc_now() + timedelta(minutes=10)
            self.session.commit()
            return SyncResult(oblast.oblast_uid, "failed", message=str(exc))

        loaded = 0
        for alert in alerts:
            if not isinstance(alert, dict):
                continue
            if not is_raion_air_raid(alert):
                continue
            normalized = normalize_alert(alert, oblast, raions_by_uid)
            if normalized is None:
                continue
            if upsert_alert(self.session, normalized):
                loaded += 1

        state.status = "synced"
        state.last_synced_at = _utc_now()
        state.last_error = None
        state.retry_after = None
        state.total_events_loaded = self.session.scalar(
            select(func.count(AlertsUaRaionEvent.id)).where(
                AlertsUaRaionEvent.requested_oblast_uid == oblast.oblast_uid
            )
        ) or 0
        self.session.commit()
        return SyncResult(oblast.oblast_uid, "synced", loaded=loaded)

    def run(self, limit: int | None = None, loop: bool = False) -> list[SyncResult]:
        results: list[SyncResult] = []
        while not self.stop_requested:
            if limit is not None and len(results) >= limit:
                break
            result = self.sync_one()
            results.append(result)
            if result.status == "daily_limit":
                break
            if result.status == "idle" and loop:
                time.sleep(60)
                continue
            if not loop:
                break
        return results
