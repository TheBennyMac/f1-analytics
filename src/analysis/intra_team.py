"""
Intra-team driver comparison analysis.

Primary metric: qualifying gap between teammates (seconds and %).
Same car, same weekend — the purest isolation of driver factor vs machinery.

Secondary metric: race pace delta — useful but noisier due to strategy,
traffic, and incident exposure.

Primary lens: 2026 Year 1 vs 2022 Year 1 (regulation reset comparison).
"""

import pandas as pd


def prepare_quali_results(session_results: pd.DataFrame) -> pd.DataFrame:
    """Normalise a FastF1 qualifying session.results DataFrame for this module.

    Extracts the best Q time (minimum of Q1/Q2/Q3) per driver and retains
    the driver abbreviation and team name.

    Args:
        session_results: FastF1 session.results DataFrame. Expected columns:
                         Abbreviation, TeamName, Q1, Q2, Q3 (timedeltas or NaT).

    Returns:
        DataFrame with columns [driver_abbr, team, best_q_s].
        best_q_s is the fastest qualifying time in seconds, or None if
        the driver set no valid time in any segment.
    """
    records = []
    for _, row in session_results.iterrows():
        times = []
        for col in ("Q1", "Q2", "Q3"):
            val = row.get(col)
            if val is not None and pd.notna(val):
                times.append(val.total_seconds())
        records.append({
            "driver_abbr": row.get("Abbreviation"),
            "team": row.get("TeamName"),
            "best_q_s": min(times) if times else None,
        })
    return pd.DataFrame(records)


def teammate_quali_gaps(
    quali_results: pd.DataFrame,
    season: int,
    round_: int,
    race_name: str,
) -> pd.DataFrame:
    """Compute the qualifying gap between teammates for a single race weekend.

    Pairs drivers within the same team. Constructors where fewer or more than
    two drivers have valid best Q times are excluded (e.g. retirement mid-session,
    third-car entries).

    Args:
        quali_results: DataFrame with columns [driver_abbr, team, best_q_s].
                       Use prepare_quali_results() to build this from FastF1 output.
        season: Championship year.
        round_: Round number.
        race_name: Race name for labelling.

    Returns:
        DataFrame with columns:
            season, round, race_name, constructor,
            driver_a, driver_b   — sorted alphabetically by abbreviation,
            time_a_s, time_b_s  — best Q times in seconds,
            gap_s               — abs(time_a_s - time_b_s),
            gap_pct             — gap_s / faster_time * 100,
            faster_driver       — abbreviation of the faster driver.
        Empty DataFrame (correct columns) if no valid pairs found.
    """
    _COLUMNS = [
        "season", "round", "race_name", "constructor",
        "driver_a", "driver_b", "time_a_s", "time_b_s",
        "gap_s", "gap_pct", "faster_driver",
    ]
    df = quali_results.dropna(subset=["best_q_s"]).copy()

    records = []
    for constructor, group in df.groupby("team"):
        if len(group) != 2:
            continue
        drivers = group.sort_values("driver_abbr").reset_index(drop=True)
        row_a, row_b = drivers.iloc[0], drivers.iloc[1]
        time_a, time_b = row_a["best_q_s"], row_b["best_q_s"]
        gap_s = abs(time_a - time_b)
        faster_time = min(time_a, time_b)
        gap_pct = gap_s / faster_time * 100
        faster = row_a["driver_abbr"] if time_a <= time_b else row_b["driver_abbr"]
        records.append({
            "season": season,
            "round": round_,
            "race_name": race_name,
            "constructor": constructor,
            "driver_a": row_a["driver_abbr"],
            "driver_b": row_b["driver_abbr"],
            "time_a_s": round(time_a, 3),
            "time_b_s": round(time_b, 3),
            "gap_s": round(gap_s, 3),
            "gap_pct": round(gap_pct, 4),
            "faster_driver": faster,
        })

    if not records:
        return pd.DataFrame(columns=_COLUMNS)
    return pd.DataFrame(records)


def season_teammate_gaps(
    season_quali: dict[tuple[int, int, str], pd.DataFrame],
) -> pd.DataFrame:
    """Aggregate teammate qualifying gaps across multiple races.

    Args:
        season_quali: Dict mapping (season, round, race_name) to a qualifying
                      results DataFrame with columns [driver_abbr, team, best_q_s].

    Returns:
        Long-form DataFrame combining teammate_quali_gaps() across all races.
        Empty DataFrame if no valid pairs found in any race.
    """
    frames = []
    for (season, round_, race_name), df in season_quali.items():
        gaps = teammate_quali_gaps(df, season, round_, race_name)
        if not gaps.empty:
            frames.append(gaps)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def mean_gap_by_constructor(gaps_df: pd.DataFrame) -> pd.DataFrame:
    """Mean qualifying gap per constructor across all races in the dataset.

    Args:
        gaps_df: Output of season_teammate_gaps() or teammate_quali_gaps().

    Returns:
        DataFrame with columns [constructor, races, mean_gap_s, mean_gap_pct].
        Sorted by mean_gap_s ascending (closest pairs first).
    """
    summary = gaps_df.groupby("constructor").agg(
        races=("gap_s", "count"),
        mean_gap_s=("gap_s", "mean"),
        mean_gap_pct=("gap_pct", "mean"),
    ).reset_index()
    summary["mean_gap_s"] = summary["mean_gap_s"].round(3)
    summary["mean_gap_pct"] = summary["mean_gap_pct"].round(4)
    return summary.sort_values("mean_gap_s").reset_index(drop=True)


def driver_dominance(gaps_df: pd.DataFrame, min_races: int = 1) -> pd.DataFrame:
    """How often each driver outqualified their teammate.

    Args:
        gaps_df: Output of season_teammate_gaps() or teammate_quali_gaps().
        min_races: Minimum number of races a driver must have participated in
                   to appear in the output. Use this to exclude replacement/
                   one-off drivers and keep the results to full-season regulars.
                   Defaults to 1 (no filtering).

    Returns:
        DataFrame with columns [driver, constructor, faster_count, total_races, win_pct].
        win_pct is the percentage of races where the driver was the faster teammate.
        Sorted by win_pct descending.
    """
    win_counts = (
        gaps_df.groupby(["faster_driver", "constructor"])["gap_s"]
        .count()
        .reset_index()
    )
    win_counts.columns = ["driver", "constructor", "faster_count"]

    # Total races per driver: each driver appears as driver_a or driver_b
    total_a = (
        gaps_df.groupby(["driver_a", "constructor"])["gap_s"].count().reset_index()
    )
    total_a.columns = ["driver", "constructor", "count_a"]
    total_b = (
        gaps_df.groupby(["driver_b", "constructor"])["gap_s"].count().reset_index()
    )
    total_b.columns = ["driver", "constructor", "count_b"]

    totals = total_a.merge(total_b, on=["driver", "constructor"], how="outer").fillna(0)
    totals["total_races"] = (totals["count_a"] + totals["count_b"]).astype(int)
    totals = totals[["driver", "constructor", "total_races"]]

    summary = totals.merge(win_counts, on=["driver", "constructor"], how="left")
    summary["faster_count"] = summary["faster_count"].fillna(0).astype(int)
    summary["win_pct"] = (summary["faster_count"] / summary["total_races"] * 100).round(1)

    summary = summary[summary["total_races"] >= min_races]
    return summary.sort_values("win_pct", ascending=False).reset_index(drop=True)
