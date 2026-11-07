from enum import Enum


class GradingCompany(str, Enum):
    PSA = "PSA"
    CGC = "CGC"
    SGC = "SGC"
    Beckett = "Beckett"
