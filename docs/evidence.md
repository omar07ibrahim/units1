# Evidence protocol

Portfolio media follows a two-commit adoption rule.

## Stage 1: generate and upload

The read-only CI job checks out one exact commit, starts the standard-library WSGI app on `127.0.0.1`, and uses the runner-provided Chrome binary without installing browser software. It produces:

- `ui-390x2300.png`, `ui-768x1700.png`, and `ui-1440x1300.png`: actual local browser renders of the same successful conversion at 390, 768, and 1440 CSS-pixel widths. Tall viewports keep the complete server-rendered flow in evidence.
- `cli-transcript.txt` and `cli-transcript.png`: stdout from an actual convert-and-verify round trip plus a deterministic bitmap rendering.
- `result-tour.gif`: three frames rendered from three actual CLI conversion outputs.
- `architecture.svg` and `conversion-flow.svg`: deterministic diagrams of implemented modules and stages.
- `drift.csv` and `legacy-drift.svg`: exact-core comparison of the original `1.60934 km/mi` approximation with the NIST exact `1.609344 km/mi` definition.
- `sample-receipt.json`: receipt emitted by the actual CLI.
- `manifest.json` and `manifest.sha256`: provenance and byte-level integrity.

The staged directory is gitignored. CI uploads it as `measuretrace-evidence-<commit SHA>`.

## Stage 2: independent audit

Before adoption, a reviewer must:

1. stream the workflow artifact from GitHub without trusting repository media;
2. run `tools/verify_evidence.py` against the extracted bytes;
3. confirm the manifest commit equals the workflow head;
4. inspect all three UI captures for clipping, overlap, missing focus/error semantics, misleading content, and responsive hierarchy;
5. compare the CLI text with the PNG and GIF content;
6. confirm diagrams match current modules and the drift chart matches `drift.csv`;
7. scan every filename and visible string for secrets, personal data, third-party marks, or unsupported claims.

Only then may a later commit place the reviewed bytes under `evidence/portfolio/` and update README links. If Chrome is unavailable or any check fails, CI fails and no screenshot claim is published.

## Adopted evidence set

The current `evidence/portfolio/` bytes came from workflow run
[`31289140743`](https://github.com/omar07ibrahim/units1/actions/runs/31289140743)
for source commit `b9f4e5a92723804a59c61fec813e63136a4b765a`. The streamed artifact
ZIP SHA-256 is
`a74ba764cb9dfae1aa0ef631e53e686d8975090463fe187a613f17196996e3c7`;
its detached manifest SHA-256 is
`19d3e446dc2b6600d333c7fe623d8875abd7f47765c5a9d2f9bc86166cd25079`.

A separate audit checked safe paths, duplicate names and JSON keys, every file
size and digest, generator/source binding, PNG chunk CRCs and decoded pixels,
GIF/SVG structure, receipt semantics, CLI output, drift values, and
secret-shaped text. All three responsive captures were then inspected at
original resolution. The desktop capture shows the complete selected
“International mile (mi)” label without colliding with the native select
affordance, and its rounding fact remains on one line. See the
[adopted review record](../evidence/portfolio/README.md).

The preceding set from artifact `9030482338` remained byte-integral but was
rejected after original-resolution review exposed the desktop select-label
clipping. Replacement candidates `9030758005` and `9030795223` were also
rejected because their layout squeezed the result card and wrapped the
rounding fact. None of those rejected bytes is present in the adopted set.
