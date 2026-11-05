"""Download a reference vault of higher-value Pokémon cards and their resale prices."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone

import requests

from card_vault.paths import API_CACHE, CATALOG_PATH, EMBEDDINGS_PATH, IMAGES
from card_vault.pricing import choose_price

API = "https://api.pokemontcg.io/v2"
INDEX_VERSION = 1

# Cards people actually travel with and would insure. The search adds the
# expensive printings; these ids keep the original Base Set holos in the vault
# even if a search page comes back incomplete.
SEED_IDS = (
    "base1-1",
    "base1-2",
    "base1-4",
    "base1-6",
    "base1-8",
    "base1-10",
    "base1-15",
)

NAMES = (
    "charizard",
    "blastoise",
    "venusaur",
    "pikachu",
    "mew",
    "mewtwo",
    "umbreon",
    "espeon",
    "sylveon",
    "rayquaza",
    "lugia",
    "ho-oh",
    "gengar",
    "dragonite",
    "gyarados",
    "alakazam",
    "snorlax",
    "garchomp",
    "greninja",
    "lucario",
)

PER_NAME = 3
MIN_MARKET = 25.0
MAX_CARDS = 48

SAMPLE_IDS = ("base1-4", "base1-2", "base1-15")


def _session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = "card-vault-prototype"
    api_key = os.environ.get("POKEMONTCG_API_KEY")
    if api_key:
        session.headers["X-Api-Key"] = api_key
    return session


def _api_get(session: requests.Session, path: str, params: dict | None = None) -> dict:
    url = f"{API}{path}"
    last_error = "no response"
    for attempt in range(4):
        try:
            response = session.get(url, params=params, timeout=45)
            if response.status_code == 200:
                return response.json()
            last_error = f"HTTP {response.status_code}: {response.text[:180]}"
        except requests.RequestException as exc:
            last_error = str(exc)
        time.sleep(0.7 * (attempt + 1))
    raise RuntimeError(f"Pokémon TCG API failed for {path}: {last_error}")


def _cache_path(key: str):
    API_CACHE.mkdir(parents=True, exist_ok=True)
    safe = key.replace("/", "_").replace(" ", "_")
    return API_CACHE / f"{safe}.json"


def fetch_card(session: requests.Session, card_id: str, use_cache: bool = True) -> dict | None:
    cache = _cache_path(f"card-{card_id}")
    if use_cache and cache.exists():
        return json.loads(cache.read_text())
    try:
        payload = _api_get(session, f"/cards/{card_id}")
    except RuntimeError as exc:
        print(f"skip {card_id}: {exc}")
        return None
    card = payload.get("data")
    if card:
        cache.write_text(json.dumps(card))
    return card


def search_name(session: requests.Session, name: str, use_cache: bool = True) -> list[dict]:
    cache = _cache_path(f"search-{name}")
    if use_cache and cache.exists():
        return json.loads(cache.read_text())
    cards: list[dict] = []
    page = 1
    try:
        while page <= 3:
            payload = _api_get(
                session,
                "/cards",
                {"q": f"name:{name}", "page": page, "pageSize": 250},
            )
            batch = payload.get("data") or []
            cards.extend(batch)
            total = int(payload.get("totalCount") or len(cards))
            if len(cards) >= total or not batch:
                break
            page += 1
    except RuntimeError as exc:
        print(f"search {name} failed: {exc}")
        return []
    cache.write_text(json.dumps(cards))
    return cards


def _name_matches(card_name: str, query: str) -> bool:
    folded = card_name.lower().replace("δ", " delta")
    if query == "ho-oh":
        return "ho-oh" in folded or "hooh" in folded
    tokens = []
    current = []
    for char in folded:
        if char.isalpha() or char.isdigit():
            current.append(char)
        elif current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return query in tokens


def _record_from_api(card: dict, image_name: str | None = None) -> dict | None:
    chosen = choose_price((card.get("tcgplayer") or {}).get("prices"))
    if not chosen:
        return None
    variant, bucket = chosen
    market = bucket.get("market")
    if market is None:
        return None
    images = card.get("images") or {}
    image_url = images.get("large") or images.get("small")
    if not image_url:
        return None
    return {
        "id": card["id"],
        "name": card.get("name") or card["id"],
        "supertype": card.get("supertype") or "",
        "set_name": (card.get("set") or {}).get("name") or "",
        "set_id": (card.get("set") or {}).get("id") or "",
        "number": str(card.get("number") or ""),
        "rarity": card.get("rarity") or "",
        "image_url": image_url,
        "image": image_name,
        "tcgplayer_url": (card.get("tcgplayer") or {}).get("url") or "",
        "price_updated_at": (card.get("tcgplayer") or {}).get("updatedAt") or "",
        "price_variant": variant,
        "market": float(market),
        "low": bucket.get("low"),
        "mid": bucket.get("mid"),
    }


def collect_cards(session: requests.Session, use_cache: bool = True) -> list[dict]:
    by_id: dict[str, dict] = {}

    for card_id in SEED_IDS:
        raw = fetch_card(session, card_id, use_cache=use_cache)
        if not raw:
            continue
        record = _record_from_api(raw)
        if record:
            by_id[record["id"]] = record
            print(f"seed {record['id']} {record['name']} ${record['market']:.2f}")

    for name in NAMES:
        ranked: list[dict] = []
        for raw in search_name(session, name, use_cache=use_cache):
            supertype = (raw.get("supertype") or "").lower()
            if supertype and supertype not in {"pokémon", "pokemon"}:
                continue
            if not _name_matches(raw.get("name") or "", name):
                continue
            record = _record_from_api(raw)
            if not record or record["market"] < MIN_MARKET:
                continue
            ranked.append(record)
        ranked.sort(key=lambda card: card["market"], reverse=True)
        for record in ranked[:PER_NAME]:
            by_id.setdefault(record["id"], record)
            print(f"  {name}: {record['id']} {record['name']} ${record['market']:.2f}")

    seeds = [by_id[card_id] for card_id in SEED_IDS if card_id in by_id]
    rest = [card for card_id, card in by_id.items() if card_id not in SEED_IDS]
    rest.sort(key=lambda card: card["market"], reverse=True)
    room = max(0, MAX_CARDS - len(seeds))
    return seeds + rest[:room]


def download_images(session: requests.Session, cards: list[dict]) -> list[dict]:
    IMAGES.mkdir(parents=True, exist_ok=True)
    for stale in IMAGES.glob("*"):
        stale.unlink()
    kept: list[dict] = []
    for card in cards:
        dest = IMAGES / f"{card['id']}.png"
        last_error = "no response"
        payload = b""
        for attempt in range(3):
            try:
                response = session.get(card["image_url"], timeout=60)
                if response.status_code == 200 and response.content:
                    payload = response.content
                    break
                last_error = f"HTTP {response.status_code}"
            except requests.RequestException as exc:
                last_error = str(exc)
            time.sleep(0.5 * (attempt + 1))
        if not payload:
            print(f"image skip {card['id']}: {last_error}")
            continue
        dest.write_bytes(payload)
        card = dict(card)
        card["image"] = f"images/{card['id']}.png"
        kept.append(card)
    return kept


def write_catalog(cards: list[dict], samples: list[dict]) -> dict:
    catalog = {
        "index_version": INDEX_VERSION,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "source": "pokemontcg.io TCGPlayer market price",
        "currency": "USD",
        "cards": cards,
        "samples": samples,
    }
    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2))
    return catalog


def load_catalog() -> dict | None:
    if not CATALOG_PATH.exists() or not EMBEDDINGS_PATH.exists():
        return None
    catalog = json.loads(CATALOG_PATH.read_text())
    if catalog.get("index_version") != INDEX_VERSION:
        return None
    return catalog


def save_catalog(catalog: dict) -> None:
    CATALOG_PATH.write_text(json.dumps(catalog, indent=2))


def refresh_prices(catalog: dict) -> dict:
    """Update resale prices without rebuilding the image index."""
    session = _session()
    updated = 0
    for card in catalog["cards"]:
        raw = fetch_card(session, card["id"], use_cache=False)
        if not raw:
            continue
        record = _record_from_api(raw, image_name=card.get("image"))
        if not record:
            continue
        card.update(
            {
                "market": record["market"],
                "low": record["low"],
                "mid": record["mid"],
                "price_variant": record["price_variant"],
                "price_updated_at": record["price_updated_at"],
                "tcgplayer_url": record["tcgplayer_url"],
            }
        )
        updated += 1
    catalog["prices_refreshed_at"] = datetime.now(timezone.utc).isoformat()
    save_catalog(catalog)
    print(f"refreshed {updated} prices")
    return catalog
