"""
Sector time breakdown analysis.

Measures competitive parity at the sector level — which parts of the track
separate the field, and how this changes across regulation eras.

Uses race fastest sector times (not theoretical best lap, which may never
have been set as a combined lap). Pit-in/out and inaccurate laps excluded.
"""

import pandas as pd


def best_sector_times(laps_df: pd.DataFrame) -> pd.DataFrame:
    """Return the best sector time (in seconds) per driver across a session.

    Args:
        laps_df: FastF1 laps DataFrame. Expected columns:
                 ['Driver', 'Sector1Time', 'Sector2Time', 'Sector3Time'].
                 Optional: ['IsAccurate']. Pit columns: PitOutLap/PitInLap
                 (boolean) or PitOutTime/PitInTime (FastF1 native timestamps).

    Returns:
        DataFrame with columns [driver, best_s1_s, best_s2_s, best_s3_s],
        sorted by best_s1_s ascending. Drivers missing any sector are excluded.

    Raises:
        ValueError: If any of the three Sector*Time columns are missing.
    """
    for col in ("Sector1Time", "Sector2Time", "Sector3Time"):
        if col not in laps_df.columns:
            raise ValueError(f"Missing column: {col}")

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

    for col in ("Sector1Time", "Sector2Time", "Sector3Time"):
        clean[col + "_s"] = pd.to_timedelta(clean[col], errors="coerce").dt.total_seconds()

    result = (
        clean.groupby("Driver")
        .agg(
            best_s1_s=("Sector1Time_s", "min"),
            best_s2_s=("Sector2Time_s", "min"),
            best_s3_s=("Sector3Time_s", "min"),
        )
        .reset_index()
        .rename(columns={"Driver": "driver"})
        .dropna(subset=["best_s1_s", "best_s2_s", "best_s3_s"])
    )
    return result.sort_values("best_s1_s").reset_index(drop=True)


def sector_gap(laps_df: pd.DataFrame, n: int = 10) -> dict[str, float | None]:
    """Return the P1-Pn gap per sector for a single session.

    Each sector is ranked independently — this is not a combined lap gap.

    Args:
        laps_df: FastF1 laps DataFrame.
        n: Position to measure the gap to (default 10).

    Returns:
        Dict with keys [s1_gap_s, s2_gap_s, s3_gap_s].
        Values are None where fewer than n drivers have a valid sector time.
    """
    best = best_sector_times(laps_df)

    def _gap(col: str) -> float | None:
        ranked = best.dropna(subset=[col]).sort_values(col).reset_index(drop=True)
        if len(ranked) < n:
            return None
        return round(float(ranked.iloc[n - 1][col] - ranked.iloc[0][col]), 3)

    return {
        "s1_gap_s": _gap("best_s1_s"),
        "s2_gap_s": _gap("best_s2_s"),
        "s3_gap_s": _gap("best_s3_s"),
    }


def sector_gap_summary(
    season_laps: dict[tuple[int, int], pd.DataFrame],
    n: int = 10,
) -> pd.DataFrame:
    """Aggregate P1-Pn sector gaps across multiple races.

    Args:
        season_laps: Dict mapping (season, round) to a FastF1 laps DataFrame.
        n: Position to measure the gap to (default 10).

    Returns:
        DataFrame with columns [season, round, s1_gap_s, s2_gap_s, s3_gap_s].
        Rounds where no gaps could be computed are excluded.
    """
    records = []
    for (season, round_), laps_df in season_laps.items():
        try:
            gaps = sector_gap(laps_df, n=n)
        except (ValueError, KeyError):
            continue
        if any(v is not None for v in gaps.values()):
            records.append({"season": season, "round": round_, **gaps})
    if not records:
        return pd.DataFrame(columns=["season", "round", "s1_gap_s", "s2_gap_s", "s3_gap_s"])
    return pd.DataFrame(records).sort_values(["season", "round"]).reset_index(drop=True)


def mean_sector_gap_by_season(sector_df: pd.DataFrame) -> pd.DataFrame:
    """Return the mean P1-Pn sector gap per season.

    Args:
        sector_df: Output of sector_gap_summary().

    Returns:
        DataFrame with columns [season, mean_s1_gap_s, mean_s2_gap_s,
                                mean_s3_gap_s, races].
    """
    summary = sector_df.groupby("season").agg(
        mean_s1_gap_s=("s1_gap_s", "mean"),
        mean_s2_gap_s=("s2_gap_s", "mean"),
        mean_s3_gap_s=("s3_gap_s", "mean"),
        races=("s1_gap_s", "count"),
    ).reset_index()
    for col in ("mean_s1_gap_s", "mean_s2_gap_s", "mean_s3_gap_s"):
        summary[col] = summary[col].round(3)
    return summary.sort_values("season").reset_index(drop=True)
