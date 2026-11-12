"""Typed exceptions used by the API Mind library."""

from __future__ import annotations


class APIMindError(Exception):
    """Base class for expected library errors."""


class CatalogError(APIMindError):
    """Raised when catalog data is malformed or inconsistent."""


class UnknownRecordError(APIMindError, KeyError):
    """Raised when a requested catalog record does not exist."""


class CredentialError(APIMindError):
    """Raised when a required environment-based credential is missing."""


class UnsafeRequestError(APIMindError):
    """Raised when a request would leave its HTTPS host allowlist."""


class HealthCheckUnavailable(APIMindError):
    """Raised when a record has no documented, safe health probe."""


class APIError(APIMindError):
    """Sanitized HTTP/network failure; never includes request URLs or bodies."""

    def __init__(
        self,
        record_id: str,
        message: str,
        *,
        status_code: int | None = None,
        retryable: bool = False,
        attempts: int = 1,
        retry_after: float | None = None,
    ) -> None:
        self.record_id = record_id
        self.status_code = status_code
        self.retryable = retryable
        self.attempts = attempts
        self.retry_after = retry_after
        super().__init__(message)
