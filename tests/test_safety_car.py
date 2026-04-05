import pytest
import pandas as pd
from src.analysis.safety_car import (
    sc_counts_per_race,
    sc_position_impact,
    sc_lottery_summary,
    intervention_frequency,
)


_RACE_COLS = [
    "season", "round", "race_name",
    "sc_count", "vsc_count", "red_flag_count",
]

_RACE_DEFAULTS = {
    "season": 2022,
    "round": 1,
    "race_name": "Bahrain Grand Prix",
    "sc_count": 0,
    "vsc_count": 0,
    "red_flag_count": 0,
}


def _make_results(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=_RACE_COLS + ["driver_id"])
    records = [{**_RACE_DEFAULTS, "driver_id": "VER", **row} for row in rows]
    return pd.DataFrame(records)


def _make_sc_df(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=_RACE_COLS + ["any_intervention"])
    records = [{**_RACE_DEFAULTS, **row} for row in rows]
    df = pd.DataFrame(records)
    if "any_intervention" not in df.columns:
        df["any_intervention"] = (
            (df["sc_count"] > 0) |
            (df["vsc_count"] > 0) |
            (df["red_flag_count"] > 0)
        )
    return df


def _make_race_oi(rows: list[dict]) -> pd.DataFrame:
    defaults = {
        "season": 2022, "round": 1, "race_name": "Bahrain Grand Prix",
        "overtake_index": 0.3, "positions_gained": 6, "finishers": 18,
    }
    records = [{**defaults, **row} for row in rows]
    return pd.DataFrame(records)


class TestScCountsPerRace:
    def test_returns_one_row_per_race(self):
        df = _make_results([
            {"driver_id": "VER"},
            {"driver_id": "LEC"},
        ])
        result = sc_counts_per_race(df)
        assert len(result) == 1

    def test_returns_correct_columns(self):
        df = _make_results([{}])
        result = sc_counts_per_race(df)
        expected = {
            "season", "round", "race_name",
            "sc_count", "vsc_count", "red_flag_count", "any_intervention",
        }
        assert set(result.columns) == expected

    def test_any_intervention_true_when_sc(self):
        df = _make_results([{"sc_count": 1}])
        result = sc_counts_per_race(df)
        assert result.iloc[0]["any_intervention"] == True

    def test_any_intervention_true_when_vsc(self):
        df = _make_results([{"vsc_count": 1}])
        result = sc_counts_per_race(df)
        assert result.iloc[0]["any_intervention"] == True

    def test_any_intervention_true_when_red_flag(self):
        df = _make_results([{"red_flag_count": 1}])
        result = sc_counts_per_race(df)
        assert result.iloc[0]["any_intervention"] == True

    def test_any_intervention_false_when_clean(self):
        df = _make_results([{}])
        result = sc_counts_per_race(df)
        assert result.iloc[0]["any_intervention"] == False

    def test_multiple_races_produce_multiple_rows(self):
        df = _make_results([
            {"round": 1, "race_name": "Bahrain Grand Prix"},
            {"round": 2, "race_name": "Monaco Grand Prix"},
        ])
        result = sc_counts_per_race(df)
        assert len(result) == 2

    def test_raises_on_missing_columns(self):
        df = pd.DataFrame({"season": [2022]})
        with pytest.raises(ValueError, match="missing columns"):
            sc_counts_per_race(df)

    def test_sorted_by_season_and_round(self):
        df = _make_results([
            {"season": 2022, "round": 3, "race_name": "C"},
            {"season": 2022, "round": 1, "race_name": "A"},
            {"season": 2022, "round": 2, "race_name": "B"},
        ])
        result = sc_counts_per_race(df)
        assert result["round"].tolist() == [1, 2, 3]


class TestScPositionImpact:
    def _sc(self):
        return _make_sc_df([
            {"round": 1, "race_name": "Bahrain Grand Prix", "sc_count": 1},
            {"round": 2, "race_name": "Monaco Grand Prix", "sc_count": 0},
        ])

    def _oi(self):
        return _make_race_oi([
            {"round": 1, "overtake_index": 0.4},
            {"round": 2, "overtake_index": 0.15},
        ])

    def test_returns_correct_columns(self):
        result = sc_position_impact(self._sc(), self._oi())
        expected = {
            "season", "round", "race_name", "sc_count", "vsc_count",
            "red_flag_count", "any_intervention",
            "overtake_index", "positions_gained", "finishers",
        }
        assert set(result.columns) == expected

    def test_joins_on_season_and_round(self):
        result = sc_position_impact(self._sc(), self._oi())
        assert len(result) == 2

    def test_sc_race_has_correct_overtake_index(self):
        result = sc_position_impact(self._sc(), self._oi())
        bahrain = result[result["round"] == 1].iloc[0]
        assert bahrain["overtake_index"] == pytest.approx(0.4)
        assert bahrain["sc_count"] == 1

    def test_excludes_races_with_no_overtake_data(self):
        sc = _make_sc_df([
            {"round": 1}, {"round": 2}, {"round": 3},
        ])
        oi = _make_race_oi([{"round": 1}, {"round": 2}])
        result = sc_position_impact(sc, oi)
        assert len(result) == 2

    def test_empty_sc_returns_empty(self):
        sc = _make_sc_df([])
        oi = _make_race_oi([{}])
        result = sc_position_impact(sc, oi)
        assert result.empty


class TestScLotterySummary:
    def _impact(self):
        return pd.DataFrame([
            {"sc_count": 0, "overtake_index": 0.20, "positions_gained": 4},
            {"sc_count": 0, "overtake_index": 0.25, "positions_gained": 5},
            {"sc_count": 1, "overtake_index": 0.35, "positions_gained": 7},
            {"sc_count": 1, "overtake_index": 0.40, "positions_gained": 8},
            {"sc_count": 2, "overtake_index": 0.55, "positions_gained": 11},
        ])

    def test_returns_correct_columns(self):
        result = sc_lottery_summary(self._impact())
        expected = {
            "sc_group", "races", "mean_overtake_index", "mean_positions_gained"
        }
        assert set(result.columns) == expected

    def test_groups_correctly(self):
        result = sc_lottery_summary(self._impact())
        assert set(result["sc_group"].tolist()) == {"0 SCs", "1 SC", "2+ SCs"}

    def test_sorted_ascending_by_group(self):
        result = sc_lottery_summary(self._impact())
        assert result["sc_group"].tolist() == ["0 SCs", "1 SC", "2+ SCs"]

    def test_mean_calculated_correctly(self):
        result = sc_lottery_summary(self._impact())
        no_sc = result[result["sc_group"] == "0 SCs"].iloc[0]
        assert no_sc["mean_overtake_index"] == pytest.approx(0.225)
        assert no_sc["races"] == 2

    def test_two_plus_sc_grouped(self):
        result = sc_lottery_summary(self._impact())
        two_plus = result[result["sc_group"] == "2+ SCs"].iloc[0]
        assert two_plus["races"] == 1

    def test_empty_returns_empty(self):
        result = sc_lottery_summary(pd.DataFrame())
        assert result.empty


class TestInterventionFrequency:
    def _sc_df(self):
        return _make_sc_df([
            {"season": 2022, "round": 1, "race_name": "A", "sc_count": 1},
            {"season": 2022, "round": 2, "race_name": "B", "sc_count": 0},
            {"season": 2022, "round": 3, "race_name": "C", "sc_count": 0, "vsc_count": 1},
            {"season": 2023, "round": 1, "race_name": "D", "sc_count": 2},
        ])

    def test_returns_correct_columns(self):
        result = intervention_frequency(self._sc_df())
        expected = {
            "season", "total_races", "sc_races", "vsc_races",
            "red_flag_races", "clean_races", "sc_rate",
        }
        assert set(result.columns) == expected

    def test_one_row_per_season(self):
        result = intervention_frequency(self._sc_df())
        assert len(result) == 2

    def test_sc_rate_calculated(self):
        result = intervention_frequency(self._sc_df())
        s2022 = result[result["season"] == 2022].iloc[0]
        assert s2022["sc_rate"] == pytest.approx(1 / 3, rel=0.01)
        assert s2022["total_races"] == 3

    def test_clean_races_counted(self):
        result = intervention_frequency(self._sc_df())
        s2022 = result[result["season"] == 2022].iloc[0]
        # Round 2 has no SC/VSC/red flag
        assert s2022["clean_races"] == 1

    def test_empty_returns_empty(self):
        result = intervention_frequency(_make_sc_df([]))
        assert result.empty
