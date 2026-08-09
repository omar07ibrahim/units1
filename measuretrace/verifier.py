"""Independent receipt verifier.

This module intentionally does not import the conversion core or registry module. Its
small duplicated trust root lets a caller validate receipts without executing the
code that created them.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal, localcontext
from fractions import Fraction
from typing import Any

RECEIPT_SCHEMA = "measuretrace.conversion-receipt.v1"
REGISTRY_ID = "nist-bipm-length-v1"
MAX_RECEIPT_BYTES = 65_536
_NUMBER_RE = re.compile(
    r"^[+-]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[eE][+-]?\d+)?$"
)
TRUSTED_UNITS = {
    "km": Fraction(1000, 1),
    "m": Fraction(1, 1),
    "mi": Fraction(201168, 125),
}
_REGISTRY_PAYLOAD = {
    "schema": "measuretrace.unit-registry.v1",
    "units": {
        "km": {"meters_denominator": "1", "meters_numerator": "1000"},
        "m": {"meters_denominator": "1", "meters_numerator": "1"},
        "mi": {"meters_denominator": "125", "meters_numerator": "201168"},
    },
}
TRUSTED_REGISTRY_SHA256 = hashlib.sha256(
    json.dumps(
        _REGISTRY_PAYLOAD, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("ascii")
).hexdigest()
ROUNDING_MODES = {
    "ROUND_DOWN": ROUND_DOWN,
    "ROUND_HALF_EVEN": ROUND_HALF_EVEN,
    "ROUND_HALF_UP": ROUND_HALF_UP,
}
REQUIRED_FIELDS = {
    "canonical_input",
    "decimal_places",
    "exact_result_denominator",
    "exact_result_numerator",
    "factor_denominator",
    "factor_numerator",
    "original_input",
    "receipt_schema",
    "receipt_sha256",
    "registry_id",
    "registry_sha256",
    "rounded_result",
    "rounding_mode",
    "source_unit",
    "target_unit",
}


class VerificationError(ValueError):
    """Raised when a receipt is malformed or fails recomputation."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError(f"Duplicate JSON key: {key}.")
        result[key] = value
    return result


def loads_receipt(document: str | bytes) -> dict[str, Any]:
    encoded = document if isinstance(document, bytes) else document.encode("utf-8")
    if len(encoded) > MAX_RECEIPT_BYTES:
        raise VerificationError("Receipt exceeds the 65536-byte limit.")
    try:
        parsed = json.loads(encoded, object_pairs_hook=_unique_object)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise VerificationError("Receipt is not valid UTF-8 JSON.") from exc
    if not isinstance(parsed, dict):
        raise VerificationError("Receipt root must be a JSON object.")
    return parsed


def _require_text(receipt: dict[str, Any], key: str) -> str:
    value = receipt.get(key)
    if not isinstance(value, str):
        raise VerificationError(f"{key} must be a string.")
    return value


def _parse_integer(receipt: dict[str, Any], key: str, *, positive: bool = False) -> int:
    value = _require_text(receipt, key)
    if re.fullmatch(r"-?(?:0|[1-9]\d*)", value) is None:
        raise VerificationError(f"{key} is not a canonical integer.")
    parsed = int(value)
    if positive and parsed <= 0:
        raise VerificationError(f"{key} must be positive.")
    return parsed


def _canonical_decimal(value: Decimal) -> str:
    if value.is_zero():
        return "0"
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def _parse_original(value: str) -> Decimal:
    candidate = value.strip()
    if not candidate or len(candidate) > 80 or _NUMBER_RE.fullmatch(candidate) is None:
        raise VerificationError("original_input is outside the accepted decimal grammar.")
    mantissa = re.split(r"[eE]", candidate, maxsplit=1)[0]
    if sum(character.isdigit() for character in mantissa) > 50:
        raise VerificationError("original_input has too many digits.")
    parsed = Decimal(candidate)
    if not parsed.is_finite():
        raise VerificationError("original_input must be finite.")
    if not parsed.is_zero() and abs(parsed.adjusted()) > 100:
        raise VerificationError("original_input magnitude is outside the accepted bound.")
    return parsed


def _rounded(value: Fraction, places: int, mode: str) -> str:
    if mode not in ROUNDING_MODES:
        raise VerificationError("rounding_mode is not trusted.")
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
        rounded = decimal_value.quantize(
            Decimal(1).scaleb(-places), rounding=ROUNDING_MODES[mode]
        )
    return format(rounded, f".{places}f")


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def verify_receipt(receipt: dict[str, Any]) -> str:
    if set(receipt) != REQUIRED_FIELDS:
        missing = sorted(REQUIRED_FIELDS - set(receipt))
        extra = sorted(set(receipt) - REQUIRED_FIELDS)
        raise VerificationError(f"Receipt fields differ; missing={missing}, extra={extra}.")

    if _require_text(receipt, "receipt_schema") != RECEIPT_SCHEMA:
        raise VerificationError("Unsupported receipt schema.")
    if _require_text(receipt, "registry_id") != REGISTRY_ID:
        raise VerificationError("Untrusted registry id.")
    if not hmac.compare_digest(
        _require_text(receipt, "registry_sha256"), TRUSTED_REGISTRY_SHA256
    ):
        raise VerificationError("Untrusted registry digest.")

    source = _require_text(receipt, "source_unit")
    target = _require_text(receipt, "target_unit")
    if source not in TRUSTED_UNITS or target not in TRUSTED_UNITS:
        raise VerificationError("Receipt contains an unsupported unit.")

    original = _require_text(receipt, "original_input")
    parsed = _parse_original(original)
    if _require_text(receipt, "canonical_input") != _canonical_decimal(parsed):
        raise VerificationError("canonical_input does not match original_input.")

    places = receipt.get("decimal_places")
    if isinstance(places, bool) or not isinstance(places, int) or not 0 <= places <= 12:
        raise VerificationError("decimal_places must be an integer from 0 through 12.")
    mode = _require_text(receipt, "rounding_mode")

    expected_factor = TRUSTED_UNITS[source] / TRUSTED_UNITS[target]
    factor = Fraction(
        _parse_integer(receipt, "factor_numerator"),
        _parse_integer(receipt, "factor_denominator", positive=True),
    )
    if factor != expected_factor:
        raise VerificationError("Conversion factor does not match the trusted registry.")

    exact_result = Fraction(parsed) * expected_factor
    observed_result = Fraction(
        _parse_integer(receipt, "exact_result_numerator"),
        _parse_integer(receipt, "exact_result_denominator", positive=True),
    )
    if observed_result != exact_result:
        raise VerificationError("Exact result does not recompute.")

    if _require_text(receipt, "rounded_result") != _rounded(
        exact_result, places, mode
    ):
        raise VerificationError("Rounded result does not recompute.")

    supplied_digest = _require_text(receipt, "receipt_sha256")
    if re.fullmatch(r"[0-9a-f]{64}", supplied_digest) is None:
        raise VerificationError("receipt_sha256 is not a lowercase SHA-256 digest.")
    payload = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    expected_digest = hashlib.sha256(_canonical_json(payload).encode("ascii")).hexdigest()
    if not hmac.compare_digest(supplied_digest, expected_digest):
        raise VerificationError("Receipt digest does not match its canonical payload.")
    return supplied_digest
