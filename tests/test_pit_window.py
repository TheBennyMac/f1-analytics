import pytest
import pandas as pd
from datetime import timedelta
from src.analysis.pit_window import (
    median_pit_lap,
    lap_time_deltas_by_phase,
    pit_window_summary,
)


def _make_race_laps(
    drivers: list[str],
    total_laps: int,
    pit_lap: int,
    base_time: float = 90.0,
    post_spread: float = 0.0,
) -> pd.DataFrame:
    """Build a minimal multi-driver race laps DataFrame.

    All drivers pit on the same lap. Pre-pit laps are close together;
    post-pit laps have additional spread if post_spread > 0.
    """
    rows = []
    for i, driver in enumerate(drivers):
        for lap in range(1, total_laps + 1):
            is_pit_in = lap == pit_lap
            is_pit_out = lap == pit_lap + 1
            lap_time = base_time + i * 0.2  # baseline spread between drivers
            if is_pit_in or is_pit_out:
                lap_time += 25.0  # pit stop adds ~25s
            elif lap > pit_lap and post_spread > 0:
                lap_time += i * post_spread  # extra spread post-stop
            rows.append({
                "Driver": driver,
                "LapNumber": lap,
                "LapTime": timedelta(seconds=lap_time),
                "PitInLap": is_pit_in,
                "PitOutLap": is_pit_out,
                "IsAccurate": not (is_pit_in or is_pit_out),
            })
    return pd.DataFrame(rows)


class TestMedianPitLap:
    def test_returns_correct_median(self):
        laps = _make_race_laps(["VER", "LEC", "HAM", "SAI", "RUS"], 30, pit_lap=15)
        result = median_pit_lap(laps)
        assert result == pytest.approx(15.0)

    def test_returns_none_when_no_pit_laps(self):
        laps = pd.DataFrame([
            {"Driver": "VER", "LapNumber": 1, "PitInLap": False}
        ])
        result = median_pit_lap(laps)
        assert result is None

    def test_returns_none_when_column_missing(self):
        laps = pd.DataFrame([{"Driver": "VER", "LapNumber": 1}])
        result = median_pit_lap(laps)
        assert result is None

    def test_uses_first_stop_per_driver(self):
        # VER pits on lap 10, LEC on lap 20 — median should be 15
        rows = [
            {"Driver": "VER", "LapNumber": 10, "PitInLap": True},
            {"Driver": "VER", "LapNumber": 30, "PitInLap": True},
            {"Driver": "LEC", "LapNumber": 20, "PitInLap": True},
        ]
        result = median_pit_lap(pd.DataFrame(rows))
        assert result == pytest.approx(15.0)


class TestLapTimeDeltasByPhase:
    def _make_simple_laps(self, n_drivers: int = 6) -> pd.DataFrame:
        return _make_race_laps(
            [f"D{i:02d}" for i in range(n_drivers)], total_laps=30, pit_lap=15
        )

    def test_returns_four_keys(self):
        laps = self._make_simple_laps()
        result = lap_time_deltas_by_phase(laps, split_lap=15.0)
        assert set(result.keys()) == {"pre_mean_gap_s", "post_mean_gap_s", "pre_laps", "post_laps"}

    def test_pre_laps_less_than_split(self):
        laps = self._make_simple_laps()
        result = lap_time_deltas_by_phase(laps, split_lap=15.0)
        # Pre phase: laps 1-14 (14 distinct laps, minus pit-adjacent laps)
        assert result["pre_laps"] > 0

    def test_post_laps_from_split_onward(self):
        laps = self._make_simple_laps()
        result = lap_time_deltas_by_phase(laps, split_lap=15.0)
        assert result["post_laps"] > 0

    def test_none_when_phase_has_insufficient_drivers(self):
        # Only 2 drivers — P1-P3 gap requires 3; should return None
        laps = _make_race_laps(["VER", "LEC"], total_laps=30, pit_lap=15)
        result = lap_time_deltas_by_phase(laps, split_lap=15.0)
        assert result["pre_mean_gap_s"] is None
        assert result["post_mean_gap_s"] is None

    def test_post_spread_increases_post_gap(self):
        # With extra post-pit spread, post gap should be larger than pre gap
        laps_spread = _make_race_laps(
            [f"D{i:02d}" for i in range(6)], total_laps=30, pit_lap=15, post_spread=2.0
        )
        result = lap_time_deltas_by_phase(laps_spread, split_lap=15.0)
        if result["pre_mean_gap_s"] is not None and result["post_mean_gap_s"] is not None:
            assert result["post_mean_gap_s"] >= result["pre_mean_gap_s"]


class TestPitWindowSummary:
    def _make_season_laps(self) -> dict:
        laps = _make_race_laps(
            [f"D{i:02d}" for i in range(6)], total_laps=30, pit_lap=15
        )
        return {(2022, 1): laps, (2022, 2): laps}

    def test_returns_one_row_per_race(self):
        result = pit_window_summary(self._make_season_laps())
        assert len(result) == 2

    def test_includes_split_lap_column(self):
        result = pit_window_summary(self._make_season_laps())
        assert "split_lap" in result.columns

    def test_excludes_races_with_no_pit_stops(self):
        # Sprint-style laps with no PitInLap column
        laps = pd.DataFrame([
            {"Driver": "VER", "LapNumber": i, "LapTime": timedelta(seconds=90.0)}
            for i in range(1, 25)
        ])
        result = pit_window_summary({(2022, 1): laps})
        assert result.empty

    def test_correct_columns(self):
        result = pit_window_summary(self._make_season_laps())
        expected = {"season", "round", "split_lap", "pre_mean_gap_s", "post_mean_gap_s",
                    "pre_laps", "post_laps"}
        assert set(result.columns) == expected
