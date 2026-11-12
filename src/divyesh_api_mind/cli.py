"""Offline catalog, review-queue, and opt-in network operations CLI."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Sequence

from .catalog import APIMind
from .discovery import (
    combine_review_queues,
    import_api_atlas_jsonl,
    import_openapi_spec,
    import_public_apis_markdown,
    load_review_queue,
    read_discovery_source,
    search_review_queue,
)
from .exceptions import APIMindError
from .mcp import MCPRegistry
from .validation import STATUS_VALUES, validate_catalog_directory
from .verification import (
    FINDING_STAGE,
    TRANSITION_OUTCOMES,
    add_review_evidence,
    create_api_record_proposal,
    create_verification_batch,
    load_verification_batch,
    probe_review_endpoint,
    record_review_finding,
    save_verification_batch,
    transition_review_stage,
    validate_verification_batch,
)

_CATALOG_KINDS = ("apis", "models", "datasets", "mcp_registry")


def _data_directory(value: str | None) -> Path:
    return Path(value) if value else Path(__file__).resolve().parent / "data"


def _add_catalog_dir(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--catalog-dir",
        help="directory containing apis.json, models.json, datasets.json, and mcp_registry.json",
    )


def _json_print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def _print_validation(directory: Path) -> int:
    results = validate_catalog_directory(directory)
    failed = False
    for kind in _CATALOG_KINDS:
        errors = results[kind]
        if errors:
            failed = True
            print(f"{kind}: INVALID")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"{kind}: valid")
    for queue_path in sorted(directory.glob("*candidates.json")):
        try:
            queue = load_review_queue(queue_path)
        except APIMindError as exc:
            failed = True
            print(f"{queue_path.name}: INVALID")
            print(f"  - {exc}")
        else:
            print(f"{queue_path.name}: valid ({queue['counts']['unique_candidates']} review candidates; not promoted)")
    return 1 if failed else 0


def _stale_records(
    directory: Path, as_of: date, days: int, *, include_sources: bool = False
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for catalog_kind in _CATALOG_KINDS:
        document = json.loads((directory / f"{catalog_kind}.json").read_text(encoding="utf-8"))
        for record in document["records"]:
            verified_value = record.get("last_verified") or record.get("verified_on")
            verified = date.fromisoformat(verified_value)
            age_days = (as_of - verified).days
            if age_days >= days:
                item: dict[str, object] = {
                    "catalog": catalog_kind,
                    "id": record["id"],
                    "name": record["name"],
                    "last_verified": verified_value,
                    "age_days": age_days,
                }
                if include_sources:
                    item["sources"] = record.get("sources", [])
                result.append(item)
    return sorted(result, key=lambda item: (-int(item["age_days"]), str(item["catalog"]), str(item["id"])))


def _canonical_cli_date(value: str | None) -> date:
    try:
        parsed = date.fromisoformat(value) if value else date.today()
        if value and parsed.isoformat() != value:
            raise ValueError("date is not in canonical form")
        return parsed
    except ValueError:
        raise ValueError("date must be a valid YYYY-MM-DD value") from None


def _read_import_input(path: str | None, url: str | None) -> bytes:
    if url:
        return read_discovery_source(url)
    if not path:
        raise ValueError("provide exactly one of --input or --url")
    try:
        return Path(path).read_bytes()
    except OSError as exc:
        raise ValueError(f"could not read input file ({type(exc).__name__})") from None


def _read_json_document(path: str | Path) -> object:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read JSON file ({type(exc).__name__})") from None


def _check_verification_output_path(
    output: str | Path,
    catalog_dir: Path,
    *,
    forbidden_paths: Sequence[str | Path] = (),
) -> Path:
    target = Path(output).expanduser().resolve()
    protected_paths = {(catalog_dir / f"{kind}.json").resolve() for kind in _CATALOG_KINDS}
    protected_paths.update(path.resolve() for path in catalog_dir.glob("*candidates.json"))
    protected_paths.update(Path(path).expanduser().resolve() for path in forbidden_paths)
    if target in protected_paths:
        raise ValueError("verification batch output cannot overwrite an accepted catalog or discovery queue")
    return target


def _save_verification_batch(
    batch: object,
    output: str | Path,
    catalog_dir: Path,
    *,
    forbidden_paths: Sequence[str | Path] = (),
) -> Path:
    target = _check_verification_output_path(output, catalog_dir, forbidden_paths=forbidden_paths)
    return save_verification_batch(batch, target)


def _write_or_print(content: str, output: str | None) -> None:
    if not output or output == "-":
        sys.stdout.write(content)
        if content and not content.endswith("\n"):
            sys.stdout.write("\n")
        return
    Path(output).write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="apimind",
        description="Inspect local DIVYESH API MIND catalogs. Network use is explicit via docs --fetch, health-check, and discover-import --url.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="validate the four JSON catalogs offline")
    _add_catalog_dir(validate_parser)

    summary_parser = subparsers.add_parser("summary", help="show catalog and free-access counts")
    _add_catalog_dir(summary_parser)

    search_parser = subparsers.add_parser("search", help="search API, model, and dataset records")
    _add_catalog_dir(search_parser)
    search_parser.add_argument("--kind", choices=("api", "model", "dataset"))
    search_parser.add_argument("--category")
    search_parser.add_argument("--capability")
    search_parser.add_argument("--free-access", choices=sorted(STATUS_VALUES))
    search_parser.add_argument("--authentication", choices=("none", "no-auth", "required", "optional", "unknown"))
    search_parser.add_argument("--no-auth", action="store_true", help="only API records with explicitly catalogued no-auth access")
    search_parser.add_argument("--query")
    search_parser.add_argument("--limit", type=int)

    docs_parser = subparsers.add_parser("docs", help="list documentation references; --fetch explicitly retrieves one page")
    _add_catalog_dir(docs_parser)
    docs_parser.add_argument("record_id")
    docs_parser.add_argument("--fetch", action="store_true", help="make one bounded, unauthenticated HTTPS GET to a recorded source")
    docs_parser.add_argument("--source-index", type=int, default=0)
    docs_parser.add_argument("--max-bytes", type=int, default=512 * 1024)

    template_parser = subparsers.add_parser("template", help="generate a Python integration starter without making requests")
    _add_catalog_dir(template_parser)
    template_parser.add_argument("record_id")
    template_parser.add_argument("--language", choices=("python",), default="python")
    template_parser.add_argument("--output", help="write the template to a file instead of stdout")

    alternatives_parser = subparsers.add_parser("alternatives", help="suggest offline capability/category neighbors")
    _add_catalog_dir(alternatives_parser)
    alternatives_parser.add_argument("record_id")
    alternatives_parser.add_argument("--limit", type=int, default=5)

    health_parser = subparsers.add_parser("health-check", help="explicitly run configured read-only API health probes")
    _add_catalog_dir(health_parser)
    health_parser.add_argument("record_ids", nargs="+", help="one or more API ids; this command sends provider requests")

    export_parser = subparsers.add_parser("export", help="export selected records as JSON or CSV")
    _add_catalog_dir(export_parser)
    export_parser.add_argument("record_ids", nargs="+", help="explicit API/model/dataset ids to export")
    export_parser.add_argument("--format", choices=("json", "csv"), default="json")
    export_parser.add_argument("--output", help="write export to a file instead of stdout")

    stale_parser = subparsers.add_parser("stale", help="list records due for source re-verification")
    _add_catalog_dir(stale_parser)
    stale_parser.add_argument("--days", type=int, default=180, help="stale threshold in days (default: 180)")
    stale_parser.add_argument("--as-of", help="comparison date in YYYY-MM-DD form; defaults to today")

    review_parser = subparsers.add_parser(
        "review-plan", help="create a local source-review queue with evidence URLs"
    )
    _add_catalog_dir(review_parser)
    review_parser.add_argument("--days", type=int, default=180, help="stale threshold in days (default: 180)")
    review_parser.add_argument("--as-of", help="comparison date in YYYY-MM-DD form; defaults to today")

    discover_parser = subparsers.add_parser(
        "discover-import",
        help="import Public APIs Markdown, API Atlas JSONL, or an OpenAPI spec into an UNKNOWN human-review queue",
    )
    discover_parser.add_argument("--format", choices=("public-apis", "api-atlas", "openapi"), required=True)
    inputs = discover_parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--input", help="local Markdown/JSON/JSONL/YAML file")
    inputs.add_argument("--url", help="fetch one public HTTPS source; redirects and credentials are refused")
    discover_parser.add_argument("--source-url", help="canonical source URL for local imports; defaults to --url")
    discover_parser.add_argument("--revision", help="Git commit hash for directory source attribution (required for Public APIs and API Atlas)")
    discover_parser.add_argument("--checked-on", help="source review date in YYYY-MM-DD form; defaults to today")
    discover_parser.add_argument("--catalog-dir", help="catalog directory used only to flag possible duplicate records")
    discover_parser.add_argument("--output", help="write review queue JSON to a file instead of stdout")

    candidates_parser = subparsers.add_parser("review-candidates", help="browse unverified discovery candidates")
    candidates_parser.add_argument(
        "--queue", help="review queue JSON path (default: bundled discovery_candidates.json)"
    )
    candidates_parser.add_argument("--category")
    candidates_parser.add_argument("--query")
    candidates_parser.add_argument("--priority", choices=("upstream_checked_pointer", "unverified_directory_pointer"))
    candidates_parser.add_argument("--limit", type=int)

    merge_parser = subparsers.add_parser("review-merge", help="merge discovery queues while preserving provenance and deduplicating exact leads")
    merge_parser.add_argument("inputs", nargs="+", help="input review-queue JSON files")
    merge_parser.add_argument("--output", help="write merged queue JSON to a file instead of stdout")

    verify_create = subparsers.add_parser("verify-create", help="rank candidates and create a non-promoting evidence-review batch")
    verify_create.add_argument("--queue", help="discovery queue JSON path (default: bundled discovery_candidates.json)")
    verify_create.add_argument("--limit", type=int, default=100, help="maximum candidates to select (default: 100)")
    verify_create.add_argument("--as-of", help="ranking and creation date in YYYY-MM-DD form")
    verify_create.add_argument("--output", required=True, help="new or existing verification-batch JSON path")

    verify_validate = subparsers.add_parser("verify-validate", help="validate a saved batch and print actual review counts")
    verify_validate.add_argument("batch", help="verification-batch JSON path")

    verify_evidence = subparsers.add_parser("verify-add-evidence", help="append one manually reviewed evidence record without fetching its URL")
    verify_evidence.add_argument("batch")
    verify_evidence.add_argument("candidate_id")
    verify_evidence.add_argument("--evidence", required=True, help="JSON file containing one evidence record")
    verify_evidence.add_argument("--reviewer", required=True)
    verify_evidence.add_argument("--recorded-on")
    verify_evidence.add_argument("--output", required=True, help="write the updated batch to this path")

    verify_finding = subparsers.add_parser("verify-finding", help="record a typed, evidence-linked finding in the active workflow stage")
    verify_finding.add_argument("batch")
    verify_finding.add_argument("candidate_id")
    verify_finding.add_argument("field", choices=sorted(FINDING_STAGE))
    verify_finding.add_argument("--value-json", required=True, help="JSON scalar/object value; UNKNOWN stays unresolved")
    verify_finding.add_argument("--status", choices=("verified", "inconclusive", "unknown"), required=True)
    verify_finding.add_argument("--evidence-id", action="append", default=[])
    verify_finding.add_argument("--reviewer", required=True)
    verify_finding.add_argument("--notes", required=True)
    verify_finding.add_argument("--confidence", type=float, required=True)
    verify_finding.add_argument("--observed-on")
    verify_finding.add_argument("--output", required=True)

    verify_transition = subparsers.add_parser("verify-transition", help="append a guarded stage transition; human approval is explicit")
    _add_catalog_dir(verify_transition)
    verify_transition.add_argument("batch")
    verify_transition.add_argument("candidate_id")
    verify_transition.add_argument("--outcome", choices=sorted(TRANSITION_OUTCOMES), required=True)
    verify_transition.add_argument("--reviewer", required=True)
    verify_transition.add_argument("--notes", required=True)
    verify_transition.add_argument("--recorded-on")
    verify_transition.add_argument("--evidence-id", action="append", default=[])
    verify_transition.add_argument("--reviewer-role", choices=("reviewer", "human", "system"), default="reviewer")
    verify_transition.add_argument("--decision", choices=("approved", "rejected", "accepted"))
    verify_transition.add_argument("--catalog-entry-id")
    verify_transition.add_argument("--catalog-entry-sha256")
    verify_transition.add_argument("--output", required=True)

    verify_probe = subparsers.add_parser("verify-probe", help="explicitly run one permitted, unauthenticated read-only HTTPS endpoint probe")
    verify_probe.add_argument("batch")
    verify_probe.add_argument("candidate_id")
    verify_probe.add_argument("--url", required=True, help="exact endpoint URL published in reviewed provider docs; no query string")
    verify_probe.add_argument("--permission-evidence-id", required=True)
    verify_probe.add_argument("--method", choices=("GET", "HEAD"), default="GET")
    verify_probe.add_argument("--reviewer", required=True)
    verify_probe.add_argument("--observed-on")
    verify_probe.add_argument("--timeout-seconds", type=float, default=5.0)
    verify_probe.add_argument("--max-response-bytes", type=int, default=65536)
    verify_probe.add_argument("--output", required=True)

    verify_propose = subparsers.add_parser("verify-propose", help="store a validated API record draft for human approval; never edits a catalog")
    _add_catalog_dir(verify_propose)
    verify_propose.add_argument("batch")
    verify_propose.add_argument("candidate_id")
    verify_propose.add_argument("--record", required=True, help="JSON file containing a proposed API catalog record")
    verify_propose.add_argument("--reviewer", required=True)
    verify_propose.add_argument("--created-on")
    verify_propose.add_argument("--output", required=True)

    mcp_parser = subparsers.add_parser("mcp", help="browse MCP directory metadata only")
    _add_catalog_dir(mcp_parser)
    mcp_parser.add_argument("--status", choices=("directory_entry", "reviewed_repository", "working_integration"))
    mcp_parser.add_argument("--query")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point. Network commands are always explicit subcommands/flags."""
    parser = build_parser()
    args = parser.parse_args(argv)
    directory = _data_directory(getattr(args, "catalog_dir", None))

    try:
        if args.command == "validate":
            return _print_validation(directory)
        if args.command == "summary":
            mind = APIMind(catalog_dir=directory)
            registry = MCPRegistry(directory / "mcp_registry.json")
            result = {
                "catalogs": mind.counts,
                "free_status_counts": mind.free_status_counts(),
                "mcp_records": len(registry.list()),
                "mcp_evidence_counts": registry.counts(),
            }
            candidate_counts = {}
            for candidate_path in sorted(directory.glob("*candidates.json")):
                candidate_counts[candidate_path.name] = load_review_queue(candidate_path)["counts"]
            if candidate_counts:
                result["discovery_candidates"] = candidate_counts
            _json_print(result)
            return 0
        if args.command == "search":
            mind = APIMind(catalog_dir=directory)
            _json_print(
                mind.search(
                    kind=args.kind,
                    category=args.category,
                    capability=args.capability,
                    free_access=args.free_access,
                    authentication=args.authentication,
                    no_auth=args.no_auth,
                    query=args.query,
                    limit=args.limit,
                )
            )
            return 0
        if args.command == "docs":
            mind = APIMind(catalog_dir=directory)
            if args.fetch:
                _json_print(
                    mind.fetch_docs(args.record_id, source_index=args.source_index, max_bytes=args.max_bytes)
                )
            else:
                _json_print(mind.get_docs(args.record_id))
            return 0
        if args.command == "template":
            mind = APIMind(catalog_dir=directory)
            _write_or_print(mind.integration_template(args.record_id, language=args.language), args.output)
            return 0
        if args.command == "alternatives":
            mind = APIMind(catalog_dir=directory)
            _json_print(mind.alternatives(args.record_id, limit=args.limit))
            return 0
        if args.command == "health-check":
            mind = APIMind(catalog_dir=directory)
            results = [mind.health_check(record_id) for record_id in args.record_ids]
            _json_print(results)
            return 1 if any(result["status"] != "healthy" for result in results) else 0
        if args.command == "export":
            mind = APIMind(catalog_dir=directory)
            _write_or_print(mind.export_records(args.record_ids, format=args.format), args.output)
            return 0
        if args.command in {"stale", "review-plan"}:
            if args.days < 0:
                parser.error("--days must be non-negative")
            try:
                as_of = _canonical_cli_date(args.as_of)
            except ValueError as exc:
                parser.error(str(exc))
            validation = validate_catalog_directory(directory)
            if any(validation.values()):
                _print_validation(directory)
                return 1
            _json_print(
                _stale_records(
                    directory,
                    as_of,
                    args.days,
                    include_sources=args.command == "review-plan",
                )
            )
            return 0
        if args.command == "discover-import":
            try:
                checked_on = _canonical_cli_date(args.checked_on)
            except ValueError as exc:
                parser.error(str(exc))
            source_url = args.source_url or args.url
            if not source_url:
                parser.error("local imports require --source-url")
            raw = _read_import_input(args.input, args.url)
            existing = APIMind(catalog_dir=args.catalog_dir).search(kind="api") if args.catalog_dir else []
            if args.format == "public-apis":
                if not args.revision:
                    parser.error("--revision is required for Public APIs imports")
                queue = import_public_apis_markdown(
                    raw.decode("utf-8"),
                    source_url=source_url,
                    revision=args.revision,
                    checked_on=checked_on,
                    existing_records=existing,
                )
            elif args.format == "api-atlas":
                if not args.revision:
                    parser.error("--revision is required for API Atlas imports")
                queue = import_api_atlas_jsonl(
                    raw,
                    source_url=source_url,
                    revision=args.revision,
                    checked_on=checked_on,
                    existing_records=existing,
                )
            else:
                queue = import_openapi_spec(
                    raw,
                    source_url=source_url,
                    checked_on=checked_on,
                    existing_records=existing,
                )
            _write_or_print(json.dumps(queue, ensure_ascii=False, indent=2, sort_keys=True) + "\n", args.output)
            return 0
        if args.command == "review-candidates":
            queue_path = Path(args.queue) if args.queue else Path(__file__).resolve().parent / "data" / "discovery_candidates.json"
            queue = load_review_queue(queue_path)
            _json_print(
                {
                    "source": queue.get("source"),
                    "counts": queue.get("counts"),
                    "candidates": search_review_queue(
                        queue, category=args.category, query=args.query, priority=args.priority, limit=args.limit
                    ),
                }
            )
            return 0
        if args.command == "review-merge":
            queues = [load_review_queue(path) for path in args.inputs]
            queue = combine_review_queues(queues)
            _write_or_print(json.dumps(queue, ensure_ascii=False, indent=2, sort_keys=True) + "\n", args.output)
            return 0
        if args.command == "verify-create":
            queue_path = Path(args.queue) if args.queue else Path(__file__).resolve().parent / "data" / "discovery_candidates.json"
            if queue_path.expanduser().resolve() == Path(args.output).expanduser().resolve():
                raise ValueError("verification batch output must not overwrite its discovery queue")
            queue = load_review_queue(queue_path)
            try:
                as_of = _canonical_cli_date(args.as_of)
            except ValueError as exc:
                parser.error(str(exc))
            batch = create_verification_batch(queue, limit=args.limit, generated_on=as_of)
            saved = _save_verification_batch(batch, args.output, directory)
            _json_print({"batch_id": batch["batch_id"], "output": str(saved), "summary": batch["summary"]})
            return 0
        if args.command == "verify-validate":
            batch = load_verification_batch(args.batch)
            _json_print({"valid": True, "batch_id": batch["batch_id"], "summary": batch["summary"]})
            return 0
        if args.command == "verify-add-evidence":
            batch = load_verification_batch(args.batch)
            evidence = _read_json_document(args.evidence)
            when = _canonical_cli_date(args.recorded_on) if args.recorded_on else None
            updated = add_review_evidence(batch, args.candidate_id, evidence, reviewer=args.reviewer, recorded_on=when)
            saved = _save_verification_batch(updated, args.output, directory)
            _json_print({"batch_id": updated["batch_id"], "output": str(saved), "summary": updated["summary"]})
            return 0
        if args.command == "verify-finding":
            batch = load_verification_batch(args.batch)
            try:
                value = json.loads(args.value_json)
            except json.JSONDecodeError as exc:
                raise ValueError(f"--value-json is invalid JSON ({type(exc).__name__})") from None
            when = _canonical_cli_date(args.observed_on) if args.observed_on else None
            updated = record_review_finding(
                batch, args.candidate_id, args.field, value, status=args.status,
                evidence_ids=args.evidence_id, reviewer=args.reviewer, notes=args.notes,
                confidence=args.confidence, observed_on=when,
            )
            saved = _save_verification_batch(updated, args.output, directory)
            _json_print({"batch_id": updated["batch_id"], "output": str(saved), "summary": updated["summary"]})
            return 0
        if args.command == "verify-transition":
            batch = load_verification_batch(args.batch)
            when = _canonical_cli_date(args.recorded_on) if args.recorded_on else None
            accepted_record = None
            if args.decision == "accepted":
                if args.outcome != "completed" or not args.catalog_entry_id or not args.catalog_entry_sha256:
                    raise ValueError("catalog acceptance requires completed outcome, catalog entry ID, and SHA-256")
                api_records = APIMind(catalog_dir=directory).search(kind="api")
                accepted_record = next((item for item in api_records if item.get("id") == args.catalog_entry_id), None)
                if accepted_record is None:
                    raise ValueError("the accepted API record must already exist in the selected catalog")
                canonical = json.dumps(accepted_record, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
                actual_digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
                if actual_digest != args.catalog_entry_sha256.casefold():
                    raise ValueError("catalog entry SHA-256 does not match the existing catalog record")
            updated = transition_review_stage(
                batch, args.candidate_id, outcome=args.outcome, reviewer=args.reviewer,
                notes=args.notes, recorded_on=when, evidence_ids=args.evidence_id,
                reviewer_role=args.reviewer_role, decision=args.decision,
                catalog_entry_id=args.catalog_entry_id, catalog_entry_sha256=args.catalog_entry_sha256,
                catalog_record=accepted_record,
            )
            saved = _save_verification_batch(updated, args.output, directory)
            _json_print({"batch_id": updated["batch_id"], "output": str(saved), "summary": updated["summary"]})
            return 0
        if args.command == "verify-probe":
            batch = load_verification_batch(args.batch)
            _check_verification_output_path(args.output, directory)
            when = _canonical_cli_date(args.observed_on) if args.observed_on else None
            updated = probe_review_endpoint(
                batch, args.candidate_id, args.url,
                permission_evidence_id=args.permission_evidence_id, reviewer=args.reviewer,
                request_method=args.method, observed_on=when,
                timeout_seconds=args.timeout_seconds, max_response_bytes=args.max_response_bytes,
            )
            saved = _save_verification_batch(updated, args.output, directory)
            _json_print({"batch_id": updated["batch_id"], "output": str(saved), "summary": updated["summary"]})
            return 0
        if args.command == "verify-propose":
            batch = load_verification_batch(args.batch)
            record = _read_json_document(args.record)
            existing_ids = [item["id"] for item in APIMind(catalog_dir=directory).search(kind="api")]
            when = _canonical_cli_date(args.created_on) if args.created_on else None
            updated = create_api_record_proposal(
                batch, args.candidate_id, record, reviewer=args.reviewer,
                created_on=when, existing_ids=existing_ids,
            )
            saved = _save_verification_batch(updated, args.output, directory)
            _json_print({"batch_id": updated["batch_id"], "output": str(saved), "summary": updated["summary"]})
            return 0
        if args.command == "mcp":
            registry = MCPRegistry(directory / "mcp_registry.json")
            _json_print(registry.list(status=args.status, query=args.query))
            return 0
    except (APIMindError, OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"apimind: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    return 2
