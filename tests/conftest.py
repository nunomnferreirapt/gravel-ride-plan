"""Load the two skill scripts as modules so their pure functions can be tested."""

import importlib.util
import sys
from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parent.parent / "skills"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def hourly_weather():
    return _load("hourly_weather", SKILLS / "gravel-ride-timing" / "scripts" / "hourly_weather.py")


@pytest.fixture(scope="session")
def scrape_events():
    return _load("scrape_events", SKILLS / "gravel-ride-events" / "scripts" / "scrape_events.py")
