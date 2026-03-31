from dataclasses import dataclass
from typing import Optional


@dataclass
class RaceResult:
    """Result for a single driver in a single race."""

    season: int
    round: int
    race_name: str
    driver_id: str
    driver_name: str
    constructor_id: str
    constructor_name: str
    grid_position: int
    finish_position: Optional[int]  # None if DNF/DSQ
    points: float
    status: str  # 'Finished', 'DNF', 'DSQ', etc.
    fastest_lap: bool
    laps_completed: int

    @property
    def classified_finish(self) -> bool:
        """True if the driver was classified as a finisher."""
        return self.finish_position is not None

    @property
    def dnf(self) -> bool:
        return self.status not in ("Finished", "+1 Lap", "+2 Laps")
