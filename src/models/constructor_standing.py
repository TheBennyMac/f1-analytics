from dataclasses import dataclass


@dataclass
class ConstructorStanding:
    """Constructor championship standing at a point in a season."""

    season: int
    round: int  # Standing after this round
    position: int
    constructor_id: str
    constructor_name: str
    points: float
    wins: int
