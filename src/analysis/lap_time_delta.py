"""
Lap time delta analysis — measures field spread within a race.

The P1-P10 gap is the difference in seconds between the fastest lap set by
the quickest driver and the fastest lap set by the 10th quickest driver.
A narrowing gap over era years indicates field convergence.
"""

import pandas as pd


def fastest_lap_per_driver(laps_df: pd.DataFrame) -> pd.DataFrame:
    """Return the fastest valid lap time (in seconds) for each driver.

    Args:
        laps_df: FastF1 laps DataFrame. Must contain columns:
                 ['Driver', 'LapTime', 'PitOutLap', 'PitInLap'].

    Returns:
        DataFrame with columns [driver, fastest_lap_s], sorted fastest first.
        Excludes pit-in and pit-out laps as these are not representative.
    """
    clean = laps_df.copy()

    # Exclude pit in/out laps and laps with no recorded time
    if "PitOutLap" in clean.columns:
        clean = clean[~clean["PitOutLap"].fillna(False)]
    if "PitInLap" in clean.columns:
        clean = clean[~clean["PitInLap"].fillna(False)]
    # Exclude laps flagged as inaccurate by FastF1 — these include SC/VSC laps
    # where drivers are not pushing, which would distort the pace comparison.
    if "IsAccurate" in clean.columns:
        clean = clean[clean["IsAccurate"].fillna(False)]
    clean = clean.dropna(subset=["LapTime"])

    clean["lap_s"] = clean["LapTime"].dt.total_seconds()
    fastest = clean.groupby("Driver")["lap_s"].min().reset_index()
    fastest.columns = ["driver", "fastest_lap_s"]
    return fastest.sort_values("fastest_lap_s").reset_index(drop=True)


def p1_to_pn_gap(laps_df: pd.DataFrame, n: int = 10) -> float | None:
    """Return the gap in seconds between the P1 and Pn fastest laps in a session.

    Args:
        laps_df: FastF1 laps DataFrame.
        n: Position to measure the gap to (default 10).

    Returns:
        Gap in seconds, or None if fewer than n drivers have valid laps.
    """
    fastest = fastest_lap_per_driver(laps_df)
    if len(fastest) < n:
        return None
    return round(fastest.iloc[n - 1]["fastest_lap_s"] - fastest.iloc[0]["fastest_lap_s"], 3)


def lap_time_delta_summary(
    season_laps: dict[tuple[int, int], pd.DataFrame],
) -> pd.DataFrame:
    """Aggregate P1-P10 lap time gaps across multiple races.

    Args:
        season_laps: Dict mapping (season, round) to a FastF1 laps DataFrame.

    Returns:
        DataFrame with columns [season, round, p1_lap_s, p10_lap_s, gap_s],
        sorted by season and round.
    """
    records = []
    for (season, round_), laps_df in season_laps.items():
        fastest = fastest_lap_per_driver(laps_df)
        if len(fastest) < 10:
            continue
        records.append({
            "season": season,
            "round": round_,
            "p1_lap_s": round(fastest.iloc[0]["fastest_lap_s"], 3),
            "p10_lap_s": round(fastest.iloc[9]["fastest_lap_s"], 3),
            "gap_s": round(fastest.iloc[9]["fastest_lap_s"] - fastest.iloc[0]["fastest_lap_s"], 3),
        })
    if not records:
        return pd.DataFrame(columns=["season", "round", "p1_lap_s", "p10_lap_s", "gap_s"])
    return pd.DataFrame(records).sort_values(["season", "round"]).reset_index(drop=True)


def mean_gap_by_season(delta_df: pd.DataFrame) -> pd.DataFrame:
    """Return the mean P1-P10 gap per season.

    Args:
        delta_df: Output of lap_time_delta_summary().

    Returns:
        DataFrame with columns [season, mean_gap_s, races].
    """
    summary = delta_df.groupby("season")["gap_s"].agg(
        mean_gap_s="mean", races="count"
    ).reset_index()
    summary["mean_gap_s"] = summary["mean_gap_s"].round(3)
    return summary.sort_values("season").reset_index(drop=True)
