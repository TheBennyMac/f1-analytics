from dataclasses import dataclass


@dataclass
class DriverStanding:
    """Driver championship standing at a point in a season."""

    season: int
    round: int  # Standing after this round
    position: int
    driver_id: str
    driver_name: str
    constructor_id: str
    constructor_name: str
    points: float
    wins: int
