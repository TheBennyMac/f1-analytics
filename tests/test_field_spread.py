import pytest
import pandas as pd
from datetime import timedelta
from src.analysis.field_spread import (
    p1_to_pn_gap_normalised,
    p11_gap_per_race,
    tail_gap_analysis,
)


def _make_laps(driver_times: dict[str, float]) -> pd.DataFrame:
    """Build a minimal laps DataFrame from {driver: lap_seconds}."""
    rows = []
    for driver, seconds in driver_times.items():
        rows.append({
            "Driver": driver,
            "LapTime": timedelta(seconds=seconds),
            "PitOutLap": False,
            "PitInLap": False,
        })
    return pd.DataFrame(rows)


def _make_15_driver_laps() -> pd.DataFrame:
    return _make_laps({f"D{i:02d}": 90.0 + i for i in range(15)})


class TestP1ToPnGapNormalised:
    def test_sufficient_field_returns_gap(self):
        result = p1_to_pn_gap_normalised({(2022, 1): _make_15_driver_laps()}, n=10)
        assert len(result) == 1
        assert result.iloc[0]["sufficient"]
        assert result.iloc[0]["gap_s"] == pytest.approx(9.0, abs=0.01)

    def test_insufficient_field_returns_none_gap_with_row(self):
        # Only 5 drivers — insufficient for n=10
        laps = _make_laps({f"D{i}": 90.0 + i for i in range(5)})
        result = p1_to_pn_gap_normalised({(2022, 1): laps}, n=10)
        assert len(result) == 1
        assert not result.iloc[0]["sufficient"]
        assert result.iloc[0]["gap_s"] is None

    def test_records_driver_count(self):
        result = p1_to_pn_gap_normalised({(2022, 1): _make_15_driver_laps()}, n=10)
        assert result.iloc[0]["drivers_with_laps"] == 15

    def test_empty_input_returns_empty(self):
        result = p1_to_pn_gap_normalised({}, n=10)
        assert result.empty

    def test_n_stored_in_output(self):
        result = p1_to_pn_gap_normalised({(2022, 1): _make_15_driver_laps()}, n=10)
        assert result.iloc[0]["n"] == 10


class TestP11GapPerRace:
    def test_returns_p10_p11_gap(self):
        laps = _make_laps({f"D{i:02d}": 90.0 + i for i in range(15)})
        result = p11_gap_per_race({(2022, 1): laps})
        assert len(result) == 1
        assert result.iloc[0]["p10_p11_gap_s"] == pytest.approx(1.0, abs=0.01)

    def test_returns_p1_p11_gap(self):
        laps = _make_laps({f"D{i:02d}": 90.0 + i for i in range(15)})
        result = p11_gap_per_race({(2022, 1): laps})
        assert result.iloc[0]["p1_p11_gap_s"] == pytest.approx(10.0, abs=0.01)

    def test_excludes_races_with_fewer_than_11_drivers(self):
        laps = _make_laps({f"D{i}": 90.0 + i for i in range(8)})
        result = p11_gap_per_race({(2022, 1): laps})
        assert result.empty

    def test_multiple_rounds_aggregated(self):
        laps = _make_laps({f"D{i:02d}": 90.0 + i for i in range(15)})
        result = p11_gap_per_race({(2022, 1): laps, (2022, 2): laps})
        assert len(result) == 2


class TestTailGapAnalysis:
    def test_tail_to_p1_gap(self):
        # 15 drivers, 1s apart: tail gap to P1 = 14s
        result = tail_gap_analysis({(2022, 1): _make_15_driver_laps()})
        assert result.iloc[0]["tail_to_p1_gap_s"] == pytest.approx(14.0, abs=0.01)

    def test_tail_to_p10_gap(self):
        # 15 drivers (D00=90s ... D14=104s): P10=D09=99s, tail=D14=104s, gap=5s
        result = tail_gap_analysis({(2022, 1): _make_15_driver_laps()})
        assert result.iloc[0]["tail_to_p10_gap_s"] == pytest.approx(5.0, abs=0.01)

    def test_p10_none_when_fewer_than_10_drivers(self):
        laps = _make_laps({f"D{i}": 90.0 + i for i in range(5)})
        result = tail_gap_analysis({(2022, 1): laps})
        assert result.iloc[0]["p10_lap_s"] is None
        assert result.iloc[0]["tail_to_p10_gap_s"] is None

    def test_excludes_races_with_fewer_than_2_drivers(self):
        laps = _make_laps({"VER": 90.0})
        result = tail_gap_analysis({(2022, 1): laps})
        assert result.empty

    def test_records_driver_count(self):
        result = tail_gap_analysis({(2022, 1): _make_15_driver_laps()})
        assert result.iloc[0]["drivers_with_laps"] == 15
