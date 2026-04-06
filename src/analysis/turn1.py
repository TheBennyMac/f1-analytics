"""
Turn 1 chaos analysis.

Tests whether regulation reset years (Year 1 of an era) produce more
first-lap incidents than settled era years (Year 2+). The hypothesis is
that unfamiliar cars, uncertain relative pace, and aggressive early-race
positioning combine to cause more chaos at Turn 1 in reset years.

Two metrics:
1. First-lap retirement rate — drivers who DNF'd on or before lap 1,
   as a proportion of starters. Uses results_df (no lap data needed).
2. Lap 1 position change activity — positions gained on lap 1 per race,
   from FastF1 lap-by-lap data. Higher activity = more chaos.

Both are grouped by year-within-era using EraHelper.
"""

import pandas as pd


def _is_dnf(status: str) -> bool:
    """Return True if the status represents a non-finish."""
    if status in ("Finished", "Lapped"):
        return False
    if isinstance(status, str) and status.startswith("+") and "Lap" in status:
        return False
    return True


def first_lap_retirements(results_df: pd.DataFrame) -> pd.DataFrame:
    """Return first-lap retirement rate per race and by era year.

    A first-lap retirement is a driver who:
    - Had a valid grid position (started the race)
    - Did not finish (DNF status)
    - Has a finish_position of None (did not complete enough laps to classify)

    This is a proxy for Turn 1 and early-lap incidents. It cannot distinguish
    a Turn 1 collision from a lap 3 mechanical, but non-classified DNFs are
    more likely to reflect early incidents than classified retirements.

    Args:
        results_df: DataFrame with columns [season, round, race_name,
                    driver_id, grid_position, finish_position, status].

    Returns:
        DataFrame with columns [season, round, race_name, era_year,
        starters, first_lap_dnfs, dnf_rate].
        One row per race, sorted by season and round.

    Raises:
        ValueError: If required columns are missing.
    """
    from src.utils.era_helper import get_year_within_era

    required = {
        "season", "round", "race_name",
        "driver_id", "grid_position", "finish_position", "status",
    }
    missing = required - set(results_df.columns)
    if missing:
        raise ValueError(f"results_df missing columns: {missing}")

    records = []
    for (season, round_, race_name), group in results_df.groupby(
        ["season", "round", "race_name"]
    ):
        starters = group[group["grid_position"].notna() &
                         (group["grid_position"] != 0)]
        n_starters = len(starters)
        if n_starters == 0:
            continue

        first_lap_dnfs = starters[
            starters["status"].apply(_is_dnf) &
            starters["finish_position"].isna()
        ]
        n_dnfs = len(first_lap_dnfs)

        try:
            era_year = get_year_within_era(int(season))
        except ValueError:
            era_year = None

        records.append({
            "season": season,
            "round": round_,
            "race_name": race_name,
            "era_year": era_year,
            "starters": n_starters,
            "first_lap_dnfs": n_dnfs,
            "dnf_rate": round(n_dnfs / n_starters, 3),
        })

    if not records:
        return pd.DataFrame(
            columns=[
                "season", "round", "race_name", "era_year",
                "starters", "first_lap_dnfs", "dnf_rate",
            ]
        )
    return (
        pd.DataFrame(records)
        .sort_values(["season", "round"])
        .reset_index(drop=True)
    )


def lap1_position_changes(laps_df: pd.DataFrame) -> dict[str, float | None]:
    """Return position change activity on lap 1 for a single race.

    Counts total positions gained on lap 1 (grid to end of lap 1 position).
    Requires both GridPosition (or Position on lap 0) and Position on lap 1.

    Args:
        laps_df: FastF1 laps DataFrame for a race. Must contain columns:
                 ['Driver', 'LapNumber', 'Position', 'GridPosition'] or
                 ['Driver', 'LapNumber', 'Position'] where lap 0 is grid.

    Returns:
        Dict with keys:
            positions_gained — total positions gained on lap 1
            drivers          — number of drivers with valid lap 1 data
    """
    required = {"Driver", "LapNumber", "Position"}
    if not required.issubset(set(laps_df.columns)):
        return {"positions_gained": None, "drivers": 0}

    lap1 = laps_df[laps_df["LapNumber"] == 1].copy()
    if lap1.empty:
        return {"positions_gained": None, "drivers": 0}

    lap1 = lap1.dropna(subset=["Position"])
    lap1["Position"] = lap1["Position"].astype(int)

    # Use GridPosition if available, otherwise fall back to starting order
    if "GridPosition" in laps_df.columns:
        grid = (
            laps_df[["Driver", "GridPosition"]]
            .dropna()
            .drop_duplicates("Driver")
            .copy()
        )
        grid["GridPosition"] = grid["GridPosition"].astype(int)
        lap1_clean = lap1.drop(columns=["GridPosition"], errors="ignore")
        merged = lap1_clean.merge(grid, on="Driver", how="inner")
        merged = merged[merged["GridPosition"] > 0]
        merged["delta"] = merged["GridPosition"] - merged["Position"]
    else:
        return {"positions_gained": None, "drivers": 0}

    if merged.empty:
        return {"positions_gained": None, "drivers": 0}

    positions_gained = int(merged[merged["delta"] > 0]["delta"].sum())
    return {
        "positions_gained": positions_gained,
        "drivers": len(merged),
    }


def turn1_summary_by_era_year(
    retirement_df: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate first-lap retirement metrics by year-within-era.

    Args:
        retirement_df: Output of first_lap_retirements().

    Returns:
        DataFrame with columns [era_year, races, mean_starters,
        total_first_lap_dnfs, mean_dnf_rate].
        Sorted by era_year ascending.
    """
    if retirement_df.empty:
        return pd.DataFrame(
            columns=[
                "era_year", "races", "mean_starters",
                "total_first_lap_dnfs", "mean_dnf_rate",
            ]
        )

    df = retirement_df.dropna(subset=["era_year"]).copy()
    agg = df.groupby("era_year").agg(
        races=("race_name", "count"),
        mean_starters=("starters", "mean"),
        total_first_lap_dnfs=("first_lap_dnfs", "sum"),
        mean_dnf_rate=("dnf_rate", "mean"),
    ).reset_index()

    agg["mean_starters"] = agg["mean_starters"].round(1)
    agg["mean_dnf_rate"] = agg["mean_dnf_rate"].round(3)

    return agg.sort_values("era_year").reset_index(drop=True)
