"""Local catalog validation; this module performs no network requests."""

from __future__ import annotations

import ipaddress
import json
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

STATUS_VALUES = frozenset(
    {
        "FREE_NO_KEY",
        "FREE_WITH_KEY",
        "FREE_TIER_LIMITED",
        "OPEN_SOURCE_SELF_HOSTED",
        "FREE_DATA_PAID_SERVICE",
        "PAID",
        "UNKNOWN",
    }
)
MCP_STATES = frozenset({"directory_entry", "reviewed_repository", "working_integration"})
CATEGORIES = frozenset(
    {
        "ai",
        "research",
        "development",
        "math",
        "data",
        "government",
        "finance",
        "communication",
        "media",
        "location",
        "security",
        "automation",
        "weather",
        "translation",
        "package-index",
        "science",
        "education",
        "open-data",
        "space",
    }
)
_AUTH_KINDS = frozenset(
    {
        "none",
        "bearer",
        "optional_bearer",
        "api_key_header",
        "optional_api_key_header",
        "api_key_query",
        "http_basic_pair",
        "unknown",
    }
)
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_HTTP_TOKEN = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
_SECRET_PATTERNS = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~-]{20,}", re.IGNORECASE),
    re.compile(r"[?&](?:api[_-]?key|apikey|key|token)=([A-Za-z0-9_-]{20,})", re.IGNORECASE),
)


def _is_date(value: Any) -> bool:
    if not isinstance(value, str) or not _DATE.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _https_url(value: Any, *, catalog_base: bool = False) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    if (
        parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
    ):
        return False
    if catalog_base and (parsed.query or parsed.fragment):
        return False
    return True


def _host(value: str) -> str:
    try:
        return value.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError:
        return ""


def _safe_public_host(value: str) -> bool:
    host = _host(value)
    if not host or host in {"localhost", "localhost.localdomain"} or host.endswith(
        (".local", ".localhost", ".internal", ".test", ".invalid")
    ):
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return "." in host
    return address.is_global


def _contains_possible_secret(value: Any) -> bool:
    if isinstance(value, str):
        return any(pattern.search(value) for pattern in _SECRET_PATTERNS)
    if isinstance(value, dict):
        return any(_contains_possible_secret(key) or _contains_possible_secret(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_possible_secret(item) for item in value)
    return False


def _check_source(record_id: str, source: Any, index: int, errors: list[str]) -> None:
    if not isinstance(source, dict):
        errors.append(f"{record_id}: source[{index}] must be an object")
        return
    if not _https_url(source.get("url")):
        errors.append(f"{record_id}: source[{index}] URL must be a credential-free HTTPS URL")
    if not isinstance(source.get("title"), str) or not source["title"].strip():
        errors.append(f"{record_id}: source[{index}] needs a non-empty title")
    if not _is_date(source.get("checked_on")):
        errors.append(f"{record_id}: source[{index}] checked_on must be ISO YYYY-MM-DD")


def _check_authentication(record_id: str, auth: Any, errors: list[str]) -> None:
    if not isinstance(auth, dict):
        errors.append(f"{record_id}: authentication must be an object")
        return
    kind = auth.get("kind", "none")
    if not isinstance(kind, str) or kind not in _AUTH_KINDS:
        errors.append(f"{record_id}: unsupported authentication kind")
        return
    required = auth.get("required", False)
    if not isinstance(required, bool):
        errors.append(f"{record_id}: authentication.required must be boolean")
    verified = auth.get("verified")
    if verified is not None and not isinstance(verified, bool):
        errors.append(f"{record_id}: authentication.verified must be boolean when present")
    if kind == "unknown":
        if required:
            errors.append(f"{record_id}: unknown authentication cannot be marked required")
        return
    if kind == "none":
        if required:
            errors.append(f"{record_id}: authentication.kind=none cannot be required")
        return
    if kind == "http_basic_pair":
        names = (auth.get("username_env"), auth.get("password_env"))
        if any(not isinstance(name, str) or not _ENV_NAME.fullmatch(name) for name in names):
            errors.append(f"{record_id}: basic authentication requires valid username_env and password_env names")
        return
    env_var = auth.get("env_var")
    if not isinstance(env_var, str) or not _ENV_NAME.fullmatch(env_var):
        errors.append(f"{record_id}: authentication requires a valid env_var name")
    if kind in {"api_key_header", "optional_api_key_header"}:
        header = auth.get("header", "X-API-Key")
        if not isinstance(header, str) or not _HTTP_TOKEN.fullmatch(header):
            errors.append(f"{record_id}: authentication header is invalid")
    if kind == "api_key_query":
        parameter = auth.get("parameter", "api_key")
        if not isinstance(parameter, str) or not parameter or any(ord(char) < 33 for char in parameter):
            errors.append(f"{record_id}: authentication query parameter is invalid")


def _check_endpoint(record_id: str, endpoint: Any, index: int, errors: list[str]) -> None:
    if not isinstance(endpoint, dict):
        errors.append(f"{record_id}: endpoint[{index}] must be an object")
        return
    method = endpoint.get("method")
    if not isinstance(method, str) or method not in {"GET", "HEAD", "POST"}:
        errors.append(f"{record_id}: endpoint[{index}] method must be GET, HEAD, or POST")
    path = endpoint.get("path")
    if not isinstance(path, str):
        errors.append(f"{record_id}: endpoint[{index}] path must be text")
    else:
        decoded_path = unquote(path)
        if (
            any(ord(char) < 32 or ord(char) == 127 for char in path)
            or any(ord(char) < 32 or ord(char) == 127 for char in decoded_path)
            or "\\" in decoded_path
            or "://" in path
            or decoded_path.startswith("//")
            or any(segment == ".." for segment in decoded_path.split("/"))
            or "?" in path
        ):
            errors.append(f"{record_id}: endpoint[{index}] path must be a safe relative API path")
    docs_url = endpoint.get("docs_url")
    if docs_url is not None and not _https_url(docs_url):
        errors.append(f"{record_id}: endpoint[{index}] docs_url must use HTTPS")


def validate_catalog_data(data: dict[str, Any], kind: str) -> list[str]:
    """Return human-readable validation errors for one catalog JSON document."""
    errors: list[str] = []
    if kind not in {"apis", "models", "datasets", "mcp_registry"}:
        return [f"Unknown catalog kind: {kind}"]
    if not isinstance(data, dict) or not isinstance(data.get("records"), list):
        return [f"{kind}: expected an object with a records array"]
    if not isinstance(data.get("schema_version"), str) or not data["schema_version"].strip():
        errors.append(f"{kind}: missing schema_version")
    if not _is_date(data.get("last_updated")):
        errors.append(f"{kind}: last_updated must be ISO YYYY-MM-DD")

    ids: set[str] = set()
    for index, record in enumerate(data["records"]):
        label = f"{kind}.records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label}: expected an object")
            continue
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id.strip():
            errors.append(f"{label}: missing non-empty id")
            record_id = f"<index {index}>"
        elif record_id in ids:
            errors.append(f"{label}: duplicate id {record_id}")
        ids.add(record_id)

        for field in ("name",):
            if not isinstance(record.get(field), str) or not record[field].strip():
                errors.append(f"{record_id}: {field} must be a non-empty string")

        if kind == "mcp_registry":
            status = record.get("status")
            if not isinstance(status, str) or status not in MCP_STATES:
                errors.append(f"{record_id}: invalid MCP status; expected {sorted(MCP_STATES)}")
            if record.get("status") == "working_integration" and not _is_date(record.get("tested_on")):
                errors.append(f"{record_id}: working_integration requires ISO tested_on evidence")
        else:
            expected_type = {"apis": "api", "models": "model", "datasets": "dataset"}[kind]
            if record.get("type") != expected_type:
                errors.append(f"{record_id}: type must be {expected_type!r}")
            free_status = record.get("free_status")
            if not isinstance(free_status, str) or free_status not in STATUS_VALUES:
                errors.append(f"{record_id}: invalid or missing free_status")
            categories = record.get("categories")
            if not isinstance(categories, list) or not categories:
                errors.append(f"{record_id}: categories must be a non-empty list")
            elif any(not isinstance(item, str) for item in categories):
                errors.append(f"{record_id}: every category must be text")
            else:
                unknown = set(categories) - CATEGORIES
                if unknown:
                    errors.append(f"{record_id}: unknown categories {sorted(unknown)}")
            if not isinstance(record.get("summary"), str) or not record["summary"].strip():
                errors.append(f"{record_id}: summary must be a non-empty string")

        sources = record.get("sources")
        if not isinstance(sources, list) or not sources:
            errors.append(f"{record_id}: at least one source reference is required")
        else:
            for source_index, source in enumerate(sources):
                _check_source(record_id, source, source_index, errors)

        checked_date = record.get("last_verified") or record.get("verified_on")
        if not _is_date(checked_date):
            errors.append(f"{record_id}: last_verified/verified_on must be ISO YYYY-MM-DD")

        if kind == "apis":
            base_url = record.get("base_url")
            if not _https_url(base_url, catalog_base=True):
                errors.append(f"{record_id}: API base_url must be credential-free HTTPS without a query or fragment")
            else:
                raw_base_host = urlsplit(base_url).hostname or ""
                base_host = _host(raw_base_host)
                if not _safe_public_host(raw_base_host):
                    errors.append(f"{record_id}: API base_url must use a public hostname")
                allowed_hosts = record.get("allowed_hosts")
                if allowed_hosts is not None:
                    if not isinstance(allowed_hosts, list) or not allowed_hosts or any(
                        not isinstance(host, str) or not host for host in allowed_hosts
                    ):
                        errors.append(f"{record_id}: allowed_hosts must be a non-empty list of hostnames")
                    elif base_host not in {_host(host) for host in allowed_hosts}:
                        errors.append(f"{record_id}: allowed_hosts must include the base_url hostname")
            endpoints = record.get("endpoints")
            if not isinstance(endpoints, list) or not endpoints:
                errors.append(f"{record_id}: at least one endpoint description is required")
            else:
                for endpoint_index, endpoint in enumerate(endpoints):
                    _check_endpoint(record_id, endpoint, endpoint_index, errors)
            _check_authentication(record_id, record.get("authentication", {}), errors)
            probe = record.get("health_probe")
            if probe is not None:
                if not isinstance(probe, dict):
                    errors.append(f"{record_id}: health_probe must be an object or null")
                else:
                    probe_method = probe.get("method", "GET")
                    if not isinstance(probe_method, str) or probe_method not in {"GET", "HEAD"}:
                        errors.append(f"{record_id}: health_probe must use GET or HEAD")
                    path = probe.get("path", "")
                    if not isinstance(path, str):
                        errors.append(f"{record_id}: health_probe path must be safe relative text")
                    else:
                        decoded_path = unquote(path)
                        if (
                            any(ord(char) < 32 or ord(char) == 127 for char in decoded_path)
                            or "\\" in decoded_path
                            or "://" in path
                            or decoded_path.startswith("//")
                            or any(segment == ".." for segment in decoded_path.split("/"))
                            or "?" in path
                        ):
                            errors.append(f"{record_id}: health_probe path must be safe relative text")
                    if not isinstance(probe.get("params", {}), dict):
                        errors.append(f"{record_id}: health_probe params must be an object")
        elif kind == "models":
            if not _https_url(record.get("model_url")):
                errors.append(f"{record_id}: model_url must be a credential-free HTTPS URL")
        elif kind == "datasets":
            if not isinstance(record.get("access"), str) or not record["access"].strip():
                errors.append(f"{record_id}: access description is required")
            api_ids = record.get("api_ids", [])
            if not isinstance(api_ids, list) or any(not isinstance(api_id, str) for api_id in api_ids):
                errors.append(f"{record_id}: api_ids must be a list of API record ids")
        elif kind == "mcp_registry":
            for field in ("description", "verification_scope"):
                if not isinstance(record.get(field), str) or not record[field].strip():
                    errors.append(f"{record_id}: {field} must be a non-empty string")

        confidence = record.get("evidence_confidence")
        if confidence is not None and (
            not isinstance(confidence, str) or confidence not in {"high", "medium", "low"}
        ):
            errors.append(f"{record_id}: evidence_confidence must be high, medium, or low")

    if _contains_possible_secret(data):
        errors.append(f"{kind}: possible credential embedded in catalog data")
    return errors


def validate_catalog_directory(directory: str | Path) -> dict[str, list[str]]:
    """Load and validate the four checked-in JSON catalogs from a directory."""
    root = Path(directory)
    results: dict[str, list[str]] = {}
    for kind in ("apis", "models", "datasets", "mcp_registry"):
        path = root / f"{kind}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            results[kind] = [f"Could not read {path.name} ({type(exc).__name__})"]
            continue
        results[kind] = validate_catalog_data(data, kind)
    return results
