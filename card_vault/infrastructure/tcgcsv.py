"""TCGplayer product lists served by tcgcsv.com. Pokémon is category 3."""

import requests

from card_vault.domain.matching import product_matches

_CATEGORY_ID = 3
_HEADERS = {"User-Agent": "card-vault/0.1"}


def find_product_id(group_id: int, card_name: str) -> int:
    """TCGplayer product id for a card name inside one set.

    Raises:
        LookupError: The name is blank, the set has no products, or none match.
    """
    if not card_name.strip():
        raise LookupError("Pokémon lookup needs a card name")
    body = _get(f"https://tcgcsv.com/tcgplayer/{_CATEGORY_ID}/{group_id}/products")
    products = body.get("results")
    if products is None:
        raise LookupError("No Pokémon cards in this group")
    for product in products:
        if product_matches(card_name, product.get("name") or ""):
            return int(product["productId"])
    raise LookupError("No Pokémon cards matches this name")


def _get(url: str) -> dict:
    response = requests.get(url, headers=_HEADERS, timeout=30)
    if not response.ok:
        raise ValueError(f"TCGcsv {response.status_code}")
    return response.json()
