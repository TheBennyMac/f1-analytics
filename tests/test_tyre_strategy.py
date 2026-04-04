import pytest
import pandas as pd
from src.analysis.tyre_strategy import (
    stints_from_laps,
    strategy_summary,
    mean_stint_length,
    compound_usage_by_constructor,
)


def _make_laps(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def _simple_laps() -> pd.DataFrame:
    """Two drivers, two stints each, one team each."""
    rows = []
    # VER: SOFT stint 1 (10 laps), MEDIUM stint 2 (15 laps)
    for lap in range(1, 11):
        rows.append({"Driver": "VER", "Team": "Red Bull", "Stint": 1,
                     "Compound": "SOFT", "LapNumber": lap,
                     "PitOutLap": False, "PitInLap": False})
    rows.append({"Driver": "VER", "Team": "Red Bull", "Stint": 1,
                 "Compound": "SOFT", "LapNumber": 10,
                 "PitOutLap": False, "PitInLap": True})
    for lap in range(11, 26):
        rows.append({"Driver": "VER", "Team": "Red Bull", "Stint": 2,
                     "Compound": "MEDIUM", "LapNumber": lap,
                     "PitOutLap": False, "PitInLap": False})
    # LEC: MEDIUM stint 1 (12 laps), HARD stint 2 (13 laps)
    for lap in range(1, 13):
        rows.append({"Driver": "LEC", "Team": "Ferrari", "Stint": 1,
                     "Compound": "MEDIUM", "LapNumber": lap,
                     "PitOutLap": False, "PitInLap": False})
    for lap in range(13, 26):
        rows.append({"Driver": "LEC", "Team": "Ferrari", "Stint": 2,
                     "Compound": "HARD", "LapNumber": lap,
                     "PitOutLap": False, "PitInLap": False})
    return pd.DataFrame(rows)


class TestStintsFromLaps:
    def test_returns_one_row_per_driver_stint(self):
        laps = _simple_laps()
        # Remove pit laps to avoid duplicates
        laps = laps[~laps["PitInLap"]]
        result = stints_from_laps(laps)
        # VER: 2 stints, LEC: 2 stints
        assert len(result) == 4

    def test_excludes_pit_in_laps_from_count(self):
        # VER has 10 laps in stint 1 but one is a PitInLap
        laps = _simple_laps()
        result = stints_from_laps(laps)
        ver_s1 = result[(result["driver"] == "VER") & (result["stint"] == 1)]
        assert ver_s1.iloc[0]["laps"] == 10  # PitInLap excluded

    def test_excludes_unknown_compound(self):
        rows = [
            {"Driver": "VER", "Team": "Red Bull", "Stint": 1,
             "Compound": "UNKNOWN", "LapNumber": 1,
             "PitOutLap": False, "PitInLap": False},
        ]
        result = stints_from_laps(pd.DataFrame(rows))
        assert len(result) == 0

    def test_fastf1_pit_time_columns_exclude_pit_laps(self):
        """FastF1 native format: PitInTime/PitOutTime timestamps; NaT = clean lap.
        tyre_strategy has no IsAccurate fallback, so this is the only guard."""
        rows = []
        for lap in range(1, 11):
            rows.append({"Driver": "VER", "Team": "Red Bull", "Stint": 1,
                         "Compound": "SOFT", "LapNumber": lap,
                         "PitInTime": pd.Timestamp("2022-01-01") if lap == 10 else pd.NaT,
                         "PitOutTime": pd.NaT})
        for lap in range(11, 21):
            rows.append({"Driver": "VER", "Team": "Red Bull", "Stint": 2,
                         "Compound": "MEDIUM", "LapNumber": lap,
                         "PitInTime": pd.NaT,
                         "PitOutTime": pd.Timestamp("2022-01-01") if lap == 11 else pd.NaT})
        result = stints_from_laps(pd.DataFrame(rows))
        ver_s1 = result[(result["driver"] == "VER") & (result["stint"] == 1)]
        assert ver_s1.iloc[0]["laps"] == 9  # pit-in lap on lap 10 excluded
        ver_s2 = result[(result["driver"] == "VER") & (result["stint"] == 2)]
        assert ver_s2.iloc[0]["laps"] == 9  # pit-out lap on lap 11 excluded

    def test_raises_on_missing_columns(self):
        with pytest.raises(ValueError, match="Missing columns"):
            stints_from_laps(pd.DataFrame([{"Driver": "VER"}]))

    def test_compound_correctly_assigned(self):
        laps = _simple_laps()
        result = stints_from_laps(laps)
        ver_s1 = result[(result["driver"] == "VER") & (result["stint"] == 1)]
        assert ver_s1.iloc[0]["compound"] == "SOFT"


class TestStrategySummary:
    def test_one_row_per_driver(self):
        result = strategy_summary(_simple_laps())
        assert len(result) == 2
        assert set(result["driver"]) == {"VER", "LEC"}

    def test_num_stops_correct(self):
        result = strategy_summary(_simple_laps())
        assert result[result["driver"] == "VER"].iloc[0]["num_stops"] == 1
        assert result[result["driver"] == "LEC"].iloc[0]["num_stops"] == 1

    def test_compounds_used_in_stint_order(self):
        result = strategy_summary(_simple_laps())
        ver = result[result["driver"] == "VER"].iloc[0]
        assert ver["compounds_used"] == "SOFT, MEDIUM"

    def test_empty_laps_returns_empty(self):
        laps = pd.DataFrame(columns=["Driver", "Team", "Stint", "Compound", "LapNumber"])
        result = strategy_summary(laps)
        assert result.empty


class TestMeanStintLength:
    def test_returns_one_row_per_compound(self):
        result = mean_stint_length(_simple_laps())
        # SOFT (VER), MEDIUM (VER+LEC), HARD (LEC)
        assert set(result["compound"]) == {"SOFT", "MEDIUM", "HARD"}

    def test_mean_lap_calculation(self):
        result = mean_stint_length(_simple_laps())
        soft = result[result["compound"] == "SOFT"].iloc[0]
        # VER: SOFT stint has 10 non-pit laps (PitInLap row excluded)
        assert soft["mean_laps"] == pytest.approx(10.0, abs=0.5)


class TestCompoundUsageByConstructor:
    def test_aggregates_across_rounds(self):
        laps = _simple_laps()
        season_laps = {(2022, 1): laps, (2022, 2): laps}
        result = compound_usage_by_constructor(season_laps)
        assert set(result["season"].unique()) == {2022}
        assert set(result["round"].unique()) == {1, 2}

    def test_returns_empty_on_missing_columns(self):
        bad_laps = pd.DataFrame([{"Driver": "VER"}])
        result = compound_usage_by_constructor({(2022, 1): bad_laps})
        assert result.empty
