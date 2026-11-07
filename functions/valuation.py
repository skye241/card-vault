"""Market value for a graded slab."""

from data.schema import GradedSlabSchema
from repository.market_api import calling_ebay


def get_market_value(slab_info: GradedSlabSchema) -> float:
    return calling_ebay(slab_info)
