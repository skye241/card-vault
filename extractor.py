"""Read slab fields from a photo with Florence-2 OCR."""

import re

from schema import GradedSlabSchema
from run_florence import run_florence_task

_COMPANIES = ("PSA", "BGS", "CGC", "SGC")


def extract_slab_info(image_bytes: bytes) -> GradedSlabSchema:
    # Florence <OCR> reads the label text. It does not take a natural-language prompt.
    parsed = run_florence_task(image_bytes, "<MORE_DETAILED_CAPTION>")
    text = parsed.get("<OCR>", "") if isinstance(parsed, dict) else ""
    if not isinstance(text, str) or not text.strip():
        return GradedSlabSchema(
            is_graded=False,
            company="",
            grade="",
            card_name="",
            cert_number="",
        )
    return _schema_from_ocr(text)


def _schema_from_ocr(text: str) -> GradedSlabSchema:
    # TODO: replace this label scan with a stricter read of the slab header.
    
    print(text)
    upper = text.upper()
    company = next((name for name in _COMPANIES if name in upper), "")
    cert_match = re.search(r"\b\d{7,10}\b", text)
    grade_match = re.search(r"\b(?:GRADE|GEM[-\s]?MT|MINT)\s*(10|[1-9](?:\.5)?)\b", upper)
    return GradedSlabSchema(
        is_graded=bool(company),
        company=company,
        grade=grade_match.group(1) if grade_match else "",
        card_name="",
        cert_number=cert_match.group(0) if cert_match else "",
    )
