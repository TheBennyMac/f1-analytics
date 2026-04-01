"""
Reliability analysis — DNF rates by team, driver, and year.

DNF (Did Not Finish) is defined as any retirement that is not a classified finish.
Classified finishes include: 'Finished', '+1 Lap', '+2 Laps', '+3 Laps', etc.
"""

import pandas as pd


def is_dnf(status: str) -> bool:
    """Return True if the given result status represents a DNF.

    Classified finishes are: 'Finished', 'Lapped' (FastF1 2026+ format),
    and the historical '+N Lap(s)' format ('+1 Lap', '+2 Laps', etc.).
    Both formats represent a driver who completed the race distance.
    """
    if status in ("Finished", "Lapped"):
        return False
    if status.startswith("+") and "Lap" in status:
        return False
    return True


def dnf_rate_by_constructor_year(results_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate DNF rate per constructor per season.

    Args:
        results_df: DataFrame with columns [season, constructor_id, constructor_name, status].
                    One row per driver per race.

    Returns:
        DataFrame with columns [season, constructor_id, constructor_name,
                                starts, dnfs, dnf_rate_pct].
        Sorted by season, then dnf_rate_pct descending.
    """
    results_df = results_df.copy()
    results_df["dnf"] = results_df["status"].apply(is_dnf)

    grouped = results_df.groupby(["season", "constructor_id", "constructor_name"])
    summary = grouped["dnf"].agg(starts="count", dnfs="sum").reset_index()
    summary["dnf_rate_pct"] = (summary["dnfs"] / summary["starts"] * 100).round(1)
    return summary.sort_values(["season", "dnf_rate_pct"], ascending=[True, False]).reset_index(drop=True)


def dnf_rate_by_driver_year(results_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate DNF rate per driver per season.

    Args:
        results_df: DataFrame with columns [season, driver_id, driver_name,
                                            constructor_id, status].

    Returns:
        DataFrame with columns [season, driver_id, driver_name, constructor_id,
                                starts, dnfs, dnf_rate_pct].
    """
    results_df = results_df.copy()
    results_df["dnf"] = results_df["status"].apply(is_dnf)

    grouped = results_df.groupby(["season", "driver_id", "driver_name", "constructor_id"])
    summary = grouped["dnf"].agg(starts="count", dnfs="sum").reset_index()
    summary["dnf_rate_pct"] = (summary["dnfs"] / summary["starts"] * 100).round(1)
    return summary.sort_values(["season", "dnf_rate_pct"], ascending=[True, False]).reset_index(drop=True)


def dnf_causes(results_df: pd.DataFrame) -> pd.DataFrame:
    """Frequency of each DNF cause across the dataset.

    Args:
        results_df: DataFrame with columns [season, status].

    Returns:
        DataFrame with columns [status, count] for DNF statuses only,
        sorted by count descending.
    """
    dnfs = results_df[results_df["status"].apply(is_dnf)]
    counts = dnfs["status"].value_counts().reset_index()
    counts.columns = ["status", "count"]
    return counts
