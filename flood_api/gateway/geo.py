from __future__ import annotations

from flask import Blueprint, jsonify, abort

from flood_api.shared.geodata import compute_context_features, layer_as_geojson, list_layers, list_regions
from flood_api.shared.geodata import load_manifest


geo_bp = Blueprint("geo", __name__, url_prefix="/geo")


@geo_bp.get("/regions")
def regions() -> tuple[str, int]:
    manifest = load_manifest()
    return jsonify({"regions": manifest.get("regions", {})}), 200


@geo_bp.get("/regions/<region>/layers")
def region_layers(region: str):
    layers = list_layers(region)
    if not layers:
        abort(404, description=f"Unknown region: {region}")
    return jsonify({"region": region, "layers": layers}), 200


@geo_bp.get("/regions/<region>/layers/<layer>")
def layer_geojson(region: str, layer: str):
    try:
        geojson = layer_as_geojson(region, layer)
    except FileNotFoundError:
        abort(404, description=f"Layer not found: {region}/{layer}")
    except RuntimeError as exc:
        abort(503, description=str(exc))
    return jsonify(geojson), 200


@geo_bp.get("/features")
def features_from_point():
    from flask import request

    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
    except (TypeError, ValueError):
        abort(400, description="lat/lon query parameters are required")

    region = request.args.get("region")
    metrics = compute_context_features(lat, lon, region)
    return jsonify(metrics), 200

