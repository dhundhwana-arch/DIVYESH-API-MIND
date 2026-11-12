from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from divyesh_api_mind import (
    APIMind,
    CatalogError,
    CredentialError,
    MCPRegistry,
    UnknownRecordError,
    UnsafeRequestError,
    validate_catalog_data,
    validate_catalog_directory,
)
from divyesh_api_mind.cli import main
from divyesh_api_mind.transport import HTTPResult

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "src" / "divyesh_api_mind" / "data"


class RecordingTransport:
    def __init__(self, result: HTTPResult | None = None) -> None:
        self.result = result or HTTPResult(200, {"content-type": "application/json"}, b'{"ok":true}')
        self.calls: list[dict[str, object]] = []
        self.user_agent = "test-agent/1.0"

    def request(self, record_id, method, url, **kwargs):  # noqa: ANN001
        self.calls.append({"record_id": record_id, "method": method, "url": url, **kwargs})
        return self.result


class CatalogTests(unittest.TestCase):
    def test_bundled_catalogs_load_and_have_unique_ids(self) -> None:
        mind = APIMind()
        self.assertEqual(mind.counts, {"apis": 26, "models": 5, "datasets": 8})
        self.assertEqual(sum(mind.counts.values()), 39)
        self.assertEqual(len({record["id"] for record in mind.search()}), 39)
        self.assertEqual(mind.get("world-bank-indicators-dataset")["type"], "dataset")

    def test_catalogs_validate_locally(self) -> None:
        results = validate_catalog_directory(DATA_DIR)
        self.assertEqual(results, {"apis": [], "models": [], "datasets": [], "mcp_registry": []})

    def test_search_filters_and_returns_defensive_copies(self) -> None:
        mind = APIMind()
        records = mind.search(kind="apis", category="RESEARCH", capability="scholarly", limit=5)
        self.assertTrue(records)
        self.assertTrue(all(record["type"] == "api" for record in records))
        original_name = mind.get("openalex")["name"]
        record = mind.get("openalex")
        record["name"] = "mutated"
        record["categories"].append("not-a-real-category")
        self.assertEqual(mind.get("openalex")["name"], original_name)
        with self.assertRaises(ValueError):
            mind.search(free_access="not-a-status")
        with self.assertRaises(ValueError):
            mind.search(limit=-1)

    def test_unknown_records_raise_typed_error(self) -> None:
        mind = APIMind()
        with self.assertRaises(UnknownRecordError):
            mind.get("no-such-record")
        with self.assertRaises(UnknownRecordError):
            mind.connector("no-such-api")

    def test_authentication_search_filters_are_explicit(self) -> None:
        mind = APIMind()
        no_auth = mind.search(no_auth=True)
        self.assertTrue(no_auth)
        self.assertTrue(all(item["type"] == "api" and item["authentication"]["kind"] == "none" for item in no_auth))
        self.assertEqual(mind.search(authentication="no-auth"), no_auth)
        required = mind.search(authentication="required")
        self.assertTrue(required)
        self.assertTrue(all(item["authentication"].get("required") is True for item in required))
        with self.assertRaises(ValueError):
            mind.search(no_auth=True, authentication="required")

    def test_document_fetch_is_explicit_bounded_and_uses_only_recorded_sources(self) -> None:
        transport = RecordingTransport(HTTPResult(200, {"content-type": "text/html; charset=utf-8"}, b"<h1>Docs</h1>"))
        mind = APIMind(transport=transport)
        refs = mind.get_docs("openalex")
        self.assertTrue(refs)
        result = mind.fetch_docs("openalex", source_index=0, max_bytes=4096)
        self.assertEqual(result["http_status"], 200)
        self.assertEqual(result["content"], "<h1>Docs</h1>")
        self.assertTrue(result["checked_at"].endswith("+00:00"))
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(transport.calls[0]["method"], "GET")
        self.assertEqual(transport.calls[0]["max_response_bytes"], 4096)
        self.assertEqual(transport.calls[0]["retries"], 0)
        self.assertNotIn("Authorization", transport.calls[0]["headers"])
        with self.assertRaises(ValueError):
            mind.fetch_docs("openalex", source_index=99)

    def test_templates_exports_and_alternatives_are_offline(self) -> None:
        transport = RecordingTransport()
        mind = APIMind(transport=transport)
        code = mind.integration_template("openalex")
        compile(code, "openalex-template.py", "exec")
        self.assertIn("client.get_json", code)
        self.assertIn("OPENALEX_API_KEY", code)
        nominatim = mind.integration_template("nominatim")
        compile(nominatim, "nominatim-template.py", "exec")
        self.assertIn("acknowledge_policy=True", nominatim)
        alternatives = mind.alternatives("openalex", limit=3)
        self.assertLessEqual(len(alternatives), 3)
        self.assertTrue(all(item["id"] != "openalex" for item in alternatives))
        self.assertTrue(all("compatibility_note" in item for item in alternatives))
        exported = json.loads(mind.export_records(["openalex", "crossref"], format="json"))
        self.assertEqual([item["id"] for item in exported], ["openalex", "crossref"])
        csv_text = mind.export_records(["openalex"], format="csv")
        self.assertIn("documentation_urls", csv_text.splitlines()[0])
        self.assertIn("openalex", csv_text)
        self.assertEqual(transport.calls, [])
        with self.assertRaises(ValueError):
            mind.export_records(["openalex", "openalex"])

    def test_mcp_registry_is_evidence_metadata_only(self) -> None:
        registry = MCPRegistry()
        listed = registry.list(status="directory_entry")
        self.assertEqual(len(registry.list()), 6)
        self.assertEqual(len(listed), registry.counts()["directory_entry"])
        self.assertEqual(registry.counts()["working_integration"], 0)
        record = registry.get("official-mcp-registry")
        self.assertFalse(record["health_checked"])
        record["name"] = "modified"
        self.assertNotEqual(registry.get("official-mcp-registry")["name"], "modified")
        with self.assertRaises(ValueError):
            registry.list(status="healthy")

    def test_invalid_mcp_record_is_rejected(self) -> None:
        document = json.loads((DATA_DIR / "mcp_registry.json").read_text(encoding="utf-8"))
        document["records"][0]["status"] = "healthy"
        self.assertTrue(validate_catalog_data(document, "mcp_registry"))
        document["records"][0]["status"] = {"unexpected": "object"}
        self.assertTrue(validate_catalog_data(document, "mcp_registry"))

    def test_validator_handles_malformed_categories_and_finds_embedded_secrets(self) -> None:
        document = json.loads((DATA_DIR / "apis.json").read_text(encoding="utf-8"))
        document["records"][0]["categories"] = [{"unexpected": "object"}]
        errors = validate_catalog_data(document, "apis")
        self.assertTrue(any("every category must be text" in error for error in errors))

        document = json.loads((DATA_DIR / "apis.json").read_text(encoding="utf-8"))
        document["records"][0]["summary"] = "Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456"
        errors = validate_catalog_data(document, "apis")
        self.assertTrue(any("possible credential" in error for error in errors))

    def test_health_check_preserves_actual_success_status(self) -> None:
        transport = RecordingTransport(HTTPResult(204, {}, b""))
        mind = APIMind(transport=transport)
        result = mind.health_check("world-bank-indicators")
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["http_status"], 204)
        self.assertEqual(len(transport.calls), 1)

    def test_connector_health_check_does_not_use_broken_factory(self) -> None:
        mind = APIMind(transport=RecordingTransport())
        result = mind.connector("openalex").health_check()
        self.assertEqual(result["status"], "not_configured")
        self.assertEqual(result["http_status"], None)

    def test_failed_health_probe_reports_http_status(self) -> None:
        mind = APIMind(transport=RecordingTransport(HTTPResult(503, {}, b"unavailable")))
        result = mind.health_check("world-bank-indicators")
        self.assertEqual(result["status"], "unhealthy")
        self.assertEqual(result["http_status"], 503)
        self.assertNotIn("https://", result["error"])

    def test_special_provider_requests_require_policy_connectors(self) -> None:
        mind = APIMind(transport=RecordingTransport())
        with self.assertRaises(UnsafeRequestError):
            mind.request("nominatim", "search", params={"q": "Ahmedabad"})
        with self.assertRaises(UnsafeRequestError):
            mind.request_text("arxiv", "query", params={"search_query": "all:test"})
        self.assertEqual(mind._client._transport.calls, [])

    def test_nominatim_requires_acknowledgement_and_identifying_user_agent(self) -> None:
        mind = APIMind()
        with self.assertRaises(ValueError):
            mind.connector("nominatim")
        with self.assertRaises(CredentialError):
            mind.connector("nominatim", acknowledge_policy=True)

    def test_cli_is_offline_and_validates_catalogs(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            status = main(["validate", "--catalog-dir", str(DATA_DIR)])
        self.assertEqual(status, 0)
        self.assertIn("apis: valid", stdout.getvalue())

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            status = main(["summary"])
        self.assertEqual(status, 0)
        summary = json.loads(stdout.getvalue())
        self.assertEqual(summary["catalogs"]["apis"], 26)
        self.assertEqual(summary["mcp_records"], 6)

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            status = main(
                [
                    "review-plan",
                    "--catalog-dir",
                    str(DATA_DIR),
                    "--days",
                    "180",
                    "--as-of",
                    "2027-05-11",
                ]
            )
        self.assertEqual(status, 0)
        review_queue = json.loads(stdout.getvalue())
        self.assertTrue(review_queue)
        self.assertTrue(review_queue[0]["sources"])

    def test_cli_search_docs_template_export_and_alternatives(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            status = main(["search", "--no-auth", "--kind", "api", "--limit", "2"])
        self.assertEqual(status, 0)
        self.assertTrue(all(item["authentication"]["kind"] == "none" for item in json.loads(stdout.getvalue())))

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            status = main(["docs", "openalex"])
        self.assertEqual(status, 0)
        self.assertTrue(json.loads(stdout.getvalue()))

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            status = main(["template", "openalex"])
        self.assertEqual(status, 0)
        self.assertIn("def request_example", stdout.getvalue())

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            status = main(["alternatives", "openalex", "--limit", "2"])
        self.assertEqual(status, 0)
        self.assertTrue(all("compatibility_note" in item for item in json.loads(stdout.getvalue())))

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            status = main(["export", "openalex", "crossref", "--format", "json"])
        self.assertEqual(status, 0)
        self.assertEqual([item["id"] for item in json.loads(stdout.getvalue())], ["openalex", "crossref"])

    def test_discovery_import_cli_writes_only_review_candidates(self) -> None:
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Queue-only API", "version": "1"},
            "servers": [{"url": "https://api.queue.example.com"}],
            "paths": {"/items": {"get": {"summary": "List items"}}},
        }
        with tempfile.TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "spec.json"
            output_path = Path(tmp) / "review.json"
            source_path.write_text(json.dumps(spec), encoding="utf-8")
            status = main(
                [
                    "discover-import",
                    "--format",
                    "openapi",
                    "--input",
                    str(source_path),
                    "--source-url",
                    "https://api.queue.example.com/openapi.json",
                    "--checked-on",
                    "2026-11-12",
                    "--output",
                    str(output_path),
                ]
            )
            self.assertEqual(status, 0)
            queue = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(queue["candidates"][0]["free_status"], "UNKNOWN")
            self.assertEqual(queue["candidates"][0]["review_status"], "needs_primary_source_review")

            atlas_input = Path(tmp) / "atlas.jsonl"
            atlas_output = Path(tmp) / "atlas-review.json"
            atlas_input.write_text(
                json.dumps(
                    {
                        "type": "API",
                        "name": "Directory Sample",
                        "category": "science",
                        "website": "https://directory.example.com",
                        "access": "Free",
                        "auth": "None",
                        "source": "editorial",
                        "verified": True,
                        "checked": "2026-11-01",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            missing_revision_stderr = io.StringIO()
            with contextlib.redirect_stderr(missing_revision_stderr):
                with self.assertRaises(SystemExit) as missing_revision:
                    main(
                        [
                            "discover-import",
                            "--format",
                            "api-atlas",
                            "--input",
                            str(atlas_input),
                            "--source-url",
                            "https://github.com/CTCycle/api-atlas/blob/547dae1fcc8356b11091200c76906787cc817ebc/data/catalog.jsonl",
                            "--checked-on",
                            "2026-11-12",
                            "--output",
                            str(atlas_output),
                        ]
                    )
            self.assertEqual(missing_revision.exception.code, 2)
            self.assertIn("--revision is required for API Atlas imports", missing_revision_stderr.getvalue())
            self.assertFalse(atlas_output.exists())

            status = main(
                [
                    "discover-import",
                    "--format",
                    "api-atlas",
                    "--input",
                    str(atlas_input),
                    "--source-url",
                    "https://github.com/CTCycle/api-atlas/blob/547dae1fcc8356b11091200c76906787cc817ebc/data/catalog.jsonl",
                    "--revision",
                    "547dae1fcc8356b11091200c76906787cc817ebc",
                    "--checked-on",
                    "2026-11-12",
                    "--output",
                    str(atlas_output),
                ]
            )
            self.assertEqual(status, 0)
            atlas_queue = json.loads(atlas_output.read_text(encoding="utf-8"))
            self.assertEqual(atlas_queue["candidates"][0]["review_priority"], "upstream_checked_pointer")
            self.assertEqual(APIMind().counts["apis"], 26)

    def test_catalog_load_rejects_broken_json_without_leaking_payload(self) -> None:
        # Invalid catalog data is reported as a typed, sanitized error.
        with self.assertRaises(CatalogError):
            APIMind(catalog_dir=ROOT / "tests" / "fixtures" / "missing-catalogs")


if __name__ == "__main__":
    unittest.main()
