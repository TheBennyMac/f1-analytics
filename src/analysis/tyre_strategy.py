"""
Tyre compound strategy analysis.

Measures how teams approach tyre strategy — which compounds they select,
how long they run them, and how this varies by constructor and regulation era.

Pit-out and pit-in laps are excluded from stint length counts as they are
not representative of normal running pace.
"""

import pandas as pd


def stints_from_laps(laps_df: pd.DataFrame) -> pd.DataFrame:
    """Extract stint-level data from a FastF1 laps DataFrame.

    A stint is a continuous run on the same tyre compound, identified by
    FastF1's Stint column. Returns one row per driver-stint, counting only
    laps that are not pit-in or pit-out laps.

    Args:
        laps_df: FastF1 laps DataFrame. Must contain columns:
                 ['Driver', 'Stint', 'Compound', 'LapNumber'].
                 Optional: ['Team']. Pit columns: PitOutLap/PitInLap (boolean)
                 or PitOutTime/PitInTime (FastF1 native timestamps).

    Returns:
        DataFrame with columns [driver, team, stint, compound, laps].
        laps = number of representative laps in the stint.
        Rows with missing or UNKNOWN compound are excluded.

    Raises:
        ValueError: If any required column is missing.
    """
    required = {"Driver", "Stint", "Compound", "LapNumber"}
    missing = required - set(laps_df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    clean = laps_df.copy()
    if "PitOutLap" in clean.columns:
        clean = clean[~clean["PitOutLap"].fillna(False)]
    elif "PitOutTime" in clean.columns:
        clean = clean[clean["PitOutTime"].isna()]
    if "PitInLap" in clean.columns:
        clean = clean[~clean["PitInLap"].fillna(False)]
    elif "PitInTime" in clean.columns:
        clean = clean[clean["PitInTime"].isna()]

    clean = clean.dropna(subset=["Compound", "Stint"])
    clean = clean[clean["Compound"] != "UNKNOWN"]

    has_team = "Team" in clean.columns
    group_cols = ["Driver", "Team", "Stint", "Compound"] if has_team else ["Driver", "Stint", "Compound"]

    summary = (
        clean.groupby(group_cols, sort=False)["LapNumber"]
        .count()
        .reset_index()
        .rename(columns={"LapNumber": "laps", "Driver": "driver",
                         "Stint": "stint", "Compound": "compound"})
    )
    if has_team:
        summary = summary.rename(columns={"Team": "team"})
    else:
        summary["team"] = None

    return summary[["driver", "team", "stint", "compound", "laps"]].sort_values(
        ["driver", "stint"]
    ).reset_index(drop=True)


def strategy_summary(laps_df: pd.DataFrame) -> pd.DataFrame:
    """Summarise each driver's tyre strategy for a race.

    Args:
        laps_df: FastF1 laps DataFrame.

    Returns:
        DataFrame with columns [driver, team, compounds_used, num_stops, total_laps].
        compounds_used is a comma-separated string of compounds in stint order.
        num_stops = number of pit stops (stints - 1).
    """
    stints = stints_from_laps(laps_df)
    records = []
    for (driver, team), group in stints.groupby(["driver", "team"], sort=False):
        group = group.sort_values("stint")
        records.append({
            "driver": driver,
            "team": team,
            "compounds_used": ", ".join(group["compound"].tolist()),
            "num_stops": len(group) - 1,
            "total_laps": int(group["laps"].sum()),
        })
    if not records:
        return pd.DataFrame(columns=["driver", "team", "compounds_used", "num_stops", "total_laps"])
    return pd.DataFrame(records).sort_values("driver").reset_index(drop=True)


def mean_stint_length(laps_df: pd.DataFrame) -> pd.DataFrame:
    """Return mean stint length per compound across a race.

    Args:
        laps_df: FastF1 laps DataFrame.

    Returns:
        DataFrame with columns [compound, mean_laps, stints].
        Sorted by compound name.
    """
    stints = stints_from_laps(laps_df)
    if stints.empty:
        return pd.DataFrame(columns=["compound", "mean_laps", "stints"])
    summary = (
        stints.groupby("compound")["laps"]
        .agg(mean_laps="mean", stints="count")
        .reset_index()
    )
    summary["mean_laps"] = summary["mean_laps"].round(1)
    return summary.sort_values("compound").reset_index(drop=True)


def compound_usage_by_constructor(
    season_laps: dict[tuple[int, int], pd.DataFrame],
) -> pd.DataFrame:
    """Count compound usage per constructor across multiple races.

    Args:
        season_laps: Dict mapping (season, round) to a FastF1 laps DataFrame.

    Returns:
        DataFrame with columns [season, round, team, compound, stints, mean_stint_laps].
    """
    records = []
    for (season, round_), laps_df in season_laps.items():
        try:
            stints = stints_from_laps(laps_df)
        except ValueError:
            continue
        if stints.empty:
            continue
        for (team, compound), group in stints.groupby(["team", "compound"]):
            records.append({
                "season": season,
                "round": round_,
                "team": team,
                "compound": compound,
                "stints": len(group),
                "mean_stint_laps": round(float(group["laps"].mean()), 1),
            })
    if not records:
        return pd.DataFrame(
            columns=["season", "round", "team", "compound", "stints", "mean_stint_laps"]
        )
    return (
        pd.DataFrame(records)
        .sort_values(["season", "round", "team"])
        .reset_index(drop=True)
    )
