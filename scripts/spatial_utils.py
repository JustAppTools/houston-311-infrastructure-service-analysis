import json
from pathlib import Path


def iter_rings(geometry: dict):
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates", [])
    if geom_type == "Polygon":
        for ring in coords:
            yield ring
    elif geom_type == "MultiPolygon":
        for polygon in coords:
            for ring in polygon:
                yield ring


def point_in_ring(lon: float, lat: float, ring: list) -> bool:
    inside = False
    if not ring:
        return False
    j = len(ring) - 1
    for i, point in enumerate(ring):
        xi, yi = point[0], point[1]
        xj, yj = ring[j][0], ring[j][1]
        intersects = ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def point_in_geometry(lon: float, lat: float, geometry: dict) -> bool:
    rings = list(iter_rings(geometry))
    if not rings:
        return False
    in_outer = point_in_ring(lon, lat, rings[0])
    in_hole = any(point_in_ring(lon, lat, ring) for ring in rings[1:])
    return in_outer and not in_hole


def load_geojson(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def assign_point_to_district(lon: float, lat: float, boundaries: dict | None) -> str | None:
    if boundaries is None:
        return None
    for feature in boundaries.get("features", []):
        district = str(feature.get("properties", {}).get("DISTRICT") or "").strip()
        if district and point_in_geometry(lon, lat, feature.get("geometry", {})):
            return district
    return None
