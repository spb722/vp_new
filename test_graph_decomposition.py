import os
import unittest
from unittest.mock import patch

os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("LANGSMITH_TRACING", "false")

import graph
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

    def test_route_after_parse_continues_on_successful_parse(self):
        self.assertEqual(graph.route_after_parse({"parse_ok": True}), "select_seed")

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
