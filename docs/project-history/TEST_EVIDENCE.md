# Test and validation evidence

**Mission 04 validation date:** 2026-11-12. Checks were run locally against the current source tree. They do not contact candidate provider endpoints or turn source claims into verified facts.

## Final integrated delivery validation — 2026-11-18 (UTC)

This final checkpoint supersedes earlier Mission 09 implementation-checkpoint counts where they differ. Commands were run against the reconciled feature-branch worktree. Historical Mission 08 evidence dates and hash-linked events were not rewritten.

| Check | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q` | **110 passed, 13 subtests passed** |
| `.venv/bin/python -m pytest -q tests/test_mission09.py` | **35 passed**; GitHub/Ollama transports remain mocked and vault files are temporary test fixtures |
| `.venv/bin/python -m compileall -q src tests examples` | Passed |
| `.venv/bin/apimind validate` | Passed; accepted catalogs, 2,964 discovery candidates, and 3 OpenAPI review candidates valid (queues remain unpromoted) |
| `verify-validate` on the original, pilot, and working review batches | Passed on all three; no historical batch content was edited |
| Source distribution and wheel build; fresh isolated target install/import; `python -S -m divyesh_api_mind --help` | Passed; isolated import reported 26 APIs / 5 models / 8 datasets / 6 MCP metadata / 0 Mission 09 discovery leads |
| README Python examples and offline CLI examples | Passed. Target-file schema example checked locally; it did not issue a GitHub request. `config-check` was exercised in a clean environment and returned the expected status 1 for absent required keys while displaying variable names only. |
| Local Markdown/image/anchor check; SVG XML check; Mermaid parser | Passed: 144 local destinations across 8 Markdown files, the logo parses as SVG XML, and both README diagrams parse under Mermaid 12.3.0. External URLs were not fetched. |
| `git diff --check` | Passed |
| `detect-secrets==1.5.0 scan --no-verify --all-files` on changed code/docs | 7 heuristic findings in 2 files (`research.py`, `tests/test_mission09.py`); manually reviewed as the `api_key_required` field name and deliberately fake test-only API-key/password/secret patterns and values. No verifier/network plugin ran; no real credentials used. |
| Focused source-level security review | Bounded vault/`.env` reads and passphrase input; regular-file and POSIX last-component symlink/FIFO protections; crypto/file permissions reviewed. Existing provider transport's DNS/proxy limits are disclosed. This is not an independent audit or certification. |
| Protected-artifact SHA-256 checks | Passed: API catalog `6a6e3d6ed2a3b638edc7767143aa209af84ab4b0b02616585699c30cbb601219`; verification batch `c07781393d477369156beceb03dd2137a6b360966b4a8f92fc7e0ae0c1193085`; Phase 4 pilot `5d68dbeee2ec646c060c3c361cbb800cd29e836284af4e59eb27e96ebb99d999`; Phase 4 review `a22fe4edf469ff73e5f0405232406e1a50908e2b1a7410901cd5819ada1cf135`. Preservation manifest SHA-256: `3af281f062a0793e2b0a9638e25948ad96e6244efc2686474d06d2081b08255a`. |

The preservation manifest inventories 69 pre-sync workspace files (54 identical to the fetched tree, 9 changed, 6 local-only); **all 69 recorded workspace SHA-256 values matched the preserved pre-sync tar archive**. The final repository contains **35 Mission 09 offline/mocked tests**. No provider page or candidate endpoint, GitHub metadata collector, MCP server, or Ollama runtime was contacted; no account, paid service, or real credential was used. PyPI access was only for local QA/build/security tooling. The collector remains unrun by design.

## Mission 08 consolidated map validation — 2026-11-14

The `#1–#30` consolidation was checked against the preserved original source batch and separate working review batch. The map JSON includes all 261 in-scope evidence records and 793 workflow events; no candidate evidence/history or accepted-catalog record was changed.

| Check | Result |
| --- | --- |
| `.venv/bin/apimind validate` | **Passed** — `apis`, `models`, `datasets`, `mcp_registry`, 2,964 discovery candidates (not promoted), and 3 OpenAPI review candidates (not promoted) valid |
| `.venv/bin/apimind verify-validate` on working review batch | **Passed** — `valid: true`; 100 selected, 29 with primary-source records, 30 source-identification completions, 100 accessibility states `NOT_TESTED`, 0 probes/proposals/approvals/acceptances |
| `.venv/bin/apimind verify-validate` on pilot batch | **Passed** — `valid: true`; 100 selected, 5 with primary-source records, 0 probes/proposals/approvals/acceptances |
| `.venv/bin/apimind verify-validate` on original source batch | **Passed** — `valid: true`; 100 selected, 0 primary-source reviews/probes/proposals/approvals/acceptances, 100 `NOT_TESTED` |
| `.venv/bin/python -m pytest -q` | **75 passed, 13 subtests passed** |
| `.venv/bin/python -m compileall -q src tests examples` | **Passed** |
| Consolidation ID/evidence/workflow integrity assertions | **Passed** — exactly ranks #1–#30 match by ID/name and original canonical candidate hash; 261/261 evidence records and 793/793 events match source fields exactly after removing documented registry indexes; all 793 original event hashes/chains recompute; every evidence/workflow reference resolves; 28 queue entries; #14/#30 deferred; no decisions; all 30 accessibility `NOT_TESTED`; source/pilot/working/catalog SHA-256 values unchanged |
| Local Markdown link/reference validation | **Passed** — 176 local paths/fragments across 10 changed/progress Markdown files; all 1,388 rendered evidence-ID link instances resolve. External URLs were not fetched. |
| `git diff --cached --check` | **Passed** on the final staged 11-file patch; `git diff --check` also passed. |

Validation uses repository files and mocked test transports. No candidate API endpoint, account, credential or paid service was used. The saved evidence `observed_on` and transition `recorded_on` fields are all 2026-11-12, while prior review commits and the source-review handoff indicate 2026-11-14; see the [date audit](../research/phase-4-consolidated-audit-report-1-30.md). This consolidation did not rewrite prior dates or hash-linked events.

## Mission 09 batch validation — 2026-11-12

After the #21–#30 documentary review, the following checks were rerun against the updated working batch and current repository tree:

| Check | Result |
| --- | --- |
| `.venv/bin/apimind validate` | Passed; API, model, dataset, MCP, discovery queue, and OpenAPI review queue valid |
| `.venv/bin/apimind verify-validate docs/research/phase-4-review-batch-2026-11-12.json` | Passed; 100 candidates, 29 with primary-source records, all 100 accessibility states `NOT_TESTED`, 0 endpoint probes/proposals/approvals/acceptances |
| `.venv/bin/apimind verify-validate` on the pilot and original source batch | Passed for both; original source batch remains unreviewed and separate |
| `.venv/bin/python -m pytest -q` | **75 passed, 13 subtests passed** |
| `.venv/bin/python -m compileall -q src tests examples` | Passed |
| `git diff --check` | Passed |

The first test command found no `.venv` in this checkout. The ignored local environment was then created with the project test and YAML extras; the virtual environment is not tracked. These checks use local files and mocked transports; no Mission 09 candidate endpoint/API, account, or credential was used. The batch/report hashes and per-candidate workflow outcomes are in [`../research/phase-4-batch-21-30-report-2026-11-12.md`](../research/phase-4-batch-21-30-report-2026-11-12.md).

## Mission 09 technology intelligence implementation — 2026-11-12

| Check | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q tests/test_mission09.py` | **34 passed**; all HTTP/Ollama interactions use fakes/mocks, and vault tests use temporary encrypted files |
| `.venv/bin/python -m pytest -q` | **109 passed, 13 subtests passed in 7.89s** |
| `.venv/bin/python -m compileall -q src tests examples` | Passed |
| `.venv/bin/apimind validate` | Passed; 26 APIs, 5 models, 8 datasets, 6 MCP metadata records, 2,964 general review candidates, and 3 OpenAPI review candidates; no Mission 09 discovery file was seeded |
| `.venv/bin/apimind verify-validate` on original, pilot, and working batches | Passed on all three; historical source/review counts and untested accessibility states preserved |
| `.venv/bin/apimind hub-recommend --capability coding --limit 5` | Passed offline; documentary recommendations only, no `nominatim` geocoding false-positive after boundary matching, fallback remains manual |
| `python -m build --outdir /tmp/divyesh-api-mind-mission09-build` | Passed; source distribution and pure-Python wheel built |
| Isolated wheel install/import using `python -S` | Passed; `IntelligenceHub` reported 26 APIs / 5 models / 8 datasets / 6 MCP metadata; new SDK exports imported without mandatory dependencies |
| `git diff --check` | Passed |
| Local Markdown paths/anchors on README and current Mission 09/status docs | **110 links checked**; external URLs were not fetched |
| `detect-secrets==1.5.0 scan --no-verify --all-files` on changed code/docs | **8 heuristic findings across 3 files**, manually reviewed as placeholder env names/field names and deliberate fake test credentials; no verifier/network check and no real credentials used |
| Protected artifact SHA-256 comparison | Passed: API catalog `6a6e3d6ed2a3b638edc7767143aa209af84ab4b0b02616585699c30cbb601219`; source batch `c07781393d477369156beceb03dd2137a6b360966b4a8f92fc7e0ae0c1193085`; Phase 4 pilot `5d68dbeee2ec646c060c3c361cbb800cd29e836284af4e59eb27e96ebb99d999`; Phase 4 review `a22fe4edf469ff73e5f0405232406e1a50908e2b1a7410901cd5819ada1cf135` |
| Mission 08 evidence map | Preserved 30 candidates, 261 evidence entries, 793 hash-linked workflow events; historical source dates and consolidation/report dates unchanged |

No new discovery lead, evidence item, or research-review decision was bundled (**0 / 0 / 0**). No GitHub collector, provider/product endpoint, existing candidate endpoint, local Ollama runtime, account, or paid service was contacted. The optional `security` extra was installed only in the ignored local virtual environment for encrypted-vault tests. The host-based secret scanner was deliberately run with `--no-verify`; its 8 heuristic matches were read as test/placeholder material and were not suppressed in a committed baseline. See [`../research/mission-09-implementation-report.md`](../research/mission-09-implementation-report.md) for scope and remaining work.

## Automated test and code checks

| Check | Result |
| --- | --- |
| `.venv/bin/python -m pytest -q` | **75 passed, 13 subtests passed** |
| `.venv/bin/python -m compileall -q src tests examples` | Passed |
| `.venv/bin/apimind validate` | Passed: `apis`, `models`, `datasets`, and `mcp_registry` valid; the 2,964-candidate queue and 3 OpenAPI review candidates valid and not promoted |
| `validate_review_queue(load_review_queue(...))` for `discovery_candidates.json` | Passed; 4,455 source rows, 2,964 unique candidates, 1,488 combined-stage exact merges, 717 possible-duplicate candidates |
| `.venv/bin/apimind verify-validate src/divyesh_api_mind/data/verification_review_batch_2026-11-12.json` | Passed; valid batch with 100 metadata-validated leads, 0 primary-source reviews, 0 probes, 0 proposals/approvals/acceptances, and 100 `NOT_TESTED` accessibility states |
| Example smoke runs (`catalog_browser.py --category research --limit 3`, `--capability weather --no-auth`) | Passed; local output only, no health-check option used |
| Issue-template YAML frontmatter parse | Passed for bug and feature templates |
| `.venv/bin/python -m build --outdir /tmp/divyesh-api-mind-build-final4` | Passed without build warnings; source distribution and pure-Python wheel built with the eight bundled JSON data files included |
| Install the built wheel into a temporary target and import with `python -S` | Passed; wheel import loaded 26 API, 5 model, and 8 dataset records; MCP working-integration count remained 0 |
| `git diff --check` | Passed at final repository review |
| Internal Markdown links and README navigation | 149 local paths, fragments, and image paths passed across 24 Markdown files; README has the required 20 numbered sections. External links were not fetched or certified |

The test suite uses mocked transports for network behavior. The project already records three one-time GitHub/PyPI/npm metadata reads from 2026-11-12 in [`../live-probes.md`](../live-probes.md); they are historical, separate from this validation, and unrelated to the 100 candidates. **No Phase 3 candidate endpoint was contacted during Mission 04.**

## Secret-scan review

`detect-secrets` 1.5.0 was run locally with `--no-verify` (so it did not call a remote verifier) on the non-ignored repository files, excluding `.git`, the virtual environment, and build artifacts. It reported **330 heuristic findings in 9 files**. Manual review classified them as non-credential material:

- 323 high-entropy-hex findings are 40-character pinned Git revisions/test fixtures or 64-character `source_content_sha256` and `event_sha256` integrity fields;
- keyword findings are environment-variable names and placeholder examples (for example, `CENSUS_API_KEY` and `TWILIO_AUTH_TOKEN`), not credential values;
- Basic Auth findings are intentionally malformed/placeholder URLs and test-only dummy values.

A follow-up scan of the updated README, history/status files, and Phase 4 plan found only the same reviewed README placeholder finding; no new finding was reported in the Phase 4 plan. The catalog validator's own embedded-credential check also passed. This is a documented, human-reviewed scan result—not proof that every possible secret detector or provider-specific credential pattern is covered. No scanner baseline was committed.

## Environment and scope

- The environment used Python 3.11.2; the package declares Python 3.10+.
- Test/build tools were installed in the ignored `.venv`; no environment or build artifact is part of the repository snapshot.
- PyPI was used only to install local QA/build tools and isolated build dependencies. No provider API or candidate endpoint was contacted by these checks.
- External hyperlinks were not tested. A local link check cannot certify external URLs, current terms, or service availability.

## Reproduction

From the repository root with the test extra installed:

```bash
python -m pytest -q
python -m compileall -q src tests examples
apimind validate
apimind verify-validate src/divyesh_api_mind/data/verification_review_batch_2026-11-12.json
python -m build --outdir /tmp/divyesh-api-mind-build
```
