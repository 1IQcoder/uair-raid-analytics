from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GEO_DIR = PROJECT_ROOT / "server" / "web" / "static" / "geo"
REGION_SOURCE_PATH = GEO_DIR / "ukr_admin1.geojson"
REGION_OUTPUT_PATH = GEO_DIR / "ukraine_regions.geojson"
DISTRICT_SOURCE_PATH = GEO_DIR / "ukr_admin2.geojson"
DISTRICT_OUTPUT_PATH = GEO_DIR / "ukraine_districts.geojson"
ALERTSUA_RAIONS_PATH = PROJECT_ROOT / "data" / "reference" / "alertsua_raions.csv"

PCODE_TO_REGION = {
    "UA01": ("29", "Автономна Республіка Крим"),
    "UA05": ("4", "Вінницька область"),
    "UA07": ("8", "Волинська область"),
    "UA12": ("9", "Дніпропетровська область"),
    "UA14": ("28", "Донецька область"),
    "UA18": ("10", "Житомирська область"),
    "UA21": ("11", "Закарпатська область"),
    "UA23": ("12", "Запорізька область"),
    "UA26": ("13", "Івано-Франківська область"),
    "UA32": ("14", "Київська область"),
    "UA35": ("15", "Кіровоградська область"),
    "UA44": ("16", "Луганська область"),
    "UA46": ("27", "Львівська область"),
    "UA48": ("17", "Миколаївська область"),
    "UA51": ("18", "Одеська область"),
    "UA53": ("19", "Полтавська область"),
    "UA56": ("5", "Рівненська область"),
    "UA59": ("20", "Сумська область"),
    "UA61": ("21", "Тернопільська область"),
    "UA63": ("22", "Харківська область"),
    "UA65": ("23", "Херсонська область"),
    "UA68": ("3", "Хмельницька область"),
    "UA71": ("24", "Черкаська область"),
    "UA73": ("26", "Чернівецька область"),
    "UA74": ("25", "Чернігівська область"),
    "UA80": ("31", "м. Київ"),
    "UA85": ("30", "м. Севастополь"),
}

ISO_TO_REGION = {
    "UA-05": ("4", "Вінницька область"),
    "UA-07": ("8", "Волинська область"),
    "UA-09": ("16", "Луганська область"),
    "UA-12": ("9", "Дніпропетровська область"),
    "UA-14": ("28", "Донецька область"),
    "UA-18": ("10", "Житомирська область"),
    "UA-21": ("11", "Закарпатська область"),
    "UA-23": ("12", "Запорізька область"),
    "UA-26": ("13", "Івано-Франківська область"),
    "UA-30": ("31", "м. Київ"),
    "UA-32": ("14", "Київська область"),
    "UA-35": ("15", "Кіровоградська область"),
    "UA-40": ("30", "м. Севастополь"),
    "UA-43": ("29", "Автономна Республіка Крим"),
    "UA-46": ("27", "Львівська область"),
    "UA-48": ("17", "Миколаївська область"),
    "UA-51": ("18", "Одеська область"),
    "UA-53": ("19", "Полтавська область"),
    "UA-56": ("5", "Рівненська область"),
    "UA-59": ("20", "Сумська область"),
    "UA-61": ("21", "Тернопільська область"),
    "UA-63": ("22", "Харківська область"),
    "UA-65": ("23", "Херсонська область"),
    "UA-68": ("3", "Хмельницька область"),
    "UA-71": ("24", "Черкаська область"),
    "UA-74": ("25", "Чернігівська область"),
    "UA-77": ("26", "Чернівецька область"),
}


def normalize_raion_title(value: str) -> str:
    text = str(value).casefold().strip()
    suffix = " \u0440\u0430\u0439\u043e\u043d"
    if text.endswith(suffix):
        text = text[: -len(suffix)]
    return text.strip()


def load_alertsua_raion_uid_map() -> dict[tuple[str, str], str]:
    if not ALERTSUA_RAIONS_PATH.exists():
        return {}
    mapping: dict[tuple[str, str], str] = {}
    with ALERTSUA_RAIONS_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            enabled = str(row.get("enabled", "")).strip().casefold() == "true"
            if not enabled:
                continue
            key = (
                str(row.get("oblast_uid", "")).strip(),
                normalize_raion_title(str(row.get("location_title", ""))),
            )
            mapping[key] = str(row.get("location_uid", "")).strip()
    return mapping


def load_geojson(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def normalize_properties(geojson: dict[str, Any]) -> None:
    missing: list[str] = []
    alertsua_raion_uids = load_alertsua_raion_uid_map()
    for feature in geojson.get("features", []):
        properties = feature.setdefault("properties", {})
        region_code = properties.get("adm1_pcode") or properties.get("shapeISO")
        region = PCODE_TO_REGION.get(region_code) or ISO_TO_REGION.get(region_code)
        if region is None:
            missing.append(str(region_code))
            continue
        properties["region_id"] = region[0]
        properties["region_name"] = region[1]
        if properties.get("adm2_pcode"):
            properties["district_id"] = properties["adm2_pcode"]
            properties["district_name"] = (
                properties.get("adm2_name1")
                or properties.get("adm2_name")
                or properties["adm2_pcode"]
            )
            alertsua_uid = alertsua_raion_uids.get(
                (properties["region_id"], normalize_raion_title(properties["district_name"]))
            )
            if alertsua_uid:
                properties["alertsua_location_uid"] = alertsua_uid

    if missing:
        raise ValueError(f"Missing region code mappings: {', '.join(sorted(set(missing)))}")


def ring_signed_area(ring: list[list[float]]) -> float:
    area = 0.0
    for index in range(len(ring) - 1):
        x1, y1 = ring[index][:2]
        x2, y2 = ring[index + 1][:2]
        area += x1 * y2 - x2 * y1
    return area / 2


def rewind_ring(ring: list[list[float]], clockwise: bool) -> list[list[float]]:
    area = ring_signed_area(ring)
    is_clockwise = area < 0
    if is_clockwise != clockwise:
        return list(reversed(ring))
    return ring


def rewind_polygon_for_d3(polygon: list[list[list[float]]]) -> list[list[list[float]]]:
    if not polygon:
        return polygon
    return [
        rewind_ring(ring, clockwise=index == 0)
        for index, ring in enumerate(polygon)
    ]


def rewind_geojson_for_d3(geojson: dict[str, Any]) -> None:
    for feature in geojson.get("features", []):
        geometry = feature.get("geometry") or {}
        geometry_type = geometry.get("type")
        coordinates = geometry.get("coordinates")
        if geometry_type == "Polygon" and coordinates:
            geometry["coordinates"] = rewind_polygon_for_d3(coordinates)
        elif geometry_type == "MultiPolygon" and coordinates:
            geometry["coordinates"] = [
                rewind_polygon_for_d3(polygon)
                for polygon in coordinates
            ]


def validate_geojson(geojson: dict[str, Any]) -> tuple[int, int | None]:
    features = geojson.get("features", [])
    missing_properties = [
        feature.get("properties", {}).get("adm1_pcode")
        or feature.get("properties", {}).get("shapeISO", "unknown")
        for feature in features
        if not feature.get("properties", {}).get("region_id")
        or not feature.get("properties", {}).get("region_name")
    ]
    if missing_properties:
        raise ValueError(
            "Features missing region_id/region_name: "
            + ", ".join(str(item) for item in missing_properties)
        )

    try:
        from shapely.geometry import shape
    except ImportError:
        return len(features), None

    invalid = 0
    for feature in features:
        geometry = feature.get("geometry")
        if geometry is None or not shape(geometry).is_valid:
            invalid += 1
    return len(features), invalid


def normalize_file(source_path: Path, output_path: Path) -> None:
    geojson = load_geojson(source_path)
    normalize_properties(geojson)
    rewind_geojson_for_d3(geojson)
    feature_count, invalid_count = validate_geojson(geojson)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(geojson, file, ensure_ascii=False, separators=(",", ":"))
        file.write("\n")

    validation = "shapely unavailable"
    if invalid_count is not None:
        validation = f"{invalid_count} invalid geometries"
    print(f"Normalized {feature_count} features to {output_path}. Geometry validation: {validation}.")


def main() -> None:
    normalize_file(REGION_SOURCE_PATH, REGION_OUTPUT_PATH)
    normalize_file(DISTRICT_SOURCE_PATH, DISTRICT_OUTPUT_PATH)


if __name__ == "__main__":
    main()
