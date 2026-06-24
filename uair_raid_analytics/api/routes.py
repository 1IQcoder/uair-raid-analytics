from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from uair_raid_analytics.analytics.metrics import (
    VALID_MODES,
    daily_region_stats,
    dataset_meta,
    region_summary,
)
from uair_raid_analytics.database import get_session
from uair_raid_analytics.schemas import DatasetMeta, RegionDailyResponse, RegionSummary


router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/regions/summary", response_model=list[RegionSummary])
def get_regions_summary(
    days: int = Query(default=7, ge=1, le=365),
    mode: str = Query(default="combined"),
    session: Session = Depends(get_session),
) -> list[dict]:
    if mode not in VALID_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode. Expected one of: {', '.join(sorted(VALID_MODES))}",
        )
    return region_summary(session=session, days=days, mode=mode)


@router.get("/regions/{region_id}/daily", response_model=RegionDailyResponse)
def get_region_daily(
    region_id: str,
    days: int = Query(default=7, ge=1, le=365),
    session: Session = Depends(get_session),
) -> dict:
    return daily_region_stats(session=session, region_id=region_id, days=days)


@router.get("/meta", response_model=DatasetMeta)
def get_meta(session: Session = Depends(get_session)) -> dict:
    return dataset_meta(session)
