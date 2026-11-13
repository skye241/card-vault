"""Domain rules for a quote: eligibility, name matching, and price selection."""

import unittest

from card_vault.application.eligibility import rejection_reason
from card_vault.application.read_slab import slab_from_reply
from card_vault.domain.matching import collection_matches
from card_vault.domain.models import GradedSlab
from card_vault.domain.pricing import history_chart, select_price
from card_vault.infrastructure.groups import find_group


def _slab(**overrides) -> GradedSlab:
    fields = dict(
        is_graded=True,
        is_pokemon=True,
        company="PSA",
        grade="10",
        card_name="Charizard",
        year="2003",
        collection_name="Skyridge",
        cert_number="12345678",
        card_number="146",
    )
    fields.update(overrides)
    return GradedSlab(**fields)


class EligibilityTest(unittest.TestCase):
    def test_rejects_other_games_before_the_graded_checks(self):
        self.assertEqual(
            rejection_reason(_slab(is_pokemon=False, is_graded=False)),
            "This card is unsupported for now",
        )

    def test_rejects_an_ungraded_pokemon_card(self):
        self.assertIn("Ungraded", rejection_reason(_slab(is_graded=False)))

    def test_accepts_a_known_company(self):
        self.assertIsNone(rejection_reason(_slab(company="BGS")))


class MatchingTest(unittest.TestCase):
    def test_skyridge_and_evolutions(self):
        self.assertEqual(find_group("Pokemon Skyridge", "2003").group_id, 1372)
        self.assertEqual(find_group("xy evolution", "2016").group_id, 1842)
        self.assertTrue(collection_matches("XY - Evolutions", "XY - Evolutions"))

    def test_wrong_year_does_not_match(self):
        with self.assertRaises(LookupError):
            find_group("Skyridge", "1999")


class PricingTest(unittest.TestCase):
    def test_exact_grade_then_closest_within_two(self):
        prices = {"ebay": {"currency": "USD", "graded": {"psa": {
            "10": {"median_price": 100},
            "9": {"median_price": 80},
        }}}}
        self.assertEqual(select_price(prices, "PSA", "10"), (100.0, "eBay PSA 10 (USD)"))
        self.assertEqual(select_price(prices, "PSA", "8"), (80.0, "eBay PSA 9 (USD)"))

    def test_grade_more_than_two_away_tries_the_next_company(self):
        prices = {"ebay": {"currency": "USD", "graded": {
            "psa": {"7": {"median_price": 40}, "6": {"median_price": 30}},
            "tag": {"10": {"median_price": 1600}},
        }}}
        self.assertEqual(select_price(prices, "PSA", "10"), (1600.0, "eBay TAG 10 (USD)"))

    def test_seven_day_average_when_nothing_graded_matches(self):
        prices = {"cardmarket": {"currency": "EUR", "7d_average": 19.5}}
        self.assertEqual(select_price(prices, "PSA", "10"), (19.5, "Cardmarket 7-day average (EUR)"))

    def test_history_uses_the_fuller_language_series(self):
        rows, note = history_chart({
            "2026-01-01": {"cm_low": None, "cm_low_de": 10, "cm_low_it": 12, "tcg_player_market": 9},
            "2026-01-02": {"cm_low": None, "cm_low_it": 11},
        })
        self.assertEqual(rows[0]["Cardmarket"], 12.0)
        self.assertIn("Cardmarket IT", note)


class ReplyTest(unittest.TestCase):
    def test_beckett_is_stored_as_bgs(self):
        slab = slab_from_reply(
            '{"is_graded": true, "is_pokemon": false, "company": "Beckett", '
            '"grade": "9.5", "card_name": "Shohei Ohtani", "card_number": "1", '
            '"year": "2018", "collection_name": "Topps", "cert_number": "12345678"}'
        )
        self.assertEqual(slab.company, "BGS")
        self.assertIs(slab.is_pokemon, False)


if __name__ == "__main__":
    unittest.main()
