"""Small, source-anchored registry for the supported length units."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True, slots=True)
class Unit:
    symbol: str
    name: str
    meters: Fraction


REGISTRY_PAYLOAD = {
    "schema": "measuretrace.unit-registry.v1",
    "units": {
        "km": {"meters_denominator": "1", "meters_numerator": "1000"},
        "m": {"meters_denominator": "1", "meters_numerator": "1"},
        "mi": {"meters_denominator": "125", "meters_numerator": "201168"},
    },
}
REGISTRY_CANONICAL_JSON = json.dumps(
    REGISTRY_PAYLOAD, ensure_ascii=True, separators=(",", ":"), sort_keys=True
)
REGISTRY_SHA256 = hashlib.sha256(REGISTRY_CANONICAL_JSON.encode("ascii")).hexdigest()
REGISTRY_ID = "nist-bipm-length-v1"

UNITS = {
    "m": Unit("m", "metre", Fraction(1, 1)),
    "km": Unit("km", "kilometre", Fraction(1000, 1)),
    "mi": Unit("mi", "international mile", Fraction(201168, 125)),
}

ALIASES = {
    "m": "m",
    "meter": "m",
    "meters": "m",
    "metre": "m",
    "metres": "m",
    "km": "km",
    "kilometer": "km",
    "kilometers": "km",
    "kilometre": "km",
    "kilometres": "km",
    "mi": "mi",
    "mile": "mi",
    "miles": "mi",
}

SOURCES = (
    {
        "authority": "BIPM",
        "title": "SI base unit: metre (m)",
        "url": "https://www.bipm.org/en/si-base-units/metre",
        "supports": "The SI base unit of length and the exact defining-constant relation.",
    },
    {
        "authority": "BIPM",
        "title": "The International System of Units (SI): Prefixes",
        "url": "https://www.bipm.org/en/measurement-units/si-prefixes",
        "supports": "The SI prefix kilo has multiplying factor 10^3.",
    },
    {
        "authority": "NIST",
        "title": "U.S. Survey Foot: Revised Unit Conversion Factors",
        "url": "https://www.nist.gov/pml/us-surveyfoot/revised-unit-conversion-factors",
        "supports": "The international/statute mile is exactly 1609.344 metres.",
    },
)
