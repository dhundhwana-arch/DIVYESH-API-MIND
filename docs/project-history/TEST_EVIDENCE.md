# Test and validation evidence

**Mission 04 validation date:** 2026-11-12. Checks were run locally against the current source tree. They do not contact candidate provider endpoints or turn source claims into verified facts.

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
| `.venv/bin/python -m build --outdir /tmp/divyesh-api-mind-build-final3` | Passed without build warnings; source distribution and pure-Python wheel built with the eight bundled JSON data files included |
| Install the built wheel into a temporary target and import with `python -S` | Passed; wheel import loaded 26 API, 5 model, and 8 dataset records; MCP working-integration count remained 0 |
| `git diff --check` | Passed at final repository review |
| Internal Markdown links and README navigation | 137 local paths, fragments, and image paths passed across 23 Markdown files; README has the required 20 numbered sections. External links were not fetched or certified |

The test suite uses mocked transports for network behavior. The project already records three one-time GitHub/PyPI/npm metadata reads from 2026-11-12 in [`../live-probes.md`](../live-probes.md); they are historical, separate from this validation, and unrelated to the 100 candidates. **No Phase 3 candidate endpoint was contacted during Mission 04.**

## Secret-scan review

`detect-secrets` 1.5.0 was run locally with `--no-verify` (so it did not call a remote verifier) on the non-ignored repository files, excluding `.git`, the virtual environment, and build artifacts. It reported **330 heuristic findings in 9 files**. Manual review classified them as non-credential material:

- 323 high-entropy-hex findings are 40-character pinned Git revisions/test fixtures or 64-character `source_content_sha256` and `event_sha256` integrity fields;
- keyword findings are environment-variable names and placeholder examples (for example, `CENSUS_API_KEY` and `TWILIO_AUTH_TOKEN`), not credential values;
- Basic Auth findings are intentionally malformed/placeholder URLs and test-only dummy values.

The catalog validator's own embedded-credential check also passed. This is a documented, human-reviewed scan result—not proof that every possible secret detector or provider-specific credential pattern is covered. No scanner baseline was committed.

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
