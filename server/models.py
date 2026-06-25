from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from server.database import Base


class AlertEvent(Base):
    __tablename__ = "alert_events"
    __table_args__ = (
        UniqueConstraint(
            "source",
            "source_event_id",
            "region_name",
            "started_at",
            name="uq_alert_event_source_identity",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(64), index=True)
    source_event_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    region_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    region_name: Mapped[str] = mapped_column(String(128), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    duration_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    alert_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_location_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class DatasetRefreshLog(Base):
    __tablename__ = "dataset_refresh_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(64), index=True)
    source_url: Mapped[str] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(32))
    rows_loaded: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AlertsUaRaionEvent(Base):
    __tablename__ = "alertsua_raion_events"
    __table_args__ = (
        UniqueConstraint("source_event_id", name="uq_alertsua_raion_source_event_id"),
        UniqueConstraint(
            "location_uid",
            "started_at",
            "alert_type",
            name="uq_alertsua_raion_fallback_identity",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_event_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    location_uid: Mapped[str] = mapped_column(String(64), index=True)
    location_title: Mapped[str] = mapped_column(String(256), index=True)
    location_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    location_oblast: Mapped[str | None] = mapped_column(String(256), index=True, nullable=True)
    location_oblast_uid: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    requested_oblast_uid: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    reference_oblast_uid: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    location_raion: Mapped[str | None] = mapped_column(String(256), index=True, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    alert_type: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    calculated: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    raw_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AlertsUaSyncState(Base):
    __tablename__ = "alertsua_sync_state"
    __table_args__ = (UniqueConstraint("oblast_uid", name="uq_alertsua_sync_oblast_uid"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    oblast_uid: Mapped[str] = mapped_column(String(64), index=True)
    oblast_name: Mapped[str] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    total_events_loaded: Mapped[int] = mapped_column(Integer, default=0)
