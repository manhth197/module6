"""M6-CTR-022 marketing_audience_dispatcher — consent-fail-closed audience sync (the ONLY audience sender).

`run_once()` drains due audience-outbox rows and, per row, re-validates consent at send (RULE-002 checkpoint 2)
before delivery:
  - operation **ADD** requires current consent VALID (via `ConsentGate.permits_send`, AUDIENCE_SYNC scope); a
    missing/expired/opt-out consent => policy-block, NOT synced (SMK-002/SMK-008, prevents FAIL-002).
  - operation **REMOVE** is always allowed (fail-closed removal — removing a member never needs consent).
Audience sync is only ever from an APPROVED segment + this outbox (enforced at enqueue) — never ad-hoc/data-mart/
runtime (RULE-004/012); membership is never a trigger owner (RULE-012). A policy-block is a TERMINAL non-send
(-> DEAD_LETTER + reason); a transient transport failure is a bounded RETRY -> DEAD_LETTER (SMK-016). The staged
transport refuses (external_send=OFF). member subjects are masked on export (O1).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple

from app.measurement.models.audience_outbox import AudienceOperation, AudienceOutboxItem
from app.measurement.models.consumed import ConsentScope
from app.measurement.models.measurement_outbox import OutboxStatus
from app.measurement.outbox.transport import _append, attempt_delivery


class AudienceDispatcher:
    def __init__(
        self,
        store: Any,
        transport: Any,
        consent_gate: Any,
        consent_reader: Any,
        audit: Any,
        *,
        scope: ConsentScope = ConsentScope.AUDIENCE_SYNC,
        backoff_base_seconds: int = 60,
    ) -> None:
        self._store = store
        self._transport = transport
        self._gate = consent_gate
        self._reader = consent_reader
        self._audit = audit
        self._scope = scope
        self._backoff = backoff_base_seconds

    def run_once(self, now: Optional[datetime] = None) -> List[AudienceOutboxItem]:
        now = now or datetime.now(timezone.utc)
        processed: List[AudienceOutboxItem] = []
        for item in self._store.due_items(now):
            self._process(item, now)
            processed.append(item)
        return processed

    def _process(self, item: AudienceOutboxItem, now: datetime) -> None:
        reason, subject = self._policy_block(item)
        if reason is not None:
            item.status = OutboxStatus.DEAD_LETTER
            item.error_log = _append(item.error_log, f"POLICY_BLOCK:{reason}")
            item.next_retry_at = None
            self._audit.record(
                "HOLD", f"SYNC_BLOCKED_{reason}", subject=subject,
                detail=f"outbox={item.outbox_id};op={item.operation.value}",
            )
            return
        attempt_delivery(
            item, self._transport, now, self._audit, subject_ref=subject, backoff_base_seconds=self._backoff
        )

    def _policy_block(self, item: AudienceOutboxItem) -> Tuple[Optional[str], Optional[str]]:
        snap = None
        try:
            snap = self._reader.get(item.consent_snapshot_id)
        except Exception:
            snap = None
        subject = getattr(snap, "subject_ref", None)
        # REMOVE always proceeds (fail-closed removal — removing a member never needs consent).
        if item.operation is not AudienceOperation.ADD:
            return None, subject
        # F-C (M6.2D): BIND the consent to THIS member. A snapshot whose subject_ref is not this member's key is
        # BORROWED consent (member A synced under member B's valid consent) — fail-closed on mismatch/absence.
        if snap is None or getattr(snap, "subject_ref", None) != item.member_key:
            return "CONSENT_SUBJECT_MISMATCH", subject
        # F-A (M6.2D): a consent-reader/current_state failure at send must DENY, never crash or fail-open.
        try:
            permitted = self._gate.permits_send(snap, self._scope, self._reader)
        except Exception:
            return "CONSENT", subject
        if not permitted:
            return "CONSENT", subject
        return None, subject
