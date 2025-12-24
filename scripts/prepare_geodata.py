#!/usr/bin/env python
"""Prepare geospatial layers for the flood platform.

This script ingests the raw shapefiles downloaded from GeoSenegal and
produces two assets:

* A geopackage per region (``flood_api/models/geodata/<region>.gpkg``)
  with each thematic layer normalised in EPSG:4326.
* A manifest JSON (``flood_api/models/geodata_manifest.json``) used by
  the API/frontend to discover available layers and metadata.

Usage
-----

```
python scripts/prepare_geodata.py --source flood_api/models --dest flood_api/models/geodata
```

The script requires ``geopandas`` and ``pyogrio``. Install the forecast
service requirements (``pip install -r flood_api/services/forecast_service/requirements.txt``)
before running it locally.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Iterable

import geopandas as gpd


LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("flood_api/models"),
        help="Directory containing <region>_shapefile folders",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path("flood_api/models/geodata"),
        help="Output directory for geopackages",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("flood_api/models/geodata_manifest.json"),
        help="Output manifest path",
    )
    parser.add_argument(
        "--crs",
        default="EPSG:4326",
        help="Target CRS for all layers",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing geopackages",
    )
    return parser.parse_args()


def discover_regions(source: Path) -> Iterable[tuple[str, Path]]:
    for folder in sorted(source.glob("*_shapefile")):
        if folder.is_dir():
            region = folder.stem.replace("_shapefile", "")
            yield region, folder


def ingest_region(region: str, src: Path, dest: Path, crs: str, force: bool) -> dict:
    dest.mkdir(parents=True, exist_ok=True)
    geopackage = dest / f"{region}.gpkg"
    if geopackage.exists() and not force:
        LOGGER.info("Skip %s (already exists)", region)
    layers_meta: list[dict] = []

    for layer_dir in sorted(src.iterdir()):
        if not layer_dir.is_dir():
            continue
        shp = next(layer_dir.glob("*.shp"), None)
        if not shp:
            continue
        layer_name = layer_dir.stem
        LOGGER.info("Processing %s/%s", region, layer_name)
        gdf = gpd.read_file(shp).to_crs(crs)

        # Drop metadata or problematic columns (ArcGIS exports)
        drop_cols = []
        for col in gdf.columns:
            upper = col.upper()
            lower = col.lower()
            if upper.startswith("SHAPE_") or lower in {"type", "fid", "elevation", "name"}:
                drop_cols.append(col)
        if drop_cols:
            gdf = gdf.drop(columns=drop_cols)

        # Normalise column names (length <= 30, no spaces)
        rename_map = {}
        for col in gdf.columns:
            new_name = col.strip().replace(" ", "_").replace("-", "_")[:30]
            if new_name in rename_map.values():
                suffix = 1
                while f"{new_name}_{suffix}" in rename_map.values():
                    suffix += 1
                new_name = f"{new_name}_{suffix}"[:30]
            rename_map[col] = new_name
        gdf = gdf.rename(columns=rename_map)

        # Cast object columns to strings to avoid mixed-type schemas
        geometry_col = gdf.geometry.name
        safe_dtypes = {"int64", "float64", "bool"}
        for col in list(gdf.columns):
            if col == geometry_col:
                continue

            dtype = gdf[col].dtype.name
            if dtype in safe_dtypes:
                continue

            if dtype == "object":
                def _coerce(val):
                    if isinstance(val, (dict, list, tuple, set)):
                        return json.dumps(val, ensure_ascii=False)
                    return "" if val is None else str(val)

                gdf[col] = gdf[col].map(_coerce)
            else:
                gdf[col] = gdf[col].astype(str)

        gdf["region"] = region
        gdf["layer"] = layer_name
        gdf.to_file(geopackage, layer=layer_name, driver="GPKG")

        bounds = (
            gdf.total_bounds.tolist()
            if geometry_col in gdf.columns and len(gdf)
            else [None, None, None, None]
        )
        layers_meta.append(
            {
                "name": layer_name,
                "feature_count": int(len(gdf)),
                "geometry_type": gdf.geom_type.unique().tolist(),
                "bounds": bounds,
            }
        )

    return {
        "region": region,
        "geopackage": geopackage.as_posix(),
        "layers": layers_meta,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()

    manifest: dict[str, dict] = {}
    for region, folder in discover_regions(args.source):
        region_meta = ingest_region(region, folder, args.dest, args.crs, args.force)
        manifest[region] = region_meta

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest.open("w", encoding="utf-8") as fh:
        json.dump({"regions": manifest}, fh, indent=2, ensure_ascii=False)
    LOGGER.info("Manifest written to %s", args.manifest)


if __name__ == "__main__":
    main()
