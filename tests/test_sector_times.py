import pytest
import pandas as pd
from datetime import timedelta
from src.analysis.sector_times import (
    best_sector_times,
    sector_gap,
    sector_gap_summary,
    mean_sector_gap_by_season,
)


def _make_laps(rows: list[dict]) -> pd.DataFrame:
    """Build a minimal laps DataFrame with sector time columns."""
    df = pd.DataFrame(rows)
    for col in ("Sector1Time", "Sector2Time", "Sector3Time"):
        if col in df.columns:
            df[col] = pd.to_timedelta(df[col], errors="coerce")
    return df


def _sector_laps(driver_sectors: dict[str, tuple[float, float, float]]) -> pd.DataFrame:
    """Build laps from {driver: (s1, s2, s3)} — all valid, no pit laps."""
    rows = []
    for driver, (s1, s2, s3) in driver_sectors.items():
        rows.append({
            "Driver": driver,
            "Sector1Time": timedelta(seconds=s1),
            "Sector2Time": timedelta(seconds=s2),
            "Sector3Time": timedelta(seconds=s3),
            "PitOutLap": False,
            "PitInLap": False,
        })
    return pd.DataFrame(rows)


class TestBestSectorTimes:
    def test_returns_one_row_per_driver(self):
        laps = _sector_laps({"VER": (30.0, 40.0, 20.0), "LEC": (31.0, 41.0, 21.0)})
        result = best_sector_times(laps)
        assert len(result) == 2

    def test_picks_best_sector_per_driver_across_multiple_laps(self):
        rows = [
            {"Driver": "VER", "Sector1Time": timedelta(seconds=30.0),
             "Sector2Time": timedelta(seconds=40.0), "Sector3Time": timedelta(seconds=20.0),
             "PitOutLap": False, "PitInLap": False},
            {"Driver": "VER", "Sector1Time": timedelta(seconds=28.0),
             "Sector2Time": timedelta(seconds=42.0), "Sector3Time": timedelta(seconds=19.0),
             "PitOutLap": False, "PitInLap": False},
        ]
        result = best_sector_times(pd.DataFrame(rows).assign(
            Sector1Time=lambda d: d["Sector1Time"],
            Sector2Time=lambda d: d["Sector2Time"],
            Sector3Time=lambda d: d["Sector3Time"],
        ))
        assert result.iloc[0]["best_s1_s"] == pytest.approx(28.0)
        assert result.iloc[0]["best_s2_s"] == pytest.approx(40.0)
        assert result.iloc[0]["best_s3_s"] == pytest.approx(19.0)

    def test_excludes_pit_out_laps(self):
        rows = [
            {"Driver": "VER", "Sector1Time": timedelta(seconds=25.0),
             "Sector2Time": timedelta(seconds=35.0), "Sector3Time": timedelta(seconds=15.0),
             "PitOutLap": True, "PitInLap": False},
            {"Driver": "VER", "Sector1Time": timedelta(seconds=30.0),
             "Sector2Time": timedelta(seconds=40.0), "Sector3Time": timedelta(seconds=20.0),
             "PitOutLap": False, "PitInLap": False},
        ]
        laps = pd.DataFrame(rows)
        for col in ("Sector1Time", "Sector2Time", "Sector3Time"):
            laps[col] = pd.to_timedelta(laps[col])
        result = best_sector_times(laps)
        assert result.iloc[0]["best_s1_s"] == pytest.approx(30.0)

    def test_raises_on_missing_sector_column(self):
        laps = pd.DataFrame([{"Driver": "VER", "Sector1Time": timedelta(seconds=30.0)}])
        laps["Sector1Time"] = pd.to_timedelta(laps["Sector1Time"])
        with pytest.raises(ValueError, match="Missing column"):
            best_sector_times(laps)

    def test_sorted_by_s1_ascending(self):
        laps = _sector_laps({
            "VER": (30.0, 40.0, 20.0),
            "LEC": (28.0, 41.0, 21.0),
        })
        result = best_sector_times(laps)
        assert result.iloc[0]["driver"] == "LEC"


class TestSectorGap:
    def _make_10_driver_laps(self) -> pd.DataFrame:
        drivers = {f"D{i:02d}": (30.0 + i, 40.0 + i, 20.0 + i) for i in range(10)}
        return _sector_laps(drivers)

    def test_returns_three_gaps(self):
        laps = self._make_10_driver_laps()
        result = sector_gap(laps, n=10)
        assert set(result.keys()) == {"s1_gap_s", "s2_gap_s", "s3_gap_s"}

    def test_gap_correct_for_linear_spread(self):
        # 10 drivers, each 1s apart per sector
        laps = self._make_10_driver_laps()
        result = sector_gap(laps, n=10)
        assert result["s1_gap_s"] == pytest.approx(9.0, abs=0.01)
        assert result["s2_gap_s"] == pytest.approx(9.0, abs=0.01)
        assert result["s3_gap_s"] == pytest.approx(9.0, abs=0.01)

    def test_returns_none_when_too_few_drivers(self):
        laps = _sector_laps({"VER": (30.0, 40.0, 20.0), "LEC": (31.0, 41.0, 21.0)})
        result = sector_gap(laps, n=10)
        assert result["s1_gap_s"] is None
        assert result["s2_gap_s"] is None
        assert result["s3_gap_s"] is None


class TestSectorGapSummary:
    def test_returns_correct_shape(self):
        drivers = {f"D{i:02d}": (30.0 + i, 40.0 + i, 20.0 + i) for i in range(10)}
        laps = _sector_laps(drivers)
        result = sector_gap_summary({(2022, 1): laps, (2022, 2): laps})
        assert len(result) == 2
        assert set(result.columns) == {"season", "round", "s1_gap_s", "s2_gap_s", "s3_gap_s"}

    def test_empty_on_invalid_laps(self):
        # Only 2 drivers — no gaps can be computed for n=10
        laps = _sector_laps({"VER": (30.0, 40.0, 20.0), "LEC": (31.0, 41.0, 21.0)})
        result = sector_gap_summary({(2022, 1): laps})
        assert len(result) == 0


class TestMeanSectorGapBySeason:
    def test_aggregates_across_rounds(self):
        df = pd.DataFrame([
            {"season": 2022, "round": 1, "s1_gap_s": 2.0, "s2_gap_s": 3.0, "s3_gap_s": 1.0},
            {"season": 2022, "round": 2, "s1_gap_s": 4.0, "s2_gap_s": 5.0, "s3_gap_s": 3.0},
        ])
        result = mean_sector_gap_by_season(df)
        assert len(result) == 1
        assert result.iloc[0]["mean_s1_gap_s"] == pytest.approx(3.0)
        assert result.iloc[0]["races"] == 2
