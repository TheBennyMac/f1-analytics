import pytest
import pandas as pd
from datetime import timedelta
from src.analysis.sprint_analysis import (
    sprint_position_changes,
    sprint_vs_race_pace,
    flag_sprint_weekends,
)


def _make_sprint_results(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def _make_laps(driver_lap_pairs: list[tuple[str, float]]) -> pd.DataFrame:
    """Build a laps DataFrame from [(driver, lap_seconds)] — repeated per lap."""
    rows = []
    for driver, seconds in driver_lap_pairs:
        rows.append({
            "Driver": driver,
            "LapTime": timedelta(seconds=seconds),
            "PitOutLap": False,
            "PitInLap": False,
        })
    return pd.DataFrame(rows)


class TestSprintPositionChanges:
    def _results(self) -> pd.DataFrame:
        return _make_sprint_results([
            {"Abbreviation": "VER", "TeamName": "Red Bull", "GridPosition": 1, "Position": 1},
            {"Abbreviation": "LEC", "TeamName": "Ferrari", "GridPosition": 3, "Position": 2},
            {"Abbreviation": "SAI", "TeamName": "Ferrari", "GridPosition": 2, "Position": 3},
        ])

    def test_returns_correct_columns(self):
        result = sprint_position_changes(self._results())
        assert set(result.columns) == {"driver", "team", "grid", "finish", "delta"}

    def test_delta_positive_for_position_gain(self):
        result = sprint_position_changes(self._results())
        lec = result[result["driver"] == "LEC"].iloc[0]
        assert lec["delta"] == 1  # grid 3 -> finish 2 = +1

    def test_delta_negative_for_position_loss(self):
        result = sprint_position_changes(self._results())
        sai = result[result["driver"] == "SAI"].iloc[0]
        assert sai["delta"] == -1  # grid 2 -> finish 3 = -1

    def test_excludes_invalid_positions(self):
        results = _make_sprint_results([
            {"Abbreviation": "VER", "TeamName": "Red Bull", "GridPosition": None, "Position": 1},
            {"Abbreviation": "LEC", "TeamName": "Ferrari", "GridPosition": 2, "Position": 2},
        ])
        result = sprint_position_changes(results)
        assert len(result) == 1
        assert result.iloc[0]["driver"] == "LEC"

    def test_empty_results_returns_empty_df(self):
        result = sprint_position_changes(pd.DataFrame())
        assert result.empty

    def test_sorted_by_finish_position(self):
        result = sprint_position_changes(self._results())
        assert list(result["finish"]) == [1, 2, 3]


class TestSprintVsRacePace:
    def _sprint_laps(self) -> pd.DataFrame:
        return _make_laps([("VER", 90.0), ("VER", 90.5), ("LEC", 91.0), ("LEC", 91.2)])

    def _race_laps(self) -> pd.DataFrame:
        return _make_laps([("VER", 92.0), ("VER", 92.5), ("LEC", 93.0), ("LEC", 93.5)])

    def test_returns_correct_columns(self):
        result = sprint_vs_race_pace(self._sprint_laps(), self._race_laps())
        assert set(result.columns) == {"driver", "sprint_median_s", "race_median_s", "delta_s"}

    def test_delta_positive_when_race_slower(self):
        result = sprint_vs_race_pace(self._sprint_laps(), self._race_laps())
        # Both drivers slower in race
        assert (result["delta_s"] > 0).all()

    def test_only_includes_drivers_in_both_sessions(self):
        sprint = _make_laps([("VER", 90.0), ("HAM", 91.0)])
        race = _make_laps([("VER", 92.0), ("LEC", 93.0)])
        result = sprint_vs_race_pace(sprint, race)
        assert set(result["driver"]) == {"VER"}

    def test_fastf1_pit_time_columns_exclude_pit_laps(self):
        """FastF1 native format: PitOutTime/PitInTime timestamps; NaT = clean lap."""
        sprint = pd.DataFrame([
            {"Driver": "VER", "LapTime": timedelta(seconds=70.0),
             "PitOutTime": pd.NaT, "PitInTime": pd.NaT},
        ])
        race = pd.DataFrame([
            {"Driver": "VER", "LapTime": timedelta(seconds=90.0),
             "PitOutTime": pd.Timestamp("2022-01-01"), "PitInTime": pd.NaT},  # pit-out lap
            {"Driver": "VER", "LapTime": timedelta(seconds=92.0),
             "PitOutTime": pd.NaT, "PitInTime": pd.NaT},
        ])
        result = sprint_vs_race_pace(sprint, race)
        assert result.iloc[0]["race_median_s"] == pytest.approx(92.0)

    def test_empty_when_no_common_drivers(self):
        sprint = _make_laps([("VER", 90.0)])
        race = _make_laps([("LEC", 91.0)])
        result = sprint_vs_race_pace(sprint, race)
        assert result.empty


class TestFlagSprintWeekends:
    def test_deduplicates_to_one_row_per_round(self):
        df = pd.DataFrame([
            {"season": 2022, "round": 4, "is_sprint_weekend": True, "driver": "VER"},
            {"season": 2022, "round": 4, "is_sprint_weekend": True, "driver": "LEC"},
            {"season": 2022, "round": 5, "is_sprint_weekend": False, "driver": "VER"},
        ])
        result = flag_sprint_weekends(df)
        assert len(result) == 2

    def test_raises_on_missing_column(self):
        df = pd.DataFrame([{"season": 2022, "round": 1}])
        with pytest.raises(ValueError, match="is_sprint_weekend"):
            flag_sprint_weekends(df)

    def test_preserves_sprint_flag_values(self):
        df = pd.DataFrame([
            {"season": 2022, "round": 4, "is_sprint_weekend": True},
            {"season": 2022, "round": 5, "is_sprint_weekend": False},
        ])
        result = flag_sprint_weekends(df)
        sprint_rounds = result[result["is_sprint_weekend"]]["round"].tolist()
        assert sprint_rounds == [4]
