from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from measuretrace.cli import main


class CliTests(unittest.TestCase):
    def test_convert_and_verify_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "receipt.json"
            output = io.StringIO()
            with redirect_stdout(output):
                status = main(
                    [
                        "convert",
                        "1",
                        "mi",
                        "km",
                        "--places",
                        "6",
                        "--receipt",
                        str(receipt),
                    ]
                )
            self.assertEqual(status, 0)
            self.assertIn("1 mi -> 1.609344 km", output.getvalue())
            self.assertTrue(receipt.read_text(encoding="utf-8").endswith("\n"))

            verification = io.StringIO()
            with redirect_stdout(verification):
                status = main(["verify", str(receipt)])
            self.assertEqual(status, 0)
            self.assertRegex(verification.getvalue(), r"^verified [0-9a-f]{64}\n$")

    def test_invalid_input_returns_nonzero_without_traceback(self) -> None:
        errors = io.StringIO()
        with redirect_stderr(errors):
            status = main(["convert", "NaN", "m", "km"])
        self.assertEqual(status, 2)
        self.assertIn("measuretrace:", errors.getvalue())
        self.assertNotIn("Traceback", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
