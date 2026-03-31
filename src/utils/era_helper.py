from dataclasses import dataclass


@dataclass(frozen=True)
class EraInfo:
    name: str
    year_within_era: int  # 1 = regulation reset year


# Era boundaries: (start_year, end_year inclusive, era_name)
_ERA_BOUNDARIES: list[tuple[int, int, str]] = [
    (1994, 2009, "Refuelling Era"),
    (2010, 2013, "KERS/DRS Era"),
    (2014, 2021, "Hybrid Power Unit Era"),
    (2022, 2025, "Ground Effect Era"),
    (2026, 9999, "2026 Era"),
]


def get_era_info(year: int) -> EraInfo:
    """Return the era name and year-within-era for a given calendar year.

    Year-within-era is 1-indexed: the regulation reset year is always Year 1.

    Raises ValueError for years before 1994.
    """
    if year < 1994:
        raise ValueError(f"Year {year} is before the supported era range (1994+).")

    for start, end, name in _ERA_BOUNDARIES:
        if start <= year <= end:
            return EraInfo(name=name, year_within_era=year - start + 1)

    raise ValueError(f"Year {year} does not fall within any defined era.")


def get_era_name(year: int) -> str:
    """Return just the era name for a given year."""
    return get_era_info(year).name


def get_year_within_era(year: int) -> int:
    """Return the year-within-era (1 = regulation reset year) for a given year."""
    return get_era_info(year).year_within_era
