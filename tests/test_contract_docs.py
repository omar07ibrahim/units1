from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from measuretrace.receipt import canonical_json
from measuretrace.registry import REGISTRY_SHA256
from measuretrace.verifier import REQUIRED_FIELDS

ROOT = Path(__file__).resolve().parents[1]


class ContractDocumentationTests(unittest.TestCase):
    def test_documented_registry_matches_runtime_digest(self) -> None:
        registry = json.loads(
            (ROOT / "docs" / "unit-registry-v1.json").read_text(encoding="utf-8")
        )
        digest = hashlib.sha256(canonical_json(registry).encode("ascii")).hexdigest()
        self.assertEqual(digest, REGISTRY_SHA256)

    def test_receipt_schema_requires_the_verifier_field_set(self) -> None:
        schema = json.loads(
            (ROOT / "docs" / "receipt-v1.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(set(schema["required"]), REQUIRED_FIELDS)
        self.assertFalse(schema["additionalProperties"])

    def test_documentation_keeps_rights_and_non_goal_boundaries_explicit(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        threat_model = (ROOT / "docs" / "threat-model.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("No repository license has been selected", readme)
        self.assertIn("not a calibration service", readme)
        self.assertIn("SHA-256 receipts are not signed", threat_model)


if __name__ == "__main__":
    unittest.main()
