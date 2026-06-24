from __future__ import annotations

import re


UKRAINE_REGIONS = [
    {"region_id": "3", "region_name": "Хмельницька область"},
    {"region_id": "4", "region_name": "Вінницька область"},
    {"region_id": "5", "region_name": "Рівненська область"},
    {"region_id": "8", "region_name": "Волинська область"},
    {"region_id": "9", "region_name": "Дніпропетровська область"},
    {"region_id": "10", "region_name": "Житомирська область"},
    {"region_id": "11", "region_name": "Закарпатська область"},
    {"region_id": "12", "region_name": "Запорізька область"},
    {"region_id": "13", "region_name": "Івано-Франківська область"},
    {"region_id": "14", "region_name": "Київська область"},
    {"region_id": "15", "region_name": "Кіровоградська область"},
    {"region_id": "16", "region_name": "Луганська область"},
    {"region_id": "17", "region_name": "Миколаївська область"},
    {"region_id": "18", "region_name": "Одеська область"},
    {"region_id": "19", "region_name": "Полтавська область"},
    {"region_id": "20", "region_name": "Сумська область"},
    {"region_id": "21", "region_name": "Тернопільська область"},
    {"region_id": "22", "region_name": "Харківська область"},
    {"region_id": "23", "region_name": "Херсонська область"},
    {"region_id": "24", "region_name": "Черкаська область"},
    {"region_id": "25", "region_name": "Чернігівська область"},
    {"region_id": "26", "region_name": "Чернівецька область"},
    {"region_id": "27", "region_name": "Львівська область"},
    {"region_id": "28", "region_name": "Донецька область"},
    {"region_id": "29", "region_name": "Автономна Республіка Крим"},
    {"region_id": "30", "region_name": "м. Севастополь"},
    {"region_id": "31", "region_name": "м. Київ"},
]

REGION_BY_ID = {item["region_id"]: item for item in UKRAINE_REGIONS}
REGION_ID_BY_NORMALIZED_NAME = {
    re.sub(r"\s+", " ", item["region_name"].casefold()).strip(): item["region_id"]
    for item in UKRAINE_REGIONS
}


def normalize_region_name(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip())


def resolve_region_id(region_name: str) -> str | None:
    return REGION_ID_BY_NORMALIZED_NAME.get(normalize_region_name(region_name).casefold())
