import pytest
import pandas as pd
from src.analysis.quali_race_delta import (
    position_delta,
    quali_race_delta,
    mean_delta_by_driver,
    mean_delta_by_constructor,
)


class TestPositionDelta:
    def test_gained_positions(self):
        assert position_delta(5, 2) == 3

    def test_lost_positions(self):
        assert position_delta(2, 5) == -3

    def test_no_change(self):
        assert position_delta(3, 3) == 0

    def test_dnf_returns_none(self):
        assert position_delta(5, None) is None


class TestQualiRaceDelta:
    def _make_results(self):
        return pd.DataFrame([
            {"season": 2022, "round": 1, "race_name": "Bahrain GP",
             "driver_id": "VER", "driver_name": "Verstappen",
             "constructor_id": "red_bull",
             "grid_position": 1, "finish_position": 1, "status": "Finished"},
            {"season": 2022, "round": 1, "race_name": "Bahrain GP",
             "driver_id": "LEC", "driver_name": "Leclerc",
             "constructor_id": "ferrari",
             "grid_position": 3, "finish_position": None, "status": "Engine"},
            {"season": 2022, "round": 1, "race_name": "Bahrain GP",
             "driver_id": "SAI", "driver_name": "Sainz",
             "constructor_id": "ferrari",
             "grid_position": 2, "finish_position": 2, "status": "Finished"},
        ])

    def test_delta_calculated_correctly(self):
        result = quali_race_delta(self._make_results())
        ver = result[result["driver_id"] == "VER"].iloc[0]
        assert ver["delta"] == 0

    def test_dnf_has_none_delta(self):
        result = quali_race_delta(self._make_results())
        lec = result[result["driver_id"] == "LEC"].iloc[0]
        assert lec["delta"] is None or pd.isna(lec["delta"])
        assert lec["dnf"] == True

    def test_dnf_flag_set_correctly(self):
        result = quali_race_delta(self._make_results())
        sai = result[result["driver_id"] == "SAI"].iloc[0]
        assert sai["dnf"] == False


class TestMeanDeltaByDriver:
    def test_excludes_dnfs(self):
        df = pd.DataFrame([
            {"driver_id": "VER", "driver_name": "Verstappen", "constructor_id": "red_bull",
             "delta": 2.0, "dnf": False},
            {"driver_id": "VER", "driver_name": "Verstappen", "constructor_id": "red_bull",
             "delta": None, "dnf": True},
            {"driver_id": "LEC", "driver_name": "Leclerc", "constructor_id": "ferrari",
             "delta": -1.0, "dnf": False},
        ])
        result = mean_delta_by_driver(df)
        ver = result[result["driver_id"] == "VER"].iloc[0]
        assert ver["races"] == 1
        assert ver["mean_delta"] == pytest.approx(2.0)

    def test_sorted_best_converters_first(self):
        df = pd.DataFrame([
            {"driver_id": "VER", "driver_name": "V", "constructor_id": "rb", "delta": 3.0, "dnf": False},
            {"driver_id": "LEC", "driver_name": "L", "constructor_id": "fer", "delta": -1.0, "dnf": False},
        ])
        result = mean_delta_by_driver(df)
        assert result.iloc[0]["driver_id"] == "VER"


class TestMeanDeltaByConstructor:
    def test_aggregates_across_drivers(self):
        df = pd.DataFrame([
            {"constructor_id": "ferrari", "delta": 2.0, "dnf": False},
            {"constructor_id": "ferrari", "delta": 0.0, "dnf": False},
            {"constructor_id": "red_bull", "delta": 1.0, "dnf": False},
        ])
        result = mean_delta_by_constructor(df)
        fer = result[result["constructor_id"] == "ferrari"].iloc[0]
        assert fer["mean_delta"] == pytest.approx(1.0)
