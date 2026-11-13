"""Pokémon sets saved from TCGcsv at ``data/groups.json``."""

import json
from datetime import date
from pathlib import Path

from card_vault.domain.matching import collection_matches
from card_vault.domain.models import SetGroup

_GROUPS_PATH = Path(__file__).resolve().parents[2] / "data" / "groups.json"
_groups_cache: list[SetGroup] | None = None


def find_group(collection_name: str, year: str) -> SetGroup:
    """First set from that publication year whose name overlaps the collection.

    Raises:
        LookupError: The collection or year is missing, or no set matches.
    """
    if not collection_name.strip() or not year.strip().isdigit():
        raise LookupError("Pokémon lookup needs a collection name and year")
    wanted_year = int(year)
    for group in _groups():
        if group.published_on.year != wanted_year:
            continue
        if collection_matches(collection_name, group.name):
            return group
    raise LookupError("No Pokémon group matches this collection")


def _groups() -> list[SetGroup]:
    global _groups_cache
    if _groups_cache is None:
        saved = json.loads(_GROUPS_PATH.read_text())
        _groups_cache = [
            SetGroup(
                group_id=item["groupId"],
                name=item["name"],
                abbreviation=item.get("abbreviation") or "",
                published_on=date.fromisoformat(item["publishedOn"][:10]),
            )
            for item in saved["results"]
        ]
    return _groups_cache
