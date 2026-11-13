"""Price a graded Pokémon slab."""

from card_vault.domain.models import GradedSlab, Quote
from card_vault.domain.pricing import select_price
from card_vault.infrastructure.ebay import median_asking_price
from card_vault.infrastructure.pokemon_api import find_pokemon_card


def quote_slab(slab: GradedSlab) -> Quote:
    """Return a market quote for one slab.

    The Pokémon card is resolved first and its graded prices are selected.
    When that lookup or those prices fail, the quote is the median of current
    eBay asking prices. A card the reader marked as not Pokémon is refused
    before either lookup. A successful Pokémon lookup keeps the card id so the
    caller can load price history, including when the number itself came from eBay.
    """
    if slab.is_pokemon is False:
        raise LookupError("This card is unsupported for now")
    card = None
    try:
        card = find_pokemon_card(slab)
        amount, source = select_price(card.get("prices") or {}, slab.company, slab.grade)
        return Quote(amount=amount, source=source, card_id=card.get("id"))
    except LookupError:
        card_id = card.get("id") if card else None
        return Quote(amount=median_asking_price(slab), source="Median eBay asking price", card_id=card_id)
