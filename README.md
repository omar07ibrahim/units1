# MeasureTrace

MeasureTrace is a narrow length-conversion workbench for metres, kilometres, and international miles. It keeps decimal input exact, makes rounding explicit, and emits a canonical JSON receipt that a deliberately independent module can recompute.

This branch is an in-progress rehabilitation of the original three-file exercise. The preserved baseline is under `legacy/`. No benchmark, certification, legal-metrology, ownership, or authorship claim is made.

## Current command-line contract

```console
python -m measuretrace convert 1 mi km --places 6
python -m measuretrace convert 1 mi km --places 6 --receipt receipt.json
python -m measuretrace verify receipt.json
```

Supported symbols are `m`, `km`, and `mi`. Decimal inputs are bounded to 80 characters, 50 mantissa digits, and adjusted exponents from -100 through 100. Rounding must be selected from half-even, half-up, or toward zero; the default is half-even at six decimal places.

## Definition sources

The registry is intentionally small and stores rational factors:

- [BIPM: SI base unit metre](https://www.bipm.org/en/si-base-units/metre)
- [BIPM: SI prefixes](https://www.bipm.org/en/measurement-units/si-prefixes), where kilo is `10^3`
- [NIST: revised unit conversion factors](https://www.nist.gov/pml/us-surveyfoot/revised-unit-conversion-factors), where the international/statute mile is `1609.344 m` exactly

The registry identifier is `nist-bipm-length-v1`; receipts carry the SHA-256 digest of its canonical payload.

## Development

Python 3.12.11 is the pinned interpreter. Runtime dependencies are empty. The build backend is the only development dependency and is installed from `requirements-dev.lock` with an exact version and wheel SHA-256.

```console
python -m pip install --require-hashes -r requirements-dev.lock
python -m unittest discover -v
python -m compileall -q measuretrace tests
```

A browser interface, threat model, CI, and evidence workflow are added in later commits on the feature branch.
