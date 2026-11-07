
import os
from statistics import median

import requests
from dotenv import load_dotenv

from data.schema import GradedSlabSchema

load_dotenv()

_EBAY_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
_EBAY_SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
_EBAY_SCOPE = "https://api.ebay.com/oauth/api_scope"


def _env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"{name} is not set")
    return value



def calling_ebay(slab_info: GradedSlabSchema) -> float:
    """Median current asking price from eBay Browse search. These are listings, not sold comps."""
    ###TODO: Stricter algorithm to determine valuation
    query = " ".join(
        part.strip()
        for part in (slab_info.year, slab_info.card_name, slab_info.company, slab_info.grade)
        if part and part.strip()
    )
    if not query:
        raise ValueError("eBay lookup needs a card name, company, or grade")
    token = _ebay_token()
    response = requests.get(
        _EBAY_SEARCH_URL,
        headers={
            "Authorization": f"Bearer {token}",
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


def _ebay_token() -> str:
    client_id = _env("EBAY_CLIENT_ID")
    client_secret = _env("EBAY_CLIENT_SECRET")
    response = requests.post(
        _EBAY_TOKEN_URL,
        auth=(client_id, client_secret),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials", "scope": _EBAY_SCOPE},
        timeout=30,
    )
    if not response.ok:
        raise ValueError(f"eBay token {response.status_code}: {response.text}")
    token = response.json().get("access_token")
    if not token:
        raise ValueError("eBay token response had no access_token")
    return token
