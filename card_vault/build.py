"""Build the local reference vault: cards, resale prices, and embeddings."""

from __future__ import annotations

import sys

from card_vault.catalog import (
    _session,
    collect_cards,
    download_images,
    write_catalog,
)
from card_vault.identify import Identifier
from card_vault.paths import DATA
from card_vault.samples import load_rgb, write_samples


def build_vault() -> dict:
    session = _session()
    print("Collecting higher-value Pokémon cards…")
    cards = collect_cards(session)
    if len(cards) < 8:
        raise SystemExit(
            f"Only found {len(cards)} priced cards. The Pokémon TCG API did not return enough data."
        )
    print(f"Downloading {len(cards)} card images…")
    cards = download_images(session, cards)
    if len(cards) < 8:
        raise SystemExit(f"Only downloaded {len(cards)} card images.")

    print("Embedding artwork…")
    identifier = Identifier.build(cards)
    _check_reference_matches(identifier)

    samples = write_samples(cards)
    _check_samples(identifier, samples)
    catalog = write_catalog(cards, samples)
    print(f"Vault ready: {len(cards)} cards, {len(samples)} sample photos.")
    return catalog


def _check_reference_matches(identifier: Identifier) -> None:
    """Each official image should retrieve itself, with daylight to the runner-up."""
    worst = []
    for card in identifier.cards:
        hits = identifier.search(load_rgb(DATA / card["image"]))
        top = hits[0]
        worst.append((top["margin"], top["id"] == card["id"], card["id"], top))
        if top["id"] != card["id"]:
            raise SystemExit(
                f"Reference image {card['id']} matched {top['id']} ({top['name']}) instead of itself."
            )
    worst.sort(key=lambda item: item[0])
    margin, _, card_id, top = worst[0]
    print(
        f"Tightest self-match: {card_id} margin {margin:.3f} "
        f"over the next card at {top['score'] - top['margin']:.3f}"
    )
    if margin < 0.02:
        print("Warning: two reference cards look very similar. Quotes for those need a human confirm.")


def _check_samples(identifier: Identifier, samples: list[dict]) -> None:
    failed = []
    for sample in samples:
        hits = identifier.search(load_rgb(DATA / sample["file"]))
        top = hits[0]
        print(
            f"sample {sample['id']} -> {top['id']} {top['name']} "
            f"similarity {top['score']:.3f} margin {top['margin']:.3f}"
        )
        if top["id"] != sample["id"]:
            failed.append((sample["id"], top["id"], top["name"]))
    if failed:
        raise SystemExit(f"Phone-style samples matched the wrong card: {failed}")


def main() -> None:
    try:
        build_vault()
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == "__main__":
    main()
