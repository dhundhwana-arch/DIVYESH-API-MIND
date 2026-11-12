# Contributing

Thank you for helping improve DIVYESH API MIND. Contributions should preserve its evidence-first, offline-by-default behavior.

## Ground rules

- Keep accepted catalog records, discovery candidates, upstream claims, and MCP metadata distinct.
- Preserve source attribution, pinned revisions, and applicable license context when importing or changing third-party material.
- Leave unresolved authentication, pricing, quotas, rights, and endpoint status as `UNKNOWN`; do not promote a candidate from directory text or a source license alone.
- Never commit credentials, personal data, provider responses containing sensitive content, or unreviewed secrets.
- Do not add an endpoint health probe or perform a provider request without reviewing the provider's current policy and exact official endpoint documentation. Do not probe any Phase 3 candidate without the required reviewed permission evidence.
- Keep tests, validation, and normal development commands offline. Mock network transports in tests.

## Development setup

Python 3.10 or newer is required. From a checkout of the repository:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
```

On Windows PowerShell, activate with `.venv\\Scripts\\Activate.ps1`.

## Before opening a pull request

Run the applicable local checks:

```bash
python -m pytest -q
python -m compileall -q src tests
apimind validate
apimind verify-validate src/divyesh_api_mind/data/verification_review_batch_2026-11-12.json
git diff --check
```

For discovery changes, validate the queue and preserve all source attributions. For package metadata changes, build a wheel and source distribution with `python -m build`; do not commit generated `dist/` or `build/` artifacts. Tests and routine validation must not contact providers.

## Pull request notes

Use the pull-request template. Describe:

- the user-facing change and affected catalog/data/doc files;
- commands/tests run, including the Python version;
- any new external data and its source, revision, license, and transformation;
- whether a real network call was made, and if so, the reviewed official permission and exact documented endpoint;
- any remaining uncertainty or limitation.

Small, reviewable changes are preferred. Do not add a CI, coverage, release, or publication claim unless a corresponding workflow or published artifact exists.
