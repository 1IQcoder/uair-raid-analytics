from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RegionSummary(BaseModel):
    region_id: str | None
    region_name: str
    alert_count: int
    total_duration_minutes: float
    average_duration_minutes: float | None
    metric_value: float


class DailyRegionStat(BaseModel):
    date: str
    alert_count: int
    total_duration_minutes: float


class RegionDailyResponse(BaseModel):
    region_id: str
    region_name: str
    days: int
    stats: list[DailyRegionStat]


class DatasetMeta(BaseModel):
    latest_event_at: datetime | None
    total_events: int
    regions: list[dict[str, str]]
    last_refresh_at: datetime | None
