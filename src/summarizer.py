"""
Stage 1: Ticket summarization.

Uses a zero-shot prompt (the model has enough pre-trained knowledge to extract
structured summaries without few-shot examples, which keeps token usage down)
to turn raw, unstructured ticket text into a structured summary with
key issues, sentiment, action items, and a confidence label.
"""

from langchain_openai import ChatOpenAI

from .config import MODEL_NAME
from .utils import safe_parse_json, strip_code_fences

SUMMARY_SYSTEM_MESSAGE = """You are a concise assistant that summarizes customer support tickets.
Always prioritize factual accuracy and avoid inventing details.
If the input lacks enough information, say "insufficient data" for missing fields.
Output only JSON with keys: "summary", "key_issues", "sentiment", "action_items", "confidence".
Keep language neutral."""

# Low temperature keeps the summary focused and deterministic; a short max_tokens
# keeps output concise; frequency/presence penalties reduce repeated phrasing.
_llm = ChatOpenAI(
    model_name=MODEL_NAME,
    temperature=0.35,
    max_tokens=300,
    frequency_penalty=0.2,
    presence_penalty=0.1,
)


def generate_ticket_summary(ticket_text: str) -> dict:
    """Generate a structured summary for one support ticket."""
    user_message = f"""
Summarize the support ticket below for a customer support agent.

Ticket text:
{ticket_text}
"""

    response = _llm.invoke([
        ("system", SUMMARY_SYSTEM_MESSAGE),
        ("human", user_message),
    ])

    response_text = strip_code_fences(response.content.strip())
    parsed = safe_parse_json(response_text)
    if parsed is not None:
        return parsed

    return {
        "summary": response_text or ticket_text,
        "key_issues": [],
        "sentiment": "unknown",
        "action_items": [],
        "confidence": "unknown",
    }
