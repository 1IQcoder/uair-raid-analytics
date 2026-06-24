from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from uair_raid_analytics.api.routes import router as api_router
from uair_raid_analytics.config import PROJECT_ROOT, settings
from uair_raid_analytics.database import init_db
from uair_raid_analytics.web.routes import router as web_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    init_db()

    static_dir = PROJECT_ROOT / "uair_raid_analytics" / "web" / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.include_router(api_router)
    app.include_router(web_router)
    return app


app = create_app()
