"""Verify staged or adopted evidence without trusting the generator."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from typing import Any, Sequence

from measuretrace.verifier import loads_receipt, verify_receipt

MANIFEST_SCHEMA = "measuretrace.evidence-manifest.v1"


class EvidenceError(ValueError):
    """Raised when evidence bytes or metadata do not verify."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(131_072), b""):
            digest.update(block)
    return digest.hexdigest()


def png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise EvidenceError(f"{path.name} is not a PNG.")
    if header[12:16] != b"IHDR":
        raise EvidenceError(f"{path.name} has no leading IHDR.")
    return struct.unpack(">II", header[16:24])


def safe_path(root: Path, value: str) -> Path:
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts:
        raise EvidenceError(f"unsafe manifest path: {value!r}")
    base = root.resolve()
    resolved = base.joinpath(*pure.parts).resolve()
    if resolved != base and base not in resolved.parents:
        raise EvidenceError(f"path escapes evidence root: {value!r}")
    return resolved


def verify_svg(path: Path) -> None:
    document = path.read_text(encoding="utf-8")
    root = ET.fromstring(document)
    if not root.tag.endswith("svg"):
        raise EvidenceError(f"{path.name} root is not SVG.")
    lowered = document.lower()
    if "<script" in lowered or "javascript:" in lowered:
        raise EvidenceError(f"{path.name} contains executable content.")
    if re.search(r"(?:href|src)=[\"']https?://", lowered):
        raise EvidenceError(f"{path.name} contains a remote resource.")


def verify_gif(path: Path, expected: tuple[int, int]) -> None:
    data = path.read_bytes()
    if not data.startswith(b"GIF89a") or len(data) < 32:
        raise EvidenceError(f"{path.name} is not a GIF89a animation.")
    dimensions = struct.unpack("<HH", data[6:10])
    if dimensions != expected:
        raise EvidenceError(
            f"{path.name} dimensions {dimensions} do not match {expected}."
        )
    if b"NETSCAPE2.0" not in data or data.count(b"\x2c") < 3:
        raise EvidenceError(f"{path.name} is not the expected looping animation.")


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise EvidenceError("Manifest is not valid UTF-8 JSON.") from exc
    if not isinstance(value, dict):
        raise EvidenceError("Manifest root must be an object.")
    return value


def verify(manifest_path: Path, root: Path, expected_ci_sha: str | None) -> int:
    manifest = load_manifest(manifest_path)
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise EvidenceError("Unsupported evidence manifest schema.")

    ci_sha = manifest.get("ci_sha")
    if not isinstance(ci_sha, str) or re.fullmatch(r"[0-9a-f]{40}", ci_sha) is None:
        raise EvidenceError("Manifest CI SHA is malformed.")
    if expected_ci_sha and ci_sha != expected_ci_sha:
        raise EvidenceError(f"Manifest CI SHA {ci_sha} != expected {expected_ci_sha}.")

    detached = manifest_path.with_name("manifest.sha256")
    expected_manifest_digest = detached.read_text(encoding="ascii").strip()
    if re.fullmatch(r"[0-9a-f]{64}", expected_manifest_digest) is None:
        raise EvidenceError("Detached manifest digest is malformed.")
    if sha256(manifest_path) != expected_manifest_digest:
        raise EvidenceError("Detached manifest digest does not match.")

    records = manifest.get("files")
    if not isinstance(records, list) or not records:
        raise EvidenceError("Manifest file records are missing.")
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise EvidenceError("Manifest file record is not an object.")
        relative = record.get("path")
        digest = record.get("sha256")
        size = record.get("bytes")
        if not isinstance(relative, str) or relative in seen:
            raise EvidenceError(f"Duplicate or invalid path: {relative!r}")
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise EvidenceError(f"Invalid digest for {relative}.")
        if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
            raise EvidenceError(f"Invalid byte count for {relative}.")
        seen.add(relative)
        path = safe_path(root, relative)
        if not path.is_file() or path.stat().st_size != size:
            raise EvidenceError(f"Missing or wrong-sized evidence file: {relative}.")
        if sha256(path) != digest:
            raise EvidenceError(f"Digest mismatch: {relative}.")

        if relative.endswith(".png"):
            dimensions = tuple(record.get("dimensions", ()))
            if len(dimensions) != 2 or png_dimensions(path) != dimensions:
                raise EvidenceError(f"PNG dimensions do not verify: {relative}.")
            if size < 1_000:
                raise EvidenceError(f"PNG is implausibly small: {relative}.")
        elif relative.endswith(".svg"):
            verify_svg(path)
        elif relative.endswith(".gif"):
            dimensions = tuple(record.get("dimensions", ()))
            verify_gif(path, dimensions)

    required = {
        "architecture.svg",
        "cli-transcript.png",
        "cli-transcript.txt",
        "conversion-flow.svg",
        "drift.csv",
        "legacy-drift.svg",
        "result-tour.gif",
        "sample-receipt.json",
        "ui-390x844.png",
        "ui-768x1024.png",
        "ui-1440x1000.png",
    }
    if not required.issubset(seen):
        raise EvidenceError(f"Required evidence is absent: {sorted(required - seen)}")

    receipt = loads_receipt((root / "sample-receipt.json").read_bytes())
    verify_receipt(receipt)

    transcript = (root / "cli-transcript.txt").read_text(encoding="utf-8")
    if "$ python -m measuretrace convert" not in transcript:
        raise EvidenceError("Transcript does not identify the executed conversion command.")
    if "receipt-sha256:" not in transcript or "\nverified " not in transcript:
        raise EvidenceError("Transcript lacks conversion or verifier output.")

    with (root / "drift.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 6 or rows[0]["miles"] != "1" or rows[-1]["miles"] != "100000":
        raise EvidenceError("Drift dataset does not match the declared range.")
    if any(float(row["legacy_drift_metres"]) <= 0 for row in rows):
        raise EvidenceError("Drift dataset contains a non-positive comparison.")

    print(
        f"verified {len(records)} evidence files for CI commit {ci_sha}; "
        f"manifest {expected_manifest_digest}"
    )
    return len(records)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--expect-ci-sha")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        verify(arguments.manifest, arguments.root, arguments.expect_ci_sha)
        return 0
    except (EvidenceError, OSError, KeyError, ValueError) as exc:
        print(f"evidence verification failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
