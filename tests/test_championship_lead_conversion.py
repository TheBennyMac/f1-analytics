"""Tests for championship_lead_conversion analysis module."""

import pandas as pd
import pytest

from src.analysis.championship_lead_conversion import (
    conversion_rate_summary,
    mid_season_leaders,
)


def _make_standings(season: int, rounds: int, teams: dict[str, list[float]]) -> pd.DataFrame:
    """Build standings DataFrame from a dict of {constructor_id: [pts_per_round]}."""
    rows = []
    cumulative = {c: 0.0 for c in teams}
    for rnd in range(1, rounds + 1):
        for constructor_id, pts_per_round in teams.items():
            pts = pts_per_round[rnd - 1] if rnd <= len(pts_per_round) else 0.0
            cumulative[constructor_id] += pts
            rows.append({
                "season": season,
                "round": rnd,
                "constructor_id": constructor_id,
                "constructor_name": constructor_id.title(),
                "points": cumulative[constructor_id],
            })
    return pd.DataFrame(rows)


def test_mid_season_leaders_identifies_leader():
    # Mercedes leads every round comfortably
    df = _make_standings(2014, 10, {
        "mercedes": [50] * 10,
        "red_bull": [20] * 10,
    })
    result = mid_season_leaders(df, min_round=4)
    assert len(result) == 1
    assert result.iloc[0]["constructor_id"] == "mercedes"
    assert result.iloc[0]["won_title"] == True  # noqa: E712 — numpy bool needs ==


def test_mid_season_leaders_excludes_early_rounds():
    # ferrari scores big in round 1 only; red_bull overtakes by round 4
    # ferrari cumulative: 80, 80, 80, 80 ...
    # red_bull cumulative: 10, 30, 60, 160 (takes lead at round 4)
    df = _make_standings(2014, 10, {
        "ferrari": [80, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "red_bull": [10, 20, 30, 100, 100, 100, 100, 100, 100, 100],
    })
    result = mid_season_leaders(df, min_round=4)
    assert "ferrari" not in result["constructor_id"].values
    assert "red_bull" in result["constructor_id"].values


def test_mid_season_leaders_only_up_to_midpoint():
    # ferrari only overtakes in rounds 8-10 (past midpoint=5 for 10-round season)
    # red_bull leads rounds 4-7; ferrari leads 8+
    df = _make_standings(2014, 10, {
        "ferrari": [10, 10, 10, 10, 10, 10, 10, 100, 100, 100],
        "red_bull": [50, 50, 50, 50, 50, 50, 50, 0, 0, 0],
    })
    result = mid_season_leaders(df, min_round=4)
    assert "red_bull" in result["constructor_id"].values
    assert "ferrari" not in result["constructor_id"].values


def test_mid_season_leaders_won_title_false_when_not_champion():
    # ferrari leads at rounds 4-5, but red_bull scores heavily late and wins
    # ferrari cumulative: 80, 160, 180, 200, 220 ... 260
    # red_bull cumulative: 10, 20, 30, 80, 180 ... overtakes at round 5-6
    df = _make_standings(2022, 10, {
        "ferrari": [80, 80, 20, 20, 20, 5, 5, 5, 5, 5],
        "red_bull": [10, 10, 10, 50, 100, 80, 80, 80, 80, 80],
    })
    result = mid_season_leaders(df, min_round=4)
    ferrari_row = result[result["constructor_id"] == "ferrari"]
    assert len(ferrari_row) == 1
    assert ferrari_row.iloc[0]["won_title"] == False  # noqa: E712


def test_mid_season_leaders_era_label():
    df = _make_standings(2022, 10, {"red_bull": [50] * 10})
    result = mid_season_leaders(df, min_round=4)
    assert result.iloc[0]["era_name"] == "Ground Effect Era"


def test_conversion_rate_summary_basic():
    df = _make_standings(2014, 10, {
        "mercedes": [50] * 10,
        "red_bull": [20] * 10,
    })
    leads = mid_season_leaders(df, min_round=4)
    summary = conversion_rate_summary(leads)
    merc = summary[summary["constructor_id"] == "mercedes"].iloc[0]
    assert merc["seasons_led"] == 1
    assert merc["titles_won"] == 1
    assert merc["conversion_rate"] == pytest.approx(1.0)


def test_conversion_rate_summary_zero_conversion():
    # 2 seasons — ferrari leads both at mid-season but mercedes wins both clearly
    df_a = _make_standings(2017, 10, {
        "ferrari": [80, 80, 20, 20, 20, 5, 5, 5, 5, 5],   # leads early, fades
        "mercedes": [10, 10, 50, 80, 80, 80, 80, 80, 80, 80],
    })
    df_b = _make_standings(2018, 10, {
        "ferrari": [80, 80, 20, 20, 20, 5, 5, 5, 5, 5],
        "mercedes": [10, 10, 50, 80, 80, 80, 80, 80, 80, 80],
    })
    leads = mid_season_leaders(pd.concat([df_a, df_b], ignore_index=True), min_round=4)
    summary = conversion_rate_summary(leads, constructors=["ferrari"])
    ferrari = summary.iloc[0]
    assert ferrari["seasons_led"] == 2
    assert ferrari["titles_won"] == 0
    assert ferrari["conversion_rate"] == 0.0


def test_conversion_rate_summary_seasons_list():
    df = pd.concat([
        _make_standings(2017, 10, {"ferrari": [50] * 10, "mercedes": [20] * 10}),
        _make_standings(2018, 10, {"ferrari": [50] * 10, "mercedes": [20] * 10}),
    ], ignore_index=True)
    leads = mid_season_leaders(df, min_round=4)
    summary = conversion_rate_summary(leads, constructors=["ferrari"])
    assert "2017" in summary.iloc[0]["seasons_list"]
    assert "2018" in summary.iloc[0]["seasons_list"]
