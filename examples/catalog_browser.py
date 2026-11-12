"""Tiny offline-first API catalog browser example.

Run from the repository root with:
    PYTHONPATH=src python examples/catalog_browser.py --category research
A live health probe is never run unless --health-check API_ID is explicit.
"""

from __future__ import annotations

import argparse
import json

from divyesh_api_mind import APIMind


def main() -> int:
    parser = argparse.ArgumentParser(description="Browse DIVYESH API MIND locally")
    parser.add_argument("--category", help="exact API category to show")
    parser.add_argument("--capability", help="capability phrase to search")
    parser.add_argument("--free-status", help="one of the catalog free-status values")
    parser.add_argument("--no-auth", action="store_true", help="show APIs catalogued without authentication")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--health-check", metavar="API_ID", help="explicitly send one configured, read-only probe")
    args = parser.parse_args()

    mind = APIMind()
    records = mind.search(
        kind="api",
        category=args.category,
        capability=args.capability,
        free_access=args.free_status,
        no_auth=args.no_auth,
        limit=args.limit,
    )
    for item in records:
        print(f"{item['id']}: {item['name']} [{item['free_status']}]")
        print(f"  auth={item['authentication']['kind']} | {item['summary']}")

    if args.health_check:
        print(json.dumps(mind.health_check(args.health_check), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
