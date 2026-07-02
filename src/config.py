"""
Environment and LLM client configuration.

API keys are loaded from a local .env file (never committed to the repo).
Copy .env.example to .env and fill in your own key before running the pipeline.
"""

import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise EnvironmentError(
        "OPENAI_API_KEY not found. Copy .env.example to .env and add your key."
    )

# Model used across all pipeline stages. gpt-4o-mini is used throughout for
# a good cost/quality tradeoff on classification, summarization, and
# short-form generation tasks like these.
MODEL_NAME = "gpt-4o-mini"
