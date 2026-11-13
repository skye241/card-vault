"""Market value for a graded slab."""

import re

from data.schema import GradedSlabSchema
from repository.market_api import calling_pokemon_tcg, calling_ebay

_SOURCES = ("ebay", "cardmarket", "tcg_player")
_COMPANY_RANK = ("tag", "ace", "bgs", "sgc", "cgc", "psa")
_GRADE_LIMIT = 2


def get_market_value(slab_info: GradedSlabSchema) -> tuple[float, str]:
    try:
        if slab_info.is_pokemon is False:
            raise LookupError("This card is unsupported for now")
        prices = calling_pokemon_tcg(slab_info)
        grade = _grade_number(slab_info.grade)
        companies = _company_order(slab_info.company)
        for source in _SOURCES:
            block = prices.get(source) or {}
            chosen = _graded_price(block.get("graded") or {}, companies, grade)
            if chosen is None:
                continue
            value, company, used_grade = chosen
            currency = block.get("currency") or "USD"
            return value, f"{_source_name(source)} {company.upper()} {used_grade:g} ({currency})"
        average = (prices.get("cardmarket") or {}).get("7d_average")
        if average not in (None, ""):
            currency = (prices.get("cardmarket") or {}).get("currency") or "EUR"
            return float(average), f"Cardmarket 7-day average ({currency})"
    except LookupError:
        return calling_ebay(slab_info), "Median eBay asking price"

    

def _graded_price(graded: dict, companies: list[str], grade: float | None) -> tuple[float, str, float] | None:
    tables = {str(name).casefold(): block for name, block in graded.items() if isinstance(block, dict)}
    for company in companies:
        listed = _listed_grades(tables.get(company) or {}, company)
        if not listed or grade is None:
            continue
        exact = [item for item in listed if item[0] == grade]
        if exact:
            return exact[0][1], company, exact[0][0]
        closest = min(listed, key=lambda item: (abs(item[0] - grade), -item[0]))
        if abs(closest[0] - grade) <= _GRADE_LIMIT:
            return closest[1], company, closest[0]
    return None


def _listed_grades(block: dict, company: str) -> list[tuple[float, float]]:
    listed = []
    for key, raw in block.items():
        number = _grade_number(str(key).casefold().removeprefix(company))
        value = _amount(raw)
        if number is None or value is None:
            continue
        listed.append((number, value))
    return listed


def _company_order(company: str) -> list[str]:
    match = company.casefold().strip()
    if match == "beckett":
        match = "bgs"
    order = [match] if match in _COMPANY_RANK else []
    order.extend(name for name in _COMPANY_RANK if name not in order)
    return order


def _grade_number(grade: str) -> float | None:
    match = re.search(r"\d+(?:\.\d+)?", str(grade))
    return float(match.group()) if match else None


def _amount(raw) -> float | None:
    if isinstance(raw, dict):
        raw = raw.get("median_price")
    if raw in (None, ""):
        return None
    return float(raw)


def _source_name(source: str) -> str:
    return {"ebay": "eBay", "cardmarket": "Cardmarket", "tcg_player": "TCGPlayer"}.get(source, source)
