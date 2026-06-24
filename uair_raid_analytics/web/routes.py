from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from uair_raid_analytics.config import PROJECT_ROOT, settings


router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory=PROJECT_ROOT / "uair_raid_analytics" / "web" / "templates")


@router.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "app_name": settings.app_name},
    )
