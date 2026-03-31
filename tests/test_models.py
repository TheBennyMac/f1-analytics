import pytest
from src.models import RaceResult, LapSummary, DriverStanding, ConstructorStanding


class TestRaceResult:
    def _make(self, **kwargs) -> RaceResult:
        defaults = dict(
            season=2022, round=1, race_name="Bahrain Grand Prix",
            driver_id="VER", driver_name="Max Verstappen",
            constructor_id="red_bull", constructor_name="Red Bull Racing",
            grid_position=1, finish_position=1, points=25.0,
            status="Finished", fastest_lap=False, laps_completed=57,
        )
        defaults.update(kwargs)
        return RaceResult(**defaults)

    def test_classified_finish_when_position_set(self):
        assert self._make(finish_position=1).classified_finish is True

    def test_classified_finish_false_when_no_position(self):
        assert self._make(finish_position=None).classified_finish is False

    def test_dnf_false_for_finisher(self):
        assert self._make(status="Finished").dnf is False

    def test_dnf_true_for_retirement(self):
        assert self._make(status="Engine").dnf is True

    def test_dnf_false_for_lapped_finisher(self):
        assert self._make(status="+1 Lap").dnf is False


class TestLapSummary:
    def _make(self, **kwargs) -> LapSummary:
        defaults = dict(
            season=2022, round=1, session_type="R",
            driver_id="VER", driver_name="Max Verstappen",
            constructor_id="red_bull",
            fastest_lap_time_s=95.5, median_lap_time_s=96.2,
            total_laps=57, pit_stops=2, tyre_compounds_used=["SOFT", "MEDIUM"],
        )
        defaults.update(kwargs)
        return LapSummary(**defaults)

    def test_has_valid_lap_when_time_set(self):
        assert self._make(fastest_lap_time_s=95.5).has_valid_lap is True

    def test_has_valid_lap_false_when_no_time(self):
        assert self._make(fastest_lap_time_s=None).has_valid_lap is False


class TestDriverStanding:
    def test_instantiation(self):
        standing = DriverStanding(
            season=2022, round=5, position=1,
            driver_id="VER", driver_name="Max Verstappen",
            constructor_id="red_bull", constructor_name="Red Bull Racing",
            points=110.0, wins=3,
        )
        assert standing.position == 1
        assert standing.points == 110.0


class TestConstructorStanding:
    def test_instantiation(self):
        standing = ConstructorStanding(
            season=2022, round=5, position=1,
            constructor_id="red_bull", constructor_name="Red Bull Racing",
            points=165.0, wins=4,
        )
        assert standing.position == 1
        assert standing.wins == 4
