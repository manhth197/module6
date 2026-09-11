"""M6.2D fix-first BINDING regressions (per M6-P1300, from the M6.2C review M6-P1209): the consent fail-OPEN
residuals F-B (set-subclass __contains__), F-C (borrowed audience consent), F-A (reader exception at send).
These are armed-not-fired only because external_send=OFF; the deadline is before external_send is EVER ON.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.measurement.adapters.consent_reader import InMemoryConsentReader
from app.measurement.consent.gate import ConsentGate
from app.measurement.models.audience_outbox import AudienceOperation, AudienceOutboxItem, AudiencePlatform
from app.measurement.models.consumed import ConsentScope, ConsentSnapshot, ConsentState
from app.measurement.outbox.audience_dispatcher import AudienceDispatcher
from app.measurement.outbox.enqueue import enqueue_measurement
from app.measurement.outbox.measurement_dispatcher import MeasurementDispatcher

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


# ================================================================ F-B — set-subclass __contains__ fail-OPEN
class _EvilScopeSet(set):
    """A set-SUBCLASS whose __contains__ LIES (claims every scope is granted) — the F-B attack."""

    def __contains__(self, _item):
        return True


def test_fb_set_subclass_contains_override_is_denied(audit):
    gate = ConsentGate(audit)
    snap = ConsentSnapshot("cs_e", "subjX", ConsentState.VALID, _TS, frozenset({ConsentScope.CRM}))
    # replace consent_scope (post-construction) with an evil set-subclass holding only {CRM}
    object.__setattr__(snap, "consent_scope", _EvilScopeSet({ConsentScope.CRM}))
    # EXTERNAL_MEASUREMENT is NOT a real member; the evil __contains__ would grant it (fail-OPEN). F-B tests
    # membership on a materialized real frozenset -> DENY.
    assert gate.evaluate(snap, ConsentScope.EXTERNAL_MEASUREMENT) is False
    assert audit.find("CONSENT_SCOPE_NOT_GRANTED")


# ================================================================ F-C — borrowed audience consent
def test_fc_enqueue_borrowed_consent_is_remove_not_add(consent_gate, audience_outbox, audit):
    from app.measurement.adapters.segment_reader import InMemorySegmentReader
    from app.measurement.models.segments import ApprovalState, CustomerSegment, SegmentMember
    from app.measurement.outbox.enqueue import enqueue_audience_sync
    borrowed = ConsentSnapshot("cs_borrow", "member_B", ConsentState.VALID, _TS, frozenset({ConsentScope.AUDIENCE_SYNC}))
    reader = InMemorySegmentReader(
        segments={"seg": CustomerSegment("seg", "s", ApprovalState.APPROVED)},
        members={"seg": [SegmentMember("seg", "member_A", "cs_borrow")]},   # member_A references member_B's consent
    )
    creader = InMemoryConsentReader(snapshots={"cs_borrow": borrowed}, current={"member_B": ConsentState.VALID})
    out = enqueue_audience_sync(
        "seg", reader=reader, consent_reader=creader, consent_gate=consent_gate, store=audience_outbox,
        audit=audit, platform=AudiencePlatform.META_AUDIENCE, max_retries=3,
    )
    ops = {row.member_key: row.operation for row, _created in out}
    assert ops["member_A"] is AudienceOperation.REMOVE, "borrowed consent must not yield an ADD (F-C)"


def test_fc_dispatcher_blocks_add_with_borrowed_consent(consent_gate, audience_outbox, audit, succeeding_transport):
    borrowed = ConsentSnapshot("cs_borrow2", "member_B", ConsentState.VALID, _TS, frozenset({ConsentScope.AUDIENCE_SYNC}))
    creader = InMemoryConsentReader(snapshots={"cs_borrow2": borrowed}, current={"member_B": ConsentState.VALID})
    item = AudienceOutboxItem(
        outbox_id="a_borrow", segment_id="seg", member_key="member_A", platform=AudiencePlatform.META_AUDIENCE,
        operation=AudienceOperation.ADD, dedup_key="dk_b", payload_ref="p", consent_snapshot_id="cs_borrow2",
        max_retries=3,
    )
    audience_outbox.enqueue(item)
    AudienceDispatcher(audience_outbox, succeeding_transport, consent_gate, creader, audit).run_once(now=_TS)
    assert succeeding_transport.delivered == [], "a borrowed-consent ADD must never be synced (F-C)"
    assert audit.find("SYNC_BLOCKED_CONSENT_SUBJECT_MISMATCH")


# ================================================================ F-A — reader exception at send is fail-closed
class _RaisingCurrentStateReader:
    def get(self, _id):
        return ConsentSnapshot("cs_r", "subjX", ConsentState.VALID, _TS, frozenset({ConsentScope.EXTERNAL_MEASUREMENT}))

    def current_state(self, _subject):
        raise RuntimeError("consent store down at send time")


def test_fa_reader_exception_at_send_denies_not_crashes(
    make_conversion, measurement_outbox, consent_gate, audit, succeeding_transport
):
    conv = make_conversion("VIEW_LANDING", consent_snapshot_id="cs_r", customer_or_guest_key="subjX")
    enqueue_measurement(conv, measurement_outbox, max_retries=3)
    disp = MeasurementDispatcher(
        measurement_outbox, succeeding_transport, consent_gate, _RaisingCurrentStateReader(), audit,
        dq_status=lambda item: "PASS",
    )
    disp.run_once(now=_TS)   # must NOT raise
    assert succeeding_transport.delivered == [], "a reader failure at send must fail-closed (deny), not send"
    assert audit.find("SEND_BLOCKED_CONSENT")
