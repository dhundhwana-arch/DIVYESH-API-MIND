# Phase 4 Consolidated Audit Report — Candidates #1–#30

- **Consolidation record date:** 2026-11-14
- **Active branch:** `arena/e2a56ea8-divyesh-api-mind`
- **Baseline commit:** `c2c1995742216ff357db817f599302c164aeca27`
- **Remote comparison before editing:** fresh fetch completed; local HEAD, FETCH_HEAD and `origin/arena/e2a56ea8-divyesh-api-mind` all matched the baseline, with `0 0` divergence.
- **Scope:** documentary consolidation for exactly original source ranks #1–#30.

## Executive result

The requested Phase 4 consolidated map and evidence registries were generated from the saved original source batch and separate working review batch. Candidate rank, ID and product name match for exactly 30 records. Existing evidence and workflow histories were not edited; the approved pilot, original source batch and accepted catalog remain unchanged. Twenty-eight workflows are at `human_approval / not_started`; #14 ClickMeter and #30 City Context remain deferred at `license_review`. No proposals, approvals, acceptances, endpoint probes or candidate API calls were created.

The repository evidence has an unresolved date inconsistency: all saved evidence and event date fields say 2026-11-12, while the earlier review commits are timestamped 2026-11-14 and the handoff says some source review occurred on that date. No hash-linked record is backdated or rewritten; the consolidated map flags the chronology as `INCONCLUSIVE`.

## Preservation gate and repository baseline

The pre-research preservation report is [`phase-4-repository-preservation-report-2026-11-14.md`](phase-4-repository-preservation-report-2026-11-14.md). Before creating this consolidation, a fresh fetch confirmed that local HEAD, FETCH_HEAD and the feature-branch remote ref all resolved to `c2c1995742216ff357db817f599302c164aeca27`; left/right divergence was `0 0`. The active feature branch was retained; no merge to `main`, reset, force-push, history rewrite, stash apply/drop or unrelated application change occurred.

| Protected artifact | SHA-256 at preflight / consolidation | Result |
| --- | --- | --- |
| Original 100-candidate source batch | `c07781393d477369156beceb03dd2137a6b360966b4a8f92fc7e0ae0c1193085` | Unchanged |
| Approved pilot batch | `5d68dbeee2ec646c060c3c361cbb800cd29e836284af4e59eb27e96ebb99d999` | Unchanged |
| Working 100-candidate batch | `a22fe4edf469ff73e5f0405232406e1a50908e2b1a7410901cd5819ada1cf135` | Read-only during consolidation |
| Accepted API catalog `apis.json` | `6a6e3d6ed2a3b638edc7767143aa209af84ab4b0b02616585699c30cbb601219` | Unchanged |
| Existing stash | `ab3b05cf5d3cce4a2701c1f010f3826b3bdc44f9` | Preserved; not applied/dropped |

Other catalog files, original batch, pilot and previous reports were not rewritten. New material is confined to research documentation and generated consolidation artifacts.

## Exact scope and integrity assertions

- Original source candidates checked: 100; consolidation rank set: `1..30` (30 entries; 30 unique candidate IDs).
- Each rank's candidate ID and name matched the original source batch and working batch; no rank gaps, duplicates or substituted IDs.
- Findings copied: 300 (10 workflow dimensions per candidate).
- Evidence records included: 261; unique evidence IDs: 261; primary 219; non-primary 42; primary-source candidates 29/30.
- Workflow events included: 793; unique event IDs: 793; original event hashes/notes/sequence values copied as stored. Registry-only `rank` and `candidate_id` index fields are added for traceability; they are not part of each original hash payload.
- The original candidate canonical-JSON hashes match for all 30 candidates. All 261 evidence records and 793 original transition events match the working batch field-for-field after removing those registry index fields; all 793 canonical event hashes and per-candidate previous-hash chains recompute successfully.
- Every finding evidence reference and transition-event evidence reference resolves to a candidate-scoped evidence record in the JSON registry. Every candidate workflow event reference resolves to its event registry entry and has the same candidate ID.
- Current workflows: 28 `human_approval/not_started`; 2 `license_review/deferred`.
- No proposal/approval/catalog-acceptance records are present for these 30 records.

## Finding counts (saved workflow status)

| Dimension | Verified in source workflow | Inconclusive in source workflow | Consolidated interpretation |
| --- | ---: | ---: | --- |
| API existence / scope | 29 | 1 | see per-candidate status and notes |
| Provider identity | 29 | 1 | see per-candidate status and notes |
| Official documentation / version | 29 | 1 | see per-candidate status and notes |
| Authentication | 22 | 8 | see per-candidate status and notes |
| Free tier / pricing / eligibility | 15 | 15 | see per-candidate status and notes |
| Quota / rate / usage limits | 21 | 9 | see per-candidate status and notes |
| API/service terms and data/content rights | 15 | 15 | see per-candidate status and notes |
| Date-qualified API maintenance | 8 | 22 | see per-candidate status and notes |
| Documentary Python feasibility | 28 | 2 | see per-candidate status and notes |
| Live endpoint accessibility | 0 | 30 | all `NOT_TESTED` |

Across all 300 findings, source workflow counters total **196 `verified`** and **104 `inconclusive`**. The 30 accessibility findings have stored status `inconclusive` but value `NOT_TESTED`; the consolidated status explicitly labels them `NOT_TESTED`. A `VERIFIED` documentary finding is not a reachability test, endorsement or blanket rights clearance.

## Evidence quality, provenance and confidence

- 261 evidence records: 219 marked primary, 42 non-primary. Source pointers and unsuccessful page fetches are retained as observations rather than provider claims.

| Evidence type | Total | Primary | Non-primary |
| --- | ---: | ---: | ---: |
| authentication_documentation | 27 | 27 | 0 |
| endpoint_documentation | 31 | 30 | 1 |
| license_documentation | 10 | 10 | 0 |
| maintenance_record | 11 | 11 | 0 |
| official_documentation | 63 | 62 | 1 |
| openapi_specification | 5 | 3 | 2 |
| other | 1 | 0 | 1 |
| pricing_access_documentation | 21 | 21 | 0 |
| provider_homepage | 2 | 1 | 1 |
| quota_documentation | 25 | 25 | 0 |
| source_directory | 36 | 0 | 36 |
| terms_of_service | 29 | 29 | 0 |

- #30 City Context is the only candidate with no primary-source evidence record; its source page failures do not show the API is closed.
- Stored finding confidence range/median: 0.50 / 0.90 / 0.99. Confidence is reviewer confidence, not a statistical probability or legal assurance.
- Access and licensing notes separate API account eligibility, trial/sandbox access, pricing/quota, service terms, data/content rights and third-party assets.
- Every spec/repository license pointer is kept distinct from API/service/data rights. No commercial-use, model-training, redistribution or privacy permission is inferred from a directory/spec license.
- All evidence entries and 793 transition events with hashes are preserved in the JSON. Prior entries were not overwritten or re-dated.

### Observation-date audit

- Stored evidence `observed_on`: {"2026-11-12": 261}.
- Stored workflow-event `recorded_on`: {"2026-11-12": 793}.
- Stored candidate `checked_on`: {"2026-11-12": 30}.
- Existing Git committer dates: Mission 07 commit `2231f93c58f68531fbb1752322b8a558cde1e9fd` = `2026-11-14T03:13:35+00:00`; Mission 09 commit `c2c1995742216ff357db817f599302c164aeca27` = `2026-11-14T04:32:02+00:00`. Prior review handoff also places some source review on 2026-11-14.
- **Conclusion: INCONCLUSIVE chronology.** 2026-11-12 is the date stored by the evidence recorder; it cannot be certified as the actual retrieval date given the later commit/review timestamps. This consolidation is based on repository records and has not added provider research. No original event or evidence date was changed to protect the hash-linked history. A future correction should be append-only and use a verified actual observation date.

## Duplicates, overlaps and catalog preservation

- #1 YouTube Data API v3 is flagged as a possible match to accepted `youtube-data-v3`; #7 APOD overlaps accepted `nasa-open-apis`; #25 Census Bureau is conceptually related to accepted `census-data` and dataset `census-acs-5year`.
- #2 Visual Crossing retains broader-queue siblings `candidate-visual-crossing-1785665833` (same canonical URL) and `candidate-visual-crossing-91f43c53a3` (normalized-name match with a different URL). #24 OpenWeatherMap retains sibling `candidate-openweathermap-33fadeaff5`; Open-Meteo lead `candidate-open-meteo-f6a4cac428` (#39) and accepted `open-meteo` are separate. Census lead `candidate-us-census-ffc0d93378` remains distinct from #25 and accepted `census-data`/`census-acs-5year`.
- Duplicate flags prompt human comparison, not merging. No entry was deleted, renamed, consolidated into `apis.json`, or accepted.
- Accepted `census-data`, `open-meteo` and every other API/model/dataset/MCP record remain unchanged; unchanged catalog SHA-256 is recorded above.

## Human queue, unresolved work and suitability

The human-approval queue contains exactly 28 candidates whose saved workflow reached `human_approval`. All remain `not_started`; the queue gives verified evidence, gaps, risks and a non-operative HOLD recommendation. #14 and #30 remain explicitly deferred, outside that queue. See [queue](phase-4-human-approval-queue-1-30.md) and [unresolved issues](phase-4-unresolved-issues-1-30.md).

Documentary-suitability assessments are included for NYAYMITRA-AI, GRANTH-AI, general AI R&D, education, analytics/visualization and mobile/web work. The repository contains no project-specific requirements for NYAYMITRA-AI or GRANTH-AI, so their result is `INCONCLUSIVE`; no integration, live test or production-readiness claim is made.

## Scope limitations

1. The consolidation does not refresh provider pages or establish current external state beyond the saved evidence; terms, prices and APIs can change.
2. No candidate endpoint, live API, authentication flow, app or integration was exercised. All 30 accessibility statuses are `NOT_TESTED`.
3. Missing terms or data rights remain `UNKNOWN`/`INCONCLUSIVE`; this report is not legal advice.
4. Candidate source categories and upstream source/spec claims are preserved as data provenance, not promoted to verified facts.
5. Suitability is only documentary and conditional; no project requirements for NYAYMITRA-AI/GRANTH-AI are in the repository.
6. The date inconsistency is unresolved; do not treat the recorded 2026-11-12 values as a certified observation chronology.

## Validation and test outcomes

All checks below used local repository files or mocked transports; external provider pages and candidate endpoints were not fetched during validation.

| Check | Exact outcome |
| --- | --- |
| `python -m py_compile .phase4_consolidate.py && python .phase4_consolidate.py` | **PASS** — refreshed the five consolidation artifacts; temporary helper was removed after QA. Later index/date/suitability edits were independently checked below. |
| `.venv/bin/apimind validate` | **PASS** — `apis`, `models`, `datasets`, `mcp_registry`, `discovery_candidates.json` (2,964 review candidates; not promoted), and `openapi_review_candidates.json` (3 review candidates; not promoted) valid. |
| `.venv/bin/apimind verify-validate docs/research/phase-4-review-batch-2026-11-12.json` | **PASS** — `valid: true`; 100 selected, 29 with primary-source records, 30 official-source stage completions, all 100 accessibility states `NOT_TESTED`, and 0 endpoint probes/proposals/approvals/acceptances. |
| `.venv/bin/apimind verify-validate docs/research/phase-4-pilot-batch-2026-11-12.json` | **PASS** — `valid: true`; 100 selected and 5 with primary-source records; 0 probes/proposals/approvals/acceptances. |
| `.venv/bin/apimind verify-validate src/divyesh_api_mind/data/verification_review_batch_2026-11-12.json` | **PASS** — `valid: true`; 100 selected, 0 primary-source reviews, 0 probes/proposals/approvals/acceptances, all 100 accessibility `NOT_TESTED`. |
| `.venv/bin/python -m pytest -q` | **PASS** — 75 passed, 13 subtests passed (3.33 seconds). |
| `.venv/bin/python -m compileall -q src tests examples` | **PASS**. |
| Consolidation integrity and preservation assertions | **PASS** — exactly ranks #1–#30 matched by ID/name and original canonical candidate hash; 261/261 evidence records and 793/793 events match source fields exactly after removing documented registry indexes; all 793 original event hashes/chains recompute; every reference resolves; 28 human-queue entries; #14/#30 deferred; no decision records; accessibility `NOT_TESTED` for all 30; four protected SHA-256 values unchanged. |
| Markdown local-link/reference check | **PASS** — 176 local targets checked across 10 changed/progress Markdown files; 1,388 rendered evidence-ID link instances resolve in the JSON registry. External URLs were not fetched or certified. |
| `git diff --cached --check` | **PASS** — no whitespace errors in the staged 11-file patch. |

## Deliverables

- [Consolidated evidence map (Markdown)](phase-4-consolidated-evidence-map-1-30.md)
- [Consolidated evidence map (JSON; full evidence + workflow-event registries)](phase-4-consolidated-evidence-map-1-30.json)
- [Human-approval queue](phase-4-human-approval-queue-1-30.md)
- [Unresolved issues](phase-4-unresolved-issues-1-30.md)
- [Repository preservation report](phase-4-repository-preservation-report-2026-11-14.md)
- [Updated README](../../README.md)
