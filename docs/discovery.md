# API discovery and human review

`apimind discover-import` ingests three discovery formats:

1. The category index in the `public-apis/public-apis` Markdown README.
2. The API-only rows in API Atlas JSONL exports.
3. OpenAPI 2.0 and OpenAPI 3.x JSON or YAML specifications.

Imports create a **review queue**, not callable records. The pipeline retains source URLs, revision/file/line attribution when available, source dates, raw directory claims, OpenAPI servers/paths/security declarations, and content hashes. It normalizes names/URLs, merges exact repeats, flags possible duplicates, and reports possible matches against the current API catalog. Nothing is automatically promoted.

Every imported candidate stays `free_status: UNKNOWN`, `authentication.kind: unknown`, `authentication.verified: false`, with quota, rate limits, and API/service license all `UNKNOWN`. Directory claims such as `No` authentication, `HTTPS: Yes`, or `CORS: Yes` are stored as unverified source claims only. An OpenAPI `info.license` is recorded as a **specification** claim and is not treated as an API/data license. API requests against records with unverified auth are blocked.

## Import a local source

```bash
apimind discover-import \
  --format public-apis \
  --input ./README.md \
  --source-url https://github.com/public-apis/public-apis/blob/COMMIT/README.md \
  --revision COMMIT \
  --checked-on 2026-11-12 \
  --output ./public-apis-review.json

apimind discover-import \
  --format api-atlas \
  --input ./catalog.jsonl \
  --source-url https://github.com/CTCycle/api-atlas/blob/COMMIT/data/catalog.jsonl \
  --revision COMMIT \
  --checked-on 2026-11-12 \
  --output ./api-atlas-review.json

apimind discover-import \
  --format openapi \
  --input ./openapi.yaml \
  --source-url https://github.com/vendor/project/blob/COMMIT/openapi.yaml \
  --checked-on 2026-11-12 \
  --output ./openapi-review.json
```

API Atlas imports require `--revision` even for local input; it must be a hexadecimal Git commit identifier, not a branch name, and is used to pin row attribution.

JSON parsing uses the Python standard library. YAML is optional:

```bash
python -m pip install 'divyesh-api-mind[discovery-yaml]'
```

## Fetch a public source explicitly

Only one caller-selected HTTPS URL is fetched; redirects are refused, no API credentials are forwarded, and response size/time are bounded. For GitHub contents, use a commit-pinned API URL and separately pass a human-readable `--source-url` pinned to the same commit when needed:

```bash
apimind discover-import \
  --format public-apis \
  --url 'https://api.github.com/repos/public-apis/public-apis/readme?ref=COMMIT' \
  --source-url 'https://github.com/public-apis/public-apis/blob/COMMIT/README.md' \
  --revision COMMIT \
  --checked-on 2026-11-12 \
  --output ./public-apis-review.json
```

For API Atlas JSONL, use the GitHub Git Blobs endpoint for the `data/catalog.jsonl` blob and pin the separate repository commit in `--source-url`:

```bash
apimind discover-import \
  --format api-atlas \
  --url 'https://api.github.com/repos/CTCycle/api-atlas/git/blobs/1ce18eadde04952d5d57e3f2c9eb26498eb8e5b0' \
  --source-url 'https://github.com/CTCycle/api-atlas/blob/547dae1fcc8356b11091200c76906787cc817ebc/data/catalog.jsonl' \
  --revision 547dae1fcc8356b11091200c76906787cc817ebc \
  --checked-on 2026-11-12 \
  --output ./api-atlas-review.json
```

The blob id pins the JSONL content; `--revision` pins the API Atlas commit used for row links. Replace neither with a branch name. For OpenAPI, the GitHub Contents API can be used with `?ref=COMMIT` to fetch the specification; set `--source-url` to its pinned GitHub `blob/COMMIT/...` file URL so attribution can retain repository, revision, and file path. Do not pass private endpoints, credential-bearing URLs, or sources whose terms do not permit your use.

## Browse, validate, and merge queues

```bash
apimind review-candidates --priority upstream_checked_pointer --limit 20
apimind review-candidates --category Weather --limit 20
apimind review-candidates --queue ./openapi_review_candidates.json --query "vehicle"
apimind review-merge ./one-review.json ./another-review.json --output ./combined-review.json
apimind validate
```

Queue searches are local. Merging retains each evidence source and only collapses identical normalized names plus canonical URLs. Similar names or shared URLs remain separate and are flagged for a human. The validator rejects non-`UNKNOWN` free/auth/quota/license candidate values or missing source evidence.

## Current discovery batch (2026-11-12)

- `public-apis/public-apis` was fetched at commit `cb581147b5e7c808cc2db43c5c590b51679dd44c`; GitHub metadata reports an MIT license. Its README index produced **2,360 source rows**, **2,357 exact-name/canonical-URL leads** after merging 3 repeated rows, **46 within-source duplicate signals**, and **51 source categories**. Directory auth/HTTPS/CORS assertions remain unverified claims.
- `CTCycle/api-atlas` was inspected at commit `547dae1fcc8356b11091200c76906787cc817ebc`; the imported `data/catalog.jsonl` Git blob was `1ce18eadde04952d5d57e3f2c9eb26498eb8e5b0`. Its README reports 2,520 total resources and 541 rows checked across APIs, portals, datasets, and MCP. The machine-readable catalog has **2,092 API rows**, of which **197** carry the upstream `verified=true`/checked-date claim and **1,895** do not. The importer stores all 2,092 as leads, ranks the 197 upstream-checked rows first, and keeps every access/auth/license value as a source claim only. API Atlas labels the compilation CC BY 4.0 and preserves each row's upstream origin; the row's upstream source/license is retained in attribution.
- `APIs-guru/openapi-directory` at commit `f04b8d0bcd39c52e1cf3ad7a5fe744709832ae49` had **11,091 tree entries**, including **4,138 OpenAPI/Swagger YAML spec files across 701 provider directories**. Its README says listed APIs can be free or paid and describes CC0 for contributed definitions alongside externally sourced definitions. Three parser examples—NASA APOD, UK Vehicle Enquiry, and YouTube Data API v3—are in `openapi_review_candidates.json`; all remain UNKNOWN. Two are flagged as possible matches to existing API records.
- The combined `discovery_candidates.json` queue contains **2,964 unique candidate leads** from those sources after **1,488 exact cross-source lead merges** (plus the 3 repeated Public APIs rows already merged at import); **717 candidates** carry possible-duplicate signals and **37** are possible matches to accepted catalog IDs. Those counts describe review leads, not accepted APIs. Source taxonomies/OpenAPI tags are not mapped to the project's 19 accepted categories. All candidates remain non-callable and `UNKNOWN` for free access, auth verification, quotas, rates, and API/service license.
- MCP registry GitHub metadata and README were inspected, but no live MCP registry call or integration test was run. The repository license metadata is `NOASSERTION`; its README's dated 2025 preview/API-freeze notes are historical, not current operational status. The accepted MCP catalog remains six metadata entries and zero working integrations. The registry endpoint was not probed.
- Government open-data verification remains incomplete: the India OGD portal returned HTTP 500/Akamai errors in the earlier review. The existing model and dataset catalogs were not expanded in this batch; Hugging Face/provider and additional official government documentation still need primary-source review. API Atlas, GitHub, and repository listings are discovery sources, not live-health or terms verification.

## Promotion checklist

A human editor should only promote a candidate after independently checking current official documentation for: the callable base URL and safe read endpoint; authentication and scopes; free/paid access path; quotas and pace limits; API service terms, data rights, and license; privacy/CORS caveats; and version/deprecation status. Record dated official source URLs and confidence. Use `UNKNOWN` for unresolved fields. Run duplicate/cross-catalog checks and offline validation before adding an API record. Set a health probe only for a documented safe read-only call; do not mark an API healthy based on a directory listing.
