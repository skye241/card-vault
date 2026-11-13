from enum import Enum


class GradingCompany(str, Enum):
    PSA = "PSA"
    CGC = "CGC"
    SGC = "SGC"
    Beckett = "Beckett"
    TAG = "TAG" #AI card grading company - Tier 2
    ACE="ACE"#England top card grading company - Tier 2
    BGS = "BGS"
