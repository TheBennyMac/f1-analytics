"""
Jolpica-F1 API client — Ergast-compatible community mirror.

Provides historical constructor standings and race results for pre-2022 seasons
that are not covered by FastF1. Base URL: https://api.jolpi.ca/ergast/f1/

Results are cached to data/cache/jolpica/ to avoid repeated API calls.
"""

import json
import time
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

_BASE_URL = "https://api.jolpi.ca/ergast/f1"
_REQUEST_DELAY_S = 0.35  # Jolpica rate limit is 4 req/s; stay safely below it
_CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "cache" / "jolpica"


def _cache_path(key: str) -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR / f"{key}.json"


def _get(path: str) -> dict:
    """GET from Jolpica with a polite delay. Returns parsed JSON dict."""
    time.sleep(_REQUEST_DELAY_S)
    url = f"{_BASE_URL}/{path.lstrip('/')}"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return resp.json()


def get_constructor_standings_by_round(season: int) -> pd.DataFrame:
    """Return cumulative constructor standings after each round for a season.

    Cached at data/cache/jolpica/constructor_standings_{season}.json.

    Returns DataFrame with columns:
        season, round, constructor_id, constructor_name, points, position
    """
    cache_key = f"constructor_standings_{season}"
    cache_file = _cache_path(cache_key)

    if cache_file.exists():
        rows = json.loads(cache_file.read_text(encoding="utf-8"))
        return pd.DataFrame(rows)

    # Fetch round count first
    races_data = _get(f"/{season}/races.json?limit=30")
    races = races_data["MRData"]["RaceTable"]["Races"]
    total_rounds = len(races)

    rows: list[dict] = []
    for rnd in range(1, total_rounds + 1):
        data = _get(f"/{season}/{rnd}/constructorStandings.json")
        lists = data["MRData"]["StandingsTable"]["StandingsLists"]
        if not lists:
            continue
        for entry in lists[0]["ConstructorStandings"]:
            rows.append({
                "season": season,
                "round": rnd,
                "constructor_id": entry["Constructor"]["constructorId"],
                "constructor_name": entry["Constructor"]["name"],
                "points": float(entry["points"]),
                "position": int(entry["position"]) if "position" in entry else None,
            })

    cache_file.write_text(json.dumps(rows), encoding="utf-8")
    return pd.DataFrame(rows)


def get_race_results(season: int) -> pd.DataFrame:
    """Return race-by-race results for a season (all drivers, all rounds).

    Cached at data/cache/jolpica/race_results_{season}.json.

    Returns DataFrame with columns:
        season, round, race_name, driver_id, constructor_id,
        position, status, points, laps, gap_ms
    where gap_ms is milliseconds behind the winner (0 for winner, NaN for DNFs).
    """
    cache_key = f"race_results_{season}"
    cache_file = _cache_path(cache_key)

    if cache_file.exists():
        rows = json.loads(cache_file.read_text(encoding="utf-8"))
        return pd.DataFrame(rows)

    # Fetch with pagination (up to 1000 results covers a full season)
    data = _get(f"/{season}/results.json?limit=1000")
    races = data["MRData"]["RaceTable"]["Races"]

    rows = []
    for race in races:
        rnd = int(race["round"])
        race_name = race["raceName"]
        for res in race["Results"]:
            pos_str = res.get("position", "")
            pos = int(pos_str) if pos_str.isdigit() else None
            time_data = res.get("Time", {})
            gap_ms: Optional[int] = None
            if "millis" in time_data:
                gap_ms = int(time_data["millis"])
            rows.append({
                "season": season,
                "round": rnd,
                "race_name": race_name,
                "driver_id": res["Driver"]["driverId"],
                "constructor_id": res["Constructor"]["constructorId"],
                "position": pos,
                "status": res["status"],
                "points": float(res["points"]),
                "laps": int(res["laps"]),
                "gap_ms": gap_ms,
            })

    cache_file.write_text(json.dumps(rows), encoding="utf-8")
    return pd.DataFrame(rows)
