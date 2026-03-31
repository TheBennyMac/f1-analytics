import pytest
from src.utils.era_helper import get_era_info, get_era_name, get_year_within_era, EraInfo


class TestGetEraInfo:
    def test_ground_effect_era_year1(self):
        info = get_era_info(2022)
        assert info.name == "Ground Effect Era"
        assert info.year_within_era == 1

    def test_ground_effect_era_year4(self):
        info = get_era_info(2025)
        assert info.name == "Ground Effect Era"
        assert info.year_within_era == 4

    def test_2026_era_year1(self):
        info = get_era_info(2026)
        assert info.name == "2026 Era"
        assert info.year_within_era == 1

    def test_hybrid_era_year1(self):
        info = get_era_info(2014)
        assert info.name == "Hybrid Power Unit Era"
        assert info.year_within_era == 1

    def test_hybrid_era_last_year(self):
        info = get_era_info(2021)
        assert info.name == "Hybrid Power Unit Era"
        assert info.year_within_era == 8

    def test_kers_drs_era(self):
        info = get_era_info(2011)
        assert info.name == "KERS/DRS Era"
        assert info.year_within_era == 2

    def test_refuelling_era_year1(self):
        info = get_era_info(1994)
        assert info.name == "Refuelling Era"
        assert info.year_within_era == 1

    def test_year_before_supported_range_raises(self):
        with pytest.raises(ValueError, match="1993"):
            get_era_info(1993)

    def test_returns_era_info_dataclass(self):
        assert isinstance(get_era_info(2022), EraInfo)


class TestGetEraName:
    def test_returns_string(self):
        assert get_era_name(2024) == "Ground Effect Era"


class TestGetYearWithinEra:
    def test_returns_int(self):
        assert get_year_within_era(2023) == 2

    def test_2026_is_year_1(self):
        assert get_year_within_era(2026) == 1
