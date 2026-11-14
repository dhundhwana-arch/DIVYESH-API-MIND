# Phase 4 Batch Report — Candidates #21–#30

- **Observation/checkpoint date:** 2026-11-12
- **Mission:** 09 — documentary review only
- **Branch:** `arena/e2a56ea8-divyesh-api-mind`
- **Working batch:** [`phase-4-review-batch-2026-11-12.json`](phase-4-review-batch-2026-11-12.json)
- **Review protocol:** [`../phase-4-research-plan.md`](../phase-4-research-plan.md) and [`../verification.md`](../verification.md)

## Outcome

Candidates #21–#30 were reviewed within the separate working 100-candidate batch. The review added **66 evidence records** (63 primary provider/repository records and three non-primary records of inaccessible City Context page pointers); the batch preserves 11 earlier imported, unreviewed directory pointers in these ten candidate records. The new findings are **62 verified and 38 inconclusive**. Inconclusive values remain `UNKNOWN` or `NOT_TESTED`.

Nine workflows (#21–#29) completed license review and reached `human_approval` with that stage still `not_started`; City Context (#30) is deferred at `license_review` because the provider-domain homepage, reference, and `/v2/` page fetches returned HTTP 500 and no current provider legal terms were established. That failure does not establish that City Context is closed. No candidate was proposed, approved, or accepted.

- Candidate API accessibility: `NOT_TESTED` for all 100 candidates.
- Candidate endpoint probes / live API calls: **0 / 0**.
- Accounts or credentials created/used; paid access: **0 / 0 / 0**.
- Proposals / human approvals / catalog acceptances: **0 / 0 / 0**.
- Accepted catalog `apis.json`: unchanged. The accepted `census-data` entry and separate OpenWeatherMap sibling candidate remain separate and untouched.
- ClickMeter (#14) remains deferred and outside this batch; no #1–#20 findings were repeated or altered.
- Candidates #31–#100 received no new evidence in this checkpoint.

The batch's `primary_source_reviews_completed` summary counts stage transitions: it is now 30 because the official-source stage was completed for these ten, including the inconclusive City Context source-access result. The stricter `candidates_with_primary_source_review` count is **29**: the three failed City Context page fetches are recorded as non-primary observations, not provider facts.

## Candidate outcomes

| # | Candidate | Workflow result | Supported findings and unresolved scope |
| ---: | --- | --- | --- |
| 21 | Zalando Shop | `human_approval` | The [archived provider-owned repository](https://github.com/zalando/shop-api-documentation/blob/master/README.md) documents a historical Shop Public API and says article, category, and product data are not supported through it. The repository was archived in 2018. No current supported Shop API, current authentication/quota, API pricing, or current API/data rights were established. General consumer terms are not treated as API-specific terms. |
| 22 | Healthsites.io | `human_approval` | [API v3 documentation](https://healthsites.io/api/docs/) and the provider-linked [API terms](https://github.com/healthsites/healthsites/wiki/API-Terms) document facilities/statistics, OSM-account/token setup, and up to 50 calls/day free for professional use; higher volume and bulk downloads are paid. Facility data is ODbL 1.0 with attribution/share-alike obligations. The terms also require AI-answer attribution and provider contact before training/fine-tuning. No key was created and no API call was made. |
| 23 | NLR Developer Network | `human_approval` | [Provider documentation](https://developer.nlr.gov/docs/) describes energy APIs and key signup. The shared default is 1,000 requests/hour/key; `DEMO_KEY` is 30/hour and 50/day/IP. General terms allow use of provided data/software, but dataset-specific rights and a stated API price remain unresolved. Recent documentation-repository activity is not API uptime. |
| 24 | OpenWeatherMap One Call | `human_approval` | [One Call API 4.0](https://openweathermap.org/api/one-call-4) is recommended for new integrations; v3 remains available. The separate One Call subscription documents 1,000 calls/day free, then £0.0012/call, with a default 2,000/day cap after subscription that can be adjusted. API-key use and self-service ODbL attribution/share-alike conditions are recorded. The OpenWeatherMap sibling lead was not merged or changed. |
| 25 | Census Bureau | `human_approval` | The [May 2026 user guide](https://www.census.gov/data/developers/guidance/api-user-guide.Query_Limits.html) says every query needs a free key and allows 50 variables/query. The official [2026-02-19 training deck](https://www2.census.gov/about/training-workshops/2026/2026-02-19-getting-started-with-census-api-presentation.pdf) instead says a key is needed above 500 queries/IP/day and describes no throttling. The conflict is preserved: the authentication finding and settled daily quota remain unknown. API terms require non-endorsement attribution and prohibit re-identification/false representation; rights remain dataset-specific. The accepted `census-data` record was not edited or duplicated in the catalog. |
| 26 | GovInfo | `human_approval` | [GovInfo API documentation](https://api.govinfo.gov/docs/) describes Search, Collections, Packages, Published, and Related operations and requires an api.data.gov key. The 1,000/hour/key and `DEMO_KEY` defaults come from the umbrella [api.data.gov manual](https://api.data.gov/docs/developer-manual/), not a GovInfo-specific guarantee. Price and collection-specific rights remain unknown; the reviewed copyright page returned only a stub. |
| 27 | RevAddress | `human_approval` | [Provider pricing](https://revaddress.com/pricing/) documents up to 1,000 monthly Census/local operations on the free plan. USPS DPV is paid: a paid plan and ten purchased credits ($0.01) per address. A free-tier DPV example conflicts with the [provider terms](https://revaddress.com/legal/terms/), so no free DPV access is inferred and no address was submitted. Authentication, broader data-license terms, and a generic request-rate limit remain unknown. |
| 28 | Telesign Verify | `human_approval` | Provider [Verify instructions](https://developer.telesign.com/enterprise/docs/verify-api-get-started-with-sms) require a full-service account and document Basic authentication. HTTP 429/code 3204 signals the per-second rate has been exceeded, but no numeric quota is published. Reviewed US prices are $0.0095/message for SMS Verify and $0.15/message for Verify Plus; the unified Verify API is sales-priced. General terms/AUP/DPA/privacy sources were reviewed, but Verify-specific data roles, retention, and a unified product price/free tier remain unresolved. The Python SDK's 2026-10-01 release is SDK-repository activity, not proof of Verify support or backend maintenance. |
| 29 | 1Password Connect | `human_approval` | [Connect documentation](https://www.1password.dev/connect) describes a private, self-hosted REST API. Requests use bearer tokens scoped to authorized vaults. Cached re-requests are unlimited; undocumented internal rate limits apply on initial secret fetch/startup. All customers have unlimited Connect access, but an underlying paid 1Password subscription is required. The API reference/spec says 1.8.1 while publisher Docker tags list 1.8.4; no dated Connect-server maintenance or deployed version was established. This is not a public data API or an open data license. |
| 30 | City Context | `license_review` — `deferred` | Provider homepage, API-reference, and `/v2/` page fetches returned HTTP 500. The records explicitly treat these as inaccessible pointers, **not** endpoint probes or proof of closure. Current API status, documentation, auth, pricing, quota, Python surface, terms, and data rights remain unknown. Stale provider-repository activity and an uncorroborated secondary closure claim were not used as provider facts. |

Exact source URLs, evidence types, observation dates, individual notes, confidence, finding references, and hash-linked workflow events are in the working-batch JSON.

## Batch and repository integrity

The validated working batch contains **355 evidence records**, of which **219** are primary provider/repository records. This checkpoint appended 66 records (63 primary and three non-primary inaccessible-page observations). There are now 29 candidates with a primary-source review record; nine newly reviewed workflows are at `human_approval` (`not_started`), and #30 is deferred at `license_review`. All 100 accessibility findings remain `NOT_TESTED`; there are no endpoint-probe records, proposals, approvals, or catalog acceptances.

The original pinned 100-candidate source batch, pilot artifact, accepted catalog, candidates #1–#20, OpenWeatherMap sibling lead, and accepted Census record remain unchanged.

- Working review batch SHA-256: `a22fe4edf469ff73e5f0405232406e1a50908e2b1a7410901cd5819ada1cf135`
- Original 100-candidate source batch SHA-256: `c07781393d477369156beceb03dd2137a6b360966b4a8f92fc7e0ae0c1193085`
- Approved pilot SHA-256: `5d68dbeee2ec646c060c3c361cbb800cd29e836284af4e59eb27e96ebb99d999`
- Accepted API catalog SHA-256: `6a6e3d6ed2a3b638edc7767143aa209af84ab4b0b02616585699c30cbb601219`

## Next checkpoint

After validation, tests, and a checkpoint on `arena/e2a56ea8-divyesh-api-mind`, proceed to candidates **#31–#40** only. Keep #14 ClickMeter and #30 City Context deferred until suitable provider-specific primary materials can be reviewed; do not probe endpoints, create accounts, use credentials, or promote candidates.
