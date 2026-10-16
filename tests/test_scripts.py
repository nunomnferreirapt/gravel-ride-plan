"""Pure functions of the skill scripts. No network: HTTP is mocked."""

from datetime import date
from unittest.mock import MagicMock


def test_wind_direction_compass_points(hourly_weather):
    assert hourly_weather._wind_direction(0) == "N"
    assert hourly_weather._wind_direction(90) == "E"
    assert hourly_weather._wind_direction(225) == "SW"
    assert hourly_weather._wind_direction(359) == "N"


def test_fetch_hourly_filters_window_and_shapes_rows(hourly_weather, monkeypatch):
    times = [f"2026-10-18T{h:02d}:00" for h in range(24)]
    hourly = {
        "time": times,
        "temperature_2m": [10.0] * 24,
        "apparent_temperature": [8.0] * 24,
        "precipitation_probability": [20] * 24,
        "precipitation": [0.0] * 24,
        "cloud_cover": [50] * 24,
        "wind_speed_10m": [12.0] * 24,
        "wind_gusts_10m": [25.0] * 24,
        "wind_direction_10m": [70.0] * 24,
        "uv_index": [2.5] * 24,
    }
    response = MagicMock()
    response.json.return_value = {"hourly": hourly}
    monkeypatch.setattr(hourly_weather.requests, "get", lambda *a, **k: response)

    result = hourly_weather.fetch_hourly(52.37, 4.90, "2026-10-18", 12, 15)

    assert result["window"] == "12:00-15:00"
    assert [row["time"] for row in result["hourly"]] == ["12:00", "13:00", "14:00", "15:00"]
    assert result["hourly"][0]["wind_dir"] == "ENE"
    assert result["hourly"][0]["feels_like_c"] == 8.0


def test_parse_date_flexible_handles_common_formats(scrape_events):
    assert scrape_events.parse_date_flexible("2026-03-28") == date(2026, 3, 28)
    assert scrape_events.parse_date_flexible("28 Mar", year=2026) == date(2026, 3, 28)
    assert scrape_events.parse_date_flexible("March 28, 2026") == date(2026, 3, 28)
    assert scrape_events.parse_date_flexible("not a date") is None


def test_is_nearby_and_date_range(scrape_events):
    assert scrape_events.is_nearby("Hilversum, Netherlands")
    assert scrape_events.is_nearby("")  # unknown location is kept
    assert not scrape_events.is_nearby("Maastricht")
    start, end = date(2026, 3, 28), date(2026, 3, 30)
    assert scrape_events.in_date_range(date(2026, 3, 29), start, end)
    assert not scrape_events.in_date_range(date(2026, 4, 1), start, end)
    assert scrape_events.in_date_range(None, start, end)


def test_scrape_maats_parses_shopify_products(scrape_events, monkeypatch):
    pages = [
        {"products": [
            {
                "title": "Maats Gravel Ride Utrecht - Sat 28 March",
                "handle": "gravel-ride-utrecht",
                "tags": ["gravel"],
                "variants": [{"title": "Default Title", "available": True, "price": "0.00"}],
            },
            {
                "title": "Club Membership", "handle": "membership", "tags": [],
                "variants": [{"title": "Default Title", "available": True, "price": "50.00"}],
            },
        ]},
        {"products": []},
    ]
    responses = iter(pages)

    def fake_get(*a, **k):
        r = MagicMock()
        r.json.return_value = next(responses)
        return r

    monkeypatch.setattr(scrape_events.requests, "get", fake_get)
    events = scrape_events.scrape_maats(date(2026, 3, 27), date(2026, 3, 29))

    assert len(events) == 1
    assert events[0]["gravel"] is True
    assert events[0]["location"] == "Utrecht"
    assert events[0]["date"] == "2026-03-28"
    assert events[0]["price"] == "Free"
