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


def get_race_control_flags(session: fastf1.core.Session) -> dict:
    """Return a dict of race control flags for a loaded session.

    Inspects race_control_messages for safety car deployments, virtual safety
    car deployments, and red flags.

    Args:
        session: A loaded FastF1 Session object (must already have .load() called).

    Returns:
        Dict with keys: had_sc (bool), had_vsc (bool), had_red_flag (bool).
    """
    try:
        rcm = session.race_control_messages
        if rcm is None or rcm.empty:
            return {"had_sc": False, "had_vsc": False, "had_red_flag": False}
        # Red flag: use the structured Flag column — 'RED' is unambiguous.
        # SC/VSC: not stored as Flag values; detected via Message text.
        #   VSC check first, then SC excludes rows that mention 'VIRTUAL'
        #   to avoid 'VIRTUAL SAFETY CAR DEPLOYED' matching the SC pattern.
        messages = (
            rcm["Message"].fillna("").str.upper()
            if "Message" in rcm.columns
            else pd.Series([], dtype=str)
        )
        flags = rcm["Flag"].fillna("") if "Flag" in rcm.columns else pd.Series([], dtype=str)
        had_red_flag = (flags == "RED").any()
        had_vsc = messages.str.contains("VIRTUAL SAFETY CAR DEPLOYED").any()
        had_sc = (
            messages.str.contains("SAFETY CAR DEPLOYED") &
            ~messages.str.contains("VIRTUAL")
        ).any()
    except Exception:
        return {"had_sc": False, "had_vsc": False, "had_red_flag": False}
    return {"had_sc": bool(had_sc), "had_vsc": bool(had_vsc), "had_red_flag": bool(had_red_flag)}


def get_event_schedule(year: int) -> pd.DataFrame:
    """Return the full event schedule for a season."""
    _ensure_cache()
    return fastf1.get_event_schedule(year)
