"""Official smoke — slice M6.2C — M6-SMK-016 (proposed — HARDENING, owner review).

Authored by TESTER in M6-P1203 (mode=build, "do not yet run"); EXECUTED and recorded in M6-P1204
(TESTER_RUN -> 04-artifacts/test-reports/M6.2C/SMOKE_RESULTS.md). Governance is immutable here:
global_gateway_state=BLOCKED, production_flag=OFF, external_send=OFF — nothing below flips a flag.

Scenario / expected are quoted VERBATIM from 00-spec/registers/SMOKE_REGISTER.md (extract, proposed row):

    Scenario (verbatim):   "Outbox item fails to send N times"
    Expected (verbatim):   "Bounded retry with error_log + next_retry_at, then dead-letter; no infinite retry,
                            no silent loss"

The bounded-retry state machine lives in `attempt_delivery` (shared by both dispatchers): a TRANSIENT transport
failure -> RETRY (error_log + next_retry_at + retry_count) up to `max_retries`, then DEAD_LETTER. A dead-lettered
row is never re-processed (no infinite retry) and keeps its full error trace (no silent loss). Exercised with an
INJECTED failing transport (a Transport-port test double) — never a real platform call, never a flag flip.
`M6-SMK-016` is `proposed — HARDENING (owner review)`; per the M6.2C done-gate leg 4 it is executed here (not
waived). RULE-004 (worker-only send) / doc §12. All ids synthetic; identity refs masked on export (O1). Reuses
the shared conftest fixtures (make_conversion, measurement_outbox, consent_gate, app_consent_reader, audit,
failing_transport, succeeding_transport).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.measurement.models.measurement_outbox import OutboxStatus
from app.measurement.outbox.enqueue import enqueue_measurement
from app.measurement.outbox.measurement_dispatcher import MeasurementDispatcher

_TS = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)


def _dispatcher(store, transport, consent_gate, reader, audit):
    # dq_status PASS so the send-policy passes and the transport (retry/dead-letter) path is what we exercise.
    return MeasurementDispatcher(store, transport, consent_gate, reader, audit, dq_status=lambda item: "PASS")


# --- primary smoke: scenario verbatim -------------------------------------------------------------
def test_smk_016_bounded_retry_then_dead_letter_no_infinite_no_silent_loss(
    make_conversion, measurement_outbox, consent_gate, app_consent_reader, audit, failing_transport
):
    """M6-SMK-016 "Outbox item fails to send N times" -> "Bounded retry with error_log + next_retry_at, then
    dead-letter; no infinite retry, no silent loss".

    A transport that always fails transiently drives each row: first attempt -> RETRY carrying an error_log and
    a scheduled next_retry_at; then, once retry_count reaches max_retries, DEAD_LETTER with the full error trace
    retained. retry_count is bounded at max_retries (no infinite retry) and the row is never dropped (no silent
    loss).
    """
    conv = make_conversion("VIEW_LANDING", consent_snapshot_id="cs_valid", customer_or_guest_key="guest_mapped_ok")
    enqueue_measurement(conv, measurement_outbox, max_retries=3)          # PIXEL + CAPI rows
    disp = _dispatcher(measurement_outbox, failing_transport, consent_gate, app_consent_reader, audit)

    # First attempt -> bounded RETRY with error_log + next_retry_at (the retry bookkeeping).
    disp.run_once(now=_TS)
    mid = measurement_outbox.all()
    assert all(r.status is OutboxStatus.RETRY for r in mid)
    assert all(r.retry_count == 1 for r in mid)
    assert all(r.next_retry_at is not None for r in mid), "a RETRY schedules next_retry_at"
    assert all(r.error_log and "SEND_FAILED" in r.error_log for r in mid), "error_log records the failure"
    assert audit.find("OUTBOX_RETRY")

    # Keep running past each next_retry_at until retries are exhausted -> DEAD_LETTER at max_retries.
    for i in range(1, 5):
        disp.run_once(now=_TS + timedelta(hours=i))

    assert measurement_outbox.count_status(OutboxStatus.SENT) == 0
    assert measurement_outbox.count_status(OutboxStatus.DEAD_LETTER) == 2
    for r in measurement_outbox.all():
        assert r.retry_count == 3, "bounded at max_retries — no infinite retry"
        assert r.error_log and "SEND_FAILED" in r.error_log, "full trace retained — no silent loss"
    assert audit.find("OUTBOX_DEAD_LETTER")


# --- negative / fail-closed companions ------------------------------------------------------------
def test_smk_016_neg_dead_lettered_item_is_not_reprocessed(
    make_conversion, measurement_outbox, consent_gate, app_consent_reader, audit, failing_transport
):
    """No infinite retry: with max_retries=1 the first failure dead-letters immediately; a later worker pass
    does not touch the transport again (dead-lettered rows are not due)."""
    conv = make_conversion("VIEW_LANDING", consent_snapshot_id="cs_valid", customer_or_guest_key="guest_mapped_ok")
    enqueue_measurement(conv, measurement_outbox, max_retries=1)
    disp = _dispatcher(measurement_outbox, failing_transport, consent_gate, app_consent_reader, audit)
    disp.run_once(now=_TS)
    assert measurement_outbox.count_status(OutboxStatus.DEAD_LETTER) == 2
    attempts_after_first = failing_transport.attempts
    disp.run_once(now=_TS + timedelta(days=1))
    assert failing_transport.attempts == attempts_after_first, "a dead-lettered item is never retried again"


def test_smk_016_neg_consent_policy_block_is_a_distinct_terminal_not_a_retry_loop(
    make_conversion, measurement_outbox, consent_gate, app_consent_reader, audit, failing_transport
):
    """A consent policy-block is a DISTINCT terminal, not a transient failure: the item is dead-lettered by
    policy WITHOUT the transport ever being attempted, so it can never spin the retry loop."""
    conv = make_conversion("VIEW_LANDING", consent_snapshot_id="cs_missing", customer_or_guest_key="guest_x")
    enqueue_measurement(conv, measurement_outbox, max_retries=3)
    disp = _dispatcher(measurement_outbox, failing_transport, consent_gate, app_consent_reader, audit)
    for i in range(5):
        disp.run_once(now=_TS + timedelta(hours=i))
    assert failing_transport.attempts == 0, "a consent policy-block never reaches the transport (not a retry)"
    assert measurement_outbox.count_status(OutboxStatus.DEAD_LETTER) == 2
    assert audit.find("SEND_BLOCKED_CONSENT")


# --- positive control: proves dead-letter is failure-caused, not a blanket outcome ----------------
def test_smk_016_control_successful_transport_marks_sent_no_retry(
    make_conversion, measurement_outbox, consent_gate, app_consent_reader, audit, succeeding_transport
):
    """Control (non-vacuity): an injected succeeding transport marks the rows SENT with no RETRY and no
    DEAD_LETTER — the dead-letter path in the primary is caused by the failing transport, not by everything."""
    conv = make_conversion("VIEW_LANDING", consent_snapshot_id="cs_valid", customer_or_guest_key="guest_mapped_ok")
    enqueue_measurement(conv, measurement_outbox, max_retries=3)
    _dispatcher(measurement_outbox, succeeding_transport, consent_gate, app_consent_reader, audit).run_once(now=_TS)
    assert measurement_outbox.count_status(OutboxStatus.SENT) == 2
    assert measurement_outbox.count_status(OutboxStatus.DEAD_LETTER) == 0
    assert len(succeeding_transport.delivered) == 2
