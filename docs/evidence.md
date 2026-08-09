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

## Rejected evidence set pending replacement

The set currently under evidence/portfolio came from workflow run 31288049557
and remains byte-integral, but it is rejected for final publication.
Original-resolution review found that ui-1440x1300.png clipped the selected
“International mile (mi)” source label beneath the native dropdown affordance.
A new source commit, CI artifact, independent audit, and later adoption are
required before the portfolio claim is restored.
