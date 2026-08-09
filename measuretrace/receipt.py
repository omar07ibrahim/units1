"""Canonical receipt construction for MeasureTrace conversions."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .core import Conversion
from .registry import REGISTRY_ID, REGISTRY_SHA256

RECEIPT_SCHEMA = "measuretrace.conversion-receipt.v1"


def canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def build_receipt(conversion: Conversion) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "canonical_input": conversion.canonical_input,
        "decimal_places": conversion.decimal_places,
        "exact_result_denominator": str(conversion.exact_result.denominator),
        "exact_result_numerator": str(conversion.exact_result.numerator),
        "factor_denominator": str(conversion.factor.denominator),
        "factor_numerator": str(conversion.factor.numerator),
        "original_input": conversion.original_input,
        "receipt_schema": RECEIPT_SCHEMA,
        "registry_id": REGISTRY_ID,
        "registry_sha256": REGISTRY_SHA256,
        "rounded_result": conversion.rounded_result,
        "rounding_mode": conversion.rounding_mode,
        "source_unit": conversion.source_unit,
        "target_unit": conversion.target_unit,
    }
    digest = hashlib.sha256(canonical_json(payload).encode("ascii")).hexdigest()
    return {**payload, "receipt_sha256": digest}


def canonical_receipt_json(receipt: dict[str, Any]) -> str:
    return canonical_json(receipt)
