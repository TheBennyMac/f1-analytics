"""
Constructor points spread analysis.

Measures competitive parity across a season or era using:
- Gini coefficient (0 = perfect equality, 1 = one team wins everything)
- Raw points gap from P1 to Pn
"""

import pandas as pd


def gini_coefficient(values: list[float]) -> float:
    """Calculate the Gini coefficient for a distribution of values.

    Returns a value between 0 (perfect equality) and 1 (perfect inequality).
    Returns 0.0 if all values are zero or the list is empty.
    """
    if not values or sum(values) == 0:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    cumsum = sum((i + 1) * v for i, v in enumerate(sorted_vals))
    return (2 * cumsum) / (n * sum(sorted_vals)) - (n + 1) / n


def points_gini_by_round(standings_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate the Gini coefficient of constructor points at each round.

    Args:
        standings_df: DataFrame with columns [season, round, constructor_id, points].
                      One row per constructor per round (cumulative points).

    Returns:
        DataFrame with columns [season, round, gini].
    """
    records = []
    for (season, round_), group in standings_df.groupby(["season", "round"]):
        gini = gini_coefficient(group["points"].tolist())
        records.append({"season": season, "round": round_, "gini": gini})
    return pd.DataFrame(records).sort_values(["season", "round"]).reset_index(drop=True)


def points_gap_by_round(standings_df: pd.DataFrame, positions: int = 10) -> pd.DataFrame:
    """Calculate the raw points gap between P1 and Pn at each round.

    Args:
        standings_df: DataFrame with columns [season, round, position, points].
        positions: Gap is measured from P1 to this position (default 10).

    Returns:
        DataFrame with columns [season, round, p1_points, pn_points, gap].
    """
    records = []
    for (season, round_), group in standings_df.groupby(["season", "round"]):
        group_sorted = group.sort_values("position")
        if len(group_sorted) < positions:
            continue
        p1 = group_sorted.iloc[0]["points"]
        pn = group_sorted.iloc[positions - 1]["points"]
        records.append({
            "season": season,
            "round": round_,
            "p1_points": p1,
            "pn_points": pn,
            "gap": p1 - pn,
        })
    if not records:
        return pd.DataFrame(columns=["season", "round", "p1_points", "pn_points", "gap"])
    return pd.DataFrame(records).sort_values(["season", "round"]).reset_index(drop=True)


def season_end_gini(standings_df: pd.DataFrame) -> pd.DataFrame:
    """Return the final-round Gini coefficient for each season.

    Args:
        standings_df: DataFrame with columns [season, round, constructor_id, points].

    Returns:
        DataFrame with columns [season, final_round, gini].
    """
    final_rounds = standings_df.groupby("season")["round"].max().reset_index()
    final_rounds.columns = ["season", "final_round"]
    merged = standings_df.merge(final_rounds, left_on=["season", "round"],
                                right_on=["season", "final_round"])
    records = []
    for (season, round_), group in merged.groupby(["season", "final_round"]):
        gini = gini_coefficient(group["points"].tolist())
        records.append({"season": season, "final_round": round_, "gini": round(gini, 4)})
    return pd.DataFrame(records).sort_values("season").reset_index(drop=True)
