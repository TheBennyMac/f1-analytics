import pytest
import pandas as pd
from src.analysis.overtake_index import (
    position_changes_per_race,
    overtake_index_per_race,
    overtake_index_by_circuit,
    monaco_vs_field,
    overtake_index_by_era,
)


_RESULTS_COLS = [
    "season", "round", "race_name", "driver_id",
    "driver_name", "grid_position", "finish_position", "status",
]

_RESULTS_DEFAULTS = {
    "season": 2022,
    "round": 1,
    "race_name": "Bahrain Grand Prix",
    "driver_id": "VER",
    "driver_name": "Max Verstappen",
    "grid_position": 1,
    "finish_position": 1,
    "status": "Finished",
}


def _make_results(rows: list[dict]) -> pd.DataFrame:
    """Build a minimal results_df for testing."""
    if not rows:
        return pd.DataFrame(columns=_RESULTS_COLS)
    records = [{**_RESULTS_DEFAULTS, **row} for row in rows]
    return pd.DataFrame(records)


class TestPositionChangesPerRace:
    def test_returns_correct_columns(self):
        df = _make_results([{}])
        result = position_changes_per_race(df)
        expected = {
            "season", "round", "race_name", "driver_id",
            "driver_name", "grid", "finish", "delta",
        }
        assert set(result.columns) == expected

    def test_delta_positive_for_gain(self):
        df = _make_results([
            {"driver_id": "LEC", "grid_position": 3, "finish_position": 1,
             "status": "Finished"},
        ])
        result = position_changes_per_race(df)
        assert result.iloc[0]["delta"] == 2

    def test_delta_negative_for_loss(self):
        df = _make_results([
            {"driver_id": "VER", "grid_position": 1, "finish_position": 3,
             "status": "Finished"},
        ])
        result = position_changes_per_race(df)
        assert result.iloc[0]["delta"] == -2

    def test_excludes_dnf(self):
        df = _make_results([
            {"driver_id": "VER", "grid_position": 1, "finish_position": 1,
             "status": "Finished"},
            {"driver_id": "LEC", "grid_position": 2, "finish_position": None,
             "status": "Accident"},
        ])
        result = position_changes_per_race(df)
        assert len(result) == 1
        assert result.iloc[0]["driver_id"] == "VER"

    def test_excludes_pit_lane_starter(self):
        df = _make_results([
            {"driver_id": "VER", "grid_position": 1, "finish_position": 1,
             "status": "Finished"},
            {"driver_id": "LEC", "grid_position": 0, "finish_position": 5,
             "status": "Finished"},
        ])
        result = position_changes_per_race(df)
        assert len(result) == 1
        assert result.iloc[0]["driver_id"] == "VER"

    def test_includes_lapped_finisher(self):
        df = _make_results([
            {"driver_id": "LAT", "grid_position": 20, "finish_position": 18,
             "status": "Lapped"},
        ])
        result = position_changes_per_race(df)
        assert len(result) == 1
        assert result.iloc[0]["delta"] == 2

    def test_includes_plus_laps_status(self):
        df = _make_results([
            {"driver_id": "LAT", "grid_position": 20, "finish_position": 18,
             "status": "+1 Lap"},
        ])
        result = position_changes_per_race(df)
        assert len(result) == 1

    def test_raises_on_missing_columns(self):
        df = pd.DataFrame({"driver_id": ["VER"]})
        with pytest.raises(ValueError, match="missing columns"):
            position_changes_per_race(df)

    def test_empty_input_returns_empty_dataframe(self):
        df = _make_results([])
        result = position_changes_per_race(df)
        assert result.empty
        assert "delta" in result.columns


class TestOvertakeIndexPerRace:
    def _two_driver_race(self) -> pd.DataFrame:
        return _make_results([
            {"driver_id": "VER", "grid_position": 2, "finish_position": 1,
             "status": "Finished"},
            {"driver_id": "LEC", "grid_position": 1, "finish_position": 2,
             "status": "Finished"},
        ])

    def test_returns_correct_columns(self):
        result = overtake_index_per_race(self._two_driver_race())
        expected = {
            "season", "round", "race_name", "starters",
            "finishers", "positions_gained", "mean_abs_delta",
            "overtake_index",
        }
        assert set(result.columns) == expected

    def test_positions_gained_counts_only_positive_deltas(self):
        result = overtake_index_per_race(self._two_driver_race())
        # VER gained 1 position; LEC lost 1 — positions_gained = 1
        assert result.iloc[0]["positions_gained"] == 1

    def test_overtake_index_normalised_by_starters(self):
        result = overtake_index_per_race(self._two_driver_race())
        # 1 position gained / 2 starters = 0.5
        assert result.iloc[0]["overtake_index"] == pytest.approx(0.5)

    def test_processional_race_has_zero_index(self):
        df = _make_results([
            {"driver_id": "VER", "grid_position": 1, "finish_position": 1,
             "status": "Finished"},
            {"driver_id": "LEC", "grid_position": 2, "finish_position": 2,
             "status": "Finished"},
        ])
        result = overtake_index_per_race(df)
        assert result.iloc[0]["overtake_index"] == 0.0

    def test_dnf_excluded_from_finishers_but_counted_in_starters(self):
        df = _make_results([
            {"driver_id": "VER", "grid_position": 1, "finish_position": 1,
             "status": "Finished"},
            {"driver_id": "LEC", "grid_position": 2, "finish_position": None,
             "status": "Accident"},
        ])
        result = overtake_index_per_race(df)
        assert result.iloc[0]["finishers"] == 1
        assert result.iloc[0]["starters"] == 2

    def test_empty_input_returns_empty_dataframe(self):
        df = _make_results([])
        result = overtake_index_per_race(df)
        assert result.empty

    def test_multiple_races_produce_multiple_rows(self):
        df = _make_results([
            {"round": 1, "race_name": "Bahrain Grand Prix",
             "driver_id": "VER", "grid_position": 1, "finish_position": 1,
             "status": "Finished"},
            {"round": 2, "race_name": "Monaco Grand Prix",
             "driver_id": "LEC", "grid_position": 2, "finish_position": 1,
             "status": "Finished"},
        ])
        result = overtake_index_per_race(df)
        assert len(result) == 2


class TestOvertakeIndexByCircuit:
    def _race_index(self) -> pd.DataFrame:
        return pd.DataFrame([
            {"season": 2022, "round": 1, "race_name": "Monaco Grand Prix",
             "starters": 20, "finishers": 18, "positions_gained": 3,
             "mean_abs_delta": 1.2, "overtake_index": 0.15},
            {"season": 2023, "round": 1, "race_name": "Monaco Grand Prix",
             "starters": 20, "finishers": 19, "positions_gained": 2,
             "mean_abs_delta": 1.0, "overtake_index": 0.10},
            {"season": 2022, "round": 5, "race_name": "Bahrain Grand Prix",
             "starters": 20, "finishers": 17, "positions_gained": 10,
             "mean_abs_delta": 3.5, "overtake_index": 0.50},
        ])

    def test_returns_correct_columns(self):
        result = overtake_index_by_circuit(self._race_index())
        expected = {
            "race_name", "races", "mean_overtake_index",
            "mean_positions_gained", "mean_abs_delta",
        }
        assert set(result.columns) == expected

    def test_sorted_ascending_by_overtake_index(self):
        result = overtake_index_by_circuit(self._race_index())
        assert result.iloc[0]["race_name"] == "Monaco Grand Prix"
        assert result.iloc[-1]["race_name"] == "Bahrain Grand Prix"

    def test_means_averaged_across_seasons(self):
        result = overtake_index_by_circuit(self._race_index())
        monaco = result[result["race_name"] == "Monaco Grand Prix"].iloc[0]
        assert monaco["mean_overtake_index"] == pytest.approx(0.125)
        assert monaco["races"] == 2

    def test_empty_input_returns_empty_dataframe(self):
        df = pd.DataFrame(
            columns=[
                "season", "round", "race_name", "starters",
                "finishers", "positions_gained", "mean_abs_delta",
                "overtake_index",
            ]
        )
        result = overtake_index_by_circuit(df)
        assert result.empty


class TestMonacoVsField:
    def _circuit_df(self) -> pd.DataFrame:
        return pd.DataFrame([
            {"race_name": "Monaco Grand Prix", "races": 4,
             "mean_overtake_index": 0.12, "mean_positions_gained": 2.5,
             "mean_abs_delta": 1.1},
            {"race_name": "Bahrain Grand Prix", "races": 4,
             "mean_overtake_index": 0.45, "mean_positions_gained": 8.0,
             "mean_abs_delta": 3.2},
            {"race_name": "Italian Grand Prix", "races": 4,
             "mean_overtake_index": 0.38, "mean_positions_gained": 7.0,
             "mean_abs_delta": 2.8},
        ])

    def test_adds_is_target_column(self):
        result = monaco_vs_field(self._circuit_df())
        assert "is_target" in result.columns

    def test_monaco_flagged_as_target(self):
        result = monaco_vs_field(self._circuit_df())
        monaco = result[result["race_name"] == "Monaco Grand Prix"].iloc[0]
        assert monaco["is_target"] == True

    def test_other_circuits_not_flagged(self):
        result = monaco_vs_field(self._circuit_df())
        others = result[result["race_name"] != "Monaco Grand Prix"]
        assert others["is_target"].sum() == 0

    def test_sorted_ascending(self):
        result = monaco_vs_field(self._circuit_df())
        indices = result["mean_overtake_index"].tolist()
        assert indices == sorted(indices)

    def test_custom_circuit_parameter(self):
        result = monaco_vs_field(
            self._circuit_df(), circuit="Italian Grand Prix"
        )
        italian = result[result["race_name"] == "Italian Grand Prix"].iloc[0]
        assert italian["is_target"] == True
        monaco = result[result["race_name"] == "Monaco Grand Prix"].iloc[0]
        assert monaco["is_target"] == False

    def test_no_match_all_false(self):
        result = monaco_vs_field(self._circuit_df(), circuit="Unknown GP")
        assert result["is_target"].sum() == 0


class TestOvertakeIndexByEra:
    def _race_index(self) -> pd.DataFrame:
        return pd.DataFrame([
            {"season": 2022, "round": 1, "race_name": "Bahrain Grand Prix",
             "overtake_index": 0.40, "positions_gained": 8, "finishers": 18},
            {"season": 2023, "round": 1, "race_name": "Bahrain Grand Prix",
             "overtake_index": 0.35, "positions_gained": 7, "finishers": 19},
            {"season": 2026, "round": 1, "race_name": "Australian Grand Prix",
             "overtake_index": 0.55, "positions_gained": 11, "finishers": 18},
        ])

    def test_returns_correct_columns(self):
        result = overtake_index_by_era(self._race_index())
        expected = {
            "era", "seasons", "races",
            "mean_overtake_index", "mean_positions_gained",
        }
        assert set(result.columns) == expected

    def test_groups_by_era_correctly(self):
        result = overtake_index_by_era(self._race_index())
        eras = set(result["era"].tolist())
        assert "Ground Effect Era" in eras
        assert "2026 Era" in eras

    def test_ground_effect_era_has_two_seasons(self):
        result = overtake_index_by_era(self._race_index())
        gee = result[result["era"] == "Ground Effect Era"].iloc[0]
        assert gee["seasons"] == 2
        assert gee["races"] == 2

    def test_mean_calculated_correctly(self):
        result = overtake_index_by_era(self._race_index())
        gee = result[result["era"] == "Ground Effect Era"].iloc[0]
        assert gee["mean_overtake_index"] == pytest.approx(0.375)

    def test_sorted_ascending_by_overtake_index(self):
        result = overtake_index_by_era(self._race_index())
        indices = result["mean_overtake_index"].tolist()
        assert indices == sorted(indices)

    def test_empty_input_returns_empty_dataframe(self):
        result = overtake_index_by_era(pd.DataFrame())
        assert result.empty
        assert "era" in result.columns

    def test_missing_season_column_returns_empty(self):
        df = pd.DataFrame({"overtake_index": [0.3], "positions_gained": [6]})
        result = overtake_index_by_era(df)
        assert result.empty
