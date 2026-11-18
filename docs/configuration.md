# Configuration

DIVYESH API MIND intentionally has no implicit `.env`, TOML, YAML, or remote configuration loader. The bundled catalog is local JSON. API credentials are read only from environment variables named on the corresponding record; no credential values belong in this repository.

## Python options

```python
from pathlib import Path
from divyesh_api_mind import APIMind, IntelligenceHub, SafeHTTPTransport

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

## Unified offline intelligence

```python
from divyesh_api_mind import IntelligenceHub

hub = IntelligenceHub()  # local catalogs only; no provider or MCP calls
matches = hub.search(capability="scholarly", access="FREE", include_discovery=True)
ranked = hub.recommend(capability="coding", limit=5)
print(hub.explain(ranked))
```

`IntelligenceHub` keeps `ACCEPTED_CATALOG`, `MCP_METADATA`, and `DISCOVERY_ONLY` provenance in each result. Unknown values do not count as “no”; unspecified quotas do not count as unlimited. `access="FREE"` excludes free-data/paid-service, paid, and unknown records. Scores are documentary heuristics; fallback IDs never trigger automatic substitutions. Use `include_discovery=False` or `--accepted-only` when you only want accepted API/model/dataset records (MCP metadata is still labeled separately).

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

## Optional encrypted local vault

Install the optional crypto dependency with `python -m pip install '.[security]'`. The CLI prompts without echo and never accepts a secret value on its command line:

```bash
apimind vault --path "$HOME/.config/divyesh-api-mind/keys.vault" set OPENALEX_API_KEY
apimind vault --path "$HOME/.config/divyesh-api-mind/keys.vault" list
apimind config-check --use-vault --vault-path "$HOME/.config/divyesh-api-mind/keys.vault"
```

For Python, obtain a passphrase through an appropriate hidden prompt or OS secret manager, then pass the decrypted mapping explicitly. Do not log the mapping:

```python
from getpass import getpass
from divyesh_api_mind import APIMind, KeyVault

vault = KeyVault()  # or KeyVault("/path/to/keys.vault")
api_mind = APIMind(env=vault.environment(getpass("Vault passphrase: ")))
```

The vault is optional local storage, not a production secret manager. A lost passphrase is unrecoverable. `KeyVault.environment()` returns secret values to the caller by design; the caller owns memory/logging safety.

`.env` files are never auto-loaded. `apimind config-check --env-file PATH` uses a restricted non-executing parser; shell environment overrides file/vault values. It reports only variable names and presence. Explicit `--use-vault` unlocks the vault for a presence check; it does not expose values.

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
- `apimind research-discover-github` (explicit invocation only) fetches public GitHub repository metadata from `api.github.com`, at most 25 targets per run. It does not call a provider product/API, does not follow redirects, and creates only UNKNOWN discovery leads. Rate-limit/authorization responses are not retried or bypassed.
- A Python connector or `APIMind.request*` call sends a provider request only when explicitly invoked.
- `apimind local-ollama-list` and `local-ollama-chat` contact only the explicitly configured fixed `127.0.0.1:11434` process. They do not download/start a model or route to a hosted provider. A chat prompt is sent to the user's local Ollama process.

The GitHub command takes a local JSON target list. Example shape (the tags are editorial categories, not verified claims):

```json
{
  "schema_version": "1.0",
  "targets": [
    {
      "repo": "modelcontextprotocol/servers",
      "kind": "mcp_reference_repository",
      "categories": ["mcp", "agents", "developer-tools"],
      "capabilities": ["reference server examples", "tool protocol"]
    }
  ]
}
```

Use a separate output such as `technology_discovery.json`; accepted catalogs and historical review artifacts are protected. Add a separately reviewed source snapshot using `research-evidence-add`, then record claim decisions in the separate `technology_research_reviews.json` hash chain with `research-review-claim`. Neither action edits accepted catalog claims or promotes records. For research details and CLI arguments, see [`research/mission-09-implementation-report.md`](research/mission-09-implementation-report.md).

For local AI, `apimind local-hardware --model-size-gib N` provides only a rough RAM estimate; GPU/VRAM and runtime compatibility remain unknown. Review official model/runtime requirements before installing anything.

Before production use, review [`security.md`](security.md), [`connectors.md`](connectors.md), and the provider's current terms and policy.
