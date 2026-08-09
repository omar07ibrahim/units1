"""Generate genuine CI evidence from the checked-out MeasureTrace application.

The generator uses only the standard library and a Chrome binary already present on
GitHub's hosted runner. It never downloads fonts, CSS, scripts, or browser packages.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import textwrap
import time
import zlib
from decimal import Decimal, localcontext
from fractions import Fraction
from html import escape as xml_escape
from pathlib import Path
from typing import Sequence
from urllib.parse import urlencode
from urllib.request import urlopen

from measuretrace.core import convert
from measuretrace.registry import REGISTRY_SHA256

ROOT = Path(__file__).resolve().parents[1]
PALETTE = (
    (16, 37, 30),
    (231, 248, 238),
    (168, 216, 190),
    (25, 92, 69),
)
FONT = {
    " ": ("00000",) * 7,
    "?": ("01110", "10001", "00010", "00100", "00100", "00000", "00100"),
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "00001", "11110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    ">": ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
    "<": ("00001", "00010", "00100", "01000", "00100", "00010", "00001"),
    "=": ("00000", "11111", "00000", "11111", "00000", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "#": ("01010", "11111", "01010", "01010", "11111", "01010", "01010"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def write_png(path: Path, width: int, height: int, pixels: bytearray) -> None:
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        offset = y * width
        for index in pixels[offset : offset + width]:
            rows.extend(PALETTE[index])
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(bytes(rows), level=9))
        + png_chunk(b"IEND", b"")
    )
    path.write_bytes(payload)


def draw_text(
    pixels: bytearray,
    width: int,
    height: int,
    x: int,
    y: int,
    text: str,
    *,
    scale: int = 2,
    color: int = 1,
) -> None:
    cursor = x
    for character in text:
        glyph = FONT.get(character.upper(), FONT["?"])
        for row, pattern in enumerate(glyph):
            for column, bit in enumerate(pattern):
                if bit != "1":
                    continue
                for dy in range(scale):
                    for dx in range(scale):
                        px = cursor + column * scale + dx
                        py = y + row * scale + dy
                        if 0 <= px < width and 0 <= py < height:
                            pixels[py * width + px] = color
        cursor += 6 * scale


def wrapped_lines(text: str, width: int) -> list[str]:
    output: list[str] = []
    for line in text.splitlines():
        output.extend(
            textwrap.wrap(
                line,
                width=width,
                replace_whitespace=False,
                drop_whitespace=False,
            )
            or [""]
        )
    return output


def transcript_pixels(text: str, width: int, height: int) -> bytearray:
    pixels = bytearray(width * height)
    draw_text(
        pixels,
        width,
        height,
        30,
        24,
        "MEASURETRACE / REAL CLI TRANSCRIPT",
        scale=2,
        color=2,
    )
    max_characters = max(20, (width - 60) // 12)
    y = 64
    for line in wrapped_lines(text, max_characters):
        draw_text(pixels, width, height, 30, y, line, scale=2, color=1)
        y += 20
        if y > height - 20:
            break
    return pixels


def write_transcript_png(text: str, path: Path) -> tuple[int, int]:
    dimensions = (1200, 430)
    write_png(path, *dimensions, transcript_pixels(text, *dimensions))
    return dimensions


def pack_lzw_codes(codes: list[int]) -> bytes:
    output = bytearray()
    accumulator = 0
    bits = 0
    for code in codes:
        accumulator |= code << bits
        bits += 3
        while bits >= 8:
            output.append(accumulator & 0xFF)
            accumulator >>= 8
            bits -= 8
    if bits:
        output.append(accumulator & 0xFF)
    return bytes(output)


def gif_frame_data(pixels: bytearray) -> bytes:
    clear = 4
    end = 5
    codes: list[int] = []
    for pixel in pixels:
        codes.extend((clear, int(pixel)))
    codes.append(end)
    return pack_lzw_codes(codes)


def write_gif(path: Path, frames: list[bytearray], width: int, height: int) -> None:
    data = bytearray(b"GIF89a")
    data.extend(struct.pack("<HHBBB", width, height, 0xF1, 0, 0))
    for red, green, blue in PALETTE:
        data.extend((red, green, blue))
    data.extend(b"!\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00")
    for frame in frames:
        data.extend(b"!\xf9\x04\x00")
        data.extend(struct.pack("<H", 150))
        data.extend(b"\x00\x00")
        data.extend(b",")
        data.extend(struct.pack("<HHHHB", 0, 0, width, height, 0))
        encoded = gif_frame_data(frame)
        data.append(2)
        for offset in range(0, len(encoded), 255):
            block = encoded[offset : offset + 255]
            data.append(len(block))
            data.extend(block)
        data.append(0)
    data.extend(b";")
    path.write_bytes(bytes(data))


def run_cli(arguments: list[str]) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "measuretrace", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout


def create_cli_evidence(output: Path) -> list[tuple[str, tuple[int, int] | None]]:
    receipt = output / "sample-receipt.json"
    try:
        receipt_argument = receipt.relative_to(ROOT).as_posix()
    except ValueError:
        receipt_argument = str(receipt)

    convert_arguments = [
        "convert",
        "1",
        "mi",
        "km",
        "--places",
        "6",
        "--receipt",
        receipt_argument,
    ]
    conversion_output = run_cli(convert_arguments)
    verify_arguments = ["verify", receipt_argument]
    verification_output = run_cli(verify_arguments)
    transcript = (
        "$ python -m measuretrace "
        + " ".join(convert_arguments)
        + "\n"
        + conversion_output
        + "$ python -m measuretrace "
        + " ".join(verify_arguments)
        + "\n"
        + verification_output
    )
    (output / "cli-transcript.txt").write_text(
        transcript, encoding="utf-8", newline="\n"
    )
    transcript_dimensions = write_transcript_png(
        transcript, output / "cli-transcript.png"
    )

    gif_commands = [
        ["convert", "1", "mi", "km", "--places", "6"],
        ["convert", "5", "km", "mi", "--places", "6"],
        ["convert", "0", "m", "km", "--places", "6"],
    ]
    width, height = 560, 315
    frames = []
    for arguments in gif_commands:
        actual = "$ python -m measuretrace " + " ".join(arguments) + "\n" + run_cli(arguments)
        frames.append(transcript_pixels(actual, width, height))
    write_gif(output / "result-tour.gif", frames, width, height)
    return [
        ("cli-transcript.png", transcript_dimensions),
        ("result-tour.gif", (width, height)),
    ]


def svg_document(
    title: str,
    subtitle: str,
    nodes: list[tuple[int, int, int, int, str, str]],
    edges: list[tuple[int, int]],
    width: int,
    height: int,
) -> str:
    pieces = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f"<title id=\"title\">{xml_escape(title)}</title>",
        f"<desc id=\"desc\">{xml_escape(subtitle)}</desc>",
        "<defs><marker id=\"arrow\" markerWidth=\"10\" markerHeight=\"10\" "
        "refX=\"8\" refY=\"3\" orient=\"auto\"><path d=\"M0,0 L0,6 L9,3 z\" "
        "fill=\"#195c45\"/></marker></defs>",
        '<rect width="100%" height="100%" fill="#f5f3ea"/>',
        f'<text x="48" y="64" font-family="system-ui,sans-serif" font-size="34" '
        f'font-weight="760" fill="#14211d">{xml_escape(title)}</text>',
        f'<text x="48" y="94" font-family="system-ui,sans-serif" font-size="16" '
        f'fill="#52615b">{xml_escape(subtitle)}</text>',
    ]
    centers = [
        (x + node_width // 2, y + node_height // 2)
        for x, y, node_width, node_height, _label, _detail in nodes
    ]
    for source, target in edges:
        x1, y1 = centers[source]
        x2, y2 = centers[target]
        pieces.append(
            f'<path d="M{x1},{y1} L{x2},{y2}" stroke="#195c45" stroke-width="3" '
            'fill="none" marker-end="url(#arrow)"/>'
        )
    for x, y, node_width, node_height, label, detail in nodes:
        pieces.extend(
            [
                f'<rect x="{x}" y="{y}" width="{node_width}" height="{node_height}" '
                'rx="18" fill="#fffdf6" stroke="#8fa198" stroke-width="2"/>',
                f'<text x="{x + 18}" y="{y + 38}" font-family="system-ui,sans-serif" '
                f'font-size="20" font-weight="720" fill="#14211d">{xml_escape(label)}</text>',
                f'<text x="{x + 18}" y="{y + 66}" font-family="ui-monospace,monospace" '
                f'font-size="13" fill="#52615b">{xml_escape(detail)}</text>',
            ]
        )
    pieces.append("</svg>\n")
    return "".join(pieces)


def create_diagrams(output: Path) -> None:
    architecture_nodes = [
        (50, 150, 210, 90, "Web UI", "measuretrace.web"),
        (50, 300, 210, 90, "CLI", "measuretrace.cli"),
        (350, 225, 220, 90, "Exact core", "Decimal → Fraction"),
        (660, 150, 220, 90, "Receipt builder", "canonical JSON"),
        (660, 330, 220, 90, "Unit registry", "NIST + BIPM"),
        (970, 225, 210, 90, "Verifier", "independent trust root"),
    ]
    architecture_edges = [(0, 2), (1, 2), (2, 3), (4, 2), (4, 5), (3, 5)]
    (output / "architecture.svg").write_text(
        svg_document(
            "MeasureTrace architecture",
            "Actual production modules and their trust boundaries.",
            architecture_nodes,
            architecture_edges,
            1230,
            520,
        ),
        encoding="utf-8",
        newline="\n",
    )

    flow_nodes = [
        (35, 165, 170, 90, "Decimal input", "bounded grammar"),
        (240, 165, 170, 90, "Exact parse", "Decimal + Fraction"),
        (445, 165, 170, 90, "Unit factor", "rational registry"),
        (650, 165, 170, 90, "Round display", "explicit mode"),
        (855, 165, 170, 90, "Issue receipt", "canonical JSON"),
        (1060, 165, 170, 90, "Recompute", "independent verify"),
    ]
    (output / "conversion-flow.svg").write_text(
        svg_document(
            "Conversion and verification flow",
            "The rounded display is downstream of an exact rational result.",
            flow_nodes,
            [(0, 1), (1, 2), (2, 3), (2, 4), (3, 4), (4, 5)],
            1265,
            420,
        ),
        encoding="utf-8",
        newline="\n",
    )


def fraction_decimal(value: Fraction, places: int = 12) -> str:
    with localcontext() as context:
        context.prec = 50
        decimal = Decimal(value.numerator) / Decimal(value.denominator)
    return format(decimal, f".{places}f").rstrip("0").rstrip(".")


def create_drift_evidence(output: Path) -> None:
    mile_counts = [1, 10, 100, 1000, 10000, 100000]
    legacy_factor = Fraction(160934, 100000)
    rows = []
    for miles in mile_counts:
        exact = convert(str(miles), "mi", "km", decimal_places=6).exact_result
        legacy = legacy_factor * miles
        drift_metres = (exact - legacy) * 1000
        rows.append(
            {
                "miles": str(miles),
                "exact_kilometres": fraction_decimal(exact),
                "legacy_kilometres": fraction_decimal(legacy),
                "legacy_drift_metres": fraction_decimal(drift_metres),
            }
        )
    with (output / "drift.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    width, height = 1100, 620
    left, top, chart_width, chart_height = 100, 130, 900, 380
    maximum = max(float(row["legacy_drift_metres"]) for row in rows)
    points = []
    for index, row in enumerate(rows):
        x = left + index * chart_width / (len(rows) - 1)
        y = top + chart_height - float(row["legacy_drift_metres"]) / maximum * chart_height
        points.append((x, y))
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    labels = []
    for (x, y), row in zip(points, rows):
        labels.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="#195c45"/>'
            f'<text x="{x:.1f}" y="{top + chart_height + 32}" text-anchor="middle" '
            f'font-family="system-ui,sans-serif" font-size="13" fill="#52615b">'
            f'{row["miles"]}</text>'
        )
    grid = []
    for tick in range(5):
        value = maximum * tick / 4
        y = top + chart_height - tick * chart_height / 4
        grid.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{left + chart_width}" y2="{y:.1f}" '
            'stroke="#c9cec7" stroke-width="1"/>'
            f'<text x="{left - 18}" y="{y + 5:.1f}" text-anchor="end" '
            'font-family="system-ui,sans-serif" font-size="13" fill="#52615b">'
            f'{value:g} m</text>'
        )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
        '<title id="title">Legacy approximation drift</title>'
        '<desc id="desc">Difference between the original 1.60934 kilometre per mile '
        'factor and the exact NIST international mile definition.</desc>'
        '<rect width="100%" height="100%" fill="#f5f3ea"/>'
        '<text x="60" y="58" font-family="system-ui,sans-serif" font-size="32" '
        'font-weight="760" fill="#14211d">Legacy approximation drift</text>'
        '<text x="60" y="88" font-family="system-ui,sans-serif" font-size="15" '
        'fill="#52615b">Original 1.60934 km/mi vs exact 1.609344 km/mi · computed by CI</text>'
        + "".join(grid)
        + f'<polyline points="{polyline}" fill="none" stroke="#195c45" '
        'stroke-width="4" stroke-linejoin="round"/>'
        + "".join(labels)
        + f'<text x="{left + chart_width / 2}" y="{top + chart_height + 76}" '
        'text-anchor="middle" font-family="system-ui,sans-serif" font-size="15" '
        'fill="#14211d">Input distance (international miles, log-spaced samples)</text>'
        '</svg>\n'
    )
    (output / "legacy-drift.svg").write_text(svg, encoding="utf-8", newline="\n")


def wait_for_server(url: str) -> None:
    for _attempt in range(80):
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("Local MeasureTrace server did not become ready.")


def create_browser_evidence(output: Path) -> tuple[str, dict[str, tuple[int, int]]]:
    chrome = shutil.which("google-chrome")
    if chrome is None:
        raise RuntimeError(
            "google-chrome is absent; evidence must not be generated or claimed."
        )
    chrome_version = subprocess.run(
        [chrome, "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    ).stdout.strip()
    base_url = "http://127.0.0.1:8765/"
    query = urlencode(
        {
            "value": "1",
            "from": "mi",
            "to": "km",
            "places": "6",
            "rounding": "half-even",
            "action": "convert",
        }
    )
    capture_url = base_url + "?" + query
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "measuretrace",
            "serve",
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    dimensions = {
        "ui-390x844.png": (390, 844),
        "ui-768x1024.png": (768, 1024),
        "ui-1440x1000.png": (1440, 1000),
    }
    profile = output / ".chrome-profile"
    try:
        wait_for_server(base_url)
        for filename, (width, height) in dimensions.items():
            result = subprocess.run(
                [
                    chrome,
                    "--headless=new",
                    "--disable-background-networking",
                    "--disable-component-update",
                    "--disable-default-apps",
                    "--disable-gpu",
                    "--disable-sync",
                    "--force-device-scale-factor=1",
                    "--hide-scrollbars",
                    "--metrics-recording-only",
                    "--no-first-run",
                    f"--user-data-dir={profile}",
                    f"--window-size={width},{height}",
                    f"--screenshot={output / filename}",
                    capture_url,
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Chrome failed for {filename}.")
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)
        shutil.rmtree(profile, ignore_errors=True)
    return chrome_version, dimensions


def png_dimensions(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError(f"{path.name} is not a PNG.")
    return struct.unpack(">II", header[16:24])


def write_manifest(
    output: Path,
    ci_sha: str,
    chrome_version: str,
    expected_dimensions: dict[str, tuple[int, int]],
) -> None:
    kinds = {
        "architecture.svg": "repo-derived architecture diagram",
        "cli-transcript.png": "bitmap rendering of the real CLI transcript",
        "cli-transcript.txt": "real CLI stdout transcript",
        "conversion-flow.svg": "repo-derived workflow diagram",
        "drift.csv": "core-computed legacy comparison data",
        "legacy-drift.svg": "chart derived from drift.csv",
        "result-tour.gif": "animated bitmap rendering of three real CLI results",
        "sample-receipt.json": "canonical receipt emitted by the real CLI",
        "ui-390x844.png": "Chrome screenshot of the local WSGI app",
        "ui-768x1024.png": "Chrome screenshot of the local WSGI app",
        "ui-1440x1000.png": "Chrome screenshot of the local WSGI app",
    }
    files = []
    for name in sorted(kinds):
        path = output / name
        record: dict[str, object] = {
            "bytes": path.stat().st_size,
            "kind": kinds[name],
            "path": name,
            "sha256": sha256(path),
        }
        if name.endswith(".png"):
            record["dimensions"] = list(png_dimensions(path))
        elif name == "result-tour.gif":
            record["dimensions"] = [560, 315]
        files.append(record)

    manifest = {
        "schema": "measuretrace.evidence-manifest.v1",
        "ci_sha": ci_sha,
        "chrome_version": chrome_version,
        "files": files,
        "generated_by": "tools/generate_evidence.py",
        "generator_sha256": sha256(Path(__file__)),
        "python": sys.version.split()[0],
        "registry_sha256": REGISTRY_SHA256,
        "source_date_epoch": os.environ.get("SOURCE_DATE_EPOCH", "1695295514"),
        "capture": {
            "network": "loopback only",
            "route": "/?value=1&from=mi&to=km&places=6&rounding=half-even&action=convert",
            "screenshots": {
                name: list(dimensions)
                for name, dimensions in sorted(expected_dimensions.items())
            },
        },
        "claims": [
            "UI PNGs are browser screenshots of the checked-out WSGI app.",
            "CLI PNG and GIF frames render stdout from commands executed in this job.",
            "SVG diagrams name actual modules and flow stages in this commit.",
            "The drift chart is derived from drift.csv generated by the exact core.",
        ],
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (output / "manifest.sha256").write_text(
        sha256(manifest_path) + "\n", encoding="ascii", newline="\n"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ci-sha", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if not __import__("re").fullmatch(r"[0-9a-f]{40}", arguments.ci_sha):
        raise SystemExit("--ci-sha must be a full lowercase Git commit SHA.")
    output = arguments.output
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    create_cli_evidence(output)
    create_diagrams(output)
    create_drift_evidence(output)
    chrome_version, dimensions = create_browser_evidence(output)
    write_manifest(output, arguments.ci_sha, chrome_version, dimensions)
    print(f"generated and manifested evidence in {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
