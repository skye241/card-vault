"""Turn a slab photo into a :class:`~card_vault.domain.models.GradedSlab`."""

import json
import re

from card_vault.domain.models import GradedSlab
from card_vault.infrastructure.openrouter import run_gpt

_PROMPT = (
    "Examine this trading card image. Is it encapsulated in a professional "
    "grading slab (PSA, Beckett, CGC, SGC, or ACE)? "
    "Return only a JSON object with keys is_graded, is_pokemon, company, grade, card_name, card_number "
    "year, collection_name, and cert_number. is_pokemon is true only for a Pokémon Trading Card Game card, "
    "and false for sports and every other game. year is the four-digit year printed on the card or slab. "
    "collection_name is the set name, similar to TCG Player Group name. Cert_number is a 6-to-10-digit string of number."
    "If the card is raw or ungraded, set is_graded to false "
    "and leave the other fields as empty strings."
)


def read_slab(image_bytes: bytes) -> GradedSlab:
    """Read one photo. A failed read returns an empty, ungraded slab."""
    try:
        reply = run_gpt(image_bytes, _PROMPT)
    except (OSError, ValueError) as error:
        print(f"Error! {error}")
        return empty_slab()
    return slab_from_reply(reply)


def slab_from_reply(reply: str) -> GradedSlab:
    """Parse the model's JSON. Beckett is stored as BGS."""
    match = re.search(r"\{.*\}", reply, re.DOTALL)
    if not match:
        return empty_slab()
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return empty_slab()
    company = str(data.get("company") or "")
    if company == "Beckett":
        company = "BGS"
    return GradedSlab(
        is_graded=bool(data.get("is_graded")),
        is_pokemon=_as_bool(data.get("is_pokemon")),
        company=company,
        grade=str(data.get("grade") or ""),
        card_name=str(data.get("card_name") or ""),
        card_number=str(data.get("card_number") or ""),
        year=str(data.get("year") or ""),
        collection_name=str(data.get("collection_name") or ""),
        cert_number=str(data.get("cert_number") or ""),
    )


def empty_slab() -> GradedSlab:
    """A slab the reader could not fill in."""
    return GradedSlab(
        is_graded=False,
        is_pokemon=None,
        company="",
        grade="",
        card_name="",
        card_number="",
        year="",
        collection_name="",
        cert_number="",
    )


def _as_bool(value) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.casefold().strip()
        if text in {"true", "yes"}:
            return True
        if text in {"false", "no"}:
            return False
    return None
