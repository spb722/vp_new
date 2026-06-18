import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def normalize_decomposition_provider(provider: str | None) -> str:
    return (
        provider or "ollama"
    ).strip().lower().replace("-", "").replace("_", "")


def get_decomposition_api_key() -> str:
    return (
        os.getenv("DECOMPOSITION_API_KEY")
        or os.getenv("DECOMPOSITION_APIKEY")
        or "ollama"
    )


DATA_DIR = Path(os.getenv("VP_DATA_DIR", "./data"))

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").strip().lower()
MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
REASONING_EFFORT = os.getenv("REASONING_EFFORT", "medium")
MAX_COMPLETION_TOKENS = int(os.getenv("MAX_COMPLETION_TOKENS", "4096"))
DECOMPOSITION_LLM_PROVIDER = normalize_decomposition_provider(
    os.getenv("DECOMPOSITION_LLM_PROVIDER")
)
DECOMPOSITION_MODEL = os.getenv("DECOMPOSITION_MODEL", "telecom-vp:3b")
DECOMPOSITION_BASE_URL = os.getenv(
    "DECOMPOSITION_BASE_URL",
    "http://localhost:11434/v1/",
)
DECOMPOSITION_MAX_TOKENS = int(
    os.getenv("DECOMPOSITION_MAX_TOKENS", "4096")
)
DECOMPOSITION_API_KEY = get_decomposition_api_key()
OPENROUTER_REQUIRE_PARAMETERS = (
    os.getenv("OPENROUTER_REQUIRE_PARAMETERS", "false").strip().lower()
    in ("1", "true", "yes")
)

VP_VERIFY_URL = "http://localhost:5678/webhook/VP_verify"
#VP_VERIFY_URL = "http://10.0.11.179:5678/webhook/VP_verify"
#

if LLM_PROVIDER == "groq":
    from groq import Groq

    _api_key = os.environ.get("GROQ_API_KEY")
    if not _api_key:
        raise EnvironmentError("GROQ_API_KEY environment variable is not set.")
    client = Groq(api_key=_api_key)
elif LLM_PROVIDER == "openrouter":
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

decomposition_client = OpenAI(
    api_key=DECOMPOSITION_API_KEY,
    base_url=DECOMPOSITION_BASE_URL,
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


def decomposition_chat_completion_options() -> dict:
    return {
        "max_tokens": DECOMPOSITION_MAX_TOKENS,
    }


print(
    f"{LLM_PROVIDER} client ready. Model: {MODEL}. "
    f"Reasoning effort: {REASONING_EFFORT}. "
    f"Max completion tokens: {MAX_COMPLETION_TOKENS}"
)
print(
    f"{DECOMPOSITION_LLM_PROVIDER} decomposition client ready. "
    f"Model: {DECOMPOSITION_MODEL}. "
    f"Base URL: {DECOMPOSITION_BASE_URL}. "
    f"Max tokens: {DECOMPOSITION_MAX_TOKENS}"
)
