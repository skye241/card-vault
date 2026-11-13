"""Fields read off a graded card slab."""

from pydantic import BaseModel
import datetime


class GradedSlabSchema(BaseModel):
    is_graded: bool
    is_pokemon: bool | None = None
    company: str
    grade: str
    card_name: str
    year: str
    collection_name: str
    cert_number: str
    card_number: str


class TCGGroup(BaseModel):
    groupId: int
    name: str
    abbreviation: str
    publishedOn: datetime.date


class TCGProduct(BaseModel):
    productId: int
    name: str
    cleanName: str
    groupId: int
    extendedData: list[dict[str, dict]]