from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("UAIR_APP_NAME", "UAir-raid-analytics")
    debug: bool = os.getenv("UAIR_DEBUG", "false").lower() == "true"
    database_url: str = os.getenv(
        "UAIR_DATABASE_URL",
        "sqlite:///./data/processed/uair_raid_analytics.sqlite3",
    )
    primary_dataset_url: str = os.getenv(
        "UAIR_PRIMARY_DATASET_URL",
        "https://raw.githubusercontent.com/Vadimkin/ukrainian-air-raid-sirens-dataset/main/datasets/official_data_uk.csv",
    )
    secondary_dataset_url: str = os.getenv(
        "UAIR_SECONDARY_DATASET_URL",
        "https://raw.githubusercontent.com/Vadimkin/ukrainian-air-raid-sirens-dataset/main/datasets/volunteer_data_uk.csv",
    )
    alerts_in_ua_token: str | None = os.getenv("ALERTS_IN_UA_TOKEN") or None

    @property
    def resolved_database_url(self) -> str:
        if not self.database_url.startswith("sqlite:///"):
            return self.database_url
        raw_path = self.database_url.replace("sqlite:///", "", 1)
        path = Path(raw_path)
        if path.is_absolute():
            return self.database_url
        return f"sqlite:///{PROJECT_ROOT / path}"

    @property
    def sqlite_path(self) -> Path | None:
        if not self.resolved_database_url.startswith("sqlite:///"):
            return None
        raw_path = self.resolved_database_url.replace("sqlite:///", "", 1)
        path = Path(raw_path)
        return path


settings = Settings()
