# Reviewed portfolio evidence

This directory contains the exact bytes reviewed from a CI artifact before
adoption. Do not replace an individual file in place: generate a new staged
artifact, repeat the audit, and adopt the complete verified set in a later
commit.

## Source and integrity

- Source commit: `b9f4e5a92723804a59c61fec813e63136a4b765a`
- Workflow run: [31289140743](https://github.com/omar07ibrahim/units1/actions/runs/31289140743)
- Artifact ID: `9030832975`
- Artifact ZIP SHA-256: `a74ba764cb9dfae1aa0ef631e53e686d8975090463fe187a613f17196996e3c7`
- Manifest SHA-256: `19d3e446dc2b6600d333c7fe623d8875abd7f47765c5a9d2f9bc86166cd25079`
- Generator SHA-256: `fe89b55b77a173f8b331a2aaf1e71db95d77e9d2c049cb8b7f8e6e4aefdcdbdf`
- Runtime: Python `3.12.11`; Google Chrome `150.0.7871.128`
- Registry SHA-256: `c139e57cc638b889c67ceebbe39a7a618fbe2bde5416626c9a9db9734f625c62`

`manifest.json` records the source commit, capture route, tool versions,
dimensions, byte counts, and SHA-256 for every evidence file.
`manifest.sha256` is the detached manifest digest.

## Review outcome

A separate stream-only audit checked for unsafe or duplicate paths,
unmanifested files, duplicate JSON keys, digest or dimension mismatches,
malformed PNG, GIF, or SVG structures, receipt inconsistencies, drift-data
changes, and secret-shaped text. It independently bound the generator bytes
to the source commit and recomputed the receipt and exact
`1 mi = 1.609344 km` result.

The 390, 768, and 1440 CSS-pixel captures were inspected at original
resolution. Each shows the complete page without clipping, overlap, blank
autofocus scrolling, misleading state, or missing responsive hierarchy. On
desktop, the full “International mile (mi)” selected value remains clear of
the native dropdown affordance and `ROUND_HALF_EVEN · 6 places` remains on one
line. The CLI PNG, animated result tour, diagram XML, and drift CSV/chart were
also checked against their source outputs.

Earlier staged artifacts with blank or scroll-shifted captures and clipped
footers were never adopted. The preceding adopted set from artifact
`9030482338` was later rejected after desktop select-label clipping was found;
replacement candidates `9030758005` and `9030795223` were rejected after
result-card wrapping appeared. None of those rejected bytes is present here.

Rights status follows [the repository provenance notes](../../docs/provenance.md);
the evidence record does not add a license or authorship claim.
