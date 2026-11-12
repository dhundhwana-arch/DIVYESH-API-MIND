# Example application

`catalog_browser.py` is a small offline-first command-line app using the public Python package interface. It demonstrates capability/category/free-status/no-auth search. It sends no network requests by default.

From the repository root:

```bash
PYTHONPATH=src python examples/catalog_browser.py --category research --limit 5
PYTHONPATH=src python examples/catalog_browser.py --capability "weather" --no-auth
```

A live probe is available only when explicitly requested, and only for a record with a configured safe health probe:

```bash
PYTHONPATH=src python examples/catalog_browser.py --health-check pypi-json
```

For installation and credential/transport settings, see [`../docs/configuration.md`](../docs/configuration.md).
