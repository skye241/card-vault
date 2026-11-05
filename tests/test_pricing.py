import unittest

from card_vault.pricing import choose_price, quote


class PricingTest(unittest.TestCase):
    def test_prefers_holofoil_over_a_higher_reverse_price(self):
        variant, bucket = choose_price(
            {
                "reverseHolofoil": {"market": 80},
                "holofoil": {"market": 40},
                "normal": {"market": 10},
            }
        )
        self.assertEqual(variant, "holofoil")
        self.assertEqual(bucket["market"], 40)

    def test_skips_empty_market_and_uses_reverse_as_fallback(self):
        variant, bucket = choose_price(
            {
                "holofoil": {"market": None},
                "reverseHolofoil": {"market": 12.5},
            }
        )
        self.assertEqual(variant, "reverseHolofoil")
        self.assertEqual(bucket["market"], 12.5)

    def test_missing_prices(self):
        self.assertIsNone(choose_price(None))
        self.assertIsNone(choose_price({"holofoil": {"low": 1}}))

    def test_condition_scales_the_resale_price(self):
        self.assertEqual(quote(100, "Near Mint"), 100)
        self.assertEqual(quote(100, "Lightly Played"), 85)
        self.assertEqual(quote(10, "Moderately Played"), 7)
        self.assertEqual(quote(10, "Heavily Played"), 5)

    def test_unknown_condition(self):
        with self.assertRaises(ValueError):
            quote(10, "Gem Mint")


if __name__ == "__main__":
    unittest.main()
