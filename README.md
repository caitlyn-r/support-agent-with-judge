# Support Ticket Intelligence Agent

A multi-stage LLM pipeline that takes raw, unstructured customer support tickets and produces a structured summary, a policy-grounded draft email response, and an automated quality check on both — designed to sit in front of a human support agent as a "draft + review" tool rather than a fully autonomous responder.

> **Context:** This project was built independently as a portfolio piece, inspired by a coursework assignment on AI agents in business applications. The company (`AuroraCart`), dataset, and support policies used here are all synthetic — written for this repo, not reused from any course materials.

## Why this exists

Support teams at any high-volume e-commerce company deal with the same recurring problem: incoming tickets are noisy, inconsistently written, and expensive to triage. Agents spend real time just figuring out what a customer is asking before they can even start resolving it, and manually drafting responses is slow and inconsistent across agents. This project is a proof-of-concept for using an LLM pipeline to compress that triage-and-draft time — while keeping a human in the loop and an automated check on the AI's output before anything reaches a customer.

## Architecture

```
        Raw Ticket
            │
            ▼
  ┌─────────────────────┐
  │ 1. Summarizer       │  → structured JSON: summary, key issues,
  │    (zero-shot LLM)  │     sentiment, action items, confidence
  └─────────┬───────────┘
            ▼
  ┌─────────────────────┐
  │ 2. Summary Judge    │  → LLM-as-judge score: factual accuracy,
  │    (LLM-as-judge)   │     completeness, conciseness, actionability
  └─────────┬───────────┘
            ▼
┌───────────────────────┐
│ 3. Response Generator │  → policy-grounded, customer-facing
│    (policy-grounded)  │     draft email
└───────────┬───────────┘
            ▼
┌────────────────────────┐
│ 4. Response Judge      │  → pass/fail + scope check, policy
│    (LLM-as-judge)      │     alignment, tone, actionability
└───────────┬────────────┘
            ▼
   Compiled table (CSV) → human agent review queue
```

Each stage is a separate module in `src/`, using its own system prompt and its own LLM call, so stages can be evaluated, swapped, or reprompted independently. The pipeline is currently linear/sequential (no branching, no retries beyond basic JSON-parse fallback) — see [Limitations](#limitations--future-work) below for where that breaks down.

## What each stage does

| Stage | Module | Purpose |
|---|---|---|
| Summarization | `src/summarizer.py` | Zero-shot prompt extracts a structured summary (summary, key issues, sentiment, action items, confidence) from raw ticket text. |
| Summary evaluation | `src/evaluator.py` | An independent LLM call scores the summary 1–5 on factual accuracy, completeness, conciseness, actionability, and tone/clarity. |
| Response generation | `src/response_generator.py` | Drafts a customer-facing email, grounded in an embedded policy document (`src/policies.py`) so it can't promise refunds/replacements outside policy. Forces an apology opener when sentiment is negative. |
| Response evaluation | `src/evaluator.py` | A second judge checks the draft for policy alignment, instruction-following, factual grounding, tone, and — critically — whether the ticket was even in scope for this company at all. |

## Example run

**Input ticket:**
> my card was charged twice for order 55210 and the site still shows payment failed, can someone check this asap i dont want to be charged again

**1. Structured summary**

| Field | Value |
|---|---|
| Summary | Customer reports being charged twice for order 55210 while the site shows payment as failed, and requests urgent help to prevent further charges. |
| Sentiment | Frustrated |
| Key issues | Double charge for order 55210; payment status shows failed |
| Action items | Verify payment status; check for duplicate charges; respond with findings |

**Summary judge:** 5/5 — accurate, concise, and actionable for a support agent.

**2. Generated email response**

> **Subject: Urgent Assistance Required for Duplicate Charge on Order 55210**
>
> Dear [Customer Name],
>
> I sincerely apologize for the inconvenience you have experienced regarding the duplicate charge for your order 55210. I understand how concerning this situation can be, especially with the payment status indicating a failure.
>
> Rest assured, I am here to assist you in resolving this issue promptly. Typically, if a payment has been deducted but the order is not confirmed, the amount is automatically reversed within 3 to 5 business days. If you do not see the reversal reflected in your account after this period, please provide me with the transaction reference number so that I can investigate this matter further for you.
>
> In the meantime, I recommend refraining from retrying the payment to avoid any potential duplicate charges.
>
> Thank you for your patience and understanding. Please let me know if there is anything else I can assist you with.
>
> Best regards,
> [Your Name]
> Customer Support Representative
> AuroraCart

**3. Response judge:** ✅ Passed (recommendation: approve)
- Scope check: 5/5 — correctly identified as an in-scope AuroraCart payment issue
- Grounded entirely in the stated policy (3–5 business day auto-reversal), no invented details or unsupported promises

## A design choice worth calling out: the scope check

Early runs surfaced a failure mode I hadn't anticipated: when a ticket described a problem with an unrelated third-party service (e.g. a food delivery complaint that had nothing to do with this company), the response generator didn't hesitate — it wrote a warm apology and offered a refund anyway. Instruction-following without boundary-awareness is a real risk once you're grounding generation in a policy document; the model will apply *a* policy even when it shouldn't apply *any* policy.

The fix was adding an explicit scope-check as the first evaluation criterion in the response judge (`src/evaluator.py`), which flags out-of-scope tickets as a critical failure and forces a `reject` recommendation rather than letting an off-policy response reach a customer. The `data/sample_tickets.csv` file includes one ticket designed to trigger this case (see the demo notebook).

## Getting started

```bash
git clone https://github.com/caitlyn-r/support-agent-with-judge.git
cd support-agent-with-judge
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your own OPENAI_API_KEY
```

Run the full pipeline on the sample dataset:

```bash
python -m src.pipeline
```

Or walk through it interactively in `demo/demo.ipynb`, which runs stage-by-stage and prints one ticket's full journey from raw text to reviewed draft email.

Output is written to `outputs/compiled_ticket_outputs.csv` (gitignored — generated locally when you run it).

## Repo structure

```
support-agent-with-judge/
├── src/
│   ├── config.py                    # env/config loading, model settings
│   ├── policies.py                  # company policy text used to ground responses
│   ├── summarizer.py                # stage 1
│   ├── evaluator.py                 # stages 2 & 4 (both LLM-as-judge calls)
│   ├── response_generator.py        # stage 3
│   ├── pipeline.py                  # orchestrates all four stages
│   └── utils.py                     # shared JSON-parsing helpers
├── data/
│   └── sample_tickets.csv           # synthetic ticket dataset
├── demo/
│   └── demo.ipynb                   # interactive walkthrough
├── outputs/                         # generated CSVs (gitignored)
│   └── compiled_ticket_outputs.csv  # example output from sample_tickets.csv
├── requirements.txt
└── .env.example
```

## Limitations & future work

- **No triage/routing step before summarization.** Right now every ticket goes through the full pipeline even when it's obviously out of scope, which is caught only at the final judge stage. A lightweight router upfront would save the wasted summarization + response-generation calls entirely.
- **Drafts, not sends.** This is intentionally a draft-and-review tool. The evaluation stages are a safety net for a human reviewer, not a substitute for one — I would not wire the response-generator output directly to an outbound email without a human approval step.
- **Confidence field is inconsistent.** The summarizer's `confidence` field mixes categorical and numeric-feeling outputs depending on the ticket; this should be constrained to a fixed enum (`high` / `medium` / `low`) in the prompt schema.
- **No structured logging/analytics layer.** The extracted `key_issues` and `action_items` fields would be genuinely useful aggregated across many tickets (e.g. spotting that 30% of negative-sentiment tickets mention the same root cause) — that's not built here, but the data's already in the right shape for it.

## Tech stack

Python · LangChain (`langchain-openai`) · OpenAI `gpt-4o-mini` · pandas
