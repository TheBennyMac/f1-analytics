import pytest
import pandas as pd
from src.analysis.dnf_categorisation import (
    categorise_dnf,
    dnf_category_counts,
    mechanical_share_by_era_year,
    MECHANICAL, COLLISION, ADMINISTRATIVE, UNKNOWN,
)


class TestCategorizeDnf:
    def test_engine_is_mechanical(self):
        assert categorise_dnf("Engine") == MECHANICAL

    def test_gearbox_is_mechanical(self):
        assert categorise_dnf("Gearbox") == MECHANICAL

    def test_hydraulics_is_mechanical(self):
        assert categorise_dnf("Hydraulics") == MECHANICAL

    def test_power_unit_is_mechanical(self):
        assert categorise_dnf("Power Unit") == MECHANICAL

    def test_brakes_is_mechanical(self):
        assert categorise_dnf("Brakes") == MECHANICAL

    def test_accident_is_collision(self):
        assert categorise_dnf("Accident") == COLLISION

    def test_collision_is_collision(self):
        assert categorise_dnf("Collision") == COLLISION

    def test_collision_damage_is_collision(self):
        assert categorise_dnf("Collision damage") == COLLISION

    def test_spun_off_is_collision(self):
        assert categorise_dnf("Spun off") == COLLISION

    def test_disqualified_is_administrative(self):
        assert categorise_dnf("Disqualified") == ADMINISTRATIVE

    def test_did_not_start_is_administrative(self):
        assert categorise_dnf("Did not start") == ADMINISTRATIVE

    def test_withdrew_is_administrative(self):
        assert categorise_dnf("Withdrew") == ADMINISTRATIVE

    def test_retired_is_unknown(self):
        assert categorise_dnf("Retired") == UNKNOWN

    def test_unrecognised_status_is_unknown(self):
        assert categorise_dnf("Some weird status") == UNKNOWN


class TestDnfCategoryCounts:
    def _make_dnf_df(self):
        return pd.DataFrame([
            {"season": 2022, "status": "Engine"},
            {"season": 2022, "status": "Engine"},
            {"season": 2022, "status": "Accident"},
            {"season": 2022, "status": "Retired"},
            {"season": 2023, "status": "Gearbox"},
            {"season": 2023, "status": "Collision"},
            {"season": 2023, "status": "Disqualified"},
        ])

    def test_total_counts_no_grouping(self):
        result = dnf_category_counts(self._make_dnf_df())
        mechanical_row = result[result["category"] == MECHANICAL]
        assert mechanical_row.iloc[0]["count"] == 3

    def test_grouped_by_season(self):
        result = dnf_category_counts(self._make_dnf_df(), group_by=["season"])
        row = result[(result["season"] == 2022) & (result["category"] == MECHANICAL)]
        assert row.iloc[0]["count"] == 2

    def test_columns_present_no_grouping(self):
        result = dnf_category_counts(self._make_dnf_df())
        assert set(result.columns) == {"category", "count"}

    def test_columns_present_with_grouping(self):
        result = dnf_category_counts(self._make_dnf_df(), group_by=["season"])
        assert {"season", "category", "count"}.issubset(result.columns)

    def test_all_four_categories_can_appear(self):
        result = dnf_category_counts(self._make_dnf_df())
        categories = set(result["category"].values)
        assert categories == {MECHANICAL, COLLISION, ADMINISTRATIVE, UNKNOWN}


class TestMechanicalShareByEraYear:
    def _make_dnf_df(self):
        # 2022 = Ground Effect Era Year 1, 2023 = Year 2
        return pd.DataFrame([
            # 2022: 3 mechanical, 1 collision, 1 administrative, 1 unknown
            {"season": 2022, "status": "Engine"},
            {"season": 2022, "status": "Gearbox"},
            {"season": 2022, "status": "Hydraulics"},
            {"season": 2022, "status": "Accident"},
            {"season": 2022, "status": "Disqualified"},
            {"season": 2022, "status": "Retired"},
            # 2023: 1 mechanical, 3 collision
            {"season": 2023, "status": "Engine"},
            {"season": 2023, "status": "Collision"},
            {"season": 2023, "status": "Collision"},
            {"season": 2023, "status": "Accident"},
        ])

    def test_mechanical_pct_excludes_administrative_and_unknown(self):
        result = mechanical_share_by_era_year(self._make_dnf_df())
        year1 = result[result["era_year"] == 1].iloc[0]
        # 3 mechanical, 1 collision → total attributed = 4 → 75%
        assert year1["total_attributed"] == 4
        assert year1["mechanical_pct"] == pytest.approx(75.0)

    def test_year2_lower_mechanical_share(self):
        result = mechanical_share_by_era_year(self._make_dnf_df())
        year2 = result[result["era_year"] == 2].iloc[0]
        # 1 mechanical, 3 collision → 25%
        assert year2["mechanical_pct"] == pytest.approx(25.0)

    def test_era_name_and_year_columns_present(self):
        result = mechanical_share_by_era_year(self._make_dnf_df())
        assert {"era_name", "era_year", MECHANICAL, COLLISION,
                "total_attributed", "mechanical_pct"}.issubset(result.columns)

    def test_sorted_by_era_name_then_year(self):
        result = mechanical_share_by_era_year(self._make_dnf_df())
        years = result["era_year"].tolist()
        assert years == sorted(years)
