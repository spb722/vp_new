import os
import unittest
from contextlib import redirect_stdout
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("LLM_PROVIDER", "groq")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("LANGSMITH_TRACING", "false")

import vp_logging


class VPLoggingTests(unittest.TestCase):
    def test_logs_decomposition_and_secondary_providers_separately(self):
        output = StringIO()

        with (
            patch.object(vp_logging, "DECOMPOSITION_MODEL", "telecom-vp:3b"),
            patch.object(
                vp_logging,
                "DECOMPOSITION_BASE_URL",
                "http://localhost:11434/v1/",
            ),
            patch.object(vp_logging, "LLM_PROVIDER", "openrouter"),
            patch.object(vp_logging, "MODEL", "openai/gpt-oss-20b"),
            redirect_stdout(output),
        ):
            vp_logging.print_vp_resolve_log(
                SimpleNamespace(input="total revenue", client_name=None),
                {"ok": False, "trajectory": []},
            )

        logged = output.getvalue()
        self.assertIn("decomposition: ollama", logged)
        self.assertIn("model=telecom-vp:3b", logged)
        self.assertIn("base_url=http://localhost:11434/v1/", logged)
        self.assertIn("secondary: openrouter", logged)


if __name__ == "__main__":
    unittest.main()
