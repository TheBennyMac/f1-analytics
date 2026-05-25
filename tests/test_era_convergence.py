"""Tests for era_convergence analysis module."""

import pandas as pd
import pytest

from src.analysis.era_convergence import convergence_by_round, era_comparison_table, label_era


def _make_standings(season: int, rounds: int, n_constructors: int) -> pd.DataFrame:
    """Build a synthetic standings DataFrame with linearly spaced points."""
    rows = []
    for r in range(1, rounds + 1):
        for c in range(n_constructors):
            rows.append({
                "season": season,
                "round": r,
                "constructor_id": f"team_{c}",
                "points": float((n_constructors - c) * r * 10),
            })
    return pd.DataFrame(rows)


def test_label_era_adds_columns():
    df = _make_standings(2014, 1, 5)
    result = label_era(df)
    assert "era_name" in result.columns
    assert "year_in_era" in result.columns
    assert (result["era_name"] == "Hybrid Power Unit Era").all()
    assert (result["year_in_era"] == 1).all()


def test_label_era_2022_ground_effect():
    df = _make_standings(2022, 1, 5)
    result = label_era(df)
    assert (result["era_name"] == "Ground Effect Era").all()
    assert (result["year_in_era"] == 1).all()


def test_label_era_2026_era():
    df = _make_standings(2026, 1, 5)
    result = label_era(df)
    assert (result["era_name"] == "2026 Era").all()
    assert (result["year_in_era"] == 1).all()


def test_convergence_by_round_shape():
    df = _make_standings(2014, 5, 10)
    result = convergence_by_round(df)
    assert len(result) == 5  # one row per round
    assert set(result.columns) >= {"season", "round", "era_name", "gap_p1_pn", "gini"}


def test_convergence_gap_increases_over_rounds():
    # P1 accumulates fastest, so gap grows each round
    df = _make_standings(2014, 5, 10)
    result = convergence_by_round(df)
    gaps = result["gap_p1_pn"].tolist()
    assert gaps == sorted(gaps), "Gap should grow monotonically with linear scoring"


def test_convergence_gini_between_zero_and_one():
    df = _make_standings(2022, 10, 10)
    result = convergence_by_round(df)
    assert (result["gini"] >= 0).all()
    assert (result["gini"] <= 1).all()


def test_convergence_top_n_fewer_than_constructors():
    # 5 constructors, top_n=3: gap is P1 - P3
    df = _make_standings(2014, 2, 5)
    result = convergence_by_round(df, top_n=3)
    r1 = result[result["round"] == 1].iloc[0]
    # P1 = 5*1*10=50, P3 = 3*1*10=30 → gap = 20
    assert r1["gap_p1_pn"] == pytest.approx(20.0)


def test_convergence_normalised_less_than_one():
    df = _make_standings(2014, 5, 10)
    result = convergence_by_round(df)
    assert (result["gap_normalised"] <= 1.0).all()
    assert (result["gap_normalised"] >= 0.0).all()


def test_era_comparison_table_one_row_per_season():
    df1 = _make_standings(2014, 19, 10)
    df2 = _make_standings(2022, 22, 10)
    combined = convergence_by_round(pd.concat([df1, df2], ignore_index=True))
    summary = era_comparison_table(combined)
    assert len(summary) == 2
    assert set(summary["season"]) == {2014, 2022}


def test_era_comparison_table_final_round_correct():
    df = _make_standings(2014, 19, 10)
    combined = convergence_by_round(df)
    summary = era_comparison_table(combined)
    assert summary.iloc[0]["final_round"] == 19
