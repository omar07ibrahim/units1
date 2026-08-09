from __future__ import annotations

import hashlib
import importlib.machinery
import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "legacy" / "baseline.json"


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


class FakeFlask:
    def __init__(self, _name: str) -> None:
        pass

    def route(self, *_args, **_kwargs):
        return lambda function: function

    def run(self, **_kwargs) -> None:
        raise AssertionError("The frozen legacy server must never run in tests.")


def load_legacy_module():
    fake_flask = types.ModuleType("flask")
    fake_flask.Flask = FakeFlask
    fake_flask.render_template = lambda *_args, **_kwargs: ""
    fake_flask.request = types.SimpleNamespace(method="GET", form={})
    previous = sys.modules.get("flask")
    sys.modules["flask"] = fake_flask
    try:
        source = ROOT / "legacy" / "source" / "app.py.txt"
        loader = importlib.machinery.SourceFileLoader(
            "measuretrace_legacy_fixture", str(source)
        )
        spec = importlib.util.spec_from_loader(loader.name, loader)
        if spec is None or spec.loader is None:
            raise AssertionError("Unable to load the frozen legacy fixture.")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if previous is None:
            del sys.modules["flask"]
        else:
            sys.modules["flask"] = previous


class LegacyBaselineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_is_anchored_to_original_main(self) -> None:
        source = self.manifest["captured_from"]
        self.assertEqual(
            source["commit"], "fe2b0332012ef9b03d73f6fc7b9ae1758f096b4b"
        )
        self.assertEqual(
            source["tree"], "7a54249ba79162be8f80370985d80bf8ec9fa909"
        )

    def test_preserved_blobs_match_git_object_ids(self) -> None:
        for record in self.manifest["files"]:
            data = (ROOT / record["copy"]).read_bytes()
            self.assertEqual(len(data), record["bytes"], record["path"])
            self.assertEqual(git_blob_sha(data), record["git_blob_sha1"], record["path"])

    def test_observed_conversion_behavior_is_reproducible(self) -> None:
        legacy = load_legacy_module()
        for case in self.manifest["behavior_cases"]:
            observed = legacy.convert_units(case["from"], case["to"], case["input"])
            expected = case["legacy_result"]
            if expected is None:
                self.assertIsNone(observed, case["name"])
            else:
                self.assertEqual(str(observed), expected, case["name"])

    def test_known_ui_defects_remain_visible_in_fixture(self) -> None:
        template = (ROOT / "legacy" / "source" / "templates" / "index.html").read_text(
            encoding="utf-8"
        )
        self.assertIn("{% if converted_value %}", template)
        self.assertNotIn("{{ error_message }}", template)
        self.assertIn("stackpath.bootstrapcdn.com", template)


if __name__ == "__main__":
    unittest.main()
