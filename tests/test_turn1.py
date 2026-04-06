import pytest
import pandas as pd
from src.analysis.turn1 import (
    first_lap_retirements,
    lap1_position_changes,
    turn1_summary_by_era_year,
)


_RESULTS_COLS = [
    "season", "round", "race_name",
    "driver_id", "grid_position", "finish_position", "status",
]

_RESULTS_DEFAULTS = {
    "season": 2022, "round": 1, "race_name": "Bahrain Grand Prix",
    "driver_id": "VER", "grid_position": 1, "finish_position": 1,
    "status": "Finished",
}


def _make_results(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=_RESULTS_COLS)
    return pd.DataFrame([{**_RESULTS_DEFAULTS, **r} for r in rows])


def _make_laps(rows: list[dict]) -> pd.DataFrame:
    defaults = {
        "Driver": "VER", "LapNumber": 1,
        "Position": 1, "GridPosition": 1,
    }
    return pd.DataFrame([{**defaults, **r} for r in rows])


class TestFirstLapRetirements:
    def test_returns_correct_columns(self):
        df = _make_results([{}])
        result = first_lap_retirements(df)
        expected = {
            "season", "round", "race_name", "era_year",
            "starters", "first_lap_dnfs", "dnf_rate",
        }
        assert set(result.columns) == expected

    def test_one_row_per_race(self):
        df = _make_results([
            {"driver_id": "VER"}, {"driver_id": "LEC"},
        ])
        result = first_lap_retirements(df)
        assert len(result) == 1

    def test_counts_unclassified_dnf_as_first_lap(self):
        df = _make_results([
            {"driver_id": "VER", "finish_position": 1, "status": "Finished"},
            {"driver_id": "LEC", "finish_position": None, "status": "Accident"},
        ])
        result = first_lap_retirements(df)
        assert result.iloc[0]["first_lap_dnfs"] == 1

    def test_classified_dnf_not_counted(self):
        # Driver finished but classified as lapped — not a first-lap DNF
        df = _make_results([
            {"driver_id": "VER", "finish_position": 1, "status": "Finished"},
            {"driver_id": "LAT", "finish_position": 18, "status": "Lapped"},
        ])
        result = first_lap_retirements(df)
        assert result.iloc[0]["first_lap_dnfs"] == 0

    def test_pit_lane_starter_excluded(self):
        df = _make_results([
            {"driver_id": "VER", "grid_position": 1, "finish_position": 1,
             "status": "Finished"},
            {"driver_id": "LEC", "grid_position": 0, "finish_position": None,
             "status": "Accident"},
        ])
        result = first_lap_retirements(df)
        assert result.iloc[0]["starters"] == 1
        assert result.iloc[0]["first_lap_dnfs"] == 0

    def test_dnf_rate_calculated(self):
        df = _make_results([
            {"driver_id": "VER", "finish_position": 1, "status": "Finished"},
            {"driver_id": "LEC", "finish_position": None, "status": "Accident"},
            {"driver_id": "SAI", "finish_position": 2, "status": "Finished"},
            {"driver_id": "HAM", "finish_position": 3, "status": "Finished"},
        ])
        result = first_lap_retirements(df)
        assert result.iloc[0]["dnf_rate"] == pytest.approx(0.25)

    def test_era_year_populated(self):
        df = _make_results([{}])
        result = first_lap_retirements(df)
        assert result.iloc[0]["era_year"] == 1  # 2022 = Year 1 of Ground Effect Era

    def test_multiple_races_produce_multiple_rows(self):
        df = _make_results([
            {"round": 1, "race_name": "Bahrain Grand Prix"},
            {"round": 2, "race_name": "Monaco Grand Prix"},
        ])
        result = first_lap_retirements(df)
        assert len(result) == 2

    def test_raises_on_missing_columns(self):
        df = pd.DataFrame({"driver_id": ["VER"]})
        with pytest.raises(ValueError, match="missing columns"):
            first_lap_retirements(df)

    def test_empty_input_returns_empty(self):
        df = _make_results([])
        result = first_lap_retirements(df)
        assert result.empty

    def test_season_laps_filters_by_lap_count(self):
        # Simulate FastF1 behaviour: all 20 drivers get a finish_position,
        # even if they retired on lap 1. Without season_laps the function
        # would see no NaN finish_positions and return 0 DNFs.
        # With season_laps, the driver who only completed 1 lap is flagged.
        df = _make_results([
            {"driver_id": "VER", "finish_position": 1, "status": "Finished"},
            {"driver_id": "ZHO", "finish_position": 19, "status": "Collision"},
        ])
        laps = pd.DataFrame([
            {"Driver": "VER", "LapNumber": i} for i in range(1, 21)
        ] + [
            {"Driver": "ZHO", "LapNumber": 1},  # retired after 1 lap
        ])
        season_laps = {(2022, 1): laps}
        result = first_lap_retirements(df, season_laps=season_laps)
        assert result.iloc[0]["first_lap_dnfs"] == 1

    def test_season_laps_does_not_count_late_dnf(self):
        # Driver who retired on lap 45 should NOT count as first-lap DNF
        df = _make_results([
            {"driver_id": "VER", "finish_position": 1, "status": "Finished"},
            {"driver_id": "LEC", "finish_position": 18, "status": "Engine"},
        ])
        laps = pd.DataFrame(
            [{"Driver": "VER", "LapNumber": i} for i in range(1, 51)]
            + [{"Driver": "LEC", "LapNumber": i} for i in range(1, 46)]
        )
        season_laps = {(2022, 1): laps}
        result = first_lap_retirements(df, season_laps=season_laps)
        assert result.iloc[0]["first_lap_dnfs"] == 0


class TestLap1PositionChanges:
    def test_returns_correct_keys(self):
        laps = _make_laps([{}])
        result = lap1_position_changes(laps)
        assert set(result.keys()) == {"positions_gained", "drivers"}

    def test_detects_position_gain(self):
        laps = _make_laps([
            {"Driver": "VER", "LapNumber": 1, "GridPosition": 3, "Position": 1},
            {"Driver": "LEC", "LapNumber": 1, "GridPosition": 1, "Position": 2},
            {"Driver": "SAI", "LapNumber": 1, "GridPosition": 2, "Position": 3},
        ])
        result = lap1_position_changes(laps)
        # VER gained 2 positions; others lost
        assert result["positions_gained"] == 2

    def test_no_gains_returns_zero(self):
        laps = _make_laps([
            {"Driver": "VER", "LapNumber": 1, "GridPosition": 1, "Position": 1},
            {"Driver": "LEC", "LapNumber": 1, "GridPosition": 2, "Position": 2},
        ])
        result = lap1_position_changes(laps)
        assert result["positions_gained"] == 0

    def test_missing_position_column_returns_none(self):
        df = pd.DataFrame({"Driver": ["VER"], "LapNumber": [1]})
        result = lap1_position_changes(df)
        assert result["positions_gained"] is None

    def test_missing_grid_position_returns_none(self):
        df = pd.DataFrame({
            "Driver": ["VER"], "LapNumber": [1], "Position": [1],
        })
        result = lap1_position_changes(df)
        assert result["positions_gained"] is None

    def test_excludes_pit_lane_starters(self):
        laps = _make_laps([
            {"Driver": "VER", "LapNumber": 1, "GridPosition": 1, "Position": 1},
            {"Driver": "LEC", "LapNumber": 1, "GridPosition": 0, "Position": 2},
        ])
        result = lap1_position_changes(laps)
        assert result["drivers"] == 1

    def test_empty_returns_none(self):
        result = lap1_position_changes(_make_laps([]))
        assert result["positions_gained"] is None


class TestTurn1SummaryByEraYear:
    def _retirement_df(self) -> pd.DataFrame:
        return pd.DataFrame([
            {"season": 2022, "round": 1, "race_name": "A",
             "era_year": 1, "starters": 20, "first_lap_dnfs": 2, "dnf_rate": 0.10},
            {"season": 2022, "round": 2, "race_name": "B",
             "era_year": 1, "starters": 20, "first_lap_dnfs": 0, "dnf_rate": 0.00},
            {"season": 2023, "round": 1, "race_name": "C",
             "era_year": 2, "starters": 20, "first_lap_dnfs": 1, "dnf_rate": 0.05},
        ])

    def test_returns_correct_columns(self):
        result = turn1_summary_by_era_year(self._retirement_df())
        expected = {
            "era_year", "races", "mean_starters",
            "total_first_lap_dnfs", "mean_dnf_rate",
        }
        assert set(result.columns) == expected

    def test_one_row_per_era_year(self):
        result = turn1_summary_by_era_year(self._retirement_df())
        assert len(result) == 2

    def test_sorted_by_era_year(self):
        result = turn1_summary_by_era_year(self._retirement_df())
        assert result["era_year"].tolist() == [1, 2]

    def test_total_dnfs_summed(self):
        result = turn1_summary_by_era_year(self._retirement_df())
        year1 = result[result["era_year"] == 1].iloc[0]
        assert year1["total_first_lap_dnfs"] == 2

    def test_mean_dnf_rate_averaged(self):
        result = turn1_summary_by_era_year(self._retirement_df())
        year1 = result[result["era_year"] == 1].iloc[0]
        assert year1["mean_dnf_rate"] == pytest.approx(0.05)

    def test_empty_input_returns_empty(self):
        result = turn1_summary_by_era_year(pd.DataFrame())
        assert result.empty
