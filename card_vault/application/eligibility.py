"""Decide whether a slab photo can be quoted."""

from card_vault.domain.grading import GradingCompany
from card_vault.domain.models import GradedSlab


def rejection_reason(slab: GradedSlab) -> str | None:
    """Why this slab cannot be quoted, or None when the quote may continue.

    A card the reader marks as not Pokémon is unsupported before the graded
    checks. A missing game answer still goes through those checks.
    """
    if slab.is_pokemon is False:
        return "This card is unsupported for now"
    if not slab.is_graded:
        return "Ineligible for Insurance (Ungraded Card)"
    if slab.card_name == "":
        return "Ineligible for Insurance (Unable to verify slab - card name is missing)"
    if slab.company not in GradingCompany:
        return "Ineligible for Insurance (Unverified grading company)"
    return None
