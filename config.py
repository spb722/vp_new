import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import urllib3
from groq import Groq

DATA_DIR = Path(os.getenv("VP_DATA_DIR", "./data"))

MODEL = "openai/gpt-oss-20b"

VP_VERIFY_URL = "http://localhost:5678/webhook/VP_verify"

_api_key = os.environ.get("GROQ_API_KEY")
if not _api_key:
    raise EnvironmentError("GROQ_API_KEY environment variable is not set.")
client = Groq(api_key=_api_key)

print("Groq client ready. Model:", MODEL)
