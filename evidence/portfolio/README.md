# Reviewed portfolio evidence

This directory contains the exact bytes reviewed from a CI artifact before
adoption. Do not replace an individual file in place: generate a new staged
artifact, repeat the audit, and adopt the complete verified set in a later
commit.

## Source and integrity

- Source commit: `e9c2d941b7a7e931329655d6ff7621801230f639`
- Workflow run: [31288049557](https://github.com/omar07ibrahim/units1/actions/runs/31288049557)
- Artifact ID: `9030482338`
- Artifact ZIP SHA-256: `9147fef9333ded23338d75bb6237a57ea2da36fce56a3b1482b171fb407b3127`
- Manifest SHA-256: `1035384373224a683e5f00288fc1c207c084364f6cbdf08b960b95c7d8bbcd16`
- Generator SHA-256: `fe89b55b77a173f8b331a2aaf1e71db95d77e9d2c049cb8b7f8e6e4aefdcdbdf`
- Runtime: Python `3.12.11`; Google Chrome `150.0.7871.128`
- Registry SHA-256: `c139e57cc638b889c67ceebbe39a7a618fbe2bde5416626c9a9db9734f625c62`

`manifest.json` records the source commit, capture route, tool versions,
dimensions, byte counts, and SHA-256 for every evidence file.
`manifest.sha256` is the detached manifest digest.

## Review outcome

A separate stream-only audit rejected unsafe or duplicate paths, unmanifested
files, duplicate JSON keys, digest or dimension mismatches, malformed PNG,
GIF, or SVG structures, receipt inconsistencies, drift-data changes, and
secret-shaped text. It independently bound the generator bytes to the source
commit and recomputed the receipt and exact `1 mi = 1.609344 km` result.

The 390, 768, and 1440 CSS-pixel captures were inspected at original
resolution. Each shows the complete page without clipping, overlap, blank
autofocus scrolling, misleading state, or missing responsive hierarchy. The
CLI PNG, animated result tour, diagram XML, and drift CSV/chart were also
checked against their source outputs.

Two earlier staged artifacts were intentionally not adopted after visual
review found blank/scroll-shifted captures and then clipped footers. Their
bytes are not present here.

Rights status follows [the repository provenance notes](../../docs/provenance.md);
the evidence record does not add a license or authorship claim.
