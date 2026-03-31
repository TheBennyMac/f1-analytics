import pytest
import pandas as pd
from src.analysis.reliability import is_dnf, dnf_rate_by_constructor_year, dnf_causes


class TestIsDnf:
    def test_finished_is_not_dnf(self):
        assert is_dnf("Finished") is False

    def test_lapped_finisher_is_not_dnf(self):
        assert is_dnf("+1 Lap") is False
        assert is_dnf("+2 Laps") is False

    def test_engine_failure_is_dnf(self):
        assert is_dnf("Engine") is True

    def test_accident_is_dnf(self):
        assert is_dnf("Accident") is True

    def test_dsq_is_dnf(self):
        assert is_dnf("Disqualified") is True

    def test_mechanical_is_dnf(self):
        assert is_dnf("Mechanical") is True


class TestDnfRateByConstructorYear:
    def _make_results(self):
        return pd.DataFrame([
            {"season": 2022, "constructor_id": "red_bull", "constructor_name": "Red Bull", "status": "Finished"},
            {"season": 2022, "constructor_id": "red_bull", "constructor_name": "Red Bull", "status": "Finished"},
            {"season": 2022, "constructor_id": "red_bull", "constructor_name": "Red Bull", "status": "Engine"},
            {"season": 2022, "constructor_id": "ferrari", "constructor_name": "Ferrari", "status": "Finished"},
            {"season": 2022, "constructor_id": "ferrari", "constructor_name": "Ferrari", "status": "Accident"},
            {"season": 2023, "constructor_id": "red_bull", "constructor_name": "Red Bull", "status": "Finished"},
            {"season": 2023, "constructor_id": "red_bull", "constructor_name": "Red Bull", "status": "Finished"},
        ])

    def test_dnf_rate_calculated_correctly(self):
        result = dnf_rate_by_constructor_year(self._make_results())
        rb_2022 = result[(result["season"] == 2022) & (result["constructor_id"] == "red_bull")]
        assert rb_2022.iloc[0]["starts"] == 3
        assert rb_2022.iloc[0]["dnfs"] == 1
        assert rb_2022.iloc[0]["dnf_rate_pct"] == pytest.approx(33.3, abs=0.1)

    def test_zero_dnf_rate(self):
        result = dnf_rate_by_constructor_year(self._make_results())
        rb_2023 = result[(result["season"] == 2023) & (result["constructor_id"] == "red_bull")]
        assert rb_2023.iloc[0]["dnf_rate_pct"] == 0.0

    def test_columns_present(self):
        result = dnf_rate_by_constructor_year(self._make_results())
        assert {"season", "constructor_id", "starts", "dnfs", "dnf_rate_pct"}.issubset(result.columns)


class TestDnfCauses:
    def test_only_dnf_statuses_returned(self):
        df = pd.DataFrame([
            {"season": 2022, "status": "Finished"},
            {"season": 2022, "status": "Engine"},
            {"season": 2022, "status": "Engine"},
            {"season": 2022, "status": "Accident"},
        ])
        result = dnf_causes(df)
        assert "Finished" not in result["status"].values
        assert result[result["status"] == "Engine"].iloc[0]["count"] == 2
