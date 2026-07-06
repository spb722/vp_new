import os
import unittest
from unittest.mock import patch

os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("LANGSMITH_TRACING", "false")

import graph
from decomposition_verifier import parse_judge_content
from decomposer import DecompositionError


class GraphDecompositionTests(unittest.TestCase):
    def test_parse_request_returns_controlled_failure_on_decomposition_error(self):
        state = {
            "user_input": "total revenue",
            "last_error": None,
            "retry_count": 0,
            "trajectory": [],
        }

        with patch.object(graph, "decompose_vp_input", side_effect=DecompositionError("bad json")):
            result = graph.parse_request(state)

        self.assertFalse(result["parse_ok"])
        self.assertIn("Decomposition failed", result["error"])
        self.assertEqual(result["trajectory"], ["parse_request:failed"])

    def test_route_after_parse_stops_on_failed_parse(self):
        self.assertEqual(graph.route_after_parse({"parse_ok": False}), "stop_failure")

    def test_route_after_parse_continues_to_decomposition_verifier(self):
        self.assertEqual(graph.route_after_parse({"parse_ok": True}), "verify_decomposition")

    def test_route_after_decomposition_verification_continues_on_success(self):
        self.assertEqual(
            graph.route_after_decomposition_verification(
                {"decomposition_verified": True, "decomposition_attempt": 1}
            ),
            "select_seed",
        )

    def test_route_after_decomposition_verification_retries_before_max_attempts(self):
        self.assertEqual(
            graph.route_after_decomposition_verification(
                {"decomposition_verified": False, "decomposition_attempt": 1}
            ),
            "parse_request",
        )

    def test_route_after_decomposition_verification_stops_after_max_attempts(self):
        self.assertEqual(
            graph.route_after_decomposition_verification(
                {"decomposition_verified": False, "decomposition_attempt": 3}
            ),
            "stop_failure",
        )

    def test_parse_judge_content_accepts_fenced_json(self):
        parsed = parse_judge_content(
            '```json\n{"judge":"aggregation","passed":true,"failures":[]}\n```'
        )

        self.assertEqual(parsed["judge"], "aggregation")
        self.assertTrue(parsed["passed"])

    def test_parse_judge_content_accepts_json_with_trailing_explanation(self):
        parsed = parse_judge_content(
            '{"judge":"time","passed":true,"failures":[]}\n\n'
            "The decomposition correctly identifies the time window."
        )

        self.assertEqual(parsed["judge"], "time")
        self.assertTrue(parsed["passed"])

    def test_resolve_columns_reports_filter_failure_separately_from_kpi(self):
        state = {
            "features": {
                "kpi_text": "data usage",
                "attribute_filters": [
                    {
                        "text": "smartphone users",
                        "values": ["smartphone"],
                        "operator_hint": "=",
                    }
                ],
                "duration_thresholds": [],
            },
            "trajectory": [],
        }

        kpi_mapping = {
            "matched": True,
            "input": "data usage",
            "kpi_col": "COMMON_Data_Usage",
            "table_name": "Common_Seg_Fct",
            "datatype": "number",
        }

        with patch.object(graph, "resolve_kpi_from_api", return_value=kpi_mapping):
            with patch.object(graph, "render_filters", side_effect=RuntimeError("smartphone failed")):
                result = graph.resolve_columns(state)

        self.assertFalse(result["columns_ok"])
        self.assertEqual(result["kpi_mapping"], kpi_mapping)
        self.assertIn("Filter resolution failed", result["columns_error"])
        self.assertIn("smartphone users", result["columns_error"])
        self.assertNotIn("resolving kpi_text", result["columns_error"])

    def test_build_kpi_lookup_text_includes_time_when_enabled(self):
        features = {
            "kpi_text": "revenue",
            "time_n": 1,
            "time_unit": "MONTHS",
            "time_bound_style": "exact",
        }

        with patch.object(graph, "VP_VERIFY_INCLUDE_TIME_IN_KPI", True):
            self.assertEqual(
                graph.build_kpi_lookup_text(features),
                "revenue last 1 month",
            )

    def test_build_kpi_lookup_text_can_be_disabled(self):
        features = {
            "kpi_text": "revenue",
            "time_n": 1,
            "time_unit": "MONTHS",
            "time_bound_style": "exact",
        }

        with patch.object(graph, "VP_VERIFY_INCLUDE_TIME_IN_KPI", False):
            self.assertEqual(graph.build_kpi_lookup_text(features), "revenue")

    def test_resolve_columns_sends_time_scoped_kpi_lookup_text(self):
        state = {
            "features": {
                "kpi_text": "revenue",
                "time_n": 1,
                "time_unit": "MONTHS",
                "time_bound_style": "exact",
                "attribute_filters": [],
                "duration_thresholds": [],
            },
            "trajectory": [],
        }

        kpi_mapping = {
            "matched": True,
            "input": "revenue last 1 month",
            "kpi_col": "TOTAL_REVENUE_M1",
            "table_name": "Profile_Cdr_group",
            "datatype": "number",
        }

        with patch.object(graph, "VP_VERIFY_INCLUDE_TIME_IN_KPI", True):
            with patch.object(graph, "resolve_kpi_from_api", return_value=kpi_mapping) as resolve:
                with patch.object(graph, "render_filters", return_value=[]):
                    result = graph.resolve_columns(state)

        resolve.assert_called_once_with("revenue last 1 month")
        self.assertTrue(result["columns_ok"])

    def test_verify_decomposition_node_sets_honest_stop_error_at_max_attempts(self):
        state = {
            "user_input": "total revenue last 3 months",
            "decomposition": {"clauses": []},
            "decomposition_attempt": 3,
            "trajectory": ["parse_request"],
        }
        verifier_result = {
            "verified": False,
            "judge_results": [
                {
                    "judge": "time",
                    "passed": False,
                    "failures": [
                        {
                            "field": "time_unit",
                            "expected": "MONTHS",
                            "actual": "DAYS",
                            "reason": "sentence says months",
                        }
                    ],
                }
            ],
            "feedback": "time judge failed; field=time_unit",
        }

        with patch.object(graph, "verify_decomposition", return_value=verifier_result):
            result = graph.verify_decomposition_node(state)

        self.assertFalse(result["decomposition_verified"])
        self.assertIn("failed after 3 attempts", result["error"])
        self.assertEqual(result["decomposition_attempt_log"][0]["attempt"], 3)
        self.assertEqual(
            result["decomposition_attempt_log"][0]["judge_results"],
            verifier_result["judge_results"],
        )
        self.assertEqual(
            result["trajectory"],
            ["parse_request", "verify_decomposition:failed"],
        )

    def test_resolve_columns_appends_kpi_unmatched_reason(self):
        state = {
            "features": {
                "kpi_text": "recharges",
                "attribute_filters": [],
                "duration_thresholds": [],
            },
            "trajectory": ["parse_request", "select_seed"],
        }

        kpi_mapping = {
            "matched": False,
            "input": "recharges",
            "kpi_col": None,
            "table_name": None,
            "datatype": None,
            "raw_response": {
                "output": {
                    "matches": [],
                    "unmatched": [
                        {
                            "condition": "recharges",
                            "reason": (
                                "No KPI matches the generic recharge count "
                                "without denomination restriction."
                            ),
                        }
                    ],
                }
            },
        }

        with patch.object(graph, "resolve_kpi_from_api", return_value=kpi_mapping):
            result = graph.resolve_columns(state)

        self.assertFalse(result["columns_ok"])
        self.assertEqual(
            result["columns_error"],
            (
                "KPI not matched: recharges "
                "No KPI matches the generic recharge count without denomination restriction."
            ),
        )
        self.assertEqual(
            result["trajectory"],
            ["parse_request", "select_seed", "resolve_columns:kpi_failed"],
        )

    def test_validate_output_rejects_uppercase_structural_placeholder(self):
        result = graph.validate_output(
            {
                "final_parent_condition": (
                    "COMMON_FCT_DT >= CurrentMonth-{N}MONTHS "
                    "AND SUM(Total_Data_Revenue) ${operator} ${value}"
                ),
                "kpi_mapping": {"kpi_col": "Total_Data_Revenue"},
                "selected_seed": {"seed_id": "S13_last_n_months_bounded"},
                "seed_candidates": [{"score": 132}],
                "trajectory": [],
            }
        )

        self.assertFalse(result["validation_result"]["valid"])
        self.assertIn(
            "Unresolved placeholders: ['{N}']",
            result["validation_result"]["errors"],
        )


if __name__ == "__main__":
    unittest.main()
