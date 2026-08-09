"""Command-line interface for conversion and independent receipt verification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .core import ConversionError, convert
from .receipt import build_receipt, canonical_receipt_json
from .verifier import VerificationError, loads_receipt, verify_receipt

ROUNDING_ARGUMENTS = {
    "down": "ROUND_DOWN",
    "half-even": "ROUND_HALF_EVEN",
    "half-up": "ROUND_HALF_UP",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="measuretrace",
        description="Exact m/km/mi conversion with independently verifiable receipts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    converter = subparsers.add_parser("convert", help="convert a decimal measurement")
    converter.add_argument("value", help="finite decimal input")
    converter.add_argument("source_unit", help="m, km, or mi")
    converter.add_argument("target_unit", help="m, km, or mi")
    converter.add_argument("--places", type=int, default=6, help="0 through 12")
    converter.add_argument(
        "--rounding",
        choices=sorted(ROUNDING_ARGUMENTS),
        default="half-even",
        help="explicit decimal rounding rule",
    )
    converter.add_argument(
        "--json", action="store_true", help="print only canonical receipt JSON"
    )
    converter.add_argument(
        "--receipt", metavar="PATH", help="also write canonical receipt JSON"
    )

    verifier = subparsers.add_parser("verify", help="verify a receipt without the core")
    verifier.add_argument("receipt", help="receipt JSON path, or - for stdin")
    return parser


def _write_receipt(path: str, document: str) -> None:
    Path(path).write_text(document + "\n", encoding="utf-8", newline="\n")


def _read_receipt(path: str) -> str:
    if path == "-":
        return sys.stdin.read(65_537)
    with Path(path).open(encoding="utf-8") as handle:
        return handle.read(65_537)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "convert":
            conversion = convert(
                arguments.value,
                arguments.source_unit,
                arguments.target_unit,
                decimal_places=arguments.places,
                rounding_mode=ROUNDING_ARGUMENTS[arguments.rounding],
            )
            receipt = build_receipt(conversion)
            document = canonical_receipt_json(receipt)
            if arguments.receipt:
                _write_receipt(arguments.receipt, document)
            if arguments.json:
                print(document)
            else:
                print(
                    f"{conversion.canonical_input} {conversion.source_unit} -> "
                    f"{conversion.rounded_result} {conversion.target_unit}"
                )
                print(
                    "exact: "
                    f"{conversion.exact_result.numerator}/"
                    f"{conversion.exact_result.denominator}"
                )
                print(
                    "factor: "
                    f"{conversion.factor.numerator}/{conversion.factor.denominator}"
                )
                print(
                    f"rounding: {conversion.rounding_mode} "
                    f"at {conversion.decimal_places} decimal places"
                )
                print(f"receipt-sha256: {receipt['receipt_sha256']}")
            return 0

        document = _read_receipt(arguments.receipt)
        receipt = loads_receipt(document)
        digest = verify_receipt(receipt)
        print(f"verified {digest}")
        return 0
    except (ConversionError, VerificationError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"measuretrace: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
