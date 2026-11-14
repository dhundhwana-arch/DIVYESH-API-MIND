# Phase 4 — bounded primary-source research plan

- **Plan date:** 2026-11-12
- **Prepared after:** Mission 04 preservation commit `8ae2641fddd72e1675d345f1e1938f4bca88a696` was pushed to the active branch and confirmed equal to `origin` with `git ls-remote`.
- **Research status (checkpoint):** in progress. The Mission 07 report records candidates #11–#20; the Mission 09 #21–#30 report records the next ten-candidate documentary review. Nine new workflows reached `human_approval` without proposals; City Context (#30) is deferred at license review because provider-domain pages were inaccessible and current legal terms remain unknown.

## Objective and scope

Conduct documentary, candidate-by-candidate review of **only the existing 100 leads** in [`review-batch-20261112-100`](../src/divyesh_api_mind/data/verification_review_batch_2026-11-12.json). The batch was generated from the preserved 2,964-candidate queue. Do not add new candidates, widen the source set, crawl directories, or treat the review score as evidence.

The sole evidence sources for candidate findings are current, provider-controlled primary materials: official developer documentation, provider-owned terms/policy/pricing/limit pages, official release/deprecation/maintenance notices, and official provider or standards registries when they establish identity. Directory rows, OpenAPI repositories, search snippets, and another party's summaries may help locate a provider page but do not establish a finding.

## Hard boundaries

- **Documentary review only. No Phase 4 endpoint calls, health checks, integrations, load tests, or batch probes.** Do not use `verify-probe` in this plan.
- Do not send credentials, create provider accounts, submit user data, or try undocumented endpoints. If a source requires login or a claim cannot be established safely from public primary materials, leave it unresolved and record the blocker.
- Do not convert upstream `verified`, free/no-auth, licensing, or checked-date fields into project findings.
- Do not auto-accept or promote candidates, change `apis.json`, or mark an MCP item as working. A future human catalog decision is separate from evidence collection.
- A future probe is outside this plan. It would require, for that exact provider and endpoint, reviewed official permission for an unauthenticated read probe **and** exact official endpoint documentation; only then can it be separately considered under the existing `verify-probe` guard.
- Do not conduct mass testing. The scope cap is 100 existing candidates; stop sooner when the evidence or timebox requires it.

## Bounded sequence

### 1. Preflight and preserve the baseline

1. Confirm the active branch and working tree, then run local catalog, discovery-queue, and verification-batch validation.
2. Keep the checked-in source batch unchanged. Create a separate working copy outside accepted catalog/queue paths; record its batch ID and source hash in the work log.
3. Review the documented workflow and this plan. Do not fetch a candidate endpoint.

### 2. Five-lead pilot

Start with the current highest-ranked leads, solely to test the review procedure and evidence recording:

| Triage order | Candidate name | Score |
| ---: | --- | ---: |
| 1 | YouTube Data API v3 | 52.96 |
| 2 | Visual Crossing Weather API | 47.80 |
| 3 | Bank Negara Malaysia Open Data | 47.00 |
| 4 | bng2latlong | 47.00 |
| 5 | IP2WHOIS Domain Lookup | 47.00 |

Scores order desk research only. They do not establish provider identity, API existence, access, safety, quality, or legal rights. First establish whether a provider-controlled source can be identified; if not, leave the lead blocked/deferred or `UNKNOWN` rather than guessing from its directory pointer.

### 3. Continue only within the existing batch

Continue through the remaining ranked leads in batches of **ten candidates**, stopping at the existing 100-candidate batch limit. Save, validate, report, and checkpoint each batch before starting the next one. If a source gap blocks a candidate, record the blocker and continue with the other candidates in the batch; do not expand to other entries in the 2,964-lead queue during this phase.

For each lead, use the candidate's retained attributions and listed URLs only as pointers, then seek and record provider-controlled primary sources for the following, where publicly documented:

1. provider identity and whether the named service/API exists;
2. current official API/developer documentation and documented version/deprecation state;
3. authentication method, scope, and credential requirements;
4. access tiers, price/free-tier conditions, and eligibility limits;
5. quotas, request/rate limits, and relevant usage policy;
6. API/service terms and data rights/license **separately**;
7. maintenance/activity only when a provider-controlled release or change record supports it;
8. privacy/retention and any relevant CORS or regional restrictions;
9. documentary Python integration feasibility, with any assumptions explicitly labeled.

Capture source URL, title/type, observed date, primary-source classification, reviewer, confidence, a concise supporting/contradicting note, and the specific fact it supports. A documentation link alone does not prove that an endpoint is reachable. Do not set accessibility to tested from documentary review.

### 4. Record uncertainty and stop cleanly

- Mark only facts directly supported by reviewed primary material as verified, using the workflow's evidence and confidence rules.
- Use `UNKNOWN` or `inconclusive` when evidence is missing, inaccessible, contradictory, secondary, or too vague. Do not infer “free,” “no authentication,” or an API/data license from an upstream directory or specification.
- Leave accessibility `NOT_TESTED` for every lead unless a separately authorized future phase performs an allowed probe. Documentary review alone cannot satisfy endpoint-accessibility or integration-test evidence gates.
- If an official provider cannot be established, sources conflict, terms/data rights are ambiguous, or review would require prohibited access, stop work on that candidate and record the reason.

Use `verify-add-evidence`, `verify-finding`, and stage transitions only on the separate working copy and only for reviewed material. Preserve the hash-linked audit sequence. The exact commands and accepted evidence fields are specified in [`docs/verification.md`](verification.md).

## Deliverables and exit criteria

At the end of a review session, preserve:

1. a validated working batch copy with source-linked evidence and unresolved values left explicit;
2. a short report with exact counts of candidates reviewed, facts supported/contradicted/inconclusive/unknown, blockers, and outstanding primary-source gaps;
3. confirmation that the original 100-lead batch and accepted catalogs were not overwritten or automatically changed;
4. confirmation that **no candidate endpoint was contacted** and no candidate was promoted.

No candidate is eligible for proposal or catalog acceptance merely because documentary research is complete. The existing workflow's proposal gate, explicit human approval, and separate acceptance of an already-existing approved catalog record continue to apply. If those gates cannot be met without a future, separately authorized probe or test, keep the lead unaccepted.

## Mission 07 execution checkpoint — 2026-11-12

Batch #11–#20 was reviewed from provider-controlled documentary sources, appended to the working batch at `docs/research/phase-4-review-batch-2026-11-12.json`, and validated. Nine candidate workflows reached the `human_approval` stage without creating proposals; ClickMeter (#14) is deferred at `license_review` because current ClickMeter-specific terms could not be established. All accessibility findings remain `NOT_TESTED`; no candidate endpoint was contacted. See the [batch report](research/phase-4-batch-11-20-report-2026-11-12.md) for per-candidate outcomes and exact counts.

## Mission 09 execution checkpoint — 2026-11-12

Candidates #21–#30 were reviewed using official provider/repository materials where available. The working batch received 66 appended evidence records (63 primary, three non-primary page-access observations) and 100 findings (62 verified, 38 inconclusive). Nine candidates (#21–#29) reached `human_approval` with no proposal; City Context (#30) remains deferred at `license_review` with all unresolved findings `UNKNOWN`/`NOT_TESTED`, because provider homepage/reference/API-page fetches returned HTTP 500 and current terms were not established. A page-fetch error is not evidence that the service is closed. All 100 accessibility findings remain `NOT_TESTED`; no endpoints or live APIs were called, no accounts/credentials or paid access were used, and no candidate was proposed or accepted. The accepted catalog, `census-data`, and the separate OpenWeatherMap sibling were unchanged. See the [#21–#30 batch report](research/phase-4-batch-21-30-report-2026-11-12.md) for per-candidate evidence and limitations.

## Related records

- [Phase 3 batch and actual result counts](project-history/PHASE_03_VERIFICATION_WORKFLOW.md)
- [Phase 3 report](phase-3-verification-report.md)
- [Evidence-gated verification workflow](verification.md)
- [Third-party attribution and license boundaries](third-party-notices.md)
