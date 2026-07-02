"""Shared helpers used across the pipeline stages."""

import json
import re


def strip_code_fences(text: str) -> str:
    """Remove leading/trailing markdown code fences (```json ... ```) if present."""
    if not text:
        return text
    return re.sub(r"^```(?:json)?|```$", "", text.strip()).strip()


def safe_parse_json(text: str):
    """
    Safely extract and parse JSON from an LLM response.

    Acts as a fallback for cases where the model wraps its JSON output in
    markdown formatting or adds stray conversational text around it.
    Returns None if no valid JSON object can be recovered.
    """
    if not text:
        return None

    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        return None
