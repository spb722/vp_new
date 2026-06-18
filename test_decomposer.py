import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import jsonschema

os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("LANGSMITH_TRACING", "false")

import config
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
    def test_ollama_prompt_matches_v2_training_prompt_exactly(self):
        self.assertEqual(
            decomposer.OLLAMA_FINE_TUNED_SYSTEM_PROMPT,
            "You are a telecom VP request decomposition engine. Return only JSON matching schema version 2.0.",
        )

    def test_default_decomposition_provider_uses_ollama_prompt(self):
        self.assertEqual(
            decomposer.select_decomposition_system_prompt(None),
            decomposer.OLLAMA_FINE_TUNED_SYSTEM_PROMPT,
        )

    def test_freellmapi_uses_detailed_general_prompt(self):
        prompt = decomposer.select_decomposition_system_prompt("free-llm-api")

        self.assertEqual(
            prompt,
            decomposer.GENERAL_DECOMPOSITION_SYSTEM_PROMPT,
        )
        self.assertIn("Splitting rules:", prompt)
        self.assertIn('"schema_version": "2.0"', prompt)
        self.assertIn("attribute_filter", prompt)
        self.assertIn("time_window", prompt)

    def test_openrouter_uses_detailed_general_prompt(self):
        self.assertEqual(
            decomposer.select_decomposition_system_prompt("openrouter"),
            decomposer.GENERAL_DECOMPOSITION_SYSTEM_PROMPT,
        )

    def test_decomposition_apikey_fallback_is_supported(self):
        with patch.dict(
            os.environ,
            {
                "DECOMPOSITION_API_KEY": "",
                "DECOMPOSITION_APIKEY": "legacy-decomposition-key",
            },
        ):
            self.assertEqual(
                config.get_decomposition_api_key(),
                "legacy-decomposition-key",
            )

    def test_secondary_freellmapi_provider_aliases_are_supported(self):
        self.assertEqual(config.normalize_llm_provider("free-llm-api"), "freellmapi")
        self.assertEqual(config.normalize_llm_provider("free_llm_api"), "freellmapi")
        self.assertEqual(config.normalize_llm_provider("freellmapi"), "freellmapi")

    def test_secondary_freellmapi_apikey_fallback_is_supported(self):
        with patch.dict(
            os.environ,
            {
                "LLM_API_KEY": "",
                "LLM_APIKEY": "secondary-free-key",
                "DECOMPOSITION_API_KEY": "decomposition-key",
                "DECOMPOSITION_APIKEY": "legacy-decomposition-key",
            },
        ):
            self.assertEqual(
                config.get_llm_api_key("free-llm-api"),
                "secondary-free-key",
            )

    def test_secondary_freellmapi_can_reuse_decomposition_apikey(self):
        with patch.dict(
            os.environ,
            {
                "LLM_API_KEY": "",
                "LLM_APIKEY": "",
                "DECOMPOSITION_API_KEY": "",
                "DECOMPOSITION_APIKEY": "shared-free-key",
            },
        ):
            self.assertEqual(
                config.get_llm_api_key("freellmapi"),
                "shared-free-key",
            )

    def test_secondary_freellmapi_uses_openai_compatible_token_option(self):
        with patch.object(config, "LLM_PROVIDER", "freellmapi"):
            options = config.chat_completion_options()

        self.assertIn("max_tokens", options)
        self.assertNotIn("max_completion_tokens", options)
        self.assertNotIn("reasoning_effort", options)
        self.assertNotIn("extra_body", options)

    def test_decomposition_schema_accepts_v2_response_shape(self):
        payload = {
            "schema_version": "2.0",
            "original_input": "Show total revenue over the last 2 days",
            "clauses": [
                {
                    "clause_id": "C1",
                    "clause_type": "aggregation",
                    "text": "total revenue",
                    "agg_hint": "SUM",
                    "kpi_text": "revenue",
                    "operator_hint": None,
                    "values": [],
                    "time_n": None,
                    "time_unit": None,
                    "is_completed_period": None,
                    "notes": "",
                },
                {
                    "clause_id": "C2",
                    "clause_type": "time_window",
                    "text": "over the last 2 days",
                    "agg_hint": None,
                    "kpi_text": None,
                    "operator_hint": None,
                    "values": [],
                    "time_n": 2,
                    "time_unit": "DAYS",
                    "is_completed_period": False,
                    "notes": "",
                },
                {
                    "clause_id": "C3",
                    "clause_type": "attribute_filter",
                    "text": "prepaid users",
                    "agg_hint": None,
                    "kpi_text": None,
                    "operator_hint": "=",
                    "values": ["prepaid"],
                    "time_n": None,
                    "time_unit": None,
                    "is_completed_period": None,
                    "notes": "",
                },
            ],
            "seed_intent": {
                "agg_type": "SUM",
                "formula_type": "none",
                "time_required": True,
                "time_unit": "DAYS",
                "time_bound_style": "lower_only",
                "groupby_required": False,
                "parameterized_window": False,
                "has_count_constraint": False,
                "presence_mode": "none",
                "entity_mode": "ordinary_kpi",
            },
            "formula": {
                "factor": None,
                "divisor": None,
            },
        }

        jsonschema.validate(payload, decomposer.decomposition_schema["schema"])

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

        with patch.object(decomposer, "decomposition_client", fake_client):
            result = decompose_vp_input("total revenue")

        self.assertEqual(result["original_input"], "total revenue")
        self.assertEqual(result["clauses"][0]["kpi_text"], "revenue")
        self.assertEqual(len(fake_client.chat.completions.calls), 2)
        self.assertEqual(
            fake_client.chat.completions.calls[0]["model"],
            decomposer.DECOMPOSITION_MODEL,
        )
        self.assertEqual(fake_client.chat.completions.calls[0]["temperature"], 0)
        self.assertIn("max_tokens", fake_client.chat.completions.calls[0])
        self.assertNotIn("max_completion_tokens", fake_client.chat.completions.calls[0])
        retry_messages = fake_client.chat.completions.calls[1]["messages"]
        self.assertIn("not valid JSON", retry_messages[-1]["content"])
        self.assertIn("schema_version", retry_messages[-1]["content"])

    def test_decompose_raises_after_failed_repair(self):
        fake_client = FakeClient([
            '{"original_input": "total revenue", "clauses": [{"text": "unterminated}]',
            '{"original_input": "total revenue", "clauses": [{"text": "still bad}]',
        ])

        with patch.object(decomposer, "decomposition_client", fake_client):
            with self.assertRaises(DecompositionError):
                decompose_vp_input("total revenue")

    def test_decompose_wraps_provider_request_failure(self):
        fake_client = FakeClient([])
        fake_client.chat.completions.create = lambda **kwargs: (_ for _ in ()).throw(
            RuntimeError("provider unavailable")
        )

        with patch.object(decomposer, "decomposition_client", fake_client):
            with self.assertRaisesRegex(DecompositionError, "request failed"):
                decompose_vp_input("total revenue")


if __name__ == "__main__":
    unittest.main()
