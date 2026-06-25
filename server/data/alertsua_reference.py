from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from server.config import PROJECT_ROOT


REFERENCE_PATH = PROJECT_ROOT / "data" / "reference" / "alertsua_raions.csv"
REQUIRED_COLUMNS = {
    "location_uid",
    "location_title",
    "oblast_uid",
    "oblast_name",
    "enabled",
}


@dataclass(frozen=True)
class AlertsUaRaion:
    location_uid: str
    location_title: str
    oblast_uid: str
    oblast_name: str


@dataclass(frozen=True)
class AlertsUaOblast:
    oblast_uid: str
    oblast_name: str


def _enabled(value: str) -> bool:
    return str(value).strip().casefold() in {"true", "1", "yes", "y"}


def load_enabled_raions(path: Path = REFERENCE_PATH) -> list[AlertsUaRaion]:
    if not path.exists():
        raise FileNotFoundError(f"alerts.in.ua raion reference file is missing: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(
                "alerts.in.ua raion reference file is missing columns: "
                + ", ".join(sorted(missing))
            )

        raions = []
        for row in reader:
            if not _enabled(row["enabled"]):
                continue
            raions.append(
                AlertsUaRaion(
                    location_uid=str(row["location_uid"]).strip(),
                    location_title=str(row["location_title"]).strip(),
                    oblast_uid=str(row["oblast_uid"]).strip(),
                    oblast_name=str(row["oblast_name"]).strip(),
                )
            )
    return raions


def enabled_oblasts_from_raions(raions: list[AlertsUaRaion]) -> list[AlertsUaOblast]:
    by_uid: dict[str, AlertsUaOblast] = {}
    for raion in raions:
        by_uid.setdefault(
            raion.oblast_uid,
            AlertsUaOblast(oblast_uid=raion.oblast_uid, oblast_name=raion.oblast_name),
        )
    return sorted(by_uid.values(), key=lambda item: (item.oblast_name, item.oblast_uid))
