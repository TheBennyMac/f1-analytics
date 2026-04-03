import pytest
import pandas as pd
from src.analysis.intra_team import (
    prepare_quali_results,
    teammate_quali_gaps,
    season_teammate_gaps,
    mean_gap_by_constructor,
    driver_dominance,
)


def _make_quali_df(rows):
    """Helper: build a [driver_abbr, team, best_q_s] DataFrame."""
    return pd.DataFrame(rows, columns=["driver_abbr", "team", "best_q_s"])


class TestPrepareQualiResults:
    def test_picks_best_of_q1_q2_q3(self):
        df = pd.DataFrame([{
            "Abbreviation": "VER",
            "TeamName": "Red Bull Racing",
            "Q1": pd.Timedelta(seconds=90.5),
            "Q2": pd.Timedelta(seconds=89.1),
            "Q3": pd.Timedelta(seconds=88.3),
        }])
        result = prepare_quali_results(df)
        assert result.iloc[0]["best_q_s"] == pytest.approx(88.3)

    def test_nat_segments_excluded(self):
        # Driver eliminated in Q1 — Q2 and Q3 are NaT
        df = pd.DataFrame([{
            "Abbreviation": "SAR",
            "TeamName": "Williams",
            "Q1": pd.Timedelta(seconds=93.0),
            "Q2": pd.NaT,
            "Q3": pd.NaT,
        }])
        result = prepare_quali_results(df)
        assert result.iloc[0]["best_q_s"] == pytest.approx(93.0)

    def test_all_nat_gives_none(self):
        df = pd.DataFrame([{
            "Abbreviation": "DNQ",
            "TeamName": "Test",
            "Q1": pd.NaT,
            "Q2": pd.NaT,
            "Q3": pd.NaT,
        }])
        result = prepare_quali_results(df)
        assert result.iloc[0]["best_q_s"] is None

    def test_columns_named_correctly(self):
        df = pd.DataFrame([{
            "Abbreviation": "LEC",
            "TeamName": "Ferrari",
            "Q1": pd.Timedelta(seconds=91.0),
            "Q2": pd.NaT,
            "Q3": pd.NaT,
        }])
        result = prepare_quali_results(df)
        assert set(result.columns) == {"driver_abbr", "team", "best_q_s"}


class TestTeammateQualiGaps:
    def _base_input(self):
        return _make_quali_df([
            {"driver_abbr": "VER", "team": "Red Bull Racing", "best_q_s": 88.3},
            {"driver_abbr": "PER", "team": "Red Bull Racing", "best_q_s": 89.1},
            {"driver_abbr": "LEC", "team": "Ferrari",         "best_q_s": 88.7},
            {"driver_abbr": "SAI", "team": "Ferrari",         "best_q_s": 88.9},
        ])

    def test_gap_calculated_correctly(self):
        result = teammate_quali_gaps(self._base_input(), 2022, 1, "Bahrain GP")
        rb = result[result["constructor"] == "Red Bull Racing"].iloc[0]
        assert rb["gap_s"] == pytest.approx(0.8)

    def test_gap_pct_relative_to_faster(self):
        result = teammate_quali_gaps(self._base_input(), 2022, 1, "Bahrain GP")
        rb = result[result["constructor"] == "Red Bull Racing"].iloc[0]
        expected_pct = 0.8 / 88.3 * 100
        assert rb["gap_pct"] == pytest.approx(expected_pct, rel=1e-3)

    def test_faster_driver_identified(self):
        result = teammate_quali_gaps(self._base_input(), 2022, 1, "Bahrain GP")
        rb = result[result["constructor"] == "Red Bull Racing"].iloc[0]
        assert rb["faster_driver"] == "VER"

    def test_drivers_sorted_alphabetically(self):
        result = teammate_quali_gaps(self._base_input(), 2022, 1, "Bahrain GP")
        rb = result[result["constructor"] == "Red Bull Racing"].iloc[0]
        assert rb["driver_a"] == "PER"  # P comes before V
        assert rb["driver_b"] == "VER"

    def test_metadata_columns_populated(self):
        result = teammate_quali_gaps(self._base_input(), 2022, 1, "Bahrain GP")
        assert result.iloc[0]["season"] == 2022
        assert result.iloc[0]["round"] == 1
        assert result.iloc[0]["race_name"] == "Bahrain GP"

    def test_two_constructors_in_result(self):
        result = teammate_quali_gaps(self._base_input(), 2022, 1, "Bahrain GP")
        assert len(result) == 2

    def test_driver_with_no_time_excluded(self):
        df = _make_quali_df([
            {"driver_abbr": "VER", "team": "Red Bull Racing", "best_q_s": 88.3},
            {"driver_abbr": "PER", "team": "Red Bull Racing", "best_q_s": None},
        ])
        result = teammate_quali_gaps(df, 2022, 1, "Bahrain GP")
        # Only one driver with a time — constructor pair invalid, excluded
        assert result.empty

    def test_three_drivers_same_team_excluded(self):
        df = _make_quali_df([
            {"driver_abbr": "VER", "team": "Red Bull Racing", "best_q_s": 88.3},
            {"driver_abbr": "PER", "team": "Red Bull Racing", "best_q_s": 89.1},
            {"driver_abbr": "LAW", "team": "Red Bull Racing", "best_q_s": 89.5},
        ])
        result = teammate_quali_gaps(df, 2022, 1, "Bahrain GP")
        assert result.empty

    def test_empty_input_returns_empty_with_correct_columns(self):
        df = _make_quali_df([])
        result = teammate_quali_gaps(df, 2022, 1, "Bahrain GP")
        assert result.empty
        assert "gap_s" in result.columns

    def test_equal_times_faster_driver_is_driver_a(self):
        # Tie goes to alphabetically-first driver (driver_a)
        df = _make_quali_df([
            {"driver_abbr": "AAA", "team": "TestTeam", "best_q_s": 90.0},
            {"driver_abbr": "ZZZ", "team": "TestTeam", "best_q_s": 90.0},
        ])
        result = teammate_quali_gaps(df, 2022, 1, "Test GP")
        assert result.iloc[0]["gap_s"] == pytest.approx(0.0)
        assert result.iloc[0]["faster_driver"] == "AAA"


class TestSeasonTeammateGaps:
    def test_aggregates_multiple_races(self):
        quali_data = {
            (2022, 1, "Bahrain GP"): _make_quali_df([
                {"driver_abbr": "VER", "team": "Red Bull Racing", "best_q_s": 88.3},
                {"driver_abbr": "PER", "team": "Red Bull Racing", "best_q_s": 89.1},
            ]),
            (2022, 2, "Saudi Arabian GP"): _make_quali_df([
                {"driver_abbr": "VER", "team": "Red Bull Racing", "best_q_s": 87.5},
                {"driver_abbr": "PER", "team": "Red Bull Racing", "best_q_s": 87.9},
            ]),
        }
        result = season_teammate_gaps(quali_data)
        assert len(result) == 2
        assert set(result["round"]) == {1, 2}

    def test_empty_dict_returns_empty_df(self):
        result = season_teammate_gaps({})
        assert result.empty


class TestMeanGapByConstructor:
    def test_mean_gap_calculated(self):
        gaps = pd.DataFrame([
            {"constructor": "Red Bull Racing", "gap_s": 0.8, "gap_pct": 0.9},
            {"constructor": "Red Bull Racing", "gap_s": 0.4, "gap_pct": 0.5},
            {"constructor": "Ferrari",         "gap_s": 0.2, "gap_pct": 0.2},
        ])
        result = mean_gap_by_constructor(gaps)
        rb = result[result["constructor"] == "Red Bull Racing"].iloc[0]
        assert rb["mean_gap_s"] == pytest.approx(0.6)
        assert rb["races"] == 2

    def test_sorted_closest_first(self):
        gaps = pd.DataFrame([
            {"constructor": "Red Bull Racing", "gap_s": 0.8, "gap_pct": 0.9},
            {"constructor": "Ferrari",         "gap_s": 0.2, "gap_pct": 0.2},
        ])
        result = mean_gap_by_constructor(gaps)
        assert result.iloc[0]["constructor"] == "Ferrari"


class TestDriverDominance:
    def _make_gaps(self):
        return pd.DataFrame([
            {"driver_a": "PER", "driver_b": "VER", "constructor": "Red Bull Racing",
             "gap_s": 0.8, "faster_driver": "VER"},
            {"driver_a": "PER", "driver_b": "VER", "constructor": "Red Bull Racing",
             "gap_s": 0.4, "faster_driver": "VER"},
            {"driver_a": "PER", "driver_b": "VER", "constructor": "Red Bull Racing",
             "gap_s": 0.1, "faster_driver": "PER"},
        ])

    def test_win_pct_calculated(self):
        result = driver_dominance(self._make_gaps())
        ver = result[result["driver"] == "VER"].iloc[0]
        assert ver["win_pct"] == pytest.approx(66.7, rel=1e-2)
        assert ver["faster_count"] == 2
        assert ver["total_races"] == 3

    def test_win_pcts_sum_to_100_per_pair(self):
        result = driver_dominance(self._make_gaps())
        ver = result[result["driver"] == "VER"].iloc[0]
        per = result[result["driver"] == "PER"].iloc[0]
        assert ver["win_pct"] + per["win_pct"] == pytest.approx(100.0)

    def test_sorted_by_win_pct_descending(self):
        result = driver_dominance(self._make_gaps())
        assert result.iloc[0]["win_pct"] >= result.iloc[1]["win_pct"]

    def test_min_races_filters_low_sample_drivers(self):
        # SUB appears in only 1 race (replacement driver); REG appears in 3
        gaps = pd.DataFrame([
            {"driver_a": "REG", "driver_b": "SUB", "constructor": "TestTeam",
             "gap_s": 0.5, "faster_driver": "SUB"},
            {"driver_a": "REG", "driver_b": "NEW", "constructor": "TestTeam",
             "gap_s": 0.3, "faster_driver": "REG"},
            {"driver_a": "REG", "driver_b": "NEW", "constructor": "TestTeam",
             "gap_s": 0.2, "faster_driver": "REG"},
        ])
        result = driver_dominance(gaps, min_races=2)
        assert "SUB" not in result["driver"].values
        assert "REG" in result["driver"].values

    def test_min_races_default_includes_all(self):
        result = driver_dominance(self._make_gaps())
        assert len(result) == 2  # both VER and PER present
