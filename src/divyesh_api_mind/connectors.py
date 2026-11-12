"""Small provider-specific connectors built on the shared safe HTTP client."""

from __future__ import annotations

import math
import re
import threading
import time
from datetime import date as date_type
from typing import Any
from urllib.parse import quote

from .api_client import APIClient
from .exceptions import CredentialError, UnsafeRequestError
from .transport import HTTPResult


class APIConnector:
    """Generic connector for catalogued HTTPS JSON endpoints."""

    def __init__(self, client: APIClient, record_id: str, **_: Any) -> None:
        self._client = client
        self.record_id = record_id

    def get_json(self, path: str = "", *, params: dict[str, Any] | None = None) -> Any:
        return self._client.request_json(self.record_id, path, params=params)

    def get_text(self, path: str = "", *, params: dict[str, Any] | None = None) -> str:
        return self._client.request_text(self.record_id, path, params=params)

    def get_raw(self, path: str = "", *, params: dict[str, Any] | None = None) -> HTTPResult:
        return self._client.request_raw(self.record_id, path, params=params)

    def post_json(self, path: str, payload: Any, *, params: dict[str, Any] | None = None) -> Any:
        return self._client.request_json(self.record_id, path, method="POST", params=params, json_body=payload)

    def post_form(self, path: str, fields: dict[str, Any], *, params: dict[str, Any] | None = None) -> Any:
        return self._client.request_json(self.record_id, path, method="POST", params=params, form_body=fields)

    def health_check(self) -> dict[str, Any]:
        """Run this API record's documented safe probe, if one is configured."""
        return self._client.health_check(self.record_id)


_ARXIV_LOCK = threading.Lock()
_ARXIV_LAST_REQUEST = 0.0
_ARXIV_MIN_INTERVAL = 3.1


class ArxivConnector(APIConnector):
    """Constrained Atom-feed search wrapper for the public arXiv API.

    Requests are serialized and spaced by at least 3.1 seconds per process.
    The provider's policy applies across every machine under an operator's
    control, so applications must coordinate separate processes/hosts too.
    """

    _FIELDS = frozenset({"all", "ti", "au", "abs", "co", "jr", "cat", "rn", "id", "doi"})

    def get_json(self, path: str = "", *, params: dict[str, Any] | None = None) -> Any:
        raise UnsafeRequestError("arXiv returns Atom XML; use ArxivConnector.search()")

    def get_text(self, path: str = "", *, params: dict[str, Any] | None = None) -> str:
        raise UnsafeRequestError("Use ArxivConnector.search() to preserve the API request cadence")

    def get_raw(self, path: str = "", *, params: dict[str, Any] | None = None) -> HTTPResult:
        raise UnsafeRequestError("Use ArxivConnector.search() to preserve the API request cadence")

    def post_json(self, path: str, payload: Any, *, params: dict[str, Any] | None = None) -> Any:
        raise UnsafeRequestError("The arXiv API connector only permits rate-limited GET search requests")

    def post_form(self, path: str, fields: dict[str, Any], *, params: dict[str, Any] | None = None) -> Any:
        raise UnsafeRequestError("The arXiv API connector only permits rate-limited GET search requests")

    def search(
        self,
        query: str,
        *,
        field: str = "all",
        start: int = 0,
        max_results: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "descending",
    ) -> str:
        if not query.strip():
            raise ValueError("query must not be empty")
        if field not in self._FIELDS:
            raise ValueError(f"field must be one of: {', '.join(sorted(self._FIELDS))}")
        if isinstance(start, bool) or not isinstance(start, int) or start < 0:
            raise ValueError("start must be a non-negative integer")
        if isinstance(max_results, bool) or not isinstance(max_results, int) or not 1 <= max_results <= 100:
            raise ValueError("max_results must be between 1 and 100")
        if sort_by not in {"relevance", "lastUpdatedDate", "submittedDate"}:
            raise ValueError("unsupported arXiv sort_by value")
        if sort_order not in {"ascending", "descending"}:
            raise ValueError("sort_order must be ascending or descending")

        global _ARXIV_LAST_REQUEST
        with _ARXIV_LOCK:
            elapsed = time.monotonic() - _ARXIV_LAST_REQUEST
            if elapsed < _ARXIV_MIN_INTERVAL:
                time.sleep(_ARXIV_MIN_INTERVAL - elapsed)
            _ARXIV_LAST_REQUEST = time.monotonic()
            return self._client.request_text(
                self.record_id,
                "query",
                params={
                    "search_query": f"{field}:{query}",
                    "start": start,
                    "max_results": max_results,
                    "sortBy": sort_by,
                    "sortOrder": sort_order,
                },
                headers={"Accept": "application/atom+xml"},
                retries=0,
            )


class OpenAlexConnector(APIConnector):
    def search_works(self, query: str, *, per_page: int = 10) -> Any:
        if not query.strip():
            raise ValueError("query must not be empty")
        if isinstance(per_page, bool) or not 1 <= per_page <= 100:
            raise ValueError("per_page must be between 1 and 100")
        return self.get_json("works", params={"search": query, "per-page": per_page})


class CrossrefConnector(APIConnector):
    def search_works(self, query: str, *, rows: int = 10) -> Any:
        if not query.strip():
            raise ValueError("query must not be empty")
        if isinstance(rows, bool) or not 0 <= rows <= 1000:
            raise ValueError("rows must be between 0 and 1000")
        return self.get_json("works", params={"query.bibliographic": query, "rows": rows})

    def work(self, doi: str) -> Any:
        if not doi.strip():
            raise ValueError("doi must not be empty")
        return self.get_json(f"works/{quote(doi.strip(), safe='')}")


class WorldBankConnector(APIConnector):
    def indicator(self, indicator: str, *, country: str = "all", per_page: int = 50, page: int = 1) -> Any:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", indicator):
            raise ValueError("indicator contains unsupported path characters")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", country):
            raise ValueError("country contains unsupported path characters")
        if isinstance(per_page, bool) or isinstance(page, bool) or not 1 <= per_page <= 1000 or page < 1:
            raise ValueError("per_page must be 1..1000 and page must be positive")
        return self.get_json(
            f"country/{country}/indicator/{indicator}",
            params={"format": "json", "per_page": per_page, "page": page},
        )


class FrankfurterConnector(APIConnector):
    def rate(self, base: str, quote: str, *, date: str | None = None, provider: str | None = None) -> Any:
        for code in (base, quote):
            if not re.fullmatch(r"[A-Za-z]{3}", code):
                raise ValueError("base and quote must be three-letter currency/asset codes")
        params: dict[str, Any] = {}
        if date is not None:
            if not isinstance(date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                raise ValueError("date must use YYYY-MM-DD")
            try:
                date_type.fromisoformat(date)
            except ValueError:
                raise ValueError("date must be a valid calendar date in YYYY-MM-DD form") from None
            params["date"] = date
        if provider:
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", provider):
                raise ValueError("provider contains unsupported characters")
            params["providers"] = provider
        return self.get_json(f"v2/rate/{base.lower()}/{quote.lower()}", params=params)


class USGSConnector(APIConnector):
    def earthquakes(
        self,
        *,
        starttime: str,
        endtime: str,
        minmagnitude: float | None = None,
        limit: int = 100,
    ) -> Any:
        if not starttime or not endtime:
            raise ValueError("starttime and endtime are required")
        if isinstance(limit, bool) or not 1 <= limit <= 20000:
            raise ValueError("limit must be between 1 and 20000")
        params: dict[str, Any] = {
            "format": "geojson",
            "starttime": starttime,
            "endtime": endtime,
            "limit": limit,
        }
        if minmagnitude is not None:
            params["minmagnitude"] = minmagnitude
        return self.get_json("query", params=params)


class OSVConnector(APIConnector):
    def query_package(self, name: str, ecosystem: str, version: str) -> Any:
        if not name.strip() or not ecosystem.strip() or not version.strip():
            raise ValueError("name, ecosystem, and version are required")
        return self.post_json(
            "query",
            {"package": {"name": name, "ecosystem": ecosystem}, "version": version},
        )


_NOMINATIM_LOCK = threading.Lock()
_NOMINATIM_LAST_REQUEST = 0.0
_NOMINATIM_MIN_INTERVAL = 1.1


class NominatimConnector(APIConnector):
    """Policy-conscious wrapper for the public OSMF Nominatim service.

    The process-wide lock serializes public lookups at >=1.1 seconds between
    request starts. Applications remain responsible for the global limit,
    caching, attribution, and policy compliance across processes and hosts.
    """

    def __init__(
        self,
        client: APIClient,
        record_id: str,
        *,
        acknowledge_policy: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(client, record_id, **kwargs)
        if not acknowledge_policy:
            raise ValueError("Read the Nominatim policy and pass acknowledge_policy=True before use")
        user_agent = self._client.user_agent.strip()
        if (
            user_agent == "divyesh-api-mind/0.1.0"
            or len(user_agent) < 10
            or not any(char in user_agent for char in "/ ")
        ):
            raise CredentialError("Pass an application-identifying user_agent to APIMind for Nominatim")

    def get_json(self, path: str = "", *, params: dict[str, Any] | None = None) -> Any:
        raise UnsafeRequestError("Use NominatimConnector.search() or reverse() to preserve public-service policy limits")

    def get_text(self, path: str = "", *, params: dict[str, Any] | None = None) -> str:
        raise UnsafeRequestError("Use NominatimConnector.search() or reverse() to preserve public-service policy limits")

    def get_raw(self, path: str = "", *, params: dict[str, Any] | None = None) -> HTTPResult:
        raise UnsafeRequestError("Use NominatimConnector.search() or reverse() to preserve public-service policy limits")

    def post_json(self, path: str, payload: Any, *, params: dict[str, Any] | None = None) -> Any:
        raise UnsafeRequestError("The public Nominatim connector only permits rate-limited read lookups")

    def post_form(self, path: str, fields: dict[str, Any], *, params: dict[str, Any] | None = None) -> Any:
        raise UnsafeRequestError("The public Nominatim connector only permits rate-limited read lookups")

    def _limited_lookup(self, path: str, params: dict[str, Any]) -> Any:
        global _NOMINATIM_LAST_REQUEST
        with _NOMINATIM_LOCK:
            elapsed = time.monotonic() - _NOMINATIM_LAST_REQUEST
            if elapsed < _NOMINATIM_MIN_INTERVAL:
                time.sleep(_NOMINATIM_MIN_INTERVAL - elapsed)
            _NOMINATIM_LAST_REQUEST = time.monotonic()
            return self._client.request_json(self.record_id, path, params=params, retries=0)

    def search(self, query: str, *, limit: int = 5) -> Any:
        if not query.strip():
            raise ValueError("query must not be empty")
        if isinstance(limit, bool) or not 1 <= limit <= 10:
            raise ValueError("limit must be between 1 and 10")
        return self._limited_lookup("search", {"q": query, "format": "jsonv2", "limit": limit})

    def reverse(self, latitude: float, longitude: float) -> Any:
        if (
            isinstance(latitude, bool)
            or isinstance(longitude, bool)
            or not isinstance(latitude, (int, float))
            or not isinstance(longitude, (int, float))
            or not math.isfinite(latitude)
            or not math.isfinite(longitude)
            or not -90 <= latitude <= 90
            or not -180 <= longitude <= 180
        ):
            raise ValueError("latitude must be finite and -90..90; longitude must be finite and -180..180")
        return self._limited_lookup(
            "reverse",
            {"lat": latitude, "lon": longitude, "format": "jsonv2"},
        )
