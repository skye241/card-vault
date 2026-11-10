"""Run the shared scorer on GPT-4o mini through OpenRouter."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from functions.run_gpt import run_gpt
from test_suite.evaluate import evaluate_pipeline

PROMPT = (
    "Examine this trading card photo. Return only a JSON object with keys "
    "is_graded, company, grade, cert_number, card_name, year, collection_name, "
    "and variant. is_graded is true only when the card is in a professional "
    "grading slab. year is the four-digit year. collection_name is the set name. "
    "variant is the printed finish, such as Holo, Gold Star, Reverse Holo, "
    "Full Art, SIR, or SAR. Use an empty string when a field is not visible."
)


def predict(image_bytes: bytes) -> str:
    for attempt in range(6):
        try:
            return run_gpt(image_bytes, PROMPT)
        except Exception as exc:
            if "402" not in str(exc) or attempt == 5:
                raise
            time.sleep(8 * (attempt + 1))


if __name__ == "__main__":
    report = evaluate_pipeline("gpt-4o-mini", predict)
    print(report["record_accuracy"], report["field_accuracy"], report["seconds"])
