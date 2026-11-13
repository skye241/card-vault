"""Pokémon TCG API on RapidAPI: one card, and a year of daily prices."""

from datetime import date, timedelta

import requests

from card_vault.domain.models import GradedSlab, PriceHistory
from card_vault.domain.pricing import history_chart
from card_vault.infrastructure.groups import find_group
from card_vault.infrastructure.settings import setting
from card_vault.infrastructure.tcgcsv import find_product_id

_CARDS_URL = "https://pokemon-tcg-api.p.rapidapi.com/cards"
_HISTORY_URL = "https://pokemon-tcg-api.p.rapidapi.com/history-prices"


def find_pokemon_card(slab: GradedSlab) -> dict:
    """Card record for this slab, including ``id`` and ``prices``.

    The set comes from the local group catalog. The product id comes from
    TCGcsv and is sent as ``tcgplayer_id``.

    Raises:
        LookupError: No set, product, or card was found.
    """
    group = find_group(slab.collection_name, slab.year)
    product_id = find_product_id(group.group_id, slab.card_name)
    body = _get(_CARDS_URL, {
        "tcgplayer_id": product_id,
        "per_page": 10,
        "page": 1,
        "sort": "relevance",
    })
    cards = body.get("data") or []
    if not cards:
        raise LookupError(f"Pokémon TCG returned no card for tcgplayer_id {product_id}")
    return cards[0]


def price_history(card_id: int) -> PriceHistory:
    """Daily Cardmarket and TCGPlayer prices for the past year.

    Pages are 30 days. English Cardmarket prices are requested with ``lang=en``.
    """
    start = date.today() - timedelta(days=365)
    days: dict[str, dict] = {}
    page = 1
    while page <= 20:
        body = _get(_HISTORY_URL, {
            "id": card_id,
            "date_from": start.isoformat(),
            "date_to": date.today().isoformat(),
            "page": page,
            "sort": "asc",
            "lang": "en",
        })
        days.update(body.get("data") or {})
        paging = body.get("paging") or {}
        if page >= int(paging.get("total") or page):
            break
        page += 1
    rows, note = history_chart(days)
    return PriceHistory(rows=rows, note=note)


def _get(url: str, params: dict | None = None) -> dict:
    headers = {}
    api_key = setting("POKEMON_TCG_API_KEY")
    if api_key:
        headers["X-RapidAPI-Key"] = api_key
    response = None
    for _ in range(2):
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code < 500:
            break
    if response is None or not response.ok:
        status = response.status_code if response is not None else "no response"
        raise ValueError(f"Pokémon TCG {status}")
    return response.json()
