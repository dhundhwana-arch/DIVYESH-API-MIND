"""Unified offline search and explainable recommendations across local records.

Accepted API/model/dataset records, MCP metadata, and research-only technology
leads remain clearly separated. Constructing or searching this hub is offline.
"""

from __future__ import annotations

import copy
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from .catalog import APIMind
from .exceptions import CatalogError
from .mcp import MCPRegistry
from .research import validate_technology_discovery
from .validation import STATUS_VALUES

_FREE_STATES = frozenset(
    {"FREE_NO_KEY", "FREE_WITH_KEY", "FREE_TIER_LIMITED", "OPEN_SOURCE_SELF_HOSTED"}
)
_ACCESS_ALIASES = {
    "FREE": "FREE",
    "FREE_NO_KEY": "FREE_NO_KEY",
    "KEYLESS": "FREE_NO_KEY",
    "FREE_WITH_KEY": "FREE_WITH_KEY",
    "FREE_TIER": "FREE_TIER_LIMITED",
    "FREE_TIER_LIMITED": "FREE_TIER_LIMITED",
    "OPEN_SOURCE": "OPEN_SOURCE_SELF_HOSTED",
    "OPEN_SOURCE_SELF_HOSTED": "OPEN_SOURCE_SELF_HOSTED",
    "FREE_DATA_PAID_SERVICE": "FREE_DATA_PAID_SERVICE",
    "PAID": "PAID",
    "UNKNOWN": "UNKNOWN",
}
_TRI_STATE = {True: "YES", False: "NO", None: "UNKNOWN"}


def _explicit_bool(record: Mapping[str, Any], *names: str) -> bool | None:
    for name in names:
        value = record.get(name)
        if isinstance(value, bool):
            return value
    return None


def _auth_requirement(record: Mapping[str, Any]) -> bool | None:
    value = record.get("api_key_required")
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value in {"YES", "NO"}:
        return value == "YES"
    auth = record.get("authentication")
    if isinstance(auth, Mapping):
        required = auth.get("required")
        # Accepted catalog auth is usable unless explicitly marked unverified.
        if isinstance(required, bool) and auth.get("verified") is not False and auth.get("kind") != "unknown":
            return required
    return None


def _open_source(record: Mapping[str, Any]) -> bool | None:
    explicit = _explicit_bool(record, "open_source")
    if explicit is not None:
        return explicit
    value = record.get("open_source_status")
    if isinstance(value, str) and value in {"YES", "NO"}:
        return value == "YES"
    if record.get("free_status") == "OPEN_SOURCE_SELF_HOSTED":
        return True
    return None


def _commercial_use(record: Mapping[str, Any]) -> bool | None:
    explicit = _explicit_bool(record, "commercial_use", "commercial_use_permitted")
    if explicit is not None:
        return explicit
    value = record.get("commercial_use_status")
    if isinstance(value, str) and value in {"YES", "NO"}:
        return value == "YES"
    license_info = record.get("license")
    if isinstance(license_info, Mapping):
        explicit = _explicit_bool(license_info, "commercial_use", "commercial_use_permitted")
        if explicit is not None:
            return explicit
    return None


def _python_sdk(record: Mapping[str, Any]) -> bool | None:
    explicit = _explicit_bool(record, "python_sdk_available", "python_sdk")
    if explicit is not None:
        return explicit
    status = record.get("python_sdk_status")
    if status == "YES":
        return True
    if status == "NO":
        return False
    # Only a positive, explicit cataloged SDK name is considered. Notes saying
    # "not verified" and generic REST/HTTP clients do not count.
    values = record.get("sdk", [])
    if not isinstance(values, list):
        return None
    names = []
    for item in values:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, Mapping):
            names.extend(str(item.get(field, "")) for field in ("name", "status"))
    text = " ".join(names).casefold()
    if not text or any(phrase in text for phrase in ("not verified", "not confirmed", "not identified", "unknown")):
        return None
    if re.search(r"\bpython\b", text) and ("sdk" in text or "client" in text or "library" in text):
        return True
    return None


def _unlimited(record: Mapping[str, Any]) -> bool | None:
    value = record.get("unlimited")
    if isinstance(value, bool):
        return value
    status = record.get("unlimited_status")
    if status == "UNLIMITED":
        return True
    if status == "LIMITED":
        return False
    return None


def _local_deployment(record: Mapping[str, Any]) -> bool | None:
    explicit = _explicit_bool(record, "local_deployment", "self_hostable")
    if explicit is not None:
        return explicit
    status = record.get("local_deployment_status")
    if isinstance(status, str) and status in {"YES", "NO"}:
        return status == "YES"
    if record.get("free_status") == "OPEN_SOURCE_SELF_HOSTED":
        return True
    deployments = record.get("deployment_options")
    if isinstance(deployments, list):
        values = {str(value).casefold() for value in deployments}
        if values & {"local", "self-hosted", "self hosted", "on-premise", "on premises"}:
            return True
    return None


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _contains_term(text: str, term: str) -> bool:
    """Match a phrase without accidental substrings such as coding/geocoding."""
    return re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, flags=re.IGNORECASE) is not None


class IntelligenceHub:
    """Search accepted offline catalogs and separate unverified research leads.

    No provider endpoint, MCP server, local runtime, or hosted model is called
    by construction, search, explain, compare, or recommendation methods.
    """

    def __init__(
        self,
        *,
        catalog_dir: str | Path | None = None,
        discovery_path: str | Path | None = None,
        include_discovery: bool = True,
    ) -> None:
        if not isinstance(include_discovery, bool):
            raise ValueError("include_discovery must be a boolean")
        self._mind = APIMind(catalog_dir=catalog_dir)
        mcp_path = Path(catalog_dir) / "mcp_registry.json" if catalog_dir else None
        self._mcp = MCPRegistry(mcp_path)
        if discovery_path is not None:
            path = Path(discovery_path)
        elif catalog_dir is not None:
            path = Path(catalog_dir) / "technology_discovery.json"
        else:
            path = Path(__file__).resolve().parent / "data" / "technology_discovery.json"
        self._discovery_records: list[dict[str, Any]] = []
        if include_discovery and path.exists():
            try:
                document = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise CatalogError(f"Could not load technology discovery catalog ({type(exc).__name__})") from None
            errors = validate_technology_discovery(document)
            if errors:
                raise CatalogError(f"Invalid technology discovery catalog: {errors[0]}")
            self._discovery_records = copy.deepcopy(document["records"])
        elif include_discovery and discovery_path is not None:
            raise CatalogError("Could not load technology discovery catalog (FileNotFoundError)")
        self._include_discovery = include_discovery

    @staticmethod
    def _kind(record: Mapping[str, Any], origin: str) -> str:
        if origin == "mcp_metadata":
            return "mcp"
        if origin == "technology_discovery":
            return str(record.get("kind", "tool"))
        return str(record.get("type", "unknown"))

    @staticmethod
    def _normalize(record: Mapping[str, Any], origin: str) -> dict[str, Any]:
        result = copy.deepcopy(dict(record))
        kind = IntelligenceHub._kind(result, origin)
        free_status = result.get("free_status")
        if not isinstance(free_status, str) or free_status not in STATUS_VALUES:
            free_status = "UNKNOWN"
        evidence_confidence = result.get("evidence_confidence", result.get("confidence"))
        try:
            confidence = float(evidence_confidence)
            if not 0 <= confidence <= 1:
                confidence = None
        except (TypeError, ValueError):
            confidence = None
        authentication = result.get("authentication")
        auth_label = "UNKNOWN"
        if isinstance(authentication, Mapping):
            required = authentication.get("required")
            if isinstance(required, bool) and authentication.get("verified") is not False and authentication.get("kind") != "unknown":
                auth_label = "KEY_REQUIRED" if required else "NO_KEY_REQUIRED"
        elif isinstance(result.get("authentication_status"), str) and result["authentication_status"] in {"YES", "NO", "CONDITIONAL"}:
            auth_label = result["authentication_status"]
        requirements = result.get("usage_limits", result.get("quota_and_rate_limits", result.get("quota", result.get("rate_limits", "UNKNOWN"))))
        result.update(
            {
                "kind": kind,
                "record_state": (
                    "ACCEPTED_CATALOG" if origin == "accepted_catalog"
                    else "MCP_METADATA" if origin == "mcp_metadata"
                    else "DISCOVERY_ONLY"
                ),
                "record_origin": origin,
                "free_status": free_status,
                "api_key_required_value": _auth_requirement(result),
                "api_key_required": _TRI_STATE[_auth_requirement(result)],
                "keyless": _TRI_STATE[not _auth_requirement(result)] if _auth_requirement(result) is not None else "UNKNOWN",
                "unlimited_status": _TRI_STATE[_unlimited(result)],
                "open_source_status": _TRI_STATE[_open_source(result)],
                "python_sdk_status": _TRI_STATE[_python_sdk(result)],
                "commercial_use_status": _TRI_STATE[_commercial_use(result)],
                "local_deployment_status": _TRI_STATE[_local_deployment(result)],
                "authentication_summary": auth_label,
                "usage_limits_summary": copy.deepcopy(requirements),
                "evidence_confidence": confidence,
                "evidence_references": copy.deepcopy(result.get("sources", result.get("evidence", []))),
                "limitations": copy.deepcopy(result.get("unknown_fields", [])),
            }
        )
        if origin == "mcp_metadata":
            result["limitations"] = [
                "MCP registry/repository metadata is not a launched, working, security-reviewed, or healthy server.",
                "Authentication, service terms, data handling, and operational status require separate review.",
            ]
        elif origin == "technology_discovery":
            result["limitations"] = list(result.get("unknown_fields", [])) + [
                "Discovery-only GitHub repository lead; not an accepted API/model/tool record.",
                "GitHub metadata is not a live product/API test or a complete pricing/license/security review.",
            ]
        else:
            result["limitations"] = list(result.get("limitations", []))
            if not result.get("sources"):
                result["limitations"].append("No source references are recorded on this catalog item.")
        return result

    def _all_records(self, *, include_discovery: bool) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for kind in ("api", "model", "dataset"):
            records.extend(self._normalize(item, "accepted_catalog") for item in self._mind.search(kind=kind))
        records.extend(self._normalize(item, "mcp_metadata") for item in self._mcp.list())
        if include_discovery:
            records.extend(self._normalize(item, "technology_discovery") for item in self._discovery_records)
        ids = [item.get("id") for item in records]
        if len(ids) != len(set(ids)):
            raise CatalogError("intelligence records must have globally unique IDs across provenance")
        records.sort(key=lambda item: (item["record_state"], item["kind"], str(item.get("id", ""))))
        return records

    @property
    def counts(self) -> dict[str, int]:
        """Counts by provenance; discovery candidates are never mixed into accepted counts."""
        return {
            **self._mind.counts,
            "mcp_metadata": len(self._mcp.list()),
            "technology_discovery_only": len(self._discovery_records),
        }

    def categories(self, *, include_discovery: bool = True) -> dict[str, int]:
        counts: Counter[str] = Counter()
        if not isinstance(include_discovery, bool):
            raise ValueError("include_discovery must be a boolean")
        for record in self._all_records(include_discovery=include_discovery):
            for value in _strings(record.get("categories")):
                counts[value] += 1
        return dict(sorted(counts.items(), key=lambda item: item[0].casefold()))

    def search(
        self,
        *,
        category: str | None = None,
        capability: str | None = None,
        provider: str | None = None,
        access: str | None = None,
        free_status: str | None = None,
        kind: str | None = None,
        query: str | None = None,
        api_key_required: bool | None = None,
        keyless: bool | None = None,
        unlimited: bool | None = None,
        open_source: bool | None = None,
        python_sdk: bool | None = None,
        commercial_use: bool | None = None,
        language: str | None = None,
        local: bool | None = None,
        record_state: str | None = None,
        include_discovery: bool = True,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Filter local catalog and discovery metadata without network access.

        Tri-state filters match only explicit YES/NO evidence. ``unlimited=True``
        returns records whose data explicitly says UNLIMITED; absent or
        unpublished limits are UNKNOWN and never treated as unlimited.
        ``access='free'`` covers explicit free/keyless, free-with-key, limited
        free-tier, or open-source self-hosted classifications. It excludes
        ``FREE_DATA_PAID_SERVICE`` (free data but paid service), UNKNOWN, and PAID.
        Capability filters match word/phrase boundaries to avoid accidental matches such as ``coding`` inside ``geocoding``.
        """
        for name, value in (("category", category), ("capability", capability), ("provider", provider), ("access", access), ("free_status", free_status), ("kind", kind), ("query", query), ("language", language)):
            if value is not None and not isinstance(value, str):
                raise ValueError(f"{name} must be text or None")
        if access is not None:
            access_key = access.strip().upper().replace("-", "_").replace(" ", "_")
            if access_key not in _ACCESS_ALIASES:
                raise ValueError(f"access must be one of: {', '.join(sorted(_ACCESS_ALIASES))}")
            access = _ACCESS_ALIASES[access_key]
        if free_status is not None and free_status not in STATUS_VALUES:
            raise ValueError(f"free_status must be one of: {', '.join(sorted(STATUS_VALUES))}")
        for name, value in (
            ("api_key_required", api_key_required), ("keyless", keyless), ("unlimited", unlimited),
            ("open_source", open_source), ("python_sdk", python_sdk),
            ("commercial_use", commercial_use), ("local", local), ("include_discovery", include_discovery),
        ):
            if value is not None and not isinstance(value, bool):
                raise ValueError(f"{name} must be a boolean or None")
        if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit < 0):
            raise ValueError("limit must be a non-negative integer or None")
        valid_states = {"ACCEPTED_CATALOG", "MCP_METADATA", "DISCOVERY_ONLY"}
        if record_state is not None and (not isinstance(record_state, str) or record_state not in valid_states):
            raise ValueError(f"record_state must be one of: {', '.join(sorted(valid_states))}")
        category_term = category.casefold() if category else None
        capability_term = capability.casefold() if capability else None
        provider_term = provider.casefold() if provider else None
        kind_term = kind.casefold() if kind else None
        query_term = query.casefold() if query else None
        language_term = language.casefold() if language else None
        selected: list[dict[str, Any]] = []
        for record in self._all_records(include_discovery=include_discovery):
            if kind_term and record["kind"].casefold() != kind_term:
                continue
            if record_state and record["record_state"] != record_state:
                continue
            categories = _strings(record.get("categories"))
            if category_term and not any(category_term == value.casefold() for value in categories):
                continue
            capabilities = _strings(record.get("capabilities"))
            if capability_term and not any(_contains_term(value, capability_term) for value in capabilities):
                continue
            record_provider = str(record.get("provider", record.get("owner", ""))).casefold()
            if provider_term and provider_term not in record_provider:
                continue
            status = record.get("free_status", "UNKNOWN")
            if free_status is not None and status != free_status:
                continue
            if access == "FREE" and status not in _FREE_STATES:
                continue
            if access and access != "FREE" and status != access:
                continue
            if api_key_required is not None and record["api_key_required_value"] is not api_key_required:
                continue
            if keyless is not None and record["keyless"] != ("YES" if keyless else "NO"):
                continue
            if unlimited is not None and record["unlimited_status"] != ("YES" if unlimited else "NO"):
                continue
            if open_source is not None and record["open_source_status"] != ("YES" if open_source else "NO"):
                continue
            if python_sdk is not None and record["python_sdk_status"] != ("YES" if python_sdk else "NO"):
                continue
            if commercial_use is not None and record["commercial_use_status"] != ("YES" if commercial_use else "NO"):
                continue
            if local is not None and record["local_deployment_status"] != ("YES" if local else "NO"):
                continue
            if language_term:
                languages = _strings(record.get("languages", record.get("supported_languages", [])))
                if not any(language_term in value.casefold() for value in languages):
                    continue
            if query_term and query_term not in json.dumps(record, ensure_ascii=False, sort_keys=True).casefold():
                continue
            selected.append(record)
        if limit is not None:
            selected = selected[:limit]
        return copy.deepcopy(selected)

    def compare(self, record_ids: Iterable[str]) -> dict[str, Any]:
        """Return a side-by-side subset of requested records with provenance."""
        if isinstance(record_ids, (str, bytes)):
            raise ValueError("record_ids must be an iterable of one or more non-empty IDs")
        wanted = list(record_ids)
        if not wanted or any(not isinstance(value, str) or not value for value in wanted):
            raise ValueError("record_ids must contain one or more non-empty IDs")
        if len(wanted) != len(set(wanted)):
            raise ValueError("record_ids must be unique")
        records = {item["id"]: item for item in self._all_records(include_discovery=True)}
        missing = [record_id for record_id in wanted if record_id not in records]
        if missing:
            raise ValueError(f"unknown intelligence record IDs: {', '.join(missing)}")
        fields = (
            "id", "name", "provider", "kind", "categories", "capabilities", "record_state", "free_status",
            "api_key_required", "unlimited_status", "open_source_status", "python_sdk_status",
            "commercial_use_status", "local_deployment_status", "usage_limits_summary", "evidence_references", "limitations",
        )
        return {"records": [{key: copy.deepcopy(records[item].get(key)) for key in fields} for item in wanted]}

    def recommend(
        self,
        *,
        capability: str,
        access: str | None = None,
        keyless: bool | None = None,
        local: bool | None = None,
        commercial_use: bool | None = None,
        include_discovery: bool = True,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Rank documentary candidates with visible score reasons, never call them."""
        if not isinstance(capability, str) or not capability.strip():
            raise ValueError("capability must be non-empty text")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        candidates = self.search(
            capability=capability,
            access=access,
            keyless=keyless,
            local=local,
            commercial_use=commercial_use,
            include_discovery=include_discovery,
        )
        ranked = []
        query = capability.casefold()
        for record in candidates:
            capabilities = _strings(record.get("capabilities"))
            exact = any(value.casefold() == query for value in capabilities)
            score = 40 if exact else 25
            reasons = ["Capability metadata matches the requested phrase." if exact else "Capability text contains the requested phrase."]
            if record.get("free_status") in _FREE_STATES:
                score += 20
                reasons.append(f"Saved access classification is {record['free_status']}.")
            else:
                reasons.append("Access/pricing is UNKNOWN; this is not ranked as free.")
            if record.get("keyless") == "YES":
                score += 10
                reasons.append("Cataloged authentication says a key is not required.")
            if record.get("local_deployment_status") == "YES":
                score += 10
                reasons.append("Local/self-hosted deployment is explicitly represented in the catalog.")
            if record.get("open_source_status") == "YES":
                score += 8
                reasons.append("Catalog access classification identifies open-source self-hosting.")
            confidence = record.get("evidence_confidence")
            if isinstance(confidence, (int, float)) and not isinstance(confidence, bool):
                score += round(max(0.0, min(1.0, confidence)) * 12)
                reasons.append(f"Source record confidence field: {confidence:.2f} (not a probability).")
            if record["record_state"] != "ACCEPTED_CATALOG":
                score -= 12
                reasons.append(f"Provenance is {record['record_state']}; not an accepted/verified catalog item.")
            if record["record_state"] == "MCP_METADATA":
                score -= 25
                reasons.append("MCP metadata is not a callable tool integration.")
            ranked.append({**record, "recommendation_score": score, "why_ranked": reasons})
        ranked.sort(key=lambda item: (-item["recommendation_score"], item["record_state"], item["id"]))
        for index, record in enumerate(ranked):
            record["fallback_record_ids"] = [item["id"] for item in ranked[index + 1 : index + 4]]
            record["automatic_fallback"] = False
            record["no_live_availability_check"] = True
        return ranked[:limit]

    @staticmethod
    def explain(results: Iterable[Mapping[str, Any]]) -> str:
        """Render a compact, human-readable explanation without network I/O."""
        items = list(results)
        if not items:
            return "No records match the saved local evidence and selected filters. This does not prove that no suitable service exists."
        lines = []
        for index, record in enumerate(items, 1):
            name = record.get("name", record.get("id", "Unknown record"))
            state = record.get("record_state", "UNKNOWN_PROVENANCE")
            free = record.get("free_status", "UNKNOWN")
            lines.append(f"{index}. {name} — {state}; access {free}; limits remain provider- and evidence-scoped.")
            reasons = record.get("why_ranked", [])
            if isinstance(reasons, list):
                lines.extend(f"   - {reason}" for reason in reasons)
            limitations = record.get("limitations", [])
            if isinstance(limitations, list):
                lines.extend(f"   - Gap: {gap}" for gap in limitations[:4])
        lines.append("Recommendations are documentary only; no service was called, selected, or automatically substituted.")
        return "\n".join(lines)
