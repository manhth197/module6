"""Official smoke — slice M6.2C — M6-SMK-002 (doc ADS-P0-002), outbox / external-sync flavor.

Authored by TESTER in M6-P1203 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1204
(TESTER_RUN -> 04-artifacts/test-reports/M6.2C/SMOKE_RESULTS.md). Governance is immutable here:
global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract line 402):

    Kịch bản (verbatim):          "Event hợp lệ nhưng thiếu consent"
    Kết quả phải đạt (verbatim):  "Không external measurement, không audience sync"

M6.2C binds SMK-002 to the OUTBOX / external-sync separation. Consent is a TWO-checkpoint gate (RULE-002):
referenced at conversion/enqueue time (checkpoint 1) and RE-VALIDATED at dispatch (checkpoint 2). A
consent-invalid item is a policy-block -> terminal DEAD_LETTER, and the transport is NEVER called — so NO
external MEASUREMENT payload leaves, and on the audience chain a non-consented member is never an ADD (it is a
fail-closed REMOVE), so NO audience SYNC-in happens. The (injected) transport here is a test double that WOULD
succeed, which is exactly what makes "not delivered" meaningful. Prevents M6-FAIL-002 (consent violation).
RULE-002 / RULE-004. All ids synthetic; identity refs are masked on export (O1). Reuses the shared conftest
fixtures (make_conversion, measurement_outbox, audience_outbox, segment_reader, consent_gate,
app_consent_reader, audit, succeeding_transport).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.measurement.models.audience_outbox import AudienceOperation, AudiencePlatform
from app.measurement.models.measurement_outbox import OutboxStatus
from app.measurement.outbox.enqueue import enqueue_audience_sync, enqueue_measurement
from app.measurement.outbox.measurement_dispatcher import MeasurementDispatcher

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def _dispatcher(store, transport, consent_gate, reader, audit):
    # dq_status PASS so data-quality is not what blocks — the CONSENT checkpoint is what we are proving.
    return MeasurementDispatcher(store, transport, consent_gate, reader, audit, dq_status=lambda item: "PASS")


# --- primary smoke: scenario verbatim, BOTH clauses (no external measurement, no audience sync) ---
def test_smk_002_missing_consent_no_external_measurement_no_audience_sync(
    make_conversion, measurement_outbox, audience_outbox, segment_reader,
    consent_gate, app_consent_reader, audit, succeeding_transport,
):
    """M6-SMK-002 "Event hợp lệ nhưng thiếu consent" -> "Không external measurement, không audience sync".

    (a) MEASUREMENT: a VALID conversion (VIEW_LANDING) whose consent is MISSING is dispatched with a transport
        that WOULD succeed — yet nothing is delivered (policy-block -> DEAD_LETTER, transport never called),
        audited SEND_BLOCKED_CONSENT. No external measurement leaves.
    (b) AUDIENCE: on an APPROVED segment, a non-consented (opt-out) member is a fail-closed REMOVE, never an
        ADD — no audience sync-in for a subject without valid AUDIENCE_SYNC consent.
    """
    # (a) no external measurement
    conv = make_conversion("VIEW_LANDING", consent_snapshot_id="cs_missing", customer_or_guest_key="guest_x")
    enqueue_measurement(conv, measurement_outbox, max_retries=3)          # PIXEL + CAPI rows
    _dispatcher(measurement_outbox, succeeding_transport, consent_gate, app_consent_reader, audit).run_once(now=_TS)
    assert succeeding_transport.delivered == [], "no external measurement send without valid consent"
    assert measurement_outbox.count_status(OutboxStatus.SENT) == 0
    assert audit.find("SEND_BLOCKED_CONSENT"), "the consent block at dispatch must be audited"

    # (b) no audience sync (a non-consented member is REMOVE, not ADD)
    out = enqueue_audience_sync(
        "seg_approved", reader=segment_reader, consent_reader=app_consent_reader, consent_gate=consent_gate,
        store=audience_outbox, audit=audit, platform=AudiencePlatform.META_AUDIENCE, max_retries=3,
    )
    ops = {row.member_key: row.operation for row, _created in out}
    assert ops["mem_optout"] is AudienceOperation.REMOVE, "no audience sync (ADD) for a non-consented member"
    assert ops["mem_consented"] is AudienceOperation.ADD, "a consented member IS an ADD (discrimination)"


# --- negative / fail-closed companions ------------------------------------------------------------
def test_smk_002_neg_consent_lapsed_at_send_is_blocked(
    make_conversion, measurement_outbox, consent_gate, app_consent_reader, audit, succeeding_transport
):
    """Checkpoint 2 (send-time): cs_valid_b was VALID at event time (subject guest_B) but its current consent
    state is not VALID at send — the dispatch-time re-validation blocks it, nothing delivered, audited."""
    conv = make_conversion("VIEW_LANDING", consent_snapshot_id="cs_valid_b", customer_or_guest_key="guest_B")
    enqueue_measurement(conv, measurement_outbox, max_retries=3)
    _dispatcher(measurement_outbox, succeeding_transport, consent_gate, app_consent_reader, audit).run_once(now=_TS)
    assert succeeding_transport.delivered == []
    assert audit.find("SEND_BLOCKED_CONSENT")


def test_smk_002_neg_non_approved_segment_enqueues_no_audience_sync(
    segment_reader, app_consent_reader, consent_gate, audience_outbox, audit
):
    """Fail-closed on the audience chain: a non-APPROVED segment enqueues NOTHING (no audience sync at all),
    audited AUDIENCE_SEGMENT_NOT_APPROVED — membership is read for sync only, never a trigger (RULE-012)."""
    out = enqueue_audience_sync(
        "seg_pending", reader=segment_reader, consent_reader=app_consent_reader, consent_gate=consent_gate,
        store=audience_outbox, audit=audit, platform=AudiencePlatform.META_AUDIENCE, max_retries=3,
    )
    assert out == [] and len(audience_outbox) == 0
    assert audit.find("AUDIENCE_SEGMENT_NOT_APPROVED")


# --- positive control: proves the block is consent-caused, not a blanket refusal ------------------
def test_smk_002_control_valid_consent_would_deliver(
    make_conversion, measurement_outbox, consent_gate, app_consent_reader, audit, succeeding_transport
):
    """Control (non-vacuity): cs_valid (subject guest_mapped_ok, current VALID) passes BOTH consent checkpoints,
    so with an injected succeeding transport it delivers — proving the primary blocks because consent is
    *missing*, not because everything is refused. (Actual real send still stays OFF via StagedBlockedTransport;
    this control injects a test-double transport by design.)"""
    conv = make_conversion("VIEW_LANDING", consent_snapshot_id="cs_valid", customer_or_guest_key="guest_mapped_ok")
    enqueue_measurement(conv, measurement_outbox, max_retries=3)
    _dispatcher(measurement_outbox, succeeding_transport, consent_gate, app_consent_reader, audit).run_once(now=_TS)
    assert measurement_outbox.count_status(OutboxStatus.SENT) == 2
