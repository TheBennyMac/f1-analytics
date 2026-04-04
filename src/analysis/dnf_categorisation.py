"""
DNF cause categorisation — groups FastF1 status values into four categories.

Categories:
  Mechanical    — direct car failure (engine, gearbox, hydraulics, etc.)
  Collision     — crash, contact, driver error, bodywork damage
  Administrative — regulatory, pre-race, or disciplinary (DSQ, DNS, withdrew)
  Unknown       — generic 'Retired' with no cause; excluded from % breakdowns

Usage pattern:
  Apply is_dnf() first (from reliability.py) to filter to DNF rows only,
  then use categorise_dnf() on the status column.
"""

import pandas as pd
from src.utils.era_helper import get_year_within_era, get_era_name


# --- Category lookup tables ---------------------------------------------------

_MECHANICAL: set[str] = {
    "Engine", "Gearbox", "Hydraulics", "Power Unit", "Electrical",
    "Brakes", "Suspension", "Transmission", "Overheating",
    "Oil leak", "Oil pressure", "Water leak", "Water pressure",
    "Fuel leak", "Fuel pressure", "Fuel system", "Turbo",
    "Throttle", "Clutch", "Mechanical", "Technical",
    "Electronics", "Steering", "ERS", "MGU-H", "MGU-K",
    "Battery", "Exhaust", "Driveshaft", "Vibrations",
    "Wheel", "Tyre", "Puncture", "Alternator", "Pneumatics",
    "Fire", "Differential", "Cooling system", "Damage",
    "Radiator", "Exhaust pipe",
}

_COLLISION: set[str] = {
    "Accident", "Collision", "Collision damage", "Spun off",
}

_ADMINISTRATIVE: set[str] = {
    "Disqualified", "Did not start", "Did not qualify",
    "Withdrew", "Safety concerns", "Excluded",
}

_UNKNOWN: set[str] = {
    "Retired",
}

# Category label constants
MECHANICAL = "Mechanical"
COLLISION = "Collision"
ADMINISTRATIVE = "Administrative"
UNKNOWN = "Unknown"


# --- Core function ------------------------------------------------------------

def categorise_dnf(status: str) -> str:
    """Map a DNF status string to one of four category labels.

    Args:
        status: A FastF1 result status string that represents a DNF
                (i.e. is_dnf(status) is True).

    Returns:
        One of: 'Mechanical', 'Collision', 'Administrative', 'Unknown'.
        Unrecognised statuses return 'Unknown'.
    """
    if status in _MECHANICAL:
        return MECHANICAL
    if status in _COLLISION:
        return COLLISION
    if status in _ADMINISTRATIVE:
        return ADMINISTRATIVE
    return UNKNOWN


# --- Aggregation functions ----------------------------------------------------

def dnf_category_counts(
    results_df: pd.DataFrame,
    group_by: list[str] | None = None,
) -> pd.DataFrame:
    """Count DNFs by category, optionally grouped.

    Expects results_df to contain only DNF rows (pre-filtered with is_dnf).

    Args:
        results_df: DataFrame with at least a 'status' column and any
                    grouping columns (e.g. 'season', 'era_year').
        group_by:   Optional list of column names to group by before counting.
                    If None, returns totals across the whole dataset.

    Returns:
        DataFrame with columns [*group_by, 'category', 'count'].
        Sorted by group columns then count descending.
    """
    df = results_df.copy()
    df["category"] = df["status"].apply(categorise_dnf)

    if group_by:
        counts = (
            df.groupby(group_by + ["category"])
            .size()
            .reset_index(name="count")
        )
        return counts.sort_values(group_by + ["count"], ascending=[True] * len(group_by) + [False]).reset_index(drop=True)
    else:
        counts = df["category"].value_counts().reset_index()
        counts.columns = ["category", "count"]
        return counts


def mechanical_share_by_era_year(results_df: pd.DataFrame) -> pd.DataFrame:
    """Mechanical DNF share (%) by year-within-era, excluding Unknown.

    Tests the narrative: 'regulation reset years skew more mechanical than
    settled era years'. Administrative DNFs are excluded as they do not
    reflect car reliability. Unknown ('Retired') DNFs are also excluded
    from the denominator as they have no attributable cause.

    Args:
        results_df: DataFrame with columns [season, status].
                    Must contain only DNF rows (pre-filtered with is_dnf).

    Returns:
        DataFrame with columns [era_name, era_year, mechanical, collision,
                                 total_attributed, mechanical_pct].
        Sorted by era_name, era_year ascending.
    """
    df = results_df.copy()
    df["category"] = df["status"].apply(categorise_dnf)
    df["era_year"] = df["season"].apply(get_year_within_era)
    df["era_name"] = df["season"].apply(get_era_name)

    # Exclude Administrative and Unknown from the attributed denominator
    attributed = df[df["category"].isin([MECHANICAL, COLLISION])]

    grouped = attributed.groupby(["era_name", "era_year", "category"]).size().unstack(fill_value=0)

    # Ensure both columns exist even if one category has zero entries
    for col in [MECHANICAL, COLLISION]:
        if col not in grouped.columns:
            grouped[col] = 0

    grouped = grouped.reset_index()
    grouped["total_attributed"] = grouped[MECHANICAL] + grouped[COLLISION]
    grouped["mechanical_pct"] = (
        grouped[MECHANICAL] / grouped["total_attributed"] * 100
    ).round(1)

    return grouped.sort_values(["era_name", "era_year"]).reset_index(drop=True)
