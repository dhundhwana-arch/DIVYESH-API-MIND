## Summary

Describe the change and why it is needed.

## Scope

- [ ] Code
- [ ] Catalog or discovery data
- [ ] Documentation / example
- [ ] Packaging / repository metadata

## Evidence and provenance

- Sources/revisions/licenses for any third-party material:
- Are upstream claims still labeled as claims?
- Are unresolved facts left `UNKNOWN`?

## Validation

- [ ] `python -m pytest -q`
- [ ] `python -m compileall -q src tests`
- [ ] `apimind validate` (if applicable)
- [ ] `apimind verify-validate ...` (if the verification batch or workflow changed)
- [ ] `git diff --check`

## Network use

- [ ] No provider/network request was made.
- [ ] A request was made only after reviewing current provider policy and exact official endpoint documentation; describe the scope and permission here:

## Remaining risks or limitations
