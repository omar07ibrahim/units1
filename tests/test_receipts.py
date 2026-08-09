from __future__ import annotations

import copy
import json
import unittest

from measuretrace.core import convert
from measuretrace.receipt import build_receipt, canonical_receipt_json
from measuretrace.registry import REGISTRY_SHA256
from measuretrace.verifier import (
    TRUSTED_REGISTRY_SHA256,
    VerificationError,
    loads_receipt,
    verify_receipt,
)


class ReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.receipt = build_receipt(
            convert(
                "12.345",
                "mi",
                "km",
                decimal_places=6,
                rounding_mode="ROUND_HALF_EVEN",
            )
        )

    def test_independent_verifier_accepts_canonical_receipt(self) -> None:
        self.assertEqual(REGISTRY_SHA256, TRUSTED_REGISTRY_SHA256)
        digest = verify_receipt(self.receipt)
        self.assertEqual(digest, self.receipt["receipt_sha256"])
        document = canonical_receipt_json(self.receipt)
        self.assertEqual(json.loads(document), self.receipt)
        self.assertEqual(verify_receipt(loads_receipt(document)), digest)

    def test_every_material_field_is_tamper_evident(self) -> None:
        mutations = {
            "canonical_input": "12.346",
            "decimal_places": 5,
            "exact_result_numerator": "1",
            "factor_denominator": "1",
            "original_input": "12.346",
            "registry_sha256": "0" * 64,
            "rounded_result": "19.999999",
            "rounding_mode": "ROUND_DOWN",
            "source_unit": "m",
            "target_unit": "m",
            "receipt_sha256": "f" * 64,
        }
        for field, replacement in mutations.items():
            with self.subTest(field=field):
                tampered = copy.deepcopy(self.receipt)
                tampered[field] = replacement
                with self.assertRaises(VerificationError):
                    verify_receipt(tampered)

    def test_extra_missing_and_duplicate_fields_are_rejected(self) -> None:
        extra = {**self.receipt, "note": "untrusted"}
        with self.assertRaises(VerificationError):
            verify_receipt(extra)

        missing = dict(self.receipt)
        del missing["factor_numerator"]
        with self.assertRaises(VerificationError):
            verify_receipt(missing)

        with self.assertRaises(VerificationError):
            loads_receipt('{"receipt_schema":"one","receipt_schema":"two"}')

    def test_receipt_size_is_bounded(self) -> None:
        with self.assertRaises(VerificationError):
            loads_receipt(b"{" + b" " * 65_536)


if __name__ == "__main__":
    unittest.main()
