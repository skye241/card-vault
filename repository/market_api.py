
import os
from statistics import median

import requests
import streamlit as st

from data.schema import GradedSlabSchema
from functions.find_group import find_group
from functions.find_product import find_product
import regex as re


_EBAY_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
_EBAY_SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
_EBAY_SCOPE = "https://api.ebay.com/oauth/api_scope"
_POKEMON_CARDS_URL = "https://pokemon-tcg-api.p.rapidapi.com/cards"
_POKEMON_CATEGORY_ID = 3
_TCGCSV_HEADERS = {"User-Agent": "card-vault/0.1"}


def _env(name: str) -> str:
    value = st.secrets[name].strip()
    if not value:
        raise ValueError(f"{name} is not set")
    return value



def calling_pokemon_tcg(slab_info: GradedSlabSchema) -> dict:
    """Prices for one Pokémon card from the Pokémon TCG API."""
    group_id = _group_id(slab_info)
    product_id = _product_id(group_id, slab_info.card_name)
    body = _pokemon_get(_POKEMON_CARDS_URL, {
        "tcgplayer_id": product_id,
        "per_page": 10,
        "page": 1,
        "sort": "relevance",
    })
    cards = body.get("data") or []
    if not cards:
        raise LookupError(f"Pokémon TCG returned no card for tcgplayer_id {product_id}")
    return cards[0].get("prices") or {}

def _group_id(slab_info: GradedSlabSchema) -> int:
    return find_group(slab_info.collection_name, slab_info.year).groupId


def _product_id(group_id: int, card_name: str) -> int:
    name = card_name
    # name = re.sub(r'[^a-zA-Z0-9]', ' ', card_name)
    if not name:
        raise LookupError("Pokémon lookup needs a card name")
    body = _tcgcsv_get(f"https://tcgcsv.com/tcgplayer/{_POKEMON_CATEGORY_ID}/{group_id}/products")
    if body["results"] is not None:
        product = find_product(name, body["results"])
        print(product["productId"])
        return product["productId"]
    else:
        raise LookupError("No Pokémon cards in this group") 


def _tcgcsv_get(url: str) -> dict:
    response = requests.get(url, headers=_TCGCSV_HEADERS, timeout=30)
    if not response.ok:
        raise ValueError(f"TCGcsv {response.status_code}")
    return response.json()


def _words(value: str) -> list[str]:
    return [part for part in "".join(ch.lower() if ch.isalnum() else " " for ch in str(value or "")).split() if part]


def _pokemon_get(url: str, params: dict | None = None) -> dict:
    headers = {}
    api_key = _optional_env("POKEMON_TCG_API_KEY")
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


def _optional_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        from dotenv import load_dotenv
        load_dotenv()
        value = os.environ.get(name, "")
    if not value:
        try:
            value = st.secrets.get(name, "") or ""
        except Exception:
            value = ""
    return str(value).strip()


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
