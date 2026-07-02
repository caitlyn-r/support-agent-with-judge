"""
Stage 3: Policy-grounded email response generation.

A detailed zero-shot prompt embeds the company's support policies directly so
the drafted response can't promise anything outside of them, and requires a
mandatory apology opener whenever the ticket's sentiment was scored negative.
"""

from langchain_openai import ChatOpenAI

from .config import MODEL_NAME
from .policies import SUPPORT_POLICIES, COMPANY_NAME

EMAIL_RESPONSE_SYSTEM_MESSAGE = f"""You are an expert Customer Support Representative for {COMPANY_NAME}. Your task is to draft a professional, empathetic, and helpful email response to a customer's support ticket.

You will be provided with two key pieces of information to guide your response:
1. Ticket Summary: A brief overview of the customer's issue, including sentiment and categorized problem area.
2. Ticket Evaluation: An analysis of the ticket, including factual accuracy and an overall score of the summarization.

INSTRUCTIONS & GUIDELINES:
- Understand the Issue: Use both the Ticket Summary and the Ticket Evaluation to understand the customer's situation and determine the appropriate resolution.
- Mandatory Apology: Check the customer's sentiment in the evaluation. If the sentiment is NEGATIVE, you MUST begin the email with a sincere apology for the inconvenience they have experienced.
- Tone: Maintain a polite, professional, and empathetic tone throughout the email.
- Format: Format the output as a ready-to-send email draft (include placeholders like [Customer Name] if the name is not provided).
- Policy Adherence: You must strictly abide by the official policies below when offering a resolution. Do not promise anything outside of these guidelines.

{SUPPORT_POLICIES}
"""

# Slightly higher max_tokens than the summarizer so a full email (greeting,
# body, next steps, sign-off) has room to breathe.
_llm = ChatOpenAI(
    model_name=MODEL_NAME,
    temperature=0.35,
    max_tokens=450,
    frequency_penalty=0.2,
    presence_penalty=0.1,
)


def generate_email_response(ticket_summary: dict, ticket_evaluation: dict) -> str:
    """Generate a customer-facing email response for one support ticket."""
    user_message = f"""
Generate a polished customer-facing support email using the information below.

Ticket Summary:
{ticket_summary}

Internal Evaluation:
{ticket_evaluation}

Requirements:
- Use the summary and evaluation to understand the issue, urgency, and tone.
- Do not mention internal labels, scores, evaluations, or model analysis.
- Include a clear subject line.
- Write in a professional, empathetic, and concise support tone.
- Return only the email response text.
"""
    response = _llm.invoke([
        ("system", EMAIL_RESPONSE_SYSTEM_MESSAGE),
        ("human", user_message),
    ])

    return response.content.strip()
