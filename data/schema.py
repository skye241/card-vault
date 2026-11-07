"""Fields read off a graded card slab."""

from pydantic import BaseModel


class GradedSlabSchema(BaseModel):
    is_graded: bool
    company: str
    grade: str
    card_name: str
    year: str
    cert_number: str
