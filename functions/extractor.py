"""Read slab fields from a photo with GPT-4o mini."""

import json
import re

from data.schema import GradedSlabSchema
from functions.run_gpt import run_gpt
from functions.run_moondream import run_moondream

_PROMPT = (
    "Examine this trading card image. Is it encapsulated in a professional "
    "grading slab (PSA, Beckett, CGC, or SGC)? "
    "Return only a JSON object with keys is_graded, company, grade, card_name, "
    "year, and cert_number. year is the four-digit year printed on the card or slab. Cert_number is a 7-to-10-digit string of number."
    "If the card is raw or ungraded, set is_graded to false "
    "and leave the other fields as empty strings."
)


def extract_slab_info(image_bytes: bytes) -> GradedSlabSchema:
    # TODO: tighten the prompt once real slab photos are checked against the schema.
    #TODO: feature: bulk extract
    try:
#         reply = """```json
# {
#   "is_graded": true,
#   "company": "CGC",
#   "grade": "7",
#   "card_name": "Alakazam",
#   "year": "1999",
#   "cert_number": "6054872090"
# }
# ```"""
        
        reply = run_gpt(image_bytes, _PROMPT)
        # print(reply)
    except (OSError, ValueError) as error:
        print(f"Error! {error}")
        return _empty_schema()
    return _schema_from_reply(reply)


def _schema_from_reply(reply: str) -> GradedSlabSchema:
    match = re.search(r"\{.*\}", reply, re.DOTALL)
    if not match:
        return _empty_schema()
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return _empty_schema()
    return GradedSlabSchema(
        is_graded=bool(data.get("is_graded")),
        company=str(data.get("company") or ""),
        grade=str(data.get("grade") or ""),
        card_name=str(data.get("card_name") or ""),
        year=str(data.get("year") or ""),
        cert_number=str(data.get("cert_number") or ""),
    )


def _empty_schema() -> GradedSlabSchema:
    return GradedSlabSchema(
        is_graded=False,
        company="",
        grade="",
        card_name="",
        year="",
        cert_number="",
    )
