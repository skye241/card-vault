"""Grading companies the insurance check accepts, and how a grade number is read."""

import re
from enum import Enum


class GradingCompany(str, Enum):
    """Companies a slab may be quoted for. Beckett on a label is stored as BGS."""

    PSA = "PSA"
    CGC = "CGC"
    SGC = "SGC"
    BECKETT = "Beckett"
    TAG = "TAG"
    ACE = "ACE"
    BGS = "BGS"


def grade_number(grade: str) -> float | None:
    """First number in a grade label. ``PSA 10`` and ``9.5`` both parse."""
    match = re.search(r"\d+(?:\.\d+)?", str(grade))
    return float(match.group()) if match else None
