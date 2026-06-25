from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from server.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.resolved_database_url,
    connect_args={"check_same_thread": False}
    if settings.resolved_database_url.startswith("sqlite")
    else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    from server import models  # noqa: F401

    if settings.sqlite_path:
        settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    if settings.resolved_database_url.startswith("sqlite"):
        _migrate_sqlite_alertsua_schema()


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _migrate_sqlite_alertsua_schema() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    with engine.begin() as connection:
        if "alertsua_raion_events" in table_names:
            columns = {column["name"] for column in inspector.get_columns("alertsua_raion_events")}
            if "requested_oblast_uid" not in columns:
                connection.execute(text("ALTER TABLE alertsua_raion_events ADD COLUMN requested_oblast_uid VARCHAR(64)"))
            if "reference_oblast_uid" not in columns:
                connection.execute(text("ALTER TABLE alertsua_raion_events ADD COLUMN reference_oblast_uid VARCHAR(64)"))

        if "alertsua_sync_state" in table_names:
            columns = {column["name"] for column in inspector.get_columns("alertsua_sync_state")}
            if "location_uid" in columns or "location_title" in columns:
                connection.execute(text("DROP TABLE alertsua_sync_state"))
                Base.metadata.tables["alertsua_sync_state"].create(bind=connection)
