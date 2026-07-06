import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def normalize_decomposition_provider(provider: str | None) -> str:
    return (
        provider or "ollama"
    ).strip().lower().replace("-", "").replace("_", "")


def normalize_llm_provider(provider: str | None) -> str:
    return (
        provider or "groq"
    ).strip().lower().replace("-", "").replace("_", "")


def get_decomposition_api_key() -> str:
    return (
        os.getenv("DECOMPOSITION_API_KEY")
        or os.getenv("DECOMPOSITION_APIKEY")
        or "ollama"
    )


def get_llm_api_key(provider: str | None = None) -> str | None:
    normalized_provider = normalize_llm_provider(provider or os.getenv("LLM_PROVIDER"))

    if normalized_provider == "groq":
        return os.getenv("GROQ_API_KEY")

    if normalized_provider == "openrouter":
        return os.getenv("OPENROUTER_API_KEY")

    if normalized_provider == "freellmapi":
        return (
            os.getenv("LLM_API_KEY")
            or os.getenv("LLM_APIKEY")
            or os.getenv("DECOMPOSITION_API_KEY")
            or os.getenv("DECOMPOSITION_APIKEY")
        )

    return None


def get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


DATA_DIR = Path(os.getenv("VP_DATA_DIR", "./data"))

LLM_PROVIDER = normalize_llm_provider(os.getenv("LLM_PROVIDER"))
MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
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

VP_VERIFY_URL = os.getenv("VP_VERIFY_URL", "http://localhost:5678/webhook/VP_verify")
VP_VERIFY_TIMEOUT_SECONDS = float(os.getenv("VP_VERIFY_TIMEOUT_SECONDS", "300"))
VP_VERIFY_INCLUDE_TIME_IN_KPI = get_bool_env("VP_VERIFY_INCLUDE_TIME_IN_KPI", True)
#VP_VERIFY_URL = "http://10.0.11.179:5678/webhook/VP_verify"
#

_client = None
_decomposition_client = None


def validate_runtime_config() -> None:
    if LLM_PROVIDER not in {"groq", "openrouter", "freellmapi"}:
        raise ValueError(
            "Unsupported LLM_PROVIDER. Expected 'groq', 'openrouter', "
            "or 'freellmapi', "
            f"got {LLM_PROVIDER!r}."
        )

    if not get_llm_api_key(LLM_PROVIDER):
        if LLM_PROVIDER == "groq":
            raise EnvironmentError("GROQ_API_KEY environment variable is not set.")
        if LLM_PROVIDER == "openrouter":
            raise EnvironmentError("OPENROUTER_API_KEY environment variable is not set.")
        raise EnvironmentError(
            "LLM_API_KEY or LLM_APIKEY environment variable is not set "
            "for freellmapi."
        )

    if VP_VERIFY_TIMEOUT_SECONDS <= 0:
        raise ValueError("VP_VERIFY_TIMEOUT_SECONDS must be greater than 0.")


def get_client():
    global _client
    if _client is not None:
        return _client

    validate_runtime_config()

    if LLM_PROVIDER == "groq":
        from groq import Groq

        _client = Groq(api_key=get_llm_api_key(LLM_PROVIDER))
    elif LLM_PROVIDER == "openrouter":
        _client = OpenAI(
            api_key=get_llm_api_key(LLM_PROVIDER),
            base_url=LLM_BASE_URL or "https://openrouter.ai/api/v1",
        )
    elif LLM_PROVIDER == "freellmapi":
        _client = OpenAI(
            api_key=get_llm_api_key(LLM_PROVIDER),
            base_url=LLM_BASE_URL or "http://localhost:3001/v1/",
        )

    return _client


def get_decomposition_client():
    global _decomposition_client
    if _decomposition_client is None:
        _decomposition_client = OpenAI(
            api_key=DECOMPOSITION_API_KEY,
            base_url=DECOMPOSITION_BASE_URL,
        )
    return _decomposition_client


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

    if LLM_PROVIDER == "freellmapi":
        return {
            "max_tokens": MAX_COMPLETION_TOKENS,
        }

    return {
        "reasoning_effort": REASONING_EFFORT,
        "max_completion_tokens": MAX_COMPLETION_TOKENS,
    }


def decomposition_chat_completion_options() -> dict:
    return {
        "max_tokens": DECOMPOSITION_MAX_TOKENS,
    }
