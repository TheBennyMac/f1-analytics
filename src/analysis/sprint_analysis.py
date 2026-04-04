"""
Sprint race analysis.

Sprints have no mandatory pit stop, making them a useful pit-stop-free
pace baseline. Comparing sprint vs full race pace on the same weekend
isolates the effect of tyre strategy and traffic on race pace.

Position changes in sprints are also less contaminated by pit stop timing
luck than in full races.
"""

import pandas as pd


def sprint_position_changes(sprint_results: pd.DataFrame) -> pd.DataFrame:
    """Return positions gained/lost per driver in a sprint.

    Args:
        sprint_results: FastF1 session.results DataFrame for a sprint session.
                        Expected columns: Abbreviation, TeamName,
                        GridPosition, Position.

    Returns:
        DataFrame with columns [driver, team, grid, finish, delta].
        delta = grid - finish (positive = gained positions).
        Excludes drivers with no valid grid or finish position.
    """
    records = []
    for _, row in sprint_results.iterrows():
        try:
            grid_i = int(row.get("GridPosition"))
            finish_i = int(row.get("Position"))
        except (TypeError, ValueError):
            continue
        records.append({
            "driver": row.get("Abbreviation"),
            "team": row.get("TeamName"),
            "grid": grid_i,
            "finish": finish_i,
            "delta": grid_i - finish_i,
        })
    if not records:
        return pd.DataFrame(columns=["driver", "team", "grid", "finish", "delta"])
    return pd.DataFrame(records).sort_values("finish").reset_index(drop=True)


def sprint_vs_race_pace(
    sprint_laps: pd.DataFrame,
    race_laps: pd.DataFrame,
) -> pd.DataFrame:
    """Compare median clean lap pace between sprint and full race per driver.

    Uses median rather than fastest lap to reduce the effect of outlier laps
    (e.g. a single very quick lap on fresh tyres in the sprint).

    Args:
        sprint_laps: FastF1 laps DataFrame for the sprint session.
        race_laps: FastF1 laps DataFrame for the full race.

    Returns:
        DataFrame with columns [driver, sprint_median_s, race_median_s, delta_s].
        delta_s = race_median_s - sprint_median_s (positive = slower in full race).
        Only includes drivers present in both sessions with valid laps.
    """
    def _median_lap(laps_df: pd.DataFrame) -> pd.DataFrame:
        clean = laps_df.copy()
        if "PitOutLap" in clean.columns:
            clean = clean[~clean["PitOutLap"].fillna(False)]
        elif "PitOutTime" in clean.columns:
            clean = clean[clean["PitOutTime"].isna()]
        if "PitInLap" in clean.columns:
            clean = clean[~clean["PitInLap"].fillna(False)]
        elif "PitInTime" in clean.columns:
            clean = clean[clean["PitInTime"].isna()]
        if "IsAccurate" in clean.columns:
            clean = clean[clean["IsAccurate"].fillna(False)]
        clean = clean.dropna(subset=["LapTime"])
        clean = clean.copy()
        clean["lap_s"] = clean["LapTime"].dt.total_seconds()
        return clean.groupby("Driver")["lap_s"].median().reset_index()

    sprint_medians = _median_lap(sprint_laps)
    sprint_medians.columns = ["driver", "sprint_median_s"]
    race_medians = _median_lap(race_laps)
    race_medians.columns = ["driver", "race_median_s"]

    merged = sprint_medians.merge(race_medians, on="driver", how="inner")
    if merged.empty:
        return pd.DataFrame(
            columns=["driver", "sprint_median_s", "race_median_s", "delta_s"]
        )
    merged["sprint_median_s"] = merged["sprint_median_s"].round(3)
    merged["race_median_s"] = merged["race_median_s"].round(3)
    merged["delta_s"] = (merged["race_median_s"] - merged["sprint_median_s"]).round(3)
    return merged.sort_values("driver").reset_index(drop=True)


def flag_sprint_weekends(results_df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per round flagged as a sprint weekend.

    Args:
        results_df: DataFrame with columns [season, round, is_sprint_weekend].

    Returns:
        DataFrame with columns [season, round, is_sprint_weekend],
        deduplicated to one row per round.

    Raises:
        ValueError: If 'is_sprint_weekend' column is missing.
    """
    if "is_sprint_weekend" not in results_df.columns:
        raise ValueError("results_df must contain 'is_sprint_weekend' column")
    return (
        results_df[["season", "round", "is_sprint_weekend"]]
        .drop_duplicates(subset=["season", "round"])
        .sort_values(["season", "round"])
        .reset_index(drop=True)
    )
