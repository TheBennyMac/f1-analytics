import os
import time
from typing import Any, Optional

import requests

_BASE_URL = os.getenv("OPENF1_BASE_URL", "https://api.openf1.org/v1")
_REQUEST_DELAY_S = 0.5  # Polite delay between requests; no official rate limit documented


def _get(endpoint: str, params: Optional[dict] = None) -> list[dict[str, Any]]:
    """Make a GET request to the OpenF1 API and return the JSON response.

    Raises requests.HTTPError on non-2xx responses.
    """
    url = f"{_BASE_URL}/{endpoint.lstrip('/')}"
    time.sleep(_REQUEST_DELAY_S)
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def get_sessions(year: int, session_type: Optional[str] = None) -> list[dict[str, Any]]:
    """Return all sessions for a season, optionally filtered by type.

    Args:
        year: Championship season year.
        session_type: Optional filter — 'Race', 'Qualifying', 'Practice 1', etc.
    """
    params: dict[str, Any] = {"year": year}
    if session_type:
        params["session_type"] = session_type
    return _get("sessions", params)


def get_drivers(session_key: int) -> list[dict[str, Any]]:
    """Return all driver entries for a given session."""
    return _get("drivers", {"session_key": session_key})


def get_laps(session_key: int, driver_number: Optional[int] = None) -> list[dict[str, Any]]:
    """Return lap data for a session, optionally filtered to a single driver."""
    params: dict[str, Any] = {"session_key": session_key}
    if driver_number is not None:
        params["driver_number"] = driver_number
    return _get("laps", params)


def get_pit_stops(session_key: int) -> list[dict[str, Any]]:
    """Return pit stop records for a session."""
    return _get("pit", {"session_key": session_key})


def get_race_control(session_key: int) -> list[dict[str, Any]]:
    """Return race control events (flags, safety car, VSC) for a session."""
    return _get("race_control", {"session_key": session_key})


def get_positions(session_key: int) -> list[dict[str, Any]]:
    """Return driver position data throughout a session."""
    return _get("position", {"session_key": session_key})
