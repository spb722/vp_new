import os
import unittest

os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("LANGSMITH_TRACING", "false")

from seeds import load_seeds
from selector import score_seed, select_seed_candidates_strict


class SelectorTests(unittest.TestCase):
    def test_unknown_client_does_not_penalize_client_specific_seed(self):
        features = {
            "agg_type": "SUM",
            "time_unit": "DAYS",
            "time_n": 2,
            "time_bound_style": "lower_only",
            "is_completed_period": False,
            "has_formula": False,
            "formula_type": None,
            "is_parameterized": False,
            "needs_groupby": False,
            "has_count_constraint": False,
        }
        seed = {
            "seed_id": "client_seed",
            "client": "omantel",
            "description": "client-specific SUM day seed",
            "output_template": "SUM(KPI)",
            "selection_signature": {
                "composition": {
                    "can_be_main_condition": True,
                },
                "agg_type": "SUM",
                "formula": {
                    "has_formula": False,
                },
                "runtime": {
                    "is_parameterized": False,
                },
                "groupby": {
                    "required": False,
                },
                "time": {
                    "required": True,
                    "units": ["DAYS"],
                    "bound_style": "lower_only",
                },
                "operation": {
                    "fixed_comparisons": [],
                },
            },
        }

        result = score_seed(seed, features, client_name=None)

        self.assertIn("client_not_provided", result["reasons"])
        self.assertNotIn("client_specific_match:omantel", result["reasons"])
        self.assertFalse(
            any(warning.startswith("client_mismatch") for warning in result["warnings"])
        )

    def test_selects_generic_max_seed_for_rolling_day_window(self):
        features = {
            "original_input": "maximum local data revenue in the past 2 days",
            "agg_type": "MAX",
            "time_unit": "DAYS",
            "time_n": 2,
            "is_completed_period": False,
            "has_formula": False,
            "formula_type": None,
            "is_parameterized": False,
            "needs_groupby": False,
            "has_count_constraint": False,
            "filtered_count": None,
            "dynamic_filter_fixed_count": None,
            "product_presence": None,
            "campaign_presence": None,
            "kpi_text": "local data revenue",
        }

        candidates = select_seed_candidates_strict(
            features=features,
            seeds=load_seeds(),
            client_name=None,
            top_k=5,
        )

        self.assertTrue(candidates)
        self.assertEqual(
            candidates[0]["seed_id"],
            "S157_last_n_days_max_lower_only",
        )

    def test_selects_generic_max_seed_for_non_completed_month_window(self):
        features = {
            "original_input": "maximum data usage over the last 3 months",
            "agg_type": "MAX",
            "time_unit": "MONTHS",
            "time_n": 3,
            "is_completed_period": False,
            "month_window_style": None,
            "has_formula": False,
            "formula_type": None,
            "is_parameterized": False,
            "needs_groupby": False,
            "has_count_constraint": False,
            "filtered_count": None,
            "dynamic_filter_fixed_count": None,
            "product_presence": None,
            "campaign_presence": None,
            "kpi_text": "data usage",
        }

        candidates = select_seed_candidates_strict(
            features=features,
            seeds=load_seeds(),
            client_name=None,
            top_k=5,
        )

        self.assertTrue(candidates)
        self.assertEqual(
            candidates[0]["seed_id"],
            "S135_last_n_months_max_lower_only",
        )

    def test_selects_generic_max_seed_for_completed_month_window(self):
        features = {
            "original_input": "maximum data usage over the last 3 completed months",
            "agg_type": "MAX",
            "time_unit": "MONTHS",
            "time_n": 3,
            "is_completed_period": True,
            "month_window_style": None,
            "has_formula": False,
            "formula_type": None,
            "is_parameterized": False,
            "needs_groupby": False,
            "has_count_constraint": False,
            "filtered_count": None,
            "dynamic_filter_fixed_count": None,
            "product_presence": None,
            "campaign_presence": None,
            "kpi_text": "data usage",
        }

        candidates = select_seed_candidates_strict(
            features=features,
            seeds=load_seeds(),
            client_name=None,
            top_k=5,
        )

        self.assertTrue(candidates)
        self.assertEqual(
            candidates[0]["seed_id"],
            "S158_last_n_months_max_bounded",
        )

    def test_selects_generic_sum_seed_for_exact_month_window(self):
        features = {
            "original_input": "total prepaid SMS revenue for the last one month",
            "agg_type": "SUM",
            "time_unit": "MONTHS",
            "time_n": 1,
            "time_bound_style": "exact",
            "is_completed_period": False,
            "month_window_style": None,
            "has_formula": False,
            "formula_type": None,
            "is_parameterized": False,
            "needs_groupby": False,
            "has_count_constraint": False,
            "filtered_count": None,
            "dynamic_filter_fixed_count": None,
            "product_presence": None,
            "campaign_presence": None,
            "kpi_text": "prepaid sms revenue",
        }

        candidates = select_seed_candidates_strict(
            features=features,
            seeds=load_seeds(),
            client_name=None,
            top_k=5,
        )

        self.assertTrue(candidates)
        self.assertEqual(
            candidates[0]["seed_id"],
            "S159_last_n_months_sum_exact",
        )

    def test_selects_month_scoped_percentage_formula_seed(self):
        features = {
            "original_input": "20% of recharge amount in the last 2 months",
            "agg_type": "FORMULA",
            "time_unit": "MONTHS",
            "time_n": 2,
            "time_bound_style": "lower_only",
            "is_completed_period": False,
            "month_window_style": None,
            "has_formula": True,
            "formula_type": "percentage_of_kpi",
            "percentage_factor": 0.2,
            "is_parameterized": False,
            "needs_groupby": False,
            "has_count_constraint": False,
            "filtered_count": None,
            "dynamic_filter_fixed_count": None,
            "product_presence": None,
            "campaign_presence": None,
            "kpi_text": "recharge amount",
        }

        candidates = select_seed_candidates_strict(
            features=features,
            seeds=load_seeds(),
            client_name=None,
            top_k=5,
        )

        self.assertTrue(candidates)
        self.assertEqual(
            candidates[0]["seed_id"],
            "S160_percentage_of_kpi_formula_months_lower_only",
        )


if __name__ == "__main__":
    unittest.main()
