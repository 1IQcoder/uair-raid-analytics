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


class RaionSummary(BaseModel):
    location_uid: str
    location_title: str
    oblast_uid: str | None
    oblast_name: str | None
    alert_count: int
    total_duration_minutes: float
    average_duration_minutes: float | None
    metric_value: float


class RaionDailyResponse(BaseModel):
    location_uid: str
    location_title: str
    days: int
    stats: list[DailyRegionStat]


class RaionSyncStatus(BaseModel):
    oblast_uid: str
    oblast_name: str
    status: str
    last_synced_at: datetime | None
    last_error: str | None
    retry_after: datetime | None
    total_events_loaded: int


class DatasetMeta(BaseModel):
    latest_event_at: datetime | None
    total_events: int
    regions: list[dict[str, str]]
    last_refresh_at: datetime | None
