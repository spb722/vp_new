import os
import unittest
from unittest.mock import patch

os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("LANGSMITH_TRACING", "false")

from renderer import render_attribute_filter, render_duration_threshold, render_seed_template


class RendererDateColumnTests(unittest.TestCase):
    def setUp(self):
        self.seed = {
            "output_template": (
                "{date_col} >= CurrentMonth-{N}MONTHS "
                "AND SUM({kpi_col}) ${operator} ${value}"
            )
        }
        self.features = {
            "time_n": 1,
            "campaign_presence": None,
            "product_presence": None,
            "filtered_count": None,
            "dynamic_filter_fixed_count": None,
            "groupby_text": None,
            "formula_type": None,
            "percentage_factor": None,
        }

    def test_non_empty_date_column_overrides_inferred_date_col(self):
        rendered = render_seed_template(
            self.seed,
            self.features,
            {
                "kpi_col": "Total_Data_Revenue",
                "table_name": "Common_Seg_Fct",
                "date_column": "COMMON_FCT_DT",
            },
        )

        self.assertEqual(
            rendered,
            "COMMON_FCT_DT >= CurrentMonth-1MONTHS "
            "AND SUM(Total_Data_Revenue) ${operator} ${value}",
        )

    def test_missing_date_column_falls_back_to_inferred_date_col(self):
        rendered = render_seed_template(
            self.seed,
            self.features,
            {
                "kpi_col": "Total_Data_Revenue",
                "table_name": "Common_Seg_Fct",
            },
        )

        self.assertEqual(
            rendered,
            "COMMON_Event_Date >= CurrentMonth-1MONTHS "
            "AND SUM(Total_Data_Revenue) ${operator} ${value}",
        )

    def test_blank_date_column_falls_back_to_inferred_date_col(self):
        rendered = render_seed_template(
            self.seed,
            self.features,
            {
                "kpi_col": "Total_Data_Revenue",
                "table_name": "Common_Seg_Fct",
                "date_column": "  ",
            },
        )

        self.assertEqual(
            rendered,
            "COMMON_Event_Date >= CurrentMonth-1MONTHS "
            "AND SUM(Total_Data_Revenue) ${operator} ${value}",
        )


class RendererFallbackTests(unittest.TestCase):
    @patch("renderer.resolve_condition_from_api", side_effect=Exception("VP_verify 500"))
    def test_duration_threshold_falls_back_when_vp_verify_errors(self, _mock_resolve):
        rendered = render_duration_threshold(
            {
                "text": "more than 35 days",
                "operator_hint": ">",
                "time_n": 35,
                "time_unit": "DAYS",
            }
        )

        self.assertEqual(rendered, "AON > 35")

    @patch("renderer.resolve_condition_from_api", side_effect=Exception("VP_verify 500"))
    def test_attribute_filter_falls_back_when_vp_verify_errors(self, _mock_resolve):
        rendered = render_attribute_filter(
            {
                "text": "smartphone users",
                "operator_hint": "=",
                "values": ["smartphone"],
            }
        )

        self.assertEqual(rendered, "Profile_Cdr_Handset_Type = smartphone")


if __name__ == "__main__":
    unittest.main()
