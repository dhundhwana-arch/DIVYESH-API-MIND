"""Evidence-first API triage, ranking, and human review workflow.

Ranking is a queue-management aid, not a verification result. Directory claims
are weak review signals only. This module makes no provider requests and never
promotes a candidate into the accepted catalog.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import threading
import time
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence
from urllib.parse import unquote, urlsplit

from .discovery import _canonical_date, _canonical_url, _name_key, _safe_http_url, validate_review_queue
from .exceptions import APIError, CatalogError, UnsafeRequestError
from .transport import HTTPResult, SafeHTTPTransport, _check_relative_path
from .validation import _contains_possible_secret, validate_catalog_data

VERIFICATION_SCHEMA_VERSION = "1.1"
VERIFICATION_STAGES = (
    "candidate_discovery",
    "metadata_validation",
    "official_source_identification",
    "documentation_review",
    "authentication_verification",
    "free_tier_verification",
    "endpoint_verification",
    "license_review",
    "human_approval",
    "catalog_acceptance",
)

# The weights total 100. Scores measure available review signals and integration
# readiness, not API quality, truth, free status, uptime, or approval.
_AUTH_RECORD_KINDS = frozenset({
    "none", "bearer", "optional_bearer", "api_key_header", "optional_api_key_header", "api_key_query", "http_basic_pair"
})

SCORING_WEIGHTS = {
    "project_usefulness": 18,
    "official_documentation_availability": 16,
    "openapi_spec_availability": 14,
    "free_access_evidence": 10,
    "authentication_requirements": 8,
    "maintenance_activity": 8,
    "license_clarity": 8,
    "category_diversity": 10,
    "integration_feasibility": 8,
}

# Themes reflect capabilities already represented by bundled records/examples.
_PROJECT_USE_CASES = {
    "research": ("research", "scholarly", "academic", "citation", "doi", "publication", "paper", "preprint", "bibliographic"),
    "public_data": ("government", "open data", "census", "statistics", "public records", "development data", "earth observation"),
    "developer_ecosystem": ("developer", "repository", "package", "npm", "pypi", "git", "code hosting", "dependency"),
    "security": ("security", "vulnerability", "cve", "osv", "malware", "threat", "identity"),
    "geospatial": ("geospatial", "geography", "geocoding", "mapping", "map", "location", "spatial", "coordinates"),
    "climate_environment": ("weather", "climate", "environment", "air quality", "earthquake", "soil", "water", "agriculture", "satellite"),
    "finance_economics": ("finance", "financial", "currency", "exchange rate", "economic", "economics", "bank", "market data"),
    "ai_ml": ("artificial intelligence", "machine learning", " llm", "language model", "inference", "embedding", "ai/ml"),
}

EVIDENCE_TYPES = frozenset({
    "source_directory",
    "provider_homepage",
    "official_registry",
    "official_documentation",
    "openapi_specification",
    "authentication_documentation",
    "pricing_access_documentation",
    "quota_documentation",
    "endpoint_documentation",
    "endpoint_probe",
    "terms_of_service",
    "license_documentation",
    "maintenance_record",
    "integration_test",
    "other",
})
SOURCE_CLASSIFICATIONS = frozenset({
    "official_provider", "official_repository", "official_registry", "secondary_catalog", "community", "probe_result", "unknown"
})
EVIDENCE_REVIEW_STATUSES = frozenset({"supports", "contradicts", "inconclusive", "not_accessible", "unreviewed"})
FINDING_STATUSES = frozenset({"verified", "inconclusive", "unknown"})
TRANSITION_OUTCOMES = frozenset({"completed", "blocked", "deferred", "rejected", "resumed"})
_PROBE_MIN_INTERVAL_SECONDS = 2.0
_PROBE_LAST_BY_HOST: dict[str, float] = {}
_PROBE_RATE_LOCK = threading.Lock()

FINDING_STAGE = {
    "api_real": "official_source_identification",
    "official_provider": "official_source_identification",
    "documentation_available": "documentation_review",
    "maintenance_activity": "documentation_review",
    "authentication": "authentication_verification",
    "free_tier": "free_tier_verification",
    "quotas": "free_tier_verification",
    "currently_accessible": "endpoint_verification",
    "python_integration": "endpoint_verification",
    "license": "license_review",
}
_FINDING_FIELDS = tuple(FINDING_STAGE)
_STAGE_FINDINGS = {
    "official_source_identification": ("api_real", "official_provider"),
    "documentation_review": ("documentation_available", "maintenance_activity"),
    "authentication_verification": ("authentication",),
    "free_tier_verification": ("free_tier", "quotas"),
    "endpoint_verification": ("currently_accessible", "python_integration"),
    "license_review": ("license",),
}
_STAGE_EVIDENCE_TYPES = {
    "official_source_identification": {"provider_homepage", "official_registry", "official_documentation"},
    "documentation_review": {"official_documentation", "openapi_specification", "maintenance_record"},
    "authentication_verification": {"authentication_documentation", "official_documentation"},
    "free_tier_verification": {"pricing_access_documentation", "terms_of_service", "official_documentation", "quota_documentation"},
    "endpoint_verification": {"endpoint_documentation", "endpoint_probe", "integration_test"},
    "license_review": {"license_documentation", "terms_of_service"},
}


def _date_text(value: str | date | None) -> str:
    if isinstance(value, datetime):
        raise ValueError("date values must not include a time component")
    return date.today().isoformat() if value is None else _canonical_date(value)


def _clean_text(value: Any, limit: int = 4000) -> str:
    return " ".join(value.split())[:limit] if isinstance(value, str) else ""


def _categories(candidate: Mapping[str, Any]) -> list[str]:
    values = [str(item) for item in candidate.get("categories", []) if isinstance(item, str)] if isinstance(candidate.get("categories"), list) else []
    if isinstance(candidate.get("category"), str):
        values.append(candidate["category"])
    normalized = {" ".join(value.casefold().split()) for value in values if value.strip()}
    return sorted(normalized or {"uncategorized"})


def _candidate_text(candidate: Mapping[str, Any]) -> str:
    values: list[str] = []
    for field in ("name", "summary", "category", "categories", "tags"):
        value = candidate.get(field)
        if isinstance(value, list):
            values.extend(str(item) for item in value if isinstance(item, (str, int, float)))
        elif isinstance(value, (str, int, float)):
            values.append(str(value))
    endpoints = candidate.get("endpoints", [])
    if isinstance(endpoints, list):
        for endpoint in endpoints:
            if isinstance(endpoint, dict):
                values.extend(str(endpoint.get(key, "")) for key in ("summary", "purpose", "path"))
    return " ".join(values).casefold()


def _claim_groups(candidate: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    groups: list[Mapping[str, Any]] = []
    claims = candidate.get("source_claims")
    if isinstance(claims, dict):
        groups.append(claims)
    grouped = candidate.get("source_claims_by_source")
    if isinstance(grouped, list):
        groups.extend(item["claims"] for item in grouped if isinstance(item, dict) and isinstance(item.get("claims"), dict))
    return groups


def _claim_values(candidate: Mapping[str, Any], *keys: str) -> list[Any]:
    values: list[Any] = []
    for group in _claim_groups(candidate):
        for key in keys:
            value = group.get(key)
            if value not in (None, "", "UNKNOWN") and value not in values:
                values.append(value)
    return values


def _workflow_from_review(review: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(review, Mapping):
        return {}
    workflow = review.get("workflow")
    return workflow if isinstance(workflow, Mapping) else review


def _evidence_map(workflow: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    values = workflow.get("evidence", [])
    if not isinstance(values, list):
        return {}
    return {item["evidence_id"]: item for item in values if isinstance(item, dict) and isinstance(item.get("evidence_id"), str)}


def _confidence_is_authoritative(evidence: Mapping[str, Any]) -> bool:
    confidence = evidence.get("confidence")
    return (
        evidence.get("reviewer_status") == "supports"
        and isinstance(confidence, (int, float))
        and not isinstance(confidence, bool)
        and math.isfinite(float(confidence))
        and float(confidence) >= 0.75
    )


def _probe_permission_valid(evidence: Mapping[str, Any] | None) -> bool:
    return bool(
        isinstance(evidence, Mapping)
        and isinstance(evidence.get("evidence_type"), str)
        and evidence.get("evidence_type") in {"terms_of_service", "official_documentation"}
        and evidence.get("source_classification") == "official_provider"
        and evidence.get("primary_source") is True
        and evidence.get("permits_unauthenticated_read_probes") is True
        and _confidence_is_authoritative(evidence)
    )


def _authoritative_evidence(evidence: Mapping[str, Any], field: str) -> bool:
    if not _confidence_is_authoritative(evidence):
        return False
    if field == "currently_accessible":
        return (
            evidence.get("evidence_type") == "endpoint_probe"
            and evidence.get("source_classification") == "probe_result"
            and evidence.get("primary_source") is True
            and evidence.get("policy_permitted") is True
            and evidence.get("credentials_sent") is False
            and evidence.get("request_method") in {"GET", "HEAD"}
            and isinstance(evidence.get("permission_evidence_id"), str)
        )
    if field == "maintenance_activity":
        try:
            _canonical_date(evidence.get("activity_on"))
        except ValueError:
            return False
        return (
            evidence.get("evidence_type") == "maintenance_record"
            and evidence.get("primary_source") is True
            and evidence.get("source_classification") in {"official_provider", "official_repository"}
        )
    if field == "python_integration" and evidence.get("evidence_type") == "integration_test":
        return (
            evidence.get("source_classification") == "probe_result"
            and evidence.get("primary_source") is False
            and evidence.get("policy_permitted") is True
            and evidence.get("credentials_sent") is False
            and evidence.get("request_method") in {"GET", "HEAD"}
        )
    if (field == "official_provider" and evidence.get("evidence_type") == "official_registry"
            and evidence.get("source_classification") == "official_registry"):
        return evidence.get("primary_source") is True
    allowed_types = {
        "api_real": {"provider_homepage", "official_documentation"},
        "official_provider": {"provider_homepage", "official_documentation", "official_registry"},
        "documentation_available": {"official_documentation", "openapi_specification"},
        "authentication": {"authentication_documentation", "official_documentation"},
        "free_tier": {"pricing_access_documentation", "terms_of_service", "official_documentation"},
        "quotas": {"quota_documentation", "pricing_access_documentation", "official_documentation", "terms_of_service"},
        "python_integration": {"endpoint_documentation", "official_documentation"},
        "license": {"license_documentation", "terms_of_service"},
    }.get(field, set())
    return (
        evidence.get("evidence_type") in allowed_types
        and evidence.get("primary_source") is True
        and evidence.get("source_classification") == "official_provider"
    )


def _verified_finding(review: Mapping[str, Any] | None, field: str) -> tuple[Mapping[str, Any] | None, list[Mapping[str, Any]]]:
    workflow = _workflow_from_review(review)
    findings = workflow.get("findings", {})
    finding = findings.get(field) if isinstance(findings, Mapping) else None
    if not isinstance(finding, Mapping) or finding.get("status") != "verified":
        return None, []
    evidence = _evidence_map(workflow)
    ids = finding.get("evidence_ids", [])
    if not isinstance(ids, list):
        return None, []
    qualifying = [
        evidence[item]
        for item in ids
        if item in evidence
        and _authoritative_evidence(evidence[item], field)
        and (
            field != "currently_accessible"
            or _probe_permission_valid(evidence.get(evidence[item].get("permission_evidence_id")))
        )
    ]
    return (finding, qualifying) if qualifying else (None, [])


def _project_usefulness(candidate: Mapping[str, Any]) -> tuple[int, list[str]]:
    text = _candidate_text(candidate)
    matches = [theme for theme, terms in _PROJECT_USE_CASES.items() if any(term in text for term in terms)]
    if len(matches) >= 3:
        return 100, [f"Matches existing project themes: {', '.join(matches)}"]
    if len(matches) == 2:
        return 88, [f"Matches existing project themes: {', '.join(matches)}"]
    if len(matches) == 1:
        return 72, [f"Matches existing project theme: {matches[0]}"]
    if candidate.get("summary") or candidate.get("listed_url"):
        return 35, ["General-purpose lead; no configured project-use theme matched"]
    return 10, ["Little project-use metadata is present"]


def _documentation_score(candidate: Mapping[str, Any], review: Mapping[str, Any] | None) -> tuple[int, list[str]]:
    finding, _ = _verified_finding(review, "documentation_available")
    if finding is not None:
        return (100 if finding.get("value") is True else 0), ["Documentation availability has primary-provider evidence"]
    if isinstance(candidate.get("documentation_url"), str) and candidate["documentation_url"].startswith("https://"):
        return 60, ["Documentation URL pointer exists; provider ownership/content not independently checked"]
    attributions = candidate.get("source_attributions", [])
    if candidate.get("endpoint_count_in_spec") or (
        isinstance(attributions, list) and any(isinstance(item, dict) and (item.get("spec_url") or item.get("openapi_version")) for item in attributions)
    ):
        return 45, ["Specification pointer exists; official provider status not independently checked"]
    if any(group.get("docs_present") is True for group in _claim_groups(candidate)):
        return 25, ["Upstream directory claims documentation exists; not independently reviewed"]
    return 0, ["No documentation pointer found in imported metadata"]


def _openapi_score(candidate: Mapping[str, Any]) -> tuple[int, list[str]]:
    attributions = candidate.get("source_attributions", [])
    has_spec_attribution = isinstance(attributions, list) and any(
        isinstance(item, dict) and (item.get("openapi_version") or item.get("spec_url")) for item in attributions
    )
    if isinstance(candidate.get("endpoint_count_in_spec"), int) and candidate["endpoint_count_in_spec"] > 0:
        return 100, ["Candidate was parsed from an OpenAPI/Swagger specification"]
    if has_spec_attribution:
        return 100, ["OpenAPI specification source attribution is present"]
    docs = str(candidate.get("documentation_url") or "").casefold()
    if any(marker in docs for marker in ("openapi", "swagger", ".yaml", ".yml", ".json")):
        return 35, ["Documentation URL resembles a spec pointer; format not confirmed"]
    return 0, ["No OpenAPI specification pointer found"]


def _free_access_score(candidate: Mapping[str, Any], review: Mapping[str, Any] | None) -> tuple[int, list[str]]:
    finding, _ = _verified_finding(review, "free_tier")
    if finding is not None:
        return 100, ["Free/paid access finding has primary-provider evidence"]
    if _claim_values(candidate, "api_atlas_access", "access", "free_status"):
        return 25, ["Upstream access/pricing claim exists; it is not treated as a verified free tier"]
    return 0, ["No access/pricing evidence is recorded"]


def _authentication_score(candidate: Mapping[str, Any], review: Mapping[str, Any] | None) -> tuple[int, list[str]]:
    finding, _ = _verified_finding(review, "authentication")
    if finding is not None:
        return 100, ["Authentication requirement has primary-provider evidence"]
    evidence = candidate.get("authentication_evidence")
    if isinstance(evidence, dict) and evidence.get("declared_by_spec") is True:
        return 55, ["Authentication scheme is declared in an imported spec; not independently verified"]
    if _claim_values(candidate, "api_atlas_auth", "authentication", "auth"):
        return 22, ["Upstream authentication claim exists; it is not treated as verified"]
    return 0, ["No authentication evidence is recorded"]


def _maintenance_score(review: Mapping[str, Any] | None, as_of: date) -> tuple[int, list[str]]:
    finding, evidence = _verified_finding(review, "maintenance_activity")
    if finding is None or not evidence:
        return 0, ["Provider/repository maintenance activity is UNKNOWN; upstream directory check dates are not maintenance evidence"]
    if finding.get("value") is False or str(finding.get("value", "")).casefold() in {"inactive", "archived", "discontinued"}:
        return 0, ["Primary evidence indicates no active maintenance"]
    activity_dates: list[date] = []
    for item in evidence:
        try:
            activity_dates.append(date.fromisoformat(_canonical_date(item.get("activity_on"))))
        except ValueError:
            continue
    if not activity_dates:
        return 0, ["Primary maintenance record is present but has no verifiable activity date"]
    latest_activity = max(activity_dates)
    if latest_activity > as_of:
        return 0, ["Maintenance activity date is after the ranking cutoff and is excluded"]
    age = (as_of - latest_activity).days
    score = 100 if age <= 30 else 80 if age <= 90 else 55 if age <= 180 else 25 if age <= 365 else 0
    return score, [f"Primary maintenance activity age: {age} day(s)"]


def _license_score(candidate: Mapping[str, Any], review: Mapping[str, Any] | None) -> tuple[int, list[str]]:
    finding, _ = _verified_finding(review, "license")
    if finding is not None:
        return 100, ["API/service or data-license finding has primary-provider evidence"]
    for value in _claim_values(candidate, "api_atlas_license", "license"):
        if isinstance(value, str) and value.strip() not in {"-", "UNKNOWN", "Unknown", "None"}:
            return 25, ["Upstream license claim exists; repository/spec terms do not automatically license API service/data"]
    return 0, ["No provider API/data-license evidence is recorded"]


def _integration_score(candidate: Mapping[str, Any], review: Mapping[str, Any] | None) -> tuple[int, list[str]]:
    finding, _ = _verified_finding(review, "python_integration")
    if finding is not None:
        return (100 if finding.get("value") in {True, "feasible"} else 0), ["Python integration feasibility was explicitly reviewed"]
    endpoints = candidate.get("endpoints", [])
    has_get = isinstance(endpoints, list) and any(
        isinstance(item, dict) and str(item.get("method", "")).upper() == "GET" for item in endpoints
    )
    base_url = candidate.get("base_url")
    if isinstance(base_url, str) and base_url.startswith("https://") and has_get:
        score, reasons = 70, ["HTTPS base URL and GET operation are present in imported spec; not live-tested"]
    elif isinstance(base_url, str) and base_url.startswith("https://"):
        score, reasons = 45, ["HTTPS base URL pointer exists but no safe read endpoint was identified"]
    elif candidate.get("documentation_url") or candidate.get("listed_url"):
        score, reasons = 30, ["Only website/documentation pointers exist; endpoint/auth are not validated"]
    else:
        score, reasons = 10, ["Integration surface is not yet described"]
    if candidate.get("possible_existing_matches") or candidate.get("possible_duplicate_flags"):
        score = max(0, score - 15)
        reasons.append("Possible duplicate/existing-catalog match lowers novelty pending review")
    return score, reasons


def _component(score: int, weight: int, reasons: Sequence[str]) -> dict[str, Any]:
    return {"score": score, "weight": weight, "weighted_points": round(weight * score / 100, 2), "reasons": list(reasons)}


def _base_components(candidate: Mapping[str, Any], review: Mapping[str, Any] | None, as_of: date) -> dict[str, dict[str, Any]]:
    scores = {
        "project_usefulness": _project_usefulness(candidate),
        "official_documentation_availability": _documentation_score(candidate, review),
        "openapi_spec_availability": _openapi_score(candidate),
        "free_access_evidence": _free_access_score(candidate, review),
        "authentication_requirements": _authentication_score(candidate, review),
        "maintenance_activity": _maintenance_score(review, as_of),
        "license_clarity": _license_score(candidate, review),
        "integration_feasibility": _integration_score(candidate, review),
    }
    return {name: _component(score, SCORING_WEIGHTS[name], reasons) for name, (score, reasons) in scores.items()}


def _diversity_score(categories: Sequence[str], selected_counts: Mapping[str, int]) -> tuple[int, list[str]]:
    count = min((selected_counts.get(category, 0) for category in categories), default=0)
    score = max(0, 100 - 25 * count)
    note = "Category not yet represented in this batch" if count == 0 else f"Least-represented category has {count} earlier selection(s)"
    return score, [note]


def rank_review_candidates(
    queue: Mapping[str, Any] | Iterable[Mapping[str, Any]],
    *,
    limit: int = 100,
    as_of: str | date | None = None,
    review_records: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Rank API leads with a transparent weighted score and marginal category diversity."""
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise ValueError("limit must be a non-negative integer")
    cutoff = date.fromisoformat(_date_text(as_of))
    if isinstance(queue, Mapping):
        if not isinstance(queue.get("candidates"), list):
            raise ValueError("review queue must contain a candidates list")
        candidates = queue["candidates"]
    else:
        candidates = list(queue)
    api_candidates = [item for item in candidates if isinstance(item, Mapping) and item.get("type") == "api_candidate"]
    unique: dict[str, Mapping[str, Any]] = {}
    for candidate in api_candidates:
        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id:
            raise ValueError("every candidate must have a candidate_id")
        if candidate_id in unique:
            raise ValueError(f"duplicate candidate_id in ranking input: {candidate_id}")
        unique[candidate_id] = candidate
    reviews = review_records or {}
    base = {
        candidate_id: _base_components(candidate, reviews.get(candidate_id), cutoff)
        for candidate_id, candidate in unique.items()
    }
    remaining = set(unique)
    selected_counts: Counter[str] = Counter()
    results: list[dict[str, Any]] = []
    while remaining and len(results) < min(limit, len(unique)):
        options: list[tuple[float, float, str, int, list[str]]] = []
        for candidate_id in remaining:
            categories = _categories(unique[candidate_id])
            diversity, diversity_reasons = _diversity_score(categories, selected_counts)
            base_score = sum(item["weighted_points"] for item in base[candidate_id].values())
            total_score = base_score + SCORING_WEIGHTS["category_diversity"] * diversity / 100
            options.append((total_score, base_score, candidate_id, diversity, diversity_reasons))
        total, base_score, candidate_id, diversity, reasons = min(
            options, key=lambda item: (-item[0], -item[1], item[2])
        )
        candidate = unique[candidate_id]
        components = copy.deepcopy(base[candidate_id])
        components["category_diversity"] = _component(diversity, SCORING_WEIGHTS["category_diversity"], reasons)
        results.append({
            "rank": len(results) + 1,
            "candidate_id": candidate_id,
            "name": str(candidate.get("name", "")),
            "priority_score": round(total, 2),
            "base_score_without_diversity": round(base_score, 2),
            "components": components,
            "categories": _categories(candidate),
            "upstream_priority_claim": candidate.get("review_priority", "not_provided"),
            "upstream_priority_note": "Source ranking claim only; not independently verified and not a score bonus.",
            "independent_verification_present": any(
                _verified_finding(reviews.get(candidate_id), field)[0] is not None for field in FINDING_STAGE
            ),
        })
        for category in _categories(candidate):
            selected_counts[category] += 1
        remaining.remove(candidate_id)
    return results


def _stable_id(prefix: str, *parts: Any) -> str:
    digest = hashlib.sha256("\0".join(str(item) for item in parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def _canonical_json_sha256(value: Any) -> str:
    content = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _initial_evidence(candidate: Mapping[str, Any], observed_on: str) -> list[dict[str, Any]]:
    pointers = candidate.get("evidence_sources", [])
    if not isinstance(pointers, list):
        return []
    evidence: list[dict[str, Any]] = []
    for pointer in pointers:
        if not isinstance(pointer, dict) or not isinstance(pointer.get("url"), str):
            continue
        title = _clean_text(pointer.get("title"), 500) or "Imported source pointer"
        level = str(pointer.get("evidence_level", "")).casefold()
        kind = "openapi_specification" if "spec" in level else "source_directory"
        checked = pointer.get("checked_on", observed_on)
        item = {
            "evidence_id": _stable_id("evidence", candidate.get("candidate_id"), pointer.get("url"), kind, checked),
            "candidate_id": candidate.get("candidate_id"),
            "url": pointer["url"],
            "evidence_type": kind,
            "observed_on": checked,
            "reviewer_status": "unreviewed",
            "confidence": 0.0,
            "notes": f"Imported pointer: {title}. Not independently accessed or reviewed in this batch.",
            "source_classification": "secondary_catalog",
            "primary_source": False,
            "reviewer": "system:triage",
        }
        evidence.append(item)
    return evidence


def _initial_findings() -> dict[str, dict[str, Any]]:
    return {
        field: {
            "status": "unknown",
            "value": "NOT_TESTED" if field == "currently_accessible" else "UNKNOWN",
            "evidence_ids": [],
            "confidence": 0.0,
            "notes": "No independent primary-source review is recorded.",
            "reviewer": None,
            "observed_on": None,
        }
        for field in _FINDING_FIELDS
    }


def _event_id(candidate_id: str, sequence: int, kind: str, actor: str, when: str) -> str:
    return _stable_id("event", candidate_id, sequence, kind, actor, when)


def _append_event(
    workflow: dict[str, Any],
    *,
    candidate_id: str,
    event_type: str,
    actor: str,
    actor_role: str,
    recorded_on: str,
    notes: str,
    evidence_ids: Sequence[str] = (),
    **details: Any,
) -> dict[str, Any]:
    log = workflow.setdefault("transition_log", [])
    event = {
        "event_id": _event_id(candidate_id, len(log) + 1, event_type, actor, recorded_on),
        "sequence": len(log) + 1,
        "previous_event_sha256": log[-1].get("event_sha256") if log else None,
        "event_type": event_type,
        "actor": actor,
        "actor_role": actor_role,
        "recorded_on": recorded_on,
        "notes": notes,
        "evidence_ids": list(evidence_ids),
        **details,
    }
    event["event_sha256"] = _canonical_json_sha256(event)
    log.append(event)
    return event


def _triage_signals(candidate: Mapping[str, Any]) -> dict[str, Any]:
    docs = candidate.get("documentation_url")
    attributions = candidate.get("source_attributions", [])
    has_spec = bool(candidate.get("endpoint_count_in_spec")) or (
        isinstance(attributions, list) and any(isinstance(item, dict) and (item.get("spec_url") or item.get("openapi_version")) for item in attributions)
    )
    return {
        "website_pointer": candidate.get("listed_url"),
        "documentation_url_pointer": docs if isinstance(docs, str) else None,
        "documentation_pointer_present": bool(docs) or bool(candidate.get("endpoint_count_in_spec")),
        "openapi_spec_pointer_present": has_spec,
        "upstream_access_claims": _claim_values(candidate, "api_atlas_access", "access", "free_status"),
        "upstream_authentication_claims": _claim_values(candidate, "api_atlas_auth", "authentication", "auth"),
        "upstream_license_claims": _claim_values(candidate, "api_atlas_license", "license"),
        "upstream_verification_claims": [
            {"verified": group.get("api_atlas_verified"), "checked": group.get("api_atlas_checked")}
            for group in _claim_groups(candidate) if "api_atlas_verified" in group
        ],
        "upstream_priority_claim": candidate.get("review_priority", "not_provided"),
        "official_source_reviewed": False,
        "accessibility_tested": False,
    }


def _review_classification(review: Mapping[str, Any]) -> dict[str, Any]:
    return classify_review_candidate(review.get("candidate", {}), review.get("workflow", {}))


def _proposal_blockers(candidate: Mapping[str, Any], classification: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    required_positive = {
        "api_real": True,
        "official_provider": "yes",
        "documentation_available": True,
        "currently_accessible": True,
    }
    for field, expected in required_positive.items():
        actual = classification.get(field)
        matches = actual is expected if isinstance(expected, bool) else actual == expected
        if not matches:
            blockers.append(field)
    for field in ("authentication", "free_status", "quota", "license", "maintenance_activity", "python_integration"):
        if _is_unknown_value(classification.get(field)):
            blockers.append(field)
    maintenance = classification.get("maintenance_activity")
    if maintenance is False or (isinstance(maintenance, str) and maintenance.casefold() in {"inactive", "archived", "discontinued"}):
        blockers.append("maintenance_activity_not_active")
    if classification.get("python_integration") in {False, "infeasible"}:
        blockers.append("python_integration_infeasible")
    if candidate.get("possible_existing_matches"):
        blockers.append("possible_existing_catalog_match")
    if candidate.get("possible_duplicate_flags"):
        blockers.append("possible_unresolved_candidate_duplicate")
    return sorted(set(blockers))


def _batch_summary(reviews: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    classifications = [_review_classification(item) for item in reviews]

    def primary_source_reviewed(review: Mapping[str, Any]) -> bool:
        workflow = review.get("workflow", {})
        if not isinstance(workflow, dict) or not isinstance(workflow.get("evidence", []), list):
            return False
        return any(
            isinstance(evidence, dict)
            and evidence.get("primary_source") is True
            and evidence.get("source_classification") in {"official_provider", "official_repository", "official_registry"}
            and evidence.get("reviewer_status") in {"supports", "contradicts", "inconclusive", "not_accessible"}
            for evidence in workflow.get("evidence", [])
        )

    result = {
        "candidates_selected": len(reviews),
        "candidates_triaged": len(reviews),
        "metadata_validated": sum(item.get("workflow", {}).get("stage_statuses", {}).get("metadata_validation") == "completed" for item in reviews),
        "candidates_with_primary_source_review": sum(primary_source_reviewed(item) for item in reviews),
        "api_existence_verified": sum(item["api_real"] is True for item in classifications),
        "api_existence_rejected": sum(item["api_real"] is False for item in classifications),
        "unknown_api_real_status": sum(item["api_real"] == "UNKNOWN" for item in classifications),
        "official_providers_identified": sum(item["official_provider"] == "yes" for item in classifications),
        "provider_identity_rejected": sum(item["official_provider"] == "no" for item in classifications),
        "unknown_provider_identity": sum(item["official_provider"] == "UNKNOWN" for item in classifications),
        "documentation_verified": sum(item["documentation_available"] is True for item in classifications),
        "documentation_unavailable_verified": sum(item["documentation_available"] is False for item in classifications),
        "unknown_documentation_status": sum(item["documentation_available"] == "UNKNOWN" for item in classifications),
        "currently_accessible_verified": sum(item["currently_accessible"] is True for item in classifications),
        "currently_not_accessible_verified": sum(item["currently_accessible"] is False for item in classifications),
        "currently_accessible_not_tested": sum(item["currently_accessible"] == "NOT_TESTED" for item in classifications),
        "authentication_requirements_verified": sum(item["authentication"] != "UNKNOWN" for item in classifications),
        "unknown_authentication_status": sum(item["authentication"] == "UNKNOWN" for item in classifications),
        "quotas_documented": sum(item["quota"] != "UNKNOWN" for item in classifications),
        "unknown_quota_status": sum(item["quota"] == "UNKNOWN" for item in classifications),
        "licenses_clarified": sum(item["license"] != "UNKNOWN" for item in classifications),
        "unknown_license_status": sum(item["license"] == "UNKNOWN" for item in classifications),
        "free_apis_independently_verified": sum(item["free_status"] in {"FREE_NO_KEY", "FREE_WITH_KEY", "FREE_TIER_LIMITED"} for item in classifications),
        "no_key_apis_independently_verified": sum(item["free_status"] == "FREE_NO_KEY" for item in classifications),
        "free_with_key_apis_independently_verified": sum(item["free_status"] == "FREE_WITH_KEY" for item in classifications),
        "limited_free_tier_apis": sum(item["free_status"] == "FREE_TIER_LIMITED" for item in classifications),
        "paid_access_independently_verified": sum(item["free_status"] == "PAID" for item in classifications),
        "unknown_free_status": sum(item["free_status"] == "UNKNOWN" for item in classifications),
        "maintenance_activity_verified": sum(item["maintenance_activity"] != "UNKNOWN" for item in classifications),
        "unknown_maintenance_activity": sum(item["maintenance_activity"] == "UNKNOWN" for item in classifications),
        "python_integration_feasibility_verified": sum(item["python_integration"] != "UNKNOWN" for item in classifications),
        "unknown_python_integration": sum(item["python_integration"] == "UNKNOWN" for item in classifications),
        "rejected_candidates": sum(item.get("workflow", {}).get("workflow_status") == "rejected" for item in reviews),
        "accepted_candidates_proposed": sum(isinstance(item.get("workflow", {}).get("proposal"), dict) for item in reviews),
        "proposals_pending_human_approval": sum(item.get("workflow", {}).get("proposal", {}).get("status") == "pending_human_approval" for item in reviews if isinstance(item.get("workflow", {}).get("proposal"), dict)),
        "human_approved_proposals": sum(item.get("workflow", {}).get("approval", {}).get("decision") == "approved" for item in reviews if isinstance(item.get("workflow", {}).get("approval"), dict)),
        "catalog_acceptance_records": sum(item.get("workflow", {}).get("workflow_status") == "catalog_acceptance_recorded" for item in reviews),
        "endpoint_probes_recorded": sum(
            sum(evidence.get("evidence_type") == "endpoint_probe" for evidence in item.get("workflow", {}).get("evidence", []))
            for item in reviews
        ),
    }
    result["primary_source_reviews_completed"] = sum(
        item.get("workflow", {}).get("stage_statuses", {}).get("official_source_identification") == "completed"
        for item in reviews
    )
    return result


def create_verification_batch(
    queue: Mapping[str, Any],
    *,
    limit: int = 100,
    generated_on: str | date | None = None,
) -> dict[str, Any]:
    """Create a ranked review batch with explicit unknown findings and audit events."""
    queue_errors = validate_review_queue(dict(queue))
    if queue_errors:
        raise ValueError(f"invalid discovery queue: {queue_errors[0]}")
    checked = _date_text(generated_on or queue.get("generated_on"))
    ranked = rank_review_candidates(queue, limit=limit, as_of=checked)
    candidates = {item["candidate_id"]: item for item in queue["candidates"] if isinstance(item, dict)}
    reviews: list[dict[str, Any]] = []
    for rank in ranked:
        candidate_id = rank["candidate_id"]
        candidate = copy.deepcopy(candidates[candidate_id])
        evidence = _initial_evidence(candidate, checked)
        statuses = {stage: "not_started" for stage in VERIFICATION_STAGES}
        statuses["candidate_discovery"] = "completed"
        statuses["metadata_validation"] = "completed"
        workflow: dict[str, Any] = {
            "current_stage": "official_source_identification",
            "current_stage_status": "not_started",
            "workflow_status": "in_review",
            "stage_statuses": statuses,
            "findings": _initial_findings(),
            "evidence": evidence,
            "transition_log": [],
            "approval": None,
            "proposal": None,
            "catalog_acceptance": None,
        }
        _append_event(
            workflow,
            candidate_id=candidate_id,
            event_type="candidate_discovery_recorded",
            actor="system:triage",
            actor_role="system",
            recorded_on=checked,
            notes="Selected by the priority model. Discovery/triage only; no provider documentation was reviewed and no endpoint was contacted.",
            evidence_ids=[item["evidence_id"] for item in evidence],
            from_stage=None,
            to_stage="candidate_discovery",
            outcome="completed",
        )
        _append_event(
            workflow,
            candidate_id=candidate_id,
            event_type="stage_transition",
            actor="system:validator",
            actor_role="system",
            recorded_on=checked,
            notes="Candidate discovery was completed and the imported queue record passed structural metadata validation. Provider identity and source claims remain unverified.",
            from_stage="candidate_discovery",
            to_stage="metadata_validation",
            outcome="completed",
        )
        _append_event(
            workflow,
            candidate_id=candidate_id,
            event_type="stage_transition",
            actor="system:validator",
            actor_role="system",
            recorded_on=checked,
            notes="Metadata validation completed from the validated source queue; independent official-source identification is the next stage.",
            from_stage="metadata_validation",
            to_stage="official_source_identification",
            outcome="completed",
        )
        reviews.append({
            "candidate_id": candidate_id,
            "rank": rank["rank"],
            "priority_score": rank["priority_score"],
            "base_score_without_diversity": rank["base_score_without_diversity"],
            "priority_components": rank["components"],
            "upstream_priority_claim": rank["upstream_priority_claim"],
            "independent_verification_present": rank["independent_verification_present"],
            "triage_signals": _triage_signals(candidate),
            "candidate": candidate,
            "workflow": workflow,
        })
    batch = {
        "schema_version": VERIFICATION_SCHEMA_VERSION,
        "batch_id": f"review-batch-{checked.replace('-', '')}-{len(reviews):03d}",
        "generated_on": checked,
        "selection_policy": {
            "limit": limit,
            "scoring_weights": dict(SCORING_WEIGHTS),
            "upstream_priority_is_claim_only": True,
            "automatic_catalog_promotion": False,
            "endpoint_probes_performed": False,
            "note": "Priority is triage, not verification. Directory claims do not set provider facts; uncertainty remains UNKNOWN.",
        },
        "source_snapshot": {
            "queue_schema_version": queue.get("schema_version"),
            "queue_generated_on": queue.get("generated_on"),
            "queue_source": copy.deepcopy(queue.get("source")),
            "queue_counts": copy.deepcopy(queue.get("counts")),
        },
        "summary": _batch_summary(reviews),
        "reviews": reviews,
    }
    errors = validate_verification_batch(batch)
    if errors:
        raise ValueError(f"generated verification batch is invalid: {errors[0]}")
    return batch


def validate_review_evidence(evidence: Any) -> list[str]:
    """Validate a credential-free evidence record and enforce safe probe metadata."""
    if not isinstance(evidence, dict):
        return ["evidence must be an object"]
    errors: list[str] = []
    for field in ("evidence_id", "candidate_id", "reviewer", "notes"):
        if not isinstance(evidence.get(field), str) or not evidence[field].strip():
            errors.append(f"evidence.{field} must be non-empty text")
    try:
        _safe_http_url(evidence.get("url"), require_https=True)
    except ValueError:
        errors.append("evidence.url must be safe HTTPS")
    if not isinstance(evidence.get("evidence_type"), str) or evidence.get("evidence_type") not in EVIDENCE_TYPES:
        errors.append("evidence.evidence_type is unsupported")
    try:
        _canonical_date(evidence.get("observed_on"))
    except ValueError:
        errors.append("evidence.observed_on must be YYYY-MM-DD")
    if not isinstance(evidence.get("reviewer_status"), str) or evidence.get("reviewer_status") not in EVIDENCE_REVIEW_STATUSES:
        errors.append("evidence.reviewer_status is unsupported")
    confidence = evidence.get("confidence")
    confidence_valid = (
        not isinstance(confidence, bool)
        and isinstance(confidence, (int, float))
        and math.isfinite(float(confidence))
        and 0 <= float(confidence) <= 1
    )
    if not confidence_valid:
        errors.append("evidence.confidence must be finite and from 0 to 1")
    elif evidence.get("reviewer_status") == "unreviewed" and float(confidence) != 0:
        errors.append("unreviewed evidence must have confidence 0")
    elif evidence.get("reviewer_status") != "unreviewed" and float(confidence) == 0:
        errors.append("reviewed evidence must have non-zero confidence")
    if not isinstance(evidence.get("source_classification"), str) or evidence.get("source_classification") not in SOURCE_CLASSIFICATIONS:
        errors.append("evidence.source_classification is unsupported")
    if not isinstance(evidence.get("primary_source"), bool):
        errors.append("evidence.primary_source must be boolean")
    if evidence.get("primary_source") is True:
        classification = evidence.get("source_classification")
        evidence_type = evidence.get("evidence_type")
        provider_types = {
            "provider_homepage", "official_registry", "official_documentation", "openapi_specification",
            "authentication_documentation", "pricing_access_documentation", "quota_documentation",
            "endpoint_documentation", "terms_of_service", "license_documentation", "maintenance_record",
        }
        allowed_primary = (
            classification == "official_provider" and evidence_type in provider_types
        ) or (
            classification == "official_registry" and evidence_type == "official_registry"
        ) or (
            classification == "official_repository" and evidence_type == "maintenance_record"
        ) or (
            classification == "probe_result" and evidence_type == "endpoint_probe"
        )
        if not allowed_primary:
            errors.append("primary evidence must be provider-controlled, an official maintenance record, or a permitted probe")
    if evidence.get("evidence_type") == "maintenance_record":
        try:
            activity_on = _canonical_date(evidence.get("activity_on"))
            observed_on = _canonical_date(evidence.get("observed_on"))
            if activity_on > observed_on:
                errors.append("maintenance activity_on cannot be after observed_on")
        except ValueError:
            errors.append("maintenance_record requires a valid activity_on date")
    if evidence.get("evidence_type") == "endpoint_documentation" and evidence.get("documented_endpoint_url") is not None:
        try:
            _safe_http_url(evidence.get("documented_endpoint_url"), require_https=True)
            endpoint_parts = urlsplit(evidence["documented_endpoint_url"])
            if endpoint_parts.query or endpoint_parts.fragment:
                errors.append("documented_endpoint_url must not include a query or fragment")
        except (KeyError, TypeError, ValueError):
            errors.append("documented_endpoint_url must be safe HTTPS without query or fragment")
        if evidence.get("documented_method") not in {"GET", "HEAD"}:
            errors.append("documented endpoint method must be GET or HEAD for a safe probe")
    if evidence.get("permits_unauthenticated_read_probes") is True and not _probe_permission_valid(evidence):
        errors.append("probe permission requires reviewed, high-confidence official provider policy evidence")
    if evidence.get("evidence_type") == "endpoint_probe":
        if evidence.get("policy_permitted") is not True:
            errors.append("endpoint_probe requires explicit provider-policy permission")
        if evidence.get("request_method") not in {"GET", "HEAD"}:
            errors.append("endpoint_probe may only record GET or HEAD")
        if evidence.get("credentials_sent") is not False:
            errors.append("endpoint_probe must record that no credentials were sent")
        if not isinstance(evidence.get("permission_evidence_id"), str) or not evidence["permission_evidence_id"]:
            errors.append("endpoint_probe requires permission_evidence_id")
        timeout = evidence.get("timeout_seconds")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < float(timeout) <= 10:
            errors.append("endpoint_probe timeout_seconds must be in (0, 10]")
        cap = evidence.get("max_response_bytes")
        if isinstance(cap, bool) or not isinstance(cap, int) or not 1 <= cap <= 262144:
            errors.append("endpoint_probe max_response_bytes must be 1..262144")
        interval = evidence.get("rate_limit_interval_seconds")
        if isinstance(interval, bool) or not isinstance(interval, (int, float)) or not _PROBE_MIN_INTERVAL_SECONDS <= float(interval) <= 60:
            errors.append("endpoint_probe rate_limit_interval_seconds must be 2..60")
        if evidence.get("retries") != 0:
            errors.append("endpoint_probe retries must be zero")
        status_code = evidence.get("status_code")
        outcome = evidence.get("probe_outcome")
        if status_code is None:
            if outcome != "network_error":
                errors.append("endpoint_probe without an HTTP status must record network_error")
        elif isinstance(status_code, bool) or not isinstance(status_code, int) or not 100 <= status_code <= 599:
            errors.append("endpoint_probe status_code must be an HTTP status code or null for network_error")
        elif outcome not in {"http_response", "http_error", "response_too_large"}:
            errors.append("endpoint_probe with an HTTP status must describe its outcome")
        response_bytes = evidence.get("response_bytes")
        if isinstance(response_bytes, bool) or not isinstance(response_bytes, int) or not 0 <= response_bytes <= (cap if isinstance(cap, int) and not isinstance(cap, bool) else 0):
            errors.append("endpoint_probe response_bytes must be within its declared cap")
        if outcome == "network_error" and response_bytes != 0:
            errors.append("network_error probe must have response_bytes=0")
        try:
            _safe_http_url(evidence.get("url"), require_https=True)
            probe_parts = urlsplit(evidence["url"])
            if probe_parts.query or probe_parts.fragment:
                errors.append("endpoint_probe URL must not include a query or fragment")
        except (KeyError, TypeError, ValueError):
            errors.append("endpoint_probe URL must be safe HTTPS")
        forbidden = {"response_body", "request_headers", "response_headers", "credential", "api_key", "token"}
        if forbidden.intersection(evidence):
            errors.append("endpoint_probe evidence must not store response bodies, headers, or credentials")
    if evidence.get("evidence_type") == "integration_test":
        if evidence.get("source_classification") == "probe_result":
            if evidence.get("primary_source") is not False or evidence.get("policy_permitted") is not True or evidence.get("credentials_sent") is not False:
                errors.append("integration_test results require permitted, credential-free direct observations")
            if evidence.get("request_method") not in {"GET", "HEAD"}:
                errors.append("integration_test may only use GET or HEAD")
    if _contains_possible_secret(evidence):
        errors.append("evidence contains a possible credential pattern")
    return errors


def _finding_has_authority(field: str, finding: Mapping[str, Any], evidence: Mapping[str, Mapping[str, Any]]) -> bool:
    ids = finding.get("evidence_ids", [])
    return isinstance(ids, list) and any(item in evidence and _authoritative_evidence(evidence[item], field) for item in ids)


def _finding_value_is_valid(field: str, value: Any) -> bool:
    if _is_unknown_value(value) or value == "NOT_TESTED":
        return False
    if field in {"api_real", "documentation_available", "currently_accessible"}:
        return isinstance(value, bool)
    if field == "official_provider":
        return isinstance(value, str) and value in {"yes", "no"}
    if field == "free_tier":
        return isinstance(value, str) and value in {"FREE_NO_KEY", "FREE_WITH_KEY", "FREE_TIER_LIMITED", "PAID"}
    if field == "authentication":
        return _authentication_is_known(value)
    if field == "python_integration":
        return isinstance(value, bool) or (isinstance(value, str) and value in {"feasible", "infeasible"})
    if field == "maintenance_activity":
        return isinstance(value, bool) or (isinstance(value, str) and bool(value.strip()))
    if field == "quotas":
        return _has_substantive_content(value)
    if field == "license":
        return (
            isinstance(value, Mapping)
            and all(isinstance(value.get(key), str) and bool(value[key].strip()) and not _is_unknown_value(value[key]) for key in ("service", "data"))
        )
    return False


def _workflow_state_from_log(workflow: Mapping[str, Any]) -> tuple[dict[str, str], str, str, str] | None:
    log = workflow.get("transition_log")
    if not isinstance(log, list) or not log:
        return None
    first = log[0]
    if (
        not isinstance(first, dict)
        or first.get("event_type") != "candidate_discovery_recorded"
        or first.get("from_stage") is not None
        or first.get("to_stage") != "candidate_discovery"
        or first.get("outcome") != "completed"
        or first.get("actor") != "system:triage"
        or first.get("actor_role") != "system"
    ):
        return None
    statuses = {stage: "not_started" for stage in VERIFICATION_STAGES}
    current = "candidate_discovery"
    current_status = "completed"
    statuses[current] = current_status
    workflow_status = "in_review"
    latest_finding_events: dict[str, Mapping[str, Any]] = {}
    evidence = _evidence_map(workflow)
    proposal_event_seen = False
    for event in log[1:]:
        if not isinstance(event, dict) or workflow_status in {"rejected", "catalog_acceptance_recorded"}:
            return None
        event_type = event.get("event_type")
        if event_type == "candidate_discovery_recorded":
            return None
        if event_type == "finding_recorded":
            field = event.get("field")
            if (field not in FINDING_STAGE or FINDING_STAGE[field] != current
                    or current_status in {"blocked", "deferred", "rejected", "completed"}):
                return None
            latest_finding_events[field] = event
            if current_status == "not_started":
                current_status = "in_progress"
                statuses[current] = current_status
            continue
        if event_type == "evidence_added":
            if current_status in {"blocked", "deferred", "rejected", "completed"}:
                return None
            continue
        if event_type == "api_record_proposal_created":
            if current != "human_approval" or current_status in {"blocked", "deferred", "rejected", "completed"} or proposal_event_seen:
                return None
            proposal_event_seen = True
            if current_status == "not_started":
                current_status = "in_progress"
                statuses[current] = current_status
            continue
        if event_type != "stage_transition":
            return None
        if event.get("from_stage") != current:
            return None
        outcome = event.get("outcome")
        target = event.get("to_stage")
        if target not in VERIFICATION_STAGES:
            return None
        if current in {"candidate_discovery", "metadata_validation"} and event.get("actor_role") != "system":
            return None
        if current not in {"human_approval", "catalog_acceptance"} and event.get("decision") is not None:
            return None
        if outcome in {"blocked", "deferred"}:
            if target != current or event.get("decision") is not None:
                return None
            current_status = outcome
            statuses[current] = outcome
            workflow_status = outcome
        elif outcome == "resumed":
            if target != current or current_status not in {"blocked", "deferred"} or event.get("decision") is not None:
                return None
            current_status = "in_progress"
            statuses[current] = "in_progress"
            workflow_status = "in_review"
        elif outcome == "rejected":
            if target != current:
                return None
            if current == "human_approval":
                if event.get("actor_role") != "human" or event.get("decision") != "rejected":
                    return None
            elif event.get("decision") is not None:
                return None
            current_status = "rejected"
            statuses[current] = "rejected"
            workflow_status = "rejected"
        elif outcome == "completed":
            if current_status in {"blocked", "deferred", "rejected"}:
                return None
            if current not in {"human_approval", "catalog_acceptance"} and event.get("decision") is not None:
                return None
            for field in _STAGE_FINDINGS.get(current, ()):
                finding_event = latest_finding_events.get(field)
                if not isinstance(finding_event, Mapping) or finding_event.get("finding_status") not in {"verified", "inconclusive"}:
                    return None
            allowed_types = _STAGE_EVIDENCE_TYPES.get(current)
            if allowed_types:
                relevant_ids = set(event.get("evidence_ids", []))
                for field in _STAGE_FINDINGS.get(current, ()):
                    finding_event = latest_finding_events.get(field)
                    if isinstance(finding_event, Mapping):
                        relevant_ids.update(finding_event.get("evidence_ids", []))
                if not any(item in evidence and evidence[item].get("evidence_type") in allowed_types for item in relevant_ids):
                    return None
            if current == "human_approval":
                proposal_id = workflow.get("proposal", {}).get("proposal_id") if isinstance(workflow.get("proposal"), dict) else None
                if event.get("decision") != "approved" or not any(
                    item.get("event_type") == "api_record_proposal_created"
                    and item.get("proposal_id") == proposal_id
                    and item.get("sequence", 0) < event.get("sequence", 0)
                    for item in log if isinstance(item, dict)
                ):
                    return None
            if current == "catalog_acceptance":
                if event.get("decision") != "accepted" or not any(
                    item.get("event_type") == "stage_transition"
                    and item.get("from_stage") == "human_approval"
                    and item.get("decision") == "approved"
                    and item.get("sequence", 0) < event.get("sequence", 0)
                    for item in log if isinstance(item, dict)
                ):
                    return None
            statuses[current] = "completed"
            if current == "catalog_acceptance":
                if target != current or event.get("actor_role") != "human" or event.get("decision") != "accepted":
                    return None
                current_status = "completed"
                workflow_status = "catalog_acceptance_recorded"
            elif current == "human_approval":
                if target != "catalog_acceptance" or event.get("actor_role") != "human" or event.get("decision") != "approved":
                    return None
                current = target
                current_status = "not_started"
                statuses[current] = current_status
                workflow_status = "approved_pending_catalog"
            else:
                expected = VERIFICATION_STAGES[VERIFICATION_STAGES.index(current) + 1]
                if target != expected:
                    return None
                current = target
                current_status = "not_started"
                statuses[current] = current_status
                workflow_status = "in_review"
        else:
            return None
    for event in log:
        if isinstance(event, dict) and event.get("event_type") == "finding_recorded":
            field = event.get("field")
            if field in FINDING_STAGE and FINDING_STAGE[field] == current and current_status == "not_started":
                current_status = "in_progress"
                statuses[current] = "in_progress"
    return statuses, current, current_status, workflow_status


def validate_verification_batch(batch: Any) -> list[str]:
    """Return schema, provenance, evidence, and state-machine validation errors."""
    if not isinstance(batch, dict):
        return ["verification batch must be an object"]
    if batch.get("schema_version") != VERIFICATION_SCHEMA_VERSION:
        return ["unsupported verification batch schema_version"]
    if not isinstance(batch.get("batch_id"), str) or not batch["batch_id"].strip():
        return ["batch_id must be non-empty text"]
    try:
        _canonical_date(batch.get("generated_on"))
    except ValueError:
        return ["generated_on must be YYYY-MM-DD"]
    policy = batch.get("selection_policy")
    if not isinstance(policy, dict) or policy.get("automatic_catalog_promotion") is not False or policy.get("upstream_priority_is_claim_only") is not True:
        return ["policy must preserve upstream claims and disable automatic catalog promotion"]
    if policy.get("scoring_weights") != SCORING_WEIGHTS:
        return ["selection_policy scoring_weights do not match this engine version"]
    limit = policy.get("limit")
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        return ["selection_policy.limit must be a non-negative integer"]
    reviews = batch.get("reviews")
    summary = batch.get("summary")
    if not isinstance(reviews, list) or not isinstance(summary, dict):
        return ["verification batch requires reviews and summary"]
    if len(reviews) > limit:
        return ["batch contains more reviews than selection_policy.limit"]
    ids: set[str] = set()
    for index, review in enumerate(reviews):
        label = f"reviews[{index}]"
        if not isinstance(review, dict):
            return [f"{label} must be an object"]
        candidate_id = review.get("candidate_id")
        candidate = review.get("candidate")
        if not isinstance(candidate_id, str) or not candidate_id or candidate_id in ids:
            return [f"{label} requires a unique candidate_id"]
        ids.add(candidate_id)
        if not isinstance(candidate, dict) or candidate.get("candidate_id") != candidate_id or candidate.get("type") != "api_candidate":
            return [f"{label} candidate payload does not match candidate_id/type"]
        if candidate.get("free_status") != "UNKNOWN" or candidate.get("license") != "UNKNOWN":
            return [f"{label} source access/license fields must remain UNKNOWN"]
        auth = candidate.get("authentication")
        if not isinstance(auth, dict) or auth.get("kind") != "unknown" or auth.get("verified") is not False:
            return [f"{label} source authentication must remain unverified"]
        if any(candidate.get(field) != "UNKNOWN" for field in ("quota", "rate_limits")):
            return [f"{label} source quota/rate-limit fields must remain UNKNOWN"]
        rank = review.get("rank")
        if isinstance(rank, bool) or not isinstance(rank, int) or rank != index + 1:
            return [f"{label} rank must be contiguous and match review order"]
        score = review.get("priority_score")
        base_score = review.get("base_score_without_diversity")
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) for value in (score, base_score)) or not 0 <= float(score) <= 100 or not 0 <= float(base_score) <= 100:
            return [f"{label} priority scores must be finite and in 0..100"]
        if review.get("upstream_priority_claim") != candidate.get("review_priority", "not_provided"):
            return [f"{label} upstream priority claim was overwritten"]
        components = review.get("priority_components")
        if not isinstance(components, dict) or set(components) != set(SCORING_WEIGHTS):
            return [f"{label} priority_components do not match the scoring model"]
        component_sum = 0.0
        base_sum = 0.0
        for component_name, weight in SCORING_WEIGHTS.items():
            component = components.get(component_name)
            if not isinstance(component, dict) or component.get("weight") != weight:
                return [f"{label} component {component_name} has an invalid weight"]
            component_score = component.get("score")
            points = component.get("weighted_points")
            if isinstance(component_score, bool) or not isinstance(component_score, int) or not 0 <= component_score <= 100:
                return [f"{label} component {component_name} has an invalid score"]
            expected_points = round(weight * component_score / 100, 2)
            if points != expected_points or not isinstance(component.get("reasons"), list):
                return [f"{label} component {component_name} has invalid points/reasons"]
            component_sum += expected_points
            if component_name != "category_diversity":
                base_sum += expected_points
        if round(component_sum, 2) != round(float(score), 2) or round(base_sum, 2) != round(float(base_score), 2):
            return [f"{label} priority total does not match its components"]
        if review.get("independent_verification_present") is not False:
            return [f"{label} ranking metadata must not label imported source claims as independent verification"]
        workflow = review.get("workflow")
        if not isinstance(workflow, dict) or workflow.get("current_stage") not in VERIFICATION_STAGES:
            return [f"{label} workflow/current_stage is invalid"]
        if not isinstance(workflow.get("workflow_status"), str) or workflow.get("workflow_status") not in {"in_review", "blocked", "deferred", "rejected", "approved_pending_catalog", "catalog_acceptance_recorded"}:
            return [f"{label} workflow_status is invalid"]
        stage_statuses = workflow.get("stage_statuses")
        if not isinstance(stage_statuses, dict) or set(stage_statuses) != set(VERIFICATION_STAGES):
            return [f"{label} stage_statuses must contain every workflow stage"]
        if any(not isinstance(value, str) or value not in {"not_started", "completed", "blocked", "deferred", "rejected", "in_progress"} for value in stage_statuses.values()):
            return [f"{label} stage_statuses contains an invalid status"]
        findings = workflow.get("findings")
        if not isinstance(findings, dict) or set(findings) != set(_FINDING_FIELDS):
            return [f"{label} findings do not match the workflow schema"]
        evidence_list = workflow.get("evidence")
        if not isinstance(evidence_list, list):
            return [f"{label} evidence must be a list"]
        evidence_ids: set[str] = set()
        for evidence_index, evidence_item in enumerate(evidence_list):
            evidence_errors = validate_review_evidence(evidence_item)
            if evidence_errors:
                return [f"{label} evidence[{evidence_index}]: {evidence_errors[0]}"]
            evidence_id = evidence_item["evidence_id"]
            if evidence_id in evidence_ids or evidence_item.get("candidate_id") != candidate_id:
                return [f"{label} evidence IDs must be unique and scoped to the candidate"]
            evidence_ids.add(evidence_id)
        evidence = _evidence_map(workflow)
        for evidence_item in evidence_list:
            if evidence_item.get("evidence_type") == "endpoint_probe":
                permission = evidence.get(evidence_item.get("permission_evidence_id"))
                if not _probe_permission_valid(permission):
                    return [f"{label} endpoint probe lacks reviewed official policy permission"]
                documented = [
                    item for item in evidence_list
                    if item.get("evidence_type") == "endpoint_documentation"
                    and item.get("primary_source") is True
                    and item.get("source_classification") == "official_provider"
                    and item.get("reviewer_status") == "supports"
                    and item.get("documented_endpoint_url") == evidence_item.get("url")
                    and item.get("documented_method") == evidence_item.get("request_method")
                    and _confidence_is_authoritative(item)
                ]
                if not documented:
                    return [f"{label} endpoint probe lacks matching official endpoint documentation"]
        for field, finding in findings.items():
            if not isinstance(finding, dict) or not isinstance(finding.get("status"), str) or finding.get("status") not in FINDING_STATUSES:
                return [f"{label} finding {field} is invalid"]
            value = finding.get("value")
            refs = finding.get("evidence_ids")
            if (not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs)
                    or len(refs) != len(set(refs)) or any(ref not in evidence_ids for ref in refs)):
                return [f"{label} finding {field} references invalid evidence"]
            confidence = finding.get("confidence")
            if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(float(confidence)) or not 0 <= float(confidence) <= 1:
                return [f"{label} finding {field} confidence is invalid"]
            if not isinstance(finding.get("notes"), str) or not finding["notes"].strip():
                return [f"{label} finding {field} notes are required"]
            if finding.get("status") == "unknown":
                if value not in ("UNKNOWN", "NOT_TESTED"):
                    return [f"{label} unknown finding {field} must keep an UNKNOWN/NOT_TESTED value"]
                if finding.get("reviewer") is not None and (not isinstance(finding.get("reviewer"), str) or not finding["reviewer"].strip()):
                    return [f"{label} unknown finding {field} reviewer is invalid"]
                if finding.get("observed_on") is not None:
                    try:
                        _canonical_date(finding.get("observed_on"))
                    except ValueError:
                        return [f"{label} unknown finding {field} date is invalid"]
            else:
                if not isinstance(finding.get("reviewer"), str) or not finding["reviewer"].strip():
                    return [f"{label} reviewed finding {field} requires a reviewer"]
                try:
                    _canonical_date(finding.get("observed_on"))
                except ValueError:
                    return [f"{label} reviewed finding {field} requires YYYY-MM-DD observed_on"]
                if finding.get("status") == "inconclusive":
                    if value not in ("UNKNOWN", "NOT_TESTED") or not refs:
                        return [f"{label} inconclusive finding {field} needs evidence and an UNKNOWN/NOT_TESTED value"]
                elif not _finding_value_is_valid(field, value):
                    return [f"{label} verified finding {field} has an invalid value"]
                if finding.get("status") == "verified":
                    qualifying = [evidence[item] for item in refs if item in evidence and _authoritative_evidence(evidence[item], field)]
                    if field == "currently_accessible":
                        qualifying = [item for item in qualifying if _probe_permission_valid(evidence.get(item.get("permission_evidence_id")))]
                    if not qualifying:
                        return [f"{label} verified finding {field} lacks qualifying authoritative evidence"]
                    if float(confidence) > max(float(item["confidence"]) for item in qualifying):
                        return [f"{label} finding {field} confidence exceeds its authoritative evidence"]
            if _contains_possible_secret(finding):
                return [f"{label} finding {field} contains a possible credential pattern"]
        log = workflow.get("transition_log")
        if not isinstance(log, list) or not log:
            return [f"{label} transition_log must contain a discovery event"]
        if (any(not isinstance(event, dict) or isinstance(event.get("sequence"), bool) or not isinstance(event.get("sequence"), int) for event in log)
                or [event.get("sequence") for event in log] != list(range(1, len(log) + 1))):
            return [f"{label} transition_log sequence is not contiguous"]
        event_ids: set[str] = set()
        latest_findings: dict[str, Mapping[str, Any]] = {}
        previous_event_date: str | None = None
        previous_event_digest: str | None = None
        for event in log:
            if not isinstance(event, dict):
                return [f"{label} transition event must be an object"]
            event_id = event.get("event_id")
            if not isinstance(event_id, str) or not event_id or event_id in event_ids:
                return [f"{label} transition event IDs must be unique text"]
            event_ids.add(event_id)
            event_digest = event.get("event_sha256")
            if (not isinstance(event_digest, str) or len(event_digest) != 64
                    or any(char not in "0123456789abcdef" for char in event_digest)
                    or event.get("previous_event_sha256") != previous_event_digest):
                return [f"{label} transition event hash chain is invalid"]
            unsigned_event = {key: value for key, value in event.items() if key != "event_sha256"}
            try:
                expected_event_digest = _canonical_json_sha256(unsigned_event)
            except (TypeError, ValueError):
                return [f"{label} transition event is not canonical JSON"]
            if event_digest != expected_event_digest:
                return [f"{label} transition event hash does not match its contents"]
            previous_event_digest = event_digest
            event_type = event.get("event_type")
            if not isinstance(event_type, str) or event_type not in {"candidate_discovery_recorded", "stage_transition", "evidence_added", "finding_recorded", "api_record_proposal_created"}:
                return [f"{label} transition event type is invalid"]
            if not isinstance(event.get("actor"), str) or not event["actor"].strip() or not isinstance(event.get("notes"), str) or not event["notes"].strip():
                return [f"{label} transition event is incomplete"]
            if not isinstance(event.get("actor_role"), str) or event.get("actor_role") not in {"system", "reviewer", "human"}:
                return [f"{label} transition event actor_role is invalid"]
            if event_id != _event_id(candidate_id, event["sequence"], event_type, event["actor"], event.get("recorded_on")):
                return [f"{label} transition event ID does not match its event data"]
            try:
                event_date = _canonical_date(event.get("recorded_on"))
            except ValueError:
                return [f"{label} transition event has an invalid date"]
            if previous_event_date is not None and event_date < previous_event_date:
                return [f"{label} transition event dates must be chronological"]
            previous_event_date = event_date
            event_refs = event.get("evidence_ids", [])
            if not isinstance(event_refs, list) or any(not isinstance(item, str) or item not in evidence_ids for item in event_refs):
                return [f"{label} transition event references unknown evidence"]
            if len(event_refs) != len(set(event_refs)):
                return [f"{label} transition event evidence IDs must be unique"]
            if any(evidence[item].get("observed_on", "") > event_date for item in event_refs):
                return [f"{label} transition event predates its cited evidence"]
            if event.get("event_type") == "finding_recorded":
                field = event.get("field")
                finding_status = event.get("finding_status")
                event_confidence = event.get("confidence")
                if (not isinstance(field, str) or field not in FINDING_STAGE
                        or not isinstance(finding_status, str) or finding_status not in FINDING_STATUSES
                        or "value" not in event
                        or isinstance(event_confidence, bool) or not isinstance(event_confidence, (int, float))
                        or not math.isfinite(float(event_confidence)) or not 0 <= float(event_confidence) <= 1):
                    return [f"{label} finding event is incomplete"]
                event_value = event.get("value")
                if finding_status == "verified":
                    if not _finding_value_is_valid(field, event_value) or event_confidence == 0:
                        return [f"{label} verified finding event has an invalid value/confidence"]
                    qualifying = [evidence[item] for item in event_refs if _authoritative_evidence(evidence[item], field)]
                    if field == "currently_accessible":
                        qualifying = [item for item in qualifying if _probe_permission_valid(evidence.get(item.get("permission_evidence_id")))]
                    if (not qualifying or float(event_confidence) > max(float(item["confidence"]) for item in qualifying)):
                        return [f"{label} verified finding event lacks suitable authoritative evidence"]
                elif finding_status == "inconclusive":
                    if event_value not in ("UNKNOWN", "NOT_TESTED") or not event_refs:
                        return [f"{label} inconclusive finding event is invalid"]
                elif event_value not in ("UNKNOWN", "NOT_TESTED"):
                    return [f"{label} unknown finding event is invalid"]
                latest_findings[field] = event
            elif event_type == "evidence_added" and (len(event_refs) != 1 or event_refs[0] not in evidence_ids):
                return [f"{label} evidence_added event must reference one evidence record"]
        state = _workflow_state_from_log(workflow)
        if state is None:
            return [f"{label} transition history is invalid or skips/reorders stages"]
        derived_statuses, derived_current, derived_current_status, derived_workflow_status = state
        if (derived_statuses != stage_statuses or derived_current != workflow.get("current_stage")
                or derived_current_status != workflow.get("current_stage_status")
                or derived_workflow_status != workflow.get("workflow_status")):
            return [f"{label} workflow state does not match its transition history"]
        for field, finding in findings.items():
            last_event = latest_findings.get(field)
            if finding.get("status") != "unknown" and last_event is None:
                return [f"{label} finding {field} has no audit event"]
            if last_event is not None and (
                finding.get("status") != last_event.get("finding_status")
                or finding.get("value") != last_event.get("value")
                or finding.get("evidence_ids") != last_event.get("evidence_ids")
                or finding.get("confidence") != last_event.get("confidence")
                or finding.get("reviewer") != last_event.get("actor")
                or finding.get("observed_on") != last_event.get("recorded_on")
            ):
                return [f"{label} current finding {field} does not match its last audit event"]
        initial_evidence_ids = set(log[0].get("evidence_ids", []))
        triage_evidence_ids = {item["evidence_id"] for item in evidence_list if item.get("reviewer") == "system:triage"}
        if initial_evidence_ids != triage_evidence_ids:
            return [f"{label} discovery event does not match imported evidence pointers"]
        for evidence_item in evidence_list:
            matching_events = [
                event for event in log
                if event.get("event_type") == "evidence_added" and evidence_item["evidence_id"] in event.get("evidence_ids", [])
            ]
            if evidence_item["evidence_id"] in initial_evidence_ids:
                if (evidence_item.get("reviewer_status") != "unreviewed" or evidence_item.get("confidence") != 0
                        or evidence_item.get("primary_source") is not False):
                    return [f"{label} imported evidence pointer was silently converted into a reviewed source"]
            elif (len(matching_events) != 1 or matching_events[0].get("actor") != evidence_item.get("reviewer")
                    or evidence_item.get("observed_on") > matching_events[0].get("recorded_on")):
                return [f"{label} evidence item is missing its append-only evidence_added event"]
        proposal = workflow.get("proposal")
        approval = workflow.get("approval")
        acceptance = workflow.get("catalog_acceptance")
        proposal_events = [event for event in log if event.get("event_type") == "api_record_proposal_created"]
        if proposal is None and proposal_events:
            return [f"{label} proposal event exists without a proposal record"]
        if proposal is not None:
            if not isinstance(proposal, dict) or proposal.get("candidate_id") != candidate_id:
                return [f"{label} proposal is invalid or for another candidate"]
            if not isinstance(proposal.get("status"), str) or proposal.get("status") not in {"pending_human_approval", "human_approved", "human_rejected", "catalog_accepted"}:
                return [f"{label} proposal status is invalid"]
            if not isinstance(proposal.get("proposal_id"), str) or not proposal["proposal_id"].strip():
                return [f"{label} proposal_id must be non-empty text"]
            if proposal.get("source_attributions") != candidate.get("source_attributions", []):
                return [f"{label} proposal lost original source attribution"]
            if proposal.get("source_claims_by_source") != candidate.get("source_claims_by_source", []):
                return [f"{label} proposal overwrote upstream source claims"]
            if proposal.get("source_claims") != candidate.get("source_claims", {}):
                return [f"{label} proposal overwrote upstream source claims"]
            try:
                _canonical_date(proposal.get("created_on"))
            except ValueError:
                return [f"{label} proposal created_on is invalid"]
            if not isinstance(proposal.get("created_by"), str) or not proposal["created_by"].strip():
                return [f"{label} proposal creator is missing"]
            record = proposal.get("api_record")
            if not isinstance(record, dict):
                return [f"{label} proposal api_record is missing"]
            errors = validate_catalog_data({"schema_version": "1.0", "last_updated": proposal.get("created_on"), "records": [record]}, "apis")
            if errors:
                return [f"{label} proposal API record is invalid: {errors[0]}"]
            try:
                record_digest = _canonical_json_sha256(record)
            except (TypeError, ValueError):
                return [f"{label} proposal API record is not canonical JSON"]
            if proposal.get("api_record_sha256") != record_digest:
                return [f"{label} proposal API record changed after the proposal event"]
            matching_proposal_events = [event for event in proposal_events if event.get("proposal_id") == proposal.get("proposal_id")]
            if (len(proposal_events) != 1 or len(matching_proposal_events) != 1
                    or matching_proposal_events[0].get("api_record_sha256") != record_digest
                    or matching_proposal_events[0].get("evidence_ids") != proposal.get("verified_evidence_ids")
                    or matching_proposal_events[0].get("actor") != proposal.get("created_by")
                    or matching_proposal_events[0].get("recorded_on") != proposal.get("created_on")
                    or matching_proposal_events[0].get("actor_role") != "reviewer"):
                return [f"{label} proposal is not supported by one matching audit event"]
            proposal_event_index = log.index(proposal_events[0])
            if proposal.get("verification_history") != log[: proposal_event_index + 1]:
                return [f"{label} proposal does not preserve its verification history"]
            verified_ids = sorted({
                evidence_item["evidence_id"]
                for finding in findings.values() if finding.get("status") == "verified"
                for evidence_item in evidence_list if evidence_item.get("evidence_id") in finding.get("evidence_ids", [])
            })
            if proposal.get("verified_evidence_ids") != verified_ids:
                return [f"{label} proposal verified_evidence_ids do not match its findings"]
            classification = _review_classification(review)
            blockers = _proposal_blockers(candidate, classification)
            if blockers:
                return [f"{label} proposal exists without required verified facts: {', '.join(blockers)}"]
            if record.get("free_status") != classification["free_status"] or record.get("quota") != classification["quota"] or record.get("license") != classification["license"]:
                return [f"{label} proposal changed verified access, quota, or license information"]
            record_auth = record.get("authentication")
            if not isinstance(record_auth, dict) or not _authentication_record_matches(classification.get("authentication"), record_auth):
                return [f"{label} proposal contradicts or omits verified authentication information"]
            record_source_urls = {source.get("url") for source in record.get("sources", []) if isinstance(source, dict)}
            required_source_urls = {evidence[item].get("url") for item in verified_ids if item in evidence}
            if not required_source_urls.issubset(record_source_urls):
                return [f"{label} proposal omitted one or more sources used for verified facts"]
            if approval is None and proposal.get("status") != "pending_human_approval":
                return [f"{label} proposal status claims a decision without human approval"]
            if isinstance(approval, dict):
                expected_status = {"approved": "human_approved", "rejected": "human_rejected"}.get(approval.get("decision"))
                if proposal.get("status") != expected_status and proposal.get("status") != "catalog_accepted":
                    return [f"{label} proposal status does not match its human decision"]
            if proposal.get("status") == "catalog_accepted" and acceptance is None:
                return [f"{label} catalog_accepted proposal lacks an acceptance record"]
            if proposal.get("status") == "human_approved" and acceptance is not None:
                return [f"{label} acceptance record requires catalog_accepted proposal state"]
        approval_events = [
            event for event in log
            if event.get("event_type") == "stage_transition"
            and event.get("from_stage") == "human_approval"
            and event.get("decision") in {"approved", "rejected"}
        ]
        if approval is None and approval_events:
            return [f"{label} human decision event exists without an approval record"]
        if approval is not None:
            if not isinstance(approval, dict) or approval.get("decision") not in {"approved", "rejected"} or not isinstance(approval.get("reviewer"), str) or not approval["reviewer"].strip():
                return [f"{label} human approval record is invalid"]
            try:
                _canonical_date(approval.get("reviewed_on"))
            except ValueError:
                return [f"{label} human approval date is invalid"]
            matching_approval_events = [event for event in approval_events if event.get("decision") == approval.get("decision")]
            expected_outcome = "completed" if approval.get("decision") == "approved" else "rejected"
            if (len(approval_events) != 1 or len(matching_approval_events) != 1
                    or matching_approval_events[0].get("actor_role") != "human"
                    or matching_approval_events[0].get("actor") != approval.get("reviewer")
                    or matching_approval_events[0].get("recorded_on") != approval.get("reviewed_on")
                    or matching_approval_events[0].get("outcome") != expected_outcome):
                return [f"{label} human approval does not match its audit event"]
            if approval.get("decision") == "approved" and proposal is None:
                return [f"{label} human approval is missing its API proposal"]
        acceptance_events = [
            event for event in log
            if event.get("event_type") == "stage_transition"
            and event.get("from_stage") == "catalog_acceptance"
            and event.get("decision") == "accepted"
        ]
        if acceptance is None and acceptance_events:
            return [f"{label} catalog acceptance event exists without an acceptance record"]
        if acceptance is not None:
            if not isinstance(acceptance, dict) or not isinstance(acceptance.get("catalog_entry_id"), str) or not acceptance["catalog_entry_id"].strip():
                return [f"{label} catalog acceptance record is invalid"]
            digest = acceptance.get("catalog_entry_sha256")
            if not isinstance(digest, str) or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                return [f"{label} catalog acceptance digest is invalid"]
            matching_acceptance_events = [
                event for event in acceptance_events
                if event.get("catalog_entry_id") == acceptance.get("catalog_entry_id")
                and event.get("catalog_entry_sha256") == digest
            ]
            if (acceptance.get("catalog_file_modified_by_this_command") is not False
                    or not isinstance(approval, dict) or approval.get("decision") != "approved"
                    or proposal is None or proposal.get("status") != "catalog_accepted"
                    or acceptance.get("catalog_entry_id") != proposal["api_record"].get("id")
                    or digest != proposal.get("api_record_sha256")
                    or not isinstance(acceptance.get("recorded_by"), str) or not acceptance["recorded_by"].strip()
                    or not isinstance(acceptance.get("recorded_on"), str)
                    or len(acceptance_events) != 1 or len(matching_acceptance_events) != 1
                    or matching_acceptance_events[0].get("actor_role") != "human"
                    or matching_acceptance_events[0].get("actor") != acceptance.get("recorded_by")
                    or matching_acceptance_events[0].get("recorded_on") != acceptance.get("recorded_on")
                    or matching_acceptance_events[0].get("outcome") != "completed"):
                return [f"{label} catalog acceptance must match the human-approved record and audit event without mutating catalog files"]
            try:
                _canonical_date(acceptance.get("recorded_on"))
            except ValueError:
                return [f"{label} catalog acceptance date is invalid"]
        if workflow.get("workflow_status") == "catalog_acceptance_recorded" and acceptance is None:
            return [f"{label} catalog acceptance state lacks an acceptance record"]
        if workflow.get("workflow_status") == "approved_pending_catalog" and (not isinstance(approval, dict) or approval.get("decision") != "approved"):
            return [f"{label} approved_pending_catalog state lacks human approval"]
    try:
        reproducible_ranking = rank_review_candidates(
            [review["candidate"] for review in reviews],
            limit=len(reviews),
            as_of=batch["generated_on"],
        )
    except (TypeError, ValueError):
        return ["selected candidates cannot be ranked reproducibly"]
    for index, (review, expected) in enumerate(zip(reviews, reproducible_ranking, strict=True)):
        if (review.get("candidate_id") != expected["candidate_id"]
                or review.get("priority_score") != expected["priority_score"]
                or review.get("base_score_without_diversity") != expected["base_score_without_diversity"]
                or review.get("priority_components") != expected["components"]
                or review.get("upstream_priority_claim") != expected["upstream_priority_claim"]):
            return [f"reviews[{index}] ranking is not reproducible from the candidate and saved model"]
    if summary != _batch_summary(reviews):
        return ["summary does not match the current review findings"]
    if _contains_possible_secret(batch):
        return ["verification batch contains a possible credential pattern"]
    return []


def _has_substantive_content(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().casefold() not in {"", "unknown", "not tested", "not_tested", "not established"}
    if value is None or isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    if isinstance(value, Mapping):
        return any(_has_substantive_content(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_has_substantive_content(item) for item in value)
    return False


def _is_unknown_value(value: Any) -> bool:
    return (
        value is None
        or isinstance(value, Mapping) and not _has_substantive_content(value)
        or isinstance(value, str) and value.strip().casefold() in {"", "unknown", "not tested", "not_tested", "not established"}
    )


def _authentication_is_known(value: Any) -> bool:
    if isinstance(value, str):
        return not _is_unknown_value(value)
    if isinstance(value, Mapping):
        kind = value.get("kind")
        required = value.get("required")
        if kind == "no_auth":
            kind = "none"
        if not isinstance(kind, str) or kind not in _AUTH_RECORD_KINDS or not isinstance(required, bool):
            return False
        if kind in {"none", "optional_bearer", "optional_api_key_header"} and required:
            return False
        return True
    return False


def _authentication_is_no_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        kind = value.get("kind")
        if not isinstance(kind, str):
            return False
        if kind in {"none", "no_auth"}:
            return value.get("required") is not True
        if kind in {"api_key_header", "optional_api_key_header", "api_key_query", "bearer", "optional_bearer", "http_basic_pair"}:
            return value.get("required") is False
        return False
    if not isinstance(value, str):
        return False
    normalized = " ".join(value.casefold().replace("_", " ").replace("-", " ").split())
    if normalized in {
        "none", "no auth", "no authentication", "no api key", "no key", "no credentials",
        "none required", "not required", "unauthenticated", "public access",
    }:
        return True
    return (
        "optional" in normalized and any(term in normalized for term in ("api key", "key", "authentication", "auth"))
    ) or any(phrase in normalized for phrase in (
        "api key not required", "no api key required", "key not required", "without an api key",
        "without api key", "no authentication required", "no credentials required",
    ))


def _authentication_requires_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        kind = value.get("kind")
        return isinstance(kind, str) and kind in {
            "api_key_header", "optional_api_key_header", "api_key_query", "bearer", "optional_bearer", "http_basic_pair",
        } and value.get("required") is True
    if not isinstance(value, str):
        return False
    normalized = " ".join(value.casefold().replace("_", " ").replace("-", " ").split())
    if "optional" in normalized:
        return False
    return any(phrase in normalized for phrase in (
        "api key required", "requires api key", "key required", "requires a key",
        "access token required", "bearer token required", "oauth required",
        "authentication required", "credentials required",
    ))


def _authentication_record_matches(value: Any, record_auth: Mapping[str, Any]) -> bool:
    kind = record_auth.get("kind")
    required = record_auth.get("required")
    if (not isinstance(kind, str) or kind not in _AUTH_RECORD_KINDS or not isinstance(required, bool)
            or record_auth.get("verified") is not True):
        return False
    if isinstance(value, Mapping):
        expected_kind = value.get("kind")
        if expected_kind == "no_auth":
            expected_kind = "none"
        expected_required = value.get("required")
        if not _authentication_is_known(value) or (kind, required) != (expected_kind, expected_required):
            return False
        for detail in ("env_var", "header", "parameter", "username_env", "password_env"):
            if detail in value and record_auth.get(detail) != value[detail]:
                return False
        return True
    if not isinstance(value, str):
        return False
    normalized = " ".join(value.casefold().replace("_", " ").replace("-", " ").split())
    if _authentication_is_no_key(value):
        optional = "optional" in normalized
        if not optional:
            return kind == "none" and required is False
        if "bearer" in normalized or "token" in normalized:
            return kind == "optional_bearer" and required is False
        if "query" in normalized and "api key" in normalized:
            return kind == "api_key_query" and required is False
        if "header" in normalized and "api key" in normalized:
            return kind == "optional_api_key_header" and required is False
        if "bearer" in normalized or "bearer token" in normalized:
            return kind == "optional_bearer" and required is False
        return False
    if _authentication_requires_key(value):
        if "basic" in normalized:
            return kind == "http_basic_pair" and required is True
        if "query" in normalized and "api key" in normalized:
            return kind == "api_key_query" and required is True
        if "header" in normalized and "api key" in normalized:
            return kind == "api_key_header" and required is True
        if "bearer" in normalized:
            return kind == "bearer" and required is True
        return False
    return False


def classify_review_candidate(candidate: Mapping[str, Any], review_or_workflow: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Classify only reviewed facts with suitable primary evidence; otherwise UNKNOWN."""
    workflow = _workflow_from_review(review_or_workflow)

    def verified_value(field: str, fallback: Any = "UNKNOWN") -> Any:
        finding, _ = _verified_finding(workflow, field)
        return finding.get("value", fallback) if finding is not None else fallback

    api_real = verified_value("api_real")
    provider = verified_value("official_provider")
    docs = verified_value("documentation_available")
    accessible = verified_value("currently_accessible", "NOT_TESTED")
    auth = verified_value("authentication")
    tier = verified_value("free_tier")
    quota = verified_value("quotas")
    license = verified_value("license")
    integration = verified_value("python_integration")
    maintenance = verified_value("maintenance_activity")
    auth_known = _authentication_is_known(auth)
    if tier == "FREE_NO_KEY" and (not auth_known or not _authentication_is_no_key(auth)):
        tier = "UNKNOWN"
    if tier == "FREE_WITH_KEY" and (not auth_known or not _authentication_requires_key(auth)):
        tier = "UNKNOWN"
    if not isinstance(tier, str) or tier not in {"FREE_NO_KEY", "FREE_WITH_KEY", "FREE_TIER_LIMITED", "PAID"}:
        tier = "UNKNOWN"
    integration_known = isinstance(integration, bool) or (isinstance(integration, str) and integration in {"feasible", "infeasible"})
    return {
        "api_real": api_real if isinstance(api_real, bool) else "UNKNOWN",
        "official_provider": provider if isinstance(provider, str) and provider in {"yes", "no"} else "UNKNOWN",
        "documentation_available": docs if isinstance(docs, bool) else "UNKNOWN",
        "currently_accessible": accessible if isinstance(accessible, bool) else "NOT_TESTED",
        "authentication": copy.deepcopy(auth) if auth_known else "UNKNOWN",
        "free_status": tier,
        "quota": copy.deepcopy(quota) if not _is_unknown_value(quota) else "UNKNOWN",
        "license": copy.deepcopy(license) if not _is_unknown_value(license) else "UNKNOWN",
        "maintenance_activity": copy.deepcopy(maintenance) if not _is_unknown_value(maintenance) else "UNKNOWN",
        "python_integration": integration if integration_known else "UNKNOWN",
        "source_claims_used_as_facts": False,
    }


def _refresh_summary(batch: dict[str, Any]) -> None:
    batch["summary"] = _batch_summary(batch.get("reviews", []))


def _find_review(batch: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    for review in batch.get("reviews", []):
        if isinstance(review, dict) and review.get("candidate_id") == candidate_id:
            return review
    raise ValueError(f"candidate is not in this verification batch: {candidate_id}")


def create_review_evidence(
    candidate_id: str,
    *,
    url: str,
    evidence_type: str,
    observed_on: str | date,
    reviewer_status: str,
    confidence: float,
    notes: str,
    source_classification: str,
    primary_source: bool,
    reviewer: str,
    evidence_id: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Build one validated evidence object; it does not fetch the URL."""
    observed = _date_text(observed_on)
    result = {
        "evidence_id": evidence_id or _stable_id("evidence", candidate_id, url, evidence_type, observed, notes),
        "candidate_id": candidate_id,
        "url": url,
        "evidence_type": evidence_type,
        "observed_on": observed,
        "reviewer_status": reviewer_status,
        "confidence": confidence,
        "notes": notes,
        "source_classification": source_classification,
        "primary_source": primary_source,
        "reviewer": reviewer,
        **copy.deepcopy(extra),
    }
    errors = validate_review_evidence(result)
    if errors:
        raise ValueError(errors[0])
    return result


def _append_review_evidence(
    batch: Mapping[str, Any],
    candidate_id: str,
    evidence: Mapping[str, Any],
    *,
    reviewer: str,
    recorded_on: str | date | None = None,
    allow_endpoint_probe: bool = False,
) -> dict[str, Any]:
    """Internal evidence append. Endpoint probes are reserved for the guarded probe function."""
    errors = validate_verification_batch(dict(batch))
    if errors:
        raise ValueError(f"invalid verification batch: {errors[0]}")
    updated = copy.deepcopy(dict(batch))
    review = _find_review(updated, candidate_id)
    workflow = review["workflow"]
    if workflow.get("workflow_status") in {"rejected", "catalog_acceptance_recorded"}:
        raise ValueError("terminal workflow cannot be modified")
    if workflow.get("current_stage_status") in {"blocked", "deferred", "rejected", "completed"}:
        raise ValueError("resume the blocked/deferred stage or move to an active stage before adding evidence")
    entry = copy.deepcopy(dict(evidence))
    entry.setdefault("candidate_id", candidate_id)
    entry.setdefault("reviewer", reviewer)
    entry.setdefault("observed_on", _date_text(recorded_on))
    entry.setdefault("evidence_id", _stable_id("evidence", candidate_id, entry.get("url"), entry.get("evidence_type"), entry.get("observed_on"), entry.get("notes")))
    evidence_errors = validate_review_evidence(entry)
    if evidence_errors:
        raise ValueError(evidence_errors[0])
    recorded = _date_text(recorded_on)
    if entry["observed_on"] > recorded:
        raise ValueError("evidence observed_on cannot be after its recorded_on date")
    if workflow.get("transition_log") and workflow["transition_log"][-1].get("recorded_on", "") > recorded:
        raise ValueError("evidence record date cannot precede the latest workflow event")
    if entry["candidate_id"] != candidate_id:
        raise ValueError("evidence candidate_id does not match selected candidate")
    if entry.get("reviewer") != reviewer:
        raise ValueError("evidence reviewer must match the append-only event actor")
    existing = _evidence_map(workflow)
    if entry["evidence_id"] in existing:
        raise ValueError("duplicate evidence_id; evidence ledger is append-only")
    if entry.get("evidence_type") == "endpoint_probe":
        if not allow_endpoint_probe:
            raise ValueError("endpoint_probe evidence can only be recorded by probe_review_endpoint")
        permission_id = entry.get("permission_evidence_id")
        permission = existing.get(permission_id)
        if workflow.get("current_stage") != "endpoint_verification":
            raise ValueError("endpoint probes are only permitted in the endpoint_verification stage")
        if not _probe_permission_valid(permission):
            raise ValueError("probe permission must reference reviewed primary provider policy that explicitly permits unauthenticated read probes")
        if not any(
            item.get("evidence_type") == "endpoint_documentation"
            and item.get("primary_source") is True
            and item.get("source_classification") == "official_provider"
            and item.get("reviewer_status") == "supports"
            and item.get("documented_endpoint_url") == entry.get("url")
            and item.get("documented_method") == entry.get("request_method")
            and _confidence_is_authoritative(item)
            for item in workflow.get("evidence", [])
        ):
            raise ValueError("probe URL and method must match reviewed official endpoint documentation")
    workflow["evidence"].append(entry)
    _append_event(
        workflow,
        candidate_id=candidate_id,
        event_type="evidence_added",
        actor=reviewer,
        actor_role="reviewer",
        recorded_on=recorded,
        notes=f"Added {entry['evidence_type']} evidence; reviewer status={entry['reviewer_status']}.",
        evidence_ids=[entry["evidence_id"]],
    )
    _refresh_summary(updated)
    errors = validate_verification_batch(updated)
    if errors:
        raise ValueError(f"evidence update would invalidate batch: {errors[0]}")
    return updated


def add_review_evidence(
    batch: Mapping[str, Any],
    candidate_id: str,
    evidence: Mapping[str, Any],
    *,
    reviewer: str,
    recorded_on: str | date | None = None,
) -> dict[str, Any]:
    """Append manually reviewed evidence without fetching its URL or spoofing a probe."""
    return _append_review_evidence(
        batch, candidate_id, evidence, reviewer=reviewer, recorded_on=recorded_on
    )


def record_review_finding(
    batch: Mapping[str, Any],
    candidate_id: str,
    field: str,
    value: Any,
    *,
    status: str,
    evidence_ids: Sequence[str],
    reviewer: str,
    notes: str,
    confidence: float,
    observed_on: str | date | None = None,
) -> dict[str, Any]:
    """Record a finding in its corresponding stage, requiring primary evidence for verified facts."""
    errors = validate_verification_batch(dict(batch))
    if errors:
        raise ValueError(f"invalid verification batch: {errors[0]}")
    if field not in FINDING_STAGE or status not in FINDING_STATUSES:
        raise ValueError("unsupported finding field or status")
    if not isinstance(reviewer, str) or not reviewer.strip() or not isinstance(notes, str) or not notes.strip():
        raise ValueError("reviewer and notes are required")
    if _contains_possible_secret({"value": value, "notes": notes}):
        raise ValueError("finding may contain credential material")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(float(confidence)) or not 0 <= float(confidence) <= 1:
        raise ValueError("finding confidence must be finite and in 0..1")
    updated = copy.deepcopy(dict(batch))
    review = _find_review(updated, candidate_id)
    workflow = review["workflow"]
    expected_stage = FINDING_STAGE[field]
    if workflow.get("workflow_status") in {"rejected", "catalog_acceptance_recorded"}:
        raise ValueError("terminal workflow cannot be modified")
    if workflow["current_stage"] != expected_stage:
        raise ValueError(f"finding {field} belongs to stage {expected_stage}")
    if workflow["current_stage_status"] in {"blocked", "deferred", "rejected", "completed"}:
        raise ValueError("resume the blocked/deferred stage or move to an active stage before recording findings")
    evidence = _evidence_map(workflow)
    if not isinstance(evidence_ids, (list, tuple)):
        raise ValueError("evidence_ids must be a sequence of evidence IDs")
    refs = list(evidence_ids)
    if any(not isinstance(item, str) or item not in evidence for item in refs):
        raise ValueError("finding references unknown evidence")
    if len(refs) != len(set(refs)):
        raise ValueError("finding evidence IDs must be unique")
    finding = {
        "status": status,
        "value": copy.deepcopy(value),
        "evidence_ids": refs,
        "confidence": float(confidence),
        "notes": _clean_text(notes),
        "reviewer": reviewer,
        "observed_on": _date_text(observed_on),
    }
    if any(evidence[item].get("observed_on", "") > finding["observed_on"] for item in refs):
        raise ValueError("finding observed_on cannot precede its cited evidence")
    if workflow.get("transition_log") and workflow["transition_log"][-1].get("recorded_on", "") > finding["observed_on"]:
        raise ValueError("finding observed_on cannot precede the latest workflow event")
    if status == "verified":
        if float(confidence) <= 0:
            raise ValueError("verified findings require non-zero confidence")
        if not _finding_value_is_valid(field, value):
            raise ValueError(f"verified finding {field} requires a determinate value of the documented type")
        qualifying = [evidence[item] for item in refs if item in evidence and _authoritative_evidence(evidence[item], field)]
        if field == "currently_accessible":
            qualifying = [item for item in qualifying if _probe_permission_valid(evidence.get(item.get("permission_evidence_id")))]
        if not qualifying:
            raise ValueError(f"verified finding {field} requires suitable authoritative evidence")
        max_evidence_confidence = max(float(item["confidence"]) for item in qualifying)
        if finding["confidence"] > max_evidence_confidence:
            raise ValueError("finding confidence cannot exceed its supporting authoritative evidence confidence")
    elif status == "inconclusive":
        if value not in ("UNKNOWN", "NOT_TESTED") or not refs:
            raise ValueError("inconclusive findings require evidence and an UNKNOWN/NOT_TESTED value")
    elif value not in ("UNKNOWN", "NOT_TESTED"):
        raise ValueError("unknown findings must keep values UNKNOWN or NOT_TESTED")
    workflow["findings"][field] = finding
    if workflow["current_stage_status"] == "not_started":
        workflow["current_stage_status"] = "in_progress"
        workflow["stage_statuses"][expected_stage] = "in_progress"
    _append_event(
        workflow,
        candidate_id=candidate_id,
        event_type="finding_recorded",
        actor=reviewer,
        actor_role="reviewer",
        recorded_on=finding["observed_on"],
        notes=f"Recorded {field} finding with status {status}; upstream claims were preserved unchanged.",
        evidence_ids=refs,
        field=field,
        finding_status=status,
        value=copy.deepcopy(value),
        confidence=float(confidence),
    )
    _refresh_summary(updated)
    errors = validate_verification_batch(updated)
    if errors:
        raise ValueError(f"finding update would invalidate batch: {errors[0]}")
    return updated


def _enforce_probe_rate_limit(host: str, *, sleeper: Callable[[float], None] | None = None, clock: Callable[[], float] | None = None) -> None:
    sleep_for = sleeper or time.sleep
    monotonic = clock or time.monotonic
    with _PROBE_RATE_LOCK:
        now = monotonic()
        previous = _PROBE_LAST_BY_HOST.get(host)
        if previous is not None:
            delay = max(0.0, previous + _PROBE_MIN_INTERVAL_SECONDS - now)
            if delay:
                sleep_for(delay)
                now = monotonic()
        _PROBE_LAST_BY_HOST[host] = now


def probe_review_endpoint(
    batch: Mapping[str, Any],
    candidate_id: str,
    url: str,
    *,
    permission_evidence_id: str,
    reviewer: str,
    request_method: str = "GET",
    observed_on: str | date | None = None,
    timeout_seconds: float = 5.0,
    max_response_bytes: int = 65536,
) -> dict[str, Any]:
    """Explicitly probe one documented read endpoint after primary policy approval.

    Only unauthenticated HTTPS GET/HEAD is permitted. Redirects are rejected,
    retries are disabled, each host is limited to one probe per two seconds, and
    no response body, header, or credential is retained in the evidence ledger.
    """
    errors = validate_verification_batch(dict(batch))
    if errors:
        raise ValueError(f"invalid verification batch: {errors[0]}")
    if not isinstance(request_method, str) or request_method not in {"GET", "HEAD"}:
        raise ValueError("only GET or HEAD endpoint probes are permitted")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or not 0 < float(timeout_seconds) <= 10:
        raise ValueError("timeout_seconds must be in (0, 10]")
    if isinstance(max_response_bytes, bool) or not isinstance(max_response_bytes, int) or not 1 <= max_response_bytes <= 262144:
        raise ValueError("max_response_bytes must be 1..262144")
    if not isinstance(reviewer, str) or not reviewer.strip() or _contains_possible_secret(reviewer):
        raise ValueError("reviewer is required and must not contain credentials")
    try:
        _safe_http_url(url, require_https=True)
        target = urlsplit(url)
    except (TypeError, ValueError):
        raise ValueError("probe URL must be safe HTTPS") from None
    if target.query or target.fragment:
        raise ValueError("endpoint probes must not include a query or fragment")
    try:
        _check_relative_path(unquote(target.path))
    except UnsafeRequestError:
        raise ValueError("endpoint probe path is unsafe") from None
    updated = copy.deepcopy(dict(batch))
    review = _find_review(updated, candidate_id)
    workflow = review["workflow"]
    if workflow.get("current_stage") != "endpoint_verification" or workflow.get("current_stage_status") in {"blocked", "deferred"}:
        raise ValueError("endpoint probes are only allowed in an active endpoint_verification stage")
    classification = classify_review_candidate(review["candidate"], workflow)
    if classification["api_real"] is not True or classification["official_provider"] != "yes" or classification["documentation_available"] is not True:
        raise ValueError("verify API existence, provider identity, and official documentation before probing")
    evidence = _evidence_map(workflow)
    permission = evidence.get(permission_evidence_id)
    if not _probe_permission_valid(permission):
        raise ValueError("probe requires reviewed official provider policy explicitly permitting unauthenticated read probes")
    endpoint_docs = [
        item for item in workflow.get("evidence", [])
        if item.get("evidence_type") == "endpoint_documentation"
        and item.get("primary_source") is True
        and item.get("source_classification") == "official_provider"
        and item.get("reviewer_status") == "supports"
        and item.get("documented_endpoint_url") == url
        and item.get("documented_method") == request_method
        and _confidence_is_authoritative(item)
    ]
    if not endpoint_docs:
        raise ValueError("probe must target an exact endpoint and method documented by the official provider")
    base_url = review["candidate"].get("base_url")
    try:
        _safe_http_url(base_url, require_https=True)
        base = urlsplit(base_url)
        if base.query or base.fragment:
            raise ValueError("base URL query/fragment is not allowed")
    except (TypeError, ValueError):
        raise ValueError("candidate has no safe HTTPS base_url for an endpoint probe") from None
    if target.hostname is None or target.hostname.casefold().rstrip(".") != (base.hostname or "").casefold().rstrip("."):
        raise ValueError("probe host must match the candidate's documented API base host")
    host = target.hostname.casefold().rstrip(".")
    _enforce_probe_rate_limit(host)
    http = SafeHTTPTransport(
        timeout=float(timeout_seconds),
        retries=0,
        max_response_bytes=max_response_bytes,
    )
    status_code: int | None = None
    response_bytes = 0
    outcome = "network_error"
    reviewer_status = "inconclusive"
    confidence = 0.5
    accessible_value: bool | str = "NOT_TESTED"
    notes = "The unauthenticated probe did not receive a classifiable HTTP response; no retry was attempted."
    try:
        result = http.request(
            candidate_id,
            request_method,
            url,
            allowed_hosts={host},
            retries=0,
            max_response_bytes=max_response_bytes,
        )
        if not isinstance(result, HTTPResult) or isinstance(result.status_code, bool) or not isinstance(result.status_code, int) or not 100 <= result.status_code <= 599 or not isinstance(result.body, bytes):
            raise ValueError("probe transport must return a valid HTTPResult")
        status_code = result.status_code
        response_bytes = min(len(result.body), max_response_bytes)
        outcome = "http_response" if status_code < 400 else "http_error"
        reviewer_status = "supports"
        confidence = 0.9
        accessible_value = 200 <= status_code < 300
        notes = f"Unauthenticated {request_method} received HTTP {status_code}; response body and headers were discarded."
    except APIError as exc:
        status_code = exc.status_code
        if status_code is None:
            outcome = "network_error"
            reviewer_status = "inconclusive"
            confidence = 0.5
            accessible_value = "NOT_TESTED"
        elif 200 <= status_code < 300 and "Response exceeds configured size limit" in str(exc):
            outcome = "response_too_large"
            response_bytes = max_response_bytes
            reviewer_status = "supports"
            confidence = 0.9
            accessible_value = True
            notes = f"Unauthenticated {request_method} received HTTP {status_code}; response exceeded the configured cap and was discarded."
        else:
            outcome = "http_error"
            reviewer_status = "supports"
            confidence = 0.9
            accessible_value = 200 <= status_code < 300
            notes = f"Unauthenticated {request_method} received HTTP {status_code}; no response body or headers were retained."
    when = _date_text(observed_on)
    probe_evidence = create_review_evidence(
        candidate_id,
        url=url,
        evidence_type="endpoint_probe",
        observed_on=when,
        reviewer_status=reviewer_status,
        confidence=confidence,
        notes=notes,
        source_classification="probe_result",
        primary_source=True,
        reviewer=reviewer,
        permission_evidence_id=permission_evidence_id,
        policy_permitted=True,
        request_method=request_method,
        credentials_sent=False,
        timeout_seconds=float(timeout_seconds),
        max_response_bytes=max_response_bytes,
        rate_limit_interval_seconds=_PROBE_MIN_INTERVAL_SECONDS,
        retries=0,
        status_code=status_code,
        response_bytes=response_bytes,
        probe_outcome=outcome,
    )
    updated = _append_review_evidence(
        updated, candidate_id, probe_evidence, reviewer=reviewer, recorded_on=when,
        allow_endpoint_probe=True,
    )
    updated = record_review_finding(
        updated,
        candidate_id,
        "currently_accessible",
        accessible_value,
        status="verified" if isinstance(accessible_value, bool) else "inconclusive",
        evidence_ids=[probe_evidence["evidence_id"]],
        reviewer=reviewer,
        notes=notes,
        confidence=confidence,
        observed_on=when,
    )
    return updated


def transition_review_stage(
    batch: Mapping[str, Any],
    candidate_id: str,
    *,
    outcome: str,
    reviewer: str,
    notes: str,
    recorded_on: str | date | None = None,
    evidence_ids: Sequence[str] = (),
    reviewer_role: str = "reviewer",
    decision: str | None = None,
    catalog_entry_id: str | None = None,
    catalog_entry_sha256: str | None = None,
    catalog_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Move one stage at a time, appending an immutable-style event to the ledger."""
    errors = validate_verification_batch(dict(batch))
    if errors:
        raise ValueError(f"invalid verification batch: {errors[0]}")
    if not isinstance(outcome, str) or outcome not in TRANSITION_OUTCOMES:
        raise ValueError(f"outcome must be one of {sorted(TRANSITION_OUTCOMES)}")
    if not isinstance(reviewer_role, str) or reviewer_role not in {"reviewer", "human", "system"}:
        raise ValueError("reviewer_role must be reviewer, human, or system")
    if not isinstance(reviewer, str) or not reviewer.strip() or not isinstance(notes, str) or not notes.strip():
        raise ValueError("reviewer and notes are required for every transition")
    if _contains_possible_secret(notes):
        raise ValueError("transition notes may contain credential material")
    updated = copy.deepcopy(dict(batch))
    review = _find_review(updated, candidate_id)
    workflow = review["workflow"]
    current = workflow["current_stage"]
    current_status = workflow["current_stage_status"]
    if workflow["workflow_status"] in {"rejected", "catalog_acceptance_recorded"}:
        raise ValueError("terminal workflow cannot be advanced")
    evidence = _evidence_map(workflow)
    if not isinstance(evidence_ids, (list, tuple)):
        raise ValueError("transition evidence_ids must be a sequence of IDs")
    refs = list(evidence_ids)
    if any(not isinstance(item, str) or item not in evidence for item in refs):
        raise ValueError("transition references unknown evidence")
    if len(refs) != len(set(refs)):
        raise ValueError("transition evidence IDs must be unique")
    when = _date_text(recorded_on)
    if workflow.get("transition_log") and workflow["transition_log"][-1].get("recorded_on", "") > when:
        raise ValueError("transition date cannot precede the latest workflow event")
    if any(evidence[item].get("observed_on", "") > when for item in refs):
        raise ValueError("transition date cannot precede its cited evidence")
    if current not in {"human_approval", "catalog_acceptance"} and decision is not None:
        raise ValueError("decision is only accepted during human approval or catalog acceptance")
    to_stage = current
    actual_outcome = outcome
    if outcome == "resumed":
        if current_status not in {"blocked", "deferred"}:
            raise ValueError("only blocked or deferred stages can be resumed")
        workflow["current_stage_status"] = "in_progress"
        workflow["stage_statuses"][current] = "in_progress"
        workflow["workflow_status"] = "in_review"
    elif outcome in {"blocked", "deferred", "rejected"}:
        if outcome == "rejected" and current == "human_approval":
            if reviewer_role != "human" or decision != "rejected":
                raise ValueError("human-approval rejection requires an explicit human decision")
            workflow["approval"] = {"decision": "rejected", "reviewer": reviewer, "reviewed_on": _date_text(recorded_on), "notes": _clean_text(notes)}
            if isinstance(workflow.get("proposal"), dict):
                workflow["proposal"]["status"] = "human_rejected"
        elif decision is not None:
            raise ValueError("decision is only accepted during human approval or catalog acceptance")
        workflow["current_stage_status"] = outcome
        workflow["stage_statuses"][current] = outcome
        workflow["workflow_status"] = "rejected" if outcome == "rejected" else outcome
    else:
        if current_status in {"blocked", "deferred", "rejected", "completed"}:
            raise ValueError("current stage is not available for completion")
        for field in _STAGE_FINDINGS.get(current, ()):
            if workflow["findings"][field]["status"] not in {"verified", "inconclusive"}:
                raise ValueError(f"complete required finding first: {field}")
        allowed_types = _STAGE_EVIDENCE_TYPES.get(current)
        if allowed_types:
            relevant = set(refs)
            for field in _STAGE_FINDINGS.get(current, ()):
                relevant.update(workflow["findings"][field].get("evidence_ids", []))
            if not any(item in evidence and evidence[item].get("evidence_type") in allowed_types for item in relevant):
                raise ValueError(f"stage {current} requires evidence of type {sorted(allowed_types)}")
        if current == "human_approval":
            if reviewer_role != "human" or decision not in {"approved", "rejected"}:
                raise ValueError("human_approval requires reviewer_role=human and an explicit decision")
            if decision == "rejected":
                workflow["approval"] = {"decision": "rejected", "reviewer": reviewer, "reviewed_on": _date_text(recorded_on), "notes": _clean_text(notes)}
                if isinstance(workflow.get("proposal"), dict):
                    workflow["proposal"]["status"] = "human_rejected"
                workflow["current_stage_status"] = "rejected"
                workflow["stage_statuses"][current] = "rejected"
                workflow["workflow_status"] = "rejected"
                actual_outcome = "rejected"
            else:
                if not isinstance(workflow.get("proposal"), dict) or workflow["proposal"].get("status") != "pending_human_approval":
                    raise ValueError("human approval requires a pending API record proposal")
                workflow["approval"] = {"decision": "approved", "reviewer": reviewer, "reviewed_on": _date_text(recorded_on), "notes": _clean_text(notes)}
                workflow["proposal"]["status"] = "human_approved"
                workflow["current_stage_status"] = "completed"
                workflow["stage_statuses"][current] = "completed"
                to_stage = VERIFICATION_STAGES[VERIFICATION_STAGES.index(current) + 1]
                workflow["current_stage"] = to_stage
                workflow["current_stage_status"] = "not_started"
                workflow["workflow_status"] = "approved_pending_catalog"
        elif current == "catalog_acceptance":
            if reviewer_role != "human" or decision != "accepted":
                raise ValueError("catalog_acceptance requires a separate human accepted decision")
            if not isinstance(workflow.get("approval"), dict) or workflow["approval"].get("decision") != "approved":
                raise ValueError("catalog acceptance requires recorded human approval")
            proposal = workflow.get("proposal")
            if not isinstance(proposal, dict) or proposal.get("status") != "human_approved":
                raise ValueError("catalog acceptance requires the approved proposal")
            if not isinstance(catalog_entry_id, str) or catalog_entry_id.strip() != proposal.get("api_record", {}).get("id"):
                raise ValueError("catalog acceptance ID must match the approved proposal")
            digest = catalog_entry_sha256.casefold() if isinstance(catalog_entry_sha256, str) else ""
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise ValueError("catalog acceptance requires SHA-256 of the accepted catalog record")
            if not isinstance(catalog_record, Mapping):
                raise ValueError("catalog acceptance requires the exact record already present in the API catalog")
            existing_record = copy.deepcopy(dict(catalog_record))
            if existing_record.get("id") != catalog_entry_id:
                raise ValueError("catalog record ID does not match the approved proposal")
            record_errors = validate_catalog_data(
                {"schema_version": "1.0", "last_updated": when, "records": [existing_record]}, "apis"
            )
            if record_errors:
                raise ValueError(f"existing catalog record is invalid: {record_errors[0]}")
            if _canonical_json_sha256(existing_record) != digest:
                raise ValueError("catalog entry digest does not match the existing API catalog record SHA-256")
            if digest != _canonical_json_sha256(proposal["api_record"]):
                raise ValueError("catalog acceptance digest must match the exact approved API record")
            workflow["catalog_acceptance"] = {
                "catalog_entry_id": catalog_entry_id,
                "catalog_entry_sha256": digest,
                "recorded_by": reviewer,
                "recorded_on": _date_text(recorded_on),
                "catalog_file_modified_by_this_command": False,
            }
            workflow["proposal"]["status"] = "catalog_accepted"
            workflow["current_stage_status"] = "completed"
            workflow["stage_statuses"][current] = "completed"
            workflow["workflow_status"] = "catalog_acceptance_recorded"
        else:
            workflow["current_stage_status"] = "completed"
            workflow["stage_statuses"][current] = "completed"
            to_stage = VERIFICATION_STAGES[VERIFICATION_STAGES.index(current) + 1]
            workflow["current_stage"] = to_stage
            workflow["current_stage_status"] = "not_started"
            workflow["workflow_status"] = "in_review"
    _append_event(
        workflow,
        candidate_id=candidate_id,
        event_type="stage_transition",
        actor=reviewer,
        actor_role=reviewer_role,
        recorded_on=when,
        notes=_clean_text(notes),
        evidence_ids=refs,
        from_stage=current,
        to_stage=to_stage,
        outcome=actual_outcome,
        decision=decision,
        catalog_entry_id=catalog_entry_id,
        catalog_entry_sha256=catalog_entry_sha256,
    )
    _refresh_summary(updated)
    errors = validate_verification_batch(updated)
    if errors:
        raise ValueError(f"stage transition would invalidate batch: {errors[0]}")
    return updated


def create_api_record_proposal(
    batch: Mapping[str, Any],
    candidate_id: str,
    api_record: Mapping[str, Any],
    *,
    reviewer: str,
    created_on: str | date | None = None,
    existing_ids: Iterable[str] = (),
) -> dict[str, Any]:
    """Store a validated record draft for human approval; do not mutate catalogs."""
    errors = validate_verification_batch(dict(batch))
    if errors:
        raise ValueError(f"invalid verification batch: {errors[0]}")
    updated = copy.deepcopy(dict(batch))
    review = _find_review(updated, candidate_id)
    workflow = review["workflow"]
    if (workflow.get("current_stage") != "human_approval" or workflow.get("workflow_status") != "in_review"
            or workflow.get("current_stage_status") not in {"not_started", "in_progress"}):
        raise ValueError("proposal can only be created at an active human_approval stage")
    if workflow.get("proposal") is not None:
        raise ValueError("a proposal already exists for this candidate")
    if not isinstance(reviewer, str) or not reviewer.strip() or _contains_possible_secret(reviewer):
        raise ValueError("proposal reviewer is required and must not contain credential material")
    if not isinstance(api_record, Mapping):
        raise ValueError("proposed API record must be an object")
    record = copy.deepcopy(dict(api_record))
    record_id = record.get("id")
    if not isinstance(record_id, str) or not record_id.strip():
        raise ValueError("proposed API record needs an id")
    try:
        accepted_ids = set(existing_ids)
    except TypeError:
        raise ValueError("existing_ids must be an iterable of record IDs") from None
    if record_id in accepted_ids:
        raise ValueError(f"proposed API id already exists: {record_id}")
    verified = classify_review_candidate(review["candidate"], workflow)
    blockers = _proposal_blockers(review["candidate"], verified)
    if blockers:
        raise ValueError(f"cannot propose until independently verified facts are complete: {', '.join(blockers)}")
    created = _date_text(created_on)
    if workflow.get("transition_log") and workflow["transition_log"][-1].get("recorded_on", "") > created:
        raise ValueError("proposal creation date cannot precede the latest workflow event")
    catalog_doc = {"schema_version": "1.0", "last_updated": created, "records": [record]}
    errors = validate_catalog_data(catalog_doc, "apis")
    if errors:
        raise ValueError(f"invalid proposed API record: {errors[0]}")
    if record.get("free_status") != verified["free_status"] or record.get("quota") != verified["quota"] or record.get("license") != verified["license"]:
        raise ValueError("proposed API record must preserve the verified access status, quota, and license exactly")
    record_auth = record.get("authentication")
    if not isinstance(record_auth, dict) or not _authentication_record_matches(verified.get("authentication"), record_auth):
        raise ValueError("proposed API record contradicts or omits verified authentication requirements")
    evidence = workflow.get("evidence", [])
    verified_ids = sorted({
        evidence_item["evidence_id"]
        for finding in workflow["findings"].values() if finding.get("status") == "verified"
        for evidence_item in evidence if evidence_item.get("evidence_id") in finding.get("evidence_ids", [])
    })
    source_urls = {source.get("url") for source in record.get("sources", []) if isinstance(source, dict)}
    verified_urls = {evidence_item.get("url") for evidence_item in evidence if evidence_item.get("evidence_id") in verified_ids}
    if not verified_urls.issubset(source_urls):
        raise ValueError("proposed API record must cite every source used for verified facts")
    record_digest = _canonical_json_sha256(record)
    proposal = {
        "proposal_id": _stable_id("proposal", candidate_id, record_id, created),
        "candidate_id": candidate_id,
        "status": "pending_human_approval",
        "created_on": created,
        "created_by": reviewer,
        "api_record": record,
        "api_record_sha256": record_digest,
        "verified_evidence_ids": verified_ids,
        "source_attributions": copy.deepcopy(review["candidate"].get("source_attributions", [])),
        "source_claims": copy.deepcopy(review["candidate"].get("source_claims", {})),
        "source_claims_by_source": copy.deepcopy(review["candidate"].get("source_claims_by_source", [])),
        "note": "Proposal only. It does not alter the accepted API catalog; explicit human review is required.",
    }
    workflow["proposal"] = proposal
    workflow["current_stage_status"] = "in_progress"
    workflow["stage_statuses"]["human_approval"] = "in_progress"
    _append_event(
        workflow,
        candidate_id=candidate_id,
        event_type="api_record_proposal_created",
        actor=reviewer,
        actor_role="reviewer",
        recorded_on=proposal["created_on"],
        notes=proposal["note"],
        evidence_ids=verified_ids,
        proposal_id=proposal["proposal_id"],
        api_record_sha256=record_digest,
    )
    proposal["verification_history"] = copy.deepcopy(workflow["transition_log"])
    _refresh_summary(updated)
    errors = validate_verification_batch(updated)
    if errors:
        raise ValueError(f"proposal would invalidate batch: {errors[0]}")
    return updated


def find_candidate_duplicates(candidates: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Report exact and possible duplicate pairs without merging or discarding leads."""
    items = [item for item in candidates if isinstance(item, Mapping)]
    by_identity: dict[tuple[str, str], list[str]] = defaultdict(list)
    by_name: dict[str, list[tuple[str, str]]] = defaultdict(list)
    by_url: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for candidate in items:
        candidate_id = str(candidate.get("candidate_id", ""))
        name = _name_key(str(candidate.get("name", "")))
        url = str(candidate.get("base_url") or candidate.get("listed_url") or candidate.get("source_url") or "")
        if not url:
            continue
        canonical = _canonical_url(url)
        by_identity[(name, canonical)].append(candidate_id)
        by_name[name].append((candidate_id, canonical))
        by_url[canonical].append((candidate_id, name))
    pairs: dict[tuple[str, str], set[str]] = defaultdict(set)
    for entries in by_identity.values():
        for index, left in enumerate(entries):
            for right in entries[index + 1:]:
                pairs[tuple(sorted((left, right)))].add("exact_name_and_url")
    for entries in by_name.values():
        for index, (left, left_url) in enumerate(entries):
            for right, right_url in entries[index + 1:]:
                if left_url != right_url:
                    pairs[tuple(sorted((left, right)))].add("same_name_different_url")
    for entries in by_url.values():
        for index, (left, left_name) in enumerate(entries):
            for right, right_name in entries[index + 1:]:
                if left_name != right_name:
                    pairs[tuple(sorted((left, right)))].add("same_url_different_name")
    return [{"candidate_ids": list(ids), "signals": sorted(signals)} for ids, signals in sorted(pairs.items())]


def load_verification_batch(path: str | Path) -> dict[str, Any]:
    """Load and validate a saved workflow batch."""
    try:
        batch = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CatalogError(f"Could not load verification batch ({type(exc).__name__})") from None
    errors = validate_verification_batch(batch)
    if errors:
        raise CatalogError(f"Invalid verification batch: {errors[0]}")
    return batch


def save_verification_batch(batch: Mapping[str, Any], path: str | Path) -> Path:
    """Validate and atomically save a workflow batch, without touching catalogs."""
    errors = validate_verification_batch(dict(batch))
    if errors:
        raise CatalogError(f"Invalid verification batch: {errors[0]}")
    target = Path(path)
    temporary = target.with_name(target.name + ".tmp")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(batch, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(target)
    except (OSError, TypeError, ValueError) as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise CatalogError(f"Could not save verification batch ({type(exc).__name__})") from None
    return target
