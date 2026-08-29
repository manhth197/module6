"""M6-CTR-021 marketing_measurement_dispatcher — the ONLY measurement sender (RULE-004).

`run_once()` drains due outbox rows and, for each, evaluates the send_policy then attempts delivery:
  send_policy [doc 12 L257] = consent_valid(SEND-TIME) AND event_in_registry AND data_quality_pass AND not_duplicate
  - **consent** is re-validated at send (RULE-002 checkpoint 2) via `ConsentGate.permits_send` — a missing/
    expired/opt-out consent => policy-block, NEVER sent (SMK-002, prevents FAIL-002).
  - **data_quality_pass** is fail-closed: read via a `dq_status` hook; the staged default is HOLD (no DQ checker
    until M6.2F / M6-CTR-024) => not PASS => not sent. Tests inject PASS to exercise the send path (SMK-016).
  - **not_duplicate** is structural: the outbox `dedup_key` is UNIQUE, so a duplicate never got a second row.
  - **event_in_registry** is enforced UPSTREAM at conversion creation (the endpoint rejects UNKNOWN_EVENT), per
    the CTR-001 contract ("registry gate enforced upstream at ingest"); the row carries no event_code to re-look-up.
A **policy-block** is a TERMINAL non-send (-> DEAD_LETTER with a reason, audited) — not a retry loop. A transient
**transport** failure is a bounded RETRY -> DEAD_LETTER (SMK-016). The staged transport refuses (external_send=OFF)
so nothing real is sent. Every subject is masked on export (O1).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, List, Optional, Tuple

from app.measurement.models.consumed import ConsentScope
from app.measurement.models.measurement_outbox import MeasurementOutboxItem, OutboxStatus
from app.measurement.outbox.transport import _append, attempt_delivery, safe_subject_ref


def _staged_dq_hold(item: Any) -> str:
    """Fail-closed default: no data_quality_checker runs until M6.2F, so every real item is HOLD (not PASS)."""
    return "HOLD"


class MeasurementDispatcher:
    def __init__(
        self,
        store: Any,
        transport: Any,
        consent_gate: Any,
        consent_reader: Any,
        audit: Any,
        *,
        scope: ConsentScope = ConsentScope.EXTERNAL_MEASUREMENT,
        dq_status: Optional[Callable[[Any], str]] = None,
        backoff_base_seconds: int = 60,
    ) -> None:
        self._store = store
        self._transport = transport
        self._gate = consent_gate
        self._reader = consent_reader
        self._audit = audit
        self._scope = scope
        self._dq_status = dq_status or _staged_dq_hold
        self._backoff = backoff_base_seconds

    def run_once(self, now: Optional[datetime] = None) -> List[MeasurementOutboxItem]:
        now = now or datetime.now(timezone.utc)
        processed: List[MeasurementOutboxItem] = []
        for item in self._store.due_items(now):
            self._process(item, now)
            processed.append(item)
        return processed

    def _process(self, item: MeasurementOutboxItem, now: datetime) -> None:
        reason, subject = self._policy_block(item)
        if reason is not None:
            # terminal fail-closed non-send (consent/DQ) — audited, dead-lettered with a trace; NOT retried.
            item.status = OutboxStatus.DEAD_LETTER
            item.error_log = _append(item.error_log, f"POLICY_BLOCK:{reason}")
            item.next_retry_at = None
            self._audit.record(
                "HOLD", f"SEND_BLOCKED_{reason}", subject=subject, detail=f"outbox={item.outbox_id}"
            )
            return
        attempt_delivery(
            item, self._transport, now, self._audit, subject_ref=subject, backoff_base_seconds=self._backoff
        )

    def _policy_block(self, item: MeasurementOutboxItem) -> Tuple[Optional[str], Optional[str]]:
        snap = None
        try:
            snap = self._reader.get(item.consent_snapshot_id)
        except Exception:
            snap = None
        # F-F (M6.2E): extract subject_ref fail-closed — a snapshot whose subject_ref PROPERTY raises must not
        # crash run_once (a plain getattr(...) only swallows AttributeError). See transport.safe_subject_ref.
        subject = safe_subject_ref(snap)
        # F-A (M6.2D): a consent-reader/current_state failure at send must DENY, never crash or fail-open.
        try:
            permitted = self._gate.permits_send(snap, self._scope, self._reader)   # consent re-check (RULE-002)
        except Exception:
            return "CONSENT", subject
        if not permitted:
            return "CONSENT", subject
        if self._dq_status(item) != "PASS":                                # fail-closed (HOLD until M6.2F)
            return "DATA_QUALITY", subject
        return None, subject
