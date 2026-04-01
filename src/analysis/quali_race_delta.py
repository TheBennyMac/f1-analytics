"""
Qualifying vs race pace consistency analysis.

Measures how reliably a driver or constructor converts qualifying position
into race finishing position. A delta of 0 means perfect conversion.
Positive delta = gained positions in the race. Negative = lost positions.
"""

import pandas as pd


def position_delta(grid: int | None, finish: int | None) -> int | None:
    """Return positions gained in the race (positive = gained, negative = lost).

    Returns None if the driver did not finish or if grid position is unknown
    (e.g. loaded via OpenF1 fallback where grid data is unavailable).
    """
    if grid is None or finish is None:
        return None
    return grid - finish


def quali_race_delta(results_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate position delta for every driver in every race.

    Args:
        results_df: DataFrame with columns [season, round, race_name,
                                            driver_id, driver_name, constructor_id,
                                            grid_position, finish_position, status].

    Returns:
        DataFrame with the same rows plus columns [delta, dnf].
        delta = grid_position - finish_position (positive = gained places).
        dnf = True if the driver did not finish.
    """
    df = results_df.copy()
    df["dnf"] = df["status"].apply(
        lambda s: s not in ("Finished", "Lapped")
        and not (s.startswith("+") and "Lap" in s)
    )
    df["delta"] = df.apply(
        lambda row: position_delta(row["grid_position"], row["finish_position"]),
        axis=1,
    )
    return df


def mean_delta_by_driver(delta_df: pd.DataFrame) -> pd.DataFrame:
    """Return mean position delta per driver, excluding DNFs.

    Args:
        delta_df: Output of quali_race_delta().

    Returns:
        DataFrame with columns [driver_id, driver_name, constructor_id,
                                races, mean_delta, dnf_count].
        Sorted by mean_delta descending (best converters first).
    """
    finished = delta_df[~delta_df["dnf"] & delta_df["delta"].notna()]
    summary = finished.groupby(["driver_id", "driver_name", "constructor_id"]).agg(
        races=("delta", "count"),
        mean_delta=("delta", "mean"),
    ).reset_index()
    dnf_counts = delta_df.groupby("driver_id")["dnf"].sum().reset_index()
    dnf_counts.columns = ["driver_id", "dnf_count"]
    summary = summary.merge(dnf_counts, on="driver_id", how="left")
    summary["mean_delta"] = summary["mean_delta"].round(2)
    return summary.sort_values("mean_delta", ascending=False).reset_index(drop=True)


def mean_delta_by_constructor(delta_df: pd.DataFrame) -> pd.DataFrame:
    """Return mean position delta per constructor, excluding DNFs.

    Args:
        delta_df: Output of quali_race_delta().

    Returns:
        DataFrame with columns [constructor_id, races, mean_delta, dnf_count].
        Sorted by mean_delta descending.
    """
    finished = delta_df[~delta_df["dnf"] & delta_df["delta"].notna()]
    summary = finished.groupby("constructor_id").agg(
        races=("delta", "count"),
        mean_delta=("delta", "mean"),
    ).reset_index()
    dnf_counts = delta_df.groupby("constructor_id")["dnf"].sum().reset_index()
    dnf_counts.columns = ["constructor_id", "dnf_count"]
    summary = summary.merge(dnf_counts, on="constructor_id", how="left")
    summary["mean_delta"] = summary["mean_delta"].round(2)
    return summary.sort_values("mean_delta", ascending=False).reset_index(drop=True)
