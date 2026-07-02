"""
End-to-end orchestration: load tickets -> summarize -> evaluate summary ->
generate email -> evaluate email -> export a single compiled table.
"""

from pathlib import Path

import pandas as pd

from .summarizer import generate_ticket_summary
from .evaluator import generate_summary_evaluation, evaluate_email_response
from .response_generator import generate_email_response, EMAIL_RESPONSE_SYSTEM_MESSAGE

EVAL_COLUMNS = [
    "factual_accuracy", "completeness", "conciseness",
    "actionability", "tone_and_clarity", "overall_score", "justification",
]


def run_pipeline(input_csv: str, output_csv: str = "outputs/compiled_ticket_outputs.csv") -> pd.DataFrame:
    df = pd.read_csv(input_csv)

    expected_columns = ["ticket_id", "ticket_text"]
    missing = [c for c in expected_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected column(s): {missing}")

    print(f"Loaded {len(df)} tickets.")

    # Stage 1: Summarization
    summary_results = df["ticket_text"].apply(generate_ticket_summary)
    df = pd.concat([df, pd.json_normalize(summary_results)], axis=1)

    # Stage 2: Summary evaluation
    eval_results = df.apply(
        lambda row: generate_summary_evaluation(row["ticket_text"], row["summary"]), axis=1
    )
    df = pd.concat([df, pd.json_normalize(eval_results)], axis=1)

    # Stage 3: Email response generation
    df["email_response"] = df.apply(
        lambda row: generate_email_response(row["summary"], row[EVAL_COLUMNS].to_dict()),
        axis=1,
    )

    # Stage 4: Email response evaluation
    response_eval_results = df.apply(
        lambda row: evaluate_email_response(
            row["ticket_text"], row["summary"], row[EVAL_COLUMNS].to_dict(),
            row["email_response"], EMAIL_RESPONSE_SYSTEM_MESSAGE,
        ),
        axis=1,
    )
    response_eval_df = pd.json_normalize(response_eval_results)
    response_eval_df.columns = [f"email_eval_{c.replace('.', '_')}" for c in response_eval_df.columns]
    df = pd.concat([df, response_eval_df], axis=1)

    # Compile and export
    compiled = df[["ticket_id", "ticket_text", "summary", "email_response"]].rename(columns={
        "ticket_id": "Ticket ID",
        "ticket_text": "Raw Ticket Text",
        "summary": "Generated Summary",
        "email_response": "Generated Response",
    })

    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    compiled.to_csv(output_path, index=False)
    print(f"Pipeline complete. Consolidated output exported to {output_path}")

    return df


if __name__ == "__main__":
    run_pipeline(input_csv="data/sample_tickets.csv")
