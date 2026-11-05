"""Stub market value. Replace the return value with an eBay query."""

from schema import GradedSlabSchema


def get_market_value(slab_info: GradedSlabSchema) -> float:
    # TODO: query the eBay API using company, grade, card_name, and cert_number.
    return 150.00
