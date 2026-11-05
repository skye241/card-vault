"""Resale quotes from TCGPlayer's near-mint market price.

The market price is what the card sells for, not what the owner paid.
Other conditions scale that price by a fixed resale factor. Those factors
are part of the quote, not a grade read from the photo.
"""

from __future__ import annotations

# Prefer the card's main printing. Reverse holofoil is a secondary finish
# and is used only when it is the only price TCGPlayer publishes.
VARIANT_PRIORITY = (
    "1stEditionHolofoil",
    "unlimitedHolofoil",
    "holofoil",
    "1stEditionNormal",
    "normal",
    "reverseHolofoil",
)

# Share of the near-mint resale price. Shown in the quote so the discount is explicit.
CONDITIONS: dict[str, float] = {
    "Near Mint": 1.0,
    "Lightly Played": 0.85,
    "Moderately Played": 0.70,
    "Heavily Played": 0.50,
}

DEFAULT_CONDITION = "Near Mint"

VARIANT_LABELS = {
    "1stEditionHolofoil": "1st edition holofoil",
    "unlimitedHolofoil": "Unlimited holofoil",
    "holofoil": "Holofoil",
    "1stEditionNormal": "1st edition",
    "normal": "Normal",
    "reverseHolofoil": "Reverse holofoil",
}


def choose_price(prices: dict | None) -> tuple[str, dict] | None:
    """Pick the resale bucket that represents the card's main printing."""
    if not prices:
        return None

    def market_of(bucket: dict) -> float | None:
        market = bucket.get("market")
        if market is None:
            return None
        return float(market)

    for variant in VARIANT_PRIORITY:
        bucket = prices.get(variant)
        if isinstance(bucket, dict) and market_of(bucket) is not None:
            return variant, bucket

    for variant, bucket in prices.items():
        if isinstance(bucket, dict) and market_of(bucket) is not None:
            return variant, bucket
    return None


def quote(market: float, condition: str) -> float:
    if condition not in CONDITIONS:
        raise ValueError(f"Unknown condition: {condition}")
    return round(float(market) * CONDITIONS[condition], 2)


def money(amount: float) -> str:
    return f"${amount:,.2f}"
