"""
Championship lead conversion analysis.

For each season and constructor, identifies whether that constructor held the
championship lead at mid-season, and whether they converted it to a title.

"Led at mid-season" is defined as holding P1 in the constructor standings after
any round from round 4 onward up to and including the halfway point of the season.
Round 4 threshold excludes fluky early-season leads caused by 1-2 competitor DNFs.

Used for the Ferrari narrative: do they consistently fail to convert leads into titles?
"""

import pandas as pd

from src.utils.era_helper import get_era_info


def mid_season_leaders(
    standings_df: pd.DataFrame,
    min_round: int = 4,
) -> pd.DataFrame:
    """Identify which constructors led the championship at mid-season for each season.

    Args:
        standings_df: Cumulative constructor standings with columns
            [season, round, constructor_id, constructor_name, points].
            One row per constructor per round. Points must be cumulative.
        min_round: Ignore rounds below this number (default 4).

    Returns:
        DataFrame with one row per (season, constructor_id) that held P1 at
        any round from min_round up to the halfway point, with columns:
            season, constructor_id, constructor_name, era_name,
            first_led_round, max_lead_points, led_at_midseason,
            won_title, final_position.
    """
    records = []

    for season, season_df in standings_df.groupby("season"):
        era = get_era_info(season)
        total_rounds = int(season_df["round"].max())
        midpoint = total_rounds // 2

        # For each round, identify who is P1 (highest cumulative points)
        for rnd, rnd_df in season_df.groupby("round"):
            if rnd < min_round or rnd > midpoint:
                continue
            leader = rnd_df.sort_values("points", ascending=False).iloc[0]
            records.append({
                "season": season,
                "round": int(rnd),
                "constructor_id": leader["constructor_id"],
                "constructor_name": leader["constructor_name"],
                "points_at_lead": float(leader["points"]),
            })

    if not records:
        return pd.DataFrame()

    leads_df = pd.DataFrame(records)

    # Compute first round led and max points while leading per (season, constructor)
    agg = (
        leads_df.groupby(["season", "constructor_id", "constructor_name"])
        .agg(
            first_led_round=("round", "min"),
            max_lead_points=("points_at_lead", "max"),
        )
        .reset_index()
    )

    # Determine the final champion for each season
    final_standings = _final_standings(standings_df)

    merged = agg.merge(final_standings, on=["season", "constructor_id"], how="left")

    # Add era label
    era_map = standings_df[["season"]].drop_duplicates()
    era_map["era_name"] = era_map["season"].map(lambda s: get_era_info(s).name)
    era_map["year_in_era"] = era_map["season"].map(lambda s: get_era_info(s).year_within_era)
    merged = merged.merge(era_map, on="season", how="left")

    merged["led_at_midseason"] = True
    merged["won_title"] = merged["final_position"] == 1

    return merged[[
        "season", "constructor_id", "constructor_name",
        "era_name", "year_in_era",
        "first_led_round", "max_lead_points",
        "led_at_midseason", "won_title", "final_position",
    ]].sort_values(["season", "first_led_round"]).reset_index(drop=True)


def _final_standings(standings_df: pd.DataFrame) -> pd.DataFrame:
    """Return the final championship position for each constructor in each season."""
    final_round = (
        standings_df.groupby("season")["round"].max().reset_index()
        .rename(columns={"round": "final_round"})
    )
    final = standings_df.merge(final_round, left_on=["season", "round"],
                               right_on=["season", "final_round"])
    ranked = (
        final.sort_values(["season", "points"], ascending=[True, False])
        .assign(final_position=lambda df: df.groupby("season").cumcount() + 1)
    )
    return ranked[["season", "constructor_id", "final_position"]]


def conversion_rate_summary(
    lead_df: pd.DataFrame,
    constructors: list[str] | None = None,
) -> pd.DataFrame:
    """Compute championship lead conversion rates per constructor.

    Args:
        lead_df: As returned by mid_season_leaders().
        constructors: Optional list of constructor_ids to include.
                      If None, includes all constructors with ≥ 1 mid-season lead.

    Returns:
        DataFrame with columns:
            constructor_id, constructor_name,
            seasons_led, titles_won, conversion_rate,
            seasons_list (comma-separated years where they led)
    """
    df = lead_df.copy()
    if constructors:
        df = df[df["constructor_id"].isin(constructors)]

    # Use most recent constructor_name for display (name can change across seasons)
    latest_name = (
        df.sort_values("season").groupby("constructor_id")["constructor_name"].last()
    )

    summary = (
        df.groupby("constructor_id")
        .agg(
            seasons_led=("season", "nunique"),
            titles_won=("won_title", "sum"),
            seasons_list=("season", lambda s: ", ".join(str(y) for y in sorted(s.unique()))),
        )
        .reset_index()
    )
    summary["constructor_name"] = summary["constructor_id"].map(latest_name)
    summary["conversion_rate"] = (
        summary["titles_won"] / summary["seasons_led"]
    ).round(3)

    return summary.sort_values("seasons_led", ascending=False).reset_index(drop=True)
