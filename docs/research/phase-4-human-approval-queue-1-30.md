# Phase 4 Human-Approval Queue — Candidates #1–#30

- **Consolidation record date:** 2026-11-14
- **Authoritative state source:** [`phase-4-consolidated-evidence-map-1-30.json`](phase-4-consolidated-evidence-map-1-30.json) and saved [working batch](phase-4-review-batch-2026-11-12.json).
- **Queue rule:** include only candidate workflows whose actual saved `current_stage` is `human_approval`.
- **Decision boundary:** recommendations below are non-operative human-review guidance. No candidate was proposed, approved, accepted or added to the catalog.

## Queue summary

There are **28** queue entries at `human_approval / not_started`: #1–#13, #15–#29. Their approval records, proposal records and catalog-acceptance records are null in the source workflow. ClickMeter #14 and City Context #30 are **not** approval-queue entries: both remain deferred at `license_review` and are listed separately below.

Each item reports primary-source verified findings, unresolved facts, material risks and a recommended human disposition. These recommendations are not workflow decisions. Evidence links resolve through the map JSON's evidence registry.

## Candidates at human_approval / not_started

### #1 — YouTube Data API v3

- **ID / provider / category:** `candidate-youtube-data-api-v3-e1c8359956` / Google / YouTube / `source category not supplied`; functional group: media / video platform, developer API.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** Google for Developers documents the YouTube Data API v3 as an API service. Evidence: [p4-yt-base](https://developers.google.com/youtube/data/getting-started).
  - **Provider identity — ✅ VERIFIED:** The documentation is on the provider-controlled Google/YouTube developer site and identifies YouTube Data API v3. Evidence: [p4-yt-base](https://developers.google.com/youtube/data/getting-started).
  - **Official documentation / version — ✅ VERIFIED:** Current provider documentation for YouTube Data API v3 is available and identifies the documented version. Evidence: [p4-yt-docs](https://developers.google.com/youtube/data/getting-started).
  - **Authentication — ✅ VERIFIED:** Provider authentication guide distinguishes public-data API-key access from OAuth-authorized private/write operations. Evidence: [p4-yt-auth](https://developers.google.com/youtube/data/guides/authentication).
  - **Quota / rate / usage limits — ✅ VERIFIED:** Current provider quota documentation supplies separate method buckets and a daily default; the stated units are not a cash price. Evidence: [p4-yt-quota](https://developers.google.com/youtube/data/determine_quota_cost).
  - **API/service terms and data/content rights — ✅ VERIFIED:** Service terms and API-data/content rights are documented separately; this is restrictive terms evidence, not an open-data license. Evidence: [p4-yt-terms](https://developers.google.com/youtube/terms/api-services-terms-of-service), [p4-yt-policy](https://developers.google.com/youtube/terms/developer-policies).
  - **Date-qualified API maintenance — ✅ VERIFIED:** The official revision history records a dated API method/quota update on 2026-06-03. Evidence: [p4-yt-maint](https://developers.google.com/youtube/data/revision_history).
  - **Documentary Python feasibility — ✅ VERIFIED:** Provider publishes Python code samples through the API Explorer and documents a REST method; Python integration is documentarily feasible, not implemented or tested. Evidence: [p4-yt-code](https://developers.google.com/youtube/data/code_samples), [p4-yt-endpoint](https://developers.google.com/youtube/data/reference/rest/v3/search/list).
- **Unknown / inconclusive / partially open matters:**
  - **Free tier / pricing / eligibility — ❓ UNKNOWN:** A quota allocation is documented, but the reviewed provider pages do not establish a monetary price or an unconditional free tier; retain UNKNOWN. Evidence: [p4-yt-price-gap](https://developers.google.com/youtube/data/getting-started).
- **Accessibility:** 🚫 NOT_TESTED; Endpoint accessibility remains NOT_TESTED: Phase 4 permits documentary review only and no YouTube API endpoint was contacted. Evidence: [p4-yt-endpoint](https://developers.google.com/youtube/data/reference/rest/v3/search/list).
- **Material risk:** Possible duplicate/overlap with accepted `youtube-data-v3`; API/content terms restrict copying, storage and downstream use.
- **Recommended human disposition (not executed):** HOLD. Compare this lead with accepted `youtube-data-v3` before any separate-record decision; define intended data retention/display and review the restrictive API/content policies. No new proposal or catalog action.
- **Workflow trace:** 29 transition events; last event `event-d35e21ea8b8fb7b1` with hash `125f3a56ae97deef6aec7e4abf90ee4647289b8a4c320b3ba6afab82b09f01c5`.

### #2 — Visual Crossing Weather API

- **ID / provider / category:** `candidate-visual-crossing-weather-api-e97aed0fba` / Visual Crossing / `geospatial`; functional group: weather / climate, geospatial.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** Visual Crossing provider documentation identifies the Timeline Weather API and its weather-data functions. Evidence: [p4-vc-base](https://www.visualcrossing.com/resources/documentation/weather-api/timeline-weather-api/).
  - **Provider identity — ✅ VERIFIED:** The named Timeline API is documented on Visual Crossing-controlled documentation pages. Evidence: [p4-vc-base](https://www.visualcrossing.com/resources/documentation/weather-api/timeline-weather-api/).
  - **Official documentation / version — ✅ VERIFIED:** Current provider Timeline Weather API documentation is available; the reviewed page has no explicit semver label. Evidence: [p4-vc-docs](https://www.visualcrossing.com/resources/documentation/weather-api/timeline-weather-api/).
  - **Authentication — ✅ VERIFIED:** Provider explicitly documents a no-key request path and separately notes registration may be required for some advanced products. Evidence: [p4-vc-auth](https://www.visualcrossing.com/resources/documentation/weather-api/free-weather-api-no-key/).
  - **Free tier / pricing / eligibility — ✅ VERIFIED:** The provider documents free supported Timeline requests without key/account; free access is subject to fair use, commercial-use and attribution conditions. Evidence: [p4-vc-pricing](https://www.visualcrossing.com/resources/documentation/weather-api/free-weather-api-no-key/).
  - **Quota / rate / usage limits — ✅ VERIFIED:** Provider publishes qualitative, IP-based usage controls and explicitly says it does not guarantee a fixed request allowance. Evidence: [p4-vc-quota](https://www.visualcrossing.com/resources/documentation/weather-api/free-weather-api-no-key/).
  - **API/service terms and data/content rights — ✅ VERIFIED:** Provider service terms and no-key documentation distinguish access conditions from raw-data/derived-data rights and attribution. Evidence: [p4-vc-terms](https://www.visualcrossing.com/weather-service-terms/), [p4-vc-pricing](https://www.visualcrossing.com/resources/documentation/weather-api/free-weather-api-no-key/).
  - **Date-qualified API maintenance — ✅ VERIFIED:** Provider changelog dated 2026-09-04 contains 2026 Q3 feature additions. Evidence: [p4-vc-maint](https://www.visualcrossing.com/resources/documentation/weather-api/weather-api-changelog/).
  - **Documentary Python feasibility — ✅ VERIFIED:** Provider publishes runnable-shape Python requests code and a documented Timeline GET/JSON endpoint; feasibility is documentary and no code was run. Evidence: [p4-vc-python](https://www.visualcrossing.com/resources/documentation/weather-api/free-weather-api-no-key/), [p4-vc-endpoint](https://www.visualcrossing.com/resources/documentation/weather-api/timeline-weather-api/).
- **Unknown / inconclusive / partially open matters:**
  - No additional UNKNOWN/INCONCLUSIVE finding in the stored review dimensions; this does not imply operational or legal approval.
- **Accessibility:** 🚫 NOT_TESTED; Endpoint accessibility remains NOT_TESTED under the documentary-only plan; no Visual Crossing API endpoint was contacted. Evidence: [p4-vc-endpoint](https://www.visualcrossing.com/resources/documentation/weather-api/timeline-weather-api/).
- **Material risk:** No fixed anonymous allowance; fair-use/IP controls, required attribution and raw-weather redistribution restrictions.
- **Recommended human disposition (not executed):** HOLD. If considered further, first scope commercial/display/export use against the raw-weather redistribution limits, attribution and IP/fair-use controls; do not treat published docs as an operational test.
- **Workflow trace:** 28 transition events; last event `event-62126072427b44e1` with hash `da0fcd19934f0c72e5caa042fe11c1e70ea3deadedd867ad4a4bc34566029f55`.

### #3 — Bank Negara Malaysia Open Data

- **ID / provider / category:** `candidate-bank-negara-malaysia-open-data-b0cff73d9d` / Bank Negara Malaysia (BNM) / `government`; functional group: government / financial data, open-data portal.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** The BNM-controlled OpenAPI portal identifies a production Open API service and version. Evidence: [p4-bnm-base](https://apikijangportal.bnm.gov.my/openapi).
  - **Provider identity — ✅ VERIFIED:** The OpenAPI portal is controlled by Bank Negara Malaysia and labels the service BNM OpenAPI. Evidence: [p4-bnm-base](https://apikijangportal.bnm.gov.my/openapi).
  - **Official documentation / version — ✅ VERIFIED:** Provider API FAQ and production v1.0.0 explorer are available; endpoint operations are exposed through the interactive portal. Evidence: [p4-bnm-docs](https://apikijangportal.bnm.gov.my/faq).
  - **Free tier / pricing / eligibility — 🟨 PARTIALLY_VERIFIED:** The factual claim “free for everyone” is supported, but this workflow enum cannot safely map it to no-key/keyed access while authentication and usage conditions are unstated; preserve UNKNOWN and flag the taxonomy gap. Evidence: [p4-bnm-free](https://apikijangportal.bnm.gov.my/faq).
  - **Documentary Python feasibility — ✅ VERIFIED:** Provider docs specify HTTP API-client use and JSON Accept-version headers; a Python HTTP client can express this pattern, but auth/endpoint details still need confirmation and no code was run. Evidence: [p4-bnm-python](https://apikijangportal.bnm.gov.my/faq), [p4-bnm-endpoint](https://apikijangportal.bnm.gov.my/openapi).
- **Unknown / inconclusive / partially open matters:**
  - **Authentication — ❓ UNKNOWN:** The reviewed provider documentation does not establish an authentication requirement; retain UNKNOWN. Evidence: [p4-bnm-auth-gap](https://apikijangportal.bnm.gov.my/faq).
  - **Free tier / pricing / eligibility — 🟨 PARTIALLY_VERIFIED:** The factual claim “free for everyone” is supported, but this workflow enum cannot safely map it to no-key/keyed access while authentication and usage conditions are unstated; preserve UNKNOWN and flag the taxonomy gap. Evidence: [p4-bnm-free](https://apikijangportal.bnm.gov.my/faq).
  - **Quota / rate / usage limits — ❓ UNKNOWN:** No request quota/rate limit is established by the reviewed official pages; retain UNKNOWN. Evidence: [p4-bnm-quota-gap](https://apikijangportal.bnm.gov.my/openapi).
  - **API/service terms and data/content rights — ❓ UNKNOWN:** The official disclaimer is a service/accuracy disclaimer, not an API or dataset reuse license; data rights remain UNKNOWN. Evidence: [p4-bnm-terms](https://apikijangportal.bnm.gov.my/disclaimer).
  - **Date-qualified API maintenance — ❓ UNKNOWN:** No dated provider-controlled release/change record was identified in reviewed BNM sources; activity remains UNKNOWN. Evidence: [p4-bnm-maint-gap](https://apikijangportal.bnm.gov.my/openapi).
- **Accessibility:** 🚫 NOT_TESTED; Accessibility remains NOT_TESTED: the plan forbids candidate endpoint requests; the interactive explorer documentation is not a reachability observation. Evidence: [p4-bnm-endpoint](https://apikijangportal.bnm.gov.my/openapi).
- **Material risk:** Auth, numeric quotas and data reuse rights unresolved despite a free-for-everyone FAQ statement.
- **Recommended human disposition (not executed):** HOLD. Obtain a clear authentication/access condition, numeric quota and API/data reuse terms; the FAQ's free-use statement alone is not a complete access or rights profile.
- **Workflow trace:** 28 transition events; last event `event-c9faf2a20226d482` with hash `387d73837dcb3070df2e92085c6f553a1cb041823f3efaa16de8aaac55f54329`.

### #4 — bng2latlong

- **ID / provider / category:** `candidate-bng2latlong-97d9ad5db0` / GetTheData / `geospatial`; functional group: geospatial, coordinate conversion.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** The provider page documents the bng2latlong HTTP API and its coordinate conversion function. Evidence: [p4-bng-base](https://www.getthedata.com/bng2latlong).
  - **Provider identity — ✅ VERIFIED:** The named service and its endpoint documentation are published on GetTheData-controlled pages. Evidence: [p4-bng-base](https://www.getthedata.com/bng2latlong).
  - **Official documentation / version — ✅ VERIFIED:** Provider documentation includes endpoint syntax, response fields, and JSON/XML examples. Evidence: [p4-bng-docs](https://www.getthedata.com/bng2latlong).
  - **Free tier / pricing / eligibility — 🟨 PARTIALLY_VERIFIED:** The provider says the service is free to use for any purpose, but the workflow access-path enum cannot assert FREE_NO_KEY or FREE_WITH_KEY without an explicit auth statement; preserve UNKNOWN. Evidence: [p4-bng-free](https://www.getthedata.com/bng2latlong).
  - **Documentary Python feasibility — ✅ VERIFIED:** The documented GET/JSON interface is feasible to call using a Python HTTP client; no integration code or request was run. Evidence: [p4-bng-python](https://www.getthedata.com/bng2latlong), [p4-bng-endpoint](https://www.getthedata.com/bng2latlong).
- **Unknown / inconclusive / partially open matters:**
  - **Authentication — ❓ UNKNOWN:** The provider page does not explicitly state authentication requirements; retain UNKNOWN. Evidence: [p4-bng-auth-gap](https://www.getthedata.com/bng2latlong).
  - **Free tier / pricing / eligibility — 🟨 PARTIALLY_VERIFIED:** The provider says the service is free to use for any purpose, but the workflow access-path enum cannot assert FREE_NO_KEY or FREE_WITH_KEY without an explicit auth statement; preserve UNKNOWN. Evidence: [p4-bng-free](https://www.getthedata.com/bng2latlong).
  - **Quota / rate / usage limits — ❓ UNKNOWN:** No quota/rate limit is established by the reviewed provider page; retain UNKNOWN. Evidence: [p4-bng-quota-gap](https://www.getthedata.com/bng2latlong).
  - **API/service terms and data/content rights — ❓ UNKNOWN:** The free-use/optional-credit statement is preserved, but the reviewed page does not separate service permission from returned-data rights or identify a specific data license; keep the combined service/data license field UNKNOWN. Evidence: [p4-bng-license](https://www.getthedata.com/bng2latlong).
  - **Date-qualified API maintenance — ❓ UNKNOWN:** No dated release/change record is present in the reviewed provider page; retain UNKNOWN. Evidence: [p4-bng-maint-gap](https://www.getthedata.com/bng2latlong).
- **Accessibility:** 🚫 NOT_TESTED; Accessibility remains NOT_TESTED because endpoint calls are outside this Phase 4 plan. Evidence: [p4-bng-endpoint](https://www.getthedata.com/bng2latlong).
- **Material risk:** Free-use wording does not establish auth, quotas, formal license or returned-data rights.
- **Recommended human disposition (not executed):** HOLD. Clarify authentication, request limits and the rights in returned data separately from the provider's 'free to use' statement; do not infer no-key access.
- **Workflow trace:** 28 transition events; last event `event-1d70209516033545` with hash `24104ab5316f392708ce7f53aee2b4af01544e8a9201837428090c32456f3b2a`.

### #5 — IP2WHOIS Domain Lookup

- **ID / provider / category:** `candidate-ip2whois-domain-lookup-9f73a9ca7c` / IP2Location.io (current sign-up route; legacy IP2WHOIS brand retained in candidate name) / `developer-tools`; functional group: developer tools, domain / WHOIS lookup.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** Current provider-controlled documentation identifies the IP2WHOIS Domain WHOIS API and its v2 route. Evidence: [p4-ip2-base](https://www.ip2location.io/ip2whois-documentation).
  - **Provider identity — ✅ VERIFIED:** The IP2WHOIS product is documented on IP2Location.io and the legacy IP2WHOIS registration page routes new signup to that provider-controlled product. Evidence: [p4-ip2-base](https://www.ip2location.io/ip2whois-documentation), [p4-ip2-migration](https://www.ip2whois.com/register).
  - **Official documentation / version — ✅ VERIFIED:** Current provider documentation for the IP2WHOIS Domain WHOIS API is available and specifies endpoint v2 and response formats. Evidence: [p4-ip2-docs](https://www.ip2location.io/ip2whois-documentation).
  - **Authentication — ✅ VERIFIED:** Provider authentication documentation explicitly requires an API key for Domain WHOIS requests. Evidence: [p4-ip2-auth](https://www.ip2location.io/ip2whois-documentation).
  - **Free tier / pricing / eligibility — ✅ VERIFIED:** Current product documentation requires an API key; current pricing lists a $0 Free plan with 500 monthly WHOIS queries and required attribution. Evidence: [p4-ip2-pricing](https://www.ip2location.io/pricing), [p4-ip2-auth](https://www.ip2location.io/ip2whois-documentation).
  - **Quota / rate / usage limits — ✅ VERIFIED:** Current provider pricing gives plan-specific monthly WHOIS query counts and confirms the free allowance is finite. Evidence: [p4-ip2-quota](https://www.ip2location.io/pricing).
  - **Documentary Python feasibility — ✅ VERIFIED:** The provider documents a Python SDK and Python HTTP example, plus the endpoint; the example requires Python 3 syntax cleanup and was not executed. Evidence: [p4-ip2-python](https://www.ip2location.io/ip2whois-documentation), [p4-ip2-endpoint](https://www.ip2location.io/ip2whois-documentation).
- **Unknown / inconclusive / partially open matters:**
  - **API/service terms and data/content rights — ❓ UNKNOWN:** Reviewed IP2Location.io terms do not clearly extend to WHOIS data, and the IP2WHOIS privacy page does not define WHOIS response reuse/retention rights; keep service/data license UNKNOWN. Evidence: [p4-ip2-terms-scope](https://www.ip2location.io/ip2location_io_terms_of_service.pdf), [p4-ip2-privacy](https://www.ip2whois.com/privacy-policy).
  - **Date-qualified API maintenance — ❓ UNKNOWN:** No dated release/change record was located in the reviewed provider WHOIS documentation; retain UNKNOWN. Evidence: [p4-ip2-maint-gap](https://www.ip2location.io/ip2whois-documentation).
- **Accessibility:** 🚫 NOT_TESTED; Accessibility remains NOT_TESTED; no IP2WHOIS endpoint call or health check was made. Evidence: [p4-ip2-endpoint](https://www.ip2location.io/ip2whois-documentation).
- **Material risk:** WHOIS-specific output rights/retention unresolved; current API is routed through a different product/provider surface.
- **Recommended human disposition (not executed):** HOLD. Establish WHOIS-specific output reuse/retention rights and any registrant-data constraints; do not extend IP geolocation terms to WHOIS output.
- **Workflow trace:** 30 transition events; last event `event-412fa3243b465c65` with hash `6edf16b92db60e21e361ca7664c07c4f96d5472c2c60185184eb52696452dbc2`.

### #6 — TAGGUN Receipt OCR Scanning API

- **ID / provider / category:** `candidate-taggun-receipt-ocr-scanning-api-b55fde580b` / TAGGUN / `ai-ml`; functional group: document AI, receipt OCR.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** Official Taggun documentation describes the named receipt/invoice REST API; this does not establish live reachability. Evidence: [evidence-650ffc61a7c2eb7d](https://developers.taggun.io/reference/overview).
  - **Provider identity — ✅ VERIFIED:** Official Taggun developer and legal pages identify and govern the service. Evidence: [evidence-650ffc61a7c2eb7d](https://developers.taggun.io/reference/overview), [evidence-782f4f0dfce75d69](https://www.taggun.io/terms).
  - **Official documentation / version — ✅ VERIFIED:** Current provider API reference and Quick Start material describe request/response behavior. Evidence: [evidence-650ffc61a7c2eb7d](https://developers.taggun.io/reference/overview), [evidence-57d64e186accbe8c](https://developers.taggun.io/reference/overview).
  - **Authentication — ✅ VERIFIED:** Provider explicitly requires an account-issued API key in the apikey header. No credentials were collected or sent. Evidence: [evidence-55067243c9cd6edf](https://developers.taggun.io/reference/overview).
  - **Free tier / pricing / eligibility — ✅ VERIFIED:** Limited account-based trial: 30 days or 1,000 scans, whichever comes first; afterward the selected plan is billed unless cancelled. No ongoing free tier is documented. Evidence: [evidence-d136634906986c17](https://developers.taggun.io/docs/getting-started), [evidence-04ec91d432b8503f](https://www.taggun.io/pricing).
  - **Quota / rate / usage limits — ✅ VERIFIED:** Published throughput, body-size and plan-volume limits are supported; gateway rate-window semantics and precise scope remain unspecified by Taggun. Evidence: [evidence-dc7e8d37a8ced3ad](https://developers.taggun.io/docs/usage-limit), [evidence-04ec91d432b8503f](https://www.taggun.io/pricing).
  - **API/service terms and data/content rights — ✅ VERIFIED:** Service and uploaded-input claims are directly supported. This is not a blanket license to source receipts or an established license for extraction outputs. Evidence: [evidence-782f4f0dfce75d69](https://www.taggun.io/terms), [evidence-630f444f07f3b89b](https://developers.taggun.io/docs/security-and-privacy).
  - **Documentary Python feasibility — ✅ VERIFIED:** Official docs include a Python requests example and JSON response; no code was executed. Evidence: [evidence-57d64e186accbe8c](https://developers.taggun.io/reference/overview).
- **Unknown / inconclusive / partially open matters:**
  - **Date-qualified API maintenance — ❓ UNKNOWN:** The official changelog has August 2026 month-level entries but no exact activity day. Current maintenance remains UNKNOWN under the workflow date rule. Evidence: [evidence-8ba02c9983d9a423](https://developers.taggun.io/docs/change-logs).
- **Accessibility:** 🚫 NOT_TESTED; The endpoint is documented; accessibility was intentionally not tested and no health check was made. Evidence: [evidence-57d64e186accbe8c](https://developers.taggun.io/reference/overview).
- **Material risk:** Limited time/scan trial is not ongoing free production access; receipt-result rights remain incomplete.
- **Recommended human disposition (not executed):** HOLD. Distinguish the expiring/trial scan allowance from ongoing production access and resolve extracted-result/third-party-content rights and handling before any catalog decision.
- **Workflow trace:** 28 transition events; last event `event-89b92b129c618140` with hash `0860ab5a44bdedfc6356119f12966d2c47f0fe957e2ae8699cb55fbc3d01abf2`.

### #7 — APOD

- **ID / provider / category:** `candidate-apod-fb659cb117` / NASA (APOD product; route-specific current support/auth remain limited) / `source category not supplied`; functional group: science / space, imagery and metadata.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** NASA identifies APOD and the migrated replacement route; legacy API retirement has a published date. Evidence: [evidence-8274d5f6b9904322](https://api.nasa.gov/), [evidence-c45270ae059757cd](https://api.nasa.gov/assets/files/apod/APOD-APIs-and-RSS-info.pdf).
  - **Provider identity — ✅ VERIFIED:** NASA API portal and NASA-linked APOD guide identify the service and replacement route. Evidence: [evidence-8274d5f6b9904322](https://api.nasa.gov/), [evidence-c45270ae059757cd](https://api.nasa.gov/assets/files/apod/APOD-APIs-and-RSS-info.pdf).
  - **Official documentation / version — ✅ VERIFIED:** NASA portal and APOD Basic guide document the current JSON route/feed formats. Evidence: [evidence-8274d5f6b9904322](https://api.nasa.gov/), [evidence-c45270ae059757cd](https://api.nasa.gov/assets/files/apod/APOD-APIs-and-RSS-info.pdf).
  - **Date-qualified API maintenance — ✅ VERIFIED:** Provider notice dates migration to 2026-09-10 and schedules legacy archival for 2026-12-01. Evidence: [evidence-59b8af20adcbe291](https://api.nasa.gov/).
  - **Documentary Python feasibility — ✅ VERIFIED:** The documented HTTPS GET and structured JSON are suitable for a Python HTTP client; no code or request was run. Evidence: [evidence-c45270ae059757cd](https://api.nasa.gov/assets/files/apod/APOD-APIs-and-RSS-info.pdf), [evidence-8e1fc66373f97f29](https://api.nasa.gov/).
- **Unknown / inconclusive / partially open matters:**
  - **Authentication — ❓ UNKNOWN:** NASA general API authentication guidance and the legacy api_key model do not establish authentication behavior for the migrated WordPress APOD route; route-specific auth remains UNKNOWN. No key was used. Evidence: [evidence-017412754bf161b6](https://api.nasa.gov/assets/html/authentication.html), [evidence-8274d5f6b9904322](https://api.nasa.gov/).
  - **Free tier / pricing / eligibility — ❓ UNKNOWN:** No APOD-specific monetary price/free-tier statement was found in reviewed NASA documentation; exploratory access and demo-key provisions are not classified as a verified free tier. Evidence: [evidence-d1f1f71f77193b16](https://api.nasa.gov/).
  - **Quota / rate / usage limits — ❓ UNKNOWN:** General NASA limits are 1,000/hour per registered key and 30/hour plus 50/day/IP for DEMO_KEY; NASA warns limits may vary by service. Quota for the migrated APOD route remains UNKNOWN. Evidence: [evidence-017412754bf161b6](https://api.nasa.gov/assets/html/authentication.html), [evidence-03018c60d1b79a58](https://api.nasa.gov/assets/html/authentication.html).
  - **API/service terms and data/content rights — ❓ UNKNOWN:** No uniform APOD service/whole-feed license was established. NASA-origin content is subject to NASA media guidelines; third-party images require per-item rights review and NASA does not convey those rights. Evidence: [evidence-08d4e90a332c3c64](https://www.nasa.gov/nasa-brand-center/images-and-media/), [evidence-7de0223190dad581](https://science.nasa.gov/apod/apod-about/).
- **Accessibility:** 🚫 NOT_TESTED; The migrated APOD GET route is documented but was intentionally not contacted. Evidence: [evidence-8e1fc66373f97f29](https://api.nasa.gov/).
- **Material risk:** Migrated route differs from legacy API guidance; media rights vary by asset and third-party source.
- **Recommended human disposition (not executed):** HOLD. Resolve APOD-route-specific authentication and fee/tier, and evaluate rights asset-by-asset, especially third-party imagery; do not generalize NASA media guidance into an APOD feed license.
- **Workflow trace:** 28 transition events; last event `event-c7da00ccc28c7cdd` with hash `c9f50b520f206384063d6b7fe21a2f66fe09e89e0eed4d41a611219f8e975961`.

### #8 — CyCAT.org API

- **ID / provider / category:** `candidate-cycat-org-api-d423696460` / CyCAT.org / `identity-security`; functional group: cybersecurity, resource catalogue.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** CyCAT Services identifies the API and links provider-hosted OpenAPI documentation with GET operations. Evidence: [evidence-4ccca13826dc4fc8](https://cycat.org/services/), [evidence-b9569ffe204f07bf](https://api.cycat.org/swagger.json).
  - **Provider identity — ✅ VERIFIED:** Official CyCAT site identifies the catalogue and links API documentation on api.cycat.org. Evidence: [evidence-93b6667c6473abf9](https://cycat.org/about/), [evidence-4ccca13826dc4fc8](https://cycat.org/services/).
  - **Official documentation / version — ✅ VERIFIED:** Official Services page, PDF link and provider-hosted OpenAPI 2.0 document are available. Evidence: [evidence-4ccca13826dc4fc8](https://cycat.org/services/), [evidence-b9569ffe204f07bf](https://api.cycat.org/swagger.json).
  - **Documentary Python feasibility — ✅ VERIFIED:** Official docs show GET routes and JSON responses, sufficient for a standard Python HTTP client; no code was executed. Evidence: [evidence-8860950dfa0d285a](https://cycat.org/services/).
- **Unknown / inconclusive / partially open matters:**
  - **Authentication — ❓ UNKNOWN:** Public GET examples omit credentials and the spec lacks a security declaration, but no explicit provider statement establishes no-auth; requirements remain UNKNOWN. Evidence: [evidence-6a9cad572f54e8be](https://api.cycat.org/swagger.json), [evidence-4ccca13826dc4fc8](https://cycat.org/services/).
  - **Free tier / pricing / eligibility — ❓ UNKNOWN:** No monetary price/free-tier statement was found in reviewed official sources; public/open API wording is insufficient to classify access price. Evidence: [evidence-8aab84996b5fd068](https://cycat.org/services/).
  - **Quota / rate / usage limits — ❓ UNKNOWN:** No request quota/rate-limit schedule was found in reviewed official docs; unlimited use is not inferred. Evidence: [evidence-1a748be87b015140](https://api.cycat.org/swagger.json).
  - **API/service terms and data/content rights — ⚠️ INCONCLUSIVE:** Official site says CyCAT.org content is CC-BY-SA and the OpenAPI spec lists CC-BY, but scope for API service/output and third-party records is unclear; API/data rights remain UNKNOWN. Evidence: [evidence-19f44987a5f44713](https://cycat.org/services/), [evidence-2cbbf05592eb5915](https://api.cycat.org/swagger.json).
  - **Date-qualified API maintenance — ❓ UNKNOWN:** Spec lists version 0.9, but reviewed official sources provide no dated release/change record; current maintenance remains UNKNOWN. Evidence: [evidence-b9569ffe204f07bf](https://api.cycat.org/swagger.json), [evidence-4ccca13826dc4fc8](https://cycat.org/services/).
- **Accessibility:** 🚫 NOT_TESTED; GET routes are documented, but no API operation or health endpoint was contacted. Evidence: [evidence-8860950dfa0d285a](https://cycat.org/services/).
- **Material risk:** License scope unclear between site content/spec/API outputs and third-party records.
- **Recommended human disposition (not executed):** HOLD. Resolve whether the stated CC-BY-SA site content and the OpenAPI spec's CC-BY label cover API outputs/third-party records, plus explicit auth/quota terms.
- **Workflow trace:** 28 transition events; last event `event-2d6fbc237802c37f` with hash `0ae0678a6f7d6663b6d9c2ee5d76a52ee8c1e104e275b3797839ca172b470fda`.

### #9 — Groundwater Wells, Aquifers and Registry API

- **ID / provider / category:** `candidate-groundwater-wells-aquifers-and-registry-16109d78d4` / Government of British Columbia (BC Data Catalogue) / `open-data`; functional group: environment / water, government geospatial data.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** Official BC documentation identifies the GWELLS API and documents operations. Evidence: [evidence-a53948e261935294](https://apps.nrs.gov.bc.ca/gwells/api/), [evidence-4b33a77295611b13](https://apps.nrs.gov.bc.ca/gwells/api/?format=openapi).
  - **Provider identity — ✅ VERIFIED:** The API is published on a Province of British Columbia host with official BC terms. Evidence: [evidence-a53948e261935294](https://apps.nrs.gov.bc.ca/gwells/api/), [evidence-082526b525d50f7d](https://www2.gov.bc.ca/gov/content/data/policy-standards/data-policies/open-data/api-terms-of-use-for-ogl-information).
  - **Official documentation / version — ✅ VERIFIED:** Official Swagger UI and generated OpenAPI document are available; UI lists v1/v2 groups. Evidence: [evidence-a53948e261935294](https://apps.nrs.gov.bc.ca/gwells/api/), [evidence-4b33a77295611b13](https://apps.nrs.gov.bc.ca/gwells/api/?format=openapi).
  - **Authentication — ✅ VERIFIED:** Provider OpenAPI declares a global required apiKey security scheme in the JWT header. Credential issuance/token lifecycle remains undocumented in reviewed sources. Evidence: [evidence-e1946a5b9b6c7010](https://apps.nrs.gov.bc.ca/gwells/api/?format=openapi).
  - **API/service terms and data/content rights — ✅ VERIFIED:** Service/API terms and the specific dataset license are distinct. Rights are not inferred for other API resources or records. Evidence: [evidence-082526b525d50f7d](https://www2.gov.bc.ca/gov/content/data/policy-standards/data-policies/open-data/api-terms-of-use-for-ogl-information), [evidence-fac02b7ae296c2e2](https://www2.gov.bc.ca/gov/content/data/policy-standards/data-policies/open-data/open-government-licence-bc), [evidence-52230134c2ff9410](https://catalogue.data.gov.bc.ca/dataset/e4731a85-ffca-4112-8caf-cb0a96905778).
  - **Documentary Python feasibility — ✅ VERIFIED:** Documented HTTPS GET and JSON/OpenAPI schema are sufficient for a standard Python HTTP client; no code ran. Evidence: [evidence-e5018e542239104e](https://apps.nrs.gov.bc.ca/gwells/api/), [evidence-4b33a77295611b13](https://apps.nrs.gov.bc.ca/gwells/api/?format=openapi).
- **Unknown / inconclusive / partially open matters:**
  - **Free tier / pricing / eligibility — ❓ UNKNOWN:** No API monetary price/free tier is published in reviewed docs. OGL-BC governs eligible data, not API price. Evidence: [evidence-fcb722aef64fb93c](https://www2.gov.bc.ca/gov/content/data/policy-standards/data-policies/open-data/api-terms-of-use-for-ogl-information).
  - **Quota / rate / usage limits — ❓ UNKNOWN:** API Terms allow BC to impose or adjust limits without notice but publish no numeric request quota/rate/window; exact quota remains UNKNOWN. Evidence: [evidence-aa542331805467d4](https://www2.gov.bc.ca/gov/content/data/policy-standards/data-policies/open-data/api-terms-of-use-for-ogl-information).
  - **Date-qualified API maintenance — ❓ UNKNOWN:** No dated API release/change history was identified. The future catalogue timestamp and dataset “On Going” status do not establish API maintenance; current activity remains UNKNOWN. Evidence: [evidence-4b33a77295611b13](https://apps.nrs.gov.bc.ca/gwells/api/?format=openapi), [evidence-bc67fb996accd7a2](https://catalogue.data.gov.bc.ca/dataset/e4731a85-ffca-4112-8caf-cb0a96905778).
- **Accessibility:** 🚫 NOT_TESTED; The GET route is documented but no API request or health check was made. Evidence: [evidence-e5018e542239104e](https://apps.nrs.gov.bc.ca/gwells/api/).
- **Material risk:** OGL-BC applies to an identified dataset record, not automatically to the service/API or every returned dataset.
- **Recommended human disposition (not executed):** HOLD. Establish API price/auth/quota and confirm that OGL-BC applies only to the specific catalogue dataset records, not all API responses or third-party data.
- **Workflow trace:** 29 transition events; last event `event-9a6b4776908fd237` with hash `a79e6b7e0ad7c800a6d4be014b4c11f90fa7f3b0c4da529bb21a7b0ea9ab2957`.

### #10 — Xero Assets API

- **ID / provider / category:** `candidate-xero-assets-api-585af6f87a` / Xero / `finance`; functional group: finance / accounting, business SaaS.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** Xero publishes Assets API overview/resource docs, version 1.0 and REST operations. Evidence: [evidence-febde8407962f2a3](https://developer.xero.com/documentation/api/assets/overview), [evidence-2fc7d9773c3d0717](https://developer.xero.com/documentation/api/assets/assets).
  - **Provider identity — ✅ VERIFIED:** Xero developer portal and platform terms identify the API/provider. Evidence: [evidence-febde8407962f2a3](https://developer.xero.com/documentation/api/assets/overview), [evidence-9417bbf3934cc513](https://developer.xero.com/xero-developer-platform-terms-conditions).
  - **Official documentation / version — ✅ VERIFIED:** Official overview and resource-level methods/parameters are available. Evidence: [evidence-febde8407962f2a3](https://developer.xero.com/documentation/api/assets/overview), [evidence-2fc7d9773c3d0717](https://developer.xero.com/documentation/api/assets/assets).
  - **Authentication — ✅ VERIFIED:** Xero requires OAuth 2.0 access; assets.read is documented for reads and assets for view/manage. Code/PKCE user-consent and paid Custom Connection flows are separate. No credentials were collected. Evidence: [evidence-488a4642d126a20a](https://developer.xero.com/documentation/guides/oauth2/scopes/), [evidence-521fbbe3ab0eca15](https://developer.xero.com/documentation/guides/oauth2/overview).
  - **Free tier / pricing / eligibility — ✅ VERIFIED:** Limited no-charge development exists: Starter app-partner tier is no charge with up to five connections and a free demo company. This is not a free live Xero Accounting subscription. Custom Connections incur separate organization-billed fees; higher partner tiers cost extra. Evidence: [evidence-efe25ce13f0afe0c](https://developer.xero.com/pricing), [evidence-90ec19f834b3cd6f](https://developer.xero.com/documentation/development-accounts/), [evidence-521fbbe3ab0eca15](https://developer.xero.com/documentation/guides/oauth2/overview).
  - **Quota / rate / usage limits — ✅ VERIFIED:** Tiered rates are explicit on OAuth limits and pricing pages; generic header gloss is internally inconsistent and is retained as caveat. Evidence: [evidence-0ba90da6a34a5457](https://developer.xero.com/documentation/guides/oauth2/limits), [evidence-efe25ce13f0afe0c](https://developer.xero.com/pricing), [evidence-d4e47ab4febbfe76](https://developer.xero.com/documentation/best-practices/api-call-efficiencies/rate-limits).
  - **API/service terms and data/content rights — ✅ VERIFIED:** Platform terms and data-use restrictions are recorded separately; this is not legal advice or a grant of redistribution rights. Evidence: [evidence-9417bbf3934cc513](https://developer.xero.com/xero-developer-platform-terms-conditions).
  - **Documentary Python feasibility — ✅ VERIFIED:** REST/JSON operations and OAuth are documented; Xero lists a Python SDK, though Assets-specific SDK support was not established. Custom Python HTTP integration is feasible; no code ran. Evidence: [evidence-a35d71a59cc71a70](https://developer.xero.com/documentation/api/assets/settings), [evidence-816cdd4599752961](https://developer.xero.com/documentation/sdks-and-tools/libraries/overview), [evidence-521fbbe3ab0eca15](https://developer.xero.com/documentation/guides/oauth2/overview).
- **Unknown / inconclusive / partially open matters:**
  - **Date-qualified API maintenance — ❓ UNKNOWN:** Only Assets-specific dated release located is initial v1.0 on 2016-07-26; current v1.0 docs do not establish recent maintenance, so current activity remains UNKNOWN. Evidence: [evidence-63bcc4f07b443755](https://developer.xero.com/documentation/api/assets/release-notes), [evidence-2fc7d9773c3d0717](https://developer.xero.com/documentation/api/assets/assets).
- **Accessibility:** 🚫 NOT_TESTED; Xero Assets endpoints are documented but none were contacted. Evidence: [evidence-a35d71a59cc71a70](https://developer.xero.com/documentation/api/assets/settings).
- **Material risk:** Developer Starter is not a free live accounting subscription; Xero terms limit purpose/AI data use.
- **Recommended human disposition (not executed):** HOLD. Define target Xero connection/tier and live-account costs; review approved-purpose, consent and AI-data restrictions and the absence of current Assets-specific maintenance evidence.
- **Workflow trace:** 31 transition events; last event `event-d064219a096e496d` with hash `a9ef5d9501d20d3eae40a7ba1d9a9b00f073246d5cd6a2447bc212dce8cd4aaf`.

### #11 — USDA ERS

- **ID / provider / category:** `candidate-usda-ers-be60dab8d0` / USDA Economic Research Service (ERS) / `agriculture`; functional group: agriculture / economics, government data.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** ERS documents a named ARMS Data API under its official Data APIs program. This verifies the ARMS API only; the imported summary's separate geospatial component remains unconfirmed. Evidence: [evidence-6e00001d084d45ae](https://www.ers.usda.gov/developer/data-apis), [evidence-7295bc6857708945](https://www.ers.usda.gov/developer/data-apis/arms-data-api).
  - **Provider identity — ✅ VERIFIED:** The documentation is on ers.usda.gov and identifies USDA Economic Research Service as the source of the API documentation. Evidence: [evidence-6e00001d084d45ae](https://www.ers.usda.gov/developer/data-apis), [evidence-7295bc6857708945](https://www.ers.usda.gov/developer/data-apis/arms-data-api).
  - **Official documentation / version — ✅ VERIFIED:** Public provider documentation identifies ARMS JSON REST/GraphQL resources, request methods, and examples; the ARMS page is marked updated 2025-01-01. Evidence: [evidence-7295bc6857708945](https://www.ers.usda.gov/developer/data-apis/arms-data-api).
  - **Authentication — ✅ VERIFIED:** Record the key requirement without inferring that a free key-management service makes ERS data access free. Evidence: [evidence-ccce2b8546e8a4e7](https://www.ers.usda.gov/developer/data-apis/arms-data-api), [evidence-7295bc6857708945](https://www.ers.usda.gov/developer/data-apis/arms-data-api).
  - **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED:** The 1,000/hour value is the shared api.data.gov default, not a confirmed ARMS-only limit. Evidence: [evidence-35042e0d30cbde7d](https://api.data.gov/docs/developer-manual/).
  - **API/service terms and data/content rights — ✅ VERIFIED:** Record only the express API-use and attribution provisions; do not extend them to unrelated datasets or infer an open-data license. Evidence: [evidence-4d28f51df9f60964](https://www.ers.usda.gov/developer/api-terms-of-service).
  - **Documentary Python feasibility — ✅ VERIFIED:** The documented HTTPS REST/JSON interface can be called with a Python HTTP client; the provider pages reviewed did not establish a Python SDK, and no code or API request was tested. Evidence: [evidence-097a6c6b2a4f7a33](https://www.ers.usda.gov/developer/data-apis/arms-data-api).
- **Unknown / inconclusive / partially open matters:**
  - **Free tier / pricing / eligibility — ❓ UNKNOWN:** The reviewed ERS pages do not explicitly price ARMS/data API access or establish an unconditional free tier. A free api.data.gov key-management service is not proof that the ERS data service is free. Evidence: [evidence-6e00001d084d45ae](https://www.ers.usda.gov/developer/data-apis), [evidence-4d28f51df9f60964](https://www.ers.usda.gov/developer/api-terms-of-service).
  - **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED:** The 1,000/hour value is the shared api.data.gov default, not a confirmed ARMS-only limit. Evidence: [evidence-35042e0d30cbde7d](https://api.data.gov/docs/developer-manual/).
  - **Date-qualified API maintenance — ❓ UNKNOWN:** The provider lists an ARMS data release dated 2024-12-18, but this is a dataset update rather than an API release/maintenance record. No API-specific maintenance activity was established. Evidence: [evidence-8c8428eee981ad31](https://www.ers.usda.gov/developer/data-apis/arms-data-api/updates-and-revisions).
- **Accessibility:** 🚫 NOT_TESTED; No candidate endpoint was contacted. Public REST documentation does not establish present live reachability. Evidence: [evidence-097a6c6b2a4f7a33](https://www.ers.usda.gov/developer/data-apis/arms-data-api).
- **Material risk:** Generic key-service limits and dataset-release dates are not ERS-specific price/quota/maintenance guarantees.
- **Recommended human disposition (not executed):** HOLD. Clarify ERS/ARMS-specific cost and limits, data-set rights, and API maintenance; do not convert an api.data.gov key or generic quota into an ERS guarantee.
- **Workflow trace:** 26 transition events; last event `event-def15aa1660ad9e8` with hash `edfc39b7237146f4107cb3a8f36fd1a8348da56c7be5cbd801638459316f8f1f`.

### #12 — Browshot

- **ID / provider / category:** `candidate-browshot-e01a9ec3f5` / Browshot / `developer-tools`; functional group: web automation, screenshots.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** Provider-hosted documentation describes Browshot API v1.31 and screenshot-related REST resources. Evidence: [evidence-731a568d76bc44dd](https://browshot.com/api/documentation).
  - **Provider identity — ✅ VERIFIED:** The API reference and migration notice are published on browshot.com and identify the Browshot service. Evidence: [evidence-731a568d76bc44dd](https://browshot.com/api/documentation), [evidence-6a0971c1188c0be0](https://browshot.com/blog/2026/11/api-migrated-to-screenshotcenter.html).
  - **Official documentation / version — ✅ VERIFIED:** Official documentation describes API v1.31, REST methods, response format, and a Python library. Evidence: [evidence-731a568d76bc44dd](https://browshot.com/api/documentation).
  - **Authentication — ✅ VERIFIED:** The provider API reference requires the key request parameter. Evidence: [evidence-b502b6b444528cae](https://browshot.com/api/documentation).
  - **Free tier / pricing / eligibility — ✅ VERIFIED:** The provider advertises a free browser plan capped at 100 screenshots per month; paid screenshot usage consumes credits. This is not unlimited free API access. Evidence: [evidence-de5fb3191d7d8465](https://browshot.com/features).
  - **Quota / rate / usage limits — ✅ VERIFIED:** The documented monthly screenshot allowance and credit-based paid use are plan/usage limits, not a universal REST request throttle. Evidence: [evidence-de5fb3191d7d8465](https://browshot.com/features).
  - **Date-qualified API maintenance — ✅ VERIFIED:** A provider notice dated 2026-11-05 reports migration, unchanged API behavior, continued v1 support, and API 2.0 development. This documents activity, not a future support guarantee. Evidence: [evidence-6a0971c1188c0be0](https://browshot.com/blog/2026/11/api-migrated-to-screenshotcenter.html).
  - **Documentary Python feasibility — ✅ VERIFIED:** Browshot publishes a Python library and examples. Neither package installation nor API integration was tested. Evidence: [evidence-880a8719fa2fcba0](https://browshot.com/api/libraries/python).
- **Unknown / inconclusive / partially open matters:**
  - **API/service terms and data/content rights — ❓ UNKNOWN:** The Terms page was last updated 2015-06-30 and does not establish current API/data-use rights; retain UNKNOWN rather than extrapolating a license. Evidence: [evidence-47201a461f1c59ba](https://browshot.com/terms).
- **Accessibility:** 🚫 NOT_TESTED; No Browshot API endpoint was contacted. Documentation and a migration notice do not prove current endpoint reachability. Evidence: [evidence-731a568d76bc44dd](https://browshot.com/api/documentation).
- **Material risk:** Provider terms are stale (2015); present API/data reuse rights unresolved.
- **Recommended human disposition (not executed):** HOLD. Obtain current API/data-use terms; the reviewed Terms page is dated 2015 and does not settle present rights.
- **Workflow trace:** 25 transition events; last event `event-711cd78420e466cb` with hash `768d4c02a198c1523e4f1abe01bf592b8ee7b7773c1d4ec8054c2e88fb68da63`.

### #13 — CFB v3 Scores

- **ID / provider / category:** `candidate-cfb-v3-scores-274b76b3c0` / SportsDataIO / `entertainment-media`; functional group: sports data, media.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** The provider's NCAA Football reference documents the CFB v3 API and its endpoint families. Evidence: [evidence-4daee2a263e1d00a](https://sportsdata.io/developers/api-documentation/ncaa-football).
  - **Provider identity — ✅ VERIFIED:** SportsDataIO's developer portal identifies its College Football API and access programs. Evidence: [evidence-4daee2a263e1d00a](https://sportsdata.io/developers/api-documentation/ncaa-football), [evidence-0ed490cb652c8f79](https://sportsdata.io/developers).
  - **Official documentation / version — ✅ VERIFIED:** The provider publishes endpoint paths, call intervals, parameters, formats, and response-field documentation for College Football. Evidence: [evidence-4daee2a263e1d00a](https://sportsdata.io/developers/api-documentation/ncaa-football).
  - **Authentication — ✅ VERIFIED:** Provider documentation marks the feeds subscription-required. This does not conflate the scrambled free trial with real feed access. Evidence: [evidence-4daee2a263e1d00a](https://sportsdata.io/developers/api-documentation/ncaa-football).
  - **Free tier / pricing / eligibility — ✅ VERIFIED:** A free trial exists with scrambled data and a small daily limit, but the provider says trial data is not real and is not for analysis/display. Real next-day College Football is offered in the paid Discovery Lab; production/commercial real-time use is agreement-specific. Evidence: [evidence-0ed490cb652c8f79](https://sportsdata.io/developers).
  - **Quota / rate / usage limits — ✅ VERIFIED:** The numeric daily range applies to Discovery Lab. The free-trial limit is qualitative, and the commercial allowance is contract-specific. Evidence: [evidence-1f23f0cac3efddc5](https://sportsdata.io/developers), [evidence-4daee2a263e1d00a](https://sportsdata.io/developers/api-documentation/ncaa-football).
  - **Documentary Python feasibility — ✅ VERIFIED:** A Python HTTP client can use the documented HTTPS REST endpoints and JSON/XML responses. No integration or live request was tested. Evidence: [evidence-f13fddde9c6ba664](https://sportsdata.io/developers/api-documentation/ncaa-football).
- **Unknown / inconclusive / partially open matters:**
  - **API/service terms and data/content rights — ❓ UNKNOWN:** General terms establish limited use of purchased services but do not establish the specific College Football feed's display, redistribution, or commercial-data license; that remains subscription/contract-specific. Evidence: [evidence-dadf2bdd01a04e21](https://sportsdata.io/terms-of-service).
  - **Date-qualified API maintenance — ❓ UNKNOWN:** No dated CFB release/change or maintenance record was established. Feed refresh intervals describe data freshness, not API software maintenance. Evidence: [evidence-4daee2a263e1d00a](https://sportsdata.io/developers/api-documentation/ncaa-football).
- **Accessibility:** 🚫 NOT_TESTED; No College Football endpoint was contacted and no credentials were used. Public endpoint documentation does not establish present reachability. Evidence: [evidence-f13fddde9c6ba664](https://sportsdata.io/developers/api-documentation/ncaa-football).
- **Material risk:** Free trial is scrambled/non-real; real CFB feeds are paid/contractual and rights remain feed-specific.
- **Recommended human disposition (not executed):** HOLD. Distinguish scrambled trial data from real delayed/production feeds and obtain feed-specific display/redistribution/commercial terms and contract pricing.
- **Workflow trace:** 24 transition events; last event `event-7633e1aa88113c44` with hash `55bbfcb089dc7c462f1f296efd1726c25230204fd8c6ad6136f389e4c1e6fd1b`.

### #15 — ExchangeRate-API

- **ID / provider / category:** `candidate-exchangerate-api-47f3e350f1` / ExchangeRate-API / `finance`; functional group: finance, currency data.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** ExchangeRate-API documents its currency API and a separate Open Access endpoint. Evidence: [evidence-5b8657f6151c9128](https://www.exchangerate-api.com/docs/overview), [evidence-70b57f2154fa0729](https://www.exchangerate-api.com/docs/free).
  - **Provider identity — ✅ VERIFIED:** The documentation and terms are published on exchangerate-api.com and identify the provider. Evidence: [evidence-5b8657f6151c9128](https://www.exchangerate-api.com/docs/overview), [evidence-70b57f2154fa0729](https://www.exchangerate-api.com/docs/free).
  - **Official documentation / version — ✅ VERIFIED:** Provider documentation covers rate and pair conversion, authentication, Open Access, and usage/quota endpoints. Evidence: [evidence-5b8657f6151c9128](https://www.exchangerate-api.com/docs/overview), [evidence-63b1f4b64045d536](https://www.exchangerate-api.com/docs/authentication).
  - **Authentication — ✅ VERIFIED:** Authentication differs by access mode; do not describe the whole service as simply keyed or no-key. Evidence: [evidence-63b1f4b64045d536](https://www.exchangerate-api.com/docs/authentication), [evidence-70b57f2154fa0729](https://www.exchangerate-api.com/docs/free).
  - **Free tier / pricing / eligibility — ✅ VERIFIED:** There is a separately rate-limited no-key Open Access path with attribution and redistribution restrictions, and a registered Free Plan with 1,500 monthly requests. These are separate access paths. Evidence: [evidence-70b57f2154fa0729](https://www.exchangerate-api.com/docs/free), [evidence-b6628ea4f03078f7](https://www.exchangerate-api.com/#pricing).
  - **Quota / rate / usage limits — ✅ VERIFIED:** The 1,500 monthly allowance applies to the registered Free Plan, not the no-key endpoint. The observed Open Access advice is not recorded as a fixed request-per-time limit. Evidence: [evidence-3db67455d550267c](https://www.exchangerate-api.com/docs/request-quota-endpoint), [evidence-b6628ea4f03078f7](https://www.exchangerate-api.com/#pricing), [evidence-70b57f2154fa0729](https://www.exchangerate-api.com/docs/free).
  - **API/service terms and data/content rights — ✅ VERIFIED:** Record the express caching and redistribution limitations without assuming commercial resale or redistribution rights. Evidence: [evidence-46658c11611a0982](https://www.exchangerate-api.com/terms).
  - **Documentary Python feasibility — ✅ VERIFIED:** The provider publishes a Python HTTP/JSON example; it was not run and is not a live integration test. Evidence: [evidence-61d22f41275d1abd](https://www.exchangerate-api.com/docs/python-currency-api).
- **Unknown / inconclusive / partially open matters:**
  - **Date-qualified API maintenance — ❓ UNKNOWN:** The reviewed pages document exchange-rate update cadence, not a dated API release or maintenance event; no such maintenance record was established. Evidence: [evidence-5b8657f6151c9128](https://www.exchangerate-api.com/docs/overview).
- **Accessibility:** 🚫 NOT_TESTED; No currency endpoint was requested; public docs do not establish present live endpoint accessibility. Evidence: [evidence-5b8657f6151c9128](https://www.exchangerate-api.com/docs/overview).
- **Material risk:** No-key and keyed free access paths have different limits; redistribution/resale remains restricted.
- **Recommended human disposition (not executed):** HOLD. Choose the intended access path and review its distinct quota/update/caching and redistribution rules; do not collapse no-key Open Access and the keyed Free Plan.
- **Workflow trace:** 26 transition events; last event `event-385927b6e3ef38bf` with hash `597c4c5590559069ab7edb9c65c83de98d4eca6b7502443d4ccc7b162ba6b345`.

### #16 — JSON2Video

- **ID / provider / category:** `candidate-json2video-ae32ed51fc` / JSON2Video / `entertainment-media`; functional group: media, video generation.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** Provider documentation identifies JSON2Video's public v2 REST resources and API host. Evidence: [evidence-e44be8ac4afc77e9](https://json2video.com/docs/v2/reference/api-endpoints).
  - **Provider identity — ✅ VERIFIED:** The API reference and Developer API Terms are on json2video.com and identify JSON2Video as provider. Evidence: [evidence-e44be8ac4afc77e9](https://json2video.com/docs/v2/reference/api-endpoints), [evidence-168dbb60d06f3047](https://json2video.com/legal/terms-of-use.html).
  - **Official documentation / version — ✅ VERIFIED:** Public provider docs cover v2 endpoints, authentication, plan/credit rules, and rate-limit/usage guidance. Evidence: [evidence-e44be8ac4afc77e9](https://json2video.com/docs/v2/reference/api-endpoints), [evidence-847f44b4a8d5c3b3](https://json2video.com/docs/v2/reference/credits/limits).
  - **Authentication — ✅ VERIFIED:** The provider documents the x-api-key header as required for public v2 API calls. Evidence: [evidence-4b6170efa18cc481](https://json2video.com/docs/v2/reference/api-endpoints).
  - **Free tier / pricing / eligibility — ✅ VERIFIED:** The free plan grants 600 nonrenewable credits, a 60-second render limit, possible watermarking, and personal/evaluation-only use. Commercial output use is associated with paid plans subject to terms. Evidence: [evidence-c0c4003752ddf87a](https://json2video.com/docs/v2/reference/credits/plans).
  - **Quota / rate / usage limits — ✅ VERIFIED:** The documented limits concern render credits, video duration, request body size, and polling guidance; no numerical general throughput limit is claimed. Evidence: [evidence-847f44b4a8d5c3b3](https://json2video.com/docs/v2/reference/credits/limits).
  - **API/service terms and data/content rights — ✅ VERIFIED:** This is an API/product-specific summary; third-party media and assets remain subject to their separate rights. Evidence: [evidence-168dbb60d06f3047](https://json2video.com/legal/terms-of-use.html).
  - **Documentary Python feasibility — ✅ VERIFIED:** The API is documented as HTTPS REST/JSON, so it can be called using a Python HTTP client. No Python SDK was established or integration tested. Evidence: [evidence-134e9bcde8ad7379](https://json2video.com/docs/v2/reference/api-endpoints/movies-create).
- **Unknown / inconclusive / partially open matters:**
  - **Date-qualified API maintenance — ❓ UNKNOWN:** The July 2026 terms update is legal activity, not evidence of an API release or maintenance event. No dated API change record was established. Evidence: [evidence-168dbb60d06f3047](https://json2video.com/legal/terms-of-use.html).
- **Accessibility:** 🚫 NOT_TESTED; No API request or render was made. Published endpoint docs do not establish current live reachability. Evidence: [evidence-134e9bcde8ad7379](https://json2video.com/docs/v2/reference/api-endpoints/movies-create).
- **Material risk:** Free output is non-commercial/possibly watermarked; commercial use and third-party assets require separate terms.
- **Recommended human disposition (not executed):** HOLD. Confirm whether non-commercial free-plan output is suitable; review credit/render caps, paid commercial-use conditions and third-party asset licenses.
- **Workflow trace:** 25 transition events; last event `event-5d6d4e3e52499a4b` with hash `b8df6830b50193fc84e4cae8399ff51460e17c8afbac443c29dd546ce7234061`.

### #17 — Personalized Offers

- **ID / provider / category:** `candidate-personalized-offers-3ef4d01fa1` / Mastercard (Offers for Publishers product) / `payments`; functional group: payments / finance, personalized offers.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** Mastercard's current Offers for Publishers documentation describes the product's REST API. This resolves the candidate to the current documented product identity. Evidence: [evidence-af0e5ca2044b88d5](https://developer.mastercard.com/presentment/documentation/).
  - **Provider identity — ✅ VERIFIED:** The API documentation and Developer Terms are published on developer.mastercard.com and identify Mastercard. Evidence: [evidence-af0e5ca2044b88d5](https://developer.mastercard.com/presentment/documentation/), [evidence-26f96bda0e79b717](https://developer.mastercard.com/terms-of-use).
  - **Official documentation / version — ✅ VERIFIED:** Public overview, API Basics, Quick Start Guide, and release-history pages are available for Offers for Publishers. Evidence: [evidence-af0e5ca2044b88d5](https://developer.mastercard.com/presentment/documentation/), [evidence-ddae9c4af118763e](https://developer.mastercard.com/presentment/documentation/api-basics/), [evidence-016c1042a03db41a](https://developer.mastercard.com/presentment/documentation/quick-start-guide/), [evidence-2cf3b090abeac87c](https://developer.mastercard.com/presentment/documentation/release-history/).
  - **Authentication — ✅ VERIFIED:** OAuth 2.0 discussion elsewhere in the Mastercard portal is not generalized to this product. Evidence: [evidence-ddae9c4af118763e](https://developer.mastercard.com/presentment/documentation/api-basics/).
  - **API/service terms and data/content rights — 🟨 PARTIALLY_VERIFIED:** These global Developer Terms establish narrow access/use conditions, not product-specific production pricing or an unrestricted data license. Evidence: [evidence-26f96bda0e79b717](https://developer.mastercard.com/terms-of-use).
  - **Documentary Python feasibility — ✅ VERIFIED:** Mastercard's official Quick Start includes Python 3 requests and OAuth-signer code for a documented Sandbox request. The code was not executed and no credentials were used. Evidence: [evidence-016c1042a03db41a](https://developer.mastercard.com/presentment/documentation/quick-start-guide/).
- **Unknown / inconclusive / partially open matters:**
  - **Free tier / pricing / eligibility — ❓ UNKNOWN:** A Sandbox is documented, but reviewed product pages do not establish its price or a generally free API tier. Production access requires verification/approval; no access was requested. Evidence: [evidence-016c1042a03db41a](https://developer.mastercard.com/presentment/documentation/quick-start-guide/), [evidence-af0e5ca2044b88d5](https://developer.mastercard.com/presentment/documentation/).
  - **Quota / rate / usage limits — ❓ UNKNOWN:** No numeric Offers for Publishers request quota/rate limit was established in the reviewed public materials. Evidence: [evidence-af0e5ca2044b88d5](https://developer.mastercard.com/presentment/documentation/).
  - **API/service terms and data/content rights — 🟨 PARTIALLY_VERIFIED:** These global Developer Terms establish narrow access/use conditions, not product-specific production pricing or an unrestricted data license. Evidence: [evidence-26f96bda0e79b717](https://developer.mastercard.com/terms-of-use).
  - **Date-qualified API maintenance — ❓ UNKNOWN:** A release-history page exists, but the reviewed public entries did not establish an exact dated maintenance event; additional notes are gated. No date-qualified activity finding is asserted. Evidence: [evidence-2cf3b090abeac87c](https://developer.mastercard.com/presentment/documentation/release-history/).
- **Accessibility:** 🚫 NOT_TESTED; No Mastercard API endpoint was contacted and no project or credentials were created; current reachability remains untested. Evidence: [evidence-016c1042a03db41a](https://developer.mastercard.com/presentment/documentation/quick-start-guide/).
- **Material risk:** Sandbox is not production access; product-specific commercial agreement and limits are unresolved.
- **Recommended human disposition (not executed):** HOLD. Establish production eligibility, pricing and complete Offers-for-Publishers terms; the Sandbox and Access Tool terms do not settle the full commercial/data agreement.
- **Workflow trace:** 24 transition events; last event `event-e20428f5e440a0e7` with hash `91ac72ccdbb44a3ae133d0c6ae75833fbcd18f0b778375b61b043682a3413141`.

### #18 — The SMS Works API

- **ID / provider / category:** `candidate-the-sms-works-api-c4a3fea09f` / The SMS Works / `communication`; functional group: communications, SMS.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** The SMS Works publishes SMS REST API documentation for send, schedule, batch, and OTP methods. Evidence: [evidence-a6de56c0e7866c52](https://thesmsworks.co.uk/developers), [evidence-be9d8359e7c527dd](https://thesmsworks.co.uk/developers).
  - **Provider identity — ✅ VERIFIED:** The developer and pricing pages are published on thesmsworks.co.uk and identify The SMS Works. Evidence: [evidence-a6de56c0e7866c52](https://thesmsworks.co.uk/developers), [evidence-773172c4bb264c9c](https://thesmsworks.co.uk/pricing).
  - **Official documentation / version — ✅ VERIFIED:** Public developer docs describe authentication, request methods/formats, callbacks, and examples. Evidence: [evidence-a6de56c0e7866c52](https://thesmsworks.co.uk/developers), [evidence-be9d8359e7c527dd](https://thesmsworks.co.uk/developers).
  - **Authentication — ✅ VERIFIED:** Provider docs require an account-generated JWT in the Authorization header. Evidence: [evidence-ee0468f0e8802d39](https://thesmsworks.co.uk/developers).
  - **Free tier / pricing / eligibility — ✅ VERIFIED:** The provider supplies 50 free test credits; after testing, usage is pay-as-you-go. Test credits do not establish free production SMS. Evidence: [evidence-773172c4bb264c9c](https://thesmsworks.co.uk/pricing).
  - **Quota / rate / usage limits — ✅ VERIFIED:** The per-destination numbers are a flooding filter, not general HTTP request throughput; the listed price is UK- and volume-specific. Evidence: [evidence-36254f064cb07e4c](https://thesmsworks.co.uk/developers), [evidence-773172c4bb264c9c](https://thesmsworks.co.uk/pricing).
  - **Documentary Python feasibility — ✅ VERIFIED:** The documented HTTPS REST POST interface uses JSON and headers and can be called with a Python HTTP client; no integration was run. Evidence: [evidence-be9d8359e7c527dd](https://thesmsworks.co.uk/developers).
- **Unknown / inconclusive / partially open matters:**
  - **API/service terms and data/content rights — ❓ UNKNOWN:** The terms cover messaging conduct, key security, and disclosure for reselling texts, but a current API/data license or broader data-use grant was not established. Evidence: [evidence-60a1ab9b7d604555](https://thesmsworks.co.uk/terms).
  - **Date-qualified API maintenance — ❓ UNKNOWN:** No dated API release or maintenance record was established. The age of the terms page is not evidence of API maintenance status. Evidence: [evidence-a6de56c0e7866c52](https://thesmsworks.co.uk/developers).
- **Accessibility:** 🚫 NOT_TESTED; No SMS was sent and no API call was made; documentation does not establish current live endpoint reachability. Evidence: [evidence-be9d8359e7c527dd](https://thesmsworks.co.uk/developers).
- **Material risk:** Free credits are test credits, not a free paid-SMS production tier; global request rate and broad reuse rights are unresolved.
- **Recommended human disposition (not executed):** HOLD. Separate the 50 test credits from paid SMS delivery, obtain an overall request limit if required, and review current messaging/data-use conditions.
- **Workflow trace:** 25 transition events; last event `event-0dd2db5f5c6cb9b0` with hash `0581d9437bd61bfac599e405200c1e29de936e9c1a4a42cffcfbe54b40248334`.

### #19 — Trash Nothing

- **ID / provider / category:** `candidate-trash-nothing-d6fee4380e` / Trash Nothing / `marketing-social`; functional group: community / social, reuse listings.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** The provider-controlled developer page and hosted v1.4 OpenAPI specification establish a real REST API. Evidence: [evidence-9c6f63c810d686dc](https://trashnothing.com/app/developer), [evidence-cf752bf5d1663352](https://trashnothing.com/api/v1.4/trashnothing-openapi.yaml).
  - **Provider identity — ✅ VERIFIED:** The developer page and spec are served from trashnothing.com and identify the Trash Nothing API. Evidence: [evidence-9c6f63c810d686dc](https://trashnothing.com/app/developer), [evidence-cf752bf5d1663352](https://trashnothing.com/api/v1.4/trashnothing-openapi.yaml).
  - **Official documentation / version — ✅ VERIFIED:** The provider publishes a developer page and versioned OpenAPI 2.0 specification. The page calls the spec information current as of May 2022; no newer release is inferred. Evidence: [evidence-9c6f63c810d686dc](https://trashnothing.com/app/developer), [evidence-cf752bf5d1663352](https://trashnothing.com/api/v1.4/trashnothing-openapi.yaml).
  - **Authentication — ✅ VERIFIED:** This is mixed, operation-specific auth documentation; do not infer that a public key authorizes every user route. Evidence: [evidence-085ceb5f17a9eb50](https://trashnothing.com/api/v1.4/trashnothing-openapi.yaml), [evidence-9c6f63c810d686dc](https://trashnothing.com/app/developer).
  - **API/service terms and data/content rights — ✅ VERIFIED:** Record the provider's stated service/content restrictions without describing the content as openly licensed. Evidence: [evidence-c3b7c3ca1154cead](https://trashnothing.com/terms).
  - **Documentary Python feasibility — ✅ VERIFIED:** The provider documents HTTPS REST/JSON and recommends OpenAPI-generated clients, which supports Python client generation; no client or API call was tested. Evidence: [evidence-e2637e2a1f7ce655](https://trashnothing.com/api/v1.4/trashnothing-openapi.yaml), [evidence-9c6f63c810d686dc](https://trashnothing.com/app/developer).
- **Unknown / inconclusive / partially open matters:**
  - **Free tier / pricing / eligibility — ❓ UNKNOWN:** App registration/login is required, but reviewed provider pages do not state a fee or explicitly establish a free tier. Personal-use terms do not prove free pricing. Evidence: [evidence-9c6f63c810d686dc](https://trashnothing.com/app/developer), [evidence-c3b7c3ca1154cead](https://trashnothing.com/terms).
  - **Quota / rate / usage limits — ❓ UNKNOWN:** The specification documents feed windows and pagination/response caps but no API-wide request-per-time quota; retain UNKNOWN for general rate limits. Evidence: [evidence-20b3422d81dba2ee](https://trashnothing.com/api/v1.4/trashnothing-openapi.yaml).
  - **Date-qualified API maintenance — ❓ UNKNOWN:** No provider API release or maintenance record later than the documentation's May 2022 reference was established. Evidence: [evidence-9c6f63c810d686dc](https://trashnothing.com/app/developer), [evidence-cf752bf5d1663352](https://trashnothing.com/api/v1.4/trashnothing-openapi.yaml).
- **Accessibility:** 🚫 NOT_TESTED; No candidate endpoint was contacted; public OpenAPI documentation does not establish current endpoint reachability. Evidence: [evidence-e2637e2a1f7ce655](https://trashnothing.com/api/v1.4/trashnothing-openapi.yaml).
- **Material risk:** Personal-use restrictions and unknown price/global quota; API key/app registration is required for some operations.
- **Recommended human disposition (not executed):** HOLD. Resolve API pricing and global rate limits and ensure intended reuse fits the personal-use/anti-resale terms; app registration is not evidence of free access.
- **Workflow trace:** 25 transition events; last event `event-a774fe6b61be7021` with hash `72014177dc79e86e0357ae87784a77e52c47061e427927c51bf86c03989a62bc`.

### #20 — Vercel API

- **ID / provider / category:** `candidate-vercel-api-d95586b8bf` / Vercel / `cloud-infrastructure`; functional group: cloud infrastructure, developer tools.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** Vercel documents an API at api.vercel.com with project, deployment, domain, and other account operations. Evidence: [evidence-45a65b0d89f4501f](https://vercel.com/docs/rest-api).
  - **Provider identity — ✅ VERIFIED:** The REST API docs and API Terms are hosted on vercel.com and identify Vercel. Evidence: [evidence-45a65b0d89f4501f](https://vercel.com/docs/rest-api), [evidence-9459b3229ca56870](https://vercel.com/legal/api-terms).
  - **Official documentation / version — ✅ VERIFIED:** Vercel publishes a REST API reference, authentication and GET quick start, and endpoint-specific rate-limit documentation. Evidence: [evidence-45a65b0d89f4501f](https://vercel.com/docs/rest-api), [evidence-e4592d721d1c0d7e](https://vercel.com/docs/rest-api/getting-started), [evidence-1446e41ddd909ebe](https://vercel.com/docs/limits).
  - **Authentication — ✅ VERIFIED:** Vercel documents access tokens in the Authorization: Bearer header. Evidence: [evidence-7f6b87566117fc01](https://vercel.com/docs/rest-api).
  - **Free tier / pricing / eligibility — ✅ VERIFIED:** A USD 0/month Hobby plan exists and the REST rate-limit table documents Free/Hobby action limits. This is a limited account path, not a universal standalone API price. Evidence: [evidence-4e81e500e4729a0f](https://vercel.com/pricing), [evidence-1446e41ddd909ebe](https://vercel.com/docs/limits).
  - **Quota / rate / usage limits — ✅ VERIFIED:** These are examples from Vercel's operation-specific table; they should not be summarized as a single global rate. Evidence: [evidence-1446e41ddd909ebe](https://vercel.com/docs/limits), [evidence-45a65b0d89f4501f](https://vercel.com/docs/rest-api).
  - **API/service terms and data/content rights — ✅ VERIFIED:** This records the general API Terms and restrictions; it is not a standalone price statement or an assertion that API data may be freely redistributed. Evidence: [evidence-9459b3229ca56870](https://vercel.com/legal/api-terms).
  - **Documentary Python feasibility — ✅ VERIFIED:** Vercel documents a standard HTTP REST API that a Python HTTP client can call. The listed TypeScript SDK and separate Vercel Connect Python SDK are not treated as a general Python REST client. Evidence: [evidence-45a65b0d89f4501f](https://vercel.com/docs/rest-api), [evidence-e4592d721d1c0d7e](https://vercel.com/docs/rest-api/getting-started).
- **Unknown / inconclusive / partially open matters:**
  - **Date-qualified API maintenance — ❓ UNKNOWN:** No dated REST API release or maintenance record was established; rate-limit documentation is not itself a release record. Evidence: [evidence-45a65b0d89f4501f](https://vercel.com/docs/rest-api).
- **Accessibility:** 🚫 NOT_TESTED; No Vercel endpoint was contacted and no access token was created; docs do not establish reachability under a particular account. Evidence: [evidence-e4592d721d1c0d7e](https://vercel.com/docs/rest-api/getting-started).
- **Material risk:** Limits vary by plan/operation and terms restrict API-data reuse/AI/ML use.
- **Recommended human disposition (not executed):** HOLD. Specify plan and operation before interpreting limits; review API-data/AI-use restrictions and account eligibility without treating a $0 Hobby account as free production capacity.
- **Workflow trace:** 25 transition events; last event `event-b4dfd1f9cebf62c5` with hash `b97626d88558985a3ff0b001dd2b6529f08138568ef34540a6b1d6f9373764eb`.

### #21 — Zalando Shop

- **ID / provider / category:** `candidate-zalando-shop-04d1e2ab90` / Zalando (historical Shop Public API documentation) / `business-commerce`; functional group: commerce, retail/shop data.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** The archived provider-owned repository documents a historical Shop Public API. It says article, category, and product data are not currently supported through it; this does not establish a current supported API. Evidence: [evidence-m09-21-docs](https://github.com/zalando/shop-api-documentation/blob/master/README.md).
  - **Provider identity — ✅ VERIFIED:** The source is in Zalando’s provider-owned GitHub organization and identifies the Shop Public API. This does not establish a present-day API. Evidence: [evidence-m09-21-docs](https://github.com/zalando/shop-api-documentation/blob/master/README.md).
  - **Official documentation / version — ✅ VERIFIED:** Provider-controlled documentation remains available as an archived repository; its age and archive state are material limitations. Evidence: [evidence-m09-21-docs](https://github.com/zalando/shop-api-documentation/blob/master/README.md).
- **Unknown / inconclusive / partially open matters:**
  - **Authentication — ⚠️ INCONCLUSIVE:** The archived source does not establish authentication for a current supported Shop API. Evidence: [evidence-m09-21-docs](https://github.com/zalando/shop-api-documentation/blob/master/README.md).
  - **Free tier / pricing / eligibility — ❓ UNKNOWN:** No current API pricing or access tier was established; general consumer-service terms are not API pricing. Evidence: [evidence-m09-21-docs](https://github.com/zalando/shop-api-documentation/blob/master/README.md).
  - **Quota / rate / usage limits — ❓ UNKNOWN:** No current Shop API quota or rate limit was established. Evidence: [evidence-m09-21-docs](https://github.com/zalando/shop-api-documentation/blob/master/README.md).
  - **API/service terms and data/content rights — ❓ UNKNOWN:** General Zalando consumer Terms restrict automated use but are not API-specific; current API-service and shop-data reuse terms remain unresolved. Evidence: [evidence-m09-21-terms](https://accounts.zalando.com/terms-of-use).
  - **Date-qualified API maintenance — ⚠️ INCONCLUSIVE:** The documentation repository was archived in 2018, with its README last committed in January 2018. No current API maintenance record was established; do not generalize to Zalando’s other APIs. Evidence: [evidence-m09-21-archive](https://github.com/zalando/shop-api-documentation/blob/master/README.md).
  - **Documentary Python feasibility — ❓ UNKNOWN:** No current endpoint or provider-maintained Python integration for the legacy Shop Public API was established. Evidence: [evidence-m09-21-endpoint](https://github.com/zalando/shop-api-documentation/blob/master/README.md).
- **Accessibility:** 🚫 NOT_TESTED; No candidate API endpoint was contacted. Archived documentation does not establish live reachability. Evidence: [evidence-m09-21-endpoint](https://github.com/zalando/shop-api-documentation/blob/master/README.md).
- **Material risk:** Provider repository is archived; current Shop API/support and API-specific rights were not established.
- **Recommended human disposition (not executed):** HOLD. Do not advance on archived historical documentation alone; require a current supported Shop API, API-specific auth and terms, and current rights evidence.
- **Workflow trace:** 23 transition events; last event `event-52e1a5f99e528ebb` with hash `e43aa77624236e6c7462f12f571e6bf55b50e6e2706e58237cda49e8c90aed0f`.

### #22 — Healthsites.io

- **ID / provider / category:** `candidate-healthsites-io-f3ca26b767` / Healthsites.io / `humanitarian-development`; functional group: public health, humanitarian geospatial data.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** Provider documentation identifies a current v3 facility API with list, detail, statistics, and shapefile functionality. Evidence: [evidence-m09-22-docs](https://healthsites.io/api/docs/), [evidence-m09-22-wiki](https://github.com/healthsites/healthsites/wiki/API).
  - **Provider identity — ✅ VERIFIED:** The service documentation and API terms identify healthsites.io as the API provider. Evidence: [evidence-m09-22-docs](https://healthsites.io/api/docs/), [evidence-m09-22-api_terms](https://github.com/healthsites/healthsites/wiki/API-Terms).
  - **Official documentation / version — ✅ VERIFIED:** Public v3 documentation and the provider-linked wiki describe endpoints, filtering, pagination, and output formats. Evidence: [evidence-m09-22-docs](https://healthsites.io/api/docs/), [evidence-m09-22-wiki](https://github.com/healthsites/healthsites/wiki/API).
  - **Authentication — ✅ VERIFIED:** The interactive docs and newer provider-linked wiki describe the api-key parameter; the wiki explains the OSM-account/token acquisition flow. No account or key was created. Evidence: [evidence-m09-22-auth](https://github.com/healthsites/healthsites/wiki/API), [evidence-m09-22-docs](https://healthsites.io/api/docs/).
  - **Free tier / pricing / eligibility — ✅ VERIFIED:** The API terms allow professional use at no charge up to 50 calls/day; higher use and bulk downloads are paid. Data licensing is separate from API-service pricing. Evidence: [evidence-m09-22-api_terms](https://github.com/healthsites/healthsites/wiki/API-Terms).
  - **Quota / rate / usage limits — ✅ VERIFIED:** The explicit free daily cap is 50; higher volume and bulk downloads are paid. This is an access-tier cap, not an inferred universal HTTP throttle. Evidence: [evidence-m09-22-quota](https://github.com/healthsites/healthsites/wiki/API-Terms).
  - **API/service terms and data/content rights — ✅ VERIFIED:** API-service access terms and data rights are distinct. Preserve ODbL attribution/share-alike obligations and the provider’s AI-use notice requirement. Evidence: [evidence-m09-22-api_terms](https://github.com/healthsites/healthsites/wiki/API-Terms), [evidence-m09-22-license](https://github.com/healthsites/healthsites/blob/develop/ATTRIBUTION.md).
  - **Date-qualified API maintenance — ✅ VERIFIED:** The provider repository records code activity on 2026-10-12 and its API-terms wiki was updated 2026-10-29. This indicates repository/documentation activity, not uptime. Evidence: [evidence-m09-22-maint](https://github.com/healthsites/healthsites/commit/0e254a0d12692adfa37dce6fa57bf8c91f677e82).
  - **Documentary Python feasibility — ✅ VERIFIED:** Provider documentation includes a Python CoreAPI example. The library was not installed or executed. Evidence: [evidence-m09-22-endpoint](https://healthsites.io/api/docs/).
- **Unknown / inconclusive / partially open matters:**
  - No additional UNKNOWN/INCONCLUSIVE finding in the stored review dimensions; this does not imply operational or legal approval.
- **Accessibility:** 🚫 NOT_TESTED; No candidate API endpoint was contacted; documentation does not establish current live reachability. Evidence: [evidence-m09-22-endpoint](https://healthsites.io/api/docs/).
- **Material risk:** ODbL attribution/share-alike applies to data; API terms cap free calls and require contact before training/fine-tuning.
- **Recommended human disposition (not executed):** HOLD. Check fit with the 50-call/day free cap, attribution/share-alike, and provider-contact condition before any AI training/fine-tuning use; keep code licensing separate.
- **Workflow trace:** 27 transition events; last event `event-9199b81a8f2434a7` with hash `79d8b43ed58add0ea8449d469644115d960932db0d234aac159ad5748b50c425`.

### #23 — NLR Developer Network

- **ID / provider / category:** `candidate-nlr-developer-network-ec3f818d2c` / National Renewable Energy Laboratory / NLR Developer Network / `energy`; functional group: energy / renewables, government research data.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** The provider documents named NLR energy APIs across multiple data categories. Evidence: [evidence-m09-23-docs](https://developer.nlr.gov/docs/).
  - **Provider identity — ✅ VERIFIED:** NLR’s developer domain identifies the API program and links its key, limits, signup, and terms materials. Evidence: [evidence-m09-23-docs](https://developer.nlr.gov/docs/), [evidence-m09-23-terms](https://developer.nlr.gov/terms/).
  - **Official documentation / version — ✅ VERIFIED:** Public provider docs describe service categories, key usage, rate limits, and errors. Evidence: [evidence-m09-23-docs](https://developer.nlr.gov/docs/), [evidence-m09-23-auth](https://developer.nlr.gov/docs/api-key/).
  - **Authentication — ✅ VERIFIED:** No key was requested or created. Documented transport alternatives do not imply that a key is optional. Evidence: [evidence-m09-23-auth](https://developer.nlr.gov/docs/api-key/), [evidence-m09-23-signup](https://developer.nlr.gov/signup/).
  - **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED:** Provider default and DEMO_KEY allowances are explicit; do not treat the shared default as a service-specific override. Evidence: [evidence-m09-23-quota](https://developer.nlr.gov/docs/rate-limits/).
  - **API/service terms and data/content rights — ✅ VERIFIED:** Record the general terms narrowly; they do not prove every underlying dataset has identical ownership or redistribution rights. Evidence: [evidence-m09-23-terms](https://developer.nlr.gov/terms/).
  - **Date-qualified API maintenance — ✅ VERIFIED:** The official developer-documentation repository has a dated 2026-11-04 update. This establishes documentation activity, not API uptime. Evidence: [evidence-m09-23-maint](https://github.com/NatLabRockies/developer.nlr.gov/commits/main).
  - **Documentary Python feasibility — ✅ VERIFIED:** The documented HTTPS REST/JSON interface is feasible from generic Python HTTP code. A provider-maintained Python SDK was not established or tested. Evidence: [evidence-m09-23-endpoint](https://developer.nlr.gov/docs/api-key/).
- **Unknown / inconclusive / partially open matters:**
  - **Free tier / pricing / eligibility — ❓ UNKNOWN:** The signup page documents key registration but does not state an API service price or unconditional free tier. No account was created. Evidence: [evidence-m09-23-signup](https://developer.nlr.gov/signup/), [evidence-m09-23-terms](https://developer.nlr.gov/terms/).
  - **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED:** Provider default and DEMO_KEY allowances are explicit; do not treat the shared default as a service-specific override. Evidence: [evidence-m09-23-quota](https://developer.nlr.gov/docs/rate-limits/).
- **Accessibility:** 🚫 NOT_TESTED; No candidate endpoint was contacted. Public docs and recent documentation commits do not establish live API reachability. Evidence: [evidence-m09-23-endpoint](https://developer.nlr.gov/docs/api-key/).
- **Material risk:** Shared api.data.gov limit is not NLR-specific; access price and dataset-level rights unresolved.
- **Recommended human disposition (not executed):** HOLD. Confirm NLR-specific pricing/limits and dataset-by-dataset rights; the shared api.data.gov default is not a product guarantee.
- **Workflow trace:** 26 transition events; last event `event-88a2c181ca37cfde` with hash `8472a1b35242d3d25adcb318d2d8978e46bf8aae7ee4d5d49eed6e62ef00210b`.

### #24 — OpenWeatherMap

- **ID / provider / category:** `candidate-openweathermap-414a390f3e` / OpenWeatherMap / `weather-climate`; functional group: weather / climate, forecast data.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** OpenWeather documents a current One Call API family; this review focuses on current endpoint version 4.0, not every OpenWeather product. Evidence: [evidence-m09-24-docs](https://openweathermap.org/api/one-call-4).
  - **Provider identity — ✅ VERIFIED:** The One Call documentation and pricing pages are published by OpenWeather. Evidence: [evidence-m09-24-docs](https://openweathermap.org/api/one-call-4), [evidence-m09-24-pricing](https://openweathermap.org/full-price).
  - **Official documentation / version — ✅ VERIFIED:** Provider documentation describes One Call 4.0 endpoints and the 3.0-to-4.0 transition; v3 remains available and v4 is recommended for new integrations. Evidence: [evidence-m09-24-docs](https://openweathermap.org/api/one-call-4), [evidence-m09-24-migration](https://openweathermap.org/api/one-call-3-migration).
  - **Authentication — ✅ VERIFIED:** Current One Call docs require an OpenWeather API key on each call; no account or key was created. Evidence: [evidence-m09-24-auth](https://openweathermap.org/api/one-call-4).
  - **Free tier / pricing / eligibility — ✅ VERIFIED:** The separate One Call subscription includes 1,000 free calls/day; additional calls are £0.0012 each. This is not the standard Free weather plan. Evidence: [evidence-m09-24-docs](https://openweathermap.org/api/one-call-4), [evidence-m09-24-pricing](https://openweathermap.org/full-price).
  - **Quota / rate / usage limits — ✅ VERIFIED:** These are One Call-specific pricing/cap values; no other OpenWeather subscription is required for this product. Evidence: [evidence-m09-24-pricing](https://openweathermap.org/full-price), [evidence-m09-24-quota](https://openweathermap.org/full-price).
  - **API/service terms and data/content rights — ✅ VERIFIED:** The general website Terms of Use were not substituted for the product-specific API/data license. Evidence: [evidence-m09-24-license](https://openweathermap.org/full-price), [evidence-m09-24-pricing](https://openweathermap.org/full-price).
  - **Documentary Python feasibility — ✅ VERIFIED:** Documented REST/HTTPS GET calls can be made from generic Python HTTP code; no provider SDK was established or tested. Evidence: [evidence-m09-24-endpoint](https://openweathermap.org/api/one-call-4).
- **Unknown / inconclusive / partially open matters:**
  - **Date-qualified API maintenance — ❓ UNKNOWN:** A provider migration guide documents the v4 transition, but no dated release/maintenance record was established. Do not infer uptime from the migration page. Evidence: [evidence-m09-24-migration](https://openweathermap.org/api/one-call-3-migration).
- **Accessibility:** 🚫 NOT_TESTED; No candidate API endpoint was contacted. Documentation and pricing do not establish live reachability. Evidence: [evidence-m09-24-endpoint](https://openweathermap.org/api/one-call-4).
- **Material risk:** Subscription/version-specific price and ODbL obligations; distinct from Open-Meteo.
- **Recommended human disposition (not executed):** HOLD. Select the exact One Call version/subscription and model the 1,000/day free cap, overage and ODbL attribution/share-alike duties; preserve OpenWeatherMap as distinct from Open-Meteo.
- **Workflow trace:** 26 transition events; last event `event-f41fab0db5f2958c` with hash `b841442f1b9c8d2dba9aab88ff11d6dec60a8530b105baf7ee49e01b9129340b`.

### #25 — Census Bureau

- **ID / provider / category:** `candidate-census-bureau-670fd2a556` / U.S. Census Bureau / `economics`; functional group: government statistics, demographic data.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** The current Census user guide identifies the Census Data API for querying Bureau datasets. Evidence: [evidence-m09-25-limits](https://www.census.gov/data/developers/guidance/api-user-guide.Query_Limits.html).
  - **Provider identity — ✅ VERIFIED:** The API is documented on Census Bureau government pages and governed by API-specific terms. Evidence: [evidence-m09-25-limits](https://www.census.gov/data/developers/guidance/api-user-guide.Query_Limits.html), [evidence-m09-25-terms](https://www.census.gov/data/developers/about/terms-of-service.html).
  - **Official documentation / version — ✅ VERIFIED:** Current user-guide pages document query limits, keys, and example dataset requests. Evidence: [evidence-m09-25-limits](https://www.census.gov/data/developers/guidance/api-user-guide.Query_Limits.html), [evidence-m09-25-endpoint](https://www.census.gov/data/developers/guidance/api-user-guide.Example_API_Queries.html).
  - **Free tier / pricing / eligibility — ✅ VERIFIED:** The provider says the API key is free of charge and the February training describes the API as free/public. The exact key requirement threshold conflicts across official sources; no per-dataset price schedule was established. Evidence: [evidence-m09-25-key](https://www.census.gov/data/developers/guidance/api-user-guide.API_Key.html), [evidence-m09-25-training](https://www2.census.gov/about/training-workshops/2026/2026-02-19-getting-started-with-census-api-presentation.pdf).
  - **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED:** The 50-variable limit is current-guide wording. Official training’s 500-per-IP/day key threshold conflicts with the newer all-queries-key wording; do not state a settled daily request quota. Evidence: [evidence-m09-25-limits](https://www.census.gov/data/developers/guidance/api-user-guide.Query_Limits.html), [evidence-m09-25-training](https://www2.census.gov/about/training-workshops/2026/2026-02-19-getting-started-with-census-api-presentation.pdf).
  - **API/service terms and data/content rights — ✅ VERIFIED:** Record API terms and re-identification restrictions separately from dataset-specific data rights. Evidence: [evidence-m09-25-terms](https://www.census.gov/data/developers/about/terms-of-service.html).
  - **Date-qualified API maintenance — ✅ VERIFIED:** The provider revised its API user guide in May 2026. This supports documentation activity only, not backend maintenance or uptime. Evidence: [evidence-m09-25-maint](https://www.census.gov/data/developers/guidance/api-user-guide.Query_Limits.html).
  - **Documentary Python feasibility — ✅ VERIFIED:** Provider examples document URL-based REST queries and JSON-array results for generic Python HTTP clients. No provider-maintained SDK was tested. Evidence: [evidence-m09-25-endpoint](https://www.census.gov/data/developers/guidance/api-user-guide.Example_API_Queries.html).
- **Unknown / inconclusive / partially open matters:**
  - **Authentication — ⚠️ INCONCLUSIVE:** The May 2026 guide says every data query needs a key; the official Feb. 19, 2026 presentation says a key is needed only above 500 queries per IP/day and demonstrates no-key use. The free key is documented, but the requirement threshold conflict remains unresolved. Evidence: [evidence-m09-25-limits](https://www.census.gov/data/developers/guidance/api-user-guide.Query_Limits.html), [evidence-m09-25-key](https://www.census.gov/data/developers/guidance/api-user-guide.API_Key.html), [evidence-m09-25-training](https://www2.census.gov/about/training-workshops/2026/2026-02-19-getting-started-with-census-api-presentation.pdf).
  - **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED:** The 50-variable limit is current-guide wording. Official training’s 500-per-IP/day key threshold conflicts with the newer all-queries-key wording; do not state a settled daily request quota. Evidence: [evidence-m09-25-limits](https://www.census.gov/data/developers/guidance/api-user-guide.Query_Limits.html), [evidence-m09-25-training](https://www2.census.gov/about/training-workshops/2026/2026-02-19-getting-started-with-census-api-presentation.pdf).
- **Accessibility:** 🚫 NOT_TESTED; No candidate API endpoint was contacted; documentation examples are not a reachability test. Evidence: [evidence-m09-25-endpoint](https://www.census.gov/data/developers/guidance/api-user-guide.Example_API_Queries.html).
- **Material risk:** Official key-threshold guidance conflicts; no settled general daily quota or blanket dataset license.
- **Recommended human disposition (not executed):** HOLD. Reconcile the conflicting official API-key guidance and unsettled global daily quota, then review dataset-specific rights; do not merge or overwrite accepted `census-data`.
- **Workflow trace:** 25 transition events; last event `event-f542d1c203901c72` with hash `ea16e5093901f4099e631ffaa5185b8dcd29c61ab6460fb44dc07704e6832601`.

### #26 — GovInfo

- **ID / provider / category:** `candidate-govinfo-d67a219b74` / U.S. Government Publishing Office (GovInfo) / `legal`; functional group: government / legal, publications.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** Provider-controlled GovInfo documentation describes current API operations for search and publication collections. Evidence: [evidence-m09-26-home](https://www.govinfo.gov/developers), [evidence-m09-26-api_docs](https://api.govinfo.gov/docs/).
  - **Provider identity — ✅ VERIFIED:** The official GovInfo developer hub links to the GovInfo API reference and key-signup process. Evidence: [evidence-m09-26-home](https://www.govinfo.gov/developers), [evidence-m09-26-api_docs](https://api.govinfo.gov/docs/).
  - **Official documentation / version — ✅ VERIFIED:** The GovInfo API reference documents several API operation families and required key usage. Evidence: [evidence-m09-26-api_docs](https://api.govinfo.gov/docs/).
  - **Authentication — ✅ VERIFIED:** The key flow was inspected but not submitted; no key or account was created. Evidence: [evidence-m09-26-api_docs](https://api.govinfo.gov/docs/), [evidence-m09-26-auth](https://www.govinfo.gov/api-signup).
  - **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED:** Record the api.data.gov default narrowly; a GovInfo-specific rate-limit override was not found in the reviewed sources. Evidence: [evidence-m09-26-quota](https://api.data.gov/docs/developer-manual/).
  - **Documentary Python feasibility — ✅ VERIFIED:** The documented REST API surface is compatible with generic Python HTTP clients. No client was installed and no API call was made. Evidence: [evidence-m09-26-endpoint](https://api.govinfo.gov/docs/).
- **Unknown / inconclusive / partially open matters:**
  - **Free tier / pricing / eligibility — ❓ UNKNOWN:** The reviewed key-signup and umbrella limit pages do not establish a GovInfo-specific price or unconditional free service tier. Evidence: [evidence-m09-26-auth](https://www.govinfo.gov/api-signup), [evidence-m09-26-quota](https://api.data.gov/docs/developer-manual/).
  - **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED:** Record the api.data.gov default narrowly; a GovInfo-specific rate-limit override was not found in the reviewed sources. Evidence: [evidence-m09-26-quota](https://api.data.gov/docs/developer-manual/).
  - **API/service terms and data/content rights — ❓ UNKNOWN:** The reviewed copyright/policies fetch was only a stub; collection-specific rights remain unresolved. Do not infer public-domain status for all GovInfo content. Evidence: [evidence-m09-26-copyright](https://www.govinfo.gov/about/policies#copyright).
  - **Date-qualified API maintenance — ❓ UNKNOWN:** No dated provider backend release or maintenance record was established. A repository history page without displayed commits is not evidence of inactivity. Evidence: [evidence-m09-26-api_docs](https://api.govinfo.gov/docs/).
- **Accessibility:** 🚫 NOT_TESTED; No candidate API endpoint was contacted; published documentation does not establish live reachability. Evidence: [evidence-m09-26-endpoint](https://api.govinfo.gov/docs/).
- **Material risk:** GovInfo key/default quotas are umbrella-level; individual collection rights are unresolved.
- **Recommended human disposition (not executed):** HOLD. Confirm GovInfo-specific access/pricing/limits and the rights for each collection; do not infer blanket public-domain rights from a government API label.
- **Workflow trace:** 25 transition events; last event `event-6785ca3b9c66cf80` with hash `558db18203058246bb467a10c98c7b539dc1c7cead74c03b66312347174b8a11`.

### #27 — RevAddress

- **ID / provider / category:** `candidate-revaddress-3b7f8a6f2c` / RevAddress / `developer-tools`; functional group: address validation, geospatial / local data.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** The provider documents an address API covering Census/local address operations and USPS DPV as a separate product. Evidence: [evidence-m09-27-docs](https://revaddress.com/docs/).
  - **Provider identity — ✅ VERIFIED:** RevAddress publishes the API documentation and its own pricing, terms, and privacy pages. Evidence: [evidence-m09-27-docs](https://revaddress.com/docs/), [evidence-m09-27-terms](https://revaddress.com/legal/terms/).
  - **Official documentation / version — ✅ VERIFIED:** Provider API documentation is available and describes the address API family. Evidence: [evidence-m09-27-docs](https://revaddress.com/docs/).
  - **Free tier / pricing / eligibility — ✅ VERIFIED:** The free plan is limited to up to 1,000 monthly Census/local operations. USPS DPV is paid, requiring a paid plan and 10 purchased credits ($0.01) per address; a free-tier DPV sample conflicts with provider terms and is not relied upon. Evidence: [evidence-m09-27-pricing](https://revaddress.com/pricing/), [evidence-m09-27-terms](https://revaddress.com/legal/terms/).
  - **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED:** The monthly operations cap and DPV purchase requirement are product-specific; no universal per-second request limit was identified. Evidence: [evidence-m09-27-pricing](https://revaddress.com/pricing/), [evidence-m09-27-terms](https://revaddress.com/legal/terms/).
  - **Documentary Python feasibility — ✅ VERIFIED:** The documented HTTPS API can be called using generic Python HTTP tooling. No library was installed and no API request was made. Evidence: [evidence-m09-27-endpoint](https://revaddress.com/docs/).
- **Unknown / inconclusive / partially open matters:**
  - **Authentication — ❓ UNKNOWN:** The reviewed sources do not establish a sufficiently clear authentication requirement for this candidate; do not infer a key requirement from directory metadata. Evidence: [evidence-m09-27-docs](https://revaddress.com/docs/).
  - **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED:** The monthly operations cap and DPV purchase requirement are product-specific; no universal per-second request limit was identified. Evidence: [evidence-m09-27-pricing](https://revaddress.com/pricing/), [evidence-m09-27-terms](https://revaddress.com/legal/terms/).
  - **API/service terms and data/content rights — ❓ UNKNOWN:** The reviewed service terms and privacy policy do not establish a complete API/data license or USPS DPV downstream rights; obtain product-specific terms before use. Evidence: [evidence-m09-27-terms](https://revaddress.com/legal/terms/), [evidence-m09-27-privacy](https://revaddress.com/legal/privacy/).
  - **Date-qualified API maintenance — ❓ UNKNOWN:** No dated provider API release or maintenance record was established. Terms revision date is not evidence of software/backend maintenance. Evidence: [evidence-m09-27-docs](https://revaddress.com/docs/).
- **Accessibility:** 🚫 NOT_TESTED; No candidate API endpoint was contacted; no address was submitted. Evidence: [evidence-m09-27-endpoint](https://revaddress.com/docs/).
- **Material risk:** Free Census/local operations do not include USPS DPV under reviewed paid terms; a free-DPV example conflicts.
- **Recommended human disposition (not executed):** HOLD. Resolve the free-plan-versus-USPS-DPV discrepancy and confirm DPV downstream rights/privacy handling; do not infer DPV is included free.
- **Workflow trace:** 24 transition events; last event `event-ddd75d8493ae9831` with hash `612adc5d0a0027bc80cd0498d80270f31a3110f197ee388d069d4189783422f6`.

### #28 — Telesign

- **ID / provider / category:** `candidate-telesign-b322500dc2` / Telesign / `telecommunications`; functional group: communications, identity / fraud verification.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** Provider Verify documentation and reference describe a verification API with multiple communication methods. Evidence: [evidence-m09-28-docs](https://developer.telesign.com/enterprise/docs/verify-api-get-started-with-sms), [evidence-m09-28-reference](https://developer.telesign.com/enterprise/reference/createverificationprocess).
  - **Provider identity — ✅ VERIFIED:** Telesign’s developer documentation and service terms identify the provider and its Verify product. Evidence: [evidence-m09-28-docs](https://developer.telesign.com/enterprise/docs/verify-api-get-started-with-sms), [evidence-m09-28-terms](https://www.telesign.com/telesign-terms-of-service).
  - **Official documentation / version — ✅ VERIFIED:** Provider materials include a Verify getting-started guide, status codes, and a create-verification reference. The reference also displayed an expired-URL warning. Evidence: [evidence-m09-28-docs](https://developer.telesign.com/enterprise/docs/verify-api-get-started-with-sms), [evidence-m09-28-reference](https://developer.telesign.com/enterprise/reference/createverificationprocess).
  - **Authentication — ✅ VERIFIED:** This is a product-account requirement; no account or credentials were created or used. Evidence: [evidence-m09-28-auth](https://developer.telesign.com/enterprise/docs/verify-api-get-started-with-sms).
  - **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED:** Record the documented signal only; no numeric quota was inferred. Evidence: [evidence-m09-28-quota](https://developer.telesign.com/enterprise/docs/verify-api-status-codes).
  - **Date-qualified API maintenance — ✅ VERIFIED:** The provider’s Python SDK repository released v4.1.1 on 2026-10-01. This is SDK repository activity, not proof that the Verify product itself changed or that this SDK version supports Verify. Evidence: [evidence-m09-28-sdk](https://github.com/TeleSign/python_telesign/releases).
  - **Documentary Python feasibility — ✅ VERIFIED:** The provider documents a REST request/response interface compatible with generic Python HTTP clients. The Telesign Python SDK release record does not establish Verify-specific support; nothing was installed or executed. Evidence: [evidence-m09-28-reference](https://developer.telesign.com/enterprise/reference/createverificationprocess).
- **Unknown / inconclusive / partially open matters:**
  - **Free tier / pricing / eligibility — ❓ UNKNOWN:** The reviewed page lists channel-specific per-message rates and says the unified Verify API is sales-priced; these facts do not establish a single permanent free tier or unified API price. Evidence: [evidence-m09-28-pricing](https://www.telesign.com/pricing/verification-pricing), [evidence-m09-28-auth](https://developer.telesign.com/enterprise/docs/verify-api-get-started-with-sms).
  - **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED:** Record the documented signal only; no numeric quota was inferred. Evidence: [evidence-m09-28-quota](https://developer.telesign.com/enterprise/docs/verify-api-status-codes).
  - **API/service terms and data/content rights — ❓ UNKNOWN:** General service terms incorporate the AUP, DPA, and Privacy Notice; consent/content restrictions apply. Verify-specific data roles, retention, and any product-specific data reuse license remain unresolved. Evidence: [evidence-m09-28-terms](https://www.telesign.com/telesign-terms-of-service), [evidence-m09-28-aup](https://www.telesign.com/acceptable-use-policy), [evidence-m09-28-dpa](https://www.telesign.com/DPA), [evidence-m09-28-privacy](https://www.telesign.com/privacy-notice).
- **Accessibility:** 🚫 NOT_TESTED; No Verify API endpoint was contacted; docs and pricing do not establish live reachability. Evidence: [evidence-m09-28-reference](https://developer.telesign.com/enterprise/reference/createverificationprocess).
- **Material risk:** Unified Verify is sales-enabled; product/channel pricing and Verify-specific processing/retention details incomplete.
- **Recommended human disposition (not executed):** HOLD. Require product-specific sales/account terms, unified Verify pricing, and Verify-specific data roles/retention; keep legacy SMS Verify and channel guides distinct.
- **Workflow trace:** 29 transition events; last event `event-b0a4942b732e664d` with hash `bd0344d7483b835da92d06a163ac192c9fb03741f240fcca723ad6d9a487feb7`.

### #29 — 1Password Connect

- **ID / provider / category:** `candidate-1password-connect-e5ab7cffc9` / 1Password / `identity-security`; functional group: identity / security, secrets infrastructure.
- **Actual state:** `human_approval / not_started`; workflow `in_review`. No proposal, approval or acceptance record.
- **Verified / partly verified findings:**
  - **API existence / scope — ✅ VERIFIED:** 1Password documents Connect as a self-hosted REST API for vault/item operations. Evidence: [evidence-m09-29-home](https://www.1password.dev/connect), [evidence-m09-29-api_ref](https://www.1password.dev/connect/api-reference).
  - **Provider identity — ✅ VERIFIED:** The Connect product and documentation are published by 1Password. Evidence: [evidence-m09-29-home](https://www.1password.dev/connect), [evidence-m09-29-manage](https://www.1password.dev/connect/manage-connect).
  - **Official documentation / version — ✅ VERIFIED:** Public Connect management, security, and API-reference pages describe setup, tokens, and REST operations. Evidence: [evidence-m09-29-api_ref](https://www.1password.dev/connect/api-reference), [evidence-m09-29-home](https://www.1password.dev/connect).
  - **Authentication — ✅ VERIFIED:** This private, self-hosted API exposes customer-selected vault data; this is not public unauthenticated access. Evidence: [evidence-m09-29-auth](https://www.1password.dev/connect/security), [evidence-m09-29-api_ref](https://www.1password.dev/connect/api-reference).
  - **Free tier / pricing / eligibility — ✅ VERIFIED:** Connect access is included without a separate usage fee for 1Password customers, but requires a paid 1Password subscription; the provider lists paid subscription pricing. No standalone free Connect plan was established. Evidence: [evidence-m09-29-manage](https://www.1password.dev/connect/manage-connect), [evidence-m09-29-pricing](https://www.1password.com/pricing/business).
  - **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED:** The cache behavior and undocumented internal initial-fetch limits are provider-documented; do not describe Connect as having no limits at all. Evidence: [evidence-m09-29-quota](https://www.1password.dev/connect), [evidence-m09-29-manage](https://www.1password.dev/connect/manage-connect).
  - **Documentary Python feasibility — ✅ VERIFIED:** The documented REST API is feasible from generic Python HTTP code; no server was provisioned, SDK installed, or secret accessed. Evidence: [evidence-m09-29-endpoint](https://www.1password.dev/connect/api-reference).
- **Unknown / inconclusive / partially open matters:**
  - **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED:** The cache behavior and undocumented internal initial-fetch limits are provider-documented; do not describe Connect as having no limits at all. Evidence: [evidence-m09-29-quota](https://www.1password.dev/connect), [evidence-m09-29-manage](https://www.1password.dev/connect/manage-connect).
  - **API/service terms and data/content rights — ❓ UNKNOWN:** The business subscription terms govern service/customer-data use, but no open/public data license applies to this private secrets API; customer data rights are account-specific. Evidence: [evidence-m09-29-terms](https://1password.com/legal/terms-of-service).
  - **Date-qualified API maintenance — ⚠️ INCONCLUSIVE:** The API reference/spec says 1.8.1 while the publisher’s Docker tags list 1.8.4; no dated Connect server release or actual deployment version was established. Preserve the discrepancy rather than infer current maintenance or uptime. Evidence: [evidence-m09-29-api_ref](https://www.1password.dev/connect/api-reference), [evidence-m09-29-docker_api](https://hub.docker.com/r/1password/connect-api/tags), [evidence-m09-29-docker_sync](https://hub.docker.com/r/1password/connect-sync/tags).
- **Accessibility:** 🚫 NOT_TESTED; No customer Connect server or candidate endpoint was contacted; docs do not establish live reachability. Evidence: [evidence-m09-29-api_ref](https://www.1password.dev/connect/api-reference).
- **Material risk:** Self-hosted private secrets service, not open data; paid subscription context, vault-scoped tokens and version references differ.
- **Recommended human disposition (not executed):** HOLD. Treat this as paid-customer, self-hosted access to private secrets, not a public data API; review tenant security/permissions, version discrepancy and account-specific data rights.
- **Workflow trace:** 29 transition events; last event `event-f605b7a30fc239df` with hash `dd6d0111f2494a7b0662daf1a6f643c71e1a3607a14e1132bceb23a5e78ee030`.

## Deferred candidates excluded from this queue

| # | Candidate | Actual state | Recorded blocker | Decision status |
| ---: | --- | --- | --- | --- |
| 14 | ClickMeter (`candidate-clickmeter-6295c914e4`) | `license_review / deferred` | No current ClickMeter API/data license was established. An attempted legacy terms URL returned Rebrandly-branded marketing content rather than ClickMeter-specific terms; this does not prove terms are absent. Rebrandly terms are not transferred to ClickMeter, so preserve UNKNOWN and defer legal review. Evidence: [evidence-8cb99199bbeb080b](https://support.clickmeter.com/hc/en-us/articles/211037086-Overview), [evidence-448e90c95b433ff9](https://support.clickmeter.com/hc/en-us/articles/211030466-What-is-Link-Shortening-), [evidence-3f67b700ab5e166e](https://www.clickmeter.com/terms-conditions). | No proposal, approval or acceptance; remains DEFERRED. |
| 30 | City Context (`candidate-city-context-30c2c95ecb`) | `license_review / deferred` | No current provider API/data terms or license were retrieved; stale/secondary sources do not establish rights. Evidence: [evidence-m09-30-reference](https://api.citycontext.com). | No proposal, approval or acceptance; remains DEFERRED. |

## Queue-wide safeguards

- `human_approval / not_started` is a pending workflow gate, not a human decision or an endorsement.
- A documented free tier, API key, quota, code sample or legal page does not imply free production use, commercial reuse permission, successful integration or live accessibility.
- Candidate #1/#7/#25 overlap with existing IDs, #2/#24 carry broader-queue sibling flags, and all records remain separate; no deduplication or catalog edit is authorized here.
- Accessibility is `NOT_TESTED` for all 28 entries. No endpoint calls, accounts, credentials, paid access or API tests were performed.
- The recommendations say HOLD/continue review only. The required future human decision must be made explicitly in the workflow and remains outside this consolidation.

[Back to the consolidated evidence map](phase-4-consolidated-evidence-map-1-30.md) · [Unresolved issues](phase-4-unresolved-issues-1-30.md) · [Audit report](phase-4-consolidated-audit-report-1-30.md)
