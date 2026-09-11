"""M6.2C: the audience chain (RULE-004/002/012). Audience sync is enqueued ONLY from an APPROVED segment +
consented members; a non-approved segment enqueues nothing; an opt-out member becomes a REMOVE (fail-closed).
Membership is read for SYNC ONLY — never a trigger owner (RULE-012). member_key is masked on export (O1).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.measurement.models.audience_outbox import AudienceOperation, AudiencePlatform
from app.measurement.models.measurement_outbox import OutboxStatus
from app.measurement.outbox.audience_dispatcher import AudienceDispatcher
from app.measurement.outbox.enqueue import enqueue_audience_sync

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def _enqueue(segment_id, segment_reader, app_consent_reader, consent_gate, audience_outbox, audit):
    return enqueue_audience_sync(
        segment_id, reader=segment_reader, consent_reader=app_consent_reader, consent_gate=consent_gate,
        store=audience_outbox, audit=audit, platform=AudiencePlatform.META_AUDIENCE, max_retries=3,
    )


def test_non_approved_segment_enqueues_nothing(segment_reader, app_consent_reader, consent_gate, audience_outbox, audit):
    out = _enqueue("seg_pending", segment_reader, app_consent_reader, consent_gate, audience_outbox, audit)
    assert out == [] and len(audience_outbox) == 0
    assert audit.find("AUDIENCE_SEGMENT_NOT_APPROVED")


def test_approved_segment_add_and_remove_by_consent(segment_reader, app_consent_reader, consent_gate, audience_outbox, audit):
    out = _enqueue("seg_approved", segment_reader, app_consent_reader, consent_gate, audience_outbox, audit)
    ops = {row.member_key: row.operation for row, _created in out}
    # F-C (M6.2D): member_key == consent subject_ref, so the member's OWN consent decides ADD vs REMOVE.
    assert ops["mem_consented"] is AudienceOperation.ADD      # cs_mem_consented: bound + VALID + AUDIENCE_SYNC
    assert ops["mem_optout"] is AudienceOperation.REMOVE      # cs_mem_optout: bound + OPT_OUT -> fail-closed REMOVE
    assert len(audience_outbox) == 2


def test_dispatch_add_and_remove_with_injected_transport(
    segment_reader, app_consent_reader, consent_gate, audience_outbox, audit, succeeding_transport
):
    _enqueue("seg_approved", segment_reader, app_consent_reader, consent_gate, audience_outbox, audit)
    AudienceDispatcher(audience_outbox, succeeding_transport, consent_gate, app_consent_reader, audit).run_once(now=_TS)
    # ADD (mem_consented, bound consent VALID at send) delivered; REMOVE (mem_optout) always proceeds (fail-closed)
    assert audience_outbox.count_status(OutboxStatus.SENT) == 2
    assert len(succeeding_transport.delivered) == 2


def test_member_key_masked_on_export(segment_reader, app_consent_reader, consent_gate, audience_outbox, audit):
    _enqueue("seg_approved", segment_reader, app_consent_reader, consent_gate, audience_outbox, audit)
    blob = " ".join(
        f"{r.action} {r.reason} {r.event_code} {r.subject_masked} {r.detail}" for r in audit.records
    )
    assert "mem_consented" not in blob, "raw member_key must not appear in the audit sink (O1)"
    assert "mem_optout" not in blob
