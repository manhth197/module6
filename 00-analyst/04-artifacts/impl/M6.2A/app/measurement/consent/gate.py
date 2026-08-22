"""RULE-002 consent fail-closed gate.

Without valid consent there is NO external measurement, NO audience sync, NO CRM send. Only a snapshot whose
`consent_state == VALID` and whose `consent_scope` includes the requested egress kind is eligible. Everything
else — MISSING, EXPIRED, OPT_OUT, an absent snapshot, or a scope not granted — is denied.

This gate marks EGRESS ELIGIBILITY ONLY; it never sends anything (external_send=OFF; no dispatcher in M6.2A).
Prevents M6-FAIL-002 (consent violation). Backs smoke M6-SMK-002. Exit-gate leg L2.
"""
from __future__ import annotations

from typing import Optional

from app.measurement.audit import AuditLog
from app.measurement.models.consumed import ConsentScope, ConsentSnapshot, ConsentState
from app.measurement.ports import ConsentReader


class ConsentGate:
    def __init__(self, audit: AuditLog) -> None:
        self._audit = audit

    def evaluate(
        self, snapshot: Optional[ConsentSnapshot], scope: ConsentScope
    ) -> bool:
        """Event-time checkpoint. Return True ONLY when egress is permitted; fail-closed otherwise."""
        # Harden the REQUESTED scope. A raw string is dangerous BOTH ways: it can hash/substring-match into
        # the ALLOW branch, and it blows up `scope.value` in every DENY audit (AttributeError). Coerce to a
        # ConsentScope member; an unrecognized scope is denied, not trusted and not crashed.
        try:
            scope = ConsentScope(scope)
        except (ValueError, TypeError):
            self._audit.record("HOLD", "CONSENT_SCOPE_MALFORMED")
            return False

        # Absent snapshot -> fail-closed (never infer/upgrade consent).
        if snapshot is None:
            self._audit.record(
                "HOLD", "CONSENT_SNAPSHOT_ABSENT", detail=scope.value
            )
            return False

        if snapshot.consent_state is not ConsentState.VALID:
            self._audit.record(
                "HOLD", f"CONSENT_{snapshot.consent_state.value.upper()}",
                subject=snapshot.subject_ref, detail=scope.value,
            )
            return False

        if scope not in snapshot.consent_scope:
            self._audit.record(
                "HOLD", "CONSENT_SCOPE_NOT_GRANTED",
                subject=snapshot.subject_ref, detail=scope.value,
            )
            return False

        return True

    def permits_send(
        self,
        snapshot: Optional[ConsentSnapshot],
        scope: ConsentScope,
        consent_reader: ConsentReader,
    ) -> bool:
        """Two-checkpoint send gate for the FUTURE dispatcher (out of scope in M6.2A).

        Requires BOTH the event-time snapshot to be eligible AND current consent to still be VALID at send time.
        Kept here to document the contract; no caller in this slice sends anything (external_send=OFF).
        """
        if not self.evaluate(snapshot, scope):
            return False
        assert snapshot is not None  # evaluate() already rejected None
        current = consent_reader.current_state(snapshot.subject_ref)
        if current is not ConsentState.VALID:
            self._audit.record(
                "HOLD", "CONSENT_LAPSED_AT_SEND_TIME",
                subject=snapshot.subject_ref, detail=scope.value,
            )
            return False
        return True
