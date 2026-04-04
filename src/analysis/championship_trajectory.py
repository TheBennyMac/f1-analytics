"""
Championship trajectory analysis.

Tracks cumulative constructor points and gap to the championship leader
round by round within a season. Used to identify when a title challenge
falters — the inflection point where a constructor's gap to the leader
starts widening consistently.
"""

import pandas as pd


def cumulative_constructor_points(results_df: pd.DataFrame) -> pd.DataFrame:
    """Build cumulative constructor points standings by round.

    Args:
        results_df: DataFrame with columns [season, round, constructor_id,
                    constructor_name, points]. One row per driver per race.

    Returns:
        DataFrame with columns [season, round, constructor_id,
        constructor_name, round_points, cumulative_points].
        One row per constructor per round.
    """
    round_totals = (
        results_df.groupby(["season", "round", "constructor_id", "constructor_name"])["points"]
        .sum()
        .reset_index()
        .rename(columns={"points": "round_points"})
        .sort_values(["season", "constructor_id", "round"])
    )

    round_totals["cumulative_points"] = (
        round_totals.groupby(["season", "constructor_id"])["round_points"].cumsum()
    )

    return round_totals.sort_values(["season", "round", "cumulative_points"],
                                    ascending=[True, True, False]).reset_index(drop=True)


def points_gap_to_leader(standings_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate each constructor's points gap to the championship leader per round.

    Args:
        standings_df: DataFrame as returned by cumulative_constructor_points().

    Returns:
        DataFrame with same rows plus columns [leader_points, gap_to_leader].
        gap_to_leader is 0 for the leader, positive for all others.
    """
    leader_points = (
        standings_df.groupby(["season", "round"])["cumulative_points"]
        .max()
        .reset_index()
        .rename(columns={"cumulative_points": "leader_points"})
    )

    merged = standings_df.merge(leader_points, on=["season", "round"])
    merged["gap_to_leader"] = merged["leader_points"] - merged["cumulative_points"]
    return merged.sort_values(["season", "round", "gap_to_leader"]).reset_index(drop=True)


def constructor_trajectory(
    gap_df: pd.DataFrame,
    constructor_id: str,
    seasons: list[int] | None = None,
) -> pd.DataFrame:
    """Extract the round-by-round trajectory for a single constructor.

    Args:
        gap_df: DataFrame as returned by points_gap_to_leader().
        constructor_id: The constructor to extract (e.g. 'ferrari').
        seasons: Optional list of seasons to filter to. If None, returns all.

    Returns:
        DataFrame with columns [season, round, round_points, cumulative_points,
        leader_points, gap_to_leader] for the specified constructor.
    """
    mask = gap_df["constructor_id"] == constructor_id
    if seasons:
        mask &= gap_df["season"].isin(seasons)
    return gap_df[mask].reset_index(drop=True)


def gap_inflection_round(trajectory_df: pd.DataFrame) -> pd.DataFrame:
    """Identify the round where each season's gap to the leader starts widening.

    The inflection round is defined as the first round after which the gap
    increases for at least two consecutive rounds — i.e., the point where
    a title challenge definitively starts to slip.

    Args:
        trajectory_df: DataFrame as returned by constructor_trajectory(),
                       containing one or more seasons.

    Returns:
        DataFrame with columns [season, inflection_round, gap_at_inflection,
        final_gap]. One row per season. inflection_round is None if the gap
        never widened for two consecutive rounds.
    """
    records = []
    for season, group in trajectory_df.groupby("season"):
        group = group.sort_values("round").reset_index(drop=True)
        inflection = None
        for i in range(len(group) - 2):
            if (group.loc[i + 1, "gap_to_leader"] > group.loc[i, "gap_to_leader"] and
                    group.loc[i + 2, "gap_to_leader"] > group.loc[i + 1, "gap_to_leader"]):
                inflection = int(group.loc[i, "round"])
                break
        final_gap = group.iloc[-1]["gap_to_leader"]
        gap_at_inflection = (
            group[group["round"] == inflection]["gap_to_leader"].iloc[0]
            if inflection is not None else None
        )
        records.append({
            "season": season,
            "inflection_round": inflection,
            "gap_at_inflection": gap_at_inflection,
            "final_gap": final_gap,
        })
    return pd.DataFrame(records)
