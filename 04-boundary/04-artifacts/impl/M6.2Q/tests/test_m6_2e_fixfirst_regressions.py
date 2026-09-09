"""M6.2E fix-first BINDING regressions (per M6-P1400 / the M6-P1309 sign-off):

  F-D — measurement-path BORROWED consent: a conversion citing ANOTHER subject's valid consent is refused
        (bind customer_or_guest_key <-> consent snapshot subject_ref at the /conversions seam; mirrors F-C).
        Round 2: the bind is MANDATORY — enforced even with the default (reader-wired) deps; a missing reader
        fails closed (reject), never skips.
  F-E — the platform event_id join was UNESCAPED -> non-injective -> two distinct events could share an
        event_id -> platform UNDER-COUNT. Escaped join -> injective.
  F-F — a hostile consent snapshot whose subject_ref PROPERTY raises (or returns a str-subclass with a raising
        __eq__/__ne__, or an object with a raising __class__) must fail-closed (deny), never crash. Covers both
        dispatchers (run_once), the /conversions bind (FF-1), and the audience enqueue (FF-2).
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.api.conversions import ConversionDeps, handle_conversions_request
from app.measurement.integration.payload import platform_event_id
from app.measurement.models.consumed import ConsentScope, ConsentState
from app.measurement.outbox.audience_dispatcher import AudienceDispatcher
from app.measurement.models.audience_outbox import AudienceOperation, AudienceOutboxItem, AudiencePlatform
from app.measurement.outbox.enqueue import enqueue_measurement
from app.measurement.outbox.measurement_dispatcher import MeasurementDispatcher

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


# ================================================================ F-D — borrowed consent at /conversions
def test_fd_conversion_borrowed_consent_refused_bound_accepted(
    validator, conversion_store, measurement_outbox, audit, app_consent_reader, make_conversion_body
):
    deps = ConversionDeps(
        validator=validator, conversion_store=conversion_store, measurement_outbox=measurement_outbox,
        audit=audit, max_retries=3, consent_reader=app_consent_reader,
    )
    # BORROWED: cs_valid_b's subject is guest_B, but the conversion's subject is guest_mapped_ok -> refuse
    borrowed = handle_conversions_request(
        make_conversion_body(consent_snapshot_id="cs_valid_b", customer_or_guest_key="guest_mapped_ok"), deps
    )
    assert borrowed.error_code == "CONSENT_MISSING_OR_INVALID"
    assert len(conversion_store) == 0 and len(measurement_outbox) == 0

    # BOUND: cs_valid's subject IS guest_mapped_ok -> accepted
    ok = handle_conversions_request(
        make_conversion_body(consent_snapshot_id="cs_valid", customer_or_guest_key="guest_mapped_ok"), deps
    )
    assert ok.status == "CREATED"


def test_fd_default_deps_reject_borrowed_accept_matching(
    conversion_deps, make_conversion_body, conversion_store, measurement_outbox
):
    """Round 2 probe §3.1: F-D is MANDATORY with the DEFAULT (reader-wired) deps. An attacker key citing a
    victim's VALID consent is REJECTED (no longer CREATED); a matching subject is CREATED."""
    borrowed = handle_conversions_request(
        make_conversion_body(customer_or_guest_key="attacker_XYZ", consent_snapshot_id="cs_valid"), conversion_deps
    )  # cs_valid.subject == guest_mapped_ok != attacker_XYZ
    assert borrowed.error_code == "CONSENT_MISSING_OR_INVALID"
    assert len(conversion_store) == 0 and len(measurement_outbox) == 0

    ok = handle_conversions_request(make_conversion_body(), conversion_deps)  # key==subject==guest_mapped_ok
    assert ok.status == "CREATED"


def test_fd_no_reader_fails_closed(
    validator, conversion_store, measurement_outbox, audit, make_conversion_body
):
    """Round 2: a missing consent_reader is a WIRING ERROR, not an opt-out — the mandatory bind cannot resolve a
    subject, so it fails CLOSED (reject), never skips (contrast the removed Round-1 'skipped' behavior)."""
    deps = ConversionDeps(
        validator=validator, conversion_store=conversion_store, measurement_outbox=measurement_outbox,
        audit=audit, max_retries=3,   # consent_reader defaults None -> fail-closed
    )
    res = handle_conversions_request(
        make_conversion_body(consent_snapshot_id="cs_valid", customer_or_guest_key="guest_mapped_ok"), deps
    )
    assert res.error_code == "CONSENT_MISSING_OR_INVALID"
    assert len(conversion_store) == 0 and len(measurement_outbox) == 0


# ================================================================ F-E — injective platform event_id
def test_fe_platform_event_id_is_injective():
    # (source_event_id, event_code) pairs that COLLIDE under an unescaped "a|b" join
    a = platform_event_id("x|y", "z")
    b = platform_event_id("x", "y|z")
    assert a != b, "distinct events must not share a platform event_id (F-E under-count guard)"
    # the cross-platform SHARED-id property is preserved for normal ids (same inputs -> same id)
    assert platform_event_id("evt_1", "ORDER_VERIFIED") == platform_event_id("evt_1", "ORDER_VERIFIED")


# ================================================================ F-F — hostile raising subject_ref property
class _RaisingSubjectSnap:
    consent_state = ConsentState.VALID
    consent_scope = frozenset({ConsentScope.EXTERNAL_MEASUREMENT, ConsentScope.AUDIENCE_SYNC})

    @property
    def subject_ref(self):
        raise RuntimeError("hostile subject_ref property")


class _EvilReader:
    def get(self, _id):
        return _RaisingSubjectSnap()

    def current_state(self, _subject):
        return ConsentState.VALID


def test_ff_measurement_dispatcher_survives_raising_subject(
    make_conversion, measurement_outbox, consent_gate, audit, succeeding_transport
):
    conv = make_conversion("VIEW_LANDING", consent_snapshot_id="cs_evil", customer_or_guest_key="subjX")
    enqueue_measurement(conv, measurement_outbox, max_retries=3)
    disp = MeasurementDispatcher(
        measurement_outbox, succeeding_transport, consent_gate, _EvilReader(), audit,
        dq_status=lambda item: "PASS",
    )
    disp.run_once(now=_TS)   # must NOT raise (F-F)
    assert succeeding_transport.delivered == [], "a raising subject_ref must fail-closed (no send), not crash"


def test_ff_audience_dispatcher_survives_raising_subject(
    consent_gate, audience_outbox, audit, succeeding_transport
):
    item = AudienceOutboxItem(
        outbox_id="a_evil", segment_id="seg", member_key="member_A", platform=AudiencePlatform.META_AUDIENCE,
        operation=AudienceOperation.ADD, dedup_key="dk_evil", payload_ref="p", consent_snapshot_id="cs_evil",
        max_retries=3,
    )
    audience_outbox.enqueue(item)
    AudienceDispatcher(audience_outbox, succeeding_transport, consent_gate, _EvilReader(), audit).run_once(now=_TS)
    assert succeeding_transport.delivered == [], "a raising subject_ref must fail-closed (no sync), not crash"


# --- F-F round 2 (adversarial review): a str-SUBCLASS with raising comparison, and a raising __class__ ----
class _EvilStr(str):
    """A str subclass whose comparison RAISES — must never reach the audience bind's `subject != member_key`."""

    def __eq__(self, other):
        raise RuntimeError("hostile __eq__")

    def __ne__(self, other):
        raise RuntimeError("hostile __ne__")

    __hash__ = str.__hash__


class _SubclassSubjectSnap:
    consent_state = ConsentState.VALID
    consent_scope = frozenset({ConsentScope.AUDIENCE_SYNC})

    @property
    def subject_ref(self):
        return _EvilStr("member_A")


class _RaisingClassObj:
    @property
    def __class__(self):
        raise RuntimeError("hostile __class__")


class _RaisingClassSubjectSnap:
    consent_state = ConsentState.VALID
    consent_scope = frozenset({ConsentScope.EXTERNAL_MEASUREMENT})

    @property
    def subject_ref(self):
        return _RaisingClassObj()


def _reader_returning(snap):
    class _R:
        def get(self, _id):
            return snap

        def current_state(self, _s):
            return ConsentState.VALID
    return _R()


def test_ff_audience_survives_str_subclass_raising_comparison(
    consent_gate, audience_outbox, audit, succeeding_transport
):
    """safe_subject_ref must return a PLAIN str or None, never a str-subclass, so the ADD bind's
    `subject != member_key` can't invoke a hostile __ne__ and crash run_once."""
    item = AudienceOutboxItem(
        outbox_id="a_sub", segment_id="seg", member_key="member_A", platform=AudiencePlatform.META_AUDIENCE,
        operation=AudienceOperation.ADD, dedup_key="dk_sub", payload_ref="p", consent_snapshot_id="cs_sub",
        max_retries=3,
    )
    audience_outbox.enqueue(item)
    AudienceDispatcher(
        audience_outbox, succeeding_transport, consent_gate, _reader_returning(_SubclassSubjectSnap()), audit
    ).run_once(now=_TS)   # must NOT raise
    assert succeeding_transport.delivered == [], "a str-subclass subject must fail-closed, not crash"


def test_ff_measurement_survives_raising_class_property(
    make_conversion, measurement_outbox, consent_gate, audit, succeeding_transport
):
    """A subject_ref whose object has a raising __class__ must not crash: safe_subject_ref uses type() (the C
    type slot), never isinstance()/__class__. F-F's guarantee is NO CRASH — the drain completes; whether the
    item delivers depends on the (valid) consent, which is not F-F's concern."""
    conv = make_conversion("VIEW_LANDING", consent_snapshot_id="cs_cls", customer_or_guest_key="subjX")
    enqueue_measurement(conv, measurement_outbox, max_retries=3)
    processed = MeasurementDispatcher(
        measurement_outbox, succeeding_transport, consent_gate, _reader_returning(_RaisingClassSubjectSnap()),
        audit, dq_status=lambda item: "PASS",
    ).run_once(now=_TS)   # must NOT raise
    assert len(processed) == 2, "the batch drain must complete (PIXEL+CAPI, no crash) despite a hostile __class__"


# --- FF-1 / FF-2 (Round 2): the two NEW bind sites must also route subject via safe_subject_ref ----------
_HOSTILE_SNAPS = [_RaisingSubjectSnap, _SubclassSubjectSnap, _RaisingClassSubjectSnap]


@pytest.mark.parametrize("snap_cls", _HOSTILE_SNAPS)
def test_ff1_conversions_bind_survives_hostile_subject(
    validator, conversion_store, measurement_outbox, audit, make_conversion_body, snap_cls
):
    """FF-1: the /conversions F-D bind must read subject via safe_subject_ref — a hostile subject_ref (raising
    access, str-subclass raising __ne__, or raising __class__) must fail-closed (reject), never crash."""
    deps = ConversionDeps(
        validator=validator, conversion_store=conversion_store, measurement_outbox=measurement_outbox,
        audit=audit, max_retries=3, consent_reader=_reader_returning(snap_cls()),
    )
    res = handle_conversions_request(   # must NOT raise
        make_conversion_body(consent_snapshot_id="cs_hostile", customer_or_guest_key="guest_mapped_ok"), deps
    )
    assert res.error_code == "CONSENT_MISSING_OR_INVALID"
    assert len(conversion_store) == 0 and len(measurement_outbox) == 0


@pytest.mark.parametrize("snap_cls", _HOSTILE_SNAPS)
def test_ff2_audience_enqueue_survives_hostile_subject(consent_gate, audience_outbox, audit, snap_cls):
    """FF-2: enqueue_audience_sync's member-consent bind must read subject via safe_subject_ref — a hostile
    subject_ref must fail-closed to REMOVE, never crash the enqueue."""
    from app.measurement.adapters.segment_reader import InMemorySegmentReader
    from app.measurement.models.segments import ApprovalState, CustomerSegment, SegmentMember
    from app.measurement.outbox.enqueue import enqueue_audience_sync
    reader = InMemorySegmentReader(
        segments={"seg": CustomerSegment("seg", "s", ApprovalState.APPROVED)},
        members={"seg": [SegmentMember("seg", "member_A", "cs_hostile")]},
    )
    out = enqueue_audience_sync(   # must NOT raise
        "seg", reader=reader, consent_reader=_reader_returning(snap_cls()), consent_gate=consent_gate,
        store=audience_outbox, audit=audit, platform=AudiencePlatform.META_AUDIENCE, max_retries=3,
    )
    ops = {row.member_key: row.operation for row, _created in out}
    assert ops["member_A"] is AudienceOperation.REMOVE, "a hostile subject must fail-closed to REMOVE, not crash"
