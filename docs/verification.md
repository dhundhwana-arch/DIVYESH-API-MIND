# Evidence-based API verification workflow

Phase 3 adds a local, auditable review workflow for API discovery candidates. It is deliberately separate from the accepted catalog: ranking does not verify a provider, and creating a batch or proposal never writes to `apis.json`.

## Current review batch

The pinned batch [`src/divyesh_api_mind/data/verification_review_batch_2026-11-12.json`](../src/divyesh_api_mind/data/verification_review_batch_2026-11-12.json) contains the 100 highest-priority leads selected from the combined discovery queue as of **2026-11-12**. It is a queue for investigation, not a verified API list. The actual findings and blockers are reported in [`phase-3-verification-report.md`](phase-3-verification-report.md).

## Ranking is triage, not truth

The weighted base score has 100 points:

| Signal | Weight |
|---|---:|
| Project usefulness | 18 |
| Official-documentation availability | 16 |
| OpenAPI/Swagger availability | 14 |
| Free-access evidence | 10 |
| Authentication requirements | 8 |
| Provider/repository maintenance activity | 8 |
| API/service/data license clarity | 8 |
| Category diversity | 10 |
| Python integration feasibility | 8 |

Every selected record carries component scores and reasons. A documentation or specification pointer is only a review lead until provider ownership/content is established. Upstream `verified`, checked-date, pricing, auth, license, and priority fields stay as source claims; upstream priority is recorded but receives **no score bonus**. An upstream “Free” claim is not a finding. Maintenance freshness uses a reviewed primary maintenance record's `activity_on` date, never a directory's `checked` date.

Category diversity is applied marginally as candidates are selected. Scores are for investigation order only; they do not indicate quality, API existence, provider identity, uptime, free status, legal rights, human approval, or catalog acceptance.

## Workflow and evidence rules

Every candidate moves through these distinct stages:

1. candidate discovery
2. metadata validation
3. official-source identification
4. documentation review
5. authentication verification
6. free-tier verification
7. endpoint verification
8. license review
9. human approval
10. catalog acceptance

The batch logs initial discovery, structural metadata validation, findings, evidence additions, stage outcomes, proposals, human decisions, and acceptance records. Audit events form a SHA-256-linked sequence so accidental edits to prior event content are detected; this is an integrity check, not a cryptographic signature of reviewer identity. Blocked/deferred work must be explicitly resumed. Stages cannot be skipped or reordered. Structural metadata validation confirms the imported queue schema only; it does **not** confirm that an API exists or that a link is current.

Every evidence item records a safe HTTPS URL, evidence type, observation date, reviewer status, confidence, reviewer, source classification, and notes. A verified fact requires supporting, primary provider evidence with confidence of at least **0.75**. Direct local probe results are accepted only for the accessibility finding and only when linked to both reviewed provider permission and exact official endpoint documentation. Community catalogs, imported OpenAPI declarations, and source-repository licenses cannot independently prove provider terms, access, auth, or API/data rights. When evidence is absent, secondary, conflicting, stale, or inconclusive, classification remains `UNKNOWN` (current accessibility remains `NOT_TESTED` unless tested).

The proposal gate requires verified API existence, provider identity, documentation, current unauthenticated endpoint accessibility, authentication, access tier, quota information, active maintenance evidence, API/service/data licensing, and feasible Python integration. Candidates with possible matches to accepted APIs are blocked from proposal until resolved. Every proposed record must preserve verified auth/access/quota/license values and cite the evidence used. It also retains the candidate's original source attributions, raw source claims, and verification-history snapshot. A separate explicit human approval is required; catalog acceptance is a later human step and is recorded only after the exact approved record already exists in a catalog. No workflow command silently promotes or overwrites accepted records.

## Safe endpoint checks

No endpoint is tested when a batch is created. An explicit `verify-probe` call is allowed only when:

- official provider policy evidence is reviewed, supports the permission claim, has confidence at least 0.75, and explicitly records `permits_unauthenticated_read_probes: true`;
- the target URL and method exactly match provider-controlled endpoint documentation;
- the candidate's base host matches the endpoint host;
- the request is unauthenticated `GET` or `HEAD`, with no query string, body, caller-supplied headers, or API credentials;
- requests are spaced by at least two seconds per host, have no retries, use a timeout no greater than 10 seconds, and read at most 256 KiB (default: 5 seconds and 64 KiB).

Redirects are not followed. Response bodies and headers are discarded; only status, bounded byte count, safe outcome, and probe metadata are recorded. Network failures are inconclusive and do not prove the service is absent. Provider restrictions always override these conservative defaults; do not probe if policy is unclear or disallows it.

## CLI workflow

Create and validate the reproducible 100-candidate batch:

```bash
apimind verify-create \
  --queue src/divyesh_api_mind/data/discovery_candidates.json \
  --limit 100 --as-of 2026-11-12 \
  --output src/divyesh_api_mind/data/verification_review_batch_2026-11-12.json
apimind verify-validate src/divyesh_api_mind/data/verification_review_batch_2026-11-12.json
```

Manually reviewed source evidence is added from a JSON file; `verify-add-evidence` does **not** fetch URLs and refuses caller-supplied `endpoint_probe` records. Only the guarded `verify-probe` operation can append a direct probe observation. A minimal evidence object looks like:

```json
{
  "evidence_id": "evidence-unique-id",
  "candidate_id": "candidate-id-from-the-batch",
  "url": "https://provider.example/docs/api",
  "evidence_type": "official_documentation",
  "observed_on": "2026-11-12",
  "reviewer_status": "supports",
  "confidence": 0.9,
  "notes": "Provider-controlled documentation reviewed; describe the relevant statement.",
  "source_classification": "official_provider",
  "primary_source": true,
  "reviewer": "reviewer-name"
}
```

Then record a stage-appropriate finding and transition only after all required findings are recorded:

```bash
apimind verify-add-evidence batch.json CANDIDATE_ID --evidence evidence.json \
  --reviewer reviewer-name --output batch-next.json
apimind verify-finding batch-next.json CANDIDATE_ID api_real \
  --value-json true --status verified --evidence-id evidence-unique-id \
  --reviewer reviewer-name --notes "Provider identifies the service as an API." \
  --confidence 0.9 --observed-on 2026-11-12 --output batch-next.json
apimind verify-transition batch-next.json CANDIDATE_ID --outcome completed \
  --reviewer reviewer-name --notes "Official-source review complete." --output batch-next.json
```

Use JSON values such as `"none"`, `"FREE_NO_KEY"`, `"FREE_TIER_LIMITED"`, a quota object with substantive quota/limit information, or a license object that separately states both `service` and `data` terms. An unresolved quota, service term, or data right must remain `UNKNOWN`, not be filled with directory claims. Do not copy secrets, tokens, or API keys into evidence, findings, notes, URLs, or the batch.

`verify-probe` is the only Phase 3 command that contacts a candidate endpoint. `verify-propose` stores a validated draft only. At the human-approval stage, use `verify-transition --reviewer-role human --decision approved`; to reject, use an explicit human rejection. To record catalog acceptance, first have a human add the exact approved record to the selected API catalog, then use `verify-transition --reviewer-role human --decision accepted` with its ID and canonical SHA-256. The CLI and library both verify the existing record against the approved proposal; neither writes to catalogs. Batch-output paths are checked so they cannot overwrite accepted catalog files or discovery queues.

## Library API

The public package exports `rank_review_candidates`, `create_verification_batch`, `validate_verification_batch`, `create_review_evidence`, `add_review_evidence`, `record_review_finding`, `transition_review_stage`, `probe_review_endpoint`, `create_api_record_proposal`, `find_candidate_duplicates`, and validated batch load/save helpers. All mutation functions return an updated batch copy and preserve the input object.
