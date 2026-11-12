"""Public catalog manager and discovery/search interface."""

from __future__ import annotations

import copy
import csv
import io
import json
import re
from collections import Counter
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from .api_client import APIClient
from .connectors import (
    APIConnector,
    ArxivConnector,
    CrossrefConnector,
    FrankfurterConnector,
    NominatimConnector,
    OpenAlexConnector,
    OSVConnector,
    USGSConnector,
    WorldBankConnector,
)
from .exceptions import CatalogError, UnknownRecordError, UnsafeRequestError
from .transport import HTTPResult, SafeHTTPTransport
from .validation import STATUS_VALUES, validate_catalog_data

_CATALOG_FILES = ("apis", "models", "datasets")
_CONNECTOR_TYPES = {
    "arxiv": ArxivConnector,
    "crossref": CrossrefConnector,
    "frankfurter": FrankfurterConnector,
    "nominatim": NominatimConnector,
    "openalex": OpenAlexConnector,
    "osv": OSVConnector,
    "usgs-earthquakes": USGSConnector,
    "world-bank-indicators": WorldBankConnector,
}
_SPECIAL_POLICY_CONNECTORS = frozenset({"arxiv", "nominatim"})
_AUTHENTICATION_FILTERS = frozenset({"none", "no-auth", "required", "optional", "unknown"})


def _authentication_state(record: Mapping[str, Any]) -> str:
    auth = record.get("authentication")
    if not isinstance(auth, dict):
        return "unknown"
    kind = auth.get("kind")
    if kind == "unknown" or auth.get("verified") is False:
        return "unknown"
    if kind == "none" and auth.get("required", False) is False:
        return "none"
    if auth.get("required") is True:
        return "required"
    if kind in {"bearer", "optional_bearer", "api_key_header", "optional_api_key_header", "api_key_query", "http_basic_pair"}:
        return "optional"
    return "unknown"


def _read_catalog(name: str, directory: str | Path | None) -> dict[str, Any]:
    try:
        if directory is None:
            text = files("divyesh_api_mind").joinpath(f"data/{name}.json").read_text(encoding="utf-8")
        else:
            text = (Path(directory) / f"{name}.json").read_text(encoding="utf-8")
        data = json.loads(text)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CatalogError(f"Could not load {name} catalog ({type(exc).__name__})") from None
    if not isinstance(data, dict):
        raise CatalogError(f"Invalid {name} catalog: expected a JSON object")
    return data


class APIMind:
    """Search local catalogs, inspect sources, and explicitly call APIs.

    Construction, local search, documentation lookup, and health-result
    formatting perform no network requests. Network access occurs only when a
    request or an explicitly called safe health probe runs. Catalog records
    marked for special public-service policies must use their dedicated
    connector wrappers.
    """

    def __init__(
        self,
        *,
        catalog_dir: str | Path | None = None,
        transport: SafeHTTPTransport | None = None,
        env: Mapping[str, str] | None = None,
        user_agent: str | None = None,
    ) -> None:
        self._catalogs: dict[str, dict[str, dict[str, Any]]] = {}
        self._records: dict[str, dict[str, Any]] = {}
        for kind in _CATALOG_FILES:
            document = _read_catalog(kind, catalog_dir)
            errors = validate_catalog_data(document, kind)
            if errors:
                raise CatalogError(f"Invalid {kind} catalog: {errors[0]}")
            records = {record["id"]: record for record in document["records"]}
            self._catalogs[kind] = records
            for record_id, record in records.items():
                if record_id in self._records:
                    raise CatalogError(f"Catalog id is not globally unique: {record_id}")
                self._records[record_id] = record

        api_records = self._catalogs["apis"]
        api_ids = set(api_records)
        for record in self._catalogs["datasets"].values():
            unlinked = set(record.get("api_ids", [])) - api_ids
            if unlinked:
                raise CatalogError(f"Dataset {record['id']} references unknown API ids: {sorted(unlinked)}")

        self._client = APIClient(
            api_records,
            transport=transport,
            env=env,
            user_agent=user_agent,
        )

    @property
    def counts(self) -> dict[str, int]:
        """Number of records in each local API/model/dataset catalog."""
        return {kind: len(records) for kind, records in self._catalogs.items()}

    def search(
        self,
        *,
        category: str | None = None,
        capability: str | None = None,
        free_access: str | None = None,
        kind: str | None = None,
        query: str | None = None,
        authentication: str | None = None,
        no_auth: bool = False,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Find API, model, and dataset records using local metadata.

        ``free_access`` accepts one of the documented status values such as
        ``FREE_NO_KEY`` or ``FREE_TIER_LIMITED``. ``authentication`` accepts
        ``none``/``no-auth``, ``required``, ``optional``, or ``unknown``;
        ``no_auth=True`` is a convenience filter for APIs whose catalogued
        auth is explicitly ``none``. Unknown or unverified auth is never
        returned as no-auth. ``kind`` may be singular or plural (``api``,
        ``apis``, ``model``, ``models``, ``dataset``, or ``datasets``).
        Category matching is exact and case-insensitive; capability matching
        is a case-insensitive substring search.
        """
        if free_access is not None and free_access not in STATUS_VALUES:
            raise ValueError(f"free_access must be one of: {', '.join(sorted(STATUS_VALUES))}")
        if not isinstance(no_auth, bool):
            raise ValueError("no_auth must be a boolean")
        if authentication is not None:
            authentication = authentication.casefold()
            if authentication not in _AUTHENTICATION_FILTERS:
                raise ValueError(f"authentication must be one of: {', '.join(sorted(_AUTHENTICATION_FILTERS))}")
            if authentication == "no-auth":
                authentication = "none"
        if no_auth and authentication not in {None, "none"}:
            raise ValueError("no_auth=True conflicts with a non-none authentication filter")
        if no_auth:
            authentication = "none"
        if kind is not None:
            kind_value = kind.casefold()
            if kind_value.endswith("s"):
                kind_value = kind_value[:-1]
            if kind_value not in {"api", "model", "dataset"}:
                raise ValueError("kind must be api, model, or dataset")
            kind = kind_value
        if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit < 0):
            raise ValueError("limit must be a non-negative integer or None")

        category_term = category.casefold() if category else None
        capability_term = capability.casefold() if capability else None
        query_term = query.casefold() if query else None
        matches: list[dict[str, Any]] = []
        for record in self._records.values():
            record_kind = str(record.get("type", "")).lower()
            if kind and record_kind != kind:
                continue
            if no_auth and record_kind != "api":
                continue
            if authentication is not None and _authentication_state(record) != authentication:
                continue
            if category_term and category_term not in {str(item).casefold() for item in record.get("categories", [])}:
                continue
            if free_access and record.get("free_status") != free_access:
                continue
            if capability_term and not any(
                capability_term in str(item).casefold() for item in record.get("capabilities", [])
            ):
                continue
            if query_term and query_term not in json.dumps(record, ensure_ascii=False).casefold():
                continue
            matches.append(copy.deepcopy(record))
        matches.sort(key=lambda item: (item.get("type", ""), item["id"]))
        return matches if limit is None else matches[:limit]

    def get(self, record_id: str) -> dict[str, Any]:
        """Return a defensive copy of one API, model, or dataset record."""
        try:
            return copy.deepcopy(self._records[record_id])
        except KeyError:
            raise UnknownRecordError(f"Unknown catalog record: {record_id}") from None

    def get_docs(self, record_id: str) -> list[dict[str, Any]]:
        """Return catalogued documentation references; does not fetch them."""
        record = self.get(record_id)
        sources = copy.deepcopy(record.get("sources", []))
        seen = {source.get("url") for source in sources if isinstance(source, dict)}
        for endpoint in record.get("endpoints", []):
            if not isinstance(endpoint, dict):
                continue
            url = endpoint.get("docs_url")
            if not isinstance(url, str) or not url or url in seen:
                continue
            sources.append(
                {
                    "url": url,
                    "title": f"Endpoint documentation: {endpoint.get('purpose', endpoint.get('path', 'API endpoint'))}",
                    "checked_on": record.get("last_verified"),
                    "evidence_level": "catalogued_endpoint_reference",
                }
            )
            seen.add(url)
        return sources

    def fetch_docs(
        self,
        record_id: str,
        *,
        source_index: int = 0,
        max_bytes: int = 512 * 1024,
    ) -> dict[str, Any]:
        """Explicitly fetch one catalogued HTTPS documentation reference.

        This operation sends an unauthenticated GET to the selected source's
        hostname, refuses redirects, applies a response-size limit, and never
        forwards API credentials. It does not follow arbitrary URLs supplied
        by a caller; ``source_index`` must refer to ``get_docs(record_id)``.
        """
        if isinstance(source_index, bool) or not isinstance(source_index, int) or source_index < 0:
            raise ValueError("source_index must be a non-negative integer")
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or not 1 <= max_bytes <= 1024 * 1024:
            raise ValueError("max_bytes must be between 1 byte and 1 MiB")
        sources = self.get_docs(record_id)
        if source_index >= len(sources):
            raise ValueError(f"source_index must be between 0 and {max(0, len(sources) - 1)}")
        source = sources[source_index]
        url = source.get("url")
        try:
            parsed = urlsplit(url)
            host = parsed.hostname or ""
            if (
                parsed.scheme.lower() != "https"
                or not host
                or parsed.username is not None
                or parsed.password is not None
                or parsed.port not in (None, 443)
                or parsed.query
            ):
                raise UnsafeRequestError("Documentation URL must be credential-free HTTPS without a query")
        except (TypeError, ValueError):
            raise UnsafeRequestError("Documentation URL must be a credential-free HTTPS URL") from None
        request_url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
        checked_at = datetime.now(timezone.utc).isoformat()
        try:
            response = self._client._transport.request(
                f"docs:{record_id}",
                "GET",
                request_url,
                allowed_hosts={host},
                headers={"Accept": "text/html, application/json, text/plain, */*"},
                retries=0,
                max_response_bytes=max_bytes,
            )
        except APIError as exc:
            return {
                "record_id": record_id,
                "source": copy.deepcopy(source),
                "checked_at": checked_at,
                "http_status": exc.status_code,
                "content_type": None,
                "content": None,
                "error": str(exc),
            }
        content_type = response.headers.get("content-type", "")
        textual = not content_type or any(
            marker in content_type.casefold()
            for marker in ("text/", "json", "xml", "javascript", "yaml", "x-www-form-urlencoded")
        )
        content = response.body.decode("utf-8", errors="replace") if textual else None
        return {
            "record_id": record_id,
            "source": copy.deepcopy(source),
            "checked_at": checked_at,
            "http_status": response.status_code,
            "content_type": content_type,
            "content": content,
            "error": None if 200 <= response.status_code < 300 else f"HTTP status {response.status_code}",
        }

    def integration_template(self, record_id: str, *, language: str = "python") -> str:
        """Generate a non-executing Python starter for one API record."""
        if language.casefold() != "python":
            raise ValueError("only Python integration templates are currently supported")
        record = self.get(record_id)
        if record.get("type") != "api":
            raise ValueError("integration templates are available only for API records")
        auth = record.get("authentication", {})
        if not isinstance(auth, dict) or auth.get("kind") == "unknown" or auth.get("verified") is False:
            raise ValueError("authentication is unverified; review the provider docs before generating a callable template")
        auth_lines: list[str] = []
        env_var = auth.get("env_var")
        if isinstance(env_var, str):
            auth_lines.append(f"# Configure {env_var} in your environment; never hard-code its value.")
        if isinstance(auth.get("username_env"), str) and isinstance(auth.get("password_env"), str):
            auth_lines.append(
                f"# Configure {auth['username_env']} and {auth['password_env']} in your environment."
            )
        if record_id == "arxiv":
            body = [
                "mind = APIMind()",
                'client = mind.connector("arxiv")',
                "",
                "def request_example():",
                '    # The connector enforces the provider\'s serialized request cadence.',
                '    return client.search("replace with a query", max_results=5)',
            ]
        elif record_id == "nominatim":
            body = [
                'mind = APIMind(user_agent="YourApp/1.0 (contact: you@example.org)")',
                'client = mind.connector("nominatim", acknowledge_policy=True)',
                "",
                "def request_example():",
                '    # Follow the public-server policy, cache results, and do not use autocomplete.',
                '    return client.search("replace with a specific place", limit=1)',
            ]
        else:
            endpoint = next(
                (item for item in record.get("endpoints", []) if isinstance(item, dict) and item.get("method") in {"GET", "POST"}),
                {},
            )
            method = endpoint.get("method", "GET")
            path = endpoint.get("path", "")
            if not isinstance(path, str):
                path = ""
            body = [
                "mind = APIMind()",
                f"client = mind.connector({record_id!r})",
                "",
                "def request_example():",
            ]
            if "{" in path or "}" in path:
                body.append(f"    # Replace path placeholders in {path!r} before calling.")
            if method == "GET":
                body.append(f"    return client.get_json({path!r}, params={{}})")
            elif method == "POST":
                body.append(f"    # Review provider terms and the request schema before any POST.")
                body.append(f"    return client.post_json({path!r}, payload={{}})")
            else:
                body.append("    raise NotImplementedError(\"No supported GET/POST example is documented\")")
        prefix = ["from divyesh_api_mind import APIMind", ""]
        if auth_lines:
            prefix.extend(auth_lines)
            prefix.append("")
        return "\n".join(prefix + body) + "\n"

    def alternatives(self, record_id: str, *, limit: int = 5) -> list[dict[str, Any]]:
        """Suggest related catalog APIs when a selected API is unavailable.

        Results are capability/category neighbors, not guaranteed compatible
        drop-in replacements. No network health checks are run by this method.
        """
        target = self.get(record_id)
        if target.get("type") != "api":
            raise ValueError("alternatives can be calculated only for API records")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
            raise ValueError("limit must be a non-negative integer")
        target_categories = {str(value).casefold() for value in target.get("categories", [])}
        target_capabilities = {str(value).casefold() for value in target.get("capabilities", [])}
        target_tokens = {token for value in target_capabilities for token in re.findall(r"[a-z0-9]+", value)}
        ranked: list[dict[str, Any]] = []
        for candidate in self._catalogs["apis"].values():
            if candidate["id"] == record_id:
                continue
            categories = {str(value).casefold() for value in candidate.get("categories", [])}
            capabilities = {str(value).casefold() for value in candidate.get("capabilities", [])}
            shared_categories = sorted(target_categories & categories)
            shared_capabilities = sorted(target_capabilities & capabilities)
            candidate_tokens = {token for value in capabilities for token in re.findall(r"[a-z0-9]+", value)}
            token_union = target_tokens | candidate_tokens
            token_similarity = len(target_tokens & candidate_tokens) / len(token_union) if token_union else 0.0
            exact_similarity = len(target_capabilities & capabilities) / max(1, len(target_capabilities | capabilities))
            category_similarity = len(shared_categories) / max(1, len(target_categories | categories))
            score = 0.65 * exact_similarity + 0.25 * token_similarity + 0.10 * category_similarity
            if score <= 0 and not shared_categories:
                continue
            item = copy.deepcopy(candidate)
            item["alternative_score"] = round(score, 4)
            item["shared_capabilities"] = shared_capabilities
            item["shared_categories"] = shared_categories
            item["compatibility_note"] = "Related discovery candidate only; check endpoint, auth, terms, and data compatibility."
            ranked.append(item)
        ranked.sort(key=lambda item: (-float(item["alternative_score"]), -len(item["shared_capabilities"]), item["id"]))
        return ranked[:limit]

    def export_records(self, record_ids: Iterable[str], *, format: str = "json") -> str:
        """Export only explicitly selected API/model/dataset records."""
        if format not in {"json", "csv"}:
            raise ValueError("format must be json or csv")
        if isinstance(record_ids, (str, bytes)):
            raise ValueError("record_ids must be a sequence of ids, not one string")
        ids = list(record_ids)
        if not ids:
            raise ValueError("select at least one record id to export")
        if any(not isinstance(record_id, str) or not record_id for record_id in ids):
            raise ValueError("every selected record id must be non-empty text")
        if len(set(ids)) != len(ids):
            raise ValueError("record_ids must not contain duplicates")
        records = [self.get(record_id) for record_id in ids]
        if format == "json":
            return json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        output = io.StringIO(newline="")
        fields = ["id", "type", "name", "categories", "free_status", "authentication", "base_url", "summary", "documentation_urls", "source_urls"]
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for record in records:
            auth = record.get("authentication", {})
            writer.writerow(
                {
                    "id": record.get("id", ""),
                    "type": record.get("type", ""),
                    "name": record.get("name", ""),
                    "categories": json.dumps(record.get("categories", []), ensure_ascii=False),
                    "free_status": record.get("free_status", ""),
                    "authentication": json.dumps(auth, ensure_ascii=False, sort_keys=True),
                    "base_url": record.get("base_url", ""),
                    "summary": record.get("summary", ""),
                    "documentation_urls": json.dumps([item["url"] for item in self.get_docs(record["id"])], ensure_ascii=False),
                    "source_urls": json.dumps([item.get("url") for item in record.get("sources", [])], ensure_ascii=False),
                }
            )
        return output.getvalue()

    def connector(self, record_id: str, **options: Any) -> APIConnector:
        """Create a callable connector; no request is sent until a method runs."""
        if record_id not in self._catalogs["apis"]:
            raise UnknownRecordError(f"Unknown API record: {record_id}")
        connector_class = _CONNECTOR_TYPES.get(record_id, APIConnector)
        return connector_class(self._client, record_id, **options)

    def _assert_generic_request_allowed(self, record_id: str) -> None:
        if record_id in _SPECIAL_POLICY_CONNECTORS:
            raise UnsafeRequestError(
                f"Use APIMind.connector({record_id!r}) to preserve this provider's format and request-cadence policy"
            )

    def request(
        self,
        record_id: str,
        path: str = "",
        *,
        method: str = "GET",
        params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        form_body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        """Make an explicit HTTPS JSON request through a cataloged API."""
        self._assert_generic_request_allowed(record_id)
        return self._client.request_json(
            record_id,
            path,
            method=method,
            params=params,
            json_body=json_body,
            form_body=form_body,
            headers=headers,
        )

    def request_text(
        self,
        record_id: str,
        path: str = "",
        *,
        method: str = "GET",
        params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        form_body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        encoding: str = "utf-8",
    ) -> str:
        """Make an explicit request and decode a non-JSON response as text."""
        self._assert_generic_request_allowed(record_id)
        return self._client.request_text(
            record_id,
            path,
            method=method,
            params=params,
            json_body=json_body,
            form_body=form_body,
            headers=headers,
            encoding=encoding,
        )

    def request_raw(
        self,
        record_id: str,
        path: str = "",
        *,
        method: str = "GET",
        params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        form_body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> HTTPResult:
        """Make an explicit request and return the bounded response bytes."""
        self._assert_generic_request_allowed(record_id)
        return self._client.request_raw(
            record_id,
            path,
            method=method,
            params=params,
            json_body=json_body,
            form_body=form_body,
            headers=headers,
        )

    def health_check(self, record_id: str) -> dict[str, Any]:
        """Run a documented read-only health probe, if the record has one."""
        return self._client.health_check(record_id)

    def free_status_counts(self) -> dict[str, int]:
        """Count API/model/dataset records by their free-access status."""
        counts = Counter(record.get("free_status", "UNKNOWN") for record in self._records.values())
        return dict(sorted(counts.items()))
