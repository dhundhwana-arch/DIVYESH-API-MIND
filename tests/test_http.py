from __future__ import annotations

import base64
import io
import urllib.error
import urllib.parse
import unittest

from divyesh_api_mind import APIConnector, APIError, CredentialError, SafeHTTPTransport, UnsafeRequestError, build_url
from divyesh_api_mind.api_client import APIClient
from divyesh_api_mind.transport import HTTPResult


class RecordingTransport:
    def __init__(self, result: HTTPResult | None = None, user_agent: str = "test-agent/1.0") -> None:
        self.result = result or HTTPResult(200, {"content-type": "application/json"}, b'{"ok":true}')
        self.user_agent = user_agent
        self.calls: list[dict[str, object]] = []

    def request(self, record_id, method, url, **kwargs):  # noqa: ANN001
        self.calls.append({"record_id": record_id, "method": method, "url": url, **kwargs})
        return self.result


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200, headers: dict[str, str] | None = None) -> None:
        self.body = body
        self.status = status
        self.headers = headers or {"Content-Length": str(len(body))}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, size=-1):
        return self.body if size < 0 else self.body[:size]

    def getcode(self):
        return self.status


class SequenceOpener:
    def __init__(self, outcomes):  # noqa: ANN001
        self.outcomes = list(outcomes)
        self.requests = []

    def open(self, request, timeout):  # noqa: ANN001
        self.requests.append(request)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class URLSafetyTests(unittest.TestCase):
    def test_build_url_encodes_query_and_omits_none(self) -> None:
        url = build_url(
            "https://api.example.com/v1",
            "/items",
            {"q": "Ahmedabad weather", "tag": ["a", "b"], "skip": None},
            allowed_hosts={"api.example.com"},
        )
        parsed = urllib.parse.urlsplit(url)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.path, "/v1/items")
        unicode_url = build_url(
            "https://api.example.com/v1",
            "caf\u00e9",
            allowed_hosts={"api.example.com"},
        )
        self.assertEqual(urllib.parse.urlsplit(unicode_url).path, "/v1/caf%C3%A9")
        self.assertEqual(urllib.parse.parse_qs(parsed.query), {"q": ["Ahmedabad weather"], "tag": ["a", "b"]})

    def test_build_url_rejects_external_or_unsafe_targets(self) -> None:
        cases = [
            ("http://api.example.com", "", {"api.example.com"}),
            ("https://user:pass@api.example.com", "", {"api.example.com"}),
            ("https://api.example.com:444", "", {"api.example.com"}),
            ("https://localhost", "", {"localhost"}),
            ("https://127.0.0.1", "", {"127.0.0.1"}),
            ("https://api.example.com", "//elsewhere.example/path", {"api.example.com"}),
            ("https://api.example.com", "../admin", {"api.example.com"}),
            ("https://api.example.com", "%2e%2e/private", {"api.example.com"}),
            ("https://api.example.com", "path?redirect=https://elsewhere.example", {"api.example.com"}),
            ("https://api.example.com", "path\\..\\secret", {"api.example.com"}),
        ]
        for base_url, path, hosts in cases:
            with self.subTest(base_url=base_url, path=path):
                with self.assertRaises(UnsafeRequestError):
                    build_url(base_url, path, allowed_hosts=hosts)

    def test_direct_transport_rechecks_public_allowlist(self) -> None:
        opener = SequenceOpener([FakeResponse(b"ok")])
        transport = SafeHTTPTransport(opener=opener)
        with self.assertRaises(UnsafeRequestError):
            transport.request(
                "test",
                "GET",
                "https://127.0.0.1/path",
                allowed_hosts={"127.0.0.1"},
            )
        self.assertEqual(opener.requests, [])

    def test_transport_blocks_header_injection_and_managed_headers(self) -> None:
        transport = SafeHTTPTransport(opener=SequenceOpener([FakeResponse(b"ok")]))
        for headers in ({"X-Test": "a\r\nb"}, {"Content-Length": "0"}, {"Cookie": "session=secret"}):
            with self.subTest(headers=headers):
                with self.assertRaises(UnsafeRequestError):
                    transport.request(
                        "test",
                        "GET",
                        "https://api.example.com/path",
                        allowed_hosts={"api.example.com"},
                        headers=headers,
                    )

    def test_get_retries_transient_status_and_captures_limited_response(self) -> None:
        opener = SequenceOpener(
            [
                urllib.error.HTTPError(
                    "https://api.example.com/path",
                    503,
                    "Unavailable",
                    {"Retry-After": "0"},
                    io.BytesIO(b""),
                ),
                FakeResponse(b'{"ok":true}', status=202, headers={"Content-Length": "11", "Content-Type": "application/json"}),
            ]
        )
        sleeps: list[float] = []
        transport = SafeHTTPTransport(opener=opener, sleep=sleeps.append, retries=2)
        with self.assertLogs("divyesh_api_mind.http", level="WARNING") as captured:
            result = transport.request(
                "demo",
                "GET",
                "https://api.example.com/path",
                allowed_hosts={"api.example.com"},
            )
        self.assertIn("status=503", captured.output[0])
        self.assertEqual(result.status_code, 202)
        self.assertEqual(result.body, b'{"ok":true}')
        self.assertEqual(len(opener.requests), 2)
        self.assertEqual(sleeps, [0.0])

    def test_post_is_not_retried_and_errors_are_sanitized(self) -> None:
        token = "a-secret-that-must-not-appear"
        opener = SequenceOpener(
            [urllib.error.HTTPError("https://api.example.com/path?token=" + token, 503, "Unavailable", {}, io.BytesIO())]
        )
        transport = SafeHTTPTransport(opener=opener, retries=3)
        with self.assertRaises(APIError) as caught:
            transport.request(
                "demo",
                "POST",
                "https://api.example.com/path",
                allowed_hosts={"api.example.com"},
                body=b"payload",
            )
        self.assertEqual(len(opener.requests), 1)
        self.assertEqual(caught.exception.attempts, 1)
        self.assertNotIn(token, str(caught.exception))
        self.assertNotIn("https://", str(caught.exception))

    def test_response_size_limit_is_enforced(self) -> None:
        transport = SafeHTTPTransport(opener=SequenceOpener([FakeResponse(b"1234")]), max_response_bytes=3)
        with self.assertRaises(APIError) as caught:
            transport.request(
                "demo",
                "GET",
                "https://api.example.com/path",
                allowed_hosts={"api.example.com"},
            )
        self.assertIn("size limit", str(caught.exception))

    def test_per_request_response_cap_can_only_reduce_transport_limit(self) -> None:
        transport = SafeHTTPTransport(opener=SequenceOpener([FakeResponse(b"1234")]), max_response_bytes=100)
        with self.assertRaises(APIError):
            transport.request(
                "docs",
                "GET",
                "https://docs.example.com/page",
                allowed_hosts={"docs.example.com"},
                max_response_bytes=3,
            )
        with self.assertRaises(ValueError):
            transport.request(
                "docs",
                "GET",
                "https://docs.example.com/page",
                allowed_hosts={"docs.example.com"},
                max_response_bytes=101,
            )


class APIClientTests(unittest.TestCase):
    def test_bearer_auth_comes_from_environment_and_is_not_overridden(self) -> None:
        transport = RecordingTransport()
        client = APIClient(
            {
                "demo": {
                    "base_url": "https://api.example.com/v1",
                    "allowed_hosts": ["api.example.com"],
                    "authentication": {"kind": "bearer", "required": True, "env_var": "DEMO_TOKEN"},
                }
            },
            transport=transport,
            env={"DEMO_TOKEN": "do-not-log-this"},
        )
        self.assertTrue(client.has_credentials("demo"))
        self.assertEqual(client.request_json("demo", "records"), {"ok": True})
        call = transport.calls[0]
        self.assertEqual(call["headers"]["Authorization"], "Bearer do-not-log-this")
        self.assertEqual(call["url"], "https://api.example.com/v1/records")
        with self.assertRaises(CredentialError):
            client.request_json("demo", "records", headers={"authorization": "Bearer attacker"})
        self.assertEqual(len(transport.calls), 1)

    def test_missing_required_credentials_fail_before_transport(self) -> None:
        transport = RecordingTransport()
        client = APIClient(
            {
                "demo": {
                    "base_url": "https://api.example.com",
                    "allowed_hosts": ["api.example.com"],
                    "authentication": {"kind": "api_key_header", "required": True, "env_var": "DEMO_KEY"},
                }
            },
            transport=transport,
            env={},
        )
        self.assertFalse(client.has_credentials("demo"))
        with self.assertRaises(CredentialError) as caught:
            client.request_json("demo")
        self.assertIn("DEMO_KEY", str(caught.exception))
        self.assertEqual(transport.calls, [])

    def test_unverified_authentication_blocks_calls(self) -> None:
        transport = RecordingTransport()
        client = APIClient(
            {
                "needs-review": {
                    "base_url": "https://api.example.com",
                    "allowed_hosts": ["api.example.com"],
                    "authentication": {"kind": "unknown", "required": False, "verified": False},
                }
            },
            transport=transport,
            env={},
        )
        self.assertFalse(client.has_credentials("needs-review"))
        with self.assertRaises(CredentialError) as caught:
            client.request_json("needs-review")
        self.assertIn("unverified", str(caught.exception))
        self.assertEqual(transport.calls, [])

    def test_caller_cannot_supply_query_credentials(self) -> None:
        client = APIClient(
            {
                "demo": {
                    "base_url": "https://api.example.com",
                    "allowed_hosts": ["api.example.com"],
                    "authentication": {
                        "kind": "api_key_query",
                        "required": False,
                        "env_var": "DEMO_KEY",
                        "parameter": "key",
                    },
                }
            },
            transport=RecordingTransport(),
            env={},
        )
        with self.assertRaises(CredentialError):
            client.request_json("demo", params={"key": "caller-supplied-secret"})

    def test_query_credentials_are_encoded_and_not_returned_in_errors(self) -> None:
        transport = RecordingTransport(HTTPResult(401, {}, b""))
        client = APIClient(
            {
                "demo": {
                    "base_url": "https://api.example.com",
                    "allowed_hosts": ["api.example.com"],
                    "authentication": {
                        "kind": "api_key_query",
                        "required": True,
                        "env_var": "DEMO_KEY",
                        "parameter": "key",
                    },
                }
            },
            transport=transport,
            env={"DEMO_KEY": "secret value"},
        )
        with self.assertRaises(APIError) as caught:
            client.request_json("demo", params={"q": "hello world"})
        self.assertEqual(urllib.parse.parse_qs(urllib.parse.urlsplit(transport.calls[0]["url"]).query), {"q": ["hello world"], "key": ["secret value"]})
        self.assertNotIn("secret value", str(caught.exception))
        self.assertNotIn("https://", str(caught.exception))

    def test_http_basic_pair_and_form_body(self) -> None:
        transport = RecordingTransport()
        client = APIClient(
            {
                "demo": {
                    "base_url": "https://api.example.com",
                    "allowed_hosts": ["api.example.com"],
                    "authentication": {
                        "kind": "http_basic_pair",
                        "required": True,
                        "username_env": "DEMO_USER",
                        "password_env": "DEMO_PASSWORD",
                    },
                }
            },
            transport=transport,
            env={"DEMO_USER": "AC123", "DEMO_PASSWORD": "private-token"},
        )
        client.request_raw("demo", "Messages", method="POST", form_body={"Body": "hello world", "To": "+911234"})
        call = transport.calls[0]
        self.assertEqual(call["headers"]["Authorization"], "Basic " + base64.b64encode(b"AC123:private-token").decode())
        self.assertEqual(call["headers"]["Content-Type"], "application/x-www-form-urlencoded")
        self.assertEqual(call["body"], b"Body=hello+world&To=%2B911234")

    def test_text_and_json_response_helpers(self) -> None:
        transport = RecordingTransport(HTTPResult(200, {"content-type": "application/atom+xml"}, b"<feed>ok</feed>"))
        client = APIClient(
            {"demo": {"base_url": "https://api.example.com", "allowed_hosts": ["api.example.com"], "authentication": {"kind": "none"}}},
            transport=transport,
        )
        self.assertEqual(client.request_text("demo"), "<feed>ok</feed>")
        with self.assertRaises(APIError):
            client.request_json("demo")

    def test_health_status_and_connector_health(self) -> None:
        transport = RecordingTransport(HTTPResult(202, {}, b""))
        client = APIClient(
            {
                "demo": {
                    "base_url": "https://api.example.com",
                    "allowed_hosts": ["api.example.com"],
                    "authentication": {"kind": "none"},
                    "health_probe": {"method": "GET", "path": "status", "params": {}},
                }
            },
            transport=transport,
        )
        self.assertEqual(client._health_check("demo")[0], 202)
        self.assertEqual(client.health_check("demo")["http_status"], 202)
        self.assertEqual(APIConnector(client, "demo").health_check()["http_status"], 202)

    def test_openalex_optional_key_uses_catalogued_query_parameter(self) -> None:
        from divyesh_api_mind import APIMind

        transport = RecordingTransport()
        mind = APIMind(transport=transport, env={"OPENALEX_API_KEY": "openalex-key-value"})
        mind.connector("openalex").search_works("climate", per_page=2)
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(transport.calls[0]["url"]).query)
        self.assertEqual(query["api_key"], ["openalex-key-value"])
        self.assertEqual(query["per-page"], ["2"])

    def test_catalog_special_connectors_keep_provider_policy(self) -> None:
        from divyesh_api_mind import APIMind
        import divyesh_api_mind.connectors as connector_module

        connector_module._ARXIV_LAST_REQUEST = 0.0
        arxiv_transport = RecordingTransport(HTTPResult(200, {"content-type": "application/atom+xml"}, b"<feed/>") )
        arxiv_mind = APIMind(transport=arxiv_transport)
        arxiv = arxiv_mind.connector("arxiv")
        self.assertEqual(arxiv.search("graph neural networks", max_results=3), "<feed/>")
        self.assertEqual(arxiv_transport.calls[0]["retries"], 0)
        self.assertIn("search_query=all%3Agraph+neural+networks", arxiv_transport.calls[0]["url"])
        with self.assertRaises(UnsafeRequestError):
            arxiv.get_json("query")

        connector_module._NOMINATIM_LAST_REQUEST = 0.0
        nominatim_transport = RecordingTransport()
        nominatim_mind = APIMind(
            transport=nominatim_transport,
            user_agent="Example App/1.0 (contact: owner@example.invalid)",
        )
        nominatim = nominatim_mind.connector("nominatim", acknowledge_policy=True)
        self.assertEqual(nominatim.search("Ahmedabad", limit=2), {"ok": True})
        self.assertEqual(nominatim_transport.calls[0]["retries"], 0)
        self.assertEqual(
            nominatim_transport.calls[0]["headers"]["User-Agent"],
            "Example App/1.0 (contact: owner@example.invalid)",
        )
        with self.assertRaises(UnsafeRequestError):
            nominatim.get_json("search", params={"q": "bypass"})
        with self.assertRaises(UnsafeRequestError):
            nominatim.get_raw("search", params={"q": "bypass"})


if __name__ == "__main__":
    unittest.main()
