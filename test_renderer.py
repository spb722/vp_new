import os
import unittest

os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("LANGSMITH_TRACING", "false")

from renderer import render_seed_template


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


if __name__ == "__main__":
    unittest.main()
