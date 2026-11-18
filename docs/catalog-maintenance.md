# Catalog maintenance policy

The catalog is curated evidence, not an automated claim that an API/model/dataset/MCP server is available or safe. Research in the bundled files was last recorded on **2026-11-12**; recheck changing prices, quotas, terms, model availability, and source pages before relying on them.

## Record types and evidence

- `apis.json`: callable HTTPS service metadata—API base URL, allowed hosts, endpoint descriptions, authentication scheme, access status, quota/rate-limit notes, privacy/CORS/license notes, and optional safe health probe.
- `models.json`: model cards and weights. A public/open-weight record does not imply hosted inference, free compute, unrestricted use, or an OSI-approved license. Gated models must state their access/terms.
- `datasets.json`: data access, license/update notes, and optional references to API ids. A dataset API's terms can differ by product or field; do not infer a blanket redistribution license.
- `mcp_registry.json`: directory/repository metadata with a separate evidence state. `directory_entry` is not code review, `reviewed_repository` is not a security audit, and `working_integration` requires a dated protocol/tool test. No current entry has the last state.

Every source reference should carry a descriptive `title`, HTTPS `url`, and ISO `checked_on` date. Evidence labels currently distinguish primary direct pages, official search-result snippets, secondary references, and failed fetches. Do not upgrade a claim based on an inaccessible source or a marketing page. The India OGD mandi record is deliberately marked `discovery_only` with low confidence because the official portal could not be fetched during the review; it is not a callable integration.

`last_verified` is the date an editor reviewed the record's evidence, not a live endpoint test. If quotas/pricing/terms cannot be confirmed, describe that uncertainty and use `UNKNOWN` instead of guessing. Preserve details that constrain safe use, such as Nominatim's aggregate policy, arXiv pacing, model gates, privacy/retention caveats, and per-dataset licensing.

## Access status

Allowed values are `FREE_NO_KEY`, `FREE_WITH_KEY`, `FREE_TIER_LIMITED`, `OPEN_SOURCE_SELF_HOSTED`, `FREE_DATA_PAID_SERVICE`, `PAID`, and `UNKNOWN`. These summarize the described access path only. They must not be used as legal advice or as a promise of uptime, commercial rights, fixed quota, or free compute.

## Adding or changing an API

1. Prefer current official documentation for auth, endpoint shape, quotas, response format, rate limiting, terms, privacy, and CORS. Record source URLs and review date.
2. Add an exact HTTPS `base_url` and `allowed_hosts` containing its hostname. Never put credentials in base URLs or catalog data.
3. Describe endpoint methods and paths; disclose XML/text vs JSON, query/form vs JSON bodies, and whether a method can incur charges or side effects.
4. Map credentials to environment variable names and a supported auth kind. Do not store credentials. Do not accept caller-supplied auth values in request params or headers.
5. Add a `health_probe` only when a documented, safe GET/HEAD call exists. The probe must not mutate state, incur a material charge, send a message, or require user data.
6. Add a typed connector only when validation, format handling, or policy protection provides real value. Special services must not be made easier to use by bypassing their documented constraints.
7. Add a dataset/model/MCP record only when its rights/access evidence can be stated precisely. Keep API ids distinct from globally unique record ids.
8. Run the offline validator and tests. Do not mark `working_integration` based only on a registry listing; record the transport version, date, and actual initialize/list/call test scope.

## Review commands

```bash
apimind validate
apimind stale --days 180
apimind review-plan --days 180
python -m unittest discover -s tests -v
python -m compileall -q src/divyesh_api_mind
```

For a custom catalog, put all four JSON files in one directory and run `apimind validate --catalog-dir PATH`. The validator performs local parsing/schema checks and a best-effort scan for obvious embedded token patterns; it does not prove that factual claims are accurate or detect every possible secret. `apimind review-plan --days 180` prints stale records with their source URLs as a human review queue; it does not fetch or edit records.

The update process is intentionally manual: automatically fetching a page is not the same as reviewing changed policy language, a model card, or license conditions. After review, update the relevant factual fields, source evidence, and dates in the JSON catalog, then validate and test. Keep API probes out of routine validation so a local `validate` or CI run never sends provider traffic.

The `discover-import` pipeline for the Public APIs Markdown directory and OpenAPI 2.0/3.x specs writes a separate `UNKNOWN` review queue. It never edits `apis.json`; confirm primary provider documentation and run duplicate checks before manually promoting anything. See [`discovery.md`](discovery.md) for attribution, source license caveats, queue validation, and the current research batch.

## Mission 09 technology discovery and review

The separate `technology_discovery.json` schema is for non-accepted research leads. Its current built-in network collector reads public GitHub repository metadata only; repository existence/activity/license metadata does not prove provider identity or product facts. Discovery `free_status`, auth, quotas, license permissions, maintenance, Python SDK status, and product availability stay `UNKNOWN` until the appropriate source is supplied and reviewed. GitHub-only leads are not catalog API records and must not be called through `APIMind`.

`research-evidence-add` appends a hash-addressed, user-supplied evidence snapshot to a discovery lead. It does not update normalized values. `research-review-claim` appends human decisions to the separate `technology_research_reviews.json` hash chain. The ledger is review history only, not an accepted catalog or a substitute for the existing verification workflow. Cross-check cited evidence, dates, reviewer notes, duplicates, product/license scope, and chronology before any manual proposal/acceptance. Neither command nor `research-discover-github` promotes data.

Use `apimind validate`, `research-validate`, and `research-review-validate` before sharing the files. Keep original candidate/evidence/event dates as recorded; append corrections rather than silently restamping historical Mission 08 artifacts. Full Mission 09 scope and remaining research gaps are in [`research/mission-09-implementation-report.md`](research/mission-09-implementation-report.md).
