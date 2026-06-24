from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from server.api.routes import router as api_router
from server.config import PROJECT_ROOT, settings
from server.database import init_db
from server.web.routes import router as web_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    init_db()

    static_dir = PROJECT_ROOT / "server" / "web" / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.include_router(api_router)
    app.include_router(web_router)
    return app


app = create_app()
