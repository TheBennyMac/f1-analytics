"""
Pre vs post pit window excitement analysis.

Tests the hypothesis that the first phase of a Grand Prix (before the main
pit window) is more competitive than the post-stop phase, where fresh tyres
tend to spread the field.

A sprint race has no mandatory stop, making it a useful pit-stop-free baseline.
The per-lap P1-P3 gap is used rather than P1-P10 to remain robust across
attrition-heavy fields and SC periods.
"""

import pandas as pd


def median_pit_lap(laps_df: pd.DataFrame) -> float | None:
    """Return the median lap on which drivers made their first pit stop.

    Args:
        laps_df: FastF1 laps DataFrame. Must contain columns:
                 ['Driver', 'LapNumber', 'PitInLap'].

    Returns:
        Median first pit lap across all drivers, or None if no pit stops found
        or if 'PitInLap' column is missing.
    """
    if "PitInLap" not in laps_df.columns:
        return None
    pit_laps = laps_df[laps_df["PitInLap"].fillna(False)]
    if pit_laps.empty:
        return None
    first_stops = pit_laps.groupby("Driver")["LapNumber"].min()
    return float(first_stops.median())


def lap_time_deltas_by_phase(
    laps_df: pd.DataFrame,
    split_lap: float,
) -> dict[str, float | None]:
    """Return mean per-lap field spread before and after a split lap.

    Computes the mean of the per-lap P1-P3 fastest lap gap across all laps in
    each phase. P1-P3 (not P1-P10) is used to remain robust across
    attrition-heavy fields and SC periods.

    Args:
        laps_df: FastF1 laps DataFrame.
        split_lap: Lap number to split on.
                   Laps < split_lap → pre-phase; laps >= split_lap → post-phase.

    Returns:
        Dict with keys:
            pre_mean_gap_s  — mean P1-P5 per-lap gap before split_lap
            post_mean_gap_s — mean P1-P5 per-lap gap from split_lap onward
            pre_laps        — number of distinct laps in the pre phase
            post_laps       — number of distinct laps in the post phase
        Values are None where a phase has no valid data.
    """
    clean = laps_df.copy()
    if "PitOutLap" in clean.columns:
        clean = clean[~clean["PitOutLap"].fillna(False)]
    if "PitInLap" in clean.columns:
        clean = clean[~clean["PitInLap"].fillna(False)]
    # IsAccurate is intentionally not applied here — in race sessions it marks
    # SC/VSC laps False but also filters too aggressively, leaving fewer than
    # the minimum drivers per lap number required to compute a gap.
    clean = clean.dropna(subset=["LapTime", "LapNumber"]).copy()
    clean["lap_s"] = clean["LapTime"].dt.total_seconds()

    def _mean_p1_p5_gap(phase_df: pd.DataFrame) -> float | None:
        if phase_df.empty:
            return None
        gaps = []
        for _, lap_group in phase_df.groupby("LapNumber"):
            ranked = lap_group["lap_s"].sort_values().reset_index(drop=True)
            if len(ranked) >= 3:
                gaps.append(float(ranked.iloc[2] - ranked.iloc[0]))
        if not gaps:
            return None
        return round(float(pd.Series(gaps).mean()), 3)

    pre = clean[clean["LapNumber"] < split_lap]
    post = clean[clean["LapNumber"] >= split_lap]
    return {
        "pre_mean_gap_s": _mean_p1_p5_gap(pre),
        "post_mean_gap_s": _mean_p1_p5_gap(post),
        "pre_laps": int(pre["LapNumber"].nunique()),
        "post_laps": int(post["LapNumber"].nunique()),
    }


def pit_window_summary(
    season_laps: dict[tuple[int, int], pd.DataFrame],
) -> pd.DataFrame:
    """Compute pre/post pit window phase analysis across multiple races.

    Args:
        season_laps: Dict mapping (season, round) to a FastF1 laps DataFrame.

    Returns:
        DataFrame with columns [season, round, split_lap, pre_mean_gap_s,
                                post_mean_gap_s, pre_laps, post_laps].
        Races with no detected pit stops are excluded — use sprint sessions
        separately as a no-stop baseline.
    """
    records = []
    for (season, round_), laps_df in season_laps.items():
        split = median_pit_lap(laps_df)
        if split is None:
            continue
        phases = lap_time_deltas_by_phase(laps_df, split)
        records.append({
            "season": season,
            "round": round_,
            "split_lap": split,
            **phases,
        })
    if not records:
        return pd.DataFrame(
            columns=[
                "season", "round", "split_lap",
                "pre_mean_gap_s", "post_mean_gap_s",
                "pre_laps", "post_laps",
            ]
        )
    return pd.DataFrame(records).sort_values(["season", "round"]).reset_index(drop=True)
