# Connectors and explicit requests

`APIMind` loads local catalogs and creates connector objects without connecting. A provider is contacted only when a connector method, `request*` method, or configured health probe is invoked.

## Typed connectors

| API id | Connector method | Return type / note |
| --- | --- | --- |
| `openalex` | `search_works(query, per_page=10)` | Parsed JSON |
| `crossref` | `search_works(query, rows=10)`, `work(doi)` | Parsed JSON |
| `world-bank-indicators` | `indicator(indicator, country="all", per_page=50, page=1)` | Parsed JSON; `format=json` is set |
| `frankfurter` | `rate(base, quote, date=None, provider=None)` | Parsed JSON |
| `usgs-earthquakes` | `earthquakes(starttime, endtime, minmagnitude=None, limit=100)` | Parsed GeoJSON |
| `osv` | `query_package(name, ecosystem, version)` | Parsed JSON; sends a POST |
| `arxiv` | `search(query, field="all", start=0, max_results=10, ...)` | Atom XML as text; per-process request spacing is enforced |
| `nominatim` | `search(query, limit=5)`, `reverse(latitude, longitude)` | Parsed JSON; requires acknowledgement, identifying User-Agent, and per-process spacing |

Example:

```python
from divyesh_api_mind import APIMind

mind = APIMind()
works = mind.connector("crossref").search_works("urban heat Ahmedabad", rows=5)
indicators = mind.connector("world-bank-indicators").indicator("SP.POP.TOTL", country="IN", per_page=2)
```

The connectors validate common input bounds and call the shared HTTPS client. They do not promise that a provider, model, identifier, or endpoint is currently available. Records with `authentication.kind="unknown"` or `authentication.verified=false` are blocked before transport until a human verifies the auth scheme.

## Generic requests

For a catalogued API without a typed wrapper, use a relative path beneath that record's base URL. The final hostname must be allowlisted by the catalog.

```python
# Public PyPI project metadata
metadata = mind.request("pypi-json", "pypi/httpx/json")

# The API record declares the auth scheme; the client reads Census key from
# CENSUS_API_KEY and encodes it without accepting a key in params.
acs = mind.request(
    "census-data",
    "2024/acs/acs5",
    params={"get": "NAME,B01001_001E", "for": "state:06"},
)

# Non-JSON response format (arXiv itself has a specialized, rate-limited wrapper)
raw = mind.request_text("wolfram-alpha", "query", params={"input": "integrate x^2"})
```

`APIMind.request` parses JSON. `request_text` decodes a text body as UTF-8 by default; `request_raw` returns `HTTPResult(status_code, headers, body)` with the bounded response bytes. `json_body` sends JSON for POST; `form_body` URL-encodes a form. Choose only the content type and method the provider documents.

Some API records include paid or side-effecting methods. For example, sending a Twilio message can incur charges and contact a real recipient. The library does not add a confirmation prompt; explicitly review the path, payload, credentials, consent, and provider charges before a POST.

## Health probes

`APIMind.health_check(api_id)` only sends a request when the catalog has a read-only `health_probe`. It reports `healthy`, `unhealthy`, or `not_configured`, includes the actual successful HTTP status, and never invents a `200` for another 2xx response. It does not prove full API correctness, account entitlement, quota availability, or production readiness. Most records intentionally have no probe.

`connector.health_check()` delegates to the same safe behavior. A missing probe or missing required key is reported as `not_configured`; network and HTTP errors are sanitized. The one-time live results recorded on 2026-11-12 for GitHub, PyPI, and npm are in [`live-probes.md`](live-probes.md), with exact status codes and UTC timestamps.

## Documentation, templates, alternatives, and export

- `mind.get_docs(id)` lists source and endpoint documentation references without contacting those hosts.
- `mind.fetch_docs(id, source_index=0)` is an explicit unauthenticated GET to a recorded HTTPS reference, with no redirects and a bounded response body. The CLI equivalent is `apimind docs ID --fetch`.
- `mind.integration_template(id)` returns a Python starter that does not call the API until the generated function is invoked. Unknown/unverified authentication blocks template generation.
- `mind.alternatives(id)` ranks local APIs by overlapping capability/category metadata. Results are related candidates, **not** drop-in replacements; check endpoint, auth, terms, quotas, and data compatibility.
- `mind.export_records([id1, id2], format="json"|"csv")` exports only explicitly selected IDs.

These operations remain local except `fetch_docs`; no documentation fetch, health check, or provider request runs during catalog search or validation.
