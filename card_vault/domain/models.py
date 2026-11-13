"""Values that move through a quote. No network or UI types."""

from datetime import date

from pydantic import BaseModel


class GradedSlab(BaseModel):
    """Fields read from one slab photo.

    ``is_pokemon`` is None when the reader did not say which game the card is.
    """

    is_graded: bool
    is_pokemon: bool | None = None
    company: str
    grade: str
    card_name: str
    year: str
    collection_name: str
    cert_number: str
    card_number: str


class SetGroup(BaseModel):
    """One Pokémon set from the local TCGplayer group catalog."""

    group_id: int
    name: str
    abbreviation: str
    published_on: date


class Quote(BaseModel):
    """A covered value and the market line that produced it."""

    amount: float
    source: str
    card_id: int | None = None

    @property
    def symbol(self) -> str:
        """Currency glyph for the source label. Cardmarket amounts are euros."""
        return "€" if "(EUR)" in self.source else "$"


class PriceHistory(BaseModel):
    """Daily points ready for a line chart, plus the caption that explains them."""

    rows: list[dict]
    note: str
