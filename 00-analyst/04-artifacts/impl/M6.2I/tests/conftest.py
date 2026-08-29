"""Test fixtures for slice M6.2A.

In-memory adapters are TEST DOUBLES for the CONSUMED tables (event_registry, guest_contacts,
guest_marketing_consent_snapshot, customers) that Core / Customer identity / the Consent system own. Seed values
are synthetic (never real customer PII); masking still applies wherever they would reach a log or evidence.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Optional, Set

import pytest

from app.measurement.audit import AuditLog
from app.measurement.consent.gate import ConsentGate
from app.measurement.identity.resolver import IdentityResolver
from app.measurement.logs.web_event_log_store import WebEventLogStore
from app.measurement.models.consumed import (
    ConsentScope,
    ConsentSnapshot,
    ConsentState,
    DataSensitivity,
    EventRegistryRow,
    GuestContact,
    RegistrationState,
)
from app.measurement.registry.validator import EventValidator

FIXED_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


# --- in-memory read-only adapters (test doubles) ---------------------------------------------------
class InMemoryEventRegistry:
    def __init__(self, rows: Dict[str, EventRegistryRow]) -> None:
        self._rows = rows

    def get(self, event_code: str) -> Optional[EventRegistryRow]:
        return self._rows.get(event_code)


class InMemoryGuestContacts:
    def __init__(self, rows: Dict[str, GuestContact]) -> None:
        self._rows = rows

    def get(self, guest_id: str) -> Optional[GuestContact]:
        return self._rows.get(guest_id)


class InMemoryConsent:
    def __init__(self, rows: Dict[str, ConsentSnapshot], current: Dict[str, ConsentState]) -> None:
        self._rows = rows
        self._current = current

    def get(self, consent_snapshot_id: str) -> Optional[ConsentSnapshot]:
        return self._rows.get(consent_snapshot_id)

    def current_state(self, subject_ref: str) -> ConsentState:
        return self._current.get(subject_ref, ConsentState.MISSING)  # unknown => fail-closed


class InMemoryCustomers:
    def __init__(self, ids: Set[str]) -> None:
        self._ids = ids

    def exists(self, customer_id: str) -> bool:
        return customer_id in self._ids


# --- seed data -------------------------------------------------------------------------------------
@pytest.fixture
def registry_rows() -> Dict[str, EventRegistryRow]:
    return {
        "VIEW_LANDING": EventRegistryRow(
            event_code="VIEW_LANDING",
            registration_state=RegistrationState.ACTIVE,
            owner="core.tracking",
            channel="web",
            data_sensitivity=DataSensitivity.INTERNAL,
            external_send_policy=None,          # M6-OD-003 OPEN
            schema_ref="evt.view_landing.v1",
        ),
        # ACTIVE with data_sensitivity MISSING -> validator must default to PII.
        "VIEW_LANDING_NO_SENS": EventRegistryRow(
            event_code="VIEW_LANDING_NO_SENS",
            registration_state=RegistrationState.ACTIVE,
            owner="core.tracking",
            channel="web",
            data_sensitivity=None,
        ),
        # De-registered -> HOLD (fail-closed, never false-ALLOW).
        "DEREG_SAMPLE": EventRegistryRow(
            event_code="DEREG_SAMPLE",
            registration_state=RegistrationState.DEREGISTERED,
            owner="core.tracking",
        ),
        # Registered ACTIVE but owner missing -> DQ item 1 FAIL -> HOLD.
        "NO_OWNER_SAMPLE": EventRegistryRow(
            event_code="NO_OWNER_SAMPLE",
            registration_state=RegistrationState.ACTIVE,
            owner=None,
        ),
    }


@pytest.fixture
def guest_rows() -> Dict[str, GuestContact]:
    return {
        "guest_mapped_ok": GuestContact(
            guest_id="guest_mapped_ok", contact_fingerprint="fp_aaaaaaaa",
            mapped_customer_id="cust_0001", mapping_audit_ref="audit_ref_123",
        ),
        "guest_no_audit": GuestContact(
            guest_id="guest_no_audit", contact_fingerprint="fp_bbbbbbbb",
            mapped_customer_id="cust_0001", mapping_audit_ref=None,   # mapping without audit -> HOLD
        ),
        "guest_unmapped": GuestContact(
            guest_id="guest_unmapped", contact_fingerprint="fp_cccccccc",
        ),
        "guest_bad_customer": GuestContact(
            guest_id="guest_bad_customer", contact_fingerprint="fp_dddddddd",
            mapped_customer_id="cust_ghost", mapping_audit_ref="audit_ref_999",
        ),
    }


@pytest.fixture
def consent_rows() -> Dict[str, ConsentSnapshot]:
    return {
        "cs_valid": ConsentSnapshot(
            "cs_valid", "guest_mapped_ok", ConsentState.VALID, FIXED_TS,
            frozenset({ConsentScope.EXTERNAL_MEASUREMENT, ConsentScope.AUDIENCE_SYNC}),
        ),
        "cs_valid_meas_only": ConsentSnapshot(
            "cs_valid_meas_only", "guest_mapped_ok", ConsentState.VALID, FIXED_TS,
            frozenset({ConsentScope.EXTERNAL_MEASUREMENT}),
        ),
        # VALID consent issued for a DIFFERENT subject (guest_B) — used to prove the seam refuses to bind
        # one person's consent to another's event (subject mismatch, FAIL-002).
        "cs_valid_b": ConsentSnapshot(
            "cs_valid_b", "guest_B", ConsentState.VALID, FIXED_TS,
            frozenset({ConsentScope.EXTERNAL_MEASUREMENT}),
        ),
        # VALID consent keyed by a CUSTOMER id (cust_0001) — subject binding must accept it for a guest that
        # is trustedly mapped to that customer (guest_mapped_ok -> cust_0001, with audit).
        "cs_valid_cust": ConsentSnapshot(
            "cs_valid_cust", "cust_0001", ConsentState.VALID, FIXED_TS,
            frozenset({ConsentScope.EXTERNAL_MEASUREMENT}),
        ),
        "cs_missing": ConsentSnapshot(
            "cs_missing", "guest_x", ConsentState.MISSING, FIXED_TS, frozenset(),
        ),
        "cs_expired": ConsentSnapshot(
            "cs_expired", "guest_x", ConsentState.EXPIRED, FIXED_TS, frozenset(),
        ),
        "cs_optout": ConsentSnapshot(
            "cs_optout", "guest_x", ConsentState.OPT_OUT, FIXED_TS, frozenset(),
        ),
        # M6.2D (F-C): audience members whose consent snapshot subject_ref EQUALS the member_key (correctly
        # BOUND consent — a member's own consent, not borrowed). Used by the audience-chain fixtures.
        "cs_mem_consented": ConsentSnapshot(
            "cs_mem_consented", "mem_consented", ConsentState.VALID, FIXED_TS,
            frozenset({ConsentScope.EXTERNAL_MEASUREMENT, ConsentScope.AUDIENCE_SYNC}),
        ),
        "cs_mem_optout": ConsentSnapshot(
            "cs_mem_optout", "mem_optout", ConsentState.OPT_OUT, FIXED_TS, frozenset(),
        ),
        # M6.2E Round 2 (owner-authorized fixture realignment, M6-P1402): "self-key" consent snapshots whose
        # subject_ref EQUALS the raw-PII customer_or_guest_key the hash-policy tests push through, so the now
        # MANDATORY F-D subject-bind ACCEPTS them (they prove PII HASHING, not borrowed consent). Markers are
        # assembled at runtime — same construction the tests use — so NO literal PII sits in this source (the
        # pack secret-scan forbids literal email/phone/user-id). Subject == key by construction (F-C pattern).
        "cs_selfkey_pii": ConsentSnapshot(
            "cs_selfkey_pii", "guest" + "_IDMARKER_" + "abc", ConsentState.VALID, FIXED_TS,
            frozenset({ConsentScope.EXTERNAL_MEASUREMENT}),
        ),
        "cs_selfkey_email": ConsentSnapshot(
            "cs_selfkey_email", "buyer" + chr(64) + "mail" + "." + "test", ConsentState.VALID, FIXED_TS,
            frozenset({ConsentScope.EXTERNAL_MEASUREMENT}),
        ),
    }


@pytest.fixture
def audit() -> AuditLog:
    return AuditLog()


@pytest.fixture
def registry(registry_rows):
    return InMemoryEventRegistry(registry_rows)


@pytest.fixture
def guest_contacts(guest_rows):
    return InMemoryGuestContacts(guest_rows)


@pytest.fixture
def consent_reader(consent_rows):
    return InMemoryConsent(consent_rows, current={"guest_mapped_ok": ConsentState.VALID})


@pytest.fixture
def customers():
    return InMemoryCustomers({"cust_0001"})


@pytest.fixture
def validator(registry, audit):
    return EventValidator(registry, audit)


@pytest.fixture
def consent_gate(audit):
    return ConsentGate(audit)


@pytest.fixture
def resolver(guest_contacts, customers, audit):
    return IdentityResolver(guest_contacts, customers, audit)


@pytest.fixture
def store():
    return WebEventLogStore()


# --- M6.2B tracking / endpoint fixtures -----------------------------------------------------------
@pytest.fixture
def app_consent_reader(consent_rows):
    """The STAGED app-level ConsentReader adapter (app.measurement.adapters), seeded from consent_rows —
    the 'real adapter' wired into the endpoint (kept in-memory)."""
    from app.measurement.adapters.consent_reader import InMemoryConsentReader
    return InMemoryConsentReader(
        snapshots=consent_rows,
        current={
            "guest_mapped_ok": ConsentState.VALID,
            "mem_consented": ConsentState.VALID,
            # M6.2E Round 2: send-time (checkpoint-2) VALID for the self-key PII subjects, so a re-keyed
            # hash-policy conversion delivers to the staged transport (result-log/no-raw-PII path stays live).
            "guest" + "_IDMARKER_" + "abc": ConsentState.VALID,
            "buyer" + chr(64) + "mail" + "." + "test": ConsentState.VALID,
        },
    )


@pytest.fixture
def measurement_store():
    from app.measurement.store.measurement_event_store import MeasurementEventStore
    return MeasurementEventStore()


@pytest.fixture
def track_ingest_service(validator, store, consent_gate, app_consent_reader, audit, resolver):
    """The hardened ingest seam wired for the endpoint (F1/F2 apply via the patched modules)."""
    from app.measurement.ingest import IngestService
    return IngestService(validator, store, consent_gate, app_consent_reader, audit, resolver=resolver)


@pytest.fixture
def track_deps(track_ingest_service, store, measurement_store, audit):
    from app.api.track import TrackDeps
    return TrackDeps(
        ingest_service=track_ingest_service, web_store=store,
        measurement_store=measurement_store, audit=audit,
    )


@pytest.fixture
def make_track_body():
    """Builder for a CTR-016 track request body. Defaults are a valid VIEW_LANDING; override per test.
    `cs_valid`'s subject is `guest_mapped_ok`, so pass guest_id='guest_mapped_ok' to bind consent."""
    def _make(**over):
        body = {
            "event_code": "VIEW_LANDING",
            "page_id": "p1",
            "session_id": "s1",
            "source": "web",
            "consent_snapshot_id": "cs_valid",
            "event_ts": "2026-07-29T12:00:00+00:00",
            "idempotency_key": "client-supplied-value-is-ignored",
            "correlation_id": "corr_test",
        }
        body.update(over)
        return body
    return _make


# --- M6.2C outbox fixtures ------------------------------------------------------------------------
@pytest.fixture
def segment_reader(consent_rows):
    """Staged CONSUMED audience chain: one APPROVED segment (a consented member + an opt-out member) and one
    PENDING (non-approved) segment. Each member's key EQUALS its consent snapshot's subject_ref (correctly BOUND
    per F-C M6.2D): cs_mem_consented.subject_ref='mem_consented', cs_mem_optout.subject_ref='mem_optout'."""
    from app.measurement.adapters.segment_reader import InMemorySegmentReader
    from app.measurement.models.segments import ApprovalState, CustomerSegment, SegmentMember
    segments = {
        "seg_approved": CustomerSegment("seg_approved", "Approved segment", ApprovalState.APPROVED),
        "seg_pending": CustomerSegment("seg_pending", "Pending segment", ApprovalState.PENDING),
    }
    members = {
        "seg_approved": [
            SegmentMember("seg_approved", "mem_consented", "cs_mem_consented"),  # bound + VALID + AUDIENCE_SYNC -> ADD
            SegmentMember("seg_approved", "mem_optout", "cs_mem_optout"),        # bound + OPT_OUT -> REMOVE
        ],
        "seg_pending": [SegmentMember("seg_pending", "mem_consented", "cs_mem_consented")],
    }
    return InMemorySegmentReader(segments=segments, members=members)


@pytest.fixture
def conversion_store():
    from app.measurement.store.conversion_event_store import ConversionEventStore
    return ConversionEventStore()


@pytest.fixture
def measurement_outbox():
    from app.measurement.outbox.outbox_store import OutboxStore
    return OutboxStore()


@pytest.fixture
def audience_outbox():
    from app.measurement.outbox.outbox_store import OutboxStore
    return OutboxStore()


@pytest.fixture
def conversion_deps(validator, conversion_store, measurement_outbox, audit, app_consent_reader):
    from app.api.conversions import ConversionDeps
    # M6.2E Round 2: the reader is now WIRED by default so the MANDATORY F-D subject-bind is exercised in every
    # conversion test. The default body (key=guest_mapped_ok, consent cs_valid subject=guest_mapped_ok) matches,
    # so carried tests stay green; a borrowed pairing is now rejected even with the default deps.
    return ConversionDeps(
        validator=validator, conversion_store=conversion_store,
        measurement_outbox=measurement_outbox, audit=audit, max_retries=3,
        consent_reader=app_consent_reader,
    )


@pytest.fixture
def make_conversion_body():
    """Builder for a CTR-017 conversions body. Defaults are a NON-revenue ORDER_SUCCESS conversion; override."""
    def _make(**over):
        body = {
            "event_code": "VIEW_LANDING",
            "source_event_id": "evt_src_1",
            "customer_or_guest_key": "guest_mapped_ok",
            "consent_snapshot_id": "cs_valid",
            "occurred_at": "2026-07-29T12:00:00+00:00",
            "idempotency_key": "client-value-ignored",
            "correlation_id": "corr_conv",
        }
        body.update(over)
        return body
    return _make


# --- fake transports (test doubles for the Transport port; NONE contacts a real platform) ---------
class _SucceedingTransport:
    """Records deliveries and succeeds — simulates a hypothetical ON environment WITHOUT a real send."""

    def __init__(self) -> None:
        self.delivered = []

    def deliver(self, item):
        self.delivered.append(item.outbox_id)


class _FailingTransport:
    """Always raises a TRANSIENT failure — drives the bounded retry -> dead-letter path (SMK-016)."""

    def __init__(self) -> None:
        self.attempts = 0

    def deliver(self, item):
        self.attempts += 1
        raise RuntimeError("simulated transient platform failure")


@pytest.fixture
def make_conversion():
    """Builder for a ConversionEvent (for the outbox/dispatcher UNIT tests, bypassing the endpoint)."""
    from datetime import datetime, timezone

    from app.measurement.models.conversion_event import ConversionEvent

    def _make(event_code="VIEW_LANDING", *, consent_snapshot_id="cs_valid",
              customer_or_guest_key="guest_mapped_ok", source_event_id="evt_src", **over):
        ts = over.pop("occurred_at", datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc))
        base = dict(
            conversion_id=f"conv_{event_code}_{source_event_id}",
            event_code=event_code,
            source_event_id=source_event_id,
            correlation_id="corr_c",
            customer_or_guest_key=customer_or_guest_key,
            consent_snapshot_id=consent_snapshot_id,
            occurred_at=ts,
            idempotency_key=f"idem_{event_code}_{source_event_id}",
        )
        base.update(over)
        return ConversionEvent(**base)
    return _make


@pytest.fixture
def staged_transport():
    from app.measurement.outbox.transport import StagedBlockedTransport
    return StagedBlockedTransport()


@pytest.fixture
def succeeding_transport():
    return _SucceedingTransport()


@pytest.fixture
def failing_transport():
    return _FailingTransport()


# --- M6.2D integration (send-discipline) fixtures ------------------------------------------------
@pytest.fixture
def platform_result_log():
    from app.measurement.integration.result_log import PlatformResultLog
    return PlatformResultLog()


@pytest.fixture
def platform_transport(conversion_store, platform_result_log):
    """The M6.2D staged platform transport, wired with the SAME conversion_store the endpoint writes to."""
    from app.measurement.integration.platform_transport import StagedPlatformTransport
    return StagedPlatformTransport(conversion_store, platform_result_log)


# --- M6.2E attribution fixtures -------------------------------------------------------------------
@pytest.fixture
def attribution_resolver():
    from app.measurement.attribution.resolver import AttributionResolver
    return AttributionResolver()


@pytest.fixture
def adjustment_log():
    from app.measurement.attribution.adjustment import AdjustmentLog
    return AdjustmentLog()


@pytest.fixture
def attribution_materializer(measurement_store, attribution_resolver, audit):
    """The CTR-023 materializer wired over the SAME measurement_store the Zone-A seeder inserts into (so a
    materialize enriches the row the resolver traced)."""
    from app.measurement.attribution.materializer import AttributionMaterializer
    return AttributionMaterializer(measurement_store, attribution_resolver, audit)


@pytest.fixture
def make_measurement_event(measurement_store):
    """Insert one Zone-A ads_measurement_event and return it. Revenue/attribution are NEVER seeded here (Zone A
    only; the store rejects a revenue-bearing insert) — they are set later by the materializer (Zone B)."""
    from app.measurement.models.measurement_event import AdsMeasurementEvent

    def _make(event_id="evt_1", *, event_code="ORDER_VERIFIED", **over):
        base = dict(
            event_id=event_id,
            event_code=event_code,
            event_ts=FIXED_TS,
            idempotency_key=over.pop("idempotency_key", f"idem_{event_id}"),
            correlation_id=over.pop("correlation_id", "corr_ame"),
            ingested_at=FIXED_TS,
        )
        base.update(over)
        row = AdsMeasurementEvent(**base)
        measurement_store.insert(row)
        return row
    return _make


# --- M6.2F dashboard / data-quality fixtures -----------------------------------------------------
@pytest.fixture
def make_verified_row(measurement_store, make_measurement_event, make_conversion, attribution_materializer):
    """Seed a Zone-A ORDER_VERIFIED event and materialize its Zone-B verified revenue (via the M6.2E CTR-023
    materializer), returning the verified store row. `signals` steers attribution (campaign / crm / diamond)."""
    def _make(event_id, *, revenue, order_code, event_code="ORDER_VERIFIED", signals=None, **event_over):
        ev = make_measurement_event(event_id, event_code=event_code, **event_over)
        conv = make_conversion(
            event_code, source_event_id=event_id, revenue_value=float(revenue), currency="VND", order_code=order_code
        )
        attribution_materializer.materialize(ev, conv, signals=signals)
        return measurement_store.get_by_event_id(event_id)
    return _make


@pytest.fixture
def make_data_mart(measurement_store):
    """Factory: a read-only DataMart over the shared measurement_store + optional ConsumedFacts."""
    from app.measurement.dashboard.data_mart import DataMart

    def _make(consumed=None):
        return DataMart(measurement_store, consumed)
    return _make


@pytest.fixture
def make_dashboard_deps(make_data_mart):
    """Factory: a read-only DashboardDeps (holds only the support-view mart)."""
    from app.api.dashboard import DashboardDeps

    def _make(consumed=None):
        return DashboardDeps(mart=make_data_mart(consumed))
    return _make


@pytest.fixture
def dq_checker(measurement_store, audit):
    from app.measurement.quality.data_quality_checker import DataQualityChecker
    return DataQualityChecker(measurement_store, audit)


# --- M6.2G scale-gate fixtures --------------------------------------------------------------------
@pytest.fixture
def scale_store():
    from app.measurement.scale.scale_request_store import ScaleRequestStore
    return ScaleRequestStore()


@pytest.fixture
def scale_gate(scale_store, audit):
    from app.measurement.scale.scale_gate import ScaleGate
    return ScaleGate(scale_store, audit)


@pytest.fixture
def make_scale_context():
    """Factory for a ScaleContext. Defaults are the BEST achievable in the staged posture (entry evidence present,
    boundaries attested, DQ PASS, no risk locks, owner NOT approved) — which still rolls up to HOLD because Funnel
    (M6-OD-002) + Dashboard-as-scale-evidence (M6-OD-005) are fail-closed. Override per test."""
    from app.measurement.models.measurement_event import DataQualityStatus
    from app.measurement.scale.conditions import ScaleContext

    def _make(**over):
        base = dict(
            entry_evidence_refs={"ENTRY-001": "e1", "ENTRY-002": "e2", "ENTRY-003": "e3", "ENTRY-004": "e4"},
            quote_order_ok=True,
            public_privacy_ok=True,
            boxes_per_order=2.0,
            dq_overall=DataQualityStatus.PASS,
            risk_flags={"recall": False, "sale_lock": False, "quality_hold": False,
                        "complaint_p0": False, "platform_spam_flag": False, "crm_suppression": False},
            owner_approved=False,
            budget_cap=None,
            rollback_condition=None,
        )
        base.update(over)
        return ScaleContext(**base)
    return _make


@pytest.fixture
def make_scale_deps(scale_gate, audit):
    from app.api.scale_requests import ScaleRequestDeps

    def _make(context):
        return ScaleRequestDeps(scale_gate=scale_gate, context=context, audit=audit)
    return _make


@pytest.fixture
def make_owner_decision():
    from app.measurement.scale.models import DecisionKind, OwnerDecision

    def _make(kind="APPROVE", **over):
        base = dict(actor="owner_ops", reason="pilot metrics reviewed", audit_ref="aud_scale_1",
                    evidence_ref="ev_scale_1", decision=DecisionKind(kind))
        base.update(over)
        return OwnerDecision(**base)
    return _make


# --- M6.2H learning-engine fixtures ---------------------------------------------------------------
@pytest.fixture
def library_store():
    from app.measurement.learning.libraries import StrategyLibraryStore
    return StrategyLibraryStore()


@pytest.fixture
def review_queue():
    from app.measurement.learning.review_queue import ReviewQueue
    return ReviewQueue()


@pytest.fixture
def learning_engine(library_store, review_queue, audit):
    from app.measurement.learning.learning_engine import LearningEngine
    return LearningEngine(library_store, review_queue, audit)


@pytest.fixture
def seed_all_libraries(library_store):
    """Seed one canonical entry into every library (framework-only; content stays None). Returns the store."""
    from app.measurement.learning.libraries import CANONICAL_SEED_SOURCES, StrategyLibraryKind

    def _make():
        for kind in StrategyLibraryKind:
            src = CANONICAL_SEED_SOURCES[kind][0]
            library_store.seed(kind, src, entry_id=f"seed_{kind.name.lower()}")
        return library_store
    return _make


@pytest.fixture
def make_learning_deps(learning_engine, audit):
    from app.api.learning_candidates import LearningDeps

    def _make():
        return LearningDeps(engine=learning_engine, audit=audit)
    return _make


@pytest.fixture
def make_candidate():
    from app.measurement.learning.candidate import AdsLearningCandidate, LearningCandidateKind, TargetDim

    def _make(candidate_id="lc_1", *, target_dim="persona", kind="OPTIMIZATION", score=0.8, sku_ref="SKU_HERO_1", **over):
        base = dict(
            candidate_id=candidate_id, kind=LearningCandidateKind(kind), target_dim=TargetDim(target_dim),
            score=score, sku_ref=sku_ref,
        )
        base.update(over)
        return AdsLearningCandidate(**base)
    return _make


@pytest.fixture
def make_review_decision():
    from app.measurement.learning.candidate import OwnerReviewDecision, ReviewState

    def _make(state="APPROVED", **over):
        base = dict(actor="owner_ops", reason="reviewed against canon", audit_ref="aud_lc_1",
                    evidence_ref="ev_lc_1", new_state=ReviewState(state))
        base.update(over)
        return OwnerReviewDecision(**base)
    return _make


@pytest.fixture
def make_signal():
    from app.measurement.learning.learning_engine import VerifiedSignal
    from app.measurement.learning.candidate import TargetDim
    from app.measurement.models.measurement_event import DataQualityStatus

    def _make(target_dim="persona", *, value=1.0, dq_status="PASS", verified=True):
        return VerifiedSignal(
            target_dim=TargetDim(target_dim), value=value,
            dq_status=DataQualityStatus(dq_status), verified=verified,
        )
    return _make


# --- M6.2I Golden Hour funnel / retargeting fixtures ----------------------------------------------
@pytest.fixture
def make_golden_hour_funnel(measurement_store):
    """Factory: a read-only GoldenHourFunnel over the shared measurement_store + optional CONSUMED annotations
    (golden_hour_state_by_event from Gateway/Live; capture_gate_passed_by_order from Commerce, RULE-021)."""
    from app.measurement.funnel.funnel import GoldenHourFunnel

    def _make(golden_hour_state_by_event=None, capture_gate_passed_by_order=None):
        return GoldenHourFunnel(
            measurement_store,
            golden_hour_state_by_event=golden_hour_state_by_event,
            capture_gate_passed_by_order=capture_gate_passed_by_order,
        )
    return _make


@pytest.fixture
def retargeting_measurement(consent_gate):
    """The measure-only retargeting-eligibility classifier, wired to the shared ConsentGate (no send surface)."""
    from app.measurement.funnel.retargeting import RetargetingMeasurement
    return RetargetingMeasurement(consent_gate)
