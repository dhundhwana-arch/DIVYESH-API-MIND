"""Evidence-preserving, discovery-only technology research helpers.

The only built-in remote collector reads public GitHub repository metadata from
``api.github.com``. It is opt-in, does not follow redirects, does not call the
provider product/API, and never promotes a discovery record into an accepted
catalog. All other source collection is by explicit, caller-supplied evidence.
"""

from __future__ import annotations

import copy
import hashlib
import ipaddress
import json
import math
import re
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import quote, urlsplit

from .validation import STATUS_VALUES

_SCHEMA_VERSION = "1.0"
_REVIEW_SCHEMA_VERSION = "1.0"
_MAX_GITHUB_RESPONSE_BYTES = 512 * 1024
_MAX_GITHUB_TARGETS = 25
_MAX_TARGET_FILE_BYTES = 256 * 1024
_MAX_TARGET_TAGS = 50
_GITHUB_API = "https://api.github.com"
_REPO_NAME = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{1,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ACCESS_STATES = frozenset({"YES", "NO", "UNKNOWN", "CONDITIONAL"})
_CLAIM_STATES = frozenset({"PENDING_REVIEW", "HUMAN_REVIEWED", "INCONCLUSIVE", "UNKNOWN"})
_REVIEW_DECISIONS = frozenset({"SUPPORTS", "CONTRADICTS", "CONFLICTING", "INSUFFICIENT", "INCONCLUSIVE"})


class ResearchError(ValueError):
    """A safe, user-facing research input/source error."""


def canonical_sha256(value: Any) -> str:
    """Hash a JSON value using deterministic UTF-8 canonical serialization."""
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _valid_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _contains_secret(value: Any) -> bool:
    patterns = (
        re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
        re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
        re.compile(r"\bBearer\s+[A-Za-z0-9._~-]{20,}", re.IGNORECASE),
        re.compile(r"[?&](?:api[_-]?key|apikey|key|token)=([A-Za-z0-9_-]{20,})", re.IGNORECASE),
    )
    if isinstance(value, str):
        return any(pattern.search(value) for pattern in patterns)
    if isinstance(value, Mapping):
        return any(_contains_secret(key) or _contains_secret(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return any(_contains_secret(item) for item in value)
    return False


def _https_source_url(value: Any, *, host: str | None = None, allow_fragment: bool = False):
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme.casefold() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or parsed.query
        or (parsed.fragment and not allow_fragment)
    ):
        return None
    try:
        address = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        return None
    if host is not None and parsed.hostname.casefold() != host.casefold():
        return None
    return parsed


def _repo_slug(repo: str) -> str:
    if not isinstance(repo, str) or len(repo) > 200 or not _REPO_NAME.fullmatch(repo) or ".." in repo:
        raise ResearchError("repository must be a GitHub owner/name pair")
    return repo


def _snapshot_from_github(payload: Mapping[str, Any]) -> dict[str, Any]:
    owner = payload.get("owner")
    license_info = payload.get("license")
    topics = payload.get("topics", [])
    if not isinstance(owner, Mapping) or not isinstance(owner.get("login"), str):
        raise ResearchError("GitHub repository response lacks a valid owner")
    if not isinstance(topics, list) or any(not isinstance(item, str) for item in topics):
        topics = []
    if not isinstance(license_info, Mapping):
        license_info = {}
    counts: dict[str, int | None] = {}
    for key in ("stargazers_count", "forks_count", "subscribers_count", "size"):
        value = payload.get(key)
        counts[key] = value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None
    return {
        "full_name": payload.get("full_name") if isinstance(payload.get("full_name"), str) else None,
        "owner_login": owner["login"],
        "html_url": payload.get("html_url") if isinstance(payload.get("html_url"), str) else None,
        "description": payload.get("description") if isinstance(payload.get("description"), str) else None,
        "homepage": payload.get("homepage") if isinstance(payload.get("homepage"), str) and payload.get("homepage") else None,
        "topics": sorted(set(topics), key=str.casefold),
        "default_branch": payload.get("default_branch") if isinstance(payload.get("default_branch"), str) else None,
        "language": payload.get("language") if isinstance(payload.get("language"), str) else None,
        "created_at": payload.get("created_at") if isinstance(payload.get("created_at"), str) else None,
        "updated_at": payload.get("updated_at") if isinstance(payload.get("updated_at"), str) else None,
        "pushed_at": payload.get("pushed_at") if isinstance(payload.get("pushed_at"), str) else None,
        "archived": payload.get("archived") if isinstance(payload.get("archived"), bool) else None,
        "disabled": payload.get("disabled") if isinstance(payload.get("disabled"), bool) else None,
        "license": {
            "key": license_info.get("key") if isinstance(license_info.get("key"), str) else None,
            "name": license_info.get("name") if isinstance(license_info.get("name"), str) else None,
            "spdx_id": license_info.get("spdx_id") if isinstance(license_info.get("spdx_id"), str) else None,
            "url": license_info.get("url") if isinstance(license_info.get("url"), str) else None,
        },
        **counts,
    }


def _github_metadata(repo: str, *, timeout: float = 12.0) -> dict[str, Any]:
    repo = _repo_slug(repo)
    url = f"{_GITHUB_API}/repos/{quote(repo, safe='/')}"
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "api.github.com" or parsed.port not in (None, 443):
        raise ResearchError("GitHub source URL is outside the fixed HTTPS allowlist")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "DIVYESH-API-MIND-Mission-09-Research/0.1",
        },
        method="GET",
    )
    # Do not follow redirects: a public metadata read must stay on api.github.com.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    try:
        response = opener.open(request, timeout=timeout)
    except urllib.error.HTTPError as exc:
        raise ResearchError(f"GitHub repository metadata request returned HTTP {exc.code} for {repo}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", None)
        category = type(reason).__name__ if reason is not None else type(exc).__name__
        raise ResearchError(f"GitHub repository metadata request failed for {repo} ({category})") from None
    with response:
        final = _https_source_url(response.geturl(), host="api.github.com")
        if final is None or not final.path.startswith("/repos/"):
            raise ResearchError("GitHub metadata response escaped the fixed HTTPS host allowlist")
        raw = response.read(_MAX_GITHUB_RESPONSE_BYTES + 1)
    if len(raw) > _MAX_GITHUB_RESPONSE_BYTES:
        raise ResearchError(f"GitHub repository metadata response exceeded {_MAX_GITHUB_RESPONSE_BYTES} bytes")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        raise ResearchError(f"GitHub repository metadata response was not valid JSON for {repo}") from None
    returned_name = payload.get("full_name") if isinstance(payload, dict) else None
    if not isinstance(returned_name, str) or returned_name.casefold() != repo.casefold():
        raise ResearchError(f"GitHub repository response did not match the requested repository {repo}")
    return payload


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, newurl):  # type: ignore[no-untyped-def]
        return None


def create_github_discovery_record(
    target: Mapping[str, Any],
    *,
    checked_on: str,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Turn GitHub repository metadata into an UNKNOWN, non-promotable lead.

    ``payload`` is primarily for deterministic tests/import pipelines. When it
    is omitted, this function performs exactly one explicit GitHub metadata
    GET. No product API or candidate endpoint is contacted.
    """
    if not isinstance(target, Mapping):
        raise ResearchError("GitHub research target must be an object")
    repo = _repo_slug(target.get("repo"))
    if not _valid_date(checked_on):
        raise ResearchError("checked_on must be a valid YYYY-MM-DD date")
    kind = target.get("kind", "software_tool")
    if not isinstance(kind, str) or not kind.strip() or len(kind) > 80:
        raise ResearchError("target kind must be non-empty text")
    categories = target.get("categories", [])
    capabilities = target.get("capabilities", [])
    if (
        not isinstance(categories, list) or len(categories) > _MAX_TARGET_TAGS
        or not all(isinstance(item, str) and item.strip() and len(item) <= 120 for item in categories)
    ):
        raise ResearchError(f"target categories must contain at most {_MAX_TARGET_TAGS} non-empty strings of at most 120 characters")
    if (
        not isinstance(capabilities, list) or len(capabilities) > _MAX_TARGET_TAGS
        or not all(isinstance(item, str) and item.strip() and len(item) <= 120 for item in capabilities)
    ):
        raise ResearchError(f"target capabilities must contain at most {_MAX_TARGET_TAGS} non-empty strings of at most 120 characters")
    if payload is not None and not isinstance(payload, Mapping):
        raise ResearchError("GitHub metadata payload must be an object")
    source = dict(payload) if payload is not None else _github_metadata(repo)
    snapshot = _snapshot_from_github(source)
    full_name = snapshot["full_name"]
    html_url = snapshot["html_url"]
    if (
        not isinstance(full_name, str) or full_name.casefold() != repo.casefold()
        or snapshot["owner_login"].casefold() != repo.split("/", 1)[0].casefold()
        or not isinstance(html_url, str)
    ):
        raise ResearchError(f"GitHub metadata for {repo} lacks matching repository identity")
    # Do not accept arbitrary URLs returned by a remote JSON object as fetch targets.
    repo_url = _https_source_url(html_url, host="github.com")
    expected_path = "/" + full_name
    if repo_url is None or repo_url.path.rstrip("/").casefold() != expected_path.casefold():
        raise ResearchError(f"GitHub metadata for {repo} supplied an unsafe repository URL")
    snapshot_hash = canonical_sha256(snapshot)
    evidence_id = f"ghmeta-{hashlib.sha256((full_name.casefold() + checked_on + snapshot_hash).encode()).hexdigest()[:18]}"
    evidence = {
        "evidence_id": evidence_id,
        "evidence_type": "github_repository_metadata",
        "source_url": f"{_GITHUB_API}/repos/{quote(repo, safe='/')}",
        "repository_url": html_url,
        "checked_on": checked_on,
        "primary_source": True,
        "source_scope": "GitHub's own repository metadata only; not proof of product publisher identity or provider API behavior.",
        "claims_supported": [
            "GitHub reports this repository name, description, topics, activity timestamps, and license-detection metadata.",
            "GitHub repository metadata is not provider pricing, usage limits, API availability, or a complete license review.",
        ],
        "snapshot": snapshot,
        "snapshot_sha256": snapshot_hash,
    }
    base_id = re.sub(r"[^a-z0-9._-]+", "-", full_name.casefold()).strip("-.")
    record = {
        "id": f"gh-{base_id[:92]}",
        "provider": snapshot["owner_login"],
        "name": full_name,
        "kind": kind,
        "categories": sorted(set(categories), key=str.casefold),
        "capabilities": sorted(set(capabilities), key=str.casefold),
        "classification_basis": "Editorial research-target tags; not a provider-verified category or capability claim.",
        "description_source_claim": snapshot["description"],
        "github_topics_source_claim": snapshot["topics"],
        "official_website": None,
        "official_api_documentation": None,
        "official_pricing_page": None,
        "github_repository": html_url,
        "api_base_url": None,
        "authentication_status": "UNKNOWN",
        "api_key_required": "UNKNOWN",
        "free_status": "UNKNOWN",
        "unlimited_status": "UNKNOWN",
        "usage_limits": {
            "requests_per_minute": "UNKNOWN",
            "requests_per_day": "UNKNOWN",
            "monthly_quota": "UNKNOWN",
            "token_limits": "UNKNOWN",
            "file_size_limits": "UNKNOWN",
            "free_tier_expiry": "UNKNOWN",
        },
        "model_availability": "UNKNOWN",
        "input_capabilities": [],
        "output_capabilities": [],
        "python_integration": "UNKNOWN",
        "python_sdk_status": "UNKNOWN",
        "source_repository_license_metadata": snapshot["license"],
        "open_source_status": "UNKNOWN",
        "hosting_options": ["UNKNOWN"],
        "local_deployment_status": "UNKNOWN",
        "commercial_use_status": "UNKNOWN",
        "maintenance_status": "UNKNOWN",
        "github_activity_metadata": {
            key: snapshot[key] for key in ("created_at", "updated_at", "pushed_at", "archived", "disabled")
        },
        "source_language_metadata": snapshot["language"],
        "last_checked": checked_on,
        "evidence": [evidence],
        "evidence_refs": [evidence_id],
        "confidence": 0.35,
        "confidence_scope": "GitHub repository metadata existence only; no product or access claim is verified.",
        "unknown_fields": [
            "provider identity and relationship between repository owner and product",
            "official product website, API documentation, API base URL, and pricing",
            "registration, authentication, API-key rules, quotas, limits, and free-tier expiry",
            "commercial-use permissions and complete source/model/data licensing",
            "hosted-model availability, Python SDK support, runtime compatibility, and hardware requirements",
            "maintenance quality, security posture, service availability, and production suitability",
        ],
        "research_stage": "discovery",
        "human_review_status": "not_started",
        "proposal_status": "not_started",
        "accepted": False,
    }
    if _contains_secret(record):
        raise ResearchError("research metadata appears to contain a credential; record was not created")
    return record


def validate_technology_discovery(document: Any) -> list[str]:
    """Validate a separate research-only discovery catalog without promotion."""
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["technology discovery document must be an object"]
    if document.get("schema_version") != _SCHEMA_VERSION:
        errors.append(f"technology discovery schema_version must be {_SCHEMA_VERSION}")
    if document.get("catalog_role") != "discovery_only":
        errors.append("technology discovery catalog_role must be discovery_only")
    policy = document.get("policy")
    if not isinstance(policy, dict) or policy.get("automatic_catalog_promotion") is not False or policy.get("candidate_endpoint_calls") is not False:
        errors.append("technology discovery policy must disable automatic promotion and candidate endpoint calls")
    if "last_updated" in document and not _valid_date(document.get("last_updated")):
        errors.append("technology discovery last_updated must be YYYY-MM-DD")
    records = document.get("records")
    if not isinstance(records, list):
        errors.append("technology discovery records must be a list")
        return errors
    seen_ids: set[str] = set()
    seen_repositories: set[str] = set()
    seen_evidence: set[str] = set()
    for index, record in enumerate(records):
        label = f"technology discovery records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} must be an object")
            continue
        record_id = record.get("id")
        if not isinstance(record_id, str) or not _ID.fullmatch(record_id) or record_id in seen_ids:
            errors.append(f"{label}.id must be unique lowercase id text")
        else:
            seen_ids.add(record_id)
        for field in ("provider", "name", "kind", "github_repository"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                errors.append(f"{label}.{field} must be non-empty text")
        if not _valid_date(record.get("last_checked")):
            errors.append(f"{label}.last_checked must be YYYY-MM-DD")
        repo_url = record.get("github_repository")
        if isinstance(repo_url, str):
            parsed_repo = _https_source_url(repo_url, host="github.com")
            if parsed_repo is None or not re.fullmatch(r"/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?", parsed_repo.path):
                errors.append(f"{label}.github_repository must identify a credential-free GitHub repository URL")
            normalized_repo = (parsed_repo.hostname + parsed_repo.path.rstrip("/")).casefold() if parsed_repo else repo_url.casefold()
            if normalized_repo in seen_repositories:
                errors.append(f"{label}.github_repository is duplicated")
            seen_repositories.add(normalized_repo)
        for field in ("categories", "capabilities", "evidence", "evidence_refs", "unknown_fields"):
            value = record.get(field)
            if not isinstance(value, list):
                errors.append(f"{label}.{field} must be a list")
            elif field in {"categories", "capabilities", "unknown_fields"} and not all(isinstance(item, str) and item.strip() for item in value):
                errors.append(f"{label}.{field} must contain non-empty text values")
        free_status = record.get("free_status")
        if not isinstance(free_status, str) or free_status not in STATUS_VALUES:
            errors.append(f"{label}.free_status must use a catalog access status")
        if free_status != "UNKNOWN":
            errors.append(f"{label}.free_status must remain UNKNOWN until provider access is separately reviewed")
        reviewed_fields = (
            "api_key_required", "authentication_status", "open_source_status", "local_deployment_status",
            "commercial_use_status", "maintenance_status", "model_availability", "python_sdk_status", "unlimited_status",
        )
        for field in reviewed_fields:
            value = record.get(field, "UNKNOWN")
            allowed = _ACCESS_STATES | ({"LIMITED", "UNLIMITED"} if field == "unlimited_status" else set())
            if not isinstance(value, str) or value not in allowed:
                errors.append(f"{label}.{field} has an unsupported normalized status")
            elif value != "UNKNOWN":
                errors.append(f"{label}.{field} cannot be asserted by this discovery-only record")
        if record.get("accepted") is not False or record.get("research_stage") != "discovery":
            errors.append(f"{label} must remain a discovery-stage, non-accepted record")
        if record.get("human_review_status") != "not_started" or record.get("proposal_status") != "not_started":
            errors.append(f"{label} cannot imply a record-level review or proposal; use the separate append-only review ledger")
        confidence = record.get("confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            errors.append(f"{label}.confidence must be a finite value between 0 and 1")
        evidence = record.get("evidence")
        if not isinstance(evidence, list):
            continue
        evidence_ids: list[str] = []
        for eindex, item in enumerate(evidence):
            elabel = f"{label}.evidence[{eindex}]"
            if not isinstance(item, dict):
                errors.append(f"{elabel} must be an object")
                continue
            evidence_id = item.get("evidence_id")
            if not isinstance(evidence_id, str) or not _ID.fullmatch(evidence_id) or evidence_id in seen_evidence:
                errors.append(f"{elabel}.evidence_id must be globally unique lowercase id text")
            else:
                seen_evidence.add(evidence_id)
                evidence_ids.append(evidence_id)
            evidence_type = item.get("evidence_type")
            if not isinstance(evidence_type, str) or not re.fullmatch(r"[a-z][a-z0-9._-]{1,63}", evidence_type):
                errors.append(f"{elabel}.evidence_type must be a lowercase evidence identifier")
            source_url = item.get("source_url")
            parsed_source = _https_source_url(source_url, allow_fragment=True)
            if parsed_source is None:
                errors.append(f"{elabel}.source_url must be a credential-free public HTTPS reference")
            elif evidence_type == "github_repository_metadata":
                expected_path = f"/repos/{record.get('name', '').split('/', 1)[0]}/{record.get('name', '').split('/', 1)[-1]}"
                if parsed_source.hostname.casefold() != "api.github.com" or parsed_source.path.casefold() != expected_path.casefold():
                    errors.append(f"{elabel}.source_url must identify this repository's GitHub metadata endpoint")
            if not isinstance(item.get("primary_source"), bool):
                errors.append(f"{elabel}.primary_source must be boolean")
            claims = item.get("claims_supported")
            if not isinstance(claims, list) or not claims or not all(isinstance(claim, str) and claim.strip() for claim in claims):
                errors.append(f"{elabel}.claims_supported must contain non-empty text")
            if not _valid_date(item.get("checked_on")):
                errors.append(f"{elabel}.checked_on must be YYYY-MM-DD")
            snapshot = item.get("snapshot")
            digest = item.get("snapshot_sha256")
            if not isinstance(snapshot, dict) or not isinstance(digest, str) or not _SHA256.fullmatch(digest):
                errors.append(f"{elabel} requires a canonical snapshot and SHA-256")
            else:
                try:
                    matches = canonical_sha256(snapshot) == digest
                except (TypeError, ValueError):
                    matches = False
                if not matches:
                    errors.append(f"{elabel}.snapshot_sha256 does not match its snapshot")
            if _contains_secret(item):
                errors.append(f"{elabel} may contain a credential-like string")
        refs = record.get("evidence_refs")
        if isinstance(refs, list):
            if not all(isinstance(ref, str) for ref in refs) or evidence_ids != refs:
                errors.append(f"{label}.evidence_refs must exactly match its ordered evidence records")
        if not evidence_ids:
            errors.append(f"{label} must retain at least one evidence record")
        if _contains_secret(record):
            errors.append(f"{label} may contain a credential-like string")
    return errors


def load_github_targets(path: str | Path) -> list[dict[str, Any]]:
    """Read a local research target list. This function does not use network."""
    try:
        with Path(path).open("rb") as stream:
            raw = stream.read(_MAX_TARGET_FILE_BYTES + 1)
        if len(raw) > _MAX_TARGET_FILE_BYTES:
            raise ResearchError(f"GitHub research target file exceeds {_MAX_TARGET_FILE_BYTES} bytes")
        document = json.loads(raw.decode("utf-8"))
    except ResearchError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ResearchError(f"could not read GitHub research targets ({type(exc).__name__})") from None
    if not isinstance(document, dict) or document.get("schema_version") != _SCHEMA_VERSION:
        raise ResearchError("GitHub research target file has an unsupported schema")
    targets = document.get("targets")
    if not isinstance(targets, list) or not targets:
        raise ResearchError("GitHub research target file must contain a non-empty targets list")
    if len(targets) > _MAX_GITHUB_TARGETS:
        raise ResearchError(f"GitHub research runs are limited to {_MAX_GITHUB_TARGETS} repositories per invocation")
    seen: set[str] = set()
    result = []
    for item in targets:
        if not isinstance(item, dict):
            raise ResearchError("each GitHub research target must be an object")
        repo = _repo_slug(item.get("repo"))
        if repo.casefold() in seen:
            raise ResearchError(f"GitHub target list contains a duplicate repository: {repo}")
        seen.add(repo.casefold())
        kind = item.get("kind", "software_tool")
        categories = item.get("categories", [])
        capabilities = item.get("capabilities", [])
        if not isinstance(kind, str) or not kind.strip() or len(kind) > 80:
            raise ResearchError(f"GitHub target kind must be non-empty text of at most 80 characters for {repo}")
        if not isinstance(categories, list) or len(categories) > _MAX_TARGET_TAGS or not all(isinstance(v, str) and v.strip() and len(v) <= 120 for v in categories):
            raise ResearchError(f"GitHub target categories must contain at most {_MAX_TARGET_TAGS} bounded strings for {repo}")
        if not isinstance(capabilities, list) or len(capabilities) > _MAX_TARGET_TAGS or not all(isinstance(v, str) and v.strip() and len(v) <= 120 for v in capabilities):
            raise ResearchError(f"GitHub target capabilities must contain at most {_MAX_TARGET_TAGS} bounded strings for {repo}")
        result.append({"repo": repo, "kind": kind, "categories": categories, "capabilities": capabilities})
    return result


def merge_discovery_records(
    existing: Mapping[str, Any] | None,
    new_records: Sequence[Mapping[str, Any]],
    *,
    checked_on: str,
) -> dict[str, Any]:
    """Append repository observations idempotently; never promote a record."""
    if not _valid_date(checked_on):
        raise ResearchError("checked_on must be a valid YYYY-MM-DD date")
    if existing is None:
        document: dict[str, Any] = {
            "schema_version": _SCHEMA_VERSION,
            "catalog_role": "discovery_only",
            "last_updated": checked_on,
            "policy": {
                "automatic_catalog_promotion": False,
                "candidate_endpoint_calls": False,
                "github_source_host_allowlist": ["api.github.com"],
                "note": "Repository metadata leads only. Unknown access, license, quota, maintenance, and provider claims remain unknown until separately reviewed.",
            },
            "records": [],
        }
    else:
        document = copy.deepcopy(dict(existing))
    errors = validate_technology_discovery(document)
    if errors:
        raise ResearchError(f"existing technology discovery catalog is invalid: {errors[0]}")
    records = document["records"]
    by_repo = {item["github_repository"].casefold(): item for item in records}
    changed = False
    for incoming_value in new_records:
        incoming = copy.deepcopy(dict(incoming_value))
        errors = validate_technology_discovery({
            "schema_version": _SCHEMA_VERSION,
            "catalog_role": "discovery_only",
            "policy": {"automatic_catalog_promotion": False, "candidate_endpoint_calls": False},
            "records": [incoming],
        })
        if errors:
            raise ResearchError(f"new GitHub discovery record is invalid: {errors[0]}")
        key = incoming["github_repository"].casefold()
        current = by_repo.get(key)
        if current is None:
            if any(item["id"] == incoming["id"] for item in records):
                raise ResearchError("discovery candidate ID collides with a different repository")
            records.append(incoming)
            by_repo[key] = records[-1]
            changed = True
            continue
        current_evidence = {item["evidence_id"] for item in current["evidence"]}
        unseen = [item for item in incoming["evidence"] if item["evidence_id"] not in current_evidence]
        if not unseen:
            continue
        # Keep every previous observation. Update only the latest projection;
        # the former values remain recoverable from prior evidence snapshots.
        current["evidence"].extend(copy.deepcopy(unseen))
        current["evidence_refs"].extend(item["evidence_id"] for item in unseen)
        changed = True
        # The projection points at the newest observation, while earlier (even
        # explicitly backdated) evidence remains append-only in the history.
        current_date = current.get("last_checked")
        if isinstance(current_date, str) and checked_on >= current_date:
            for key_name in (
                "description_source_claim", "github_topics_source_claim", "source_repository_license_metadata",
                "github_activity_metadata", "source_language_metadata", "last_checked",
            ):
                current[key_name] = copy.deepcopy(incoming[key_name])
    if changed:
        previous_updated = document.get("last_updated", checked_on)
        document["last_updated"] = max(previous_updated, checked_on) if isinstance(previous_updated, str) else checked_on
    errors = validate_technology_discovery(document)
    if errors:
        raise ResearchError(f"merged technology discovery catalog is invalid: {errors[0]}")
    return document


class TechnologyResearchPipeline:
    """Opt-in GitHub source collector plus append-only research helpers."""

    def __init__(self, *, timeout: float = 12.0) -> None:
        if (
            isinstance(timeout, bool) or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout) or timeout <= 0 or timeout > 30
        ):
            raise ValueError("timeout must be greater than 0 and no more than 30 seconds")
        self.timeout = float(timeout)

    def discover_github_targets(
        self,
        targets: Sequence[Mapping[str, Any]],
        *,
        checked_on: str,
        existing: Mapping[str, Any] | None = None,
        fetcher=None,
    ) -> tuple[dict[str, Any], list[str]]:
        """Read one GitHub repo metadata document per target; preserve successes.

        ``fetcher`` is injectable for offline tests. No product endpoint is
        contacted. Per-target failures are returned as sanitized strings.
        """
        if not _valid_date(checked_on):
            raise ResearchError("checked_on must be a valid YYYY-MM-DD date")
        if not isinstance(targets, Sequence) or isinstance(targets, (str, bytes)) or len(targets) > _MAX_GITHUB_TARGETS:
            raise ResearchError(f"targets must be a sequence of at most {_MAX_GITHUB_TARGETS} repositories")
        records: list[dict[str, Any]] = []
        errors: list[str] = []
        seen: set[str] = set()
        source_fetch = fetcher or (lambda repo: _github_metadata(repo, timeout=self.timeout))
        for index, target in enumerate(targets, 1):
            if not isinstance(target, Mapping):
                errors.append(f"target {index}: expected an object; skipped")
                continue
            try:
                repo = _repo_slug(target.get("repo"))
            except ResearchError as exc:
                errors.append(f"target {index}: {exc}")
                continue
            if repo.casefold() in seen:
                errors.append(f"{repo}: duplicate target skipped")
                continue
            seen.add(repo.casefold())
            try:
                payload = source_fetch(repo)
                records.append(create_github_discovery_record(target, checked_on=checked_on, payload=payload))
            except ResearchError as exc:
                errors.append(str(exc))
        return merge_discovery_records(existing, records, checked_on=checked_on), errors

    @staticmethod
    def append_evidence(
        record: Mapping[str, Any],
        *,
        evidence_type: str,
        source_url: str,
        checked_on: str,
        claims_supported: Sequence[str],
        snapshot: Mapping[str, Any],
        primary_source: bool,
    ) -> dict[str, Any]:
        """Append hash-identified source evidence without changing any review state."""
        if not isinstance(record, Mapping):
            raise ResearchError("discovery record must be an object")
        if not isinstance(evidence_type, str) or not re.fullmatch(r"[a-z][a-z0-9._-]{1,63}", evidence_type):
            raise ResearchError("evidence_type must be a lowercase evidence identifier")
        if not _valid_date(checked_on):
            raise ResearchError("checked_on must be YYYY-MM-DD")
        parsed = _https_source_url(source_url, allow_fragment=True)
        if parsed is None:
            raise ResearchError("evidence source must be a credential-free public HTTPS URL")
        if not isinstance(primary_source, bool):
            raise ResearchError("primary_source must be boolean")
        if not isinstance(snapshot, Mapping) or not isinstance(claims_supported, Sequence) or isinstance(claims_supported, (str, bytes)):
            raise ResearchError("evidence snapshot and supported claims must be structured values")
        if not claims_supported or not all(isinstance(claim, str) and claim.strip() for claim in claims_supported):
            raise ResearchError("claims_supported must contain non-empty strings")
        value = copy.deepcopy(dict(record))
        policy = {"automatic_catalog_promotion": False, "candidate_endpoint_calls": False}
        validation_document = {"schema_version": _SCHEMA_VERSION, "catalog_role": "discovery_only", "policy": policy, "records": [value]}
        errors = validate_technology_discovery(validation_document)
        if errors:
            raise ResearchError(f"discovery record is invalid: {errors[0]}")
        snapshot_value = copy.deepcopy(dict(snapshot))
        if _contains_secret({"source_url": source_url, "claims_supported": claims_supported, "snapshot": snapshot_value}):
            raise ResearchError("evidence appears to contain a credential")
        try:
            digest = canonical_sha256(snapshot_value)
        except (TypeError, ValueError):
            raise ResearchError("evidence snapshot must be finite, canonical JSON data") from None
        evidence_id = f"evidence-{hashlib.sha256((value['id'] + evidence_type + source_url + checked_on + digest).encode()).hexdigest()[:18]}"
        evidence = copy.deepcopy(value["evidence"])
        if any(item.get("evidence_id") == evidence_id for item in evidence if isinstance(item, dict)):
            raise ResearchError("evidence already exists; prior observations are append-only")
        evidence.append({
            "evidence_id": evidence_id,
            "evidence_type": evidence_type,
            "source_url": source_url,
            "checked_on": checked_on,
            "primary_source": primary_source,
            "claims_supported": list(claims_supported),
            "snapshot": snapshot_value,
            "snapshot_sha256": digest,
        })
        value["evidence"] = evidence
        value["evidence_refs"] = [item["evidence_id"] for item in evidence]
        final_document = {"schema_version": _SCHEMA_VERSION, "catalog_role": "discovery_only", "policy": policy, "records": [value]}
        errors = validate_technology_discovery(final_document)
        if errors:
            raise ResearchError(f"appended discovery evidence is invalid: {errors[0]}")
        return value

    @staticmethod
    def normalize_claim(
        *,
        field: str,
        raw_value: Any,
        normalized_value: Any,
        evidence_refs: Sequence[str],
        confidence: float,
        reviewer: str | None = None,
        disposition: str = "PENDING_REVIEW",
    ) -> dict[str, Any]:
        """Create a normalized claim for separate human review.

        This helper does not write into the discovery record or accepted catalog.
        It deliberately does not provide an automatic ``VERIFIED`` disposition.
        """
        if not isinstance(field, str) or not field.strip():
            raise ResearchError("claim field must be non-empty text")
        if not isinstance(disposition, str) or disposition not in _CLAIM_STATES:
            raise ResearchError(f"disposition must be one of: {', '.join(sorted(_CLAIM_STATES))}")
        if disposition == "HUMAN_REVIEWED" and (not isinstance(reviewer, str) or not reviewer.strip()):
            raise ResearchError("human-reviewed claims require a named reviewer")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            raise ResearchError("claim confidence must be a finite value between 0 and 1")
        if not isinstance(evidence_refs, Sequence) or isinstance(evidence_refs, (str, bytes)):
            raise ResearchError("evidence_refs must be a list of evidence identifiers")
        refs = list(evidence_refs)
        if not refs or not all(isinstance(ref, str) and ref for ref in refs) or len(refs) != len(set(refs)):
            raise ResearchError("a claim must cite unique, non-empty evidence references")
        if _contains_secret({"raw_value": raw_value, "normalized_value": normalized_value}):
            raise ResearchError("claim values appear to contain a credential")
        try:
            claim_digest = canonical_sha256({"field": field, "raw_value": raw_value, "normalized_value": normalized_value})
        except (TypeError, ValueError):
            raise ResearchError("claim values must be finite JSON data") from None
        return {
            "claim_id": f"claim-{claim_digest[:18]}",
            "field": field,
            "raw_value": copy.deepcopy(raw_value),
            "normalized_value": copy.deepcopy(normalized_value),
            "evidence_refs": refs,
            "confidence": float(confidence),
            "disposition": disposition,
            "reviewer": reviewer.strip() if isinstance(reviewer, str) and reviewer.strip() else None,
        }


def new_research_review_ledger() -> dict[str, Any]:
    """Create an empty append-only human claim-review ledger."""
    return {
        "schema_version": _REVIEW_SCHEMA_VERSION,
        "ledger_role": "human_claim_review_only",
        "automatic_catalog_promotion": False,
        "accepted_catalog_modified": False,
        "events": [],
    }


def validate_research_review_ledger(document: Any) -> list[str]:
    """Validate event sequencing, hash links, evidence references, and review scope."""
    if not isinstance(document, dict):
        return ["research review ledger must be an object"]
    errors: list[str] = []
    if document.get("schema_version") != _REVIEW_SCHEMA_VERSION:
        errors.append(f"research review ledger schema_version must be {_REVIEW_SCHEMA_VERSION}")
    if document.get("ledger_role") != "human_claim_review_only":
        errors.append("research review ledger role is invalid")
    if document.get("automatic_catalog_promotion") is not False or document.get("accepted_catalog_modified") is not False:
        errors.append("research review ledger must not promote records or modify accepted catalogs")
    events = document.get("events")
    if not isinstance(events, list):
        errors.append("research review ledger events must be a list")
        return errors
    previous_digest = ""
    seen_ids: set[str] = set()
    for index, event in enumerate(events, 1):
        label = f"research review ledger events[{index - 1}]"
        if not isinstance(event, dict):
            errors.append(f"{label} must be an object")
            continue
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not _ID.fullmatch(event_id) or event_id in seen_ids:
            errors.append(f"{label}.event_id must be unique lowercase id text")
        else:
            seen_ids.add(event_id)
        sequence = event.get("sequence")
        if isinstance(sequence, bool) or sequence != index:
            errors.append(f"{label}.sequence must be {index}")
        record_id = event.get("record_id")
        if not isinstance(record_id, str) or not _ID.fullmatch(record_id):
            errors.append(f"{label}.record_id must be a discovery record ID")
        field = event.get("field")
        if not isinstance(field, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,79}", field):
            errors.append(f"{label}.field must be a normalized field name")
        if not isinstance(event.get("decision"), str) or event.get("decision") not in _REVIEW_DECISIONS:
            errors.append(f"{label}.decision is unsupported")
        if not isinstance(event.get("reviewer"), str) or not event["reviewer"].strip():
            errors.append(f"{label}.reviewer must identify a human reviewer")
        if not isinstance(event.get("notes"), str) or not event["notes"].strip():
            errors.append(f"{label}.notes must explain the review")
        if not _valid_date(event.get("recorded_on")):
            errors.append(f"{label}.recorded_on must be YYYY-MM-DD")
        refs = event.get("evidence_refs")
        if not isinstance(refs, list) or not refs or not all(isinstance(ref, str) and _ID.fullmatch(ref) for ref in refs):
            errors.append(f"{label}.evidence_refs must contain evidence IDs")
        elif len(refs) != len(set(refs)):
            errors.append(f"{label}.evidence_refs must be unique")
        confidence = event.get("confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            errors.append(f"{label}.confidence must be finite and between 0 and 1")
        if "raw_value" not in event or "normalized_value" not in event:
            errors.append(f"{label} must retain raw and normalized claim values")
        claim_digest = event.get("claim_payload_sha256")
        if not isinstance(claim_digest, str) or not _SHA256.fullmatch(claim_digest):
            errors.append(f"{label}.claim_payload_sha256 must be a lowercase SHA-256")
        else:
            try:
                claim_matches = canonical_sha256({"raw_value": event.get("raw_value"), "normalized_value": event.get("normalized_value")}) == claim_digest
            except (TypeError, ValueError):
                claim_matches = False
            if not claim_matches:
                errors.append(f"{label}.claim_payload_sha256 does not match its claim values")
        if event.get("automatic_catalog_promotion") is not False or event.get("accepted_catalog_modified") is not False:
            errors.append(f"{label} must not promote records or modify accepted catalogs")
        if event.get("previous_event_sha256") != previous_digest:
            errors.append(f"{label}.previous_event_sha256 does not match the preceding event")
        digest = event.get("event_sha256")
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            errors.append(f"{label}.event_sha256 must be a lowercase SHA-256")
        else:
            payload = {key: value for key, value in event.items() if key != "event_sha256"}
            try:
                matches = canonical_sha256(payload) == digest
            except (TypeError, ValueError):
                matches = False
            if not matches:
                errors.append(f"{label}.event_sha256 does not match its event")
        if _contains_secret(event):
            errors.append(f"{label} may contain a credential-like string")
        if isinstance(digest, str) and _SHA256.fullmatch(digest):
            previous_digest = digest
    return errors


def append_research_review_event(
    ledger: Mapping[str, Any] | None,
    *,
    discovery_document: Mapping[str, Any],
    record_id: str,
    field: str,
    raw_value: Any,
    normalized_value: Any,
    decision: str,
    evidence_refs: Sequence[str],
    reviewer: str,
    notes: str,
    confidence: float,
    recorded_on: str,
) -> dict[str, Any]:
    """Append one explicit human review decision, never changing source records.

    Every event is linked to prior evidence from its discovery record and hashed
    into an ordered chain. This is tamper-evident history, not a digital
    signature or a substitute for a protected backup.
    """
    if not isinstance(discovery_document, Mapping):
        raise ResearchError("a valid discovery-only catalog is required to review a claim")
    discovery_errors = validate_technology_discovery(dict(discovery_document))
    if discovery_errors:
        raise ResearchError(f"discovery catalog is invalid: {discovery_errors[0]}")
    matches = [item for item in discovery_document["records"] if item.get("id") == record_id]
    if len(matches) != 1:
        raise ResearchError("review record ID does not identify one discovery-only record")
    record_evidence = set(matches[0]["evidence_refs"])
    if not isinstance(evidence_refs, Sequence) or isinstance(evidence_refs, (str, bytes)):
        raise ResearchError("evidence_refs must be a list of evidence IDs")
    refs = list(evidence_refs)
    if not refs or not all(isinstance(ref, str) and ref in record_evidence for ref in refs):
        raise ResearchError("every review evidence reference must belong to this discovery record")
    if len(refs) != len(set(refs)):
        raise ResearchError("review evidence references must be unique")
    if not isinstance(decision, str) or decision not in _REVIEW_DECISIONS:
        raise ResearchError(f"decision must be one of: {', '.join(sorted(_REVIEW_DECISIONS))}")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ResearchError("a named human reviewer is required")
    if not isinstance(notes, str) or not notes.strip():
        raise ResearchError("review notes are required")
    if not _valid_date(recorded_on):
        raise ResearchError("recorded_on must be YYYY-MM-DD")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise ResearchError("review confidence must be finite and between 0 and 1")
    if not isinstance(field, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,79}", field):
        raise ResearchError("field must be a normalized field name")
    try:
        values_digest = canonical_sha256({"raw_value": raw_value, "normalized_value": normalized_value})
    except (TypeError, ValueError):
        raise ResearchError("review claim values must be finite JSON data") from None
    if _contains_secret({"raw_value": raw_value, "normalized_value": normalized_value, "reviewer": reviewer, "notes": notes}):
        raise ResearchError("review event appears to contain a credential")
    if ledger is None:
        updated = new_research_review_ledger()
    else:
        if not isinstance(ledger, Mapping):
            raise ResearchError("research review ledger must be an object")
        errors = validate_research_review_ledger(dict(ledger))
        if errors:
            raise ResearchError(f"research review ledger is invalid: {errors[0]}")
        updated = copy.deepcopy(dict(ledger))
    events = updated["events"]
    previous = events[-1]["event_sha256"] if events else ""
    core: dict[str, Any] = {
        "sequence": len(events) + 1,
        "record_id": record_id,
        "field": field,
        "raw_value": copy.deepcopy(raw_value),
        "normalized_value": copy.deepcopy(normalized_value),
        "claim_payload_sha256": values_digest,
        "decision": decision,
        "evidence_refs": refs,
        "reviewer": reviewer.strip(),
        "notes": notes.strip(),
        "confidence": float(confidence),
        "recorded_on": recorded_on,
        "previous_event_sha256": previous,
        "automatic_catalog_promotion": False,
        "accepted_catalog_modified": False,
    }
    # Reuse the strict claim checks for confidence bounds and credential shape.
    normalized_claim = TechnologyResearchPipeline.normalize_claim(
        field=field, raw_value=raw_value, normalized_value=normalized_value,
        evidence_refs=refs, confidence=confidence, reviewer=reviewer, disposition="HUMAN_REVIEWED",
    )
    core["claim_id"] = normalized_claim["claim_id"]
    core["event_id"] = f"review-{hashlib.sha256(canonical_sha256(core).encode()).hexdigest()[:18]}"
    core["event_sha256"] = canonical_sha256(core)
    events.append(core)
    errors = validate_research_review_ledger(updated)
    if errors:
        raise ResearchError(f"appended review event is invalid: {errors[0]}")
    return updated
