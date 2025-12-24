from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from flask import current_app
except ImportError:  # pragma: no cover - gateway not importing Flask
    current_app = None  # type: ignore

MANIFEST_PATH = Path(__file__).resolve().parent.parent / "models" / "geodata_manifest.json"
GEODATA_PATH = Path(__file__).resolve().parent.parent / "models" / "geodata"

try:  # optional dependency
    import geopandas as gpd
    from shapely.geometry import Point
except ImportError:  # pragma: no cover - geospatial stack not installed
    gpd = None  # type: ignore[assignment]
    Point = None  # type: ignore[assignment]


def _log_debug(message: str) -> None:
    if current_app:
        current_app.logger.debug(message)


@lru_cache(maxsize=1)
def load_manifest() -> Dict[str, Any]:
    if not MANIFEST_PATH.exists():
        _log_debug(f"Geodata manifest missing: {MANIFEST_PATH}")
        return {"regions": {}}
    with MANIFEST_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def list_regions() -> List[str]:
    return sorted(load_manifest().get("regions", {}).keys())


def list_layers(region: str) -> List[Dict[str, Any]]:
    manifest = load_manifest().get("regions", {})
    data = manifest.get(region) or manifest.get(region.lower())
    if not data:
        return []
    return data.get("layers", [])


def load_layer(region: str, layer: str):  # type: ignore[override]
    if gpd is None:
        raise RuntimeError("geopandas is required to load geospatial layers")

    geopackage = GEODATA_PATH / f"{region}.gpkg"
    if not geopackage.exists():
        raise FileNotFoundError(f"Geopackage not found: {geopackage}")
    return gpd.read_file(geopackage, layer=layer)


def layer_as_geojson(region: str, layer: str) -> Dict[str, Any]:
    if gpd is None:
        raise RuntimeError("geopandas is required to serialise geospatial layers")
    gdf = load_layer(region, layer)
    return json.loads(gdf.to_json())


def compute_context_features(lat: float, lon: float, region: Optional[str] = None) -> Dict[str, Any]:
    """Return geospatial signals to enrich detection/prediction models."""

    if gpd is None or Point is None:
        return {
            "geo_available": False,
            "distance_to_flow_m": None,
            "inside_flood_zone": False,
        }

    manifest = load_manifest().get("regions", {})
    if not manifest:
        return {
            "geo_available": False,
            "distance_to_flow_m": None,
            "inside_flood_zone": False,
        }

    region = region or next(iter(manifest.keys()))
    if region not in manifest:
        return {
            "geo_available": False,
            "distance_to_flow_m": None,
            "inside_flood_zone": False,
        }

    point = Point(lon, lat)
    metrics: Dict[str, Any] = {"geo_available": True}

    try:
        flow_layer = "Axe_ecoulement_temporaire"
        if any(layer["name"] == flow_layer for layer in manifest[region]["layers"]):
            flows = load_layer(region, flow_layer)
            metrics["distance_to_flow_m"] = float(flows.distance(point).min())
        else:
            metrics["distance_to_flow_m"] = None

        zone_layer = "Zone_inondable_humide"
        if any(layer["name"] == zone_layer for layer in manifest[region]["layers"]):
            zones = load_layer(region, zone_layer)
            metrics["inside_flood_zone"] = bool(zones.contains(point).any())
        else:
            metrics["inside_flood_zone"] = False
    except Exception as exc:  # pragma: no cover - best effort
        _log_debug(f"Failed to compute geospatial metrics: {exc}")
        metrics.update(
            {
                "geo_available": False,
                "distance_to_flow_m": None,
                "inside_flood_zone": False,
            }
        )

    return metrics

