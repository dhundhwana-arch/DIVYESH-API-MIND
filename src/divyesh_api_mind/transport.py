"""Small, dependency-free HTTPS transport with bounded retries and safe errors."""

from __future__ import annotations

import ipaddress
import logging
import re
import socket
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Callable, Mapping

from .exceptions import APIError, UnsafeRequestError

_LOG = logging.getLogger("divyesh_api_mind.http")
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_PROTECTED_HEADERS = {
    "host",
    "cookie",
    "set-cookie",
    "proxy-authorization",
    "content-length",
    "transfer-encoding",
    "connection",
    "proxy-connection",
    "upgrade",
    "te",
    "trailer",
}
_HEADER_NAME = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
_LOCAL_SUFFIXES = (".local", ".localhost", ".internal", ".test", ".invalid")
_PATH_SAFE = "/%:@!$&'()*+,;=-._~"


@dataclass(frozen=True)
class HTTPResult:
    """A successful HTTP response with an explicitly bounded body."""

    status_code: int
    headers: Mapping[str, str]
    body: bytes


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Do not forward authorization to an unreviewed redirect destination."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def _normalise_hostname(host: str) -> str:
    if not isinstance(host, str) or not host:
        raise UnsafeRequestError("Request URL must include a valid host")
    try:
        return host.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError:
        raise UnsafeRequestError("Request URL contains an invalid hostname") from None


def _validate_public_hostname(host: str) -> str:
    normalised = _normalise_hostname(host)
    if (
        normalised in {"localhost", "localhost.localdomain"}
        or normalised.endswith(_LOCAL_SUFFIXES)
        or "." not in normalised and not _is_global_ip(normalised)
    ):
        raise UnsafeRequestError("Local and internal network destinations are blocked")
    if not _is_global_ip(normalised):
        try:
            ipaddress.ip_address(normalised.strip("[]"))
        except ValueError:
            pass
        else:
            raise UnsafeRequestError("Private and non-global IP destinations are blocked")
    return normalised


def _is_global_ip(host: str) -> bool:
    try:
        address = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        return False
    return address.is_global


def _parsed_https_url(url: str):
    if not isinstance(url, str) or any(ord(char) < 32 or ord(char) == 127 for char in url):
        raise UnsafeRequestError("Request URL must be valid HTTPS text")
    try:
        parsed = urllib.parse.urlsplit(url)
        port = parsed.port
    except ValueError:
        raise UnsafeRequestError("Request URL is malformed") from None
    if (
        parsed.scheme.lower() != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
        or parsed.fragment
    ):
        raise UnsafeRequestError("Only credential-free HTTPS URLs on the default port are allowed")
    host = _validate_public_hostname(parsed.hostname)
    return parsed, host


def _check_relative_path(path: str) -> str:
    if not isinstance(path, str):
        raise UnsafeRequestError("API path must be relative text")
    if any(ord(char) < 32 or ord(char) == 127 for char in path):
        raise UnsafeRequestError("Control characters are not allowed in an API path")
    if any(char in path for char in "\\?#") or "://" in path:
        raise UnsafeRequestError("API paths cannot contain a URL, query, fragment, or backslash")
    decoded_path = urllib.parse.unquote(path)
    if any(ord(char) < 32 or ord(char) == 127 for char in decoded_path) or "\\" in decoded_path:
        raise UnsafeRequestError("Encoded controls and backslashes are not allowed in an API path")
    if decoded_path.startswith("//") or any(segment == ".." for segment in decoded_path.split("/")):
        raise UnsafeRequestError("Absolute and parent-directory paths are not allowed")
    return path


def build_url(
    base_url: str,
    path: str = "",
    params: Mapping[str, object] | None = None,
    *,
    allowed_hosts: set[str] | frozenset[str] | tuple[str, ...] | list[str],
) -> str:
    """Join a relative API path to an allowlisted, public HTTPS origin.

    Query credentials are URL-encoded like any other parameter and are never
    included in this module's logs or exceptions.
    """
    base, host = _parsed_https_url(base_url)
    if base.query or base.fragment:
        raise UnsafeRequestError("Catalog base URLs cannot contain a query or fragment")
    if host not in {_normalise_hostname(item) for item in allowed_hosts}:
        raise UnsafeRequestError("Catalog origin is not in the API host allowlist")
    _check_relative_path(path)

    base_path = urllib.parse.quote(base.path.rstrip("/"), safe=_PATH_SAFE)
    relative_path = urllib.parse.quote(path.lstrip("/"), safe=_PATH_SAFE)
    joined_path = base_path + ("/" + relative_path if relative_path else "")

    clean_params: dict[str, object] = {}
    for key, value in (params or {}).items():
        if not isinstance(key, str) or not key or any(ord(char) < 32 or ord(char) == 127 for char in key):
            raise UnsafeRequestError("Invalid query parameter name")
        if value is None:
            continue
        values = value if isinstance(value, (list, tuple)) else (value,)
        filtered = [item for item in values if item is not None]
        if any(any(ord(char) < 32 or ord(char) == 127 for char in str(item)) for item in filtered):
            raise UnsafeRequestError("Control characters are not allowed in query parameters")
        if not filtered:
            continue
        clean_params[key] = filtered if isinstance(value, (list, tuple)) else filtered[0]

    query = urllib.parse.urlencode(clean_params, doseq=True)
    netloc = f"[{host}]" if ":" in host else host
    return urllib.parse.urlunsplit(("https", netloc, joined_path or "/", query, ""))


def _normal_headers(headers: Mapping[str, object] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for name, value in (headers or {}).items():
        name = str(name)
        text = str(value)
        if (
            not _HEADER_NAME.fullmatch(name)
            or any((ord(char) < 32 and char != "\t") or ord(char) == 127 for char in text)
        ):
            raise UnsafeRequestError("Invalid HTTP header")
        if name.lower() in _PROTECTED_HEADERS:
            raise UnsafeRequestError(f"The {name} header is managed by the transport")
        result[name] = text
    return result


def _retry_after_seconds(value: str | None, now: datetime | None = None) -> float | None:
    if not value:
        return None
    try:
        return max(0.0, float(value.strip()))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            current = now or datetime.now(timezone.utc)
            return max(0.0, (parsed - current).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None


def _has_header(headers: Mapping[str, str], name: str) -> bool:
    return any(key.lower() == name.lower() for key in headers)


class SafeHTTPTransport:
    """HTTPS-only transport with bounded retries and sanitized failures.

    Redirects are deliberately rejected so credentials cannot be forwarded to
    an unreviewed destination. Only GET/HEAD are retried automatically. A
    caller may lower the retry count for a provider with a stricter cadence.
    """

    def __init__(
        self,
        *,
        timeout: float = 10.0,
        retries: int = 2,
        backoff_seconds: float = 0.25,
        max_retry_after: float = 30.0,
        max_response_bytes: int = 5 * 1024 * 1024,
        user_agent: str = "divyesh-api-mind/0.1.0",
        opener=None,  # noqa: ANN001 - injectable for deterministic tests
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if timeout <= 0 or retries < 0 or max_response_bytes <= 0:
            raise ValueError("timeout and response size must be positive; retries cannot be negative")
        self.timeout = timeout
        self.retries = retries
        self.backoff_seconds = max(0.0, backoff_seconds)
        self.max_retry_after = max(0.0, max_retry_after)
        self.max_response_bytes = max_response_bytes
        self.user_agent = user_agent
        self._sleep = sleep
        self._opener = opener or urllib.request.build_opener(
            _NoRedirect(),
            urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        )

    def request(
        self,
        record_id: str,
        method: str,
        url: str,
        *,
        allowed_hosts: set[str] | frozenset[str] | tuple[str, ...] | list[str],
        headers: Mapping[str, object] | None = None,
        body: bytes | None = None,
        retries: int | None = None,
        max_response_bytes: int | None = None,
    ) -> HTTPResult:
        if not isinstance(method, str):
            raise UnsafeRequestError("HTTP method must be text")
        method = method.upper()
        if method not in {"GET", "HEAD", "POST"}:
            raise UnsafeRequestError("Only GET, HEAD, and POST are supported")
        if body is not None and not isinstance(body, bytes):
            raise UnsafeRequestError("HTTP request body must be bytes")
        if body is not None and method != "POST":
            raise UnsafeRequestError("Request bodies are only supported for POST")
        retry_count = self.retries if retries is None else retries
        if not isinstance(retry_count, int) or retry_count < 0:
            raise ValueError("retries must be a non-negative integer")
        response_limit = self.max_response_bytes if max_response_bytes is None else max_response_bytes
        if (
            isinstance(response_limit, bool)
            or not isinstance(response_limit, int)
            or not 1 <= response_limit <= self.max_response_bytes
        ):
            raise ValueError("max_response_bytes must be positive and cannot exceed the transport limit")

        parsed, host = _parsed_https_url(url)
        if host not in {_normalise_hostname(item) for item in allowed_hosts}:
            raise UnsafeRequestError("Request URL is outside the HTTPS host allowlist")
        _check_relative_path(urllib.parse.unquote(parsed.path))

        request_headers = _normal_headers(headers)
        if not _has_header(request_headers, "Accept"):
            request_headers["Accept"] = "application/json"
        if not _has_header(request_headers, "User-Agent"):
            request_headers["User-Agent"] = self.user_agent
        request = urllib.request.Request(url, data=body, headers=request_headers, method=method)
        may_retry = method in {"GET", "HEAD"}
        max_attempts = 1 + (retry_count if may_retry else 0)

        for attempt in range(1, max_attempts + 1):
            try:
                with self._opener.open(request, timeout=self.timeout) as response:
                    response_status = getattr(response, "status", None)
                    status = int(response_status if response_status is not None else response.getcode())
                    response_headers = {str(key).lower(): str(value) for key, value in response.headers.items()}
                    content_length = response_headers.get("content-length")
                    if content_length:
                        try:
                            if int(content_length) > response_limit:
                                raise APIError(record_id, "Response exceeds configured size limit", status_code=status)
                        except ValueError:
                            pass
                    body_bytes = response.read(response_limit + 1)
                    if len(body_bytes) > response_limit:
                        raise APIError(record_id, "Response exceeds configured size limit", status_code=status)
                    return HTTPResult(status, response_headers, body_bytes)
            except urllib.error.HTTPError as exc:
                status = int(exc.code)
                response_headers = {str(key).lower(): str(value) for key, value in (exc.headers or {}).items()}
                retry_after = _retry_after_seconds(response_headers.get("retry-after"))
                retryable = status in _RETRYABLE_STATUS and may_retry
                if retryable and attempt < max_attempts:
                    delay = retry_after if retry_after is not None else self.backoff_seconds * (2 ** (attempt - 1))
                    if delay <= self.max_retry_after:
                        _LOG.warning("Transient HTTP failure for %s (status=%s, attempt=%s)", record_id, status, attempt)
                        try:
                            exc.close()
                        except Exception:  # noqa: BLE001 - best-effort cleanup only
                            pass
                        self._sleep(delay)
                        continue
                try:
                    exc.close()
                except Exception:  # noqa: BLE001 - best-effort cleanup only
                    pass
                raise APIError(
                    record_id,
                    f"HTTP request failed for {record_id} (status {status})",
                    status_code=status,
                    retryable=status in _RETRYABLE_STATUS,
                    attempts=attempt,
                    retry_after=retry_after,
                ) from None
            except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError, OSError) as exc:
                retryable = may_retry
                if retryable and attempt < max_attempts:
                    delay = self.backoff_seconds * (2 ** (attempt - 1))
                    _LOG.warning("Transient network failure for %s (attempt=%s)", record_id, attempt)
                    self._sleep(delay)
                    continue
                # Do not stringify URLError: its reason can contain a URL or other detail.
                reason_name = type(getattr(exc, "reason", exc)).__name__
                raise APIError(
                    record_id,
                    f"Network request failed for {record_id} ({reason_name})",
                    retryable=retryable,
                    attempts=attempt,
                ) from None

        raise APIError(record_id, f"Request failed for {record_id}", attempts=max_attempts)
