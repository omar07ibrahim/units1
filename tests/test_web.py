from __future__ import annotations

import unittest
from unittest.mock import patch
from urllib.parse import urlencode

from measuretrace.core import ConversionError
from measuretrace.web import application


def request(path: str = "/", query: str = "", method: str = "GET"):
    captured: dict[str, object] = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)

    body = b"".join(
        application(
            {
                "REQUEST_METHOD": method,
                "PATH_INFO": path,
                "QUERY_STRING": query,
            },
            start_response,
        )
    )
    return captured["status"], captured["headers"], body.decode("utf-8")


class WebTests(unittest.TestCase):
    def test_initial_page_is_semantic_responsive_and_dependency_free(self) -> None:
        status, headers, body = request()
        self.assertEqual(status, "200 OK")
        self.assertIn('<html lang="en">', body)
        self.assertIn('name="viewport"', body)
        self.assertIn('href="#main"', body)
        self.assertIn('<main id="main">', body)
        self.assertIn('action="/#result"', body)
        self.assertIn('label for="value"', body)
        self.assertIn('label for="from"', body)
        self.assertIn('label for="to"', body)
        self.assertIn("@media (max-width: 780px)", body)
        self.assertIn("@media (max-width: 1200px)", body)
        self.assertIn("width: min(1200px, calc(100% - 2rem));", body)
        self.assertIn('class="field-row direction-row"', body)
        self.assertIn(
            "grid-template-columns: minmax(0, 1.15fr) auto minmax(0, 0.85fr);",
            body,
        )
        self.assertNotIn("bootstrap", body.lower())
        self.assertNotIn("<script", body.lower())
        self.assertNotIn("debug", body.lower())
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertIn("default-src 'none'", headers["Content-Security-Policy"])
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["X-Frame-Options"], "DENY")

    def test_exact_result_and_receipt_are_rendered(self) -> None:
        query = urlencode(
            {
                "value": "1",
                "from": "mi",
                "to": "km",
                "places": "6",
                "rounding": "half-even",
                "action": "convert",
            }
        )
        status, _headers, body = request(query=query)
        self.assertEqual(status, "200 OK")
        self.assertIn("1.609344", body)
        self.assertIn("25146/15625", body)
        self.assertIn(
            '<option value="mi" selected>International mile (mi)</option>',
            body,
        )
        self.assertIn('role="status"', body)
        self.assertIn('<section class="card result-card" id="result"', body)
        self.assertNotIn("autofocus", body)
        self.assertIn("receipt_sha256", body)

    def test_zero_result_is_visible(self) -> None:
        query = urlencode(
            {
                "value": "0",
                "from": "mi",
                "to": "km",
                "places": "6",
                "rounding": "half-even",
            }
        )
        _status, _headers, body = request(query=query)
        self.assertIn("0.000000", body)
        self.assertIn("0/1", body)

    def test_errors_are_actionable_and_focusable(self) -> None:
        query = urlencode(
            {
                "value": "NaN",
                "from": "m",
                "to": "km",
                "places": "6",
                "rounding": "half-even",
            }
        )
        _status, _headers, body = request(query=query)
        self.assertIn('role="alert"', body)
        self.assertIn('aria-invalid="true"', body)
        self.assertIn("Check the measurement", body)
        self.assertIn("autofocus", body)

    def test_internal_conversion_details_are_not_exposed(self) -> None:
        query = urlencode(
            {
                "value": "1",
                "from": "mi",
                "to": "km",
                "places": "6",
                "rounding": "half-even",
            }
        )
        with patch(
            "measuretrace.web.convert",
            side_effect=ConversionError("internal implementation detail"),
        ):
            status, _headers, body = request(query=query)
        self.assertEqual(status, "200 OK")
        self.assertIn("Check the measurement", body)
        self.assertNotIn("internal implementation detail", body)

    def test_swap_preserves_value_and_converts_in_new_direction(self) -> None:
        query = urlencode(
            {
                "value": "1",
                "from": "mi",
                "to": "km",
                "places": "6",
                "rounding": "half-even",
                "action": "swap",
            }
        )
        _status, _headers, body = request(query=query)
        self.assertIn('<option value="km" selected>', body)
        self.assertIn('<option value="mi" selected>', body)
        self.assertIn("0.621371", body)

    def test_request_shape_is_bounded(self) -> None:
        _status, _headers, body = request(query="value=1&value=2")
        self.assertIn("Check the measurement", body)

        _status, _headers, body = request(query="unexpected=value")
        self.assertIn("Check the measurement", body)

    def test_not_found_and_method_not_allowed(self) -> None:
        status, _headers, body = request(path="/missing")
        self.assertEqual(status, "404 Not Found")
        self.assertEqual(body, "Not found\n")

        status, headers, body = request(method="POST")
        self.assertEqual(status, "405 Method Not Allowed")
        self.assertEqual(headers["Allow"], "GET, HEAD")
        self.assertEqual(body, "Method not allowed\n")

    def test_head_has_headers_without_body(self) -> None:
        status, headers, body = request(method="HEAD")
        self.assertEqual(status, "200 OK")
        self.assertEqual(body, "")
        self.assertGreater(int(headers["Content-Length"]), 1000)


if __name__ == "__main__":
    unittest.main()
