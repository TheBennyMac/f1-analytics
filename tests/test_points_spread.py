import pytest
import pandas as pd
from src.analysis.points_spread import (
    gini_coefficient,
    points_gini_by_round,
    points_gap_by_round,
    season_end_gini,
)


class TestGiniCoefficient:
    def test_perfect_equality(self):
        assert gini_coefficient([10, 10, 10, 10]) == 0.0

    def test_perfect_inequality(self):
        # One team has all the points
        result = gini_coefficient([0, 0, 0, 100])
        assert result == pytest.approx(0.75, abs=0.01)

    def test_empty_list(self):
        assert gini_coefficient([]) == 0.0

    def test_all_zeros(self):
        assert gini_coefficient([0, 0, 0]) == 0.0

    def test_single_value(self):
        assert gini_coefficient([50]) == 0.0

    def test_returns_float(self):
        assert isinstance(gini_coefficient([10, 20, 30]), float)

    def test_value_between_zero_and_one(self):
        result = gini_coefficient([5, 15, 25, 55, 100, 200, 300])
        assert 0.0 <= result <= 1.0


class TestPointsGiniByRound:
    def _make_standings(self):
        return pd.DataFrame([
            {"season": 2022, "round": 1, "constructor_id": "red_bull", "points": 44},
            {"season": 2022, "round": 1, "constructor_id": "ferrari", "points": 38},
            {"season": 2022, "round": 1, "constructor_id": "mercedes", "points": 12},
            {"season": 2022, "round": 2, "constructor_id": "red_bull", "points": 69},
            {"season": 2022, "round": 2, "constructor_id": "ferrari", "points": 63},
            {"season": 2022, "round": 2, "constructor_id": "mercedes", "points": 27},
        ])

    def test_returns_one_row_per_round(self):
        result = points_gini_by_round(self._make_standings())
        assert len(result) == 2

    def test_columns_present(self):
        result = points_gini_by_round(self._make_standings())
        assert set(result.columns) == {"season", "round", "gini"}

    def test_gini_values_in_range(self):
        result = points_gini_by_round(self._make_standings())
        assert all(0.0 <= g <= 1.0 for g in result["gini"])


class TestPointsGapByRound:
    def _make_standings(self):
        rows = []
        for pos in range(1, 11):
            rows.append({
                "season": 2022, "round": 1,
                "position": pos,
                "constructor_id": f"team_{pos}",
                "points": float(110 - (pos - 1) * 10),
            })
        return pd.DataFrame(rows)

    def test_gap_calculated_correctly(self):
        result = points_gap_by_round(self._make_standings(), positions=10)
        assert len(result) == 1
        assert result.iloc[0]["gap"] == pytest.approx(90.0)

    def test_skips_rounds_with_too_few_constructors(self):
        df = pd.DataFrame([
            {"season": 2022, "round": 1, "position": 1, "constructor_id": "a", "points": 100.0},
            {"season": 2022, "round": 1, "position": 2, "constructor_id": "b", "points": 50.0},
        ])
        result = points_gap_by_round(df, positions=10)
        assert len(result) == 0


class TestSeasonEndGini:
    def test_returns_one_row_per_season(self):
        df = pd.DataFrame([
            {"season": 2022, "round": 22, "constructor_id": "a", "points": 200.0},
            {"season": 2022, "round": 22, "constructor_id": "b", "points": 100.0},
            {"season": 2023, "round": 22, "constructor_id": "a", "points": 860.0},
            {"season": 2023, "round": 22, "constructor_id": "b", "points": 50.0},
        ])
        result = season_end_gini(df)
        assert len(result) == 2
        assert set(result["season"]) == {2022, 2023}
