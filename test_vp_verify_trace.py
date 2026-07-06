import os
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("LANGSMITH_TRACING", "false")

import api_client


class FakeResponse:
    ok = True
    status_code = 200
    text = ""

    def json(self):
        return {
            "output": {
                "matches": [
                    {
                        "kpi": "COMMON_Data_Usage",
                        "table_name": "Common_Seg_Fct",
                        "datatype": "number",
                        "date_column": "COMMON_Event_Date",
                    }
                ],
                "unmatched": [],
            }
        }


class VPVerifyTraceTests(unittest.TestCase):
    def test_resolve_condition_preserves_date_column(self):
        response = {
            "output": {
                "matches": [
                    {
                        "kpi": "Total_Data_Revenue",
                        "table_name": "Instant_cdr_group",
                        "datatype": "numeric",
                        "date_column": "COMMON_FCT_DT",
                    }
                ],
                "unmatched": [],
            }
        }

        with patch.object(api_client, "call_vp_verify", return_value=response):
            result = api_client.resolve_condition_from_api("data bundle revenue")

        self.assertTrue(result["matched"])
        self.assertEqual(result["column"], "Total_Data_Revenue")
        self.assertEqual(result["date_column"], "COMMON_FCT_DT")

    def test_resolve_kpi_preserves_date_column(self):
        resolved = {
            "matched": True,
            "input": "data bundle revenue",
            "column": "Total_Data_Revenue",
            "table_name": "Instant_cdr_group",
            "datatype": "numeric",
            "date_column": "COMMON_FCT_DT",
            "raw_match": {},
            "raw_response": {},
        }

        with patch.object(api_client, "resolve_condition_from_api", return_value=resolved):
            result = api_client.resolve_kpi_from_api("data bundle revenue")

        self.assertTrue(result["matched"])
        self.assertEqual(result["kpi_col"], "Total_Data_Revenue")
        self.assertEqual(result["table_name"], "Instant_cdr_group")
        self.assertEqual(result["date_column"], "COMMON_FCT_DT")

    def test_trace_records_request_payload_and_response(self):
        api_client.start_vp_verify_trace()
        condition_text = f"__unit_test_trace_data_usage_{time.time_ns()}__"
        api_client.clear_vp_cache(condition_text)
        self.addCleanup(api_client.clear_vp_cache, condition_text)

        with patch.object(api_client.requests, "post", return_value=FakeResponse()) as post:
            with api_client.vp_verify_lookup_context(
                lookup_type="kpi",
                source_text="data usage",
                candidate_text="data usage",
            ):
                result = api_client.call_vp_verify(condition_text)

        self.assertTrue(result["output"]["matches"])
        post.assert_called_once()

        trace = api_client.get_vp_verify_trace()
        self.assertEqual(len(trace), 1)

        event = trace[0]
        self.assertEqual(event["lookup_type"], "kpi")
        self.assertEqual(event["condition_text"], condition_text)
        self.assertEqual(
            event["payload"],
            {"conditions": [condition_text], "check": False},
        )
        self.assertEqual(event["status"], "ok")
        self.assertEqual(event["status_code"], 200)
        self.assertEqual(event["matches_count"], 1)
        self.assertEqual(event["response"]["output"]["matches"][0]["kpi"], "COMMON_Data_Usage")
        self.assertEqual(
            event["response"]["output"]["matches"][0]["date_column"],
            "COMMON_Event_Date",
        )

    def test_resolve_kpi_reformulates_after_miss(self):
        api_client._KPI_NEGATIVE_CACHE.clear()
        miss = {
            "matched": False,
            "input": "free data revenue",
            "column": None,
            "table_name": None,
            "datatype": None,
            "raw_response": {
                "output": {
                    "matches": [],
                    "unmatched": [
                        {"condition": "free data revenue", "reason": "not found"}
                    ],
                }
            },
        }
        hit = {
            "matched": True,
            "input": "revenue from free data usage",
            "column": "COMMON_Data_Free_Revenue",
            "table_name": "Common_Seg_Fct",
            "datatype": "number",
            "date_column": "COMMON_Event_Date",
            "raw_match": {
                "condition": "free data revenue",
                "kpi": "COMMON_Data_Free_Revenue",
            },
            "raw_response": {"output": {"matches": [], "unmatched": []}},
        }

        with patch.object(api_client, "resolve_condition_from_api", side_effect=[miss, hit]):
            with patch.object(
                api_client,
                "reformulate_kpi_text",
                return_value="revenue from free data usage",
            ):
                result = api_client.resolve_kpi_from_api("free data revenue")

        self.assertTrue(result["matched"])
        self.assertEqual(result["input"], "revenue from free data usage")
        self.assertEqual(result["kpi_col"], "COMMON_Data_Free_Revenue")
        self.assertEqual(len(result["attempt_log"]), 2)

    def test_resolve_kpi_rejects_match_that_drops_qualifier(self):
        api_client._KPI_NEGATIVE_CACHE.clear()
        bad_hit = {
            "matched": True,
            "input": "free data revenue",
            "column": "Total_Data_usage",
            "table_name": "Instant_cdr_group",
            "datatype": "numeric",
            "date_column": None,
            "raw_match": {
                "condition": "pay-as-you-go data usage",
                "kpi": "Total_Data_usage",
            },
            "raw_response": {"output": {"matches": [], "unmatched": []}},
        }

        with patch.object(api_client, "resolve_condition_from_api", return_value=bad_hit):
            with patch.object(
                api_client,
                "reformulate_kpi_text",
                return_value="free data revenue",
            ):
                result = api_client.resolve_kpi_from_api("free data revenue")

        self.assertFalse(result["matched"])
        self.assertIn("dropped required KPI qualifier", result["attempt_log"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
