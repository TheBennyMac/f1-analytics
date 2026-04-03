"""
Field size normalisation, points boundary, and tail-of-field gap analysis.

Addresses the distortion that attrition races introduce when the classified
finisher count drops below the P1-Pn depth being measured.

Also tracks:
- P10/P11 boundary: how arbitrary is the points cut?
- Tail-of-field: how far behind is the back of the grid?
"""

import pandas as pd
from src.analysis.lap_time_delta import fastest_lap_per_driver


def p1_to_pn_gap_normalised(
    season_laps: dict[tuple[int, int], pd.DataFrame],
    n: int,
) -> pd.DataFrame:
    """Compute the P1-Pn lap time gap, flagging races where fewer than n
    drivers have valid lap data (attrition races).

    Unlike the base lap_time_delta functions which silently skip short fields,
    this always emits a row per race — with gap_s=None and sufficient=False
    when the field is too small. This makes attrition races visible rather
    than quietly removed from averages.

    Args:
        season_laps: Dict mapping (season, round) to a FastF1 laps DataFrame.
        n: Field depth to measure gap to (e.g. 10 for P1-P10).

    Returns:
        DataFrame with columns [season, round, n, gap_s,
                                drivers_with_laps, sufficient].
        sufficient = True where drivers_with_laps >= n.
    """
    records = []
    for (season, round_), laps_df in season_laps.items():
        fastest = fastest_lap_per_driver(laps_df)
        driver_count = len(fastest)
        gap = None
        if driver_count >= n:
            gap = round(
                float(fastest.iloc[n - 1]["fastest_lap_s"] - fastest.iloc[0]["fastest_lap_s"]),
                3,
            )
        records.append({
            "season": season,
            "round": round_,
            "n": n,
            "gap_s": gap,
            "drivers_with_laps": driver_count,
            "sufficient": driver_count >= n,
        })
    if not records:
        return pd.DataFrame(
            columns=["season", "round", "n", "gap_s", "drivers_with_laps", "sufficient"]
        )
    return pd.DataFrame(records).sort_values(["season", "round"]).reset_index(drop=True)


def p11_gap_per_race(
    season_laps: dict[tuple[int, int], pd.DataFrame],
) -> pd.DataFrame:
    """Return the P10-P11 and P1-P11 lap time gaps per race.

    The P10-P11 gap measures how arbitrary the points boundary is: a large
    gap means P11 was genuinely off the pace; a small gap means the cut
    was razor-thin.

    Args:
        season_laps: Dict mapping (season, round) to a FastF1 laps DataFrame.

    Returns:
        DataFrame with columns [season, round, p10_lap_s, p11_lap_s,
                                p10_p11_gap_s, p1_p11_gap_s].
        Races with fewer than 11 drivers with valid laps are excluded.
    """
    records = []
    for (season, round_), laps_df in season_laps.items():
        fastest = fastest_lap_per_driver(laps_df)
        if len(fastest) < 11:
            continue
        records.append({
            "season": season,
            "round": round_,
            "p10_lap_s": round(float(fastest.iloc[9]["fastest_lap_s"]), 3),
            "p11_lap_s": round(float(fastest.iloc[10]["fastest_lap_s"]), 3),
            "p10_p11_gap_s": round(
                float(fastest.iloc[10]["fastest_lap_s"] - fastest.iloc[9]["fastest_lap_s"]), 3
            ),
            "p1_p11_gap_s": round(
                float(fastest.iloc[10]["fastest_lap_s"] - fastest.iloc[0]["fastest_lap_s"]), 3
            ),
        })
    if not records:
        return pd.DataFrame(
            columns=["season", "round", "p10_lap_s", "p11_lap_s",
                     "p10_p11_gap_s", "p1_p11_gap_s"]
        )
    return pd.DataFrame(records).sort_values(["season", "round"]).reset_index(drop=True)


def tail_gap_analysis(
    season_laps: dict[tuple[int, int], pd.DataFrame],
) -> pd.DataFrame:
    """Return the gap from the last classified driver to P1 and P10 per race.

    Uses fastest race lap as the pace proxy — drivers who set no valid laps
    (complete DNFs, DNS) are not included, so the tail represents the slowest
    driver who actually raced rather than someone who parked on lap 1.

    Args:
        season_laps: Dict mapping (season, round) to a FastF1 laps DataFrame.

    Returns:
        DataFrame with columns [season, round, drivers_with_laps,
                                p1_lap_s, p10_lap_s, last_lap_s,
                                tail_to_p1_gap_s, tail_to_p10_gap_s].
        p10_lap_s and tail_to_p10_gap_s are None where fewer than 10 drivers
        have valid laps.
    """
    records = []
    for (season, round_), laps_df in season_laps.items():
        fastest = fastest_lap_per_driver(laps_df)
        if len(fastest) < 2:
            continue
        p1_s = float(fastest.iloc[0]["fastest_lap_s"])
        last_s = float(fastest.iloc[-1]["fastest_lap_s"])
        p10_s = float(fastest.iloc[9]["fastest_lap_s"]) if len(fastest) >= 10 else None
        records.append({
            "season": season,
            "round": round_,
            "drivers_with_laps": len(fastest),
            "p1_lap_s": round(p1_s, 3),
            "p10_lap_s": round(p10_s, 3) if p10_s is not None else None,
            "last_lap_s": round(last_s, 3),
            "tail_to_p1_gap_s": round(last_s - p1_s, 3),
            "tail_to_p10_gap_s": round(last_s - p10_s, 3) if p10_s is not None else None,
        })
    if not records:
        return pd.DataFrame(
            columns=[
                "season", "round", "drivers_with_laps",
                "p1_lap_s", "p10_lap_s", "last_lap_s",
                "tail_to_p1_gap_s", "tail_to_p10_gap_s",
            ]
        )
    return pd.DataFrame(records).sort_values(["season", "round"]).reset_index(drop=True)
