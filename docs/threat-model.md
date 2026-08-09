# Threat model

## Assets and claims worth protecting

- The exact relationship between input, unit factor, and rational result.
- The explicit rounding rule and displayed decimal.
- The canonical receipt bytes and registry identity.
- Availability of the small local web demonstration.
- Honesty and provenance of portfolio evidence.

The system does not hold credentials, personal data, sessions, payment data, or server-side user content.

## In-scope threats and controls

| Threat | Control |
| --- | --- |
| Decimal or exponent resource abuse | 80-character, 50-digit, and adjusted-exponent bounds before conversion |
| NaN/infinity ambiguity | decimal grammar plus finite-value check |
| Caller-selected or confused unit factor | compiled three-unit registry and normalized aliases |
| Ambient rounding changes | local decimal contexts and an explicit allowlist |
| Receipt field injection | exact field set, strict types, unique-key JSON loader, 65,536-byte cap |
| Result/factor/rounding tampering | independent recomputation and constant-time digest comparison |
| Reflected markup injection | HTML escaping for every caller-controlled value |
| Cross-site state change | no mutable route; web conversion uses GET and has no session |
| Clickjacking or content injection | CSP, `frame-ancestors 'none'`, `X-Frame-Options: DENY`, no scripts or remote assets |
| Supply-chain drift | no runtime packages; exact Python; hash-locked build backend; Actions pinned to commit SHAs |
| CI credential reuse | read-only contents permission and `persist-credentials: false` |
| Fabricated portfolio media | CI-local capture, real command transcript, per-file manifest hashes, verifier, review-before-adoption protocol |

## Residual risks

- SHA-256 receipts are not signed and do not prove issuer identity or creation time.
- The independent verifier duplicates the small registry trust root inside the same repository. A malicious code change could alter both; commit review remains required.
- `wsgiref.simple_server` is not a hardened internet server.
- Inline CSS requires `style-src 'unsafe-inline'`; there is no script allowance.
- Browser screenshots depend on the runner-provided Chrome build recorded in the manifest. Pixel identity across different Chrome builds is not promised.
- NIST/BIPM sources can evolve. Registry changes require a new identifier, digest, tests, source review, and receipt schema compatibility decision.
- Accessibility tests cover semantics and keyboard/focus contracts. Manual assistive-technology and zoom testing remains necessary before calling the UI production-ready.

## Explicit non-goals

No authentication, receipt signing, user accounts, persistence, analytics, arbitrary unit definitions, locale-aware parsing, scientific uncertainty, measurement calibration, or legal-metrology conformance is provided.
