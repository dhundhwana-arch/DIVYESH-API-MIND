# Configuration

DIVYESH API MIND intentionally has no implicit `.env`, TOML, YAML, or remote configuration loader. The bundled catalog is local JSON. API credentials are read only from environment variables named on the corresponding record; no credential values belong in this repository.

## Python options

```python
from pathlib import Path
from divyesh_api_mind import APIMind, SafeHTTPTransport

transport = SafeHTTPTransport(
    timeout=8.0,                 # per attempt
    retries=1,                   # GET/HEAD only; POST is never retried
    max_response_bytes=1_000_000,
)
mind = APIMind(
    catalog_dir=Path("./my-reviewed-catalog"),  # omit to use bundled data
    transport=transport,
    user_agent="ExampleResearchTool/1.0 (contact: dev@example.org)",
)
```

Use a descriptive, truthful User-Agent and follow the selected provider's identification requirements. Nominatim additionally requires explicit policy acknowledgement and uses the supplied User-Agent; arXiv and Nominatim wrappers apply process-local request pacing. Their limits still apply across the operator's other processes and machines.

`SafeHTTPTransport` defaults to a 10-second timeout, 2 retries for selected transient GET/HEAD failures, and a 5 MiB response cap. Lower these limits if the provider or task requires it. Retries can wait on `Retry-After` up to the configured cap. Set `retries=0` for one-shot probes. Redirects are refused.

## Credentials

First inspect the selected record's auth metadata:

```bash
apimind search --kind api --query "openalex"
apimind export openalex --format json
```

Then set only the environment variable(s) documented on that record. For example:

```bash
export CENSUS_API_KEY="<your key>"
export NASA_API_KEY="<your key>"
```

Do not put real values in shell history, notebooks, `.env` files shared with others, URLs, catalogs, logs, or generated templates. Query-string auth can appear in provider/proxy logs even when this library redacts errors. Optional authentication does not imply that a service or its free tier is unlimited.

A discovery candidate with `authentication.kind="unknown"` or `verified=false` cannot be called by `APIClient`; verify the official auth documentation and replace the candidate with a reviewed catalog record first.

## Alternate catalogs

A custom catalog directory must contain all four files: `apis.json`, `models.json`, `datasets.json`, and `mcp_registry.json`. Validate before use:

```bash
apimind validate --catalog-dir ./my-reviewed-catalog
```

The catalog directory is data, not executable configuration. Do not accept untrusted edits without reviewing URLs, auth, license, provider terms, rate limits, endpoint methods, and record evidence.

## Explicit network commands

Local search, export, template generation, queue browsing, validation, and MCP metadata inspection do not contact providers. These commands are opt-in network operations:

- `apimind docs API_ID --fetch` fetches one recorded documentation URL, unauthenticated, without redirects, and with a body-size cap.
- `apimind health-check API_ID` sends the record's configured read-only probe.
- `apimind discover-import --url HTTPS_URL ...` fetches one explicitly named public source over HTTPS; it refuses redirects and limits response size.
- A Python connector or `APIMind.request*` call sends a provider request only when explicitly invoked.

Before production use, review [`security.md`](security.md), [`connectors.md`](connectors.md), and the provider's current terms and policy.
