# Live API probe snapshot

This is a dated, one-time snapshot, not a standing uptime monitor or a promise of availability. Run `apimind health-check API_ID` to request a fresh check only when permitted by the provider's current policies.

At **2026-11-12 07:57 UTC**, one unauthenticated, read-only `GET` was made to each configured public metadata endpoint below. Transport settings were a 5-second timeout, zero retries, a 1 MiB response cap, and redirects refused. `APIMind` received an empty environment mapping, so no credential was sent. No response bodies were saved.

| Catalog ID | Host/path | HTTP status | Result | Checked at (UTC) |
| --- | --- | ---: | --- | --- |
| `github-rest` | `api.github.com/repos/public-apis/public-apis` | 200 | healthy | `2026-11-12T07:57:17.815735+00:00` |
| `pypi-json` | `pypi.org/pypi/pip/json` | 200 | healthy | `2026-11-12T07:57:18.570378+00:00` |
| `npm-registry` | `registry.npmjs.org/is-number` | 200 | healthy | `2026-11-12T07:57:18.840238+00:00` |

The timestamp/status records are also in `src/divyesh_api_mind/data/live_probe_results.json`. These probes confirm only that those read endpoints responded successfully at that time; they do not validate all API methods, data accuracy, terms, quotas, security, or continuing availability. The chosen paths are small public metadata reads. No call was made to an endpoint that sends messages, mutates data, incurs a known charge, or requires a key.
