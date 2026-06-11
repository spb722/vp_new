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
                    }
                ],
                "unmatched": [],
            }
        }


class VPVerifyTraceTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
