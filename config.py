import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

DATA_DIR = Path(os.getenv("VP_DATA_DIR", "./data"))

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").strip().lower()
MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
REASONING_EFFORT = os.getenv("REASONING_EFFORT", "medium")
MAX_COMPLETION_TOKENS = int(os.getenv("MAX_COMPLETION_TOKENS", "4096"))
OPENROUTER_REQUIRE_PARAMETERS = (
    os.getenv("OPENROUTER_REQUIRE_PARAMETERS", "false").strip().lower()
    in ("1", "true", "yes")
)

#VP_VERIFY_URL = "http://localhost:5678/webhook/VP_verify"
VP_VERIFY_URL = "http://10.0.11.179:5678/webhook/VP_verify"
#

if LLM_PROVIDER == "groq":
    from groq import Groq

    _api_key = os.environ.get("GROQ_API_KEY")
    if not _api_key:
        raise EnvironmentError("GROQ_API_KEY environment variable is not set.")
    client = Groq(api_key=_api_key)
elif LLM_PROVIDER == "openrouter":
    from openai import OpenAI

    _api_key = os.environ.get("OPENROUTER_API_KEY")
    if not _api_key:
        raise EnvironmentError("OPENROUTER_API_KEY environment variable is not set.")
    client = OpenAI(
        api_key=_api_key,
        base_url="https://openrouter.ai/api/v1",
    )
else:
    raise ValueError(
        "Unsupported LLM_PROVIDER. Expected 'groq' or 'openrouter', "
        f"got {LLM_PROVIDER!r}."
    )


def chat_completion_options() -> dict:
    if LLM_PROVIDER == "openrouter":
        extra_body = {
            "reasoning": {
                "effort": REASONING_EFFORT,
            },
        }

        if OPENROUTER_REQUIRE_PARAMETERS:
            extra_body["provider"] = {"require_parameters": True}

        return {
            "extra_body": extra_body,
            "max_completion_tokens": MAX_COMPLETION_TOKENS,
        }

    return {
        "reasoning_effort": REASONING_EFFORT,
        "max_completion_tokens": MAX_COMPLETION_TOKENS,
    }


print(
    f"{LLM_PROVIDER} client ready. Model: {MODEL}. "
    f"Reasoning effort: {REASONING_EFFORT}. "
    f"Max completion tokens: {MAX_COMPLETION_TOKENS}"
)
