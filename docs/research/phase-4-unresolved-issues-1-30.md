# Phase 4 Unresolved Issues — Candidates #1–#30

- **Consolidation record date:** 2026-11-14
- **Scope:** only unresolved questions preserved in the #1–#30 workflows plus explicit cross-cutting audit issues.
- **Status convention:** `UNKNOWN` is a gap; `INCONCLUSIVE` is conflicting/inaccessible/ambiguous evidence; `PARTIALLY_VERIFIED` is a bounded fact with an open remainder; `DEFERRED` is workflow state; `NOT_TESTED` is not an availability conclusion.
- **Machine-readable issue references:** [`phase-4-consolidated-evidence-map-1-30.json`](phase-4-consolidated-evidence-map-1-30.json).

## Cross-cutting unresolved issues

### 1. Observation-date chronology — INCONCLUSIVE

Persisted observed_on/recorded_on/checked_on values are uniformly 2026-11-12, but the prior two review commits are timestamped 2026-11-14 and the handoff identifies some source research as having occurred on 2026-11-14. The stored dates are preserved as recorded metadata, not certified retrieval timestamps. This consolidation did not rewrite evidence, events, hashes or dates and did not add provider findings. Resolve chronology only through an append-only correction with the actual observation date if known.

### 2. Accessibility / operational availability — NOT_TESTED for all 30

Every accessibility field stores `NOT_TESTED`. This is deliberate: candidate endpoint calls, API probes and live health checks were outside the documentary consolidation. Documentation and failed page fetches cannot answer present reachability.

### 3. Source taxonomy — PARTIALLY_VERIFIED

YouTube #1 has no source category field; its raw tag/categories are operation/resource names. APOD #7 carries the non-taxonomic value `request tag`. The original records are unchanged; normalized functional categories are editorial only.

### 4. Product-specific applicability of free accounts, tests and sandbox access

TAGGUN #6, SportsDataIO #13, Mastercard #17 and SMS Works #18 each have a limited trial/test/sandbox route that is distinct from live paid commercial use. Xero #10 development access is not a free live accounting subscription. 1Password Connect #29 is customer-entitled/self-hosted. See their queue/evidence citations and the detailed entries below.

### 5. License and data-rights scope

Do not transfer OpenAPI directory/repository license statements to API/service/data rights. Do not generalize Healthsites ODbL or code BSD to its API terms; OpenWeather ODbL to unrelated products; or Census/GovInfo terms to every dataset/collection. YouTube, APOD, Xero, Telesign and 1Password have product/content/customer-specific restrictions. See each candidate's evidence links.

### 6. Duplicate/overlap checks — preserve, do not merge

YouTube #1 and APOD #7 have possible existing catalog matches; Census #25 overlaps the existing `census-data` API and `census-acs-5year` dataset plus a distinct broader-queue Census lead. Visual Crossing #2 and OpenWeatherMap #24 have broader-queue duplicate/sibling IDs; OpenWeatherMap and Open-Meteo are distinct. All candidate and catalog records remain separate; nothing was merged, removed, or rewritten.

## Candidate-specific unresolved questions

For each candidate below, the cited workflow note is copied from the saved finding; it is not a new provider claim. Fields marked `VERIFIED` with a partial status are included because a caveat remains in the field value.

### #1 — YouTube Data API v3 (`candidate-youtube-data-api-v3-e1c8359956`)

- **Free tier / pricing / eligibility — ❓ UNKNOWN.** A quota allocation is documented, but the reviewed provider pages do not establish a monetary price or an unconditional free tier; retain UNKNOWN. Evidence: [p4-yt-price-gap](https://developers.google.com/youtube/data/getting-started).

### #3 — Bank Negara Malaysia Open Data (`candidate-bank-negara-malaysia-open-data-b0cff73d9d`)

- **Authentication — ❓ UNKNOWN.** The reviewed provider documentation does not establish an authentication requirement; retain UNKNOWN. Evidence: [p4-bnm-auth-gap](https://apikijangportal.bnm.gov.my/faq).
- **Free tier / pricing / eligibility — 🟨 PARTIALLY_VERIFIED.** The factual claim “free for everyone” is supported, but this workflow enum cannot safely map it to no-key/keyed access while authentication and usage conditions are unstated; preserve UNKNOWN and flag the taxonomy gap. Evidence: [p4-bnm-free](https://apikijangportal.bnm.gov.my/faq).
- **Quota / rate / usage limits — ❓ UNKNOWN.** No request quota/rate limit is established by the reviewed official pages; retain UNKNOWN. Evidence: [p4-bnm-quota-gap](https://apikijangportal.bnm.gov.my/openapi).
- **API/service terms and data/content rights — ❓ UNKNOWN.** The official disclaimer is a service/accuracy disclaimer, not an API or dataset reuse license; data rights remain UNKNOWN. Evidence: [p4-bnm-terms](https://apikijangportal.bnm.gov.my/disclaimer).
- **Date-qualified API maintenance — ❓ UNKNOWN.** No dated provider-controlled release/change record was identified in reviewed BNM sources; activity remains UNKNOWN. Evidence: [p4-bnm-maint-gap](https://apikijangportal.bnm.gov.my/openapi).

### #4 — bng2latlong (`candidate-bng2latlong-97d9ad5db0`)

- **Authentication — ❓ UNKNOWN.** The provider page does not explicitly state authentication requirements; retain UNKNOWN. Evidence: [p4-bng-auth-gap](https://www.getthedata.com/bng2latlong).
- **Free tier / pricing / eligibility — 🟨 PARTIALLY_VERIFIED.** The provider says the service is free to use for any purpose, but the workflow access-path enum cannot assert FREE_NO_KEY or FREE_WITH_KEY without an explicit auth statement; preserve UNKNOWN. Evidence: [p4-bng-free](https://www.getthedata.com/bng2latlong).
- **Quota / rate / usage limits — ❓ UNKNOWN.** No quota/rate limit is established by the reviewed provider page; retain UNKNOWN. Evidence: [p4-bng-quota-gap](https://www.getthedata.com/bng2latlong).
- **API/service terms and data/content rights — ❓ UNKNOWN.** The free-use/optional-credit statement is preserved, but the reviewed page does not separate service permission from returned-data rights or identify a specific data license; keep the combined service/data license field UNKNOWN. Evidence: [p4-bng-license](https://www.getthedata.com/bng2latlong).
- **Date-qualified API maintenance — ❓ UNKNOWN.** No dated release/change record is present in the reviewed provider page; retain UNKNOWN. Evidence: [p4-bng-maint-gap](https://www.getthedata.com/bng2latlong).

### #5 — IP2WHOIS Domain Lookup (`candidate-ip2whois-domain-lookup-9f73a9ca7c`)

- **API/service terms and data/content rights — ❓ UNKNOWN.** Reviewed IP2Location.io terms do not clearly extend to WHOIS data, and the IP2WHOIS privacy page does not define WHOIS response reuse/retention rights; keep service/data license UNKNOWN. Evidence: [p4-ip2-terms-scope](https://www.ip2location.io/ip2location_io_terms_of_service.pdf), [p4-ip2-privacy](https://www.ip2whois.com/privacy-policy).
- **Date-qualified API maintenance — ❓ UNKNOWN.** No dated release/change record was located in the reviewed provider WHOIS documentation; retain UNKNOWN. Evidence: [p4-ip2-maint-gap](https://www.ip2location.io/ip2whois-documentation).

### #6 — TAGGUN Receipt OCR Scanning API (`candidate-taggun-receipt-ocr-scanning-api-b55fde580b`)

- **Date-qualified API maintenance — ❓ UNKNOWN.** The official changelog has August 2026 month-level entries but no exact activity day. Current maintenance remains UNKNOWN under the workflow date rule. Evidence: [evidence-8ba02c9983d9a423](https://developers.taggun.io/docs/change-logs).

### #7 — APOD (`candidate-apod-fb659cb117`)

- **Authentication — ❓ UNKNOWN.** NASA general API authentication guidance and the legacy api_key model do not establish authentication behavior for the migrated WordPress APOD route; route-specific auth remains UNKNOWN. No key was used. Evidence: [evidence-017412754bf161b6](https://api.nasa.gov/assets/html/authentication.html), [evidence-8274d5f6b9904322](https://api.nasa.gov/).
- **Free tier / pricing / eligibility — ❓ UNKNOWN.** No APOD-specific monetary price/free-tier statement was found in reviewed NASA documentation; exploratory access and demo-key provisions are not classified as a verified free tier. Evidence: [evidence-d1f1f71f77193b16](https://api.nasa.gov/).
- **Quota / rate / usage limits — ❓ UNKNOWN.** General NASA limits are 1,000/hour per registered key and 30/hour plus 50/day/IP for DEMO_KEY; NASA warns limits may vary by service. Quota for the migrated APOD route remains UNKNOWN. Evidence: [evidence-017412754bf161b6](https://api.nasa.gov/assets/html/authentication.html), [evidence-03018c60d1b79a58](https://api.nasa.gov/assets/html/authentication.html).
- **API/service terms and data/content rights — ❓ UNKNOWN.** No uniform APOD service/whole-feed license was established. NASA-origin content is subject to NASA media guidelines; third-party images require per-item rights review and NASA does not convey those rights. Evidence: [evidence-08d4e90a332c3c64](https://www.nasa.gov/nasa-brand-center/images-and-media/), [evidence-7de0223190dad581](https://science.nasa.gov/apod/apod-about/).

### #8 — CyCAT.org API (`candidate-cycat-org-api-d423696460`)

- **Authentication — ❓ UNKNOWN.** Public GET examples omit credentials and the spec lacks a security declaration, but no explicit provider statement establishes no-auth; requirements remain UNKNOWN. Evidence: [evidence-6a9cad572f54e8be](https://api.cycat.org/swagger.json), [evidence-4ccca13826dc4fc8](https://cycat.org/services/).
- **Free tier / pricing / eligibility — ❓ UNKNOWN.** No monetary price/free-tier statement was found in reviewed official sources; public/open API wording is insufficient to classify access price. Evidence: [evidence-8aab84996b5fd068](https://cycat.org/services/).
- **Quota / rate / usage limits — ❓ UNKNOWN.** No request quota/rate-limit schedule was found in reviewed official docs; unlimited use is not inferred. Evidence: [evidence-1a748be87b015140](https://api.cycat.org/swagger.json).
- **API/service terms and data/content rights — ⚠️ INCONCLUSIVE.** Official site says CyCAT.org content is CC-BY-SA and the OpenAPI spec lists CC-BY, but scope for API service/output and third-party records is unclear; API/data rights remain UNKNOWN. Evidence: [evidence-19f44987a5f44713](https://cycat.org/services/), [evidence-2cbbf05592eb5915](https://api.cycat.org/swagger.json).
- **Date-qualified API maintenance — ❓ UNKNOWN.** Spec lists version 0.9, but reviewed official sources provide no dated release/change record; current maintenance remains UNKNOWN. Evidence: [evidence-b9569ffe204f07bf](https://api.cycat.org/swagger.json), [evidence-4ccca13826dc4fc8](https://cycat.org/services/).

### #9 — Groundwater Wells, Aquifers and Registry API (`candidate-groundwater-wells-aquifers-and-registry-16109d78d4`)

- **Free tier / pricing / eligibility — ❓ UNKNOWN.** No API monetary price/free tier is published in reviewed docs. OGL-BC governs eligible data, not API price. Evidence: [evidence-fcb722aef64fb93c](https://www2.gov.bc.ca/gov/content/data/policy-standards/data-policies/open-data/api-terms-of-use-for-ogl-information).
- **Quota / rate / usage limits — ❓ UNKNOWN.** API Terms allow BC to impose or adjust limits without notice but publish no numeric request quota/rate/window; exact quota remains UNKNOWN. Evidence: [evidence-aa542331805467d4](https://www2.gov.bc.ca/gov/content/data/policy-standards/data-policies/open-data/api-terms-of-use-for-ogl-information).
- **Date-qualified API maintenance — ❓ UNKNOWN.** No dated API release/change history was identified. The future catalogue timestamp and dataset “On Going” status do not establish API maintenance; current activity remains UNKNOWN. Evidence: [evidence-4b33a77295611b13](https://apps.nrs.gov.bc.ca/gwells/api/?format=openapi), [evidence-bc67fb996accd7a2](https://catalogue.data.gov.bc.ca/dataset/e4731a85-ffca-4112-8caf-cb0a96905778).

### #10 — Xero Assets API (`candidate-xero-assets-api-585af6f87a`)

- **Date-qualified API maintenance — ❓ UNKNOWN.** Only Assets-specific dated release located is initial v1.0 on 2016-07-26; current v1.0 docs do not establish recent maintenance, so current activity remains UNKNOWN. Evidence: [evidence-63bcc4f07b443755](https://developer.xero.com/documentation/api/assets/release-notes), [evidence-2fc7d9773c3d0717](https://developer.xero.com/documentation/api/assets/assets).

### #11 — USDA ERS (`candidate-usda-ers-be60dab8d0`)

- **Free tier / pricing / eligibility — ❓ UNKNOWN.** The reviewed ERS pages do not explicitly price ARMS/data API access or establish an unconditional free tier. A free api.data.gov key-management service is not proof that the ERS data service is free. Evidence: [evidence-6e00001d084d45ae](https://www.ers.usda.gov/developer/data-apis), [evidence-4d28f51df9f60964](https://www.ers.usda.gov/developer/api-terms-of-service).
- **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED.** The 1,000/hour value is the shared api.data.gov default, not a confirmed ARMS-only limit. Evidence: [evidence-35042e0d30cbde7d](https://api.data.gov/docs/developer-manual/).
- **Date-qualified API maintenance — ❓ UNKNOWN.** The provider lists an ARMS data release dated 2024-12-18, but this is a dataset update rather than an API release/maintenance record. No API-specific maintenance activity was established. Evidence: [evidence-8c8428eee981ad31](https://www.ers.usda.gov/developer/data-apis/arms-data-api/updates-and-revisions).

### #12 — Browshot (`candidate-browshot-e01a9ec3f5`)

- **API/service terms and data/content rights — ❓ UNKNOWN.** The Terms page was last updated 2015-06-30 and does not establish current API/data-use rights; retain UNKNOWN rather than extrapolating a license. Evidence: [evidence-47201a461f1c59ba](https://browshot.com/terms).

### #13 — CFB v3 Scores (`candidate-cfb-v3-scores-274b76b3c0`)

- **API/service terms and data/content rights — ❓ UNKNOWN.** General terms establish limited use of purchased services but do not establish the specific College Football feed's display, redistribution, or commercial-data license; that remains subscription/contract-specific. Evidence: [evidence-dadf2bdd01a04e21](https://sportsdata.io/terms-of-service).
- **Date-qualified API maintenance — ❓ UNKNOWN.** No dated CFB release/change or maintenance record was established. Feed refresh intervals describe data freshness, not API software maintenance. Evidence: [evidence-4daee2a263e1d00a](https://sportsdata.io/developers/api-documentation/ncaa-football).

### #14 — ClickMeter (`candidate-clickmeter-6295c914e4`)

- **Free tier / pricing / eligibility — ❓ UNKNOWN.** Current ClickMeter-specific pricing/free access was not established. Rebrandly pricing content is not evidence of ClickMeter API pricing. Evidence: [evidence-448e90c95b433ff9](https://support.clickmeter.com/hc/en-us/articles/211030466-What-is-Link-Shortening-), [evidence-8cb99199bbeb080b](https://support.clickmeter.com/hc/en-us/articles/211037086-Overview).
- **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED.** The 100-result cap is pagination. The request-rate figure is from 2019 support material and neither historical limit is represented as newly verified current service behavior. Evidence: [evidence-bd850f15dadd1d2b](https://support.clickmeter.com/hc/en-us/articles/211036966), [evidence-667618f594b0a12a](https://support.clickmeter.com/hc/en-us/articles/211037406-Getting-Started-with-API-V2-0).
- **API/service terms and data/content rights — ❓ UNKNOWN.** No current ClickMeter API/data license was established. An attempted legacy terms URL returned Rebrandly-branded marketing content rather than ClickMeter-specific terms; this does not prove terms are absent. Rebrandly terms are not transferred to ClickMeter, so preserve UNKNOWN and defer legal review. Evidence: [evidence-8cb99199bbeb080b](https://support.clickmeter.com/hc/en-us/articles/211037086-Overview), [evidence-448e90c95b433ff9](https://support.clickmeter.com/hc/en-us/articles/211030466-What-is-Link-Shortening-), [evidence-3f67b700ab5e166e](https://www.clickmeter.com/terms-conditions).
- **Date-qualified API maintenance — ❓ UNKNOWN.** No dated API release or maintenance record was established. Old support articles and Rebrandly-branded homepage results do not establish current maintenance or discontinuation. Evidence: [evidence-448e90c95b433ff9](https://support.clickmeter.com/hc/en-us/articles/211030466-What-is-Link-Shortening-).
- **Workflow — ⏸️ DEFERRED.** Actual saved stage: `license_review / deferred`; final transition `event-bfeccdf78b58586a`. Remain deferred; no proposal/approval/acceptance.

### #15 — ExchangeRate-API (`candidate-exchangerate-api-47f3e350f1`)

- **Date-qualified API maintenance — ❓ UNKNOWN.** The reviewed pages document exchange-rate update cadence, not a dated API release or maintenance event; no such maintenance record was established. Evidence: [evidence-5b8657f6151c9128](https://www.exchangerate-api.com/docs/overview).

### #16 — JSON2Video (`candidate-json2video-ae32ed51fc`)

- **Date-qualified API maintenance — ❓ UNKNOWN.** The July 2026 terms update is legal activity, not evidence of an API release or maintenance event. No dated API change record was established. Evidence: [evidence-168dbb60d06f3047](https://json2video.com/legal/terms-of-use.html).

### #17 — Personalized Offers (`candidate-personalized-offers-3ef4d01fa1`)

- **Free tier / pricing / eligibility — ❓ UNKNOWN.** A Sandbox is documented, but reviewed product pages do not establish its price or a generally free API tier. Production access requires verification/approval; no access was requested. Evidence: [evidence-016c1042a03db41a](https://developer.mastercard.com/presentment/documentation/quick-start-guide/), [evidence-af0e5ca2044b88d5](https://developer.mastercard.com/presentment/documentation/).
- **Quota / rate / usage limits — ❓ UNKNOWN.** No numeric Offers for Publishers request quota/rate limit was established in the reviewed public materials. Evidence: [evidence-af0e5ca2044b88d5](https://developer.mastercard.com/presentment/documentation/).
- **API/service terms and data/content rights — 🟨 PARTIALLY_VERIFIED.** These global Developer Terms establish narrow access/use conditions, not product-specific production pricing or an unrestricted data license. Evidence: [evidence-26f96bda0e79b717](https://developer.mastercard.com/terms-of-use).
- **Date-qualified API maintenance — ❓ UNKNOWN.** A release-history page exists, but the reviewed public entries did not establish an exact dated maintenance event; additional notes are gated. No date-qualified activity finding is asserted. Evidence: [evidence-2cf3b090abeac87c](https://developer.mastercard.com/presentment/documentation/release-history/).

### #18 — The SMS Works API (`candidate-the-sms-works-api-c4a3fea09f`)

- **API/service terms and data/content rights — ❓ UNKNOWN.** The terms cover messaging conduct, key security, and disclosure for reselling texts, but a current API/data license or broader data-use grant was not established. Evidence: [evidence-60a1ab9b7d604555](https://thesmsworks.co.uk/terms).
- **Date-qualified API maintenance — ❓ UNKNOWN.** No dated API release or maintenance record was established. The age of the terms page is not evidence of API maintenance status. Evidence: [evidence-a6de56c0e7866c52](https://thesmsworks.co.uk/developers).

### #19 — Trash Nothing (`candidate-trash-nothing-d6fee4380e`)

- **Free tier / pricing / eligibility — ❓ UNKNOWN.** App registration/login is required, but reviewed provider pages do not state a fee or explicitly establish a free tier. Personal-use terms do not prove free pricing. Evidence: [evidence-9c6f63c810d686dc](https://trashnothing.com/app/developer), [evidence-c3b7c3ca1154cead](https://trashnothing.com/terms).
- **Quota / rate / usage limits — ❓ UNKNOWN.** The specification documents feed windows and pagination/response caps but no API-wide request-per-time quota; retain UNKNOWN for general rate limits. Evidence: [evidence-20b3422d81dba2ee](https://trashnothing.com/api/v1.4/trashnothing-openapi.yaml).
- **Date-qualified API maintenance — ❓ UNKNOWN.** No provider API release or maintenance record later than the documentation's May 2022 reference was established. Evidence: [evidence-9c6f63c810d686dc](https://trashnothing.com/app/developer), [evidence-cf752bf5d1663352](https://trashnothing.com/api/v1.4/trashnothing-openapi.yaml).

### #20 — Vercel API (`candidate-vercel-api-d95586b8bf`)

- **Date-qualified API maintenance — ❓ UNKNOWN.** No dated REST API release or maintenance record was established; rate-limit documentation is not itself a release record. Evidence: [evidence-45a65b0d89f4501f](https://vercel.com/docs/rest-api).

### #21 — Zalando Shop (`candidate-zalando-shop-04d1e2ab90`)

- **Authentication — ⚠️ INCONCLUSIVE.** The archived source does not establish authentication for a current supported Shop API. Evidence: [evidence-m09-21-docs](https://github.com/zalando/shop-api-documentation/blob/master/README.md).
- **Free tier / pricing / eligibility — ❓ UNKNOWN.** No current API pricing or access tier was established; general consumer-service terms are not API pricing. Evidence: [evidence-m09-21-docs](https://github.com/zalando/shop-api-documentation/blob/master/README.md).
- **Quota / rate / usage limits — ❓ UNKNOWN.** No current Shop API quota or rate limit was established. Evidence: [evidence-m09-21-docs](https://github.com/zalando/shop-api-documentation/blob/master/README.md).
- **API/service terms and data/content rights — ❓ UNKNOWN.** General Zalando consumer Terms restrict automated use but are not API-specific; current API-service and shop-data reuse terms remain unresolved. Evidence: [evidence-m09-21-terms](https://accounts.zalando.com/terms-of-use).
- **Date-qualified API maintenance — ⚠️ INCONCLUSIVE.** The documentation repository was archived in 2018, with its README last committed in January 2018. No current API maintenance record was established; do not generalize to Zalando’s other APIs. Evidence: [evidence-m09-21-archive](https://github.com/zalando/shop-api-documentation/blob/master/README.md).
- **Documentary Python feasibility — ❓ UNKNOWN.** No current endpoint or provider-maintained Python integration for the legacy Shop Public API was established. Evidence: [evidence-m09-21-endpoint](https://github.com/zalando/shop-api-documentation/blob/master/README.md).

### #23 — NLR Developer Network (`candidate-nlr-developer-network-ec3f818d2c`)

- **Free tier / pricing / eligibility — ❓ UNKNOWN.** The signup page documents key registration but does not state an API service price or unconditional free tier. No account was created. Evidence: [evidence-m09-23-signup](https://developer.nlr.gov/signup/), [evidence-m09-23-terms](https://developer.nlr.gov/terms/).
- **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED.** Provider default and DEMO_KEY allowances are explicit; do not treat the shared default as a service-specific override. Evidence: [evidence-m09-23-quota](https://developer.nlr.gov/docs/rate-limits/).

### #24 — OpenWeatherMap (`candidate-openweathermap-414a390f3e`)

- **Date-qualified API maintenance — ❓ UNKNOWN.** A provider migration guide documents the v4 transition, but no dated release/maintenance record was established. Do not infer uptime from the migration page. Evidence: [evidence-m09-24-migration](https://openweathermap.org/api/one-call-3-migration).

### #25 — Census Bureau (`candidate-census-bureau-670fd2a556`)

- **Authentication — ⚠️ INCONCLUSIVE.** The May 2026 guide says every data query needs a key; the official Feb. 19, 2026 presentation says a key is needed only above 500 queries per IP/day and demonstrates no-key use. The free key is documented, but the requirement threshold conflict remains unresolved. Evidence: [evidence-m09-25-limits](https://www.census.gov/data/developers/guidance/api-user-guide.Query_Limits.html), [evidence-m09-25-key](https://www.census.gov/data/developers/guidance/api-user-guide.API_Key.html), [evidence-m09-25-training](https://www2.census.gov/about/training-workshops/2026/2026-02-19-getting-started-with-census-api-presentation.pdf).
- **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED.** The 50-variable limit is current-guide wording. Official training’s 500-per-IP/day key threshold conflicts with the newer all-queries-key wording; do not state a settled daily request quota. Evidence: [evidence-m09-25-limits](https://www.census.gov/data/developers/guidance/api-user-guide.Query_Limits.html), [evidence-m09-25-training](https://www2.census.gov/about/training-workshops/2026/2026-02-19-getting-started-with-census-api-presentation.pdf).

### #26 — GovInfo (`candidate-govinfo-d67a219b74`)

- **Free tier / pricing / eligibility — ❓ UNKNOWN.** The reviewed key-signup and umbrella limit pages do not establish a GovInfo-specific price or unconditional free service tier. Evidence: [evidence-m09-26-auth](https://www.govinfo.gov/api-signup), [evidence-m09-26-quota](https://api.data.gov/docs/developer-manual/).
- **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED.** Record the api.data.gov default narrowly; a GovInfo-specific rate-limit override was not found in the reviewed sources. Evidence: [evidence-m09-26-quota](https://api.data.gov/docs/developer-manual/).
- **API/service terms and data/content rights — ❓ UNKNOWN.** The reviewed copyright/policies fetch was only a stub; collection-specific rights remain unresolved. Do not infer public-domain status for all GovInfo content. Evidence: [evidence-m09-26-copyright](https://www.govinfo.gov/about/policies#copyright).
- **Date-qualified API maintenance — ❓ UNKNOWN.** No dated provider backend release or maintenance record was established. A repository history page without displayed commits is not evidence of inactivity. Evidence: [evidence-m09-26-api_docs](https://api.govinfo.gov/docs/).

### #27 — RevAddress (`candidate-revaddress-3b7f8a6f2c`)

- **Authentication — ❓ UNKNOWN.** The reviewed sources do not establish a sufficiently clear authentication requirement for this candidate; do not infer a key requirement from directory metadata. Evidence: [evidence-m09-27-docs](https://revaddress.com/docs/).
- **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED.** The monthly operations cap and DPV purchase requirement are product-specific; no universal per-second request limit was identified. Evidence: [evidence-m09-27-pricing](https://revaddress.com/pricing/), [evidence-m09-27-terms](https://revaddress.com/legal/terms/).
- **API/service terms and data/content rights — ❓ UNKNOWN.** The reviewed service terms and privacy policy do not establish a complete API/data license or USPS DPV downstream rights; obtain product-specific terms before use. Evidence: [evidence-m09-27-terms](https://revaddress.com/legal/terms/), [evidence-m09-27-privacy](https://revaddress.com/legal/privacy/).
- **Date-qualified API maintenance — ❓ UNKNOWN.** No dated provider API release or maintenance record was established. Terms revision date is not evidence of software/backend maintenance. Evidence: [evidence-m09-27-docs](https://revaddress.com/docs/).

### #28 — Telesign (`candidate-telesign-b322500dc2`)

- **Free tier / pricing / eligibility — ❓ UNKNOWN.** The reviewed page lists channel-specific per-message rates and says the unified Verify API is sales-priced; these facts do not establish a single permanent free tier or unified API price. Evidence: [evidence-m09-28-pricing](https://www.telesign.com/pricing/verification-pricing), [evidence-m09-28-auth](https://developer.telesign.com/enterprise/docs/verify-api-get-started-with-sms).
- **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED.** Record the documented signal only; no numeric quota was inferred. Evidence: [evidence-m09-28-quota](https://developer.telesign.com/enterprise/docs/verify-api-status-codes).
- **API/service terms and data/content rights — ❓ UNKNOWN.** General service terms incorporate the AUP, DPA, and Privacy Notice; consent/content restrictions apply. Verify-specific data roles, retention, and any product-specific data reuse license remain unresolved. Evidence: [evidence-m09-28-terms](https://www.telesign.com/telesign-terms-of-service), [evidence-m09-28-aup](https://www.telesign.com/acceptable-use-policy), [evidence-m09-28-dpa](https://www.telesign.com/DPA), [evidence-m09-28-privacy](https://www.telesign.com/privacy-notice).

### #29 — 1Password Connect (`candidate-1password-connect-e5ab7cffc9`)

- **Quota / rate / usage limits — 🟨 PARTIALLY_VERIFIED.** The cache behavior and undocumented internal initial-fetch limits are provider-documented; do not describe Connect as having no limits at all. Evidence: [evidence-m09-29-quota](https://www.1password.dev/connect), [evidence-m09-29-manage](https://www.1password.dev/connect/manage-connect).
- **API/service terms and data/content rights — ❓ UNKNOWN.** The business subscription terms govern service/customer-data use, but no open/public data license applies to this private secrets API; customer data rights are account-specific. Evidence: [evidence-m09-29-terms](https://1password.com/legal/terms-of-service).
- **Date-qualified API maintenance — ⚠️ INCONCLUSIVE.** The API reference/spec says 1.8.1 while the publisher’s Docker tags list 1.8.4; no dated Connect server release or actual deployment version was established. Preserve the discrepancy rather than infer current maintenance or uptime. Evidence: [evidence-m09-29-api_ref](https://www.1password.dev/connect/api-reference), [evidence-m09-29-docker_api](https://hub.docker.com/r/1password/connect-api/tags), [evidence-m09-29-docker_sync](https://hub.docker.com/r/1password/connect-sync/tags).

### #30 — City Context (`candidate-city-context-30c2c95ecb`)

- **API existence / scope — ⚠️ INCONCLUSIVE.** Current API existence could not be confirmed from the inaccessible provider-domain pages. Stale repository activity and an uncorroborated secondary closure claim are not treated as provider facts. Evidence: [evidence-m09-30-home](https://citycontext.com), [evidence-m09-30-reference](https://api.citycontext.com).
- **Provider identity — ⚠️ INCONCLUSIVE.** Provider identity and current API operation could not be independently confirmed from the failed page fetches; preserve the imported lead as unverified. Evidence: [evidence-m09-30-home](https://citycontext.com), [evidence-m09-30-reference](https://api.citycontext.com).
- **Official documentation / version — ⚠️ INCONCLUSIVE.** The documentation URL fetch returned HTTP 500; this does not establish that documentation is absent. Evidence: [evidence-m09-30-reference](https://api.citycontext.com).
- **Authentication — ⚠️ INCONCLUSIVE.** The API reference could not be retrieved, so authentication requirements remain unknown. Evidence: [evidence-m09-30-reference](https://api.citycontext.com).
- **Free tier / pricing / eligibility — ⚠️ INCONCLUSIVE.** Current pricing or free access could not be confirmed from provider-controlled material. Evidence: [evidence-m09-30-reference](https://api.citycontext.com).
- **Quota / rate / usage limits — ⚠️ INCONCLUSIVE.** No provider-controlled quota/rate-limit documentation was available from the failed fetch. Evidence: [evidence-m09-30-reference](https://api.citycontext.com).
- **API/service terms and data/content rights — ⚠️ INCONCLUSIVE.** No current provider API/data terms or license were retrieved; stale/secondary sources do not establish rights. Evidence: [evidence-m09-30-reference](https://api.citycontext.com).
- **Date-qualified API maintenance — ⚠️ INCONCLUSIVE.** No current provider-controlled maintenance record was obtained; stale repository activity is not proof of inactivity or closure. Evidence: [evidence-m09-30-home](https://citycontext.com).
- **Documentary Python feasibility — ⚠️ INCONCLUSIVE.** No usable provider endpoint schema or SDK evidence was retrieved; generic integration feasibility remains unassessed. Evidence: [evidence-m09-30-reference](https://api.citycontext.com).
- **Workflow — ⏸️ DEFERRED.** Actual saved stage: `license_review / deferred`; final transition `event-affa143c3f8e29b5`. Remain deferred; no proposal/approval/acceptance.

## Explicit high-priority contradiction / scope items

| Candidate | Issue | What remains unresolved | Evidence |
| ---: | --- | --- | --- |
| #25 Census Bureau | Authentication/quota guidance conflict | May 2026 user guide says every data query requires a key; official Feb. 19, 2026 presentation says only above 500 queries/IP/day and no throttling. No universal daily quota settled; dataset rights remain per-data product. | [evidence-m09-25-limits](https://www.census.gov/data/developers/guidance/api-user-guide.Query_Limits.html), [evidence-m09-25-key](https://www.census.gov/data/developers/guidance/api-user-guide.API_Key.html), [evidence-m09-25-training](https://www2.census.gov/about/training-workshops/2026/2026-02-19-getting-started-with-census-api-presentation.pdf) |
| #27 RevAddress | Free USPS DPV discrepancy | Free plan describes Census/local operations; USPS DPV terms/pricing say paid credits. Do not infer DPV is free from a conflicting example. | [evidence-m09-27-pricing](https://revaddress.com/pricing/), [evidence-m09-27-terms](https://revaddress.com/legal/terms/) |
| #28 Telesign | Product/channel scope | Unified Verify is distinct from legacy SMS Verify and channel-specific pages; method lists/prices do not establish unified Verify pricing or Verify-specific processing/retention. | [evidence-m09-28-pricing](https://www.telesign.com/pricing/verification-pricing), [evidence-m09-28-auth](https://developer.telesign.com/enterprise/docs/verify-api-get-started-with-sms), [evidence-m09-28-terms](https://www.telesign.com/telesign-terms-of-service), [evidence-m09-28-aup](https://www.telesign.com/acceptable-use-policy), [evidence-m09-28-dpa](https://www.telesign.com/DPA), [evidence-m09-28-privacy](https://www.telesign.com/privacy-notice) |
| #29 1Password Connect | Version / entitlement scope | API docs/spec version and publisher Docker tag differ; no actual deployment version or numeric initial-fetch quota. Connect is self-hosted and customer-subscription entitled, not a public dataset API. | [evidence-m09-29-api_ref](https://www.1password.dev/connect/api-reference), [evidence-m09-29-docker_api](https://hub.docker.com/r/1password/connect-api/tags), [evidence-m09-29-docker_sync](https://hub.docker.com/r/1password/connect-sync/tags), [evidence-m09-29-quota](https://www.1password.dev/connect), [evidence-m09-29-manage](https://www.1password.dev/connect/manage-connect) |
| #14 ClickMeter | Deferred current legal review | Historic API v2 docs and a Rebrandly-branded legacy terms destination do not establish current ClickMeter service/data terms or pricing. | [evidence-8cb99199bbeb080b](https://support.clickmeter.com/hc/en-us/articles/211037086-Overview), [evidence-448e90c95b433ff9](https://support.clickmeter.com/hc/en-us/articles/211030466-What-is-Link-Shortening-), [evidence-3f67b700ab5e166e](https://www.clickmeter.com/terms-conditions) |
| #30 City Context | Deferred provider evidence | Provider-domain page fetches returned HTTP 500; no current provider identity, API status, documentation, pricing or terms were established. Failure does not prove closure. | [evidence-m09-30-home](https://citycontext.com), [evidence-m09-30-reference](https://api.citycontext.com) |

## Follow-up order (documentary only)

1. Preserve current hashes and append a date correction only if the actual source-review timestamps can be established; do not edit old evidence or break the event chain.
2. Keep #14 and #30 deferred unless suitable current provider-controlled primary evidence is available. Do not infer closure or substitute another provider's terms.
3. Reconcile Census #25 official authentication/quota guidance and RevAddress #27 DPV pricing examples before classifying those conditions more narrowly.
4. Obtain use-case-specific rights/pricing details for the UNKNOWN product-specific scopes; keep free account/trial/sandbox distinct from free production service.
5. Preserve `NOT_TESTED` accessibility until a separately authorized and policy-compliant testing phase is approved; this consolidation makes no such request.
6. Continue candidate review only as a separate mission/checkpoint; no #31–#100 conclusions are made here.

This issue inventory enumerates **83 candidate-specific unresolved/partial field items** (accessibility is summarized once across all candidates). Some concerns are cross-cutting and therefore appear both here and in a candidate section.

[Back to the consolidated evidence map](phase-4-consolidated-evidence-map-1-30.md) · [Human-approval queue](phase-4-human-approval-queue-1-30.md) · [Audit report](phase-4-consolidated-audit-report-1-30.md)
