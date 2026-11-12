from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from divyesh_api_mind.discovery import (
    combine_review_queues,
    import_api_atlas_jsonl,
    import_openapi_spec,
    import_public_apis_markdown,
    load_review_queue,
    read_discovery_source,
    search_review_queue,
    validate_review_queue,
)
from divyesh_api_mind.exceptions import UnsafeRequestError
from divyesh_api_mind.transport import HTTPResult


class RecordingTransport:
    def __init__(self, response: HTTPResult) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def request(self, record_id, method, url, **kwargs):  # noqa: ANN001
        self.calls.append({"record_id": record_id, "method": method, "url": url, **kwargs})
        return self.response


class DiscoveryImportTests(unittest.TestCase):
    def test_public_apis_rows_are_unknown_attributed_candidates_and_deduplicated(self) -> None:
        markdown = """# Directory intro

## Index
### Data
| API | Description | Auth | HTTPS | CORS |
|:---|:---|:---|:---|:---|
| [Sample API](https://sample.example/docs?utm_source=list) | Public data | No | Yes | Yes |
### Science
| API | Description | Auth | HTTPS | CORS |
|:---|:---|:---|:---|:---|
| [Sample API](https://sample.example/docs) | Public data | No | Yes | Yes |
| [Sample API](https://different.example/docs) | Another entry | `apiKey` | Yes | Unknown |
## License
"""
        queue = import_public_apis_markdown(
            markdown,
            source_url="https://github.com/public-apis/public-apis/blob/main/README.md",
            revision="cb581147b5e7c808cc2db43c5c590b51679dd44c",
            checked_on="2026-11-12",
        )
        self.assertEqual(queue["counts"]["source_rows"], 3)
        self.assertEqual(queue["counts"]["unique_candidates"], 2)
        self.assertEqual(queue["counts"]["exact_duplicate_rows_merged"], 1)
        self.assertEqual(queue["counts"]["possible_duplicate_candidates"], 2)
        self.assertEqual(queue["counts"]["categories"], 2)
        first = next(candidate for candidate in queue["candidates"] if candidate["listed_url"].startswith("https://sample"))
        self.assertEqual(first["free_status"], "UNKNOWN")
        self.assertEqual(first["authentication"]["kind"], "unknown")
        self.assertFalse(first["authentication"]["verified"])
        self.assertEqual(first["source_claims"]["authentication"], "No")
        self.assertEqual(first["quota"], "UNKNOWN")
        self.assertEqual(first["license"], "UNKNOWN")
        self.assertEqual(first["attribution"]["license"], "MIT")
        self.assertEqual(len(first["source_attributions"]), 2)
        self.assertTrue(first["possible_duplicate_flags"])
        self.assertEqual(first["review_status"], "needs_primary_source_review")
        self.assertFalse(queue["policy"]["automatic_catalog_promotion"])

    def test_api_atlas_import_preserves_upstream_claims_but_never_promotes_them(self) -> None:
        rows = [
            {
                "type": "API",
                "id": "example.com/sample-api",
                "name": "Sample API",
                "category": "science-research",
                "description": "Official research data API",
                "website": "https://example.com/api",
                "docs": "https://docs.example.com/api",
                "access": "Free",
                "auth": "None",
                "license": "CC BY 4.0",
                "source": "editorial",
                "checked": "2026-10-26",
                "verified": True,
                "docs_present": True,
                "license_known": True,
            },
            {
                "type": "API",
                "id": "other.example/api",
                "name": "Second API",
                "category": "data-analytics",
                "description": "Upstream pointer without a reviewed docs date",
                "website": "https://other.example/api",
                "docs": None,
                "access": "Free tier",
                "auth": "API key",
                "license": "-",
                "source": "public-apis, APIs.guru",
                "checked": None,
                "verified": False,
                "docs_present": False,
                "license_known": False,
            },
            {"type": "Portal", "id": "portal.example", "name": "Not an API"},
        ]
        content = "\n".join(json.dumps(row) for row in rows)
        queue = import_api_atlas_jsonl(
            content,
            source_url="https://github.com/CTCycle/api-atlas/blob/547dae1fcc8356b11091200c76906787cc817ebc/data/catalog.jsonl",
            revision="547dae1fcc8356b11091200c76906787cc817ebc",
            checked_on="2026-11-12",
        )
        self.assertEqual(queue["counts"]["source_rows"], 2)
        self.assertEqual(queue["counts"]["unique_candidates"], 2)
        self.assertEqual(queue["counts"]["api_rows_marked_verified_upstream"], 1)
        self.assertEqual(queue["source"]["non_api_rows_excluded"], 1)
        verified = next(candidate for candidate in queue["candidates"] if candidate["name"] == "Sample API")
        self.assertEqual(verified["free_status"], "UNKNOWN")
        self.assertEqual(verified["license"], "UNKNOWN")
        self.assertEqual(verified["authentication"]["kind"], "unknown")
        self.assertFalse(verified["authentication"]["verified"])
        self.assertEqual(verified["quota"], "UNKNOWN")
        self.assertEqual(verified["rate_limits"], "UNKNOWN")
        self.assertEqual(verified["review_status"], "needs_primary_source_review")
        self.assertEqual(verified["review_priority"], "upstream_checked_pointer")
        self.assertEqual(verified["source_claims"]["api_atlas_access"], "Free")
        self.assertEqual(verified["source_claims"]["api_atlas_auth"], "None")
        self.assertEqual(verified["source_claims"]["api_atlas_license"], "CC BY 4.0")
        self.assertIs(verified["source_claims"]["api_atlas_verified"], True)
        self.assertEqual(verified["source_claims"]["api_atlas_checked"], "2026-10-26")
        self.assertIs(verified["source_claims"]["docs_present"], True)
        self.assertIs(verified["source_claims"]["license_known"], True)
        self.assertEqual(verified["attribution"]["catalog_license"], "CC BY 4.0")
        self.assertEqual(verified["attribution"]["upstream_license_claims"]["editorial"], "CC BY 4.0 catalog content")
        self.assertEqual(verified["documentation_url"], "https://docs.example.com/api")
        unverified = next(candidate for candidate in queue["candidates"] if candidate["name"] == "Second API")
        self.assertIs(unverified["source_claims"]["api_atlas_verified"], False)
        self.assertIsNone(unverified["source_claims"]["api_atlas_checked"])
        self.assertEqual(unverified["source_claims"]["api_atlas_license"], "-")
        self.assertEqual(unverified["review_priority"], "unverified_directory_pointer")
        self.assertTrue(validate_review_queue(queue) == [])
        self.assertEqual(len(search_review_queue(queue, priority="upstream_checked_pointer")), 1)
        self.assertEqual(len(search_review_queue(queue, priority="unverified_directory_pointer")), 1)
        self.assertTrue(queue["policy"]["automatic_catalog_promotion"] is False)

        public_queue = import_public_apis_markdown(
            """## Index
### Science
| API | Description | Auth | HTTPS | CORS |
|---|---|---|---|---|
| [Sample API](https://example.com/api) | Example lead | Unknown | Yes | Unknown |
""",
            source_url="https://github.com/public-apis/public-apis/blob/cb581147b5e7c808cc2db43c5c590b51679dd44c/README.md",
            revision="cb581147b5e7c808cc2db43c5c590b51679dd44c",
            checked_on="2026-11-12",
        )
        merged = combine_review_queues([public_queue, queue])
        merged_sample = next(candidate for candidate in merged["candidates"] if candidate["name"] == "Sample API")
        self.assertEqual(merged_sample["review_priority"], "upstream_checked_pointer")
        self.assertEqual(len(merged_sample["source_claims_by_source"]), 2)

        with self.assertRaisesRegex(ValueError, "Git commit hash"):
            import_api_atlas_jsonl(
                content,
                source_url="https://github.com/CTCycle/api-atlas/blob/main/data/catalog.jsonl",
                revision="main",
                checked_on="2026-11-12",
            )

    def test_public_apis_parser_rejects_unsafe_urls_and_bad_revision(self) -> None:
        markdown = """## Index
### Test
| API | Description | Auth | HTTPS | CORS |
|---|---|---|---|---|
| [Unsafe](https://user:pass@example.com/path) | x | No | Yes | No |
"""
        with self.assertRaises(ValueError):
            import_public_apis_markdown(
                markdown,
                source_url="https://github.com/public-apis/public-apis/README.md",
                revision="main",
            )

    def test_openapi_3_candidate_extracts_servers_paths_and_security_without_free_claims(self) -> None:
        spec = {
            "openapi": "3.0.3",
            "info": {
                "title": "Example Pet API",
                "version": "1.2.0",
                "description": "Read pets and submit a pet.",
                "license": {"name": "Apache-2.0", "url": "https://example.com/license"},
            },
            "servers": [{"url": "https://api.example.com/v1"}],
            "externalDocs": {"url": "https://docs.example.com/guide"},
            "components": {
                "securitySchemes": {"accessKey": {"type": "apiKey", "in": "header", "name": "X-Example-Key"}}
            },
            "security": [{"accessKey": []}],
            "tags": [{"name": "Pets"}],
            "paths": {
                "/pets": {
                    "get": {"operationId": "listPets", "summary": "List pets", "tags": ["Pets"]},
                    "post": {"summary": "Create a pet", "security": [{"accessKey": []}]},
                }
            },
        }
        queue = import_openapi_spec(
            json.dumps(spec),
            source_url="https://api.example.com/openapi.json",
            checked_on="2026-11-12",
        )
        candidate = queue["candidates"][0]
        self.assertEqual(candidate["name"], "Example Pet API")
        self.assertEqual(candidate["base_url"], "https://api.example.com/v1")
        self.assertEqual(candidate["endpoint_count_in_spec"], 2)
        self.assertEqual(candidate["endpoints"][0]["method"], "GET")
        self.assertEqual(candidate["authentication"]["kind"], "unknown")
        self.assertTrue(candidate["authentication_evidence"]["declared_by_spec"])
        self.assertEqual(candidate["authentication_evidence"]["scheme_names"], ["accessKey"])
        self.assertEqual(candidate["authentication_evidence"]["scheme_details"]["accessKey"]["name"], "X-Example-Key")
        self.assertEqual(candidate["free_status"], "UNKNOWN")
        self.assertEqual(candidate["quota"], "UNKNOWN")
        self.assertEqual(candidate["rate_limits"], "UNKNOWN")
        self.assertEqual(candidate["license"], "UNKNOWN")
        self.assertEqual(candidate["spec_license"]["name"], "Apache-2.0")
        self.assertEqual(candidate["listed_url"], "https://docs.example.com/guide")
        self.assertEqual(candidate["review_status"], "needs_primary_source_review")

    def test_queue_validation_rejects_free_claims_and_missing_provenance(self) -> None:
        from divyesh_api_mind import CatalogError, validate_review_queue

        queue = import_openapi_spec(
            {
                "openapi": "3.0.0",
                "info": {"title": "Review me", "version": "1"},
                "servers": [{"url": "https://review.example.com"}],
                "paths": {"/items": {"get": {}}},
            },
            source_url="https://review.example.com/openapi.json",
        )
        self.assertEqual(validate_review_queue(queue), [])
        queue["candidates"][0]["free_status"] = "FREE_NO_KEY"
        self.assertTrue(any("must remain UNKNOWN" in error for error in validate_review_queue(queue)))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.json"
            path.write_text(json.dumps(queue), encoding="utf-8")
            with self.assertRaises(CatalogError):
                load_review_queue(path)

    def test_openapi_v2_and_invalid_specs(self) -> None:
        queue = import_openapi_spec(
            {
                "swagger": "2.0",
                "info": {"title": "Legacy API", "version": "1"},
                "host": "legacy.example.com",
                "basePath": "/v2",
                "schemes": ["http", "https"],
                "paths": {"/items": {"get": {"summary": "Items"}}},
            },
            source_url="https://github.com/example/specs/blob/main/legacy.json",
        )
        self.assertEqual(queue["candidates"][0]["base_url"], "https://legacy.example.com/v2")
        self.assertEqual(queue["candidates"][0]["authentication"]["kind"], "unknown")
        with self.assertRaises(ValueError):
            import_openapi_spec({"info": {"title": "Not OpenAPI"}}, source_url="https://example.com/spec.json")

    def test_queue_round_trip_and_local_search(self) -> None:
        queue = import_openapi_spec(
            {
                "openapi": "3.0.0",
                "info": {"title": "Weather Service", "version": "1"},
                "servers": [{"url": "https://weather.example.com"}],
                "tags": [{"name": "Weather"}],
                "paths": {"/forecast": {"get": {"tags": ["Weather"], "summary": "Forecast"}}},
            },
            source_url="https://weather.example.com/openapi.json",
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queue.json"
            path.write_text(json.dumps(queue), encoding="utf-8")
            loaded = load_review_queue(path)
            self.assertEqual(len(search_review_queue(loaded, query="forecast")), 1)
            self.assertEqual(len(search_review_queue(loaded, category="weather")), 1)
            self.assertEqual(search_review_queue(loaded, limit=0), [])

    def test_merge_queues_deduplicates_exact_leads_without_losing_attribution(self) -> None:
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Shared API", "version": "1"},
            "servers": [{"url": "https://shared.example.com/v1"}],
            "paths": {"/items": {"get": {"summary": "List items"}}},
        }
        first = import_openapi_spec(spec, source_url="https://github.com/vendor/spec-a.json", checked_on="2026-11-10")
        second = import_openapi_spec(spec, source_url="https://github.com/vendor/spec-b.json", checked_on="2026-11-12")
        merged = combine_review_queues([first, second])
        self.assertEqual(merged["counts"]["unique_candidates"], 1)
        self.assertEqual(merged["counts"]["exact_duplicate_rows_merged"], 1)
        self.assertEqual(len(merged["candidates"][0]["source_attributions"]), 2)
        self.assertEqual(len(merged["candidates"][0]["evidence_sources"]), 2)
        self.assertEqual(merged["generated_on"], "2026-11-12")

    def test_safe_github_contents_fetch_decodes_base64_and_refuses_other_destinations(self) -> None:
        body = json.dumps({"encoding": "base64", "content": "IyBIZWxsbwo="}).encode("utf-8")
        transport = RecordingTransport(HTTPResult(200, {"content-type": "application/json"}, body))
        result = read_discovery_source(
            "https://api.github.com/repos/public-apis/public-apis/contents/README.md",
            transport=transport,
        )
        self.assertEqual(result, b"# Hello\n")
        self.assertEqual(transport.calls[0]["retries"], 0)
        self.assertEqual(transport.calls[0]["max_response_bytes"], 2 * 1024 * 1024)
        with self.assertRaises((ValueError, UnsafeRequestError)):
            read_discovery_source("https://127.0.0.1/private", transport=transport)
        with self.assertRaises(ValueError):
            read_discovery_source("https://api.github.com/repos/example/repo/contents/spec.json?token=secret", transport=transport)


if __name__ == "__main__":
    unittest.main()
