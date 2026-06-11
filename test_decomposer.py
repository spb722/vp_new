import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("LANGSMITH_TRACING", "false")

import decomposer
from decomposer import DecompositionError, decompose_vp_input, parse_decomposition_content


VALID_DECOMPOSITION = """
{
  "original_input": "total revenue",
  "clauses": [
    {
      "clause_id": "C1",
      "clause_type": "aggregation",
      "text": "total revenue",
      "agg_hint": "SUM",
      "kpi_text": "revenue",
      "operator_hint": null,
      "values": [],
      "time_n": null,
      "time_unit": null,
      "is_completed_period": null,
      "notes": ""
    }
  ]
}
"""


class FakeCompletions:
    def __init__(self, contents):
        self.contents = list(contents)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        content = self.contents.pop(0)
        message = SimpleNamespace(content=content)
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


class FakeClient:
    def __init__(self, contents):
        self.chat = SimpleNamespace(completions=FakeCompletions(contents))


class DecomposerTests(unittest.TestCase):
    def test_parse_wraps_top_level_clause_list(self):
        result = parse_decomposition_content(
            '[{"clause_id": "C1", "clause_type": "aggregation"}]',
            "total revenue",
        )

        self.assertEqual(result["original_input"], "total revenue")
        self.assertEqual(result["clauses"][0]["clause_id"], "C1")

    def test_decompose_repairs_malformed_json_on_second_attempt(self):
        fake_client = FakeClient([
            '{"original_input": "total revenue", "clauses": [{"text": "unterminated}]',
            VALID_DECOMPOSITION,
        ])

        with patch.object(decomposer, "client", fake_client):
            result = decompose_vp_input("total revenue")

        self.assertEqual(result["original_input"], "total revenue")
        self.assertEqual(result["clauses"][0]["kpi_text"], "revenue")
        self.assertEqual(len(fake_client.chat.completions.calls), 2)
        retry_messages = fake_client.chat.completions.calls[1]["messages"]
        self.assertIn("not valid JSON", retry_messages[-1]["content"])

    def test_decompose_raises_after_failed_repair(self):
        fake_client = FakeClient([
            '{"original_input": "total revenue", "clauses": [{"text": "unterminated}]',
            '{"original_input": "total revenue", "clauses": [{"text": "still bad}]',
        ])

        with patch.object(decomposer, "client", fake_client):
            with self.assertRaises(DecompositionError):
                decompose_vp_input("total revenue")

    def test_decompose_wraps_provider_request_failure(self):
        fake_client = FakeClient([])
        fake_client.chat.completions.create = lambda **kwargs: (_ for _ in ()).throw(
            RuntimeError("provider unavailable")
        )

        with patch.object(decomposer, "client", fake_client):
            with self.assertRaisesRegex(DecompositionError, "request failed"):
                decompose_vp_input("total revenue")


if __name__ == "__main__":
    unittest.main()
