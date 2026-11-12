"""Policy-aware JSON, text, and raw client for catalogued APIs."""

from __future__ import annotations

import base64
import json
import os
import re
import urllib.parse
from collections.abc import Mapping
from datetime import datetime, timezone
from time import monotonic
from typing import Any

from .exceptions import APIError, CredentialError, HealthCheckUnavailable, UnknownRecordError
from .transport import HTTPResult, SafeHTTPTransport, build_url

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
_SECRET_HEADER_NAMES = frozenset(
    {
        "authorization",
        "proxy-authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "api-key",
        "apikey",
        "api_key",
        "x-goog-api-key",
        "x-auth-token",
        "x-access-token",
        "x-api-token",
    }
)
_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class APIClient:
    """Send bounded HTTPS requests to a catalog record's allowlisted origin.

    Credentials are resolved only from environment variables declared in the
    catalog. Caller-supplied authentication headers and query credentials are
    rejected so they cannot replace or bypass catalogued auth configuration.
    """

    def __init__(
        self,
        records: Mapping[str, dict[str, Any]],
        *,
        transport: SafeHTTPTransport | None = None,
        env: Mapping[str, str] | None = None,
        user_agent: str | None = None,
    ) -> None:
        self._records = records
        self._transport = transport or SafeHTTPTransport(user_agent=user_agent or "divyesh-api-mind/0.1.0")
        self._env = env if env is not None else os.environ
        self.user_agent = user_agent or self._transport.user_agent

    def has_credentials(self, record_id: str) -> bool:
        """Return whether all required catalog credentials are available."""
        record = self._record(record_id)
        auth = record.get("authentication", {})
        if not isinstance(auth, dict):
            return False
        kind = auth.get("kind", "none")
        required = bool(auth.get("required", False))
        if kind not in _AUTH_KINDS or kind == "unknown" or auth.get("verified") is False:
            return False
        names = self._credential_names(auth, kind)
        if not required:
            return True
        return bool(names) and all(bool(self._env.get(name)) for name in names)

    @staticmethod
    def _credential_names(auth: dict[str, Any], kind: str) -> tuple[str, ...]:
        if kind in {
            "bearer",
            "optional_bearer",
            "api_key_header",
            "optional_api_key_header",
            "api_key_query",
        }:
            name = auth.get("env_var")
            return (name,) if isinstance(name, str) and name else ()
        if kind == "http_basic_pair":
            names = (auth.get("username_env"), auth.get("password_env"))
            if all(isinstance(name, str) and name for name in names):
                return names
            return ()
        return ()

    def _record(self, record_id: str) -> dict[str, Any]:
        try:
            return self._records[record_id]
        except KeyError:
            raise UnknownRecordError(f"Unknown API record: {record_id}") from None

    def _auth_headers_and_params(
        self, record_id: str, auth: dict[str, Any], params: dict[str, Any]
    ) -> tuple[dict[str, str], dict[str, Any]]:
        kind = auth.get("kind", "none")
        required = bool(auth.get("required", False))
        if kind not in _AUTH_KINDS:
            raise CredentialError(f"Unsupported authentication scheme in catalog for {record_id}")
        if kind == "unknown" or auth.get("verified") is False:
            raise CredentialError(f"Authentication for {record_id} is unverified; review primary documentation before requests")

        headers: dict[str, str] = {}
        updated_params = dict(params)
        if kind == "none":
            return headers, updated_params

        if kind == "api_key_query":
            parameter = auth.get("parameter", "api_key")
            if not isinstance(parameter, str) or not parameter:
                raise CredentialError(f"Invalid query authentication configuration for {record_id}")
            if parameter in updated_params:
                raise CredentialError(
                    f"Do not supply {parameter} directly; configure the catalog credential in the environment"
                )

        if kind == "http_basic_pair":
            username_env = auth.get("username_env", "")
            password_env = auth.get("password_env", "")
            username = self._env.get(username_env, "") if isinstance(username_env, str) else ""
            password = self._env.get(password_env, "") if isinstance(password_env, str) else ""
            if not username or not password:
                if required:
                    raise CredentialError(
                        f"Set {username_env} and {password_env} in the environment for {record_id}"
                    )
                return headers, updated_params
            raw = f"{username}:{password}".encode("utf-8")
            headers["Authorization"] = "Basic " + base64.b64encode(raw).decode("ascii")
            return headers, updated_params

        env_var = auth.get("env_var")
        if env_var is not None and (not isinstance(env_var, str) or not _ENV_NAME.fullmatch(env_var)):
            raise CredentialError(f"Invalid environment-variable configuration for {record_id}")
        secret = self._env.get(env_var, "") if env_var else ""
        if not secret:
            if required:
                raise CredentialError(
                    f"Set {env_var or 'the required credential'} in the environment for {record_id}"
                )
            return headers, updated_params

        if kind in {"bearer", "optional_bearer"}:
            headers["Authorization"] = f"Bearer {secret}"
        elif kind in {"api_key_header", "optional_api_key_header"}:
            header_name = auth.get("header", "X-API-Key")
            prefix = auth.get("prefix", "")
            if not isinstance(header_name, str) or not header_name:
                raise CredentialError(f"Invalid authentication header in catalog for {record_id}")
            if not isinstance(prefix, str):
                raise CredentialError(f"Invalid authentication prefix in catalog for {record_id}")
            headers[header_name] = f"{prefix}{secret}"
        elif kind == "api_key_query":
            updated_params[parameter] = secret
        return headers, updated_params

    @staticmethod
    def _auth_header_names(auth: dict[str, Any], generated: Mapping[str, str]) -> set[str]:
        names = set(_SECRET_HEADER_NAMES)
        names.update(name.lower() for name in generated)
        kind = auth.get("kind", "none")
        if kind in {"bearer", "optional_bearer", "http_basic_pair"}:
            names.add("authorization")
        if kind in {"api_key_header", "optional_api_key_header"}:
            header_name = auth.get("header", "X-API-Key")
            if isinstance(header_name, str):
                names.add(header_name.lower())
        return names

    @staticmethod
    def _set_default_header(headers: dict[str, str], name: str, value: str) -> None:
        if not any(existing.lower() == name.lower() for existing in headers):
            headers[name] = value

    def _request_response(
        self,
        record_id: str,
        path: str = "",
        *,
        method: str = "GET",
        params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        form_body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        retries: int | None = None,
    ) -> HTTPResult:
        record = self._record(record_id)
        auth = record.get("authentication", {})
        if not isinstance(auth, dict):
            raise CredentialError(f"Invalid authentication configuration for {record_id}")
        auth_headers, request_params = self._auth_headers_and_params(record_id, auth, dict(params or {}))
        caller_headers = dict(headers or {})
        protected_headers = self._auth_header_names(auth, auth_headers)
        if any(str(name).lower() in protected_headers for name in caller_headers):
            raise CredentialError(
                f"Authentication headers for {record_id} are managed by the catalog; use its environment variables"
            )

        merged_headers = dict(auth_headers)
        merged_headers.update(caller_headers)
        self._set_default_header(merged_headers, "User-Agent", self.user_agent)
        base_url = record.get("base_url")
        if not isinstance(base_url, str) or not base_url:
            raise APIError(record_id, f"No callable base URL is configured for {record_id}")
        allowed_hosts = set(record.get("allowed_hosts") or [])
        if not allowed_hosts:
            allowed_hosts = {urllib.parse.urlsplit(base_url).hostname or ""}
        url = build_url(base_url, path, request_params, allowed_hosts=allowed_hosts)

        if not isinstance(method, str):
            raise ValueError("method must be text")
        method = method.upper()
        if json_body is not None and form_body is not None:
            raise ValueError("choose either json_body or form_body, not both")
        body: bytes | None = None
        if json_body is not None:
            if method != "POST":
                raise ValueError("json_body is supported only for POST requests")
            try:
                body = json.dumps(json_body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            except (TypeError, ValueError):
                raise ValueError("json_body must be JSON serializable") from None
            self._set_default_header(merged_headers, "Content-Type", "application/json")
        elif form_body is not None:
            if method != "POST":
                raise ValueError("form_body is supported only for POST requests")
            body = urllib.parse.urlencode(form_body, doseq=True).encode("utf-8")
            self._set_default_header(merged_headers, "Content-Type", "application/x-www-form-urlencoded")

        request_options = {
            "allowed_hosts": allowed_hosts,
            "headers": merged_headers,
            "body": body,
        }
        if retries is not None:
            request_options["retries"] = retries
        response = self._transport.request(record_id, method, url, **request_options)
        if not 200 <= response.status_code < 300:
            raise APIError(
                record_id,
                f"HTTP request failed for {record_id} (status {response.status_code})",
                status_code=response.status_code,
                retryable=response.status_code in {429, 500, 502, 503, 504},
            )
        return response

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
        retries: int | None = None,
    ) -> HTTPResult:
        """Return a bounded raw response after a successful request."""
        return self._request_response(
            record_id,
            path,
            method=method,
            params=params,
            json_body=json_body,
            form_body=form_body,
            headers=headers,
            retries=retries,
        )

    def request_json(
        self,
        record_id: str,
        path: str = "",
        *,
        method: str = "GET",
        params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        form_body: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        retries: int | None = None,
    ) -> Any:
        """Send a bounded JSON request and decode its UTF-8 JSON response."""
        response = self._request_response(
            record_id,
            path,
            method=method,
            params=params,
            json_body=json_body,
            form_body=form_body,
            headers=headers,
            retries=retries,
        )
        if method.upper() == "HEAD" or response.status_code == 204 or not response.body:
            return None
        try:
            return json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise APIError(
                record_id,
                f"Response from {record_id} was not valid UTF-8 JSON",
                status_code=response.status_code,
            ) from None

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
        retries: int | None = None,
    ) -> str:
        """Send a request and decode its response body as text."""
        response = self._request_response(
            record_id,
            path,
            method=method,
            params=params,
            json_body=json_body,
            form_body=form_body,
            headers=headers,
            retries=retries,
        )
        try:
            return response.body.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            raise APIError(
                record_id,
                f"Response from {record_id} could not be decoded as {encoding}",
                status_code=response.status_code,
            ) from None

    def _health_check(self, record_id: str) -> tuple[int, float]:
        """Run a documented, read-only probe and return its real status/latency."""
        record = self._record(record_id)
        probe = record.get("health_probe")
        if not isinstance(probe, dict):
            raise HealthCheckUnavailable(f"No documented safe health probe is configured for {record_id}")
        method = probe.get("method", "GET")
        if method not in {"GET", "HEAD"}:
            raise HealthCheckUnavailable(f"Health probe for {record_id} is not a read-only method")
        started = monotonic()
        response = self._request_response(
            record_id,
            probe.get("path", ""),
            method=method,
            params=probe.get("params", {}),
        )
        return response.status_code, (monotonic() - started) * 1000

    def health_check(self, record_id: str) -> dict[str, Any]:
        """Run a read-only health probe and return a stable, sanitized result."""
        checked_at = datetime.now(timezone.utc).isoformat()
        started = monotonic()
        try:
            status, _elapsed = self._health_check(record_id)
            return {
                "api_id": record_id,
                "status": "healthy" if 200 <= status < 300 else "unhealthy",
                "checked_at": checked_at,
                "latency_ms": round((monotonic() - started) * 1000, 2),
                "http_status": status,
                "error": None,
            }
        except (HealthCheckUnavailable, CredentialError) as exc:
            return {
                "api_id": record_id,
                "status": "not_configured",
                "checked_at": checked_at,
                "latency_ms": None,
                "http_status": None,
                "error": str(exc),
            }
        except APIError as exc:
            return {
                "api_id": record_id,
                "status": "unhealthy",
                "checked_at": checked_at,
                "latency_ms": round((monotonic() - started) * 1000, 2),
                "http_status": exc.status_code,
                "error": str(exc),
            }
