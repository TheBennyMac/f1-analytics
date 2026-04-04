import pytest
import pandas as pd
from datetime import timedelta
from src.analysis.lap_time_delta import (
    fastest_lap_per_driver,
    p1_to_pn_gap,
    lap_time_delta_summary,
    mean_gap_by_season,
)


def _make_laps(driver_times: dict[str, float]) -> pd.DataFrame:
    """Helper: build a minimal laps DataFrame from {driver: lap_seconds}."""
    rows = []
    for driver, seconds in driver_times.items():
        rows.append({
            "Driver": driver,
            "LapTime": timedelta(seconds=seconds),
            "PitOutLap": False,
            "PitInLap": False,
        })
    return pd.DataFrame(rows)


class TestFastestLapPerDriver:
    def test_returns_one_row_per_driver(self):
        laps = _make_laps({"VER": 90.0, "LEC": 91.0, "HAM": 92.0})
        result = fastest_lap_per_driver(laps)
        assert len(result) == 3

    def test_sorted_fastest_first(self):
        laps = _make_laps({"VER": 90.0, "LEC": 91.0, "HAM": 92.0})
        result = fastest_lap_per_driver(laps)
        assert result.iloc[0]["driver"] == "VER"

    def test_excludes_pit_out_laps(self):
        rows = [
            {"Driver": "VER", "LapTime": timedelta(seconds=85.0), "PitOutLap": True, "PitInLap": False},
            {"Driver": "VER", "LapTime": timedelta(seconds=90.0), "PitOutLap": False, "PitInLap": False},
        ]
        result = fastest_lap_per_driver(pd.DataFrame(rows))
        assert result.iloc[0]["fastest_lap_s"] == pytest.approx(90.0)

    def test_fastf1_pit_time_columns_exclude_pit_laps(self):
        """FastF1 native format: PitInTime/PitOutTime are timestamps; NaT = clean lap."""
        rows = [
            {"Driver": "VER", "LapTime": timedelta(seconds=85.0),
             "PitOutTime": pd.Timestamp("2022-01-01 01:00:00"), "PitInTime": pd.NaT},
            {"Driver": "VER", "LapTime": timedelta(seconds=90.0),
             "PitOutTime": pd.NaT, "PitInTime": pd.NaT},
        ]
        result = fastest_lap_per_driver(pd.DataFrame(rows))
        assert result.iloc[0]["fastest_lap_s"] == pytest.approx(90.0)


class TestP1ToPnGap:
    def test_gap_calculated_correctly(self):
        times = {f"D{i}": 90.0 + i for i in range(15)}
        laps = _make_laps(times)
        gap = p1_to_pn_gap(laps, n=10)
        assert gap == pytest.approx(9.0, abs=0.01)

    def test_returns_none_when_too_few_drivers(self):
        laps = _make_laps({"VER": 90.0, "LEC": 91.0})
        assert p1_to_pn_gap(laps, n=10) is None


class TestLapTimeDeltaSummary:
    def test_returns_correct_shape(self):
        times = {f"D{i}": 90.0 + i for i in range(15)}
        season_laps = {(2022, 1): _make_laps(times), (2022, 2): _make_laps(times)}
        result = lap_time_delta_summary(season_laps)
        assert len(result) == 2
        assert set(result.columns) == {"season", "round", "p1_lap_s", "p10_lap_s", "gap_s"}

    def test_skips_races_with_too_few_drivers(self):
        few_drivers = _make_laps({"VER": 90.0, "LEC": 91.0})
        result = lap_time_delta_summary({(2022, 1): few_drivers})
        assert len(result) == 0


class TestMeanGapBySeason:
    def test_aggregates_correctly(self):
        df = pd.DataFrame([
            {"season": 2022, "round": 1, "gap_s": 10.0},
            {"season": 2022, "round": 2, "gap_s": 8.0},
            {"season": 2023, "round": 1, "gap_s": 6.0},
        ])
        result = mean_gap_by_season(df)
        assert result[result["season"] == 2022].iloc[0]["mean_gap_s"] == pytest.approx(9.0)
        assert result[result["season"] == 2022].iloc[0]["races"] == 2
