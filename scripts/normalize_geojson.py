from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = PROJECT_ROOT / "server" / "web" / "static" / "geo" / "ukr_admin1.geojson"
OUTPUT_PATH = PROJECT_ROOT / "server" / "web" / "static" / "geo" / "ukraine_regions.geojson"

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


def load_geojson(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def normalize_properties(geojson: dict[str, Any]) -> None:
    missing: list[str] = []
    for feature in geojson.get("features", []):
        properties = feature.setdefault("properties", {})
        region_code = properties.get("adm1_pcode") or properties.get("shapeISO")
        region = PCODE_TO_REGION.get(region_code) or ISO_TO_REGION.get(region_code)
        if region is None:
            missing.append(str(region_code))
            continue
        properties["region_id"] = region[0]
        properties["region_name"] = region[1]

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


def main() -> None:
    geojson = load_geojson(SOURCE_PATH)
    normalize_properties(geojson)
    rewind_geojson_for_d3(geojson)
    feature_count, invalid_count = validate_geojson(geojson)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(geojson, file, ensure_ascii=False, separators=(",", ":"))
        file.write("\n")

    validation = "shapely unavailable"
    if invalid_count is not None:
        validation = f"{invalid_count} invalid geometries"
    print(f"Normalized {feature_count} features to {OUTPUT_PATH}. Geometry validation: {validation}.")


if __name__ == "__main__":
    main()
