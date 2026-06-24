from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from server.config import PROJECT_ROOT, settings


router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory=PROJECT_ROOT / "server" / "web" / "templates")


@router.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": settings.app_name},
    )
