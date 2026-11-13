"""Choose one graded price, then shape a year of daily prices for the chart."""

from card_vault.domain.grading import grade_number

_SOURCES = ("ebay", "cardmarket", "tcg_player")
_COMPANY_RANK = ("tag", "ace", "bgs", "sgc", "cgc", "psa")
_GRADE_LIMIT = 2
_SOURCE_NAMES = {"ebay": "eBay", "cardmarket": "Cardmarket", "tcg_player": "TCGPlayer"}
_CARDMARKET_SERIES = (
    ("cm_low", "Cardmarket"),
    ("cm_low_de", "Cardmarket DE"),
    ("cm_low_fr", "Cardmarket FR"),
    ("cm_low_es", "Cardmarket ES"),
    ("cm_low_it", "Cardmarket IT"),
)


def company_order(company: str) -> list[str]:
    """Slab company first, then TAG, ACE, BGS, SGC, CGC, PSA.

    Beckett is looked up as BGS. A company outside that list is skipped and the
    ranking is used on its own.
    """
    match = company.casefold().strip()
    if match == "beckett":
        match = "bgs"
    order = [match] if match in _COMPANY_RANK else []
    order.extend(name for name in _COMPANY_RANK if name not in order)
    return order


def select_price(prices: dict, company: str, grade: str) -> tuple[float, str]:
    """Pick a graded price, then Cardmarket's 7-day average.

    Sources are tried in order: eBay, Cardmarket, TCGPlayer. Inside a source,
    companies follow :func:`company_order`. Inside a company, the exact grade
    wins. A missing grade may use the closest listed grade when it is at most
    2 points away. A wider gap skips that company.

    Raises:
        LookupError: No graded price and no 7-day average are present.
    """
    wanted = grade_number(grade)
    companies = company_order(company)
    for source in _SOURCES:
        block = prices.get(source) or {}
        chosen = _graded_price(block.get("graded") or {}, companies, wanted)
        if chosen is None:
            continue
        value, used_company, used_grade = chosen
        currency = block.get("currency") or "USD"
        label = f"{_SOURCE_NAMES.get(source, source)} {used_company.upper()} {used_grade:g} ({currency})"
        return value, label
    average = (prices.get("cardmarket") or {}).get("7d_average")
    if average not in (None, ""):
        currency = (prices.get("cardmarket") or {}).get("currency") or "EUR"
        return float(average), f"Cardmarket 7-day average ({currency})"
    raise LookupError("Pokémon TCG returned no usable price")


def history_chart(days: dict) -> tuple[list[dict], str]:
    """Turn daily history into Cardmarket and TCGPlayer columns.

    English Cardmarket low (``cm_low``) is preferred. When it is empty, the
    language series with the most prices is used. Days with neither price are
    left out.
    """
    counted = {
        key: sum(1 for prices in days.values() if isinstance(prices, dict) and prices.get(key) not in (None, ""))
        for key, _label in _CARDMARKET_SERIES
    }
    if counted["cm_low"]:
        chosen = "cm_low"
    else:
        languages = {key: count for key, count in counted.items() if key != "cm_low"}
        chosen = max(languages, key=languages.get) if any(languages.values()) else None
    label = dict(_CARDMARKET_SERIES).get(chosen, "Cardmarket")
    rows = []
    for day in sorted(days):
        prices = days[day] if isinstance(days[day], dict) else {}
        row = {"date": day}
        market = prices.get(chosen) if chosen else None
        tcg = prices.get("tcg_player_market")
        if market not in (None, ""):
            row["Cardmarket"] = float(market)
        if tcg not in (None, ""):
            row["TCGPlayer"] = float(tcg)
        if len(row) > 1:
            rows.append(row)
    note = (
        "*Average estimated daily value of this card ungraded. "
        f"{label} prices are euros. TCGPlayer prices are US dollars."
    )
    return rows, note


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
        number = grade_number(str(key).casefold().removeprefix(company))
        value = _amount(raw)
        if number is None or value is None:
            continue
        listed.append((number, value))
    return listed


def _amount(raw) -> float | None:
    if isinstance(raw, dict):
        raw = raw.get("median_price")
    if raw in (None, ""):
        return None
    return float(raw)
