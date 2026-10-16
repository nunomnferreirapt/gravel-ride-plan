#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests>=2.28"]
# ///
"""Fetch hourly weather from Open-Meteo for a specific ride window.

Usage:
    uv run hourly_weather.py --lat 52.374 --lon 4.89 --date 2026-03-22 --start-hour 12 --end-hour 15

Output: JSON with hourly breakdown to stdout. No API key needed.
Dependencies: requests (resolved by uv from the header above, or install it yourself and use python3).
"""

import argparse
import json
import sys

import requests


def fetch_hourly(lat: float, lon: float, target_date: str,
                 start_hour: int, end_hour: int) -> dict:
    """Fetch hourly weather from Open-Meteo API for a specific window."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "precipitation_probability",
            "precipitation",
            "cloud_cover",
            "wind_speed_10m",
            "wind_gusts_10m",
            "wind_direction_10m",
            "uv_index",
        ]),
        "start_date": target_date,
        "end_date": target_date,
        "timezone": "Europe/Amsterdam",
        "wind_speed_unit": "kmh",
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        print(f"Error fetching weather: {e}", file=sys.stderr)
        return {}

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])

    # Filter to requested hour range
    hours = []
    for i, time_str in enumerate(times):
        hour = int(time_str.split("T")[1].split(":")[0])
        if start_hour <= hour <= end_hour:
            hours.append({
                "time": time_str.split("T")[1][:5],
                "temp_c": hourly["temperature_2m"][i],
                "feels_like_c": hourly["apparent_temperature"][i],
                "rain_prob_pct": hourly["precipitation_probability"][i],
                "rain_mm": hourly["precipitation"][i],
                "cloud_pct": hourly["cloud_cover"][i],
                "wind_kmh": hourly["wind_speed_10m"][i],
                "gusts_kmh": hourly["wind_gusts_10m"][i],
                "wind_dir": _wind_direction(hourly["wind_direction_10m"][i]),
                "uv_index": hourly["uv_index"][i],
            })

    return {
        "date": target_date,
        "window": f"{start_hour:02d}:00-{end_hour:02d}:00",
        "location": {"lat": lat, "lon": lon},
        "hourly": hours,
    }


def _wind_direction(degrees: float) -> str:
    """Convert wind direction degrees to compass direction."""
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = round(degrees / 22.5) % 16
    return dirs[idx]


def main():
    parser = argparse.ArgumentParser(description="Fetch hourly weather for a ride window")
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    parser.add_argument("--start-hour", type=int, required=True, help="Start hour (0-23)")
    parser.add_argument("--end-hour", type=int, required=True, help="End hour (0-23)")
    args = parser.parse_args()

    result = fetch_hourly(args.lat, args.lon, args.date, args.start_hour, args.end_hour)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
