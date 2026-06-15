import os
import unittest

os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("LANGSMITH_TRACING", "false")

from seeds import load_seeds
from selector import select_seed_candidates_strict


class SelectorTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
