# Contributing

MeasureTrace is intentionally small: exact m/km/mi conversion, canonical
receipts, an independent verifier, CLI, and a server-rendered local UI.

## Development setup

Use the pinned Python and hash-locked build backend:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements-dev.lock
.venv/bin/python tools/quality_gate.py
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m compileall -q -f measuretrace tests tools
```

The supported interpreter is exactly Python `3.12.x`; CI currently pins
`3.12.11`.

## Contract rules

- Keep conversion factors rational and preserve the independent verifier's
  deliberately separate trust root.
- Preserve the bounded input grammar, stable receipt schema, explicit rounding,
  unique-key JSON loading, and redacted public errors.
- Do not add runtime dependencies, remote browser assets, cookies, analytics,
  persistence, or JavaScript without an explicit threat-model revision.
- Use synthetic values only. Never commit secrets, personal measurements,
  local paths, hostnames, or account data.
- Do not infer or grant repository reuse rights; license selection requires a
  documented rights-holder decision.

## Visual evidence

Never hand-edit or replace one file under `evidence/portfolio/`. Generate a
complete staged set in CI, stream-audit its archive, verify the manifest and
source binding, inspect every viewport/CLI/GIF/diagram at original resolution,
scan for secrets and personal data, and adopt the complete reviewed set in a
later commit. Follow [docs/evidence.md](docs/evidence.md).
