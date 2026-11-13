"""Run the shared scorer on local Moondream."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from functions.run_moondream import run_moondream
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
    print("Start evaluation")
    return run_moondream(image_bytes, PROMPT)


if __name__ == "__main__":
    report = evaluate_pipeline("moondream", predict)
    print(report["record_accuracy"], report["seconds"])
