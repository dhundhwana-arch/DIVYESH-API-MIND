from __future__ import annotations

import io
import json
import os
import shutil
import stat
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

import pytest

from divyesh_api_mind import (
    APIMind,
    IntelligenceHub,
    KeyVault,
    LocalRuntimeError,
    OllamaLocalClient,
    ResearchError,
    TechnologyResearchPipeline,
    VaultError,
    append_research_review_event,
    create_github_discovery_record,
    detect_hardware,
    estimate_model_memory,
    merge_discovery_records,
    new_research_review_ledger,
    validate_research_review_ledger,
    validate_technology_discovery,
)
from divyesh_api_mind import cli
from divyesh_api_mind.research import canonical_sha256

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "src" / "divyesh_api_mind" / "data"


def github_payload(
    repo: str = "example-org/example-tool",
    *,
    updated_at: str = "2026-11-10T12:00:00Z",
    description: str | None = "A test repository",
) -> dict[str, object]:
    owner, name = repo.split("/", 1)
    return {
        "full_name": repo,
        "owner": {"login": owner},
        "html_url": f"https://github.com/{repo}",
        "description": description,
        "homepage": None,
        "topics": ["ai", "research"],
        "default_branch": "main",
        "language": "Python",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": updated_at,
        "pushed_at": updated_at,
        "archived": False,
        "disabled": False,
        "license": {"key": "mit", "name": "MIT License", "spdx_id": "MIT", "url": None},
        "stargazers_count": 42,
        "forks_count": 4,
        "subscribers_count": 3,
        "size": 123,
    }


def target(repo: str = "example-org/example-tool") -> dict[str, object]:
    return {
        "repo": repo,
        "kind": "software_tool",
        "categories": ["ai", "research"],
        "capabilities": ["document search", "summarization"],
    }


def discovery_document() -> dict[str, object]:
    lead = create_github_discovery_record(
        target(), checked_on="2026-11-12", payload=github_payload()
    )
    return merge_discovery_records(None, [lead], checked_on="2026-11-12")


def copy_catalogs(destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    for filename in ("apis.json", "models.json", "datasets.json", "mcp_registry.json"):
        shutil.copy2(DATA_DIR / filename, destination / filename)
    return destination


def test_github_target_file_reader_enforces_size_limit(tmp_path: Path) -> None:
    from divyesh_api_mind.research import load_github_targets

    path = tmp_path / "targets.json"
    path.write_bytes(b"x" * (256 * 1024 + 1))
    with pytest.raises(ResearchError, match="exceeds"):
        load_github_targets(path)


def test_github_discovery_is_unknown_separate_and_hashes_source_snapshot() -> None:
    record = create_github_discovery_record(
        target(), checked_on="2026-11-12", payload=github_payload()
    )
    assert record["accepted"] is False
    assert record["research_stage"] == "discovery"
    assert record["free_status"] == "UNKNOWN"
    assert record["api_key_required"] == "UNKNOWN"
    assert record["maintenance_status"] == "UNKNOWN"
    assert record["python_sdk_status"] == "UNKNOWN"
    assert record["commercial_use_status"] == "UNKNOWN"
    assert record["evidence"][0]["snapshot_sha256"] == canonical_sha256(record["evidence"][0]["snapshot"])
    assert validate_technology_discovery(merge_discovery_records(None, [record], checked_on="2026-11-12")) == []


def test_github_discovery_rejects_identity_and_unsafe_repository_urls() -> None:
    payload = github_payload()
    payload["full_name"] = "attacker/other"
    with pytest.raises(ResearchError, match="identity"):
        create_github_discovery_record(target(), checked_on="2026-11-12", payload=payload)

    payload = github_payload()
    payload["html_url"] = "https://user@github.com/example-org/example-tool"
    with pytest.raises(ResearchError, match="unsafe"):
        create_github_discovery_record(target(), checked_on="2026-11-12", payload=payload)


def test_github_discovery_rejects_secret_and_invalid_checked_date() -> None:
    payload = github_payload(description="Bearer abcdefghijklmnopqrstuvwxyz123456")
    with pytest.raises(ResearchError, match="credential"):
        create_github_discovery_record(target(), checked_on="2026-11-12", payload=payload)
    with pytest.raises(ResearchError, match="YYYY-MM-DD"):
        create_github_discovery_record(target(), checked_on="2026-02-30", payload=github_payload())


def test_github_metadata_fetch_is_allowlisted_unproxied_and_mocked() -> None:
    from divyesh_api_mind.research import _NoRedirect, _github_metadata

    class Response(io.BytesIO):
        def geturl(self) -> str:
            return "https://api.github.com/repos/example-org/example-tool"

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.close()
            return False

    opener = FakeOpener(Response(json.dumps(github_payload()).encode()))
    captured: dict[str, object] = {}

    def build_opener(*handlers):
        captured["handlers"] = handlers
        return opener

    with patch("divyesh_api_mind.research.urllib.request.build_opener", side_effect=build_opener):
        result = _github_metadata("example-org/example-tool", timeout=2.5)
    request, timeout = opener.requests[0]
    handlers = captured["handlers"]
    assert result["full_name"] == "example-org/example-tool"
    assert request.full_url == "https://api.github.com/repos/example-org/example-tool"
    assert timeout == 2.5
    assert "Authorization" not in request.headers
    assert any(isinstance(item, urllib.request.ProxyHandler) and item.proxies == {} for item in handlers)
    assert any(isinstance(item, _NoRedirect) for item in handlers)


def test_pipeline_is_mockable_append_only_and_idempotent() -> None:
    calls: list[str] = []
    pipeline = TechnologyResearchPipeline(timeout=1)

    def fetch(repo: str) -> dict[str, object]:
        calls.append(repo)
        return github_payload(updated_at=f"2026-11-{10 + len(calls):02d}T12:00:00Z")

    first, errors = pipeline.discover_github_targets(
        [target()], checked_on="2026-11-12", fetcher=fetch
    )
    assert errors == []
    assert len(first["records"]) == 1
    assert len(first["records"][0]["evidence"]) == 1

    second, errors = pipeline.discover_github_targets(
        [target()], checked_on="2026-11-13", existing=first, fetcher=fetch
    )
    assert errors == []
    assert len(second["records"][0]["evidence"]) == 2
    assert second["records"][0]["evidence_refs"] == [e["evidence_id"] for e in second["records"][0]["evidence"]]
    assert second["records"][0]["last_checked"] == "2026-11-13"
    assert second["records"][0]["accepted"] is False
    assert len(calls) == 2

    backdated, errors = pipeline.discover_github_targets(
        [target()], checked_on="2026-11-11", existing=second, fetcher=fetch
    )
    assert errors == []
    assert len(backdated["records"][0]["evidence"]) == 3
    assert backdated["records"][0]["last_checked"] == "2026-11-13"
    assert backdated["last_updated"] == "2026-11-13"

    duplicate, errors = pipeline.discover_github_targets(
        [target()], checked_on="2026-11-11", existing=backdated,
        fetcher=lambda _repo: github_payload(updated_at="2026-11-13T12:00:00Z"),
    )
    assert errors == []
    assert duplicate == backdated


def test_pipeline_skips_bad_targets_without_fetching_them_and_caps_targets() -> None:
    calls: list[str] = []
    pipeline = TechnologyResearchPipeline()
    document, errors = pipeline.discover_github_targets(
        [{"repo": "../invalid"}, target()],
        checked_on="2026-11-12",
        fetcher=lambda repo: calls.append(repo) or github_payload(repo),
    )
    assert len(document["records"]) == 1
    assert len(errors) == 1
    assert calls == ["example-org/example-tool"]
    with pytest.raises(ResearchError, match="at most 25"):
        pipeline.discover_github_targets([target()] * 26, checked_on="2026-11-12", fetcher=lambda _repo: {})
    with pytest.raises(ValueError, match="timeout"):
        TechnologyResearchPipeline(timeout=float("nan"))


def test_loader_validates_target_file_and_deduplicates(tmp_path: Path) -> None:
    path = tmp_path / "targets.json"
    path.write_text(json.dumps({"schema_version": "1.0", "targets": [target(), target()]}))
    with pytest.raises(ResearchError, match="duplicate"):
        from divyesh_api_mind.research import load_github_targets

        load_github_targets(path)


def test_validator_handles_malicious_types_without_raising() -> None:
    bad = {
        "schema_version": "1.0",
        "catalog_role": "discovery_only",
        "policy": {"automatic_catalog_promotion": False, "candidate_endpoint_calls": False},
        "records": [{"id": "bad-record", "free_status": [], "unlimited_status": {}, "evidence": [], "evidence_refs": []}],
    }
    errors = validate_technology_discovery(bad)
    assert errors
    assert any("free_status" in error for error in errors)


def test_manual_evidence_appends_without_changing_claim_or_review_state() -> None:
    document = discovery_document()
    record = document["records"][0]
    state_before = {key: record[key] for key in ("accepted", "free_status", "human_review_status", "proposal_status", "last_checked")}
    updated = TechnologyResearchPipeline.append_evidence(
        record,
        evidence_type="official_pricing_documentation",
        source_url="https://provider.example/pricing#limits",
        checked_on="2026-11-12",
        claims_supported=["The linked official pricing page states the listed plan conditions."],
        snapshot={"visible_pricing_text": "The plan includes a documented monthly quota."},
        primary_source=True,
    )
    assert len(updated["evidence"]) == 2
    assert updated["evidence_refs"][-1] == updated["evidence"][-1]["evidence_id"]
    assert {key: updated[key] for key in state_before} == state_before
    assert validate_technology_discovery(merge_discovery_records(None, [updated], checked_on="2026-11-12")) == []


def test_manual_evidence_rejects_credentials_query_and_noncanonical_snapshots() -> None:
    record = discovery_document()["records"][0]
    kwargs = dict(
        evidence_type="official_provider_documentation",
        source_url="https://provider.example/docs",
        checked_on="2026-11-12",
        claims_supported=["The public documentation states this claim."],
        snapshot={"excerpt": "safe"},
        primary_source=True,
    )
    bad_query = {**kwargs, "source_url": "https://provider.example/docs?api_key=abcdefghijklmnopqrstuvwxyz123456"}
    with pytest.raises(ResearchError, match="HTTPS"):
        TechnologyResearchPipeline.append_evidence(record, **bad_query)
    bad_secret = {**kwargs, "snapshot": {"token": "sk-abcdefghijklmnopqrstuvwxyz123456"}}
    with pytest.raises(ResearchError, match="credential"):
        TechnologyResearchPipeline.append_evidence(record, **bad_secret)
    bad_number = {**kwargs, "snapshot": {"value": float("nan")}}
    with pytest.raises(ResearchError, match="canonical JSON"):
        TechnologyResearchPipeline.append_evidence(record, **bad_number)


def test_claim_normalization_requires_evidence_and_human_reviewer() -> None:
    with pytest.raises(ResearchError, match="named reviewer"):
        TechnologyResearchPipeline.normalize_claim(
            field="free_status", raw_value="Free", normalized_value="FREE_NO_KEY",
            evidence_refs=["evidence-001"], confidence=0.9, disposition="HUMAN_REVIEWED",
        )
    claim = TechnologyResearchPipeline.normalize_claim(
        field="free_status", raw_value="Free, subject to a cap", normalized_value="FREE_TIER_LIMITED",
        evidence_refs=["evidence-001"], confidence=0.72, reviewer="Reviewer A", disposition="HUMAN_REVIEWED",
    )
    assert claim["disposition"] == "HUMAN_REVIEWED"
    assert claim["normalized_value"] == "FREE_TIER_LIMITED"
    with pytest.raises(ResearchError, match="finite"):
        TechnologyResearchPipeline.normalize_claim(
            field="free_status", raw_value="unknown", normalized_value="UNKNOWN",
            evidence_refs=["evidence-001"], confidence=float("nan"),
        )


def test_research_review_ledger_is_append_only_hash_linked_and_never_promotes() -> None:
    discovery = discovery_document()
    record = discovery["records"][0]
    ledger = new_research_review_ledger()
    ledger = append_research_review_event(
        ledger,
        discovery_document=discovery,
        record_id=record["id"],
        field="python_sdk_status",
        raw_value="Python SDK is mentioned in the readme",
        normalized_value="UNKNOWN",
        decision="INSUFFICIENT",
        evidence_refs=[record["evidence_refs"][0]],
        reviewer="Researcher A",
        notes="Repository metadata/readme did not establish provider-maintained SDK support.",
        confidence=0.4,
        recorded_on="2026-11-12",
    )
    ledger = append_research_review_event(
        ledger,
        discovery_document=discovery,
        record_id=record["id"],
        field="free_status",
        raw_value="No pricing source was checked",
        normalized_value="UNKNOWN",
        decision="INSUFFICIENT",
        evidence_refs=[record["evidence_refs"][0]],
        reviewer="Researcher B",
        notes="No provider pricing documentation was supplied.",
        confidence=0.2,
        recorded_on="2026-11-13",
    )
    assert validate_research_review_ledger(ledger) == []
    assert len(ledger["events"]) == 2
    assert ledger["events"][1]["previous_event_sha256"] == ledger["events"][0]["event_sha256"]
    assert ledger["events"][0]["automatic_catalog_promotion"] is False
    assert record["free_status"] == "UNKNOWN"
    assert record["accepted"] is False

    tampered = json.loads(json.dumps(ledger))
    tampered["events"][0]["notes"] += " changed"
    assert any("event_sha256" in error for error in validate_research_review_ledger(tampered))


def test_research_review_rejects_unrelated_evidence_and_wrong_decision() -> None:
    discovery = discovery_document()
    record = discovery["records"][0]
    arguments = dict(
        discovery_document=discovery,
        record_id=record["id"],
        field="license_status",
        raw_value="unknown",
        normalized_value="UNKNOWN",
        decision="INSUFFICIENT",
        evidence_refs=["evidence-not-from-this-record"],
        reviewer="Researcher",
        notes="The evidence is not tied to this lead.",
        confidence=0.1,
        recorded_on="2026-11-12",
    )
    with pytest.raises(ResearchError, match="belong to this discovery record"):
        append_research_review_event(None, **arguments)
    arguments["evidence_refs"] = record["evidence_refs"]
    arguments["decision"] = "ACCEPTED"
    with pytest.raises(ResearchError, match="decision"):
        append_research_review_event(None, **arguments)


def test_intelligence_hub_search_compare_recommend_and_explain_offline() -> None:
    hub = IntelligenceHub(catalog_dir=DATA_DIR, include_discovery=False)
    assert hub.counts == {"apis": 26, "models": 5, "datasets": 8, "mcp_metadata": 6, "technology_discovery_only": 0}
    api_results = hub.search(kind="api", capability="scholarly", record_state="ACCEPTED_CATALOG")
    assert api_results
    openalex = next(item for item in api_results if item["id"] == "openalex")
    assert openalex["keyless"] == "YES"
    assert all(item["record_state"] == "ACCEPTED_CATALOG" for item in api_results)
    assert all(item["record_origin"] == "accepted_catalog" for item in api_results)

    compared = hub.compare([api_results[0]["id"], "official-mcp-registry"])
    assert compared["records"][0]["record_state"] == "ACCEPTED_CATALOG"
    assert compared["records"][1]["record_state"] == "MCP_METADATA"
    with pytest.raises(ValueError, match="unique"):
        hub.compare([api_results[0]["id"], api_results[0]["id"]])

    recommendations = hub.recommend(capability="scholarly")
    assert recommendations
    assert recommendations[0]["why_ranked"]
    assert recommendations[0]["automatic_fallback"] is False
    assert recommendations[0]["no_live_availability_check"] is True
    explanation = hub.explain(recommendations[:2])
    assert "documentary only" in explanation
    assert "not an accepted" not in explanation.lower() or "accepted" in explanation.lower()


def test_intelligence_capability_matching_avoids_substring_false_positives() -> None:
    hub = IntelligenceHub(catalog_dir=DATA_DIR, include_discovery=False)
    results = hub.search(capability="coding")
    assert results
    assert all(record["id"] != "nominatim" for record in results)


def test_intelligence_unknown_values_never_match_negative_filters() -> None:
    unknown = {
        "id": "unknown-tool",
        "name": "Unknown Tool",
        "type": "api",
        "provider": "Example",
        "categories": ["ai"],
        "capabilities": ["summarization"],
        "free_status": "UNKNOWN",
        "authentication": {"kind": "unknown", "required": False, "verified": False},
        "usage_limits": {"requests_per_day": "UNKNOWN"},
    }
    from divyesh_api_mind.intelligence import IntelligenceHub as Hub

    normalized = Hub._normalize(unknown, "accepted_catalog")
    assert normalized["api_key_required"] == "UNKNOWN"
    assert normalized["keyless"] == "UNKNOWN"
    assert normalized["unlimited_status"] == "UNKNOWN"
    assert normalized["open_source_status"] == "UNKNOWN"
    assert normalized["commercial_use_status"] == "UNKNOWN"


def test_intelligence_hub_labels_discovery_records_separately(tmp_path: Path) -> None:
    discovery_path = tmp_path / "technology_discovery.json"
    discovery_path.write_text(json.dumps(discovery_document()))
    hub = IntelligenceHub(catalog_dir=DATA_DIR, discovery_path=discovery_path)
    results = hub.search(record_state="DISCOVERY_ONLY", query="example-tool")
    assert len(results) == 1
    assert results[0]["free_status"] == "UNKNOWN"
    assert "not an accepted" in " ".join(results[0]["limitations"]).lower()
    assert hub.counts["technology_discovery_only"] == 1


def test_intelligence_filters_reject_invalid_arguments_and_unhashable_catalog_values() -> None:
    hub = IntelligenceHub(catalog_dir=DATA_DIR, include_discovery=False)
    with pytest.raises(ValueError, match="free_status"):
        hub.search(free_status=[])
    with pytest.raises(ValueError, match="include_discovery"):
        hub.search(include_discovery="yes")
    with pytest.raises(ValueError, match="access"):
        hub.search(access="free-ish")


def test_intelligence_recommendation_unknown_access_does_not_appear_free() -> None:
    hub = IntelligenceHub(catalog_dir=DATA_DIR, include_discovery=False)
    recommendations = hub.recommend(capability="coding")
    for item in recommendations:
        if item["free_status"] in {"UNKNOWN", "PAID"}:
            assert "not ranked as free" in " ".join(item["why_ranked"])


def test_hardware_inventory_and_memory_estimate_are_offline_and_conservative() -> None:
    with patch("divyesh_api_mind.local_ai._memory_bytes", return_value=16 * 1024**3), patch(
        "divyesh_api_mind.local_ai.shutil.disk_usage", return_value=type("Disk", (), {"free": 100 * 1024**3})()
    ):
        profile = detect_hardware(disk_path="/ignored-in-test")
    assert profile["network_used"] is False
    assert profile["gpu_or_accelerator"].startswith("UNKNOWN")
    estimate = estimate_model_memory(8, profile=profile)
    assert estimate["status"] == "POSSIBLE_BUT_UNVERIFIED"
    assert "not a benchmark" in estimate["confidence"]
    with pytest.raises(ValueError, match="positive"):
        estimate_model_memory(float("nan"), profile=profile)


def test_ollama_client_restricts_origin_and_never_uses_hosted_fallback() -> None:
    for url in (
        "https://127.0.0.1:11434",
        "http://192.0.2.1:11434",
        "http://localhost:11434",
        "http://127.0.0.1:11434@evil.example",
        "http://127.0.0.1:9999",
    ):
        with pytest.raises(ValueError):
            OllamaLocalClient(url)
    with pytest.raises(ValueError, match="timeout"):
        OllamaLocalClient(timeout=float("nan"))


class FakeResponse(io.BytesIO):
    def __init__(self, payload: bytes, url: str = "http://127.0.0.1:11434/api/tags") -> None:
        super().__init__(payload)
        self._url = url

    def geturl(self) -> str:
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()
        return False


class FakeOpener:
    def __init__(self, response=None, error=None) -> None:
        self.response = response
        self.error = error
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        if self.error:
            raise self.error
        return self.response


def test_ollama_client_sends_only_bounded_loopback_get_and_post() -> None:
    opener = FakeOpener(FakeResponse(b'{"models":[{"name":"local-model"}]}'))
    with patch("divyesh_api_mind.local_ai.urllib.request.build_opener", return_value=opener):
        client = OllamaLocalClient()
        models = client.list_models()
    assert models[0]["name"] == "local-model"
    request, timeout = opener.requests[-1]
    assert request.full_url == "http://127.0.0.1:11434/api/tags"
    assert timeout == 30.0
    assert request.get_method() == "GET"

    opener = FakeOpener(FakeResponse(b'{"message":{"content":"local reply"}}', "http://127.0.0.1:11434/api/chat"))
    with patch("divyesh_api_mind.local_ai.urllib.request.build_opener", return_value=opener):
        result = OllamaLocalClient().chat("local-model", [{"role": "user", "content": "hello"}])
    request, _ = opener.requests[-1]
    sent = json.loads(request.data)
    assert result["message"]["content"] == "local reply"
    assert sent["stream"] is False
    assert sent["model"] == "local-model"
    assert request.full_url == "http://127.0.0.1:11434/api/chat"


def test_ollama_client_rejects_redirects_and_surfaces_only_safe_local_errors() -> None:
    redirected = FakeOpener(FakeResponse(b'{"models":[]}', "http://attacker.example/api/tags"))
    with patch("divyesh_api_mind.local_ai.urllib.request.build_opener", return_value=redirected):
        with pytest.raises(LocalRuntimeError, match="left the fixed loopback"):
            OllamaLocalClient().list_models()
    offline = FakeOpener(error=urllib.error.URLError("secret details should not leak"))
    with patch("divyesh_api_mind.local_ai.urllib.request.build_opener", return_value=offline):
        with pytest.raises(LocalRuntimeError, match="no fallback") as error:
            OllamaLocalClient().list_models()
    assert "secret details" not in str(error.value)
    with pytest.raises(ValueError, match="role"):
        OllamaLocalClient.chat(OllamaLocalClient.__new__(OllamaLocalClient), "m", [{"role": [], "content": "x"}])


def test_local_ollama_chat_streaming_is_rejected() -> None:
    client = OllamaLocalClient.__new__(OllamaLocalClient)
    with pytest.raises(ValueError, match="streaming"):
        client.chat("model", [{"role": "user", "content": "hello"}], stream=True)


def test_vault_round_trip_permissions_wrong_password_rekey_and_delete(tmp_path: Path) -> None:
    pytest.importorskip("cryptography")
    path = tmp_path / "private" / "keys.vault"
    vault = KeyVault(path)
    old_password = "test-only master phrase"
    new_password = "another test-only phrase"
    secret = "local-test-not-a-real-provider-key"

    vault.set("EXAMPLE_API_KEY", secret, old_password)
    assert vault.get("EXAMPLE_API_KEY", old_password) == secret
    assert vault.list_names(old_password) == ["EXAMPLE_API_KEY"]
    envelope = path.read_bytes()
    assert secret.encode() not in envelope
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    with pytest.raises(VaultError, match="wrong passphrase"):
        vault.list_names("wrong master phrase")

    vault.rekey(old_password, new_password)
    assert vault.get("EXAMPLE_API_KEY", new_password) == secret
    vault.delete("EXAMPLE_API_KEY", new_password)
    assert vault.list_names(new_password) == []
    assert vault.status()["encrypted"] is True


def test_vault_refuses_weak_password_symlinks_and_permissive_files(tmp_path: Path) -> None:
    pytest.importorskip("cryptography")
    path = tmp_path / "cfg" / "keys.vault"
    vault = KeyVault(path)
    with pytest.raises(VaultError, match="12 characters"):
        vault.set("MY_KEY", "not-real", "too short")
    with pytest.raises(VaultError, match="safe length limit"):
        vault.set("MY_KEY", "not-real", "x" * 1025)
    vault.set("MY_KEY", "test-secret", "a secure test passphrase")
    path.chmod(0o644)
    with pytest.raises(VaultError, match="permissions are too broad"):
        vault.get("MY_KEY", "a secure test passphrase")

    link = tmp_path / "keys-link.vault"
    try:
        link.symlink_to(path)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not available")
    with pytest.raises(VaultError, match="symbolic link"):
        KeyVault(link)
    if hasattr(os, "mkfifo"):
        fifo = tmp_path / "vault.fifo"
        os.mkfifo(fifo)
        with pytest.raises(VaultError, match="regular file"):
            KeyVault(fifo)

    oversized = tmp_path / "oversized.vault"
    oversized.write_bytes(b"x" * (1024 * 1024 + 1))
    if os.name == "posix":
        oversized.chmod(0o600)
    with pytest.raises(VaultError, match="safe size limit"):
        KeyVault(oversized).list_names("a secure test passphrase")


def test_env_file_is_restricted_and_composition_precedence_is_explicit(tmp_path: Path) -> None:
    pytest.importorskip("cryptography")
    from divyesh_api_mind.vault import compose_environment, load_env_file

    env_path = tmp_path / ".env"
    env_path.write_text("# comment\nA='from-file'\nB=$HOME\n")
    assert load_env_file(env_path) == {"A": "from-file", "B": "$HOME"}
    vault = KeyVault(tmp_path / "vault" / "keys.vault")
    vault.set("A", "from-vault", "a secure test passphrase")
    vault.set("C", "from-vault-c", "a secure test passphrase")
    result = compose_environment(
        process_environment={"A": "from-shell"}, env_file=env_path,
        vault=vault, master_passphrase="a secure test passphrase",
    )
    assert result["A"] == "from-shell"
    assert result["B"] == "$HOME"
    assert result["C"] == "from-vault-c"

    duplicate = tmp_path / "bad.env"
    duplicate.write_text("A=one\nA=two\n")
    with pytest.raises(VaultError, match="duplicate"):
        load_env_file(duplicate)
    script = tmp_path / "code.env"
    script.write_text("A=$(touch /tmp/never-run)\n")
    assert load_env_file(script)["A"] == "$(touch /tmp/never-run)"

    oversized = tmp_path / "oversized.env"
    oversized.write_bytes(b"A=" + b"x" * (64 * 1024))
    with pytest.raises(VaultError, match="safe size limit"):
        load_env_file(oversized)
    if hasattr(os, "mkfifo"):
        fifo = tmp_path / "env.fifo"
        os.mkfifo(fifo)
        with pytest.raises(VaultError, match="regular file"):
            load_env_file(fifo)


def test_cli_vault_never_prints_secret_or_passphrase(tmp_path: Path, capsys) -> None:
    pytest.importorskip("cryptography")
    path = tmp_path / "vault" / "keys.vault"
    entered = iter(["test-only passphrase phrase", "test-only passphrase phrase", "do-not-display-secret", "do-not-display-secret"])
    with patch("divyesh_api_mind.cli.getpass", side_effect=lambda _prompt: next(entered)):
        status = cli.main(["vault", "--path", str(path), "set", "EXAMPLE_API_KEY"])
    output = capsys.readouterr().out
    assert status == 0
    assert "EXAMPLE_API_KEY" in output
    assert "do-not-display-secret" not in output
    assert "test-only passphrase" not in output


def test_cli_config_check_reads_vault_presence_without_printing_values(tmp_path: Path, capsys) -> None:
    pytest.importorskip("cryptography")
    path = tmp_path / "vault" / "keys.vault"
    secret = "test-only-census-value-do-not-display"
    KeyVault(path).set("CENSUS_API_KEY", secret, "test-only vault passphrase")
    with patch("divyesh_api_mind.cli.getpass", return_value="test-only vault passphrase"), patch.dict(os.environ, {}, clear=True):
        status = cli.main(["config-check", "--use-vault", "--vault-path", str(path)])
    output = capsys.readouterr().out
    assert status == 1  # other required credentials are intentionally absent
    payload = json.loads(output)
    assert payload["credentials_displayed"] is False
    assert "CENSUS_API_KEY" in output
    assert any(item["variable_name"] == "CENSUS_API_KEY" and item["configured"] for item in payload["items"])
    assert secret not in output


def test_cli_discovery_output_is_safe_mocked_and_never_promotes(tmp_path: Path, capsys) -> None:
    target_file = tmp_path / "targets.json"
    target_file.write_text(json.dumps({"schema_version": "1.0", "targets": [target()]}))
    output = tmp_path / "technology_discovery.json"

    class MockPipeline:
        def __init__(self, *, timeout: float) -> None:
            assert timeout == 12.0

        def discover_github_targets(self, targets, *, checked_on, existing):
            lead = create_github_discovery_record(targets[0], checked_on=checked_on, payload=github_payload())
            return merge_discovery_records(existing, [lead], checked_on=checked_on), []

    with patch("divyesh_api_mind.cli.TechnologyResearchPipeline", MockPipeline):
        status = cli.main([
            "research-discover-github", "--targets", str(target_file), "--output", str(output),
            "--checked-on", "2026-11-12",
        ])
    result = json.loads(capsys.readouterr().out)
    saved = json.loads(output.read_text())
    assert status == 0
    assert result["provider_product_endpoints_called"] == 0
    assert result["automatic_promotion"] is False
    assert validate_technology_discovery(saved) == []
    assert saved["records"][0]["accepted"] is False

    with patch("divyesh_api_mind.cli.TechnologyResearchPipeline", MockPipeline):
        unsafe = cli.main([
            "research-discover-github", "--targets", str(target_file), "--output", str(DATA_DIR / "apis.json"),
            "--checked-on", "2026-11-12",
        ])
    assert unsafe == 2
    assert "must be named technology_discovery.json" in capsys.readouterr().err


def test_cli_manual_evidence_and_review_ledger_preserve_acceptance_files(tmp_path: Path, capsys) -> None:
    data_dir = copy_catalogs(tmp_path / "catalogs")
    discovery_path = data_dir / "technology_discovery.json"
    discovery_path.write_text(json.dumps(discovery_document(), indent=2))
    record = json.loads(discovery_path.read_text())["records"][0]
    evidence_file = tmp_path / "evidence.json"
    evidence_file.write_text(json.dumps({
        "evidence_type": "official_provider_documentation",
        "source_url": "https://provider.example/docs/pricing",
        "checked_on": "2026-11-12",
        "primary_source": True,
        "claims_supported": ["This page publishes the provider's pricing and plan conditions."],
        "snapshot": {"review_note": "Manually reviewed documentation; no endpoint was called."},
    }))
    hashes_before = {name: (data_dir / name).read_bytes() for name in ("apis.json", "models.json", "datasets.json", "mcp_registry.json")}

    status = cli.main([
        "research-evidence-add", "--catalog-dir", str(data_dir), "--record-id", record["id"],
        "--evidence", str(evidence_file),
    ])
    evidence_output = json.loads(capsys.readouterr().out)
    assert status == 0
    assert evidence_output["claims_normalized"] is False

    status = cli.main([
        "research-review-claim", "--catalog-dir", str(data_dir), "--record-id", record["id"],
        "--field", "free_status", "--raw-value-json", '"pricing page states a limited plan"',
        "--normalized-value-json", '"UNKNOWN"', "--decision", "INSUFFICIENT",
        "--evidence-id", record["evidence_refs"][0], "--evidence-id", evidence_output["evidence_id"],
        "--reviewer", "Researcher A", "--notes", "A human reviewed the evidence, but service access was not confirmed.",
        "--confidence", "0.4", "--recorded-on", "2026-11-12",
    ])
    review_output = json.loads(capsys.readouterr().out)
    assert status == 0
    assert review_output["accepted_catalog_modified"] is False
    ledger = json.loads((data_dir / "technology_research_reviews.json").read_text())
    assert validate_research_review_ledger(ledger) == []
    assert len(ledger["events"]) == 1
    for name, content in hashes_before.items():
        assert (data_dir / name).read_bytes() == content


def test_cli_refuses_to_overwrite_a_different_existing_review_history(tmp_path: Path, capsys) -> None:
    data_dir = copy_catalogs(tmp_path / "catalogs")
    discovery = discovery_document()
    discovery_path = data_dir / "technology_discovery.json"
    discovery_path.write_text(json.dumps(discovery))
    record = discovery["records"][0]

    def make_ledger(notes: str) -> dict[str, object]:
        return append_research_review_event(
            None,
            discovery_document=discovery,
            record_id=record["id"],
            field="free_status",
            raw_value="not established",
            normalized_value="UNKNOWN",
            decision="INSUFFICIENT",
            evidence_refs=[record["evidence_refs"][0]],
            reviewer="Reviewer",
            notes=notes,
            confidence=0.2,
            recorded_on="2026-11-12",
        )

    source_ledger = tmp_path / "source-ledger.json"
    source_ledger.write_text(json.dumps(make_ledger("source ledger history")))
    output_path = tmp_path / "technology_research_reviews.json"
    output_path.write_text(json.dumps(make_ledger("independent output history")))
    original_output = output_path.read_bytes()

    status = cli.main([
        "research-review-claim", "--catalog-dir", str(data_dir), "--record-id", record["id"],
        "--field", "python_sdk_status", "--raw-value-json", '"SDK not confirmed"',
        "--normalized-value-json", '"UNKNOWN"', "--decision", "INSUFFICIENT",
        "--evidence-id", record["evidence_refs"][0], "--reviewer", "Reviewer B",
        "--notes", "No official SDK evidence was supplied.", "--confidence", "0.1",
        "--recorded-on", "2026-11-12", "--ledger", str(source_ledger), "--output", str(output_path),
    ])
    assert status == 2
    assert "refusing to overwrite a different review history" in capsys.readouterr().err
    assert output_path.read_bytes() == original_output


def test_cli_hub_and_validation_do_not_contact_network(capsys) -> None:
    status = cli.main(["hub-search", "--accepted-only", "--capability", "scholarly"])
    records = json.loads(capsys.readouterr().out)
    assert status == 0
    assert records
    assert all(record["record_state"] == "ACCEPTED_CATALOG" for record in records)
    assert cli.main(["validate"]) == 0
    output = capsys.readouterr().out
    assert "apis: valid" in output


def test_intelligence_hub_does_not_mutate_user_documents() -> None:
    before = (DATA_DIR / "apis.json").read_bytes()
    hub = IntelligenceHub(catalog_dir=DATA_DIR)
    hub.search(query="OpenAlex")
    assert (DATA_DIR / "apis.json").read_bytes() == before
    assert APIMind(catalog_dir=DATA_DIR).counts["apis"] == 26
