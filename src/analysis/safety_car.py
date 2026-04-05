"""
Safety car lottery analysis.

Tests whether safety car deployments materially affect race outcomes
(position changes). The "lottery" narrative holds that SC timing is
arbitrary and disproportionately reshuffles the field — benefiting
drivers who happened to pit just before the deployment and penalising
those who just pitted or who were running long.

Method:
- Count distinct SC/VSC/red flag deployment events per race
- Correlate deployment count with overtake index (position change activity)
- Compare mean overtake index across races grouped by SC count (0, 1, 2+)

A high overtake index in SC races versus non-SC races would support the
narrative that SCs artificially inflate position changes (lottery effect).
A low index in SC races would suggest SCs cause bunching without genuine
overtaking.
"""

import pandas as pd


def sc_counts_per_race(results_df: pd.DataFrame) -> pd.DataFrame:
    """Extract one row per race with SC/VSC/red flag deployment counts.

    Args:
        results_df: DataFrame with columns [season, round, race_name,
                    sc_count, vsc_count, red_flag_count].
                    One row per driver per race (counts are race-level,
                    so any driver row is representative).

    Returns:
        DataFrame with columns [season, round, race_name, sc_count,
        vsc_count, red_flag_count, any_intervention].
        One row per race, sorted by season and round.

    Raises:
        ValueError: If required columns are missing.
    """
    required = {"season", "round", "race_name", "sc_count",
                "vsc_count", "red_flag_count"}
    missing = required - set(results_df.columns)
    if missing:
        raise ValueError(f"results_df missing columns: {missing}")

    race_level = (
        results_df[["season", "round", "race_name",
                    "sc_count", "vsc_count", "red_flag_count"]]
        .drop_duplicates(subset=["season", "round"])
        .copy()
    )
    race_level["any_intervention"] = (
        (race_level["sc_count"] > 0) |
        (race_level["vsc_count"] > 0) |
        (race_level["red_flag_count"] > 0)
    )
    return race_level.sort_values(["season", "round"]).reset_index(drop=True)


def sc_position_impact(
    sc_df: pd.DataFrame,
    race_oi_df: pd.DataFrame,
) -> pd.DataFrame:
    """Join SC deployment counts with overtake index per race.

    Args:
        sc_df: Output of sc_counts_per_race().
        race_oi_df: Output of overtake_index_per_race() from overtake_index.py.
                    Expected columns: [season, round, race_name,
                    overtake_index, positions_gained, finishers].

    Returns:
        DataFrame with one row per race combining SC counts and overtake
        index. Columns: [season, round, race_name, sc_count, vsc_count,
        red_flag_count, any_intervention, overtake_index,
        positions_gained, finishers].
        Races with no overtake index data are excluded.
    """
    merged = sc_df.merge(
        race_oi_df[["season", "round", "overtake_index",
                    "positions_gained", "finishers"]],
        on=["season", "round"],
        how="inner",
    )
    return merged.sort_values(["season", "round"]).reset_index(drop=True)


def sc_lottery_summary(impact_df: pd.DataFrame) -> pd.DataFrame:
    """Mean overtake index grouped by SC deployment count (0, 1, 2+).

    Args:
        impact_df: Output of sc_position_impact().

    Returns:
        DataFrame with columns [sc_group, races, mean_overtake_index,
        mean_positions_gained].
        sc_group values: '0 SCs', '1 SC', '2+ SCs'.
        Sorted by sc_group ascending.
    """
    if impact_df.empty:
        return pd.DataFrame(
            columns=["sc_group", "races", "mean_overtake_index",
                     "mean_positions_gained"]
        )

    df = impact_df.copy()
    df["sc_group"] = df["sc_count"].apply(
        lambda n: "0 SCs" if n == 0 else ("1 SC" if n == 1 else "2+ SCs")
    )

    summary = df.groupby("sc_group").agg(
        races=("overtake_index", "count"),
        mean_overtake_index=("overtake_index", "mean"),
        mean_positions_gained=("positions_gained", "mean"),
    ).reset_index()

    summary["mean_overtake_index"] = summary["mean_overtake_index"].round(3)
    summary["mean_positions_gained"] = summary["mean_positions_gained"].round(1)

    order = ["0 SCs", "1 SC", "2+ SCs"]
    summary["sc_group"] = pd.Categorical(
        summary["sc_group"], categories=order, ordered=True
    )
    return summary.sort_values("sc_group").reset_index(drop=True)


def intervention_frequency(sc_df: pd.DataFrame) -> pd.DataFrame:
    """Count races by intervention type per season.

    Args:
        sc_df: Output of sc_counts_per_race().

    Returns:
        DataFrame with columns [season, total_races, sc_races, vsc_races,
        red_flag_races, clean_races, sc_rate].
        sc_rate = sc_races / total_races.
    """
    if sc_df.empty:
        return pd.DataFrame(
            columns=["season", "total_races", "sc_races", "vsc_races",
                     "red_flag_races", "clean_races", "sc_rate"]
        )

    agg = sc_df.groupby("season").agg(
        total_races=("race_name", "count"),
        sc_races=("sc_count", lambda x: (x > 0).sum()),
        vsc_races=("vsc_count", lambda x: (x > 0).sum()),
        red_flag_races=("red_flag_count", lambda x: (x > 0).sum()),
        clean_races=("any_intervention", lambda x: (~x).sum()),
    ).reset_index()

    agg["sc_rate"] = (agg["sc_races"] / agg["total_races"]).round(3)
    return agg.sort_values("season").reset_index(drop=True)
