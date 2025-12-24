#!/usr/bin/env python3
"""
Fetch hourly weather observations from the OpenWeather One Call API and export
them as a CSV compatible with the modelling pipeline.

Example:
    export OPENWEATHER_API_KEY=...
    python scripts/fetch_openweather.py --lat 14.6937 --lon -17.4441 \
        --location dakar_plateau --hours 48 \
        --output flood_api/donnees/openweather_dakar_latest.csv
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import requests


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download hourly weather from OpenWeather.")
    parser.add_argument("--lat", type=float, required=True, help="Latitude in decimal degrees.")
    parser.add_argument("--lon", type=float, required=True, help="Longitude in decimal degrees.")
    parser.add_argument(
        "--location",
        type=str,
        default="unknown_location",
        help="Identifier used for the location column in the exported CSV.",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=48,
        help="Number of future hours to fetch (max 48 for free tier).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("openweather_latest.csv"),
        help="Path where the CSV will be saved.",
    )
    parser.add_argument(
        "--units",
        choices=["metric", "standard", "imperial"],
        default="metric",
        help="Units to request from the API. The pipeline expects metric values.",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        help="Optional path to store the raw JSON payload for debugging.",
    )
    return parser


def fetch_openweather(lat: float, lon: float, api_key: str, units: str, hours: int) -> Dict[str, Any]:
    url = "https://api.openweathermap.org/data/2.5/onecall"
    params = {
        "lat": lat,
        "lon": lon,
        "units": units,
        "appid": api_key,
        "exclude": "minutely,daily,alerts",
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if hours < len(payload.get("hourly", [])):
        payload["hourly"] = payload["hourly"][:hours]
    return payload


def normalise_hourly(payload: Dict[str, Any], location: str) -> pd.DataFrame:
    records: List[Dict[str, Any]] = []
    tz_offset_seconds = payload.get("timezone_offset", 0)
    hourly_data = payload.get("hourly", [])

    for entry in hourly_data:
        ts_utc = dt.datetime.fromtimestamp(entry["dt"], tz=dt.timezone.utc)
        ts_local = ts_utc + dt.timedelta(seconds=tz_offset_seconds)
        rain_mm = entry.get("rain", {}).get("1h", 0.0)
        snow_mm = entry.get("snow", {}).get("1h", 0.0)

        records.append(
            {
                "time": ts_local.replace(microsecond=0).isoformat(),
                "precipitation (mm)": round(rain_mm + snow_mm, 3),
                "rain (mm)": round(rain_mm, 3),
                "relative_humidity_2m (%)": entry.get("humidity"),
                "temperature_2m (°C)": entry.get("temp"),
                "dew_point_2m (°C)": entry.get("dew_point"),
                "pressure_msl (hPa)": entry.get("pressure"),
                "wind_speed_10m (km/h)": convert_ms_to_kmh(entry.get("wind_speed")),
                "wind_gusts_10m (km/h)": convert_ms_to_kmh(entry.get("wind_gust")),
                "cloud_cover (%)": entry.get("clouds"),
                "shortwave_radiation (W/m²)": entry.get("uvi"),
                "location": location,
            }
        )

    if not records:
        raise ValueError("No hourly records returned by the API.")

    frame = pd.DataFrame.from_records(records)
    return frame.sort_values("time")


def convert_ms_to_kmh(value: Any) -> float:
    if value is None:
        return 0.0
    return float(value) * 3.6


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise SystemExit("Missing OPENWEATHER_API_KEY environment variable.")

    payload = fetch_openweather(args.lat, args.lon, api_key, args.units, args.hours)
    if args.metadata:
        args.metadata.parent.mkdir(parents=True, exist_ok=True)
        args.metadata.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    hourly_df = normalise_hourly(payload, args.location)
    # enrich metadata row with coordinates and timezone when available
    metadata = {
        "latitude": payload.get("lat"),
        "longitude": payload.get("lon"),
        "elevation": "",
        "utc_offset_seconds": payload.get("timezone_offset", 0),
        "timezone": payload.get("timezone"),
        "timezone_abbreviation": payload.get("timezone", ""),
    }
    write_csv_with_metadata(hourly_df, args.output, metadata)
    print(f"Saved {len(hourly_df)} hourly rows to {args.output}")


def write_csv_with_metadata(frame: pd.DataFrame, output_path: Path, metadata: Dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    meta_columns = [
        "latitude",
        "longitude",
        "elevation",
        "utc_offset_seconds",
        "timezone",
        "timezone_abbreviation",
    ]
    metadata_values = [metadata.get(col, "") for col in meta_columns]
    with output_path.open("w", encoding="utf-8") as fh:
        fh.write(",".join(meta_columns) + "\n")
        fh.write(",".join(str(v) for v in metadata_values) + "\n\n")
        frame.drop(columns=["location"], errors="ignore").to_csv(fh, index=False)


if __name__ == "__main__":
    main()
