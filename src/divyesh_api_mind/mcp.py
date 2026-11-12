"""Read-only access to the separate, evidence-graded MCP registry."""

from __future__ import annotations

import copy
import json
from importlib.resources import files
from pathlib import Path
from typing import Any

from .exceptions import CatalogError, UnknownRecordError
from .validation import MCP_STATES, validate_catalog_data


class MCPRegistry:
    """Browse MCP metadata without launching or invoking any server.

    A registry listing is discovery metadata only. It is not a health check,
    code review, security audit, or proof that a server integrates correctly.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        try:
            if path is None:
                raw = files("divyesh_api_mind").joinpath("data/mcp_registry.json").read_text(encoding="utf-8")
            else:
                raw = Path(path).read_text(encoding="utf-8")
            data = json.loads(raw)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise CatalogError(f"Could not load MCP registry ({type(exc).__name__})") from None
        errors = validate_catalog_data(data, "mcp_registry")
        if errors:
            raise CatalogError(f"Invalid MCP registry: {errors[0]}")

        self._metadata = {key: value for key, value in data.items() if key != "records"}
        self._records = {record["id"]: record for record in data["records"]}

    @property
    def metadata(self) -> dict[str, Any]:
        """Return a defensive copy of the registry document metadata."""
        return copy.deepcopy(self._metadata)

    def list(self, *, status: str | None = None, query: str | None = None) -> list[dict[str, Any]]:
        """Return matching MCP metadata without connecting to servers."""
        if status is not None and status not in MCP_STATES:
            raise ValueError(f"status must be one of: {', '.join(sorted(MCP_STATES))}")
        terms = (query or "").casefold()
        result = []
        for record in self._records.values():
            if status is not None and record.get("status") != status:
                continue
            if terms and terms not in json.dumps(record, ensure_ascii=False).casefold():
                continue
            result.append(copy.deepcopy(record))
        return sorted(result, key=lambda item: item["id"])

    def get(self, record_id: str) -> dict[str, Any]:
        """Return a defensive copy of one MCP record."""
        try:
            return copy.deepcopy(self._records[record_id])
        except KeyError:
            raise UnknownRecordError(f"Unknown MCP record: {record_id}") from None

    def counts(self) -> dict[str, int]:
        """Count entries by evidence state; never interpreted as health status."""
        counts = {state: 0 for state in sorted(MCP_STATES)}
        for record in self._records.values():
            counts[record["status"]] += 1
        return counts
