from __future__ import annotations

import contextlib
import copy
import io
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from divyesh_api_mind import (
    APIError,
    add_review_evidence,
    classify_review_candidate,
    create_api_record_proposal,
    create_review_evidence,
    create_verification_batch,
    find_candidate_duplicates,
    probe_review_endpoint,
    rank_review_candidates,
    record_review_finding,
    transition_review_stage,
    validate_review_evidence,
    validate_verification_batch,
)
from divyesh_api_mind.cli import main
from divyesh_api_mind.discovery import import_openapi_spec
from divyesh_api_mind.transport import HTTPResult
from divyesh_api_mind.verification import (
    _PROBE_LAST_BY_HOST,
    _authentication_record_matches,
    _enforce_probe_rate_limit,
    _finding_value_is_valid,
)

AS_OF = "2026-11-12"
CANDIDATE_ID = "candidate-evidence-api-test"
ENDPOINT_URL = "https://api.evidence.example.com/v1/items"


class RecordingTransport:
    def __init__(self, result: HTTPResult | BaseException) -> None:
        self.result = result
        self.calls: list[dict[str, object]] = []

    def request(self, record_id, method, url, **kwargs):  # noqa: ANN001
        self.calls.append({"record_id": record_id, "method": method, "url": url, **kwargs})
        if isinstance(self.result, BaseException):
            raise self.result
        return self.result


def make_queue():
    queue = import_openapi_spec(
        {
            "openapi": "3.0.0",
            "info": {"title": "Evidence API", "version": "1.0"},
            "servers": [{"url": "https://api.evidence.example.com/v1"}],
            "externalDocs": {"url": "https://provider.example.com/docs"},
            "paths": {"/items": {"get": {"summary": "List public items"}}},
        },
        source_url="https://specs.example.net/evidence-api/openapi.json",
        checked_on=AS_OF,
    )
    queue["candidates"][0]["candidate_id"] = CANDIDATE_ID
    queue["candidates"][0]["source_claims"] = {
        "api_atlas_access": "Free",
        "api_atlas_auth": "None",
        "api_atlas_verified": True,
        "api_atlas_checked": AS_OF,
    }
    return queue


def make_batch():
    return create_verification_batch(make_queue(), limit=1, generated_on=AS_OF)


def add_evidence(batch, evidence_type, url, *, source_classification="official_provider", primary_source=True,
                 confidence=0.95, reviewer_status="supports", notes="Reviewed authoritative source.", **extra):
    evidence = create_review_evidence(
        CANDIDATE_ID,
        url=url,
        evidence_type=evidence_type,
        observed_on=AS_OF,
        reviewer_status=reviewer_status,
        confidence=confidence,
        notes=notes,
        source_classification=source_classification,
        primary_source=primary_source,
        reviewer="reviewer:test",
        **extra,
    )
    return add_review_evidence(batch, CANDIDATE_ID, evidence, reviewer="reviewer:test", recorded_on=AS_OF), evidence


def find(batch, field, value, evidence_ids, *, status="verified", confidence=0.9):
    return record_review_finding(
        batch,
        CANDIDATE_ID,
        field,
        value,
        status=status,
        evidence_ids=evidence_ids,
        reviewer="reviewer:test",
        notes=f"Independently reviewed {field} evidence.",
        confidence=confidence,
        observed_on=AS_OF,
    )


def transition(batch, outcome="completed", *, role="reviewer", decision=None, **kwargs):
    return transition_review_stage(
        batch,
        CANDIDATE_ID,
        outcome=outcome,
        reviewer="reviewer:test" if role != "human" else "human:approver",
        notes="Recorded after reviewing the evidence for this stage.",
        recorded_on=AS_OF,
        reviewer_role=role,
        decision=decision,
        **kwargs,
    )


def advance_to_endpoint(*, permit_probe=True):
    batch = make_batch()
    batch, provider = add_evidence(
        batch, "provider_homepage", "https://provider.example.com/api",
        notes="Official provider page identifies this API and the provider.",
    )
    batch = find(batch, "api_real", True, [provider["evidence_id"]])
    batch = find(batch, "official_provider", "yes", [provider["evidence_id"]])
    batch = transition(batch)

    batch, docs = add_evidence(
        batch, "official_documentation", "https://provider.example.com/docs",
        notes="Official endpoint and authentication reference.",
    )
    batch = find(batch, "documentation_available", True, [docs["evidence_id"]])
    batch, maintenance = add_evidence(
        batch, "maintenance_record", "https://github.com/example/evidence-api/commits/main",
        source_classification="official_repository",
        notes="Official repository release/change record; latest verified activity date recorded separately.",
        activity_on="2026-11-01",
    )
    batch = find(batch, "maintenance_activity", True, [maintenance["evidence_id"]])
    batch = transition(batch)

    batch, auth = add_evidence(
        batch, "authentication_documentation", "https://provider.example.com/docs/authentication",
        notes="Provider documents public read access without an API key.",
    )
    batch = find(batch, "authentication", "none", [auth["evidence_id"]])
    batch = transition(batch)

    batch, pricing = add_evidence(
        batch, "pricing_access_documentation", "https://provider.example.com/pricing",
        notes="Provider pricing page documents an available free no-key tier.",
    )
    batch = find(batch, "free_tier", "FREE_NO_KEY", [pricing["evidence_id"]])
    batch, quota = add_evidence(
        batch, "quota_documentation", "https://provider.example.com/docs/limits",
        notes="Provider documents request limits and per-endpoint quota notes.",
    )
    quota_value = {"details": "No fixed daily quota is published for this documented read endpoint."}
    batch = find(batch, "quotas", quota_value, [quota["evidence_id"]])
    batch = transition(batch)

    batch, permission = add_evidence(
        batch, "terms_of_service", "https://provider.example.com/terms",
        notes="Provider policy reviewed; permits a single low-rate unauthenticated GET/HEAD read probe.",
        permits_unauthenticated_read_probes=permit_probe,
    )
    batch, endpoint_docs = add_evidence(
        batch, "endpoint_documentation", "https://provider.example.com/reference/items",
        notes="Provider documents the exact public GET endpoint used by this review.",
        documented_endpoint_url=ENDPOINT_URL,
        documented_method="GET",
    )
    return batch, permission, endpoint_docs, quota_value


def advance_to_human_approval(transport=None):
    batch, permission, endpoint_docs, quota_value = advance_to_endpoint()
    _PROBE_LAST_BY_HOST.clear()
    probe_transport = transport or RecordingTransport(HTTPResult(200, {"content-type": "application/json"}, b'{"items":[]}'))
    with patch("divyesh_api_mind.verification.SafeHTTPTransport", return_value=probe_transport):
        batch = probe_review_endpoint(
            batch,
            CANDIDATE_ID,
            ENDPOINT_URL,
            permission_evidence_id=permission["evidence_id"],
            reviewer="reviewer:test",
            observed_on=AS_OF,
        )
    batch = find(batch, "python_integration", True, [endpoint_docs["evidence_id"]])
    batch = transition(batch)

    batch, license_doc = add_evidence(
        batch, "license_documentation", "https://provider.example.com/legal/data-license",
        notes="Provider states API-service and returned-data terms; they are recorded separately.",
    )
    license_value = {
        "service": "Provider API service terms apply.",
        "data": "Provider documentation grants CC0 reuse for public API data.",
    }
    batch = find(batch, "license", license_value, [license_doc["evidence_id"]])
    batch = transition(batch)
    assert batch["reviews"][0]["workflow"]["current_stage"] == "human_approval"
    return batch, quota_value, license_value


class VerificationRankingTests(unittest.TestCase):
    def test_upstream_priority_is_not_a_score_bonus_or_verification(self) -> None:
        queue = make_queue()
        candidate = queue["candidates"][0]
        candidate["review_priority"] = "unverified_directory_pointer"
        before = rank_review_candidates(queue, limit=1, as_of=AS_OF)[0]
        candidate["review_priority"] = "upstream_checked_pointer"
        after = rank_review_candidates(queue, limit=1, as_of=AS_OF)[0]
        self.assertEqual(before["priority_score"], after["priority_score"])
        self.assertEqual(before["components"], after["components"])
        self.assertEqual(after["upstream_priority_claim"], "upstream_checked_pointer")
        self.assertFalse(after["independent_verification_present"])

    def test_weighted_model_has_transparent_components_and_diversity(self) -> None:
        ranked = rank_review_candidates(make_queue(), limit=1, as_of=AS_OF)
        item = ranked[0]
        self.assertEqual(sum(item["components"][name]["weight"] for name in item["components"]), 100)
        self.assertAlmostEqual(item["priority_score"], sum(value["weighted_points"] for value in item["components"].values()))
        self.assertEqual(item["components"]["category_diversity"]["score"], 100)
        self.assertIn("project_usefulness", item["components"])
        self.assertIn("free_access_evidence", item["components"])
        self.assertIn("maintenance_activity", item["components"])

    def test_duplicate_candidate_ids_are_rejected(self) -> None:
        candidate = make_queue()["candidates"][0]
        with self.assertRaisesRegex(ValueError, "duplicate candidate_id"):
            rank_review_candidates([candidate, copy.deepcopy(candidate)], limit=2, as_of=AS_OF)

    def test_batch_validator_recomputes_triage_scores_and_rejects_tampering(self) -> None:
        batch = make_batch()
        tampered = copy.deepcopy(batch)
        review = tampered["reviews"][0]
        usefulness = review["priority_components"]["project_usefulness"]
        removed_points = usefulness["weighted_points"]
        usefulness["score"] = 0
        usefulness["weighted_points"] = 0.0
        review["base_score_without_diversity"] = round(review["base_score_without_diversity"] - removed_points, 2)
        review["priority_score"] = round(review["priority_score"] - removed_points, 2)
        self.assertTrue(any("ranking is not reproducible" in error for error in validate_verification_batch(tampered)))

    def test_duplicate_finder_reports_exact_and_possible_pairs_without_merging(self) -> None:
        candidates = [
            {"candidate_id": "a", "name": "Same API", "base_url": "https://same.example.com/v1"},
            {"candidate_id": "b", "name": "Same API", "base_url": "https://same.example.com/v1/"},
            {"candidate_id": "c", "name": "Different API", "base_url": "https://same.example.com/v1"},
            {"candidate_id": "d", "name": "Same API", "base_url": "https://other.example.com"},
        ]
        pairs = find_candidate_duplicates(candidates)
        self.assertIn({"candidate_ids": ["a", "b"], "signals": ["exact_name_and_url"]}, pairs)
        self.assertIn({"candidate_ids": ["a", "c"], "signals": ["same_url_different_name"]}, pairs)
        self.assertIn({"candidate_ids": ["a", "d"], "signals": ["same_name_different_url"]}, pairs)


class VerificationEvidenceAndStateTests(unittest.TestCase):
    def test_initial_batch_has_all_stages_unknown_and_audits_discovery_and_metadata_validation(self) -> None:
        batch = make_batch()
        self.assertEqual(validate_verification_batch(batch), [])
        review = batch["reviews"][0]
        self.assertEqual(review["workflow"]["current_stage"], "official_source_identification")
        self.assertEqual(review["workflow"]["stage_statuses"]["metadata_validation"], "completed")
        self.assertEqual(review["workflow"]["findings"]["api_real"]["value"], "UNKNOWN")
        self.assertEqual(batch["summary"]["candidates_with_primary_source_review"], 0)
        self.assertEqual(
            [item["event_type"] for item in review["workflow"]["transition_log"]],
            ["candidate_discovery_recorded", "stage_transition", "stage_transition"],
        )

    def test_upstream_free_auth_verified_and_checked_claims_never_classify_as_facts(self) -> None:
        batch = make_batch()
        candidate = batch["reviews"][0]["candidate"]
        classification = classify_review_candidate(candidate, batch["reviews"][0]["workflow"])
        self.assertEqual(classification["free_status"], "UNKNOWN")
        self.assertEqual(classification["authentication"], "UNKNOWN")
        self.assertEqual(classification["api_real"], "UNKNOWN")
        self.assertFalse(classification["source_claims_used_as_facts"])
        self.assertIs(candidate["source_claims"]["api_atlas_verified"], True)

    def test_secondary_directory_evidence_cannot_verify_a_finding(self) -> None:
        batch = make_batch()
        batch, evidence = add_evidence(
            batch,
            "official_documentation",
            "https://community.example.net/listing",
            source_classification="community",
            primary_source=False,
            notes="Community page repeats upstream claims; not a provider source.",
        )
        with self.assertRaisesRegex(ValueError, "authoritative evidence"):
            find(batch, "api_real", True, [evidence["evidence_id"]])
        self.assertEqual(batch["reviews"][0]["workflow"]["findings"]["api_real"]["status"], "unknown")

    def test_license_and_quota_findings_must_contain_resolved_claims(self) -> None:
        self.assertFalse(_finding_value_is_valid("license", {"service": "UNKNOWN", "data": "CC0"}))
        self.assertFalse(_finding_value_is_valid("license", {"service": "Terms apply.", "data": "UNKNOWN"}))
        self.assertFalse(_finding_value_is_valid("license", "MIT"))
        self.assertTrue(_finding_value_is_valid("license", {"service": "Provider terms apply.", "data": "CC0"}))
        self.assertFalse(_finding_value_is_valid("quotas", {"details": "UNKNOWN"}))
        self.assertTrue(_finding_value_is_valid("quotas", {"details": "100 requests per day."}))

    def test_free_status_needs_authentication_consistency(self) -> None:
        auth_evidence = create_review_evidence(
            CANDIDATE_ID, url="https://provider.example.com/docs/auth", evidence_type="authentication_documentation",
            observed_on=AS_OF, reviewer_status="supports", confidence=0.95, notes="Official auth docs.",
            source_classification="official_provider", primary_source=True, reviewer="reviewer:test",
        )
        free_evidence = create_review_evidence(
            CANDIDATE_ID, url="https://provider.example.com/pricing", evidence_type="pricing_access_documentation",
            observed_on=AS_OF, reviewer_status="supports", confidence=0.95, notes="Official access docs.",
            source_classification="official_provider", primary_source=True, reviewer="reviewer:test",
        )
        def classify(auth_value, tier):
            workflow = {
                "evidence": [auth_evidence, free_evidence],
                "findings": {
                    "authentication": {"status": "verified", "value": auth_value, "evidence_ids": [auth_evidence["evidence_id"]]},
                    "free_tier": {"status": "verified", "value": tier, "evidence_ids": [free_evidence["evidence_id"]]},
                },
            }
            return classify_review_candidate({}, workflow)["free_status"]
        self.assertEqual(classify("UNKNOWN", "FREE_NO_KEY"), "UNKNOWN")
        self.assertEqual(classify("optional API key", "FREE_WITH_KEY"), "UNKNOWN")
        self.assertEqual(classify({"kind": "api_key_header", "required": True}, "FREE_WITH_KEY"), "FREE_WITH_KEY")
        self.assertEqual(classify({"kind": "api_key_header", "required": True}, "FREE_NO_KEY"), "UNKNOWN")
        self.assertEqual(classify({"kind": "optional_api_key_header", "required": False}, "FREE_NO_KEY"), "FREE_NO_KEY")
        self.assertEqual(classify("none", "FREE_NO_KEY"), "FREE_NO_KEY")
        optional_header = {"kind": "optional_api_key_header", "required": False, "verified": True}
        self.assertFalse(_authentication_record_matches("optional API key", optional_header))
        self.assertTrue(_authentication_record_matches("optional API key header", optional_header))

    def test_evidence_validation_requires_source_date_confidence_and_safe_probe_metadata(self) -> None:
        evidence = {
            "evidence_id": "evidence-test",
            "candidate_id": CANDIDATE_ID,
            "url": "https://provider.example.com/docs",
            "evidence_type": "official_documentation",
            "observed_on": AS_OF,
            "reviewer_status": "supports",
            "confidence": 0.9,
            "notes": "Primary source reviewed.",
            "source_classification": "official_provider",
            "primary_source": True,
            "reviewer": "reviewer:test",
        }
        self.assertEqual(validate_review_evidence(evidence), [])
        invalid = copy.deepcopy(evidence)
        invalid["url"] = "https://user:secret@provider.example.com/docs"
        self.assertTrue(validate_review_evidence(invalid))
        invalid = copy.deepcopy(evidence)
        invalid["observed_on"] = "not-a-date"
        self.assertTrue(validate_review_evidence(invalid))
        invalid = copy.deepcopy(evidence)
        invalid["reviewer_status"] = "unreviewed"
        invalid["confidence"] = 0.9
        self.assertTrue(validate_review_evidence(invalid))

    def test_duplicate_evidence_id_and_wrong_stage_are_rejected(self) -> None:
        batch = make_batch()
        batch, evidence = add_evidence(batch, "provider_homepage", "https://provider.example.com/api")
        with self.assertRaisesRegex(ValueError, "duplicate evidence_id"):
            add_review_evidence(batch, CANDIDATE_ID, evidence, reviewer="reviewer:test", recorded_on=AS_OF)
        with self.assertRaisesRegex(ValueError, "belongs to stage"):
            record_review_finding(
                batch, CANDIDATE_ID, "authentication", "none", status="verified",
                evidence_ids=[evidence["evidence_id"]], reviewer="reviewer:test",
                notes="wrong stage", confidence=0.8, observed_on=AS_OF,
            )

    def test_blocked_stage_requires_resumption_and_every_transition_is_logged(self) -> None:
        batch = make_batch()
        with self.assertRaisesRegex(ValueError, "complete required finding"):
            transition(batch)
        blocked = transition(batch, "blocked")
        self.assertEqual(blocked["reviews"][0]["workflow"]["workflow_status"], "blocked")
        with self.assertRaisesRegex(ValueError, "resume the blocked/deferred stage"):
            add_evidence(blocked, "provider_homepage", "https://provider.example.com/api")
        resumed = transition(blocked, "resumed")
        self.assertEqual(resumed["reviews"][0]["workflow"]["current_stage_status"], "in_progress")
        self.assertEqual(len(resumed["reviews"][0]["workflow"]["transition_log"]), 5)
        self.assertEqual(validate_verification_batch(resumed), [])

    def test_modified_workflow_state_without_transition_record_is_invalid(self) -> None:
        batch = make_batch()
        tampered = copy.deepcopy(batch)
        tampered["reviews"][0]["workflow"]["current_stage"] = "documentation_review"
        self.assertTrue(validate_verification_batch(tampered))

    def test_audit_event_hash_chain_detects_changed_notes(self) -> None:
        batch = make_batch()
        tampered = copy.deepcopy(batch)
        tampered["reviews"][0]["workflow"]["transition_log"][0]["notes"] = "Changed after recording."
        self.assertTrue(any("hash does not match" in error for error in validate_verification_batch(tampered)))

    def test_terminal_workflow_cannot_receive_new_evidence(self) -> None:
        rejected = transition(make_batch(), "rejected")
        with self.assertRaisesRegex(ValueError, "terminal workflow"):
            add_evidence(rejected, "provider_homepage", "https://provider.example.com/api")

    def test_future_dated_evidence_cannot_be_backdated_into_the_ledger(self) -> None:
        batch = make_batch()
        future = create_review_evidence(
            CANDIDATE_ID,
            url="https://provider.example.com/api",
            evidence_type="provider_homepage",
            observed_on="2026-11-13",
            reviewer_status="supports",
            confidence=0.9,
            notes="Observed after the claimed evidence-entry date.",
            source_classification="official_provider",
            primary_source=True,
            reviewer="reviewer:test",
        )
        with self.assertRaisesRegex(ValueError, "cannot be after"):
            add_review_evidence(batch, CANDIDATE_ID, future, reviewer="reviewer:test", recorded_on=AS_OF)

    def test_official_registry_can_verify_provider_identity_but_not_api_existence(self) -> None:
        batch = make_batch()
        batch, homepage = add_evidence(batch, "provider_homepage", "https://provider.example.com/api")
        batch = find(batch, "api_real", True, [homepage["evidence_id"]])
        registry = create_review_evidence(
            CANDIDATE_ID,
            url="https://registry.example.gov/providers/example",
            evidence_type="official_registry",
            observed_on=AS_OF,
            reviewer_status="supports",
            confidence=0.9,
            notes="Official registry identifies the provider responsible for the service.",
            source_classification="official_registry",
            primary_source=True,
            reviewer="reviewer:test",
        )
        batch = add_review_evidence(batch, CANDIDATE_ID, registry, reviewer="reviewer:test", recorded_on=AS_OF)
        batch = find(batch, "official_provider", "yes", [registry["evidence_id"]])
        classification = classify_review_candidate(batch["reviews"][0]["candidate"], batch["reviews"][0]["workflow"])
        self.assertEqual(classification["api_real"], True)
        self.assertEqual(classification["official_provider"], "yes")

    def test_maintenance_rank_uses_provider_activity_date_not_date_reviewed(self) -> None:
        # A recent source review cannot make a years-old maintenance event look current.
        batch, provider = add_evidence(make_batch(), "provider_homepage", "https://provider.example.com/api")
        batch = find(batch, "api_real", True, [provider["evidence_id"]])
        batch = find(batch, "official_provider", "yes", [provider["evidence_id"]])
        batch = transition(batch)
        batch, docs = add_evidence(batch, "official_documentation", "https://provider.example.com/docs")
        batch = find(batch, "documentation_available", True, [docs["evidence_id"]])
        batch, maintenance = add_evidence(
            batch, "maintenance_record", "https://github.com/example/project/commits/main",
            source_classification="official_repository", activity_on="2020-01-01",
        )
        batch = find(batch, "maintenance_activity", True, [maintenance["evidence_id"]])
        ranked = rank_review_candidates(make_queue(), limit=1, as_of=AS_OF, review_records={CANDIDATE_ID: batch["reviews"][0]})[0]
        self.assertEqual(ranked["components"]["maintenance_activity"]["score"], 0)


class EndpointProbeTests(unittest.TestCase):
    def test_probe_enforces_permission_rate_time_and_data_limits_without_credentials(self) -> None:
        batch, permission, endpoint_docs, _ = advance_to_endpoint()
        transport = RecordingTransport(HTTPResult(200, {"content-type": "application/json"}, b'{"ok":true}'))
        _PROBE_LAST_BY_HOST.clear()
        with patch("divyesh_api_mind.verification.SafeHTTPTransport", return_value=transport):
            updated = probe_review_endpoint(
                batch, CANDIDATE_ID, ENDPOINT_URL,
                permission_evidence_id=permission["evidence_id"], reviewer="reviewer:test",
                observed_on=AS_OF, timeout_seconds=4, max_response_bytes=4096,
            )
        call = transport.calls[0]
        self.assertEqual(call["method"], "GET")
        self.assertEqual(call["retries"], 0)
        self.assertEqual(call["max_response_bytes"], 4096)
        self.assertEqual("Authorization" not in call.get("headers", {}), True)
        workflow = updated["reviews"][0]["workflow"]
        probe = next(item for item in workflow["evidence"] if item["evidence_type"] == "endpoint_probe")
        self.assertEqual(probe["response_bytes"], len(b'{"ok":true}'))
        self.assertNotIn("response_body", probe)
        self.assertNotIn("response_headers", probe)
        self.assertEqual(workflow["findings"]["currently_accessible"]["value"], True)
        self.assertEqual(validate_verification_batch(updated), [])

    def test_manually_supplied_probe_result_cannot_masquerade_as_a_live_observation(self) -> None:
        batch, permission, _, _ = advance_to_endpoint()
        forged_probe = create_review_evidence(
            CANDIDATE_ID,
            url=ENDPOINT_URL,
            evidence_type="endpoint_probe",
            observed_on=AS_OF,
            reviewer_status="supports",
            confidence=0.9,
            notes="A manually supplied result is not a probe execution.",
            source_classification="probe_result",
            primary_source=True,
            reviewer="reviewer:test",
            permission_evidence_id=permission["evidence_id"],
            policy_permitted=True,
            request_method="GET",
            credentials_sent=False,
            timeout_seconds=5.0,
            max_response_bytes=65536,
            rate_limit_interval_seconds=2.0,
            retries=0,
            status_code=200,
            response_bytes=2,
            probe_outcome="http_response",
        )
        with self.assertRaisesRegex(ValueError, "only be recorded by probe_review_endpoint"):
            add_review_evidence(batch, CANDIDATE_ID, forged_probe, reviewer="reviewer:test", recorded_on=AS_OF)
        self.assertEqual(validate_verification_batch(batch), [])

    def test_probe_rate_limiter_spaces_repeated_requests(self) -> None:
        _PROBE_LAST_BY_HOST.clear()
        now = [10.0]
        sleeps = []

        def sleep(seconds):
            sleeps.append(seconds)
            now[0] += seconds

        _enforce_probe_rate_limit("api.example.com", sleeper=sleep, clock=lambda: now[0])
        _enforce_probe_rate_limit("api.example.com", sleeper=sleep, clock=lambda: now[0])
        self.assertEqual(sleeps, [2.0])
        _PROBE_LAST_BY_HOST.clear()

    def test_probe_is_blocked_without_explicit_provider_permission(self) -> None:
        batch, permission, _, _ = advance_to_endpoint(permit_probe=False)
        transport = RecordingTransport(HTTPResult(200, {}, b"{}"))
        _PROBE_LAST_BY_HOST.clear()
        with patch("divyesh_api_mind.verification.SafeHTTPTransport", return_value=transport):
            with self.assertRaisesRegex(ValueError, "explicitly permitting"):
                probe_review_endpoint(
                    batch, CANDIDATE_ID, ENDPOINT_URL,
                    permission_evidence_id=permission["evidence_id"], reviewer="reviewer:test",
                    observed_on=AS_OF,
                )
        self.assertEqual(transport.calls, [])

    def test_probe_network_failure_remains_inconclusive_and_unknown(self) -> None:
        batch, permission, _, _ = advance_to_endpoint()
        transport = RecordingTransport(APIError(CANDIDATE_ID, "sanitized network error"))
        _PROBE_LAST_BY_HOST.clear()
        with patch("divyesh_api_mind.verification.SafeHTTPTransport", return_value=transport):
            updated = probe_review_endpoint(
                batch, CANDIDATE_ID, ENDPOINT_URL,
                permission_evidence_id=permission["evidence_id"], reviewer="reviewer:test",
                observed_on=AS_OF,
            )
        classification = classify_review_candidate(updated["reviews"][0]["candidate"], updated["reviews"][0]["workflow"])
        self.assertEqual(classification["currently_accessible"], "NOT_TESTED")
        self.assertEqual(updated["summary"]["currently_accessible_not_tested"], 1)
        probe = next(item for item in updated["reviews"][0]["workflow"]["evidence"] if item["evidence_type"] == "endpoint_probe")
        self.assertEqual(probe["probe_outcome"], "network_error")
        self.assertEqual(validate_verification_batch(updated), [])

    def test_probe_refuses_query_strings_and_other_hosts(self) -> None:
        batch, permission, _, _ = advance_to_endpoint()
        transport = RecordingTransport(HTTPResult(200, {}, b"{}"))
        with patch("divyesh_api_mind.verification.SafeHTTPTransport", return_value=transport):
            with self.assertRaisesRegex(ValueError, "query or fragment"):
                probe_review_endpoint(
                    batch, CANDIDATE_ID, ENDPOINT_URL + "?q=example",
                    permission_evidence_id=permission["evidence_id"], reviewer="reviewer:test",
                )
            with self.assertRaisesRegex(ValueError, "exact endpoint"):
                probe_review_endpoint(
                    batch, CANDIDATE_ID, "https://other.example.com/items",
                    permission_evidence_id=permission["evidence_id"], reviewer="reviewer:test",
                )
            with self.assertRaisesRegex(ValueError, "path is unsafe"):
                probe_review_endpoint(
                    batch, CANDIDATE_ID, "https://api.evidence.example.com/v1/%252e%252e/admin",
                    permission_evidence_id=permission["evidence_id"], reviewer="reviewer:test",
                )
        self.assertEqual(transport.calls, [])


class ProposalAndAttributionTests(unittest.TestCase):
    def test_proposal_requires_independent_review_and_does_not_mutate_input(self) -> None:
        batch = make_batch()
        before = copy.deepcopy(batch)
        record = {"id": "evidence-api-test"}
        with self.assertRaisesRegex(ValueError, "active human_approval"):
            create_api_record_proposal(batch, CANDIDATE_ID, record, reviewer="human:approver")
        self.assertEqual(batch, before)

    def test_verified_proposal_requires_human_approval_and_preserves_sources_history_and_license(self) -> None:
        original = make_batch()
        batch, quota_value, license_value = advance_to_human_approval()
        workflow = batch["reviews"][0]["workflow"]
        verified_ids = sorted({
            evidence_id
            for finding in workflow["findings"].values() if finding["status"] == "verified"
            for evidence_id in finding["evidence_ids"]
        })
        source_rows = [
            {
                "url": item["url"],
                "title": item["notes"],
                "checked_on": item["observed_on"],
                "evidence_level": "primary_direct",
            }
            for item in workflow["evidence"] if item["evidence_id"] in verified_ids
        ]
        record = {
            "id": "evidence-api-test",
            "type": "api",
            "name": "Evidence API",
            "categories": ["data"],
            "summary": "A synthetic record used only to test approval gates.",
            "base_url": "https://api.evidence.example.com/v1",
            "allowed_hosts": ["api.evidence.example.com"],
            "endpoints": [{"method": "GET", "path": "/items", "purpose": "List public items."}],
            "authentication": {"kind": "none", "required": False, "verified": True},
            "free_status": "FREE_NO_KEY",
            "quota": quota_value,
            "license": license_value,
            "sources": source_rows,
            "last_verified": AS_OF,
            "evidence_confidence": "high",
            "health_probe": None,
        }
        contradictory_auth = copy.deepcopy(record)
        contradictory_auth["authentication"] = {
            "kind": "optional_bearer", "required": False, "verified": True, "env_var": "EXAMPLE_API_TOKEN"
        }
        with self.assertRaisesRegex(ValueError, "authentication"):
            create_api_record_proposal(
                batch, CANDIDATE_ID, contradictory_auth, reviewer="reviewer:test", created_on=AS_OF,
            )
        with self.assertRaisesRegex(ValueError, "already exists"):
            create_api_record_proposal(
                batch, CANDIDATE_ID, record, reviewer="reviewer:test", created_on=AS_OF,
                existing_ids={record["id"]},
            )
        review = batch["reviews"][0]
        review["candidate"]["possible_existing_matches"] = ["existing-record"]
        reranked = rank_review_candidates([review["candidate"]], limit=1, as_of=AS_OF)[0]
        review["priority_score"] = reranked["priority_score"]
        review["base_score_without_diversity"] = reranked["base_score_without_diversity"]
        review["priority_components"] = reranked["components"]
        with self.assertRaisesRegex(ValueError, "possible_existing_catalog_match"):
            create_api_record_proposal(
                batch, CANDIDATE_ID, record, reviewer="reviewer:test", created_on=AS_OF,
            )
        review["candidate"]["possible_existing_matches"] = []
        reranked = rank_review_candidates([review["candidate"]], limit=1, as_of=AS_OF)[0]
        review["priority_score"] = reranked["priority_score"]
        review["base_score_without_diversity"] = reranked["base_score_without_diversity"]
        review["priority_components"] = reranked["components"]
        original_duplicate_flags = copy.deepcopy(review["candidate"].get("possible_duplicate_flags", []))
        review["candidate"]["possible_duplicate_flags"] = ["same_normalized_name_different_url"]
        reranked = rank_review_candidates([review["candidate"]], limit=1, as_of=AS_OF)[0]
        review["priority_score"] = reranked["priority_score"]
        review["base_score_without_diversity"] = reranked["base_score_without_diversity"]
        review["priority_components"] = reranked["components"]
        with self.assertRaisesRegex(ValueError, "possible_unresolved_candidate_duplicate"):
            create_api_record_proposal(
                batch, CANDIDATE_ID, record, reviewer="reviewer:test", created_on=AS_OF,
            )
        review["candidate"]["possible_duplicate_flags"] = original_duplicate_flags
        reranked = rank_review_candidates([review["candidate"]], limit=1, as_of=AS_OF)[0]
        review["priority_score"] = reranked["priority_score"]
        review["base_score_without_diversity"] = reranked["base_score_without_diversity"]
        review["priority_components"] = reranked["components"]
        proposed = create_api_record_proposal(
            batch, CANDIDATE_ID, record, reviewer="reviewer:test", created_on=AS_OF,
            existing_ids={"already-taken"},
        )
        proposal = proposed["reviews"][0]["workflow"]["proposal"]
        self.assertEqual(proposal["status"], "pending_human_approval")
        self.assertEqual(proposal["source_attributions"], proposed["reviews"][0]["candidate"]["source_attributions"])
        self.assertEqual(proposal["source_claims"], proposed["reviews"][0]["candidate"]["source_claims"])
        self.assertEqual(proposal["api_record"]["license"], license_value)
        self.assertTrue(proposal["verification_history"])
        self.assertEqual(validate_verification_batch(proposed), [])
        self.assertIsNone(batch["reviews"][0]["workflow"]["proposal"])
        self.assertEqual(original["reviews"][0]["candidate"]["free_status"], "UNKNOWN")

        with self.assertRaisesRegex(ValueError, "reviewer_role=human"):
            transition(proposed)
        approved = transition(proposed, role="human", decision="approved")
        self.assertEqual(approved["reviews"][0]["workflow"]["proposal"]["status"], "human_approved")
        self.assertEqual(approved["summary"]["human_approved_proposals"], 1)
        with self.assertRaisesRegex(ValueError, "digest"):
            transition(
                approved, role="human", decision="accepted", catalog_entry_id=record["id"],
                catalog_entry_sha256="0" * 64, catalog_record=record,
            )

        import hashlib
        canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        accepted_digest = hashlib.sha256(canonical).hexdigest()
        with self.assertRaisesRegex(ValueError, "already present in the API catalog"):
            transition(
                approved, role="human", decision="accepted", catalog_entry_id=record["id"],
                catalog_entry_sha256=accepted_digest,
            )
        accepted = transition(
            approved, role="human", decision="accepted", catalog_entry_id=record["id"],
            catalog_entry_sha256=accepted_digest, catalog_record=record,
        )
        self.assertEqual(accepted["summary"]["catalog_acceptance_records"], 1)
        self.assertEqual(accepted["summary"]["accepted_candidates_proposed"], 1)
        self.assertEqual(validate_verification_batch(accepted), [])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog_dir = root / "catalogs"
            catalog_dir.mkdir()
            source_data = Path(__file__).resolve().parents[1] / "src" / "divyesh_api_mind" / "data"
            for filename in ("apis.json", "models.json", "datasets.json", "mcp_registry.json"):
                shutil.copyfile(source_data / filename, catalog_dir / filename)
            api_path = catalog_dir / "apis.json"
            api_document = json.loads(api_path.read_text(encoding="utf-8"))
            api_document["records"].append(record)
            api_path.write_text(json.dumps(api_document, ensure_ascii=False, indent=2), encoding="utf-8")
            before_cli_acceptance = api_path.read_bytes()
            approved_path = root / "approved.json"
            approved_path.write_text(json.dumps(approved), encoding="utf-8")
            cli_output_path = root / "catalog-accepted.json"
            cli_output = io.StringIO()
            with contextlib.redirect_stdout(cli_output):
                status = main([
                    "verify-transition", "--catalog-dir", str(catalog_dir), str(approved_path), CANDIDATE_ID,
                    "--outcome", "completed", "--reviewer", "human:approver",
                    "--notes", "Confirmed the exact approved record is already in the catalog.",
                    "--recorded-on", AS_OF, "--reviewer-role", "human", "--decision", "accepted",
                    "--catalog-entry-id", record["id"], "--catalog-entry-sha256", accepted_digest,
                    "--output", str(cli_output_path),
                ])
            self.assertEqual(status, 0)
            self.assertEqual(json.loads(cli_output.getvalue())["summary"]["catalog_acceptance_records"], 1)
            self.assertEqual(api_path.read_bytes(), before_cli_acceptance)

            error_output = io.StringIO()
            with contextlib.redirect_stderr(error_output):
                status = main([
                    "verify-transition", "--catalog-dir", str(catalog_dir), str(approved_path), CANDIDATE_ID,
                    "--outcome", "completed", "--reviewer", "human:approver",
                    "--notes", "Confirm the same record without changing the catalog.",
                    "--recorded-on", AS_OF, "--reviewer-role", "human", "--decision", "accepted",
                    "--catalog-entry-id", record["id"], "--catalog-entry-sha256", accepted_digest,
                    "--output", str(api_path),
                ])
            self.assertEqual(status, 2)
            self.assertIn("cannot overwrite", error_output.getvalue())
            self.assertEqual(api_path.read_bytes(), before_cli_acceptance)

class VerificationCLITests(unittest.TestCase):
    def test_cli_creates_and_validates_a_local_batch_without_network_access(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            queue_path = root / "queue.json"
            batch_path = root / "batch.json"
            queue_path.write_text(json.dumps(make_queue()), encoding="utf-8")
            create_output = io.StringIO()
            with contextlib.redirect_stdout(create_output):
                status = main([
                    "verify-create", "--queue", str(queue_path), "--limit", "1",
                    "--as-of", AS_OF, "--output", str(batch_path),
                ])
            self.assertEqual(status, 0)
            self.assertTrue(batch_path.is_file())
            created = json.loads(batch_path.read_text(encoding="utf-8"))
            self.assertEqual(validate_verification_batch(created), [])
            self.assertEqual(json.loads(create_output.getvalue())["summary"]["candidates_selected"], 1)
            validate_output = io.StringIO()
            with contextlib.redirect_stdout(validate_output):
                status = main(["verify-validate", str(batch_path)])
            self.assertEqual(status, 0)
            self.assertTrue(json.loads(validate_output.getvalue())["valid"])
            original_queue = queue_path.read_bytes()
            error_output = io.StringIO()
            with contextlib.redirect_stderr(error_output):
                status = main([
                    "verify-create", "--queue", str(queue_path), "--limit", "1",
                    "--as-of", AS_OF, "--output", str(queue_path),
                ])
            self.assertEqual(status, 2)
            self.assertEqual(queue_path.read_bytes(), original_queue)
            self.assertIn("must not overwrite", error_output.getvalue())

    def test_probe_cli_rejects_protected_output_before_probe_validation(self) -> None:
        batch, permission, _, _ = advance_to_endpoint()
        with tempfile.TemporaryDirectory() as tmp:
            batch_path = Path(tmp) / "batch.json"
            batch_path.write_text(json.dumps(batch), encoding="utf-8")
            protected_queue = Path(__file__).resolve().parents[1] / "src" / "divyesh_api_mind" / "data" / "discovery_candidates.json"
            error_output = io.StringIO()
            with contextlib.redirect_stderr(error_output):
                status = main([
                    "verify-probe", str(batch_path), CANDIDATE_ID,
                    "--url", "http://example.com", "--permission-evidence-id", permission["evidence_id"],
                    "--reviewer", "reviewer:test", "--output", str(protected_queue),
                ])
            self.assertEqual(status, 2)
            self.assertIn("cannot overwrite", error_output.getvalue())
            self.assertNotIn("probe URL must be safe HTTPS", error_output.getvalue())


if __name__ == "__main__":
    unittest.main()
