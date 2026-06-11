import os
import unittest
from unittest.mock import patch

from features import build_seed_features, extract_formula_kpi_text

os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("LANGSMITH_TRACING", "false")


class FormulaFeatureTests(unittest.TestCase):
    def test_extract_formula_kpi_text_from_percentage_formula(self):
        self.assertEqual(
            extract_formula_kpi_text(
                "20% of their recharge amount greater than the specified threshold"
            ),
            "recharge amount",
        )

    def test_extract_formula_kpi_text_is_metric_agnostic(self):
        self.assertEqual(
            extract_formula_kpi_text(
                "15 percent of total roaming revenue is less than the selected value"
            ),
            "total roaming revenue",
        )

    def test_build_seed_features_recovers_missing_formula_kpi_text(self):
        result = {
            "original_input": (
                "Which customers have 20% of their recharge amount greater than "
                "the specified threshold?"
            ),
            "clauses": [
                {
                    "clause_id": "formula",
                    "clause_type": "formula",
                    "text": "20% of their recharge amount greater than the specified threshold",
                    "agg_hint": "FORMULA",
                    "kpi_text": None,
                    "operator_hint": None,
                    "values": [],
                    "time_n": None,
                    "time_unit": None,
                    "is_completed_period": None,
                    "notes": "",
                }
            ],
        }

        features = build_seed_features(result)

        self.assertEqual(features["agg_type"], "FORMULA")
        self.assertEqual(features["formula_type"], "percentage_of_kpi")
        self.assertEqual(features["percentage_factor"], 0.2)
        self.assertEqual(features["kpi_text"], "recharge amount")
        self.assertEqual(features["attribute_filters"], [])

    def test_percentage_formula_condition_dominates_unconditional_aggregation(self):
        result = {
            "original_input": (
                "Get customers with a recharge amount where 20% of the value "
                "exceeds the given threshold."
            ),
            "clauses": [
                {
                    "clause_id": "clause_1",
                    "clause_type": "aggregation",
                    "text": "recharge amount",
                    "agg_hint": "SUM",
                    "kpi_text": "recharge amount",
                    "operator_hint": None,
                    "values": [],
                    "time_n": None,
                    "time_unit": None,
                    "is_completed_period": None,
                    "notes": "",
                },
                {
                    "clause_id": "clause_2",
                    "clause_type": "formula",
                    "text": "20% of the value exceeds the given threshold",
                    "agg_hint": "FORMULA",
                    "kpi_text": "recharge amount",
                    "operator_hint": ">",
                    "values": [],
                    "time_n": None,
                    "time_unit": None,
                    "is_completed_period": None,
                    "notes": "",
                },
            ],
        }

        features = build_seed_features(result)

        self.assertEqual(features["agg_type"], "FORMULA")
        self.assertEqual(features["formula_type"], "percentage_of_kpi")
        self.assertEqual(features["percentage_factor"], 0.2)
        self.assertEqual(features["kpi_text"], "recharge amount")

    def test_generic_subject_attribute_filter_is_removed(self):
        result = {
            "original_input": (
                "Which customers have 20% of their recharge amount greater than "
                "the specified threshold?"
            ),
            "clauses": [
                {
                    "clause_id": "1",
                    "clause_type": "formula",
                    "text": "20% of recharge amount greater than the specified threshold",
                    "agg_hint": "FORMULA",
                    "kpi_text": "recharge amount",
                    "operator_hint": ">",
                    "values": [],
                    "time_n": None,
                    "time_unit": None,
                    "is_completed_period": None,
                    "notes": "",
                },
                {
                    "clause_id": "2",
                    "clause_type": "attribute_filter",
                    "text": "customers",
                    "agg_hint": None,
                    "kpi_text": None,
                    "operator_hint": None,
                    "values": [],
                    "time_n": None,
                    "time_unit": None,
                    "is_completed_period": None,
                    "notes": "",
                },
            ],
        }

        features = build_seed_features(result)

        self.assertEqual(features["agg_type"], "FORMULA")
        self.assertEqual(features["kpi_text"], "recharge amount")
        self.assertEqual(features["attribute_filters"], [])

    def test_dynamic_empty_filter_is_preserved(self):
        result = {
            "original_input": "Customers who bought any product more than three times in a month",
            "clauses": [
                {
                    "clause_id": "1",
                    "clause_type": "time_window",
                    "text": "in a month",
                    "agg_hint": None,
                    "kpi_text": None,
                    "operator_hint": None,
                    "values": [],
                    "time_n": 1,
                    "time_unit": "MONTHS",
                    "is_completed_period": False,
                    "notes": "",
                },
                {
                    "clause_id": "2",
                    "clause_type": "attribute_filter",
                    "text": "any product",
                    "agg_hint": None,
                    "kpi_text": None,
                    "operator_hint": None,
                    "values": [],
                    "time_n": None,
                    "time_unit": None,
                    "is_completed_period": None,
                    "notes": "",
                },
                {
                    "clause_id": "3",
                    "clause_type": "count_constraint",
                    "text": "more than three times",
                    "agg_hint": None,
                    "kpi_text": None,
                    "operator_hint": ">",
                    "values": ["product", "3"],
                    "time_n": None,
                    "time_unit": None,
                    "is_completed_period": None,
                    "notes": "",
                },
            ],
        }

        features = build_seed_features(result)

        self.assertEqual(features["attribute_filters"], [])
        self.assertIsNotNone(features["dynamic_filter_fixed_count"])
        self.assertEqual(
            features["dynamic_filter_fixed_count"]["entity_text"],
            "any product",
        )

    def test_product_presence_exact_month_uses_month_seed(self):
        result = {
            "original_input": (
                "List customers who purchased either product 123 or product 125 "
                "in the past month."
            ),
            "clauses": [
                {
                    "clause_id": "1",
                    "clause_type": "attribute_filter",
                    "text": "product 123 or product 125",
                    "agg_hint": None,
                    "kpi_text": None,
                    "operator_hint": "IN_LIST",
                    "values": ["123", "125"],
                    "time_n": None,
                    "time_unit": None,
                    "is_completed_period": None,
                    "notes": "",
                },
                {
                    "clause_id": "2",
                    "clause_type": "time_window",
                    "text": "in the past month",
                    "agg_hint": None,
                    "kpi_text": None,
                    "operator_hint": None,
                    "values": [],
                    "time_n": 1,
                    "time_unit": "MONTHS",
                    "is_completed_period": False,
                    "notes": "",
                },
            ],
        }

        with patch(
            "features.classify_month_window_for_features",
            return_value={
                "has_month_window": True,
                "style": "exact",
                "time_n": 1,
                "confidence": "high",
                "reason": "pinned previous month",
            },
        ):
            features = build_seed_features(result)

        self.assertEqual(features["agg_type"], "COUNT_ALL")
        self.assertEqual(features["kpi_text"], "product id")
        self.assertEqual(features["time_unit"], "MONTHS")
        self.assertEqual(features["time_n"], 1)
        self.assertEqual(features["month_window_style"], "exact")
        self.assertEqual(
            features["product_presence"],
            {"product_ids": ["123", "125"], "presence_direction": "present"},
        )

        from seeds import load_seeds
        from selector import choose_seed_or_report_ambiguity, select_seed_candidates_strict

        candidates = select_seed_candidates_strict(
            features,
            load_seeds(),
            client_name=None,
            top_k=3,
        )
        decision = choose_seed_or_report_ambiguity(candidates, client_name=None)

        self.assertEqual(decision["status"], "MATCH_FOUND")
        self.assertEqual(
            decision["selected_seed"]["seed_id"],
            "S153_product_presence_month_exact",
        )

    def test_product_presence_month_classifier_runs_when_time_unit_missing(self):
        result = {
            "original_input": (
                "List customers who purchased either product 123 or product 125 "
                "in the past month."
            ),
            "clauses": [
                {
                    "clause_id": "1",
                    "clause_type": "aggregation",
                    "text": "List customers",
                    "agg_hint": "COUNT_ALL",
                    "kpi_text": "customers",
                    "operator_hint": None,
                    "values": [],
                    "time_n": None,
                    "time_unit": None,
                    "is_completed_period": False,
                    "notes": "",
                },
                {
                    "clause_id": "2",
                    "clause_type": "attribute_filter",
                    "text": "product 123 or product 125",
                    "agg_hint": None,
                    "kpi_text": None,
                    "operator_hint": "IN_LIST",
                    "values": ["123", "125"],
                    "time_n": None,
                    "time_unit": None,
                    "is_completed_period": False,
                    "notes": "",
                },
                {
                    "clause_id": "3",
                    "clause_type": "time_window",
                    "text": "in the past month",
                    "agg_hint": None,
                    "kpi_text": None,
                    "operator_hint": None,
                    "values": [],
                    "time_n": None,
                    "time_unit": None,
                    "is_completed_period": False,
                    "notes": "",
                },
            ],
        }

        with patch(
            "features.classify_month_window_for_features",
            return_value={
                "has_month_window": True,
                "style": "exact",
                "time_n": 1,
                "confidence": "high",
                "reason": "pinned previous month",
            },
        ) as classifier:
            features = build_seed_features(result)

        classifier.assert_called_once()
        self.assertEqual(features["time_unit"], "MONTHS")
        self.assertEqual(features["time_n"], 1)
        self.assertEqual(features["month_window_style"], "exact")

        from seeds import load_seeds
        from selector import choose_seed_or_report_ambiguity, select_seed_candidates_strict

        candidates = select_seed_candidates_strict(
            features,
            load_seeds(),
            client_name=None,
            top_k=3,
        )
        decision = choose_seed_or_report_ambiguity(candidates, client_name=None)

        self.assertEqual(decision["status"], "MATCH_FOUND")
        self.assertEqual(
            decision["selected_seed"]["seed_id"],
            "S153_product_presence_month_exact",
        )

    def test_product_presence_bounded_month_uses_bounded_seed(self):
        result = {
            "original_input": (
                "Find customers who purchased product 123 across the last 3 months."
            ),
            "clauses": [
                {
                    "clause_id": "1",
                    "clause_type": "attribute_filter",
                    "text": "product 123",
                    "agg_hint": None,
                    "kpi_text": None,
                    "operator_hint": "=",
                    "values": ["123"],
                    "time_n": None,
                    "time_unit": None,
                    "is_completed_period": None,
                    "notes": "",
                },
                {
                    "clause_id": "2",
                    "clause_type": "time_window",
                    "text": "across the last 3 months",
                    "agg_hint": None,
                    "kpi_text": None,
                    "operator_hint": None,
                    "values": [],
                    "time_n": 3,
                    "time_unit": "MONTHS",
                    "is_completed_period": False,
                    "notes": "",
                },
            ],
        }

        with patch(
            "features.classify_month_window_for_features",
            return_value={
                "has_month_window": True,
                "style": "bounded",
                "time_n": 3,
                "confidence": "high",
                "reason": "range across three months",
            },
        ):
            features = build_seed_features(result)

        from seeds import load_seeds
        from selector import choose_seed_or_report_ambiguity, select_seed_candidates_strict

        candidates = select_seed_candidates_strict(
            features,
            load_seeds(),
            client_name=None,
            top_k=3,
        )
        decision = choose_seed_or_report_ambiguity(candidates, client_name=None)

        self.assertEqual(decision["status"], "MATCH_FOUND")
        self.assertEqual(
            decision["selected_seed"]["seed_id"],
            "S154_product_presence_month_bounded",
        )

    def test_product_presence_unknown_month_style_has_no_candidate(self):
        result = {
            "original_input": "Find customers who purchased product 123 sometime around month end.",
            "clauses": [
                {
                    "clause_id": "1",
                    "clause_type": "attribute_filter",
                    "text": "product 123",
                    "agg_hint": None,
                    "kpi_text": None,
                    "operator_hint": "=",
                    "values": ["123"],
                    "time_n": None,
                    "time_unit": None,
                    "is_completed_period": None,
                    "notes": "",
                },
                {
                    "clause_id": "2",
                    "clause_type": "time_window",
                    "text": "around month end",
                    "agg_hint": None,
                    "kpi_text": None,
                    "operator_hint": None,
                    "values": [],
                    "time_n": 1,
                    "time_unit": "MONTHS",
                    "is_completed_period": False,
                    "notes": "",
                },
            ],
        }

        with patch(
            "features.classify_month_window_for_features",
            return_value={
                "has_month_window": True,
                "style": "unknown",
                "time_n": None,
                "confidence": "low",
                "reason": "unclear month semantics",
            },
        ):
            features = build_seed_features(result)

        from seeds import load_seeds
        from selector import select_seed_candidates_strict

        candidates = select_seed_candidates_strict(
            features,
            load_seeds(),
            client_name=None,
            top_k=3,
        )

        self.assertEqual(features["month_window_style"], "unknown")
        self.assertEqual(candidates, [])

    def test_aggregation_with_own_condition_dominates_auxiliary_formula(self):
        result = {
            "original_input": (
                "Customers whose total recharge amount is greater than the "
                "specified threshold and calculate 20% of it for display."
            ),
            "clauses": [
                {
                    "clause_id": "clause_1",
                    "clause_type": "aggregation",
                    "text": "total recharge amount is greater than the specified threshold",
                    "agg_hint": "SUM",
                    "kpi_text": "total recharge amount",
                    "operator_hint": ">",
                    "values": [],
                    "time_n": None,
                    "time_unit": None,
                    "is_completed_period": None,
                    "notes": "",
                },
                {
                    "clause_id": "clause_2",
                    "clause_type": "formula",
                    "text": "calculate 20% of it for display",
                    "agg_hint": "FORMULA",
                    "kpi_text": None,
                    "operator_hint": None,
                    "values": [],
                    "time_n": None,
                    "time_unit": None,
                    "is_completed_period": None,
                    "notes": "",
                },
            ],
        }

        features = build_seed_features(result)

        self.assertEqual(features["agg_type"], "SUM")
        self.assertFalse(features["has_formula"])
        self.assertIsNone(features["formula_type"])
        self.assertEqual(features["kpi_text"], "recharge amount")


if __name__ == "__main__":
    unittest.main()
