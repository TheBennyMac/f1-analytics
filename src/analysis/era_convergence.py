"""
Three-era convergence analysis.

Combines constructor standings from multiple seasons across different regulation
eras and measures how quickly the field compresses (or stays spread) across Year 1.

Inputs come from two sources depending on era:
  - Hybrid PU Era (2014+): Jolpica API via src/data/jolpica_client
  - Ground Effect Era (2022+) and 2026 Era: FastF1 via notebooks + export

All standings must be pre-computed as cumulative points per constructor per round
before being passed to these functions.
"""

import pandas as pd

from src.analysis.points_spread import gini_coefficient
from src.utils.era_helper import get_era_info


def label_era(standings_df: pd.DataFrame) -> pd.DataFrame:
    """Add era_name and year_in_era columns to a standings DataFrame.

    Args:
        standings_df: Must contain a 'season' column.

    Returns:
        Copy of input with 'era_name' and 'year_in_era' columns added.
    """
    df = standings_df.copy()
    era_infos = df["season"].map(get_era_info)
    df["era_name"] = era_infos.map(lambda e: e.name)
    df["year_in_era"] = era_infos.map(lambda e: e.year_within_era)
    return df


def convergence_by_round(
    standings_df: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    """Compute field convergence metrics at each round for each season.

    Args:
        standings_df: Cumulative constructor standings with columns:
            [season, round, constructor_id, points].
            One row per constructor per round.
        top_n: Measure gap from P1 to this finishing position (default 10).

    Returns:
        DataFrame with columns:
            season, round, era_name, year_in_era,
            p1_points, pn_points, gap_p1_pn, gap_normalised, gini, n_constructors
        where gap_normalised = gap / p1_points (0 when only one round complete,
        proportional spread thereafter). One row per (season, round).
    """
    df = label_era(standings_df)
    records = []

    for (season, round_), group in df.groupby(["season", "round"]):
        group_sorted = group.sort_values("points", ascending=False).reset_index(drop=True)
        n = len(group_sorted)
        p1_pts = float(group_sorted.iloc[0]["points"])
        pn_pts = float(group_sorted.iloc[min(top_n - 1, n - 1)]["points"])
        gap = p1_pts - pn_pts
        gap_norm = gap / p1_pts if p1_pts > 0 else 0.0
        gini = gini_coefficient(group_sorted["points"].tolist())
        era_row = group_sorted.iloc[0]

        records.append({
            "season": season,
            "round": round_,
            "era_name": era_row["era_name"],
            "year_in_era": era_row["year_in_era"],
            "p1_points": p1_pts,
            "pn_points": pn_pts,
            "gap_p1_pn": gap,
            "gap_normalised": round(gap_norm, 4),
            "gini": round(gini, 4),
            "n_constructors": n,
        })

    return pd.DataFrame(records).sort_values(["season", "round"]).reset_index(drop=True)


def era_comparison_table(convergence_df: pd.DataFrame) -> pd.DataFrame:
    """Summarise final-round convergence metrics for each season.

    Useful for the findings table in the narrative page.

    Args:
        convergence_df: As returned by convergence_by_round().

    Returns:
        DataFrame with one row per season showing final-round gap and Gini.
    """
    final = (
        convergence_df.sort_values("round")
        .groupby("season")
        .last()
        .reset_index()
    )
    return final[["season", "era_name", "year_in_era", "round",
                  "gap_p1_pn", "gap_normalised", "gini"]].rename(
        columns={"round": "final_round"}
    )
