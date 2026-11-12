"""Conservative, provenance-preserving import of API directory leads.

Directory and OpenAPI imports produce review candidates, never trusted API
records. Imported free-access status is always UNKNOWN until a human verifies
provider terms, authentication, quotas, and licensing from primary sources.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import html
import ipaddress
import json
import re
import unicodedata
from collections import defaultdict
from datetime import date, datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .exceptions import APIError, CatalogError, UnsafeRequestError
from .transport import SafeHTTPTransport
from .validation import _contains_possible_secret

_DISCOVERY_SCHEMA_VERSION = "1.0"
_PUBLIC_APIS_REPOSITORY = "https://github.com/public-apis/public-apis"
_PUBLIC_APIS_LICENSE = "MIT"
_TRACKING_PREFIXES = ("utm_",)
_SECRET_QUERY_KEYS = frozenset({"key", "api_key", "apikey", "token", "access_token", "secret", "password", "auth"})
_HTTP_METHODS = frozenset({"get", "head", "post", "put", "patch", "delete", "options", "trace"})


def _canonical_date(value: str | date | None) -> str:
    if value is None:
        return date.today().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError("checked_on must be a valid YYYY-MM-DD date") from None
    if parsed.isoformat() != value:
        raise ValueError("checked_on must use canonical YYYY-MM-DD form")
    return value


def _safe_http_url(value: Any, *, require_https: bool = False) -> str:
    if not isinstance(value, str) or not value or any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError("source URLs must be non-empty text without control characters")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise ValueError("source URL is malformed") from None
    allowed_schemes = {"https"} if require_https else {"http", "https"}
    if (
        parsed.scheme.lower() not in allowed_schemes
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or port not in ({None, 443} if require_https else {None, 80, 443})
    ):
        raise ValueError("source URL must be a credential-free public HTTP(S) URL")
    try:
        host = parsed.hostname.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError:
        raise ValueError("source URL contains an invalid hostname") from None
    if (
        host in {"localhost", "localhost.localdomain"}
        or host.endswith((".local", ".localhost", ".internal", ".test", ".invalid"))
    ):
        raise ValueError("source URL must use a public hostname")
    try:
        address = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        if "." not in host:
            raise ValueError("source URL must use a public hostname") from None
    else:
        if not address.is_global:
            raise ValueError("source URL must not use a private or non-global IP address")
    if parsed.query:
        for key, _ in parse_qsl(parsed.query, keep_blank_values=True):
            if key.casefold() in _SECRET_QUERY_KEYS:
                raise ValueError("source URL appears to contain a credential query parameter")
    return value


def _canonical_url(value: str) -> str:
    parsed = urlsplit(value)
    host = (parsed.hostname or "").rstrip(".").encode("idna").decode("ascii").lower()
    port = parsed.port
    netloc = f"[{host}]" if ":" in host else host
    if port is not None and not (parsed.scheme.lower() == "https" and port == 443) and not (
        parsed.scheme.lower() == "http" and port == 80
    ):
        netloc = f"{netloc}:{port}"
    path = re.sub(r"/{2,}", "/", parsed.path or "/").rstrip("/") or "/"
    query = urlencode(
        sorted(
            (key, val)
            for key, val in parse_qsl(parsed.query, keep_blank_values=True)
            if not key.casefold().startswith(_TRACKING_PREFIXES)
        )
    )
    return urlunsplit((parsed.scheme.lower(), netloc, path, query, ""))


def _slug(value: str, limit: int = 48) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return (slug or "api")[:limit].strip("-") or "api"


def _name_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower())


def _meaningful_name_tokens(value: str) -> set[str]:
    generic = {
        "api", "apis", "rest", "public", "official", "service", "the", "v1", "v2", "v3",
        "data", "rate", "rates", "weather", "search", "metadata", "registry", "open",
        "reference", "developer", "developers",
    }
    return {token for token in re.findall(r"[a-z0-9]+", value.casefold()) if token not in generic}


def _candidate_id(name: str, url: str, category: str = "") -> str:
    identity = "\0".join((name.casefold().strip(), _canonical_url(url), category.casefold().strip()))
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:10]
    return f"candidate-{_slug(name, 40)}-{digest}"


def _clean_markdown_cell(value: str, limit: int = 2000) -> str:
    text = html.unescape(value).strip()
    if text.startswith("`") and text.endswith("`") and len(text) >= 2:
        text = text[1:-1].strip()
    return text[:limit]


def _parse_markdown_link(cell: str) -> tuple[str, str] | None:
    match = re.match(r"^\[([^\]]+)\]\((https?://[^)]+)\)$", cell.strip())
    if not match:
        return None
    name, target = match.groups()
    try:
        target = _safe_http_url(target.strip(), require_https=False)
    except ValueError:
        return None
    return _clean_markdown_cell(name, 300), target


def _candidate_catalog_matches(candidate: Mapping[str, Any], existing_records: Iterable[Mapping[str, Any]]) -> list[str]:
    candidate_name = str(candidate.get("name", ""))
    candidate_key = _name_key(candidate_name)
    candidate_tokens = _meaningful_name_tokens(candidate_name)
    candidate_url = str(candidate.get("base_url") or candidate.get("listed_url") or "")
    candidate_host = (urlsplit(candidate_url).hostname or "").lower()
    candidate_host = candidate_host.removeprefix("www.").removeprefix("api.")
    matches: list[str] = []
    for record in existing_records:
        record_id = record.get("id")
        if not isinstance(record_id, str):
            continue
        record_name = str(record.get("name", ""))
        record_key = _name_key(record_name)
        record_tokens = _meaningful_name_tokens(record_name)
        name_score = SequenceMatcher(None, candidate_key, record_key).ratio() if candidate_key and record_key else 0
        token_related = bool(
            candidate_tokens
            and record_tokens
            and (
                candidate_tokens == record_tokens
                or (len(candidate_tokens) >= 2 and candidate_tokens <= record_tokens)
                or (len(record_tokens) >= 2 and record_tokens <= candidate_tokens)
                or (
                    len(candidate_tokens) == 1
                    and len(next(iter(candidate_tokens))) >= 4
                    and candidate_tokens <= record_tokens
                )
                or (
                    len(record_tokens) == 1
                    and len(next(iter(record_tokens))) >= 4
                    and record_tokens <= candidate_tokens
                )
            )
        )
        record_host = (urlsplit(str(record.get("base_url", ""))).hostname or "").lower()
        record_host = record_host.removeprefix("www.").removeprefix("api.")
        host_match = bool(candidate_host and record_host and (candidate_host == record_host or candidate_host.endswith("." + record_host) or record_host.endswith("." + candidate_host)))
        if name_score >= 0.9 or token_related or (host_match and name_score >= 0.9):
            matches.append(record_id)
    return sorted(set(matches))


def _decorate_duplicate_warnings(candidates: list[dict[str, Any]]) -> None:
    by_url: dict[str, list[int]] = defaultdict(list)
    by_name: dict[str, list[int]] = defaultdict(list)
    for index, item in enumerate(candidates):
        url = item.get("base_url") or item.get("listed_url") or item.get("source_url")
        by_url[_canonical_url(url)].append(index)
        by_name[_name_key(str(item.get("name", "")))].append(index)
    for indices in by_url.values():
        if len(indices) < 2:
            continue
        names = {str(candidates[index].get("name", "")).casefold() for index in indices}
        warning = "same_canonical_url_as_another_candidate" if len(names) > 1 else "same_name_and_canonical_url_merged"
        if len(names) > 1:
            for index in indices:
                candidates[index].setdefault("possible_duplicate_flags", []).append(warning)
    for indices in by_name.values():
        if len(indices) < 2:
            continue
        urls = {
            _canonical_url(str(candidates[index].get("base_url") or candidates[index].get("listed_url") or candidates[index].get("source_url")))
            for index in indices
        }
        if len(urls) > 1:
            for index in indices:
                candidates[index].setdefault("possible_duplicate_flags", []).append("same_normalized_name_different_url")


def _merge_exact_candidates(candidates: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    input_count = len(candidates)
    for candidate in candidates:
        target = str(candidate.get("base_url") or candidate.get("listed_url") or candidate.get("source_url"))
        key = (_name_key(str(candidate.get("name", ""))), _canonical_url(target))
        attributions = candidate.get("source_attributions")
        if not isinstance(attributions, list) or not attributions:
            attributions = [candidate.get("attribution", {})]
        claim_groups = candidate.get("source_claims_by_source")
        if not isinstance(claim_groups, list):
            claims = candidate.get("source_claims")
            claim_groups = (
                [{"source_attributions": copy.deepcopy(attributions), "claims": copy.deepcopy(claims)}]
                if isinstance(claims, dict)
                else []
            )
        if key not in merged:
            item = copy.deepcopy(candidate)
            item["source_attributions"] = [copy.deepcopy(attribution) for attribution in attributions if attribution]
            item["source_claims_by_source"] = copy.deepcopy(claim_groups)
            candidate_categories = list(candidate.get("categories", []))
            if candidate.get("category") and candidate["category"] not in candidate_categories:
                candidate_categories.append(candidate["category"])
            item["categories"] = candidate_categories
            merged[key] = item
            continue
        item = merged[key]
        for attribution in attributions:
            if attribution and attribution not in item["source_attributions"]:
                item["source_attributions"].append(copy.deepcopy(attribution))
        for claim_group in claim_groups:
            existing_groups = item.setdefault("source_claims_by_source", [])
            if claim_group not in existing_groups:
                existing_groups.append(copy.deepcopy(claim_group))
        priority_order = {"upstream_checked_pointer": 0, "unverified_directory_pointer": 1}
        candidate_priority = candidate.get("review_priority")
        current_priority = item.get("review_priority")
        if isinstance(candidate_priority, str) and candidate_priority in priority_order and (
            not isinstance(current_priority, str)
            or current_priority not in priority_order
            or priority_order[candidate_priority] < priority_order[current_priority]
        ):
            item["review_priority"] = candidate_priority
        for flag in candidate.get("possible_duplicate_flags", []):
            if flag not in item.setdefault("possible_duplicate_flags", []):
                item["possible_duplicate_flags"].append(flag)
        candidate_categories = list(candidate.get("categories", []))
        if candidate.get("category") and candidate["category"] not in candidate_categories:
            candidate_categories.append(candidate["category"])
        for category in candidate_categories:
            if category and category not in item["categories"]:
                item["categories"].append(category)
        sources = item.setdefault("evidence_sources", [])
        for source in candidate.get("evidence_sources", []):
            if source not in sources:
                sources.append(copy.deepcopy(source))
    return list(merged.values()), input_count - len(merged)


def _build_queue(source: dict[str, Any], candidates: list[dict[str, Any]], raw_count: int) -> dict[str, Any]:
    candidates, exact_duplicates_merged = _merge_exact_candidates(candidates)
    _decorate_duplicate_warnings(candidates)
    possible = sum(bool(candidate.get("possible_duplicate_flags")) for candidate in candidates)
    return {
        "schema_version": _DISCOVERY_SCHEMA_VERSION,
        "generated_on": source["checked_on"],
        "source": source,
        "policy": {
            "free_status": "UNKNOWN",
            "automatic_catalog_promotion": False,
            "note": "Directory/spec metadata is a discovery lead only. Verify official docs, authentication, quotas, rates, terms, and licensing before promotion.",
        },
        "counts": {
            "source_rows": raw_count,
            "unique_candidates": len(candidates),
            "exact_duplicate_rows_merged": exact_duplicates_merged,
            "possible_duplicate_candidates": possible,
            "categories": len({category for candidate in candidates for category in candidate.get("categories", [])}),
            "needs_review": len(candidates),
        },
        "candidates": candidates,
    }


def combine_review_queues(queues: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Combine imported queues while retaining every source attribution."""
    queue_list = list(queues)
    if not queue_list:
        raise ValueError("provide at least one review queue")
    candidates: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    checked_dates: list[date] = []
    raw_count = 0
    for queue in queue_list:
        if queue.get("schema_version") != _DISCOVERY_SCHEMA_VERSION or not isinstance(queue.get("candidates"), list):
            raise ValueError("all inputs must be valid discovery review queues")
        source = queue.get("source")
        if isinstance(source, dict):
            sources.append(copy.deepcopy(source))
            checked_value = source.get("checked_on")
            if isinstance(checked_value, str):
                checked_dates.append(date.fromisoformat(_canonical_date(checked_value)))
        candidates.extend(copy.deepcopy(queue["candidates"]))
        counts = queue.get("counts", {})
        raw_count += int(counts.get("source_rows", len(queue["candidates"]))) if isinstance(counts, dict) else len(queue["candidates"])
    checked = max(checked_dates).isoformat() if checked_dates else date.today().isoformat()
    source_summary = {"format": "combined-review-queues", "checked_on": checked, "sources": sources}
    return _build_queue(source_summary, candidates, raw_count)


def import_public_apis_markdown(
    markdown: str,
    *,
    source_url: str,
    revision: str,
    checked_on: str | date | None = None,
    existing_records: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Convert Public APIs Markdown rows into attributed UNKNOWN review leads.

    Auth/HTTPS/CORS values are preserved as raw directory claims only. In
    particular, the repository's "free" framing is not used to set a free
    status, API endpoint, license, or verified authentication scheme.
    """
    if not isinstance(markdown, str) or not markdown.strip():
        raise ValueError("markdown must be non-empty text")
    source_url = _safe_http_url(source_url, require_https=True)
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-fA-F]{7,64}", revision):
        raise ValueError("revision must be a Git commit hash")
    checked = _canonical_date(checked_on)
    lines = markdown.splitlines()
    in_index = False
    category: str | None = None
    raw_candidates: list[dict[str, Any]] = []
    rejected_rows = 0
    for line_number, line in enumerate(lines, start=1):
        if line.strip() == "## Index":
            in_index = True
            continue
        if in_index and line.startswith("## ") and not line.startswith("### "):
            break
        if not in_index:
            continue
        if line.startswith("### "):
            category = _clean_markdown_cell(line[4:], 200)
            continue
        if not category or not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 5 or cells[0].casefold() == "api" or not cells[0]:
            continue
        linked = _parse_markdown_link(cells[0])
        if linked is None:
            if not cells[0].startswith(":") and not set(cells[0]) <= set("-: "):
                rejected_rows += 1
            continue
        name, listed_url = linked
        description = _clean_markdown_cell(cells[1], 1500)
        auth_claim = _clean_markdown_cell(cells[2], 100)
        https_claim = _clean_markdown_cell(cells[3], 100)
        cors_claim = _clean_markdown_cell(cells[4], 100)
        candidate_id = _candidate_id(name, listed_url, category)
        attribution = {
            "repository": _PUBLIC_APIS_REPOSITORY,
            "revision": revision.lower(),
            "file": "README.md",
            "line": line_number,
            "license": _PUBLIC_APIS_LICENSE,
            "row_url": f"https://github.com/public-apis/public-apis/blob/{revision}/README.md#L{line_number}",
        }
        candidate = {
            "candidate_id": candidate_id,
            "type": "api_candidate",
            "name": name,
            "category": category,
            "summary": description or "No description was supplied in the source directory.",
            "listed_url": listed_url,
            "listed_url_role": "directory link; not verified as official documentation or API endpoint",
            "endpoint": None,
            "authentication": {"kind": "unknown", "required": False, "verified": False},
            "source_claims": {
                "authentication": auth_claim,
                "https": https_claim,
                "cors": cors_claim,
                "interpretation": "unverified community-directory fields; not independently checked",
            },
            "free_status": "UNKNOWN",
            "quota": "UNKNOWN",
            "rate_limits": "UNKNOWN",
            "license": "UNKNOWN",
            "checked_on": checked,
            "review_status": "needs_primary_source_review",
            "review_reasons": [
                "Resolve the listed URL to current official documentation and an API base endpoint.",
                "Verify authentication and any key/OAuth requirements from the provider.",
                "Verify free/paid access, quotas, rate limits, service/data licenses, and terms from primary sources.",
            ],
            "evidence_sources": [
                {
                    "url": attribution["row_url"],
                    "title": f"Public APIs community directory row: {name}",
                    "checked_on": checked,
                    "evidence_level": "community_directory_lead",
                }
            ],
            "attribution": attribution,
            "possible_duplicate_flags": [],
        }
        candidate["possible_existing_matches"] = _candidate_catalog_matches(candidate, existing_records)
        raw_candidates.append(candidate)

    source = {
        "format": "public-apis-markdown-index",
        "url": source_url,
        "repository": _PUBLIC_APIS_REPOSITORY,
        "revision": revision.lower(),
        "file": "README.md",
        "license": _PUBLIC_APIS_LICENSE,
        "checked_on": checked,
        "source_content_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        "rejected_rows": rejected_rows,
    }
    result = _build_queue(source, raw_candidates, len(raw_candidates))
    result["counts"]["rejected_rows"] = rejected_rows
    return result


def import_api_atlas_jsonl(
    jsonl: str | bytes,
    *,
    source_url: str,
    revision: str,
    checked_on: str | date | None = None,
    existing_records: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Import API Atlas JSONL API rows as attributed UNKNOWN review candidates.

    API Atlas access/auth/license and `verified` values are retained as source
    claims, not accepted as this project's verification. Non-API resources are
    counted but not imported into the API review queue.
    """
    source_url = _safe_http_url(source_url, require_https=True)
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-fA-F]{7,64}", revision):
        raise ValueError("revision must be a Git commit hash")
    checked = _canonical_date(checked_on)
    raw = jsonl.decode("utf-8") if isinstance(jsonl, bytes) else jsonl
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("API Atlas input must be non-empty JSONL text")
    if len(raw.encode("utf-8")) > 10 * 1024 * 1024:
        raise ValueError("API Atlas JSONL exceeds the 10 MiB import limit")

    rows: list[dict[str, Any]] = []
    rejected_rows = 0
    for line_number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            rejected_rows += 1
            continue
        if not isinstance(row, dict):
            rejected_rows += 1
            continue
        rows.append({"line": line_number, "row": row})

    all_verified = sum(item["row"].get("verified") is True for item in rows)
    api_items = [item for item in rows if str(item["row"].get("type", "")).casefold() == "api"]
    api_verified = sum(item["row"].get("verified") is True for item in api_items)
    raw_candidates: list[dict[str, Any]] = []
    upstream_license_map = {
        "public-apis": "MIT",
        "apis.guru": "CC0-1.0 for contributed OpenAPI definitions; external-source terms vary",
        "awesome-datasets": "MIT",
        "editorial": "CC BY 4.0 catalog content",
    }
    for item in api_items:
        row = item["row"]
        line_number = item["line"]
        name = row.get("name")
        website = row.get("website")
        if not isinstance(name, str) or not name.strip() or not isinstance(website, str):
            rejected_rows += 1
            continue
        try:
            website = _safe_http_url(website, require_https=False)
        except ValueError:
            rejected_rows += 1
            continue
        documentation_url = row.get("docs")
        if isinstance(documentation_url, str):
            try:
                documentation_url = _safe_http_url(documentation_url, require_https=False)
            except ValueError:
                documentation_url = None
        else:
            documentation_url = None
        category = row.get("category") if isinstance(row.get("category"), str) else "uncategorized"
        description = row.get("description") if isinstance(row.get("description"), str) else ""
        upstream_source = row.get("source") if isinstance(row.get("source"), str) else "UNKNOWN"
        source_names = [part.strip() for part in upstream_source.split(",") if part.strip()]
        attribution = {
            "repository": "https://github.com/CTCycle/api-atlas",
            "revision": revision.lower(),
            "file": "data/catalog.jsonl",
            "line": line_number,
            "row_id": str(row.get("id", ""))[:300],
            "catalog_license": "CC BY 4.0",
            "upstream_source": upstream_source,
            "upstream_license_claims": {source: upstream_license_map.get(source, "UNKNOWN") for source in source_names},
            "row_url": f"https://github.com/CTCycle/api-atlas/blob/{revision}/data/catalog.jsonl#L{line_number}",
        }
        upstream_checked = row.get("checked")
        candidate = {
            "candidate_id": _candidate_id(name.strip(), website, category),
            "type": "api_candidate",
            "name": name.strip()[:300],
            "category": category[:150],
            "categories": [category[:150]],
            "summary": re.sub(r"\s+", " ", description).strip()[:1500] or "No description was supplied in the source catalog.",
            "listed_url": website,
            "listed_url_role": "API Atlas website field; not verified as an API base URL",
            "documentation_url": documentation_url,
            "documentation_url_role": "API Atlas documentation pointer; not fetched or independently verified",
            "endpoint": None,
            "authentication": {"kind": "unknown", "required": False, "verified": False},
            "source_claims": {
                "api_atlas_access": str(row.get("access", "UNKNOWN"))[:100],
                "api_atlas_auth": str(row.get("auth", "UNKNOWN"))[:100],
                "api_atlas_license": str(row.get("license", "UNKNOWN"))[:500],
                "api_atlas_source": upstream_source,
                "api_atlas_verified": row.get("verified") is True,
                "api_atlas_checked": upstream_checked,
                "docs_present": row.get("docs_present") is True,
                "license_known": row.get("license_known") is True,
                "interpretation": "upstream directory claims only; not independently verified by DIVYESH API MIND",
            },
            "review_priority": "upstream_checked_pointer" if row.get("verified") is True else "unverified_directory_pointer",
            "free_status": "UNKNOWN",
            "quota": "UNKNOWN",
            "rate_limits": "UNKNOWN",
            "license": "UNKNOWN",
            "checked_on": checked,
            "upstream_checked_on": upstream_checked,
            "review_status": "needs_primary_source_review",
            "review_reasons": [
                "Confirm the current API base endpoint and at least one safe read operation from provider documentation.",
                "Independently verify access price/tier, auth requirements, quotas, and rate limits.",
                "Verify provider API/service terms and data license; API Atlas licensing applies to its catalog content, not the service/data.",
            ],
            "evidence_sources": [
                {
                    "url": attribution["row_url"],
                    "title": f"API Atlas curated API row: {name.strip()}",
                    "checked_on": checked,
                    "evidence_level": "secondary_curated_directory",
                }
            ],
            "attribution": attribution,
            "possible_duplicate_flags": [],
        }
        candidate["possible_existing_matches"] = _candidate_catalog_matches(candidate, existing_records)
        raw_candidates.append(candidate)

    source = {
        "format": "api-atlas-jsonl",
        "url": source_url,
        "repository": "https://github.com/CTCycle/api-atlas",
        "revision": revision.lower(),
        "file": "data/catalog.jsonl",
        "catalog_license": "CC BY 4.0",
        "checked_on": checked,
        "source_content_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        "resource_rows": len(rows),
        "verified_rows_across_all_resource_types": all_verified,
        "api_rows": len(api_items),
        "api_rows_marked_verified_upstream": api_verified,
        "non_api_rows_excluded": len(rows) - len(api_items),
        "rejected_rows": rejected_rows,
        "license_context": "API Atlas identifies its catalog compilation as CC BY 4.0 and preserves upstream row origins/licenses. These terms do not establish any listed API's service or data license.",
    }
    result = _build_queue(source, raw_candidates, len(raw_candidates))
    result["counts"]["api_rows_marked_verified_upstream"] = api_verified
    result["counts"]["unverified_directory_pointers"] = len(raw_candidates) - api_verified
    result["counts"]["rejected_rows"] = rejected_rows
    return result


def _parse_openapi_document(document: str | bytes | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(document, Mapping):
        return copy.deepcopy(dict(document))
    raw = document.decode("utf-8") if isinstance(document, bytes) else document
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("OpenAPI document must be non-empty JSON or YAML text")
    if len(raw.encode("utf-8")) > 5 * 1024 * 1024:
        raise ValueError("OpenAPI document exceeds 5 MiB import limit")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore[import-not-found]
        except ImportError:
            raise ValueError("YAML OpenAPI support is optional; install divyesh-api-mind[discovery-yaml]") from None
        try:
            parsed = yaml.safe_load(raw)
        except Exception as exc:  # yaml exception types vary between PyYAML releases
            raise ValueError(f"OpenAPI YAML could not be parsed ({type(exc).__name__})") from None
    if not isinstance(parsed, dict):
        raise ValueError("OpenAPI document root must be an object")
    return parsed


def _openapi_server(document: Mapping[str, Any], swagger_v2: bool) -> tuple[str | None, str]:
    candidates: list[str] = []
    if swagger_v2:
        host = document.get("host")
        if isinstance(host, str) and host:
            schemes = document.get("schemes")
            scheme = "https" if isinstance(schemes, list) and "https" in schemes else None
            if scheme:
                base_path = document.get("basePath", "")
                if not isinstance(base_path, str):
                    base_path = ""
                candidates.append(f"{scheme}://{host}{base_path}")
    else:
        servers = document.get("servers", [])
        if isinstance(servers, list):
            for server in servers:
                if not isinstance(server, dict) or not isinstance(server.get("url"), str):
                    continue
                url = server["url"]
                variables = server.get("variables", {})
                if isinstance(variables, dict):
                    for key, definition in variables.items():
                        if isinstance(definition, dict) and "default" in definition:
                            url = url.replace("{" + str(key) + "}", str(definition["default"]))
                candidates.append(url)
    if not candidates:
        return None, "no HTTPS server URL was declared"
    for candidate in candidates:
        if "{" in candidate or "}" in candidate:
            continue
        try:
            _safe_http_url(candidate, require_https=True)
            parsed = urlsplit(candidate)
            if parsed.query or parsed.fragment:
                continue
        except ValueError:
            continue
        return candidate.rstrip("/"), "first declared public HTTPS server"
    return None, "declared server is unresolved, non-HTTPS, or otherwise unsuitable for safe client use"


def _openapi_security_evidence(document: Mapping[str, Any], swagger_v2: bool) -> dict[str, Any]:
    if swagger_v2:
        schemes = document.get("securityDefinitions", {})
    else:
        components = document.get("components", {})
        schemes = components.get("securitySchemes", {}) if isinstance(components, dict) else {}
    global_security_present = "security" in document
    global_security = document.get("security") if global_security_present else None
    scheme_names = sorted(str(key) for key in schemes) if isinstance(schemes, dict) else []
    safe_scheme_fields = ("type", "in", "name", "scheme", "bearerFormat", "flow")
    scheme_details: dict[str, dict[str, str]] = {}
    if isinstance(schemes, dict):
        for key, definition in schemes.items():
            if not isinstance(key, str) or not isinstance(definition, dict):
                continue
            scheme_details[key[:100]] = {
                field: str(definition[field])[:200]
                for field in safe_scheme_fields
                if isinstance(definition.get(field), str)
            }
    operation_security: list[dict[str, Any]] = []
    paths = document.get("paths", {})
    if isinstance(paths, dict):
        for path, item in paths.items():
            if not isinstance(item, dict):
                continue
            for method, operation in item.items():
                if method.casefold() not in _HTTP_METHODS or not isinstance(operation, dict):
                    continue
                if "security" in operation:
                    operation_security.append(
                        {"path": str(path), "method": method.upper(), "requirements": copy.deepcopy(operation.get("security"))}
                    )
    return {
        "declared_by_spec": bool(scheme_names or global_security_present or operation_security),
        "scheme_names": scheme_names,
        "scheme_details": scheme_details,
        "global_security_declared": global_security_present,
        "global_security": copy.deepcopy(global_security),
        "operation_security": operation_security[:100],
        "reviewed": False,
        "warning": "OpenAPI security declarations are source claims; verify them against current official provider docs.",
    }


def _github_file_attribution(source_url: str, checked_on: str, spec_license: Mapping[str, Any]) -> dict[str, Any] | None:
    parsed = urlsplit(source_url)
    if parsed.hostname != "github.com":
        return None
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 5 or parts[2] != "blob":
        return None
    owner, repository, _blob, revision = parts[:4]
    return {
        "repository": f"https://github.com/{owner}/{repository}",
        "revision": revision,
        "file": "/".join(parts[4:]),
        "checked_on": checked_on,
        "spec_license": copy.deepcopy(dict(spec_license)),
        "repository_license_note": (
            "Repository-wide license metadata may not establish a third-party API's service/data license; "
            "review per-file provenance and provider terms."
        ),
    }


def import_openapi_spec(
    document: str | bytes | Mapping[str, Any],
    *,
    source_url: str,
    checked_on: str | date | None = None,
    existing_records: Iterable[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Parse an OpenAPI 2.0/3.x JSON/YAML spec into one UNKNOWN review lead."""
    source_url = _safe_http_url(source_url, require_https=True)
    checked = _canonical_date(checked_on)
    spec = _parse_openapi_document(document)
    swagger_v2 = spec.get("swagger") == "2.0"
    version = spec.get("openapi") if isinstance(spec.get("openapi"), str) else None
    if not swagger_v2 and not (isinstance(version, str) and version.startswith("3.")):
        raise ValueError("only OpenAPI 2.0 and 3.x specifications are supported")
    info = spec.get("info")
    if not isinstance(info, dict) or not isinstance(info.get("title"), str) or not info["title"].strip():
        raise ValueError("OpenAPI document must include info.title")
    name = _clean_markdown_cell(info["title"], 300)
    description = info.get("description", "")
    if not isinstance(description, str):
        description = ""
    description = re.sub(r"\s+", " ", html.unescape(description)).strip()[:1500]
    base_url, server_note = _openapi_server(spec, swagger_v2)
    paths = spec.get("paths", {})
    endpoints: list[dict[str, Any]] = []
    tags: set[str] = set()
    if isinstance(paths, dict):
        for path, path_item in sorted(paths.items(), key=lambda item: str(item[0])):
            if not isinstance(path, str) or not path.startswith("/") or not isinstance(path_item, dict):
                continue
            for method, operation in path_item.items():
                if not isinstance(method, str) or method.casefold() not in _HTTP_METHODS or not isinstance(operation, dict):
                    continue
                op_tags = operation.get("tags", [])
                if isinstance(op_tags, list):
                    tags.update(str(tag)[:100] for tag in op_tags if isinstance(tag, str) and tag.strip())
                endpoint: dict[str, Any] = {"method": method.upper(), "path": path[:500]}
                operation_id = operation.get("operationId")
                summary = operation.get("summary") or operation.get("description")
                if isinstance(operation_id, str) and operation_id:
                    endpoint["operation_id"] = operation_id[:200]
                if isinstance(summary, str) and summary.strip():
                    endpoint["summary"] = re.sub(r"\s+", " ", html.unescape(summary)).strip()[:500]
                if isinstance(op_tags, list):
                    endpoint["tags"] = [str(tag)[:100] for tag in op_tags if isinstance(tag, str)][:20]
                endpoints.append(endpoint)
                if len(endpoints) >= 100:
                    break
            if len(endpoints) >= 100:
                break
    external_docs = spec.get("externalDocs")
    official_docs_url = None
    if isinstance(external_docs, dict) and isinstance(external_docs.get("url"), str):
        try:
            official_docs_url = _safe_http_url(external_docs["url"], require_https=True)
        except ValueError:
            official_docs_url = None
    license_info = info.get("license")
    if isinstance(license_info, dict):
        spec_license = {
            "name": str(license_info.get("name", "UNKNOWN"))[:200],
            "url": license_info.get("url") if isinstance(license_info.get("url"), str) else None,
        }
    else:
        spec_license = {"name": "UNKNOWN", "url": None}
    security = _openapi_security_evidence(spec, swagger_v2)
    candidate = {
        "candidate_id": _candidate_id(name, base_url or source_url),
        "type": "api_candidate",
        "name": name,
        "summary": description or "No API summary was supplied by the OpenAPI document.",
        "base_url": base_url,
        "server_resolution": server_note,
        "listed_url": official_docs_url or source_url,
        "listed_url_role": "OpenAPI externalDocs URL" if official_docs_url else "OpenAPI specification source; not independently confirmed as provider-owned",
        "endpoint_count_in_spec": len(endpoints),
        "endpoints": endpoints,
        "tags": sorted(tags),
        "categories": sorted(tags),
        "authentication": {"kind": "unknown", "required": False, "verified": False},
        "authentication_evidence": security,
        "free_status": "UNKNOWN",
        "quota": "UNKNOWN",
        "rate_limits": "UNKNOWN",
        "license": "UNKNOWN",
        "spec_license": spec_license,
        "checked_on": checked,
        "review_status": "needs_primary_source_review",
        "review_reasons": [
            "Verify that the current specification is published or endorsed by the API provider.",
            "Verify auth semantics and any required credential scopes from official documentation.",
            "OpenAPI spec licensing does not establish API/data licensing; review the service terms.",
            "No free-tier, quota, or rate-limit claim is inferred from the specification.",
        ],
        "evidence_sources": [
            {"url": source_url, "title": f"OpenAPI {version or '2.0'} specification: {name}", "checked_on": checked, "evidence_level": "spec_import_not_independently_verified"}
        ],
        "source_attributions": [
            {
                "spec_url": source_url,
                "openapi_version": version or "2.0",
                "checked_on": checked,
                "spec_license": spec_license,
                **(_github_file_attribution(source_url, checked, spec_license) or {}),
            }
        ],
        "possible_duplicate_flags": [],
    }
    candidate["possible_existing_matches"] = _candidate_catalog_matches(candidate, existing_records)
    queue_source = {
        "format": "openapi-spec",
        "url": source_url,
        "checked_on": checked,
        "repository_attribution": _github_file_attribution(source_url, checked, spec_license),
        "source_content_sha256": hashlib.sha256(
            json.dumps(spec, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
        ).hexdigest(),
        "license": "UNKNOWN for the API; the spec's info.license is recorded separately and is not assumed to cover the service or data.",
    }
    return _build_queue(queue_source, [candidate], 1)


def read_discovery_source(
    url: str,
    *,
    transport: SafeHTTPTransport | None = None,
    max_bytes: int = 2 * 1024 * 1024,
) -> bytes:
    """Fetch one explicitly requested public HTTPS source with no redirects.

    The transport validates HTTPS/public hostnames, has bounded timeouts and
    responses, and refuses cross-host redirects. GitHub Contents API JSON
    responses are decoded when they contain base64 file content.
    """
    url = _safe_http_url(url, require_https=True)
    parsed = urlsplit(url)
    if parsed.fragment:
        raise UnsafeRequestError("Discovery source URLs must not contain a fragment")
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or not 1 <= max_bytes <= 5 * 1024 * 1024:
        raise ValueError("max_bytes must be between 1 byte and 5 MiB")
    client = transport or SafeHTTPTransport(timeout=10.0, retries=0, max_response_bytes=max_bytes)
    response = client.request(
        "discovery-source",
        "GET",
        url,
        allowed_hosts={parsed.hostname or ""},
        headers={"Accept": "application/vnd.github.raw+json, application/json, text/plain, */*"},
        retries=0,
        max_response_bytes=max_bytes,
    )
    if not 200 <= response.status_code < 300:
        raise APIError("discovery-source", f"Source fetch failed (status {response.status_code})", status_code=response.status_code)
    body = response.body
    if (parsed.hostname or "").lower() == "api.github.com":
        try:
            wrapper = json.loads(body.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            wrapper = None
        if isinstance(wrapper, dict) and wrapper.get("encoding") == "base64" and isinstance(wrapper.get("content"), str):
            try:
                body = base64.b64decode(wrapper["content"], validate=False)
            except (ValueError, base64.binascii.Error):
                raise CatalogError("GitHub contents response contains invalid base64 data") from None
            if len(body) > max_bytes:
                raise CatalogError("Decoded GitHub source exceeds the configured size limit")
    return body


def validate_review_queue(queue: Any) -> list[str]:
    """Return validation errors for a conservative discovery review queue."""
    if not isinstance(queue, dict):
        return ["discovery queue must be a JSON object"]
    if queue.get("schema_version") != _DISCOVERY_SCHEMA_VERSION:
        return ["unsupported discovery queue schema_version"]
    candidates = queue.get("candidates")
    counts = queue.get("counts")
    if not isinstance(candidates, list) or not isinstance(counts, dict):
        return ["discovery queue requires candidates and counts objects"]
    errors: list[str] = []
    try:
        _canonical_date(queue.get("generated_on"))
    except ValueError:
        errors.append("generated_on must be a valid YYYY-MM-DD date")
    policy = queue.get("policy")
    if not isinstance(policy, dict) or policy.get("free_status") != "UNKNOWN" or policy.get("automatic_catalog_promotion") is not False:
        errors.append("discovery policy must keep candidates UNKNOWN and disable automatic promotion")
    if counts.get("unique_candidates") != len(candidates):
        errors.append("counts.unique_candidates does not match candidates length")
    ids: set[str] = set()
    for index, candidate in enumerate(candidates):
        label = f"candidates[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{label} must be an object")
            continue
        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id:
            errors.append(f"{label} needs a candidate_id")
        elif candidate_id in ids:
            errors.append(f"{label} has duplicate candidate_id {candidate_id}")
        ids.add(candidate_id if isinstance(candidate_id, str) else f"<index {index}>")
        if not isinstance(candidate.get("name"), str) or not candidate["name"].strip():
            errors.append(f"{label} needs a non-empty name")
        if candidate.get("free_status") != "UNKNOWN":
            errors.append(f"{label} free_status must remain UNKNOWN until human review")
        auth = candidate.get("authentication")
        if not isinstance(auth, dict) or auth.get("kind") != "unknown" or auth.get("verified") is not False:
            errors.append(f"{label} authentication must remain unverified in the discovery queue")
        for field in ("quota", "rate_limits", "license"):
            if candidate.get(field) != "UNKNOWN":
                errors.append(f"{label} {field} must remain UNKNOWN until independently verified")
        if candidate.get("review_status") != "needs_primary_source_review":
            errors.append(f"{label} must remain in needs_primary_source_review")
        checked = candidate.get("checked_on")
        if checked is not None:
            try:
                _canonical_date(checked)
            except ValueError:
                errors.append(f"{label} checked_on must be YYYY-MM-DD")
        evidence = candidate.get("evidence_sources", [])
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{label} requires source attribution")
        else:
            for source_index, source in enumerate(evidence):
                if not isinstance(source, dict):
                    errors.append(f"{label} evidence_sources[{source_index}] must be an object")
                    continue
                try:
                    _safe_http_url(source.get("url"), require_https=True)
                except ValueError:
                    errors.append(f"{label} evidence_sources[{source_index}] URL must be safe HTTPS")
                if not isinstance(source.get("title"), str) or not source["title"].strip():
                    errors.append(f"{label} evidence_sources[{source_index}] needs a title")
                try:
                    _canonical_date(source.get("checked_on"))
                except ValueError:
                    errors.append(f"{label} evidence_sources[{source_index}] checked_on must be YYYY-MM-DD")
    if _contains_possible_secret(queue):
        errors.append("discovery queue contains a possible credential pattern")
    return errors


def load_review_queue(path: str | Path) -> dict[str, Any]:
    """Read and validate a review queue without promoting candidates to APIs."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CatalogError(f"Could not load discovery queue ({type(exc).__name__})") from None
    errors = validate_review_queue(data)
    if errors:
        raise CatalogError(f"Invalid discovery queue: {errors[0]}")
    return data


def search_review_queue(
    queue: Mapping[str, Any],
    *,
    query: str | None = None,
    category: str | None = None,
    priority: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Filter review candidates locally; does not verify or approve them."""
    allowed_priorities = {"upstream_checked_pointer", "unverified_directory_pointer"}
    if priority is not None and priority not in allowed_priorities:
        raise ValueError(f"priority must be one of: {', '.join(sorted(allowed_priorities))}")
    if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit < 0):
        raise ValueError("limit must be a non-negative integer or None")
    query_term = query.casefold() if query else None
    category_term = category.casefold() if category else None
    matches = []
    for candidate in queue.get("candidates", []):
        if not isinstance(candidate, dict):
            continue
        if category_term and category_term not in {
            str(value).casefold() for value in candidate.get("categories", [])
        } | ({str(candidate.get("category", "")).casefold()} if candidate.get("category") else set()):
            continue
        if priority is not None and candidate.get("review_priority") != priority:
            continue
        if query_term and query_term not in json.dumps(candidate, ensure_ascii=False).casefold():
            continue
        matches.append(copy.deepcopy(candidate))
    priority_order = {"upstream_checked_pointer": 0, "unverified_directory_pointer": 1}
    matches.sort(
        key=lambda item: (
            priority_order.get(str(item.get("review_priority", "")), 2),
            str(item.get("name", "")).casefold(),
            str(item.get("candidate_id", "")),
        )
    )
    return matches if limit is None else matches[:limit]
