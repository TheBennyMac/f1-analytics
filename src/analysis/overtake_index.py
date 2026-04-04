"""
Overtake index analysis.

Measures position change activity per race as a proxy for overtaking.
Used to test whether circuits like Monaco produce processional races
compared to the rest of the calendar.

Overtake index = total positions gained by all finishers / starters.
Normalising by starters controls for field size and attrition differences.

DNFs and pit-lane starters (grid_position == 0) are excluded from deltas
because their position changes do not reflect on-track overtaking.
"""

import pandas as pd


_DNF_STATUSES = frozenset({"Finished", "Lapped"})


def _is_classified(status: str) -> bool:
    """Return True if the status represents a classified finisher."""
    if status in _DNF_STATUSES:
        return True
    if isinstance(status, str) and status.startswith("+") and "Lap" in status:
        return True
    return False


def position_changes_per_race(results_df: pd.DataFrame) -> pd.DataFrame:
    """Return net position change per driver for every race.

    Args:
        results_df: DataFrame with columns [season, round, race_name,
                    driver_id, driver_name, grid_position,
                    finish_position, status].

    Returns:
        DataFrame with columns [season, round, race_name, driver_id,
        driver_name, grid, finish, delta].
        delta = grid - finish (positive = gained positions).
        Excludes DNFs and pit-lane starters (grid == 0 or None).
    """
    required = {
        "season", "round", "race_name", "driver_id",
        "driver_name", "grid_position", "finish_position", "status",
    }
    missing = required - set(results_df.columns)
    if missing:
        raise ValueError(f"results_df missing columns: {missing}")

    records = []
    for _, row in results_df.iterrows():
        if not _is_classified(row["status"]):
            continue
        try:
            grid = int(row["grid_position"])
            finish = int(row["finish_position"])
        except (TypeError, ValueError):
            continue
        if grid == 0:
            continue
        records.append({
            "season": row["season"],
            "round": row["round"],
            "race_name": row["race_name"],
            "driver_id": row["driver_id"],
            "driver_name": row["driver_name"],
            "grid": grid,
            "finish": finish,
            "delta": grid - finish,
        })

    if not records:
        return pd.DataFrame(
            columns=[
                "season", "round", "race_name", "driver_id",
                "driver_name", "grid", "finish", "delta",
            ]
        )
    return (
        pd.DataFrame(records)
        .sort_values(["season", "round", "finish"])
        .reset_index(drop=True)
    )


def overtake_index_per_race(results_df: pd.DataFrame) -> pd.DataFrame:
    """Compute aggregate overtake index per race.

    overtake_index = positions_gained / starters, where:
    - positions_gained = sum of positive deltas among classified finishers
      (excluding pit-lane starters)
    - starters = drivers with a valid grid position > 0

    Normalising by starters controls for different field sizes and attrition.

    Args:
        results_df: Same format as position_changes_per_race().

    Returns:
        DataFrame with columns [season, round, race_name, starters,
        finishers, positions_gained, mean_abs_delta, overtake_index].
        Sorted by season and round.
    """
    changes = position_changes_per_race(results_df)
    if changes.empty:
        return pd.DataFrame(
            columns=[
                "season", "round", "race_name", "starters",
                "finishers", "positions_gained", "mean_abs_delta",
                "overtake_index",
            ]
        )

    # starters = all drivers with a valid grid > 0 (regardless of finish)
    starters_df = results_df.copy()
    starters_df = starters_df[
        starters_df["grid_position"].apply(
            lambda x: _safe_int(x) is not None and _safe_int(x) > 0
        )
    ]
    starters_counts = (
        starters_df.groupby(["season", "round"])
        .size()
        .reset_index(name="starters")
    )

    agg = changes.groupby(["season", "round", "race_name"]).agg(
        finishers=("delta", "count"),
        positions_gained=("delta", lambda x: int(x[x > 0].sum())),
        mean_abs_delta=("delta", lambda x: round(x.abs().mean(), 3)),
    ).reset_index()

    agg = agg.merge(starters_counts, on=["season", "round"], how="left")
    agg["starters"] = agg["starters"].fillna(agg["finishers"]).astype(int)
    agg["overtake_index"] = (
        agg["positions_gained"] / agg["starters"]
    ).round(3)

    return agg.sort_values(["season", "round"]).reset_index(drop=True)


def overtake_index_by_circuit(race_index_df: pd.DataFrame) -> pd.DataFrame:
    """Mean overtake index per circuit across all seasons in the dataset.

    Args:
        race_index_df: Output of overtake_index_per_race().

    Returns:
        DataFrame with columns [race_name, races, mean_overtake_index,
        mean_positions_gained, mean_abs_delta].
        Sorted by mean_overtake_index ascending (most processional first).
    """
    if race_index_df.empty:
        return pd.DataFrame(
            columns=[
                "race_name", "races", "mean_overtake_index",
                "mean_positions_gained", "mean_abs_delta",
            ]
        )

    agg = race_index_df.groupby("race_name").agg(
        races=("overtake_index", "count"),
        mean_overtake_index=("overtake_index", "mean"),
        mean_positions_gained=("positions_gained", "mean"),
        mean_abs_delta=("mean_abs_delta", "mean"),
    ).reset_index()

    agg["mean_overtake_index"] = agg["mean_overtake_index"].round(3)
    agg["mean_positions_gained"] = agg["mean_positions_gained"].round(1)
    agg["mean_abs_delta"] = agg["mean_abs_delta"].round(3)

    return agg.sort_values("mean_overtake_index").reset_index(drop=True)


def monaco_vs_field(
    circuit_df: pd.DataFrame,
    circuit: str = "Monaco Grand Prix",
) -> pd.DataFrame:
    """Return circuit rankings with the target circuit flagged.

    Args:
        circuit_df: Output of overtake_index_by_circuit().
        circuit: Exact race_name string to highlight. Defaults to
                 'Monaco Grand Prix'. Use a substring match via
                 circuit_df[circuit_df['race_name'].str.contains('Monaco')]
                 to find the correct name first if unsure.

    Returns:
        circuit_df with an added boolean column 'is_target',
        sorted by mean_overtake_index ascending.
    """
    df = circuit_df.copy()
    df["is_target"] = df["race_name"] == circuit
    return df.sort_values("mean_overtake_index").reset_index(drop=True)


def _safe_int(value: object) -> int | None:
    """Convert value to int, returning None on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
