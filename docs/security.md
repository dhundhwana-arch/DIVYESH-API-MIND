# Security and privacy notes

This package is a client for explicit user-directed calls; it is not a sandbox, credential vault, proxy, or security audit. Read the provider's policies before sending requests.

## Network boundaries

No network call is made by package import, catalog construction, local search, documentation-reference lookup (`get_docs`), validation, CLI summary, or MCP directory browsing. `APIMind.fetch_docs`/`apimind docs --fetch`, `health_check`, `discover-import --url`, `APIMind.request*`, and typed connector methods send requests only when explicitly invoked.

The shared transport accepts only HTTPS on the default port, checks the final hostname against the API record's allowlist, rejects URL user-info and local/private IP destinations, and does not follow redirects. API paths are relative; control characters, backslashes, absolute-URL forms, and parent-directory segments are rejected. These checks reduce accidental host/path escape, but they are not a DNS-pinning or network sandbox. Use trusted catalog data and appropriate egress controls for high-risk applications.

Responses are capped at 5 MiB by default and requests time out after 10 seconds. Configure `SafeHTTPTransport(timeout=..., retries=..., max_response_bytes=...)` for a provider's documented response size and latency. GET/HEAD may retry selected transient failures; POST is not retried. A GET endpoint can still have provider-specific side effects, so review methods and parameters.

## Credentials

The client reads secrets only from the environment-variable names in the API record. Caller-supplied authentication headers and direct authentication query parameters are rejected. Do not place credentials in catalog JSON, source URLs, request paths, exception text, or application logs.

Some providers require query-string keys. The library URL-encodes them and does not log request URLs, but the provider, proxies, and server access logs may still see query values. Restrict access to logs and prefer header-based auth when supported. Environment variables are not a full secrets-management system; use your deployment platform's secret store for production.

The transport avoids logging URLs, headers, request bodies, and response bodies. Error messages contain the catalog record id, status (when available), and a sanitized error category. Avoid adding debug handlers that print `urllib.request.Request` objects, since those can include query credentials.

## Privacy and external services

When a request is sent, the provider receives its query/body, network metadata, and possibly the configured API key or application-identifying User-Agent. Search strings, coordinates, CVE/package data, and model prompts can be sensitive. Do not send personal, confidential, unpublished, or security-sensitive content unless permitted by the provider and your organization.

The local library does not persist API responses or prompts. That statement does not describe the remote provider's retention, abuse monitoring, or downstream model-provider terms. In particular, routed AI providers can have different data-retention rules per model/provider and account plan; review current terms and controls before sending sensitive content.

## Public-service policy guards

- **Nominatim:** direct generic requests are blocked. Use `NominatimConnector` with `acknowledge_policy=True` and an identifying `user_agent`. The connector serializes lookups with a 1.1-second start interval inside one process and disables retries. This cannot coordinate across processes, hosts, or unrelated applications. The operator remains responsible for the public service's aggregate limit, caching, attribution, no-autocomplete rule, and all other policy requirements. Do not use the public endpoint for bulk or confidential geocoding.
- **arXiv:** direct generic calls are blocked. `ArxivConnector.search` serializes calls with a 3.1-second interval inside one process and disables retries. Coordinate other processes/machines under your control to stay within arXiv's stated limit.

The Python-level guards can be bypassed by deliberately using private internals or another HTTP client. They are guardrails against accidental policy violations, not enforcement against a malicious caller.

## Documentation and discovery fetches

Documentation retrieval is restricted to a URL already present in the selected record's source/endpoint references. It sends an unauthenticated GET, strips a fragment, refuses query credentials and redirects, and applies a per-request response cap (512 KiB by default; callers may lower it up to 1 MiB). Discovery URL imports are an explicit opt-in and are separate from catalog use: they accept one credential-free HTTPS URL, reject non-global IP/local destinations, refuse redirects, use no API key, and cap downloads at 2 MiB by default. GitHub Contents API base64 payloads are decoded under the same decoded-size limit. Remote source data is untrusted input; imports remain review candidates and are never executed or promoted automatically.

The hostname guard is not DNS pinning or a network sandbox; apply egress controls when importing untrusted URLs in sensitive environments. Prefer a pinned commit URL and verify source licenses before retaining or redistributing imported data.

## MCP metadata

`MCPRegistry` reads JSON metadata only. It does not install, launch, initialize, or call any MCP server. A registry status such as `active` is not an uptime, code-quality, privacy, or security signal. Review server source, publisher identity, dependency chain, requested permissions, and data handling independently before connecting it to tools or credentials.
