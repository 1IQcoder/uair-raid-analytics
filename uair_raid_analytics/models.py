from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from uair_raid_analytics.database import Base


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
