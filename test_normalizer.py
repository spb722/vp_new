import unittest

from features import build_seed_features
from normalizer import normalize_decomposition


class TimeWindowNormalizerTests(unittest.TestCase):
    def test_plain_days_window_is_not_completed_even_if_model_marks_true(self):
        result = {
            "original_input": "average daily revenue over the last 90 days",
            "clauses": [
                {
                    "clause_id": "1",
                    "clause_type": "time_window",
                    "text": "over the last 90 days",
                    "agg_hint": None,
                    "kpi_text": "over the last 90 days",
                    "operator_hint": None,
                    "values": [],
                    "time_n": 90,
                    "time_unit": "DAYS",
                    "is_completed_period": True,
                    "notes": "",
                }
            ],
        }

        normalized = normalize_decomposition(result)

        self.assertFalse(normalized["clauses"][0]["is_completed_period"])

    def test_explicit_completed_days_window_stays_completed(self):
        result = {
            "original_input": "last 90 completed days excluding today",
            "clauses": [
                {
                    "clause_id": "1",
                    "clause_type": "time_window",
                    "text": "last 90 completed days excluding today",
                    "agg_hint": None,
                    "kpi_text": None,
                    "operator_hint": None,
                    "values": [],
                    "time_n": 90,
                    "time_unit": "DAYS",
                    "is_completed_period": True,
                    "notes": "",
                }
            ],
        }

        normalized = normalize_decomposition(result)

        self.assertTrue(normalized["clauses"][0]["is_completed_period"])

    def test_average_daily_last_90_days_features_use_lower_only_window(self):
        result = {
            "original_input": (
                "Show the average daily revenue generated from bundled data usage "
                "by a customer over the last 90 days."
            ),
            "clauses": [
                {
                    "clause_id": "1",
                    "clause_type": "aggregation",
                    "text": "average daily revenue generated from bundled data usage by a customer",
                    "agg_hint": "AVG",
                    "kpi_text": "average daily revenue generated from bundled data usage by a customer",
                    "operator_hint": None,
                    "values": [],
                    "time_n": None,
                    "time_unit": None,
                    "is_completed_period": False,
                    "notes": "",
                },
                {
                    "clause_id": "2",
                    "clause_type": "time_window",
                    "text": "over the last 90 days",
                    "agg_hint": None,
                    "kpi_text": "over the last 90 days",
                    "operator_hint": None,
                    "values": [],
                    "time_n": 90,
                    "time_unit": "DAYS",
                    "is_completed_period": True,
                    "notes": "",
                },
            ],
        }

        features = build_seed_features(result)

        self.assertEqual(features["time_unit"], "DAYS")
        self.assertEqual(features["time_n"], 90)
        self.assertFalse(features["is_completed_period"])


if __name__ == "__main__":
    unittest.main()
