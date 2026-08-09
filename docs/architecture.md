# Architecture

MeasureTrace separates conversion, presentation, and verification so each claim has a small reviewable boundary.

## Runtime path

1. `measuretrace.core.parse_decimal` accepts a bounded finite decimal grammar. It never coerces through `float`.
2. `measuretrace.registry` maps `m`, `km`, and `mi` to exact metres-per-unit fractions.
3. `measuretrace.core.convert` multiplies the exact input fraction by the exact source/target factor.
4. `round_fraction` applies one named decimal rounding mode at 0–12 places.
5. `measuretrace.receipt` serializes the conversion as sorted, compact, ASCII JSON and hashes the payload.
6. `measuretrace.verifier` recomputes all material fields without importing the core or registry module.

The CLI and WSGI interface call the same core. Neither can supply a factor or precomputed result.

## Trust boundaries

| Boundary | Trusted input | Rejected input |
| --- | --- | --- |
| Decimal parser | bounded finite decimal text | NaN, infinity, separators, non-decimal syntax, >50 digits, magnitude outside 1e±100 |
| Unit registry | three compiled symbols and aliases | caller-supplied factors or unknown units |
| Rounding | named mode and 0–12 places | ambient decimal context or unbounded precision |
| Receipt loader | UTF-8 JSON ≤65,536 bytes with unique keys | duplicate keys, extra/missing fields, non-object roots |
| Web request | GET/HEAD, loopback-safe query ≤2,048 characters and ≤10 fields | state-changing methods, duplicates, unknown fields |
| Evidence | files listed and hashed by the CI manifest | unmanifested, wrong-sized, remote-resource, or unreviewed media |

## Canonical receipt

A receipt contains the original and canonical decimal input, unit symbols, reduced rational factor, reduced rational exact result, rounding contract, rounded display, unit-registry identifier/digest, and a digest of the remaining canonical payload.

The digest is tamper-evidence, not identity, authorization, timestamping, or a digital signature. A verifier trusts the code and registry constants it is running.

## Web surface

`measuretrace.web.application` is a dependency-free WSGI application. The form uses GET because conversion is deterministic and does not mutate server state. Values are escaped before rendering. The response sets CSP, clickjacking, MIME-sniffing, referrer, opener, resource, permissions, and no-store headers. Inline CSS is the only CSP exception; there are no scripts, remote assets, cookies, sessions, or database writes.

`wsgiref.simple_server` is a local demonstration server. Production deployment requires an independently reviewed WSGI host, TLS termination, request/time limits, logging policy, and operational monitoring.
