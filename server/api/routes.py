from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from server.analytics.metrics import (
    VALID_MODES,
    daily_region_stats,
    dataset_meta,
    region_summary,
)
from server.analytics.raion_metrics import (
    daily_raion_stats,
    raion_summary,
    raion_sync_status,
)
from server.database import get_session
from server.schemas import (
    DatasetMeta,
    RaionDailyResponse,
    RaionSummary,
    RaionSyncStatus,
    RegionDailyResponse,
    RegionSummary,
)


router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/regions/summary", response_model=list[RegionSummary])
def get_regions_summary(
    days: int = Query(default=7, ge=1, le=365),
    mode: str = Query(default="combined"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[dict]:
    if mode not in VALID_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode. Expected one of: {', '.join(sorted(VALID_MODES))}",
        )
    return region_summary(
        session=session,
        days=days,
        mode=mode,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/regions/{region_id}/daily", response_model=RegionDailyResponse)
def get_region_daily(
    region_id: str,
    days: int = Query(default=7, ge=1, le=365),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    session: Session = Depends(get_session),
) -> dict:
    return daily_region_stats(
        session=session,
        region_id=region_id,
        days=days,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/raions/summary", response_model=list[RaionSummary])
def get_raions_summary(
    days: int = Query(default=7, ge=1, le=365),
    mode: str = Query(default="combined"),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[dict]:
    if mode not in VALID_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode. Expected one of: {', '.join(sorted(VALID_MODES))}",
        )
    return raion_summary(
        session=session,
        days=days,
        mode=mode,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/raions/sync-status", response_model=list[RaionSyncStatus])
def get_raions_sync_status(session: Session = Depends(get_session)) -> list[dict]:
    return raion_sync_status(session)


@router.get("/raions/{location_uid}/daily", response_model=RaionDailyResponse)
def get_raion_daily(
    location_uid: str,
    days: int = Query(default=7, ge=1, le=365),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    session: Session = Depends(get_session),
) -> dict:
    return daily_raion_stats(
        session=session,
        location_uid=location_uid,
        days=days,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/meta", response_model=DatasetMeta)
def get_meta(session: Session = Depends(get_session)) -> dict:
    return dataset_meta(session)
