# Phase 1 — Foundation

**Status:** foundation artifacts are present in the current project tree. This page documents the implementation visible in the repository; it does not claim a phase-specific commit date.

> **History note:** at the Mission 04 audit, the available Git history was shallow and contained only the grafted `a219f1760f9ff8ec63002fb5d8d9bf01e512984b` initial commit. The source, catalogs, tests, and most documentation were present locally but untracked. The phase narrative therefore follows repository artifacts and prior project records, not a reconstructed series of commits.

## Purpose

Provide a small Python package for browsing local API/model/dataset records and for making carefully bounded, explicitly requested HTTPS calls to selected APIs. Keep discovery and uncertain claims separate from the curated catalogs.

## Foundation represented in the source tree

- **Public package surface:** [`src/divyesh_api_mind/__init__.py`](../../src/divyesh_api_mind/__init__.py) exports `APIMind`, typed connectors, the safe transport, discovery and verification functions, validation helpers, and the MCP metadata reader.
- **Catalog loading and search:** [`catalog.py`](../../src/divyesh_api_mind/catalog.py) reads bundled JSON and provides offline search, detail, export, template, alternative, and documentation-reference helpers.
- **HTTP client and transport:** [`api_client.py`](../../src/divyesh_api_mind/api_client.py) and [`transport.py`](../../src/divyesh_api_mind/transport.py) apply catalogued host/auth boundaries, HTTPS checks, bounded responses, no-redirect behavior, and explicit request methods.
- **Typed connectors:** [`connectors.py`](../../src/divyesh_api_mind/connectors.py) wraps selected providers, including dedicated pacing/acknowledgement guards for arXiv and Nominatim.
- **Local CLI:** [`cli.py`](../../src/divyesh_api_mind/cli.py) exposes catalog validation, search, export, review, discovery, and verification commands. Network operations are explicit commands rather than import-time behavior.
- **Offline sample app:** [`examples/catalog_browser.py`](../../examples/catalog_browser.py) demonstrates the public `APIMind` interface.

## Bundled catalog snapshot

All four catalog files record `last_updated: 2026-11-12`:

| Data file | Records | Meaning |
| --- | ---: | --- |
| [`apis.json`](../../src/divyesh_api_mind/data/apis.json) | 26 | Curated API metadata and evidence references; not a live availability guarantee |
| [`models.json`](../../src/divyesh_api_mind/data/models.json) | 5 | Model metadata and access/terms notes; not hosted inference |
| [`datasets.json`](../../src/divyesh_api_mind/data/datasets.json) | 8 | Dataset access, rights, and update notes |
| [`mcp_registry.json`](../../src/divyesh_api_mind/data/mcp_registry.json) | 6 | Five `directory_entry`, one `reviewed_repository`, and zero `working_integration` records |

The 26 API entries span 19 categories. The package has no mandatory third-party runtime dependencies, supports Python 3.10+, and declares optional `test` and `discovery-yaml` extras in [`pyproject.toml`](../../pyproject.toml). Its metadata version `0.1.0` is not proof that a distribution was published.

## Boundaries

Catalog loading, local search, record inspection, export, and validation are offline. A catalog record's source review date does not mean its endpoint was tested. `FREE_*` labels summarize a documented tier and do not promise unlimited access, free compute, uptime, or commercial rights. The MCP entries are metadata only; the package does not launch or call servers.

The one-time HTTP observations are documented separately in [`live-probes.md`](../live-probes.md). They are not treated as evidence for unrelated discovery candidates. See [`security.md`](../security.md) for the current request and privacy boundaries.

## Evidence links

- [Catalog maintenance rules](../catalog-maintenance.md)
- [Configuration and explicit network operations](../configuration.md)
- [Connector surface](../connectors.md)
- [Test evidence](TEST_EVIDENCE.md)
- [Implementation timeline and history limitations](IMPLEMENTATION_TIMELINE.md)
