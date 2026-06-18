import os
import unittest

os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("LANGSMITH_TRACING", "false")

from month_classifier import MONTH_WINDOW_PROMPT, parse_month_window_content


class MonthClassifierPromptTests(unittest.TestCase):
    def test_prompt_has_generic_singular_and_plural_month_rules(self):
        self.assertIn('"over the last month" -> exact, time_n=1', MONTH_WINDOW_PROMPT)
        self.assertIn('"over the last N months"', MONTH_WINDOW_PROMPT)
        self.assertIn("bounded, time_n=N", MONTH_WINDOW_PROMPT)
        self.assertIn("Return exactly one complete JSON object", MONTH_WINDOW_PROMPT)
        self.assertNotIn("product 123", MONTH_WINDOW_PROMPT)

    def test_parse_month_window_completes_partial_provider_schema_output(self):
        result = parse_month_window_content(
            '{"style":"exact","time_n":1,'
            '"reason":"past month indicates exact previous month"}'
        )

        self.assertEqual(result["style"], "exact")
        self.assertEqual(result["time_n"], 1)
        self.assertTrue(result["has_month_window"])
        self.assertEqual(result["confidence"], "medium")


if __name__ == "__main__":
    unittest.main()
