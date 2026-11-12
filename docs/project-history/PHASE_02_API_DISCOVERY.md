# Phase 2 — API discovery

**Status:** source imports and a combined review queue are preserved. Discovery is not provider verification, and none of the imported leads is counted as an accepted API record.

> **History note:** the repository's shallow/grafted Git history does not provide separate Phase 2 commits. Counts and source revisions below come from the bundled queue metadata and [`docs/discovery.md`](../discovery.md), not from inferred commit timestamps.

## Import and provenance model

[`src/divyesh_api_mind/discovery.py`](../../src/divyesh_api_mind/discovery.py) imports Public APIs Markdown, API Atlas JSONL, and OpenAPI 2.0/3.x documents. It normalizes candidate names/URLs, merges exact repeated leads, records possible-duplicate signals, preserves source claims and row/file/revision attribution where available, and writes a separate review queue.

Imported candidates remain non-callable and `UNKNOWN` for free-access status, verified authentication, quota/rate information, and API/service license. An OpenAPI security scheme, directory “no auth/free” assertion, upstream check marker, or specification license is retained as a source claim—not promoted to a finding. Queue import and merge do not edit `apis.json`.

## Preserved discovery snapshot

The combined [`discovery_candidates.json`](../../src/divyesh_api_mind/data/discovery_candidates.json) records:

| Measure | Count | Interpretation |
| --- | ---: | --- |
| Source rows | 4,455 | 2,360 Public APIs rows, 2,092 API Atlas API rows, and 3 OpenAPI examples as represented in the import snapshot |
| Unique leads | 2,964 | Review candidates after source-local and cross-source exact merging |
| Exact duplicate rows merged in the combined queue | 1,488 | The Public APIs import had already coalesced three repeated rows before the combined merge |
| Candidates with possible-duplicate flags | 717 | Signals for human review, not automatic merges |
| Source categories | 127 | Imported source taxonomy, not mapped one-to-one to the accepted catalog's categories |
| Possible matches to accepted catalog IDs | 37 | Duplicate-review signals; not accepted candidate records |

The queue's source entries pin the upstream revisions and content hashes. Its API Atlas source metadata records 2,092 API rows, of which 197 carry the source's upstream `verified`/checked claim. Those 197 are **not independently verified by this project**. API Atlas reports 2,520 total resources and 541 checked rows across resource types; those broader source totals are not API-only counts.

Three OpenAPI examples—NASA APOD, UK Vehicle Enquiry, and YouTube Data API v3—are preserved separately in [`openapi_review_candidates.json`](../../src/divyesh_api_mind/data/openapi_review_candidates.json). Two have possible matches to existing API records. OpenAPI `info.license` applies to the specification claim as recorded; it does not establish the API service or data license.

## Results and non-results

- The accepted API catalog remains at **26** entries; queue candidates are not added to that total.
- No API Atlas upstream check marker, directory claim, or source license was treated as independent provider evidence.
- The India OGD portal fetch attempt recorded in prior research failed with HTTP 500/Akamai errors; it is not verification and the related record remains discovery-only/low confidence as described in [`catalog-maintenance.md`](../catalog-maintenance.md).
- Three dated reads of GitHub, PyPI, and npm metadata endpoints are recorded in [`live-probes.md`](../live-probes.md). They concern those specific endpoints only and do not test the discovery queue.
- No endpoint from the Phase 3 top-100 batch was tested.

## Source and rights notes

The source snapshots use pinned revisions for the Public APIs directory, API Atlas, and APIs.guru OpenAPI directory. Their distinct licenses, per-file caveats, attribution, and separation from provider/API/data rights are documented in [`third-party-notices.md`](../third-party-notices.md). No source affiliation or endorsement is implied.

## Evidence links

- [Discovery workflow and source breakdown](../discovery.md)
- [Queue importer, normalizer, and validator](../../src/divyesh_api_mind/discovery.py)
- [Discovery tests](../../tests/test_discovery.py)
- [Combined queue](../../src/divyesh_api_mind/data/discovery_candidates.json)
- [Phase 3 review batch](../../src/divyesh_api_mind/data/verification_review_batch_2026-11-12.json)
- [Phase 3 verification workflow](PHASE_03_VERIFICATION_WORKFLOW.md)
