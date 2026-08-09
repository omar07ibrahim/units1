from __future__ import annotations

import itertools
import unittest
from decimal import Decimal
from fractions import Fraction

from measuretrace.core import ConversionError, convert, parse_decimal
from measuretrace.registry import UNITS


class CoreConversionTests(unittest.TestCase):
    def test_complete_unit_matrix_uses_exact_rational_factors(self) -> None:
        for source, target in itertools.product(UNITS, repeat=2):
            with self.subTest(source=source, target=target):
                result = convert("1", source, target)
                expected = UNITS[source].meters / UNITS[target].meters
                self.assertEqual(result.factor, expected)
                self.assertEqual(result.exact_result, expected)

    def test_international_mile_is_exact(self) -> None:
        miles_to_metres = convert("1", "mi", "m", decimal_places=3)
        self.assertEqual(miles_to_metres.exact_result, Fraction(201168, 125))
        self.assertEqual(miles_to_metres.rounded_result, "1609.344")

        miles_to_kilometres = convert("1", "mile", "kilometre", decimal_places=6)
        self.assertEqual(miles_to_kilometres.rounded_result, "1.609344")

    def test_zero_is_preserved_and_visible(self) -> None:
        result = convert("-0.000", "m", "km", decimal_places=6)
        self.assertEqual(result.canonical_input, "0")
        self.assertEqual(result.exact_result, 0)
        self.assertEqual(result.rounded_result, "0.000000")

    def test_explicit_rounding_modes(self) -> None:
        self.assertEqual(
            convert("1.005", "m", "m", decimal_places=2).rounded_result, "1.00"
        )
        self.assertEqual(
            convert(
                "1.005",
                "m",
                "m",
                decimal_places=2,
                rounding_mode="ROUND_HALF_UP",
            ).rounded_result,
            "1.01",
        )
        self.assertEqual(
            convert(
                "-1.009",
                "m",
                "m",
                decimal_places=2,
                rounding_mode="ROUND_DOWN",
            ).rounded_result,
            "-1.00",
        )

    def test_decimal_input_is_not_first_coerced_to_binary_float(self) -> None:
        result = convert("0.1", "m", "m", decimal_places=12)
        self.assertEqual(result.exact_result, Fraction(1, 10))
        self.assertEqual(result.rounded_result, "0.100000000000")

    def test_bounded_parser_rejects_unsafe_or_ambiguous_inputs(self) -> None:
        rejected = [
            "",
            "NaN",
            "Infinity",
            "0x10",
            "1,5",
            "1_000",
            "1e101",
            "1e-101",
            "9" * 51,
            "1" * 81,
        ]
        for value in rejected:
            with self.subTest(value=value):
                with self.assertRaises(ConversionError):
                    parse_decimal(value)

    def test_parser_accepts_boundary_magnitudes(self) -> None:
        self.assertEqual(parse_decimal("1e100")[1], Decimal("1e100"))
        self.assertEqual(parse_decimal("1e-100")[1], Decimal("1e-100"))

    def test_invariants_hold_for_exact_results(self) -> None:
        samples = ("0", "0.1", "-2.5", "123456.789")
        for value, first, second, third in itertools.product(
            samples, UNITS, UNITS, UNITS
        ):
            with self.subTest(value=value, first=first, second=second, third=third):
                initial = Fraction(Decimal(value))
                first_result = convert(value, first, second).exact_result
                first_text = (
                    str(first_result.numerator / first_result.denominator)
                    if first_result.denominator != 1
                    else str(first_result.numerator)
                )
                composed_factor = (
                    UNITS[first].meters
                    / UNITS[second].meters
                    * UNITS[second].meters
                    / UNITS[third].meters
                )
                direct_factor = UNITS[first].meters / UNITS[third].meters
                self.assertEqual(composed_factor, direct_factor)
                self.assertEqual(
                    first_result * UNITS[second].meters / UNITS[first].meters,
                    initial,
                )
                self.assertTrue(first_text)


if __name__ == "__main__":
    unittest.main()
