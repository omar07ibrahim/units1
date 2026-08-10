# Security policy

## Supported state

Security fixes target the default branch and the maintained `0.1.x` source
state. No release archive or package-index distribution is currently
published because the repository has no selected license.

## Reporting a vulnerability

Use
[GitHub private vulnerability reporting](https://github.com/omar07ibrahim/measuretrace/security/advisories/new).
Do not open a public issue for an undisclosed vulnerability and never include
credentials, personal measurements, private files, or unrelated account data.

A useful report contains the affected CLI, receipt, verifier, or WSGI path; a
minimal synthetic input; the observed bounded output or error; the expected
contract; and Python version `3.12.11`.

## Security boundaries

MeasureTrace parses bounded decimal text, performs exact local arithmetic, and
can serve a loopback demonstration. It has no authentication, persistence,
cookies, analytics, remote assets, or runtime dependencies. The standard
library WSGI server is not intended for untrusted internet deployment.

Receipt SHA-256 values detect byte changes; they are not signatures and do not
establish issuer identity or creation time. The independent verifier remains
inside the same repository, so review must reject coordinated changes to both
the producer and its duplicated trust root.

The frozen files under `legacy/source/` are archival input to regression
tests, never executable production code or reusable portfolio media.
