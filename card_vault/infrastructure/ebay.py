"""Median asking price from the eBay Browse API. These are listings, not sold comps."""

from statistics import median

import requests

from card_vault.domain.models import GradedSlab
from card_vault.infrastructure.settings import setting

_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
_SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
_SCOPE = "https://api.ebay.com/oauth/api_scope"


def median_asking_price(slab: GradedSlab) -> float:
    """Median of up to 10 current listings for year, name, company, and grade.

    Raises:
        ValueError: The query is empty, or eBay returns no prices.
    """
    query = " ".join(
        part.strip()
        for part in (slab.year, slab.card_name, slab.company, slab.grade)
        if part and part.strip()
    )
    if not query:
        raise ValueError("eBay lookup needs a card name, company, or grade")
    response = requests.get(
        _SEARCH_URL,
        headers={
            "Authorization": f"Bearer {_token()}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        },
        params={"q": query, "limit": "10", "itemFilter": "(name=SoldItemsOnly, value=true)"},
        timeout=30,
    )
    if not response.ok:
        raise ValueError(f"eBay {response.status_code}: {response.text}")
    prices = []
    for item in response.json().get("itemSummaries") or []:
        value = (item.get("price") or {}).get("value")
        if value not in (None, ""):
            prices.append(float(value))
    if not prices:
        raise ValueError("eBay returned no prices")
    return float(median(prices))


def _token() -> str:
    client_id = setting("EBAY_CLIENT_ID", required=True)
    client_secret = setting("EBAY_CLIENT_SECRET", required=True)
    response = requests.post(
        _TOKEN_URL,
        auth=(client_id, client_secret),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials", "scope": _SCOPE},
        timeout=30,
    )
    if not response.ok:
        raise ValueError(f"eBay token {response.status_code}: {response.text}")
    token = response.json().get("access_token")
    if not token:
        raise ValueError("eBay token response had no access_token")
    return token
