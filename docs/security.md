# Security and privacy notes

This package is a client for explicit user-directed calls; it is not a sandbox, production secret manager, proxy, or security audit. It includes an optional passphrase-encrypted local vault, but that feature does not change this production-security boundary. Read the provider's policies before sending requests.

## Network boundaries

No network call is made by package import, catalog construction, local search, documentation-reference lookup (`get_docs`), validation, CLI summary, or MCP directory browsing. `APIMind.fetch_docs`/`apimind docs --fetch`, `health_check`, `discover-import --url`, `research-discover-github`, `APIMind.request*`, and typed connector methods send requests only when explicitly invoked. `local-ollama-list` and `local-ollama-chat` are explicit loopback requests, not hosted-service calls.

The shared transport accepts only HTTPS on the default port, checks the final hostname against the API record's allowlist, rejects URL user-info and local/private IP literals, and does not follow redirects. API paths are relative; control characters, backslashes, absolute-URL forms, and parent-directory segments are rejected. The default urllib opener may honor configured environment proxies, which can observe request metadata and query-string credentials; assess proxy trust and prefer header authentication when supported. Hostname resolution is not pinned, so these checks are not a DNS-rebinding defense or network sandbox. Use trusted catalog data and appropriate egress controls for high-risk applications.

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

## Research metadata and human review

`research-discover-github` is an explicit public metadata read against the fixed `api.github.com` host. Each run is capped at 25 repositories, uses no credentials, disables environment proxies, refuses redirects, limits response bytes/time, and performs no retries. It reads repository metadata only; it does not call a product API, fetch provider docs, execute repository code, or establish pricing, quotas, API authentication, license rights, security, or operational availability. GitHub rate-limit and access-control responses are surfaced, not bypassed. Do not submit private repository names or other sensitive research targets if that disclosure is not acceptable.

`research-evidence-add` records a source URL and a user-supplied observation snapshot; it does not fetch or authenticate the source itself. Verify the source and its scope independently. SHA-256 makes the snapshot content addressable but does not prove source authenticity or reviewer identity. `research-review-claim` writes a separate append-only event hash chain and never changes an accepted record. The chain is tamper-evident only while a trusted copy/hash is retained; it is not signed, encrypted, or a substitute for protected backups. Discovery records and review ledgers remain user-controlled JSON and may contain public text, so inspect them before sharing.

## Optional encrypted local key vault

The optional `.[security]` extra supplies `cryptography`. The vault encrypts a JSON key map with AES-256-GCM and a scrypt-derived key from a user-provided passphrase. It uses bounded files, authenticated encryption, temporary-file replacement, and restrictive POSIX directory/file modes; symlink checks reduce accidental path redirection. The master passphrase is never stored or printed by CLI commands. A forgotten passphrase cannot be recovered.

This is not a hardware-backed key store, OS keychain integration, cloud secret manager, audited key-rotation service, or defense against a compromised user account, process, kernel, or same-user malware. Filesystem race conditions and platform-specific ACL semantics still require review. Python callers explicitly receive decrypted strings through `KeyVault.get`/`environment`; Python cannot reliably zero all immutable string copies. Do not log values, put them on command lines, commit the vault, or use this as the only production secret-control layer. Use a deployment secret manager for production.

The `.env` parser accepts a restricted subset only when explicitly asked to load a path. It does not execute shell code, expand `$VARS`, or auto-load a file. `config-check` displays variable names/presence and never displays credential values; names can still reveal configuration information.

## Local AI and hardware inventory

`detect_hardware` performs local CPU/RAM/disk reads only; it does not query GPU utilities or contact a service. Container/cgroup limits, usable RAM, GPU/VRAM, model quantization, context cache, drivers, speed, and compatibility may be unknown. The memory estimate is a low-confidence heuristic, not a fit test.

`OllamaLocalClient` accepts only `http://127.0.0.1:11434`, disables HTTP proxies, refuses redirects, and bounds payload/response sizes and timeouts. It will not install, pull, start, or switch to a hosted model. An explicit chat request sends the prompt to the local Ollama process; that process may retain logs or telemetry according to its own configuration. Review it before sending sensitive prompts. No Ollama endpoint was contacted in the Mission 09 test run; all transport behavior is tested with mocks.
