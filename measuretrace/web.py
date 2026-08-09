"""Dependency-free, server-rendered MeasureTrace web interface."""

from __future__ import annotations

from html import escape
from http import HTTPStatus
from typing import Callable, Iterable
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from .core import Conversion, ConversionError, convert
from .receipt import build_receipt, canonical_receipt_json
from .registry import REGISTRY_ID, REGISTRY_SHA256, UNITS

MAX_QUERY_CHARS = 2_048
MAX_QUERY_FIELDS = 10
PUBLIC_INPUT_ERROR = (
    "Check the measurement, units, decimal places, and rounding mode."
)

_STYLES = """
:root {
  color-scheme: light;
  --ink: #14211d;
  --muted: #52615b;
  --paper: #f5f3ea;
  --panel: #fffdf6;
  --line: #c9cec7;
  --accent: #195c45;
  --accent-strong: #0d4432;
  --accent-soft: #d9ede3;
  --warning: #8a2d20;
  --warning-soft: #fae5df;
  --code: #10251e;
  --shadow: 0 20px 55px rgba(25, 49, 40, 0.12);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
    "Segoe UI", sans-serif;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  color: var(--ink);
  background:
    radial-gradient(circle at 90% 5%, rgba(97, 181, 137, 0.18), transparent 28rem),
    linear-gradient(180deg, #faf8ef 0%, var(--paper) 100%);
}
a { color: var(--accent-strong); }
a:hover { text-decoration-thickness: 0.14em; }
a:focus-visible,
button:focus-visible,
input:focus-visible,
select:focus-visible,
[tabindex]:focus-visible {
  outline: 3px solid #b45718;
  outline-offset: 3px;
}
.skip-link {
  position: fixed;
  left: 1rem;
  top: 1rem;
  z-index: 10;
  padding: 0.7rem 1rem;
  color: #fff;
  background: var(--code);
  transform: translateY(-180%);
}
.skip-link:focus { transform: translateY(0); }
.shell {
  width: min(1200px, calc(100% - 2rem));
  margin: 0 auto;
  padding: 1.4rem 0 3rem;
}
.masthead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 4rem;
}
.brand {
  display: inline-flex;
  align-items: center;
  gap: 0.7rem;
  color: var(--ink);
  font-weight: 800;
  letter-spacing: -0.02em;
  text-decoration: none;
}
.mark {
  display: grid;
  width: 2.2rem;
  height: 2.2rem;
  place-items: center;
  border: 2px solid var(--ink);
  border-radius: 0.65rem;
  background: var(--accent-soft);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
}
.registry-tag {
  margin: 0;
  color: var(--muted);
  font: 0.76rem/1.2 ui-monospace, SFMono-Regular, Consolas, monospace;
}
.hero {
  max-width: 820px;
  margin-bottom: 2.25rem;
}
.eyebrow {
  margin: 0 0 0.8rem;
  color: var(--accent);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.11em;
  text-transform: uppercase;
}
h1 {
  max-width: 13ch;
  margin: 0;
  font-size: clamp(2.6rem, 8vw, 5.5rem);
  line-height: 0.96;
  letter-spacing: -0.065em;
}
.hero-copy {
  max-width: 62ch;
  margin: 1.5rem 0 0;
  color: var(--muted);
  font-size: clamp(1rem, 2vw, 1.18rem);
  line-height: 1.65;
}
.workspace {
  display: grid;
  grid-template-columns: minmax(0, 0.92fr) minmax(0, 1.08fr);
  gap: 1rem;
  align-items: stretch;
}
.card {
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: 1.25rem;
  background: rgba(255, 253, 246, 0.94);
  box-shadow: var(--shadow);
}
.converter { padding: clamp(1.25rem, 3vw, 2rem); }
.card-heading {
  margin: 0 0 0.35rem;
  font-size: 1.25rem;
  letter-spacing: -0.025em;
}
.card-intro {
  margin: 0 0 1.5rem;
  color: var(--muted);
  line-height: 1.55;
}
fieldset {
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
}
legend {
  width: 100%;
  margin-bottom: 1rem;
  font-weight: 750;
}
.field {
  min-width: 0;
  margin-bottom: 1.1rem;
}
.field-row {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 0.7rem;
  align-items: end;
}
.direction-row {
  grid-template-columns: minmax(0, 1.15fr) auto minmax(0, 0.85fr);
}
label {
  display: block;
  margin-bottom: 0.42rem;
  font-size: 0.88rem;
  font-weight: 760;
}
input,
select,
button {
  width: 100%;
  min-height: 2.9rem;
  border-radius: 0.7rem;
  font: inherit;
}
input,
select {
  border: 1px solid #89968f;
  padding: 0.68rem 0.76rem;
  color: var(--ink);
  background: #fff;
}
input[aria-invalid="true"] { border-color: var(--warning); }
.help {
  margin: 0.42rem 0 0;
  color: var(--muted);
  font-size: 0.78rem;
  line-height: 1.45;
}
.swap {
  width: 3rem;
  padding: 0;
  border: 1px solid #89968f;
  color: var(--ink);
  background: var(--accent-soft);
  cursor: pointer;
}
.actions {
  display: flex;
  gap: 0.7rem;
  margin-top: 1.45rem;
}
.primary {
  border: 1px solid var(--accent-strong);
  padding: 0.75rem 1rem;
  color: #fff;
  background: var(--accent);
  font-weight: 780;
  cursor: pointer;
}
.primary:hover { background: var(--accent-strong); }
.error {
  margin: 0 0 1rem;
  border-left: 4px solid var(--warning);
  padding: 0.8rem 0.9rem;
  color: #5e1c14;
  background: var(--warning-soft);
  line-height: 1.45;
}
.result-card {
  display: flex;
  min-height: 100%;
  flex-direction: column;
  overflow: hidden;
}
.result-top {
  padding: clamp(1.25rem, 3vw, 2rem);
  color: #f7fff9;
  background: var(--code);
}
.result-kicker {
  margin: 0 0 1rem;
  color: #a8d8be;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.result-value {
  margin: 0;
  overflow-wrap: anywhere;
  font: 750 clamp(2rem, 6vw, 4rem)/1.02 ui-monospace, SFMono-Regular,
    Consolas, monospace;
  letter-spacing: -0.055em;
}
.result-unit {
  display: block;
  margin-top: 0.45rem;
  color: #b9c8c1;
  font-size: 1rem;
  letter-spacing: 0;
}
.result-body {
  display: grid;
  gap: 1rem;
  padding: clamp(1.25rem, 3vw, 2rem);
}
.fact-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.7rem;
}
.fact {
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: 0.8rem;
  padding: 0.85rem;
  background: #fff;
}
.fact dt {
  margin-bottom: 0.35rem;
  color: var(--muted);
  font-size: 0.72rem;
  font-weight: 750;
  text-transform: uppercase;
}
.fact dd {
  margin: 0;
  overflow-wrap: anywhere;
  font: 0.86rem/1.4 ui-monospace, SFMono-Regular, Consolas, monospace;
}
details {
  border-top: 1px solid var(--line);
  padding-top: 1rem;
}
summary {
  cursor: pointer;
  font-weight: 760;
}
pre {
  max-height: 18rem;
  margin: 0.8rem 0 0;
  overflow: auto;
  border-radius: 0.7rem;
  padding: 0.9rem;
  color: #e7f8ee;
  background: var(--code);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font: 0.72rem/1.5 ui-monospace, SFMono-Regular, Consolas, monospace;
}
.empty-state {
  display: grid;
  min-height: 100%;
  place-items: center;
  padding: clamp(2rem, 7vw, 5rem);
  text-align: center;
}
.empty-glyph {
  display: grid;
  width: 5rem;
  height: 5rem;
  margin: 0 auto 1.2rem;
  place-items: center;
  border: 2px solid var(--accent);
  border-radius: 50%;
  color: var(--accent);
  background: var(--accent-soft);
  font: 800 1.35rem/1 ui-monospace, SFMono-Regular, Consolas, monospace;
}
.empty-state h2 { margin: 0; font-size: 1.5rem; }
.empty-state p {
  max-width: 34ch;
  margin: 0.65rem auto 0;
  color: var(--muted);
  line-height: 1.55;
}
.provenance {
  margin-top: 1rem;
  border: 1px solid var(--line);
  border-radius: 1rem;
  padding: 1rem 1.2rem;
  color: var(--muted);
  background: rgba(255, 253, 246, 0.7);
  font-size: 0.82rem;
  line-height: 1.55;
}
.provenance p { margin: 0; }
.provenance p + p { margin-top: 0.35rem; }
@media (max-width: 1200px) {
  .workspace { grid-template-columns: 1fr; }
  .result-card { min-height: 28rem; }
}
@media (max-width: 780px) {
  .masthead { padding-bottom: 2.8rem; }
  .registry-tag { display: none; }
}
@media (max-width: 460px) {
  .shell { width: min(100% - 1rem, 1200px); padding-top: 0.7rem; }
  .field-row { grid-template-columns: 1fr; }
  .swap { width: 100%; }
  .fact-grid { grid-template-columns: 1fr; }
  h1 { font-size: clamp(2.45rem, 15vw, 4rem); }
}
@media (prefers-reduced-motion: reduce) {
  * { scroll-behavior: auto !important; }
}
"""


class WebInputError(ValueError):
    """Raised when a request is outside the bounded web contract."""


def _single_values(query_string: str) -> dict[str, str]:
    if len(query_string) > MAX_QUERY_CHARS:
        raise WebInputError("The request is too long.")
    try:
        parsed = parse_qs(
            query_string,
            keep_blank_values=True,
            max_num_fields=MAX_QUERY_FIELDS,
        )
    except ValueError as exc:
        raise WebInputError("The request has too many fields.") from exc
    allowed = {"action", "from", "places", "rounding", "to", "value"}
    if not set(parsed).issubset(allowed):
        raise WebInputError("The request contains an unsupported field.")
    if any(len(values) != 1 for values in parsed.values()):
        raise WebInputError("Each field must appear exactly once.")
    return {key: values[0] for key, values in parsed.items()}


def _unit_options(selected: str) -> str:
    labels = {"m": "Metre (m)", "km": "Kilometre (km)", "mi": "International mile (mi)"}
    return "".join(
        f'<option value="{symbol}"'
        f'{" selected" if symbol == selected else ""}>{escape(label)}</option>'
        for symbol, label in labels.items()
    )


def _rounding_options(selected: str) -> str:
    labels = {
        "half-even": "Half even",
        "half-up": "Half up",
        "down": "Toward zero",
    }
    return "".join(
        f'<option value="{key}"'
        f'{" selected" if key == selected else ""}>{escape(label)}</option>'
        for key, label in labels.items()
    )


def _result_markup(conversion: Conversion | None, receipt: dict | None) -> str:
    if conversion is None or receipt is None:
        return """
        <section class="card result-card empty-state" aria-labelledby="empty-title">
          <div>
            <div class="empty-glyph" aria-hidden="true">m↔mi</div>
            <h2 id="empty-title">Your exact trail appears here</h2>
            <p>Convert a value to inspect the rational factor, exact fraction,
              rounding rule, and canonical receipt.</p>
          </div>
        </section>
        """

    exact = f"{conversion.exact_result.numerator}/{conversion.exact_result.denominator}"
    factor = f"{conversion.factor.numerator}/{conversion.factor.denominator}"
    document = escape(canonical_receipt_json(receipt))
    digest = escape(str(receipt["receipt_sha256"]))
    return f"""
    <section class="card result-card" id="result" role="status" aria-live="polite"
      aria-atomic="true" tabindex="-1" aria-labelledby="result-title">
      <div class="result-top">
        <p class="result-kicker">Rounded display · verified inputs</p>
        <h2 class="result-value" id="result-title">
          {escape(conversion.rounded_result)}
          <span class="result-unit">{escape(conversion.target_unit)}</span>
        </h2>
      </div>
      <div class="result-body">
        <dl class="fact-grid">
          <div class="fact">
            <dt>Exact result</dt>
            <dd>{escape(exact)}</dd>
          </div>
          <div class="fact">
            <dt>Exact factor</dt>
            <dd>{escape(factor)}</dd>
          </div>
          <div class="fact">
            <dt>Rounding</dt>
            <dd>{escape(conversion.rounding_mode)} · {conversion.decimal_places} places</dd>
          </div>
          <div class="fact">
            <dt>Receipt SHA-256</dt>
            <dd>{digest}</dd>
          </div>
        </dl>
        <details>
          <summary>Inspect canonical JSON receipt</summary>
          <pre>{document}</pre>
        </details>
      </div>
    </section>
    """


def render_page(
    *,
    value: str = "",
    source: str = "mi",
    target: str = "km",
    places: str = "6",
    rounding: str = "half-even",
    conversion: Conversion | None = None,
    receipt: dict | None = None,
    error: str | None = None,
    submitted: bool = False,
) -> str:
    error_markup = ""
    input_state = ""
    if error:
        error_markup = (
            f'<p class="error" id="form-error" role="alert">{escape(error)}</p>'
        )
        input_state = ' aria-invalid="true" aria-describedby="value-help form-error" autofocus'
    result_markup = _result_markup(conversion, receipt)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>MeasureTrace · exact length conversion</title>
  <style>{_STYLES}</style>
</head>
<body>
  <a class="skip-link" href="#main">Skip to converter</a>
  <div class="shell">
    <header class="masthead">
      <a class="brand" href="/" aria-label="MeasureTrace home">
        <span class="mark" aria-hidden="true">↔</span>
        <span>MeasureTrace</span>
      </a>
      <p class="registry-tag">{REGISTRY_ID} · {REGISTRY_SHA256[:12]}</p>
    </header>
    <main id="main">
      <section class="hero" aria-labelledby="page-title">
        <p class="eyebrow">Exact by definition · explicit by design</p>
        <h1 id="page-title">Conversions you can check.</h1>
        <p class="hero-copy">Enter a decimal measurement. MeasureTrace keeps it
          rational through the conversion, then shows exactly where the rounded
          display came from.</p>
      </section>
      <div class="workspace">
        <form class="card converter" action="/#result" method="get" aria-labelledby="form-title">
          <h2 class="card-heading" id="form-title">Build a conversion</h2>
          <p class="card-intro">Three units. One bounded input. No hidden float step.</p>
          {error_markup}
          <fieldset>
            <legend>1 · Enter the measurement</legend>
            <div class="field">
              <label for="value">Decimal value</label>
              <input id="value" name="value" value="{escape(value, quote=True)}"
                inputmode="decimal" autocomplete="off" maxlength="80"
                placeholder="e.g. 12.345" required{input_state}>
              <p class="help" id="value-help">Finite decimal; up to 50 digits and
                magnitude from 1e-100 through 1e100.</p>
            </div>
          </fieldset>
          <fieldset>
            <legend>2 · Choose the direction</legend>
            <div class="field-row direction-row">
              <div class="field">
                <label for="from">From</label>
                <select id="from" name="from">{_unit_options(source)}</select>
              </div>
              <button class="swap" type="submit" name="action" value="swap"
                aria-label="Swap source and target units">⇄</button>
              <div class="field">
                <label for="to">To</label>
                <select id="to" name="to">{_unit_options(target)}</select>
              </div>
            </div>
          </fieldset>
          <fieldset>
            <legend>3 · Make rounding explicit</legend>
            <div class="field-row">
              <div class="field">
                <label for="places">Decimal places</label>
                <input id="places" name="places" type="number" min="0" max="12"
                  step="1" value="{escape(places, quote=True)}" required>
              </div>
              <span aria-hidden="true"></span>
              <div class="field">
                <label for="rounding">Rounding mode</label>
                <select id="rounding" name="rounding">
                  {_rounding_options(rounding)}
                </select>
              </div>
            </div>
          </fieldset>
          <div class="actions">
            <button class="primary" type="submit" name="action" value="convert">
              Convert and issue receipt
            </button>
          </div>
        </form>
        {result_markup}
      </div>
      <aside class="provenance" aria-label="Definition provenance">
        <p><strong>Definition trail:</strong>
          <a href="https://www.bipm.org/en/si-base-units/metre">BIPM metre</a>,
          <a href="https://www.bipm.org/en/measurement-units/si-prefixes">BIPM kilo prefix</a>,
          and <a href="https://www.nist.gov/pml/us-surveyfoot/revised-unit-conversion-factors">NIST international mile</a>.
        </p>
        <p>Scope: m, km, and international mi. This is an inspectable software
          demonstration, not a legal-metrology service or calibration certificate.</p>
      </aside>
    </main>
  </div>
</body>
</html>
"""


def _headers(content: bytes) -> list[tuple[str, str]]:
    return [
        ("Content-Type", "text/html; charset=utf-8"),
        ("Content-Length", str(len(content))),
        ("Cache-Control", "no-store"),
        (
            "Content-Security-Policy",
            "default-src 'none'; style-src 'unsafe-inline'; "
            "form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
        ),
        ("Cross-Origin-Opener-Policy", "same-origin"),
        ("Cross-Origin-Resource-Policy", "same-origin"),
        ("Permissions-Policy", "camera=(), microphone=(), geolocation=()"),
        ("Referrer-Policy", "no-referrer"),
        ("X-Content-Type-Options", "nosniff"),
        ("X-Frame-Options", "DENY"),
    ]


def application(
    environ: dict,
    start_response: Callable[[str, list[tuple[str, str]]], None],
) -> Iterable[bytes]:
    method = str(environ.get("REQUEST_METHOD", "GET")).upper()
    path = str(environ.get("PATH_INFO", "/"))
    if path != "/":
        content = b"Not found\n"
        start_response(
            f"{HTTPStatus.NOT_FOUND.value} {HTTPStatus.NOT_FOUND.phrase}",
            [("Content-Type", "text/plain; charset=utf-8"), ("Content-Length", str(len(content)))],
        )
        return [] if method == "HEAD" else [content]
    if method not in {"GET", "HEAD"}:
        content = b"Method not allowed\n"
        start_response(
            f"{HTTPStatus.METHOD_NOT_ALLOWED.value} {HTTPStatus.METHOD_NOT_ALLOWED.phrase}",
            [
                ("Allow", "GET, HEAD"),
                ("Content-Type", "text/plain; charset=utf-8"),
                ("Content-Length", str(len(content))),
            ],
        )
        return [content]

    value = ""
    source = "mi"
    target = "km"
    places_text = "6"
    rounding_argument = "half-even"
    conversion = None
    receipt = None
    error = None
    submitted = False

    try:
        parameters = _single_values(str(environ.get("QUERY_STRING", "")))
        value = parameters.get("value", "")
        source = parameters.get("from", source)
        target = parameters.get("to", target)
        places_text = parameters.get("places", places_text)
        rounding_argument = parameters.get("rounding", rounding_argument)
        action = parameters.get("action", "")
        submitted = "value" in parameters
        if action == "swap":
            source, target = target, source
        if submitted:
            if rounding_argument not in {
                "half-even": "ROUND_HALF_EVEN",
                "half-up": "ROUND_HALF_UP",
                "down": "ROUND_DOWN",
            }:
                raise WebInputError("Choose a supported rounding mode.")
            try:
                decimal_places = int(places_text)
            except ValueError as exc:
                raise WebInputError("Decimal places must be a whole number.") from exc
            conversion = convert(
                value,
                source,
                target,
                decimal_places=decimal_places,
                rounding_mode={
                    "half-even": "ROUND_HALF_EVEN",
                    "half-up": "ROUND_HALF_UP",
                    "down": "ROUND_DOWN",
                }[rounding_argument],
            )
            source = conversion.source_unit
            target = conversion.target_unit
            receipt = build_receipt(conversion)
    except (ConversionError, WebInputError):
        error = PUBLIC_INPUT_ERROR

    content = render_page(
        value=value,
        source=source if source in UNITS else "mi",
        target=target if target in UNITS else "km",
        places=places_text,
        rounding=rounding_argument,
        conversion=conversion,
        receipt=receipt,
        error=error,
        submitted=submitted,
    ).encode("utf-8")
    start_response(f"{HTTPStatus.OK.value} {HTTPStatus.OK.phrase}", _headers(content))
    return [] if method == "HEAD" else [content]


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    if not 1 <= port <= 65_535:
        raise ValueError("Port must be between 1 and 65535.")
    with make_server(host, port, application) as server:
        print(f"MeasureTrace listening on http://{host}:{port}", flush=True)
        server.serve_forever()


def main() -> None:
    serve()


if __name__ == "__main__":
    main()
