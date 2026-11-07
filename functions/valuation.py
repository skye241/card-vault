"""Market value for a graded slab."""

from constant.grading_company import GradingCompany
from data.schema import GradedSlabSchema
from repository.market_api import calling_ebay, calling_psa


def get_market_value(slab_info: GradedSlabSchema) -> float:
    if slab_info.company.strip().upper() == GradingCompany.PSA:
        return calling_psa(slab_info)
    return calling_ebay(slab_info)
