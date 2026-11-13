import json
from datetime import date
from pathlib import Path

from data.schema import TCGGroup

_GROUPS_PATH = Path(__file__).resolve().parents[1] / "data" / "groups.json"
_groups_cache: list[TCGGroup] | None = None


def _pokemon_groups() -> list[TCGGroup]:
    global _groups_cache
    if _groups_cache is None:
        saved = json.loads(_GROUPS_PATH.read_text())
        _groups_cache = [
            TCGGroup(
                groupId=item["groupId"],
                name=item["name"],
                abbreviation=item.get("abbreviation") or "",
                publishedOn=date.fromisoformat(item["publishedOn"][:10]),
            )
            for item in saved["results"]
        ]
    return _groups_cache


def _plain(value: str) -> str:
    """Drop punctuation and the word Pokémon so 'XY - Evolutions' compares as 'xy evolutions'."""
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in value)
    return " ".join(part for part in cleaned.split() if part != "pokemon")


def _same_word(left: str, right: str) -> bool:
    if left == right:
        return True
    short, long = sorted((left, right), key=len)
    extra = long[len(short):]
    return len(short) >= 4 and long.startswith(short) and extra in {"s", "es"}


def _matches(collection_name: str, group_name: str) -> bool:
    left = _plain(collection_name)
    right = _plain(group_name)
    if not left or not right:
        return False
    if left in right or right in left:
        return True
    left_words = left.split()
    right_words = right.split()
    return all(any(_same_word(word, token) for token in right_words) for word in left_words)


def find_group(collection_name: str, year: str) -> TCGGroup:
    """Return the first Pokémon group from that year whose name overlaps the collection."""
    if not collection_name.strip() or not year.strip().isdigit():
        raise LookupError("Pokémon lookup needs a collection name and year")
    wanted_year = int(year)
    for group in _pokemon_groups():
        if group.publishedOn.year != wanted_year:
            continue
        if _matches(collection_name, group.name):
            return group
    raise LookupError("No Pokémon group matches this collection")
