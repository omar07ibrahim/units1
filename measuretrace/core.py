"""Exact conversion core with bounded decimal parsing and explicit rounding."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import (
    ROUND_DOWN,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    Decimal,
    InvalidOperation,
    localcontext,
)
from fractions import Fraction

from .registry import ALIASES, UNITS

MAX_INPUT_CHARS = 80
MAX_SIGNIFICANT_DIGITS = 50
MAX_ADJUSTED_EXPONENT = 100
MAX_DECIMAL_PLACES = 12

_NUMBER_RE = re.compile(
    r"^[+-]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[eE][+-]?\d+)?$"
)
ROUNDING_MODES = {
    "ROUND_DOWN": ROUND_DOWN,
    "ROUND_HALF_EVEN": ROUND_HALF_EVEN,
    "ROUND_HALF_UP": ROUND_HALF_UP,
}


class ConversionError(ValueError):
    """Raised when an input cannot be converted within the public contract."""


@dataclass(frozen=True, slots=True)
class Conversion:
    original_input: str
    canonical_input: str
    source_unit: str
    target_unit: str
    factor: Fraction
    exact_result: Fraction
    rounded_result: str
    decimal_places: int
    rounding_mode: str


def normalize_unit(value: str) -> str:
    candidate = str(value).strip().lower()
    try:
        return ALIASES[candidate]
    except KeyError as exc:
        supported = ", ".join(UNITS)
        raise ConversionError(f"Unsupported unit {value!r}; choose {supported}.") from exc


def parse_decimal(value: str) -> tuple[str, Decimal]:
    original = str(value)
    candidate = original.strip()
    if not candidate:
        raise ConversionError("Enter a measurement.")
    if len(candidate) > MAX_INPUT_CHARS:
        raise ConversionError(f"Measurement must be at most {MAX_INPUT_CHARS} characters.")
    if _NUMBER_RE.fullmatch(candidate) is None:
        raise ConversionError("Use a finite decimal number, optionally with an exponent.")

    mantissa = re.split(r"[eE]", candidate, maxsplit=1)[0]
    digit_count = sum(character.isdigit() for character in mantissa)
    if digit_count > MAX_SIGNIFICANT_DIGITS:
        raise ConversionError(
            f"Measurement must contain at most {MAX_SIGNIFICANT_DIGITS} digits."
        )

    try:
        parsed = Decimal(candidate)
    except InvalidOperation as exc:
        raise ConversionError("The measurement is not a valid decimal number.") from exc
    if not parsed.is_finite():
        raise ConversionError("NaN and infinite measurements are not supported.")
    if not parsed.is_zero() and abs(parsed.adjusted()) > MAX_ADJUSTED_EXPONENT:
        raise ConversionError(
            "Measurement magnitude must remain between 1e-100 and 1e100."
        )
    return original, parsed


def canonical_decimal(value: Decimal) -> str:
    if value.is_zero():
        return "0"
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def validate_decimal_places(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConversionError("Decimal places must be an integer.")
    if not 0 <= value <= MAX_DECIMAL_PLACES:
        raise ConversionError(
            f"Decimal places must be between 0 and {MAX_DECIMAL_PLACES}."
        )
    return value


def round_fraction(value: Fraction, decimal_places: int, rounding_mode: str) -> str:
    places = validate_decimal_places(decimal_places)
    if rounding_mode not in ROUNDING_MODES:
        choices = ", ".join(ROUNDING_MODES)
        raise ConversionError(f"Unsupported rounding mode; choose {choices}.")

    precision = max(
        80,
        len(str(abs(value.numerator)))
        + len(str(abs(value.denominator)))
        + places
        + 20,
    )
    with localcontext() as context:
        context.prec = precision
        decimal_value = Decimal(value.numerator) / Decimal(value.denominator)
        quantum = Decimal(1).scaleb(-places)
        try:
            rounded = decimal_value.quantize(
                quantum, rounding=ROUNDING_MODES[rounding_mode]
            )
        except InvalidOperation as exc:
            raise ConversionError("Result cannot be represented at that precision.") from exc
    return format(rounded, f".{places}f")


def convert(
    value: str,
    source_unit: str,
    target_unit: str,
    *,
    decimal_places: int = 6,
    rounding_mode: str = "ROUND_HALF_EVEN",
) -> Conversion:
    original, parsed = parse_decimal(value)
    source = normalize_unit(source_unit)
    target = normalize_unit(target_unit)
    places = validate_decimal_places(decimal_places)

    factor = UNITS[source].meters / UNITS[target].meters
    exact_input = Fraction(parsed)
    exact_result = exact_input * factor
    rounded_result = round_fraction(exact_result, places, rounding_mode)

    return Conversion(
        original_input=original,
        canonical_input=canonical_decimal(parsed),
        source_unit=source,
        target_unit=target,
        factor=factor,
        exact_result=exact_result,
        rounded_result=rounded_result,
        decimal_places=places,
        rounding_mode=rounding_mode,
    )
