import pytest
import pandas as pd
from src.analysis.championship_trajectory import (
    cumulative_constructor_points,
    points_gap_to_leader,
    constructor_trajectory,
    gap_inflection_round,
)


def _make_results():
    """Two constructors across two rounds in one season."""
    return pd.DataFrame([
        # Round 1: Ferrari 25, Red Bull 18
        {"season": 2022, "round": 1, "constructor_id": "ferrari",
         "constructor_name": "Ferrari", "points": 25.0},
        {"season": 2022, "round": 1, "constructor_id": "red_bull",
         "constructor_name": "Red Bull", "points": 18.0},
        # Round 2: Ferrari 12, Red Bull 25 → Red Bull takes lead
        {"season": 2022, "round": 2, "constructor_id": "ferrari",
         "constructor_name": "Ferrari", "points": 12.0},
        {"season": 2022, "round": 2, "constructor_id": "red_bull",
         "constructor_name": "Red Bull", "points": 25.0},
        # Round 3: Ferrari 6, Red Bull 25 → gap widens further
        {"season": 2022, "round": 3, "constructor_id": "ferrari",
         "constructor_name": "Ferrari", "points": 6.0},
        {"season": 2022, "round": 3, "constructor_id": "red_bull",
         "constructor_name": "Red Bull", "points": 25.0},
    ])


class TestCumulativeConstructorPoints:
    def test_cumulative_points_accumulate_correctly(self):
        result = cumulative_constructor_points(_make_results())
        ferrari = result[(result["constructor_id"] == "ferrari") & (result["round"] == 2)]
        assert ferrari.iloc[0]["cumulative_points"] == pytest.approx(37.0)

    def test_round_points_not_cumulative(self):
        result = cumulative_constructor_points(_make_results())
        ferrari_r2 = result[(result["constructor_id"] == "ferrari") & (result["round"] == 2)]
        assert ferrari_r2.iloc[0]["round_points"] == pytest.approx(12.0)

    def test_columns_present(self):
        result = cumulative_constructor_points(_make_results())
        assert {"season", "round", "constructor_id", "constructor_name",
                "round_points", "cumulative_points"}.issubset(result.columns)

    def test_one_row_per_constructor_per_round(self):
        result = cumulative_constructor_points(_make_results())
        assert len(result) == 6  # 2 constructors × 3 rounds


class TestPointsGapToLeader:
    def test_leader_has_zero_gap(self):
        standings = cumulative_constructor_points(_make_results())
        gaps = points_gap_to_leader(standings)
        # Round 1: Ferrari leads with 25 pts
        leader_r1 = gaps[(gaps["round"] == 1) & (gaps["constructor_id"] == "ferrari")]
        assert leader_r1.iloc[0]["gap_to_leader"] == pytest.approx(0.0)

    def test_non_leader_gap_is_positive(self):
        standings = cumulative_constructor_points(_make_results())
        gaps = points_gap_to_leader(standings)
        rb_r1 = gaps[(gaps["round"] == 1) & (gaps["constructor_id"] == "red_bull")]
        assert rb_r1.iloc[0]["gap_to_leader"] == pytest.approx(7.0)

    def test_leader_switches_correctly(self):
        standings = cumulative_constructor_points(_make_results())
        gaps = points_gap_to_leader(standings)
        # Round 2: Red Bull leads (43 pts) vs Ferrari (37 pts)
        ferrari_r2 = gaps[(gaps["round"] == 2) & (gaps["constructor_id"] == "ferrari")]
        assert ferrari_r2.iloc[0]["gap_to_leader"] == pytest.approx(6.0)

    def test_columns_present(self):
        standings = cumulative_constructor_points(_make_results())
        gaps = points_gap_to_leader(standings)
        assert {"leader_points", "gap_to_leader"}.issubset(gaps.columns)


class TestConstructorTrajectory:
    def test_filters_to_single_constructor(self):
        standings = cumulative_constructor_points(_make_results())
        gaps = points_gap_to_leader(standings)
        traj = constructor_trajectory(gaps, "ferrari")
        assert set(traj["constructor_id"].unique()) == {"ferrari"}

    def test_filters_by_season(self):
        standings = cumulative_constructor_points(_make_results())
        gaps = points_gap_to_leader(standings)
        traj = constructor_trajectory(gaps, "ferrari", seasons=[2022])
        assert list(traj["season"].unique()) == [2022]

    def test_returns_all_rounds(self):
        standings = cumulative_constructor_points(_make_results())
        gaps = points_gap_to_leader(standings)
        traj = constructor_trajectory(gaps, "ferrari")
        assert len(traj) == 3


class TestGapInflectionRound:
    def test_inflection_detected_at_round_1(self):
        # Ferrari leads R1, gap widens R2 and R3 → inflection at round 1
        standings = cumulative_constructor_points(_make_results())
        gaps = points_gap_to_leader(standings)
        traj = constructor_trajectory(gaps, "ferrari")
        result = gap_inflection_round(traj)
        assert result.iloc[0]["inflection_round"] == 1

    def test_final_gap_correct(self):
        standings = cumulative_constructor_points(_make_results())
        gaps = points_gap_to_leader(standings)
        traj = constructor_trajectory(gaps, "ferrari")
        result = gap_inflection_round(traj)
        # After R3: Red Bull 68 pts, Ferrari 43 pts → gap = 25
        assert result.iloc[0]["final_gap"] == pytest.approx(25.0)

    def test_no_inflection_when_gap_never_widens(self):
        # Constructor that stays leader all season → gap always 0
        results = pd.DataFrame([
            {"season": 2022, "round": r, "constructor_id": "ferrari",
             "constructor_name": "Ferrari", "points": 25.0}
            for r in [1, 2, 3]
        ])
        standings = cumulative_constructor_points(results)
        gaps = points_gap_to_leader(standings)
        traj = constructor_trajectory(gaps, "ferrari")
        result = gap_inflection_round(traj)
        assert result.iloc[0]["inflection_round"] is None

    def test_returns_one_row_per_season(self):
        standings = cumulative_constructor_points(_make_results())
        gaps = points_gap_to_leader(standings)
        traj = constructor_trajectory(gaps, "ferrari")
        result = gap_inflection_round(traj)
        assert len(result) == 1
