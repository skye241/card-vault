"""Compare a slab's printed names with TCGplayer set and product names."""


def plain(value: str) -> str:
    """Lowercase, drop punctuation, and drop the word Pokémon.
    """
    cleaned = "".join(character.lower() if character.isalnum() else " " for character in value)
    return " ".join(part for part in cleaned.split() if part != "pokemon")


def _same_word(left: str, right: str) -> bool:
    if left == right:
        return True
    short, long = sorted((left, right), key=len)
    extra = long[len(short):]
    return len(short) >= 4 and long.startswith(short) and extra in {"s", "es"}


def collection_matches(collection_name: str, group_name: str) -> bool:
    """True when the printed set name and the catalog set name refer to one set.

    A name may contain the other. Otherwise every collection word must equal a
    catalog word, or differ only by a trailing s/es.
    """
    left = plain(collection_name)
    right = plain(group_name)
    if not left or not right:
        return False
    if left in right or right in left:
        return True
    left_words = left.split()
    right_words = right.split()
    return all(any(_same_word(word, token) for token in right_words) for word in left_words)


def product_matches(card_name: str, product_name: str) -> bool:
    """True when the card name appears inside the TCGplayer product name."""
    return card_name.casefold() in product_name.casefold()
