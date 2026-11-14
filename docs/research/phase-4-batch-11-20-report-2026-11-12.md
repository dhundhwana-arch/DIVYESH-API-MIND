# Phase 4 Batch Report — Candidates #11–#20

- **Observation/checkpoint date:** 2026-11-12
- **Mission:** 07 — documentary review only
- **Branch:** `arena/e2a56ea8-divyesh-api-mind`
- **Working batch:** [`phase-4-review-batch-2026-11-12.json`](phase-4-review-batch-2026-11-12.json)
- **Review protocol:** [`../phase-4-research-plan.md`](../phase-4-research-plan.md) and [`../verification.md`](../verification.md)

## Outcome

All ten candidates #11–#20 received source-linked review records using provider-controlled public documentation, pricing/access material, quota descriptions, or terms. The workflow's official-source-identification stage is complete for all ten. Nine records proceeded through license review to `human_approval` (`not_started`); ClickMeter (#14) is deferred at `license_review` because current ClickMeter-specific service/data terms could not be established. Deferral is not a rejection, proposal, or approval.

The records contain **60 newly appended evidence items**: 59 primary provider sources and one non-primary, inconclusive observation that a legacy ClickMeter terms URL returned Rebrandly-branded marketing content rather than ClickMeter terms. The ten new reviews contain 71 verified and 29 inconclusive findings. Inconclusive items retain `UNKNOWN` or `NOT_TESTED` rather than converting a documentation gap into a claim.

- Candidate API accessibility: `NOT_TESTED` for all 100 candidates.
- Candidate endpoint probes / live API calls: **0**.
- Accounts or credentials created/used: **0**.
- Proposals, human approvals, and catalog acceptances: **0 / 0 / 0**.
- `src/divyesh_api_mind/data/apis.json`: unchanged.
- Candidates #21–#100: no new review evidence added.

The batch validator's `primary_source_reviews_completed: 20` counter represents completion of the official-source-identification stage, not completion of every later workflow stage. Of the new ten, nine are at the human-approval gate and one remains deferred at license review.

## Candidate outcomes

| # | Candidate | Workflow result | Supported scope and material unresolved items |
| ---: | --- | --- | --- |
| 11 | USDA ERS | `human_approval` | ERS documents the ARMS JSON API, REST/GraphQL methods, registration/key requirements, and a shared api.data.gov default quota. A dated 2024 ARMS dataset update is not treated as API maintenance. The separate geospatial claim, API-specific quota override, explicit price, and broader data rights remain unresolved. |
| 12 | Browshot | `human_approval` | Official docs describe API v1.31, API-key authentication, Python client material, and a capped free screenshot allowance; a provider notice dated 2026-11-05 describes the ScreenshotCenter platform migration and v1 support. The terms page is dated 2015, so current API/data rights remain `UNKNOWN`. |
| 13 | CFB v3 Scores | `human_approval` | SportsDataIO documents subscription-key REST feeds. Its scrambled free trial is distinguished from paid real next-day Discovery Lab data and commercial service. Free-trial numeric limits, CFB-specific production price, date-qualified maintenance, and feed-specific redistribution rights remain unresolved. |
| 14 | ClickMeter | `license_review` — `deferred` | Older provider support materials document API v2, auth-key methods, historical rate/pagination limits, and REST operations. Current operation, pricing, and terms are unverified; Rebrandly redirects/content are not transferred to ClickMeter. The license finding is `UNKNOWN`; the workflow is deferred rather than treating a missing current terms source as a completed legal review. |
| 15 | ExchangeRate-API | `human_approval` | Provider docs distinguish the no-key Open Access endpoint from the registered keyed Free Plan (1,500 requests/month), and document quota-reporting delay and a Python example. Terms allow end-use caching but restrict redistribution/resale; paid-tier details were not generalized. |
| 16 | JSON2Video | `human_approval` | Current v2 docs describe REST resources and `x-api-key`; plan/terms sources describe 600 free credits, a 60-second free render cap, non-commercial free output, and the paid-plan output conditions. Credit, duration, body-size, and polling limits are kept distinct from an unspecified general HTTP rate. |
| 17 | Mastercard Offers for Publishers | `human_approval` | Current product docs describe the REST/Sandbox workflow and OAuth 1.0a; the official quick start includes Python 3 sample code. Production approval, price, numeric quota, and product-specific commercial/data terms remain unresolved; global Developer Terms are not treated as a substitute. |
| 18 | The SMS Works API | `human_approval` | Docs describe JWT Authorization and REST send/batch methods. The 50 free test credits are separated from paid SMS usage; a destination-level flooding filter is not described as a global API rate limit. Current broad data-use rights remain `UNKNOWN`. |
| 19 | Trash Nothing | `human_approval` | The provider-hosted v1.4 OpenAPI spec supersedes the imported v1.3 pointer for this review. App registration, endpoint-specific auth, feed windows/paging caps, and personal-use/resale restrictions are recorded. Pricing and an API-wide request quota remain `UNKNOWN`. |
| 20 | Vercel API | `human_approval` | REST docs describe Bearer tokens, response rate-limit headers, and plan/action-specific limits; a $0 Hobby account path is documented. No universal quota or standalone API price is inferred; API Terms restrictions are recorded separately. |

For exact source URLs, types, observation dates, claim wording, confidence, evidence references, and the complete hash-linked transition history, use the working-batch JSON above.

## Batch and repository integrity

The working 100-candidate batch remains the review artifact; the separate original 100-candidate source batch and approved pilot were not modified. The working batch now validates with 100 selected candidates, 20 candidates having primary-source review records, 156 primary evidence records, 289 total evidence records, 100 accessibility findings still `NOT_TESTED`, and zero endpoint probes, proposals, or acceptances. Candidate #14's terms-URL redirect evidence is explicitly non-primary and inconclusive.

- Working review batch SHA-256 after this batch: `68fbe7fc39a942f9ac7502321d64e5d80fa85b5e416d8322a465fd9d594d71e9`
- Original 100-candidate source batch SHA-256: `c07781393d477369156beceb03dd2137a6b360966b4a8f92fc7e0ae0c1193085`
- Approved pilot SHA-256: `5d68dbeee2ec646c060c3c361cbb800cd29e836284af4e59eb27e96ebb99d999`
- Accepted API catalog SHA-256: `6a6e3d6ed2a3b638edc7767143aa209af84ab4b0b02616585699c30cbb601219`

## Next checkpoint

Proceed to candidates **#21–#30** only after this batch's validation, test, Git commit, and push checkpoint. Preserve the same source and safety boundaries; do not repeat #1–#20, probe endpoints, create accounts, use credentials, or promote any candidate automatically.