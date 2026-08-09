# Provenance and rights notes

## Original baseline

The rehabilitation starts from the historical public repository identity `omar07ibrahim/units1`, main commit `fe2b0332012ef9b03d73f6fc7b9ae1758f096b4b`, tree `7a54249ba79162be8f80370985d80bf8ec9fa909`. The current canonical repository is `omar07ibrahim/measuretrace`; GitHub redirects the legacy URL.

`legacy/baseline.json` records every original blob ID and byte length. The two application blobs are copied byte-for-byte under `legacy/source/`; the original Python blob is stored as `app.py.txt` so an archival debug entry point is not presented as runnable code. The root `.gitattributes` remains unchanged. The complete original history contained two commits and three blobs when captured.

This record documents technical lineage only. It does not claim authorship, ownership, permission, or licensing. No `LICENSE` file is added in this branch; a rights holder must make that decision separately.

## Unit definitions

The registry is a small transcription of facts from primary standards bodies, stored as rational numbers rather than copied prose:

- BIPM, [SI base unit: metre](https://www.bipm.org/en/si-base-units/metre)
- BIPM, [SI prefixes](https://www.bipm.org/en/measurement-units/si-prefixes)
- NIST, [U.S. Survey Foot: Revised Unit Conversion Factors](https://www.nist.gov/pml/us-surveyfoot/revised-unit-conversion-factors)
- NIST, [SP 811 Appendix B.8 conversion factors](https://www.nist.gov/pml/special-publication-811/nist-guide-si-appendix-b-conversion-factors/nist-guide-si-appendix-b8)

The BIPM SI Brochure page states that the brochure is available under CC BY 4.0. This repository links to the source and does not copy its tables or narrative. NIST pages are linked as primary U.S. standards references.

## Dependencies and actions

Production code imports only the Python 3.12 standard library. The wheel build backend is `flit_core==3.12.0`, locked to the SHA-256 of its universal wheel. GitHub Actions are pinned to full commit SHAs with version comments for review.

## Generated evidence

Evidence is generated at a specific Git commit in GitHub Actions. The manifest records the commit, generator hash, Python and Chrome versions, unit-registry hash, every output path, byte count, dimensions where applicable, and SHA-256. The verifier rejects missing, extra-contract, malformed, wrong-sized, or digest-mismatched evidence.

Browser captures use only a loopback URL and local inline CSS. CLI media is rendered from stdout produced during the job. Diagrams name actual modules and stages. The drift chart is derived from a committed CSV generated through the core. No stock image, personal data, secret, fabricated testimonial, or third-party logo is used.
