import os
from pathlib import Path
from typing import Optional

import fastf1
import pandas as pd

_CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "cache"
_cache_enabled = False


def _ensure_cache() -> None:
    global _cache_enabled
    if not _cache_enabled:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        fastf1.Cache.enable_cache(str(_CACHE_DIR))
        _cache_enabled = True


def load_session(year: int, event: str | int, session_type: str) -> fastf1.core.Session:
    """Load a FastF1 session with caching enabled.

    Args:
        year: Championship season year.
        event: Round number (int) or event name (str), e.g. 'Bahrain' or 1.
        session_type: 'R' (race), 'Q' (qualifying), 'FP1', 'FP2', 'FP3', 'S' (sprint).

    Returns:
        A loaded FastF1 Session object.
    """
    _ensure_cache()
    session = fastf1.get_session(year, event, session_type)
    session.load()
    return session


def get_race_laps(year: int, event: str | int) -> pd.DataFrame:
    """Return all laps for a race session as a DataFrame."""
    session = load_session(year, event, "R")
    return session.laps


def get_qualifying_laps(year: int, event: str | int) -> pd.DataFrame:
    """Return all laps for a qualifying session as a DataFrame."""
    session = load_session(year, event, "Q")
    return session.laps


def get_session_results(year: int, event: str | int, session_type: str) -> pd.DataFrame:
    """Return the results table for any session type."""
    session = load_session(year, event, session_type)
    return session.results


def get_event_schedule(year: int) -> pd.DataFrame:
    """Return the full event schedule for a season."""
    _ensure_cache()
    return fastf1.get_event_schedule(year)
