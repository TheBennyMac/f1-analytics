from dataclasses import dataclass
from typing import Optional


@dataclass
class LapSummary:
    """Aggregated lap data for a single driver in a single session."""

    season: int
    round: int
    session_type: str  # 'R', 'Q', 'FP1', etc.
    driver_id: str
    driver_name: str
    constructor_id: str
    fastest_lap_time_s: Optional[float]  # Fastest lap in seconds; None if no clean lap
    median_lap_time_s: Optional[float]
    total_laps: int
    pit_stops: int
    tyre_compounds_used: list[str]

    @property
    def has_valid_lap(self) -> bool:
        return self.fastest_lap_time_s is not None
